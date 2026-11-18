"""Shared value types."""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class QuestionType(StrEnum):
    """Supported question shapes.

    Further examinations can add values without changing the export envelope.
    """

    SINGLE_CHOICE = "single_choice"
    MULTIPLE_CHOICE = "multiple_choice"
    FREE_TEXT = "free_text"
    NAVIGATION_TASK = "navigation_task"


class Severity(StrEnum):
    """Validation and parse finding severity."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


class ImageOrigin(StrEnum):
    """How an image file was produced.

    ``manual_redraw`` is reserved for a later, explicitly marked asset.
    The extractor never assigns it.
    """

    RASTER_ORIGINAL = "raster_original"
    RENDERED_REGION = "rendered_region"
    MANUAL_REDRAW = "manual_redraw"


class BoundingBox(BaseModel):
    """Axis-aligned rectangle in PDF user space."""

    model_config = ConfigDict(extra="forbid")

    x0: float
    y0: float
    x1: float
    y1: float

    @property
    def width(self) -> float:
        """Width of the rectangle."""
        return self.x1 - self.x0

    @property
    def height(self) -> float:
        """Height of the rectangle."""
        return self.y1 - self.y0

    def center(self) -> tuple[float, float]:
        """Return the rectangle center."""
        return ((self.x0 + self.x1) / 2.0, (self.y0 + self.y1) / 2.0)

    def union(self, other: BoundingBox) -> BoundingBox:
        """Return the smallest rectangle containing both boxes."""
        return BoundingBox(
            x0=min(self.x0, other.x0),
            y0=min(self.y0, other.y0),
            x1=max(self.x1, other.x1),
            y1=max(self.y1, other.y1),
        )

    def contains_point(self, x: float, y: float) -> bool:
        """Return whether the point lies inside the rectangle."""
        return self.x0 <= x <= self.x1 and self.y0 <= y <= self.y1


class PageRegion(BaseModel):
    """A text fragment located on one PDF page."""

    model_config = ConfigDict(extra="forbid")

    page: int = Field(ge=1)
    bbox: BoundingBox
    block_ids: list[str] = Field(default_factory=list)


class PageSpan(BaseModel):
    """Vertical band on a page that belongs to one question."""

    model_config = ConfigDict(extra="forbid")

    page: int = Field(ge=1)
    y0: float
    y1: float
