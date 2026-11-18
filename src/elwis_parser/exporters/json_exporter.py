"""JSON export."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from elwis_parser import SCHEMA_VERSION, __version__
from elwis_parser.exceptions import ExportError
from elwis_parser.models import ExamParseResult, ExportDocument, ValidationReport
from elwis_parser.utils.paths import ensure_within


def build_export(
    result: ExamParseResult,
    report: ValidationReport,
    *,
    exported_at: datetime,
) -> ExportDocument:
    """Build the public export document.

    Local filesystem paths are omitted. Page-chrome images are omitted.
    """
    images = [image for image in result.images if image.metadata.get("role") != "page_chrome"]
    referenced = {image_id for question in result.questions for image_id in question.image_ids}
    images = [image for image in images if image.id in referenced or image.associated_question_ids]
    return ExportDocument(
        schema_version=SCHEMA_VERSION,
        parser_version=__version__,
        exported_at=exported_at,
        examination=result.examination_id,
        catalogs=result.catalogs,
        questions=result.questions,
        images=images,
        sources=[source.public_dict() for source in result.sources],
        validation=report.summary(),
        metadata={"preamble": result.preamble},
    )


def write_json(document: ExportDocument, path: Path) -> None:
    """Write UTF-8 JSON with stable key order from the model."""
    path.parent.mkdir(parents=True, exist_ok=True)
    ensure_within(path.parent, path)
    payload = document.model_dump(mode="json")
    text = json.dumps(payload, ensure_ascii=False, indent=2)
    path.write_text(text + "\n", encoding="utf-8")


def read_export(path: Path) -> ExportDocument:
    """Load an export file."""
    if not path.is_file():
        raise ExportError(f"Export file not found: {path}")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ExportError(f"Export file is not valid JSON: {exc}") from exc
    if not isinstance(payload, dict):
        raise ExportError("Export file must contain a JSON object.")
    try:
        return ExportDocument.model_validate(payload)
    except Exception as exc:
        raise ExportError(f"Export file does not match schema {SCHEMA_VERSION}: {exc}") from exc
