"""Build small synthetic PDFs for parser tests."""

from __future__ import annotations

import base64
from pathlib import Path

import pymupdf

Line = str | tuple[float, str]

PNG_1X1 = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
)


def build_pdf(
    path: Path,
    pages: list[list[Line]],
    *,
    image: bool = False,
    vector: bool = False,
    header: str | None = None,
) -> None:
    """Write a text PDF. Each item is a line or an ``(x, text)`` pair."""
    document = pymupdf.open()
    try:
        for page_index, lines in enumerate(pages, start=1):
            page = document.new_page()
            if header:
                page.insert_text((72, 28), header, fontsize=9)
                page.insert_text((72, 820), f"Seite {page_index}", fontsize=9)
            y = 72.0
            for item in lines:
                # Default x matches the official catalog's question column.
                x, text = item if isinstance(item, tuple) else (37.0, item)
                page.insert_text((x, y), text, fontsize=11)
                y += 16
            if image and page_index == 1:
                page.insert_image(pymupdf.Rect(200, 118, 240, 148), stream=PNG_1X1)
            if vector and page_index == len(pages):
                shape = page.new_shape()
                shape.draw_circle(pymupdf.Point(320, 400), 28)
                shape.finish(color=(0, 0, 1), fill=(0.6, 0.7, 1))
                shape.commit()
        path.parent.mkdir(parents=True, exist_ok=True)
        document.save(path)
    finally:
        document.close()
