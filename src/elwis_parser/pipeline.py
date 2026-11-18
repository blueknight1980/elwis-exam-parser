"""Command workflows shared by the CLI."""

from __future__ import annotations

import json
import logging
from datetime import date, datetime
from pathlib import Path

from elwis_parser.config import Settings
from elwis_parser.exceptions import (
    ConfigurationError,
    ExportError,
    UsageError,
    ValidationFailedError,
)
from elwis_parser.exporters.csv_exporter import write_csv
from elwis_parser.exporters.json_exporter import build_export, read_export, write_json
from elwis_parser.models import ExamParseResult, ExportDocument, SourceDocument, ValidationReport
from elwis_parser.parsers import get_parser
from elwis_parser.pdf.backend import open_pdf
from elwis_parser.pdf.extractor import extract_document
from elwis_parser.pdf.images import associate_images, materialize_rasters, materialize_vectors
from elwis_parser.pdf.inspector import inspection_payload, inspection_text
from elwis_parser.sources.local import load_local_pdf
from elwis_parser.sources.registry import normalize_exam_id
from elwis_parser.utils.paths import ensure_within
from elwis_parser.validation import validate_result

logger = logging.getLogger(__name__)


def inspect_pdf(
    path: Path,
    *,
    settings: Settings,
    page: int | None = None,
    as_json: bool = False,
) -> str:
    """Inspect one PDF and return text for the terminal."""
    source = load_local_pdf(path, settings=settings)
    document = open_pdf(path, settings)
    try:
        extraction = extract_document(document, source.id)
    finally:
        document.close()
    if page is not None and (page < 1 or page > extraction.page_count):
        raise UsageError(f"Page {page} is outside 1..{extraction.page_count}.")
    if as_json:
        payload = inspection_payload(extraction, page=page)
        payload["filename"] = source.filename
        payload["sha256"] = source.sha256
        return json.dumps(payload, ensure_ascii=False, indent=2)
    text = inspection_text(extraction, page=page)
    return f"File: {source.filename}\nSHA-256: {source.sha256}\n{text}"


def extract_pdf(
    path: Path,
    output: Path,
    *,
    settings: Settings,
    overwrite: bool = False,
) -> Path:
    """Write a technical extraction and any rendered regions."""
    _prepare_dir(output, overwrite, "extraction.json")
    source = load_local_pdf(path, settings=settings)
    document = open_pdf(path, settings)
    try:
        extraction = extract_document(document, source.id)
        pending = materialize_rasters(
            document,
            extraction.images,
            source_id=source.id,
            settings=settings,
        )
        pending.extend(
            materialize_vectors(
                document,
                extraction.vectors,
                source_id=source.id,
                settings=settings,
            )
        )
    finally:
        document.close()
    image_dir = output / "images"
    image_dir.mkdir(parents=True, exist_ok=True)
    for asset, data in pending:
        if asset.metadata.get("role") == "page_chrome":
            continue
        target = ensure_within(output, output / asset.relative_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
    payload = extraction.model_dump(mode="json")
    payload["filename"] = source.filename
    payload["sha256"] = source.sha256
    destination = output / "extraction.json"
    destination.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return destination


def parse_pdf(
    path: Path,
    examination: str,
    output: Path,
    *,
    settings: Settings,
    strict: bool = False,
    overwrite: bool = False,
    title: str | None = None,
    publisher: str | None = None,
    source_url: str | None = None,
    document_date: date | None = None,
    retrieved_at: datetime | None = None,
    exported_at: datetime | None = None,
) -> tuple[Path, ValidationReport]:
    """Parse a catalog PDF and write ``catalog.json``."""
    try:
        examination_id = normalize_exam_id(examination)
    except KeyError as exc:
        raise ConfigurationError(str(exc)) from exc
    parser = get_parser(examination_id)
    _prepare_dir(output, overwrite, "catalog.json")
    source = load_local_pdf(
        path,
        settings=settings,
        title=title,
        publisher=publisher,
        source_url=source_url,
        document_date=document_date,
        retrieved_at=retrieved_at,
    )
    document = open_pdf(path, settings)
    try:
        extraction = extract_document(document, source.id)
        result = parser.parse(source, extraction)
        rasters = materialize_rasters(
            document,
            extraction.images,
            source_id=source.id,
            settings=settings,
        )
        vectors = materialize_vectors(
            document,
            extraction.vectors,
            source_id=source.id,
            settings=settings,
        )
    except Exception:
        document.close()
        raise
    else:
        document.close()
    content = [
        (asset, data)
        for asset, data in [*rasters, *vectors]
        if asset.metadata.get("role") != "page_chrome"
    ]
    result.images = [asset for asset, _data in content]
    result.findings.extend(associate_images(result.questions, result.layouts, result.images))
    result.findings.extend(extraction.anomalies)
    report = validate_result(result)
    output.mkdir(parents=True, exist_ok=True)
    validation_path = output / "validation.json"
    validation_path.write_text(
        json.dumps(report.summary(), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    if strict and report.error_count:
        raise ValidationFailedError(
            f"Strict mode refused the export: {report.error_count} validation error(s). "
            f"See {validation_path.name}."
        )
    exported = exported_at or datetime.now().astimezone()
    export_document = build_export(result, report, exported_at=exported)
    kept = {image.id for image in export_document.images}
    _write_images(output, [(asset, data) for asset, data in content if asset.id in kept])
    destination = output / "catalog.json"
    write_json(export_document, destination)
    logger.info(
        "Parsed %s questions from %s (%s errors, %s warnings)",
        len(result.questions),
        source.filename,
        report.error_count,
        report.warning_count,
    )
    return destination, report


def validate_export(path: Path) -> ValidationReport:
    """Re-validate an export file."""
    document = read_export(path)
    if document.schema_version != "1.0":
        raise ExportError(f"Unsupported schema version {document.schema_version}.")
    result = _result_from_export(document)
    return validate_result(result)


def export_csv(path: Path, destination: Path, *, overwrite: bool = False) -> Path:
    """Write a CSV view of an export file."""
    if destination.exists() and not overwrite:
        raise UsageError(f"Output already exists: {destination}. Pass --overwrite to replace it.")
    document = read_export(path)
    write_csv(document, destination)
    return destination


def _result_from_export(document: ExportDocument) -> ExamParseResult:
    sources: list[SourceDocument] = []
    for raw in document.sources:
        payload = dict(raw)
        payload.setdefault("parser_version", document.parser_version)
        payload.setdefault("filename", "unknown.pdf")
        payload.setdefault("sha256", "")
        sources.append(SourceDocument.model_validate(payload))
    return ExamParseResult(
        examination_id=document.examination,
        catalogs=document.catalogs,
        questions=document.questions,
        images=document.images,
        sources=sources,
        preamble=[
            str(item) for item in document.metadata.get("preamble", []) if isinstance(item, str)
        ],
    )


def _prepare_dir(output: Path, overwrite: bool, marker: str) -> None:
    output.mkdir(parents=True, exist_ok=True)
    existing = output / marker
    if existing.exists() and not overwrite:
        raise UsageError(f"Output already exists: {existing}. Pass --overwrite to replace it.")


def _write_images(output: Path, content: list[tuple[object, bytes]]) -> None:
    from elwis_parser.models import ImageAsset

    for asset, data in content:
        if not isinstance(asset, ImageAsset):
            continue
        target = ensure_within(output, output / asset.relative_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        if not target.exists():
            target.write_bytes(data)
