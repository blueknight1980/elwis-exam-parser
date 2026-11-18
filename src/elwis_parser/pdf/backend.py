"""Typed boundary around PyMuPDF.

PyMuPDF does not ship type stubs. Values that cross this module are checked
before they are returned.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pymupdf

from elwis_parser.config import Settings
from elwis_parser.exceptions import PdfError
from elwis_parser.models import BoundingBox


def open_pdf(path: Path, settings: Settings) -> Any:
    """Open a PDF or raise ``PdfError``.

    Encrypted documents are rejected. PDF JavaScript is never executed.
    """
    if not path.is_file():
        raise PdfError(f"PDF not found: {path}")
    if path.stat().st_size > settings.max_pdf_bytes:
        raise PdfError(f"PDF exceeds the size limit of {settings.max_pdf_bytes} bytes.")
    document = pymupdf.open(path)
    needs_password = bool(document.needs_pass)
    if needs_password:
        document.close()
        raise PdfError("Encrypted PDFs are not processed.")
    page_count = int(document.page_count)
    if page_count > settings.max_pdf_pages:
        document.close()
        raise PdfError(f"PDF has {page_count} pages, above the limit of {settings.max_pdf_pages}.")
    if page_count == 0:
        document.close()
        raise PdfError("PDF has no pages.")
    return document


def metadata_dict(document: Any) -> dict[str, str]:
    """Return PDF metadata values as strings."""
    raw = document.metadata
    if not isinstance(raw, dict):
        return {}
    result: dict[str, str] = {}
    for key, value in raw.items():
        if isinstance(key, str) and isinstance(value, str) and value:
            result[key] = value
    return result


def bbox_from(value: Any) -> BoundingBox | None:
    """Build a box from a rectangle-like value."""
    if isinstance(value, pymupdf.Rect):
        return BoundingBox(
            x0=float(value.x0), y0=float(value.y0), x1=float(value.x1), y1=float(value.y1)
        )
    if isinstance(value, (list, tuple)) and len(value) == 4:
        numbers: list[float] = []
        for item in value:
            if isinstance(item, (int, float)):
                numbers.append(float(item))
            else:
                return None
        return BoundingBox(x0=numbers[0], y0=numbers[1], x1=numbers[2], y1=numbers[3])
    x0 = getattr(value, "x0", None)
    y0 = getattr(value, "y0", None)
    x1 = getattr(value, "x1", None)
    y1 = getattr(value, "y1", None)
    if (
        isinstance(x0, (int, float))
        and isinstance(y0, (int, float))
        and isinstance(x1, (int, float))
        and isinstance(y1, (int, float))
    ):
        return BoundingBox(x0=float(x0), y0=float(y0), x1=float(x1), y1=float(y1))
    return None


def as_float(value: Any, default: float = 0.0) -> float:
    """Return ``value`` as a float when it is numeric."""
    if isinstance(value, (int, float)):
        return float(value)
    return default


def as_int(value: Any, default: int = 0) -> int:
    """Return ``value`` as an int when it is numeric."""
    if isinstance(value, bool):
        return default
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    return default


def as_str(value: Any) -> str:
    """Return ``value`` when it is a string."""
    if isinstance(value, str):
        return value
    return ""
