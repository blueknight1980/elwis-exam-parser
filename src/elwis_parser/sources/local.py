"""Load a local PDF into a source record."""

from __future__ import annotations

from datetime import date, datetime
from pathlib import Path

from elwis_parser import __version__
from elwis_parser.config import Settings
from elwis_parser.exceptions import SourceError, UsageError
from elwis_parser.models import SourceDocument
from elwis_parser.utils.hashing import sha256_file


def load_local_pdf(
    path: Path,
    *,
    settings: Settings,
    title: str | None = None,
    publisher: str | None = None,
    source_url: str | None = None,
    document_date: date | None = None,
    retrieved_at: datetime | None = None,
) -> SourceDocument:
    """Hash a local PDF and return its source record.

    The file is not opened here. PDF parsing happens in the PDF layer.
    """
    if path.suffix.casefold() != ".pdf":
        raise UsageError(f"Expected a PDF file, got {path.name}")
    if not path.is_file():
        raise SourceError(f"PDF not found: {path}")
    size = path.stat().st_size
    if size > settings.max_pdf_bytes:
        raise SourceError(
            f"PDF exceeds the size limit of {settings.max_pdf_bytes} bytes: {path.name}"
        )
    if size == 0:
        raise SourceError(f"PDF is empty: {path.name}")
    digest = sha256_file(path)
    return SourceDocument(
        id=f"src:{digest[:16]}",
        title=title,
        publisher=publisher,
        source_url=source_url,
        document_date=document_date,
        retrieved_at=retrieved_at,
        sha256=digest,
        filename=path.name,
        local_path=str(path),
        parser_version=__version__,
    )
