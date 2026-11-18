"""Reading order and running headers."""

from __future__ import annotations

import re

from elwis_parser.models.extraction import TextBlock

_PAGE_LABEL = re.compile(r"^(seite|page)\s+\d+$", re.IGNORECASE)


def order_blocks(blocks: list[TextBlock], page_width: float) -> list[TextBlock]:
    """Order blocks for a single-column or simple two-column page.

    A two-column split is used only when a wide horizontal gap separates two
    groups that each contain more than one block. Navigation tables keep the
    geometric order because their columns are handled by the exam parser.
    """
    if len(blocks) < 4:
        ordered = sorted(blocks, key=lambda block: (block.bbox.y0, block.bbox.x0))
        for index, block in enumerate(ordered):
            block.reading_order = index
        return ordered
    by_x = sorted(blocks, key=lambda block: block.bbox.x0)
    split_at: float | None = None
    best_gap = 0.0
    for left, right in zip(by_x, by_x[1:], strict=False):
        gap = right.bbox.x0 - left.bbox.x1
        if gap > best_gap:
            best_gap = gap
            split_at = right.bbox.x0
    spanning = [
        block
        for block in blocks
        if split_at is not None and block.bbox.x0 < split_at < block.bbox.x1
    ]
    if split_at is None or best_gap < max(36.0, page_width * 0.04) or spanning:
        # A block that crosses the gap is a full-width row, such as a
        # navigation scenario or a table line. Those pages stay in geometric
        # order so the row is not discarded.
        ordered = sorted(blocks, key=lambda block: (block.bbox.y0, block.bbox.x0))
    else:
        left_col = [block for block in blocks if block.bbox.x1 <= split_at]
        right_col = [block for block in blocks if block.bbox.x0 >= split_at]
        if len(left_col) < 2 or len(right_col) < 2:
            ordered = sorted(blocks, key=lambda block: (block.bbox.y0, block.bbox.x0))
        else:
            left_col.sort(key=lambda block: block.bbox.y0)
            right_col.sort(key=lambda block: block.bbox.y0)
            for block in left_col:
                block.column = 0
            for block in right_col:
                block.column = 1
            ordered = left_col + right_col
    for index, block in enumerate(ordered):
        block.reading_order = index
    return ordered


def mark_running_margins(
    blocks: list[TextBlock], page_sizes: dict[int, tuple[float, float]]
) -> None:
    """Mark repeated top and bottom text as ``header`` or ``footer``.

    Digits are ignored when comparing repeated margin text, so ``Seite 1`` and
    ``Seite 2`` are treated as the same running footer.
    """
    grouped: dict[tuple[str, str], list[TextBlock]] = {}
    pages = set(page_sizes)
    for block in blocks:
        width, height = page_sizes.get(block.page, (0.0, 0.0))
        if height <= 0:
            continue
        zone = ""
        if block.bbox.y1 <= height * 0.08:
            zone = "header"
        elif block.bbox.y0 >= height * 0.92:
            zone = "footer"
        if not zone:
            continue
        normalized = re.sub(r"\d+", "#", " ".join(block.text.split()).casefold())
        if not normalized:
            continue
        grouped.setdefault((zone, normalized), []).append(block)
    minimum = 2 if len(pages) > 1 else 1
    threshold = max(minimum, len(pages) / 2)
    for (zone, _text), members in grouped.items():
        seen_pages = {block.page for block in members}
        if len(seen_pages) >= threshold or (len(pages) == 1 and _PAGE_LABEL.match(members[0].text)):
            for block in members:
                block.role = zone
