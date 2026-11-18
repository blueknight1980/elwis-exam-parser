"""Technical PDF extraction. This module does not interpret exam questions."""

from __future__ import annotations

from collections import Counter
from typing import Any

from elwis_parser.models import BoundingBox, Finding, Severity
from elwis_parser.models.extraction import (
    Extraction,
    PageInfo,
    RasterPlacement,
    TextBlock,
    TextLine,
)
from elwis_parser.pdf.backend import as_int, as_str, bbox_from, metadata_dict
from elwis_parser.pdf.images import vector_regions
from elwis_parser.pdf.layout import mark_running_margins, order_blocks
from elwis_parser.utils.text import join_wrapped_lines


def extract_document(document: Any, source_id: str) -> Extraction:
    """Extract text, raster placements, and vector regions from an open PDF."""
    pages: list[PageInfo] = []
    blocks: list[TextBlock] = []
    images: list[RasterPlacement] = []
    vectors = []
    anomalies: list[Finding] = []
    page_sizes: dict[int, tuple[float, float]] = {}
    for index, page in enumerate(document, start=1):
        rect = page.rect
        width = float(rect.width)
        height = float(rect.height)
        page_sizes[index] = (width, height)
        pages.append(
            PageInfo(
                number=index,
                width=width,
                height=height,
                rotation=as_int(page.rotation),
            )
        )
        page_blocks = _page_blocks(page, index)
        if not page_blocks:
            anomalies.append(
                Finding(
                    code="EMPTY_PAGE",
                    severity=Severity.INFO,
                    message="The page has no text blocks.",
                    entity_type="page",
                    entity_id=str(index),
                    source_id=source_id,
                    page=index,
                )
            )
        blocks.extend(order_blocks(page_blocks, width))
        images.extend(_page_images(page, index))
        drawings = page.get_drawings()
        drawing_list = drawings if isinstance(drawings, list) else []
        vectors.extend(
            vector_regions(
                drawing_list,
                page=index,
                page_width=width,
                page_height=height,
            )
        )
    mark_running_margins(blocks, page_sizes)
    return Extraction(
        source_id=source_id,
        page_count=len(pages),
        metadata=metadata_dict(document),
        pages=pages,
        blocks=blocks,
        images=images,
        vectors=vectors,
        anomalies=anomalies,
    )


def _page_blocks(page: Any, page_number: int) -> list[TextBlock]:
    raw = page.get_text("dict")
    if not isinstance(raw, dict):
        return []
    block_values = raw.get("blocks")
    if not isinstance(block_values, list):
        return []
    blocks: list[TextBlock] = []
    for block_index, block in enumerate(block_values):
        if not isinstance(block, dict) or block.get("type") != 0:
            continue
        box = bbox_from(block.get("bbox"))
        if box is None:
            continue
        lines = _lines(block)
        raw_lines = [line.text for line in lines]
        if not any(line.strip() for line in raw_lines):
            continue
        sizes = [line.font_size for line in lines if line.font_size is not None]
        blocks.append(
            TextBlock(
                id=f"p{page_number}-b{block_index}",
                page=page_number,
                bbox=box,
                lines=lines,
                text=join_wrapped_lines(raw_lines),
                raw_text="\n".join(raw_lines),
                font_size=_dominant(sizes),
            )
        )
    return blocks


def _lines(block: dict[str, Any]) -> list[TextLine]:
    raw_lines = block.get("lines")
    if not isinstance(raw_lines, list):
        return []
    lines: list[TextLine] = []
    for raw_line in raw_lines:
        if not isinstance(raw_line, dict):
            continue
        spans = raw_line.get("spans")
        if not isinstance(spans, list):
            continue
        texts: list[str] = []
        sizes: list[float] = []
        font_name: str | None = None
        for span in spans:
            if not isinstance(span, dict):
                continue
            texts.append(as_str(span.get("text")))
            size = span.get("size")
            if isinstance(size, (int, float)):
                sizes.append(float(size))
            if font_name is None:
                candidate = as_str(span.get("font"))
                font_name = candidate or None
        box = bbox_from(raw_line.get("bbox")) or BoundingBox(x0=0, y0=0, x1=0, y1=0)
        lines.append(
            TextLine(
                text="".join(texts),
                bbox=box,
                font_size=_dominant(sizes),
                font_name=font_name,
            )
        )
    return lines


def _page_images(page: Any, page_number: int) -> list[RasterPlacement]:
    info = page.get_image_info(xrefs=True)
    if not isinstance(info, list):
        return []
    placements: list[RasterPlacement] = []
    for item in info:
        if not isinstance(item, dict):
            continue
        box = bbox_from(item.get("bbox"))
        if box is None:
            continue
        placements.append(
            RasterPlacement(
                xref=as_int(item.get("xref")),
                page=page_number,
                bbox=box,
                width=as_int(item.get("width")),
                height=as_int(item.get("height")),
            )
        )
    return placements


def _dominant(sizes: list[float]) -> float | None:
    if not sizes:
        return None
    rounded = [round(size, 1) for size in sizes]
    return Counter(rounded).most_common(1)[0][0]
