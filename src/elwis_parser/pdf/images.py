"""Raster and vector image handling."""

from __future__ import annotations

import logging
from typing import Any

import pymupdf

from elwis_parser.config import Settings
from elwis_parser.exceptions import PdfError
from elwis_parser.models import (
    BoundingBox,
    Finding,
    ImageAsset,
    ImageOrigin,
    PageSpan,
    Question,
    Severity,
)
from elwis_parser.models.extraction import RasterPlacement, VectorRegion
from elwis_parser.pdf.backend import as_int, as_str, bbox_from
from elwis_parser.utils.hashing import sha256_bytes

logger = logging.getLogger(__name__)

_MIME = {
    "png": "image/png",
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "jp2": "image/jp2",
    "tif": "image/tiff",
    "tiff": "image/tiff",
}
_KEEP_EXT = set(_MIME)


def is_page_chrome_image(bbox: BoundingBox) -> bool:
    """Return whether a placement is the running publisher logo."""
    return bbox.x0 > 280 and bbox.y0 < 150 and bbox.height < 80 and bbox.width > 100


def vector_regions(
    drawings: list[Any],
    *,
    page: int,
    page_width: float,
    page_height: float,
) -> list[VectorRegion]:
    """Cluster drawable marks that are larger than hairlines and page borders."""
    boxes: list[BoundingBox] = []
    for drawing in drawings:
        if not isinstance(drawing, dict):
            continue
        box = bbox_from(drawing.get("rect"))
        if box is None:
            continue
        if box.width < 2.5 or box.height < 2.5:
            continue
        if box.width > page_width * 0.9 or box.height > page_height * 0.9:
            continue
        boxes.append(box)
    clusters: list[BoundingBox] = []
    for box in boxes:
        placed = False
        for index, cluster in enumerate(clusters):
            if _near(cluster, box, margin=8):
                clusters[index] = cluster.union(box)
                placed = True
                break
        if not placed:
            clusters.append(box)
    regions: list[VectorRegion] = []
    for index, cluster in enumerate(clusters):
        if cluster.width < 12 or cluster.height < 12:
            continue
        regions.append(
            VectorRegion(
                id=f"vec-p{page}-{index}",
                page=page,
                bbox=cluster,
                drawing_count=1,
            )
        )
    return regions


def materialize_rasters(
    document: Any,
    placements: list[RasterPlacement],
    *,
    source_id: str,
    settings: Settings,
) -> list[tuple[ImageAsset, bytes]]:
    """Read embedded images. Identical bytes share one filename."""
    cache: dict[int, tuple[bytes, str, str]] = {}
    assets: list[tuple[ImageAsset, bytes]] = []
    total = 0
    for index, placement in enumerate(placements):
        if placement.xref not in cache:
            cache[placement.xref] = _read_xref(document, placement.xref)
        data, ext, encoding = cache[placement.xref]
        total += len(data)
        if total > settings.max_image_bytes:
            raise PdfError("Extracted images exceed the configured byte limit.")
        digest = sha256_bytes(data)
        filename = f"{digest[:20]}.{ext}"
        chrome = is_page_chrome_image(placement.bbox)
        asset = ImageAsset(
            id=f"img:{digest[:12]}:p{placement.page}:n{index}",
            filename=filename,
            relative_path=f"images/{filename}",
            mime_type=_MIME.get(ext, "application/octet-stream"),
            sha256=digest,
            source_page=placement.page,
            source_document_id=source_id,
            bounding_box=placement.bbox,
            width=placement.width,
            height=placement.height,
            origin=ImageOrigin.RASTER_ORIGINAL,
            metadata={
                "xref": placement.xref,
                "encoding": encoding,
                "role": "page_chrome" if chrome else "content",
            },
        )
        assets.append((asset, data))
    return assets


