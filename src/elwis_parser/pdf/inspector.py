"""Human and JSON inspection reports."""

from __future__ import annotations

from collections import Counter
from typing import Any

from elwis_parser.models.extraction import Extraction


def inspection_payload(extraction: Extraction, *, page: int | None = None) -> dict[str, Any]:
    """Return a JSON-ready inspection summary."""
    pages = extraction.pages
    if page is not None:
        pages = [item for item in pages if item.number == page]
    blocks = extraction.blocks
    images = extraction.images
    vectors = extraction.vectors
    anomalies = extraction.anomalies
    if page is not None:
        blocks = [block for block in blocks if block.page == page]
        images = [image for image in images if image.page == page]
        vectors = [vector for vector in vectors if vector.page == page]
        anomalies = [item for item in anomalies if item.page == page]
    fonts: Counter[str] = Counter()
    for block in blocks:
        if block.font_size is not None:
            fonts[str(block.font_size)] += 1
    return {
        "source_id": extraction.source_id,
        "page_count": extraction.page_count,
        "metadata": extraction.metadata,
        "selected_page": page,
        "pages": [item.model_dump(mode="json") for item in pages],
        "block_count": len(blocks),
        "image_count": len(images),
        "vector_region_count": len(vectors),
        "font_sizes": dict(fonts),
        "anomalies": [item.model_dump(mode="json") for item in anomalies],
        "blocks": [block.model_dump(mode="json") for block in blocks] if page else [],
        "images": [image.model_dump(mode="json") for image in images] if page else [],
        "vectors": [vector.model_dump(mode="json") for vector in vectors] if page else [],
    }


def inspection_text(extraction: Extraction, *, page: int | None = None) -> str:
    """Return a plain-text inspection summary."""
    payload = inspection_payload(extraction, page=page)
    lines = [
        f"Pages: {extraction.page_count}",
        f"Text blocks: {payload['block_count']}",
        f"Raster images: {payload['image_count']}",
        f"Vector regions: {payload['vector_region_count']}",
        f"Anomalies: {len(payload['anomalies'])}",
    ]
    if extraction.metadata:
        title = extraction.metadata.get("title", "")
        author = extraction.metadata.get("author", "")
        if title:
            lines.append(f"Title: {title}")
        if author:
            lines.append(f"Author: {author}")
    for anomaly in extraction.anomalies:
        if page is not None and anomaly.page != page:
            continue
        lines.append(f"- {anomaly.severity.value} {anomaly.code}: {anomaly.message}")
    if page is not None:
        lines.append(f"Page {page} text blocks:")
        for block in extraction.blocks:
            if block.page != page:
                continue
            preview = " ".join(block.raw_text.split())
            if len(preview) > 160:
                preview = preview[:157] + "..."
            lines.append(f"  [{block.role}] y={block.bbox.y0:.1f} x={block.bbox.x0:.1f} {preview}")
    return "\n".join(lines)
