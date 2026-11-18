"""Geometric text lines used by the exam parsers."""

from __future__ import annotations

from dataclasses import dataclass

from elwis_parser.models import BoundingBox, Extraction, PageRegion


@dataclass(frozen=True)
class RawLine:
    """One non-empty visual line."""

    page: int
    x: float
    y: float
    text: str
    bbox: BoundingBox
    block_id: str
    font_size: float | None
    role: str = "body"

    def region(self) -> PageRegion:
        """Return the provenance region for this line."""
        return PageRegion(page=self.page, bbox=self.bbox, block_ids=[self.block_id])


def flatten_lines(extraction: Extraction) -> list[RawLine]:
    """Return non-empty lines in geometric order."""
    lines: list[RawLine] = []
    for block in extraction.blocks:
        for line in block.lines:
            text = " ".join(line.text.split())
            if not text:
                continue
            lines.append(
                RawLine(
                    page=block.page,
                    x=line.bbox.x0,
                    y=line.bbox.y0,
                    text=text,
                    bbox=line.bbox,
                    block_id=block.id,
                    font_size=line.font_size or block.font_size,
                    role=block.role,
                )
            )
    lines.sort(key=lambda item: (item.page, item.y, item.x))
    return lines