def materialize_vectors(
    document: Any,
    regions: list[VectorRegion],
    *,
    source_id: str,
    settings: Settings,
) -> list[tuple[ImageAsset, bytes]]:
    """Render vector clusters to PNG clips."""
    assets: list[tuple[ImageAsset, bytes]] = []
    total = 0
    for region in regions:
        page = document[region.page - 1]
        rectangle = pymupdf.Rect(
            region.bbox.x0,
            region.bbox.y0,
            region.bbox.x1,
            region.bbox.y1,
        )
        matrix = pymupdf.Matrix(2, 2)
        pixmap = page.get_pixmap(matrix=matrix, clip=rectangle, alpha=False)
        if pixmap.width * pixmap.height > 8_000_000:
            pixmap = page.get_pixmap(matrix=pymupdf.Matrix(1, 1), clip=rectangle, alpha=False)
        data = pixmap.tobytes("png")
        if not isinstance(data, bytes):
            continue
        total += len(data)
        if total > settings.max_image_bytes:
            raise PdfError("Rendered vector regions exceed the configured byte limit.")
        digest = sha256_bytes(data)
        filename = f"render-{digest[:20]}.png"
        asset = ImageAsset(
            id=f"img:{digest[:12]}:p{region.page}:{region.id}",
            filename=filename,
            relative_path=f"images/{filename}",
            mime_type="image/png",
            sha256=digest,
            source_page=region.page,
            source_document_id=source_id,
            bounding_box=region.bbox,
            width=int(pixmap.width),
            height=int(pixmap.height),
            origin=ImageOrigin.RENDERED_REGION,
            metadata={"vector_region_id": region.id, "role": "content"},
        )
        assets.append((asset, data))
    return assets


def associate_images(
    questions: list[Question],
    layouts: dict[str, list[PageSpan]],
    images: list[ImageAsset],
) -> list[Finding]:
    """Attach content images to the question whose vertical span contains them."""
    findings: list[Finding] = []
    for image in images:
        if image.metadata.get("role") == "page_chrome":
            continue
        _x, center_y = image.bounding_box.center()
        matches: list[Question] = []
        for question in questions:
            for span in layouts.get(question.id, []):
                if span.page == image.source_page and span.y0 - 2 <= center_y < span.y1:
                    matches.append(question)
                    break
        if not matches:
            findings.append(
                Finding(
                    code="UNASSOCIATED_IMAGE",
                    severity=Severity.WARNING,
                    message="An image placement does not fall inside a question span.",
                    entity_type="image",
                    entity_id=image.id,
                    source_id=image.source_document_id,
                    page=image.source_page,
                )
            )
            continue
        if len(matches) > 1:
            findings.append(
                Finding(
                    code="AMBIGUOUS_IMAGE",
                    severity=Severity.WARNING,
                    message="An image placement matches more than one question span.",
                    entity_type="image",
                    entity_id=image.id,
                    source_id=image.source_document_id,
                    page=image.source_page,
                )
            )
            matches.sort(
                key=lambda question: _distance(layouts.get(question.id, []), image),
            )
        chosen = matches[0]
        if image.id not in chosen.image_ids:
            chosen.image_ids.append(image.id)
        if chosen.id not in image.associated_question_ids:
            image.associated_question_ids.append(chosen.id)
        if len(matches) > 1:
            image.metadata["association_ambiguous"] = True
    return findings


def _distance(spans: list[PageSpan], image: ImageAsset) -> float:
    _x, center_y = image.bounding_box.center()
    for span in spans:
        if span.page == image.source_page:
            return abs(span.y0 - center_y)
    return 10_000.0


def _near(left: BoundingBox, right: BoundingBox, margin: float) -> bool:
    expanded = BoundingBox(
        x0=left.x0 - margin,
        y0=left.y0 - margin,
        x1=left.x1 + margin,
        y1=left.y1 + margin,
    )
    return expanded.contains_point(right.center()[0], right.center()[1]) or _overlaps(
        expanded, right
    )


def _overlaps(left: BoundingBox, right: BoundingBox) -> bool:
    return not (
        right.x1 < left.x0 or right.x0 > left.x1 or right.y1 < left.y0 or right.y0 > left.y1
    )


def _read_xref(document: Any, xref: int) -> tuple[bytes, str, str]:
    info = document.extract_image(xref)
    if not isinstance(info, dict):
        logger.warning("Image xref %s could not be extracted", xref)
        return b"", "png", "missing"
    data = info.get("image")
    ext = as_str(info.get("ext")).lower() or "png"
    smask = as_int(info.get("smask"))
    if isinstance(data, bytes) and ext in _KEEP_EXT and smask == 0:
        return data, "jpg" if ext == "jpeg" else ext, "original_bytes"
    pixmap = pymupdf.Pixmap(document, xref)
    if pixmap.n >= 5:
        pixmap = pymupdf.Pixmap(pymupdf.csRGB, pixmap)
    encoded = pixmap.tobytes("png")
    if not isinstance(encoded, bytes):
        return b"", "png", "png_reencoded"
    return encoded, "png", "png_reencoded"
