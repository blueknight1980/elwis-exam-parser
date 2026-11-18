"""Low-level PDF extraction records.

These models describe the file. They do not decide what a question is.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from elwis_parser.models.common import BoundingBox
from elwis_parser.models.report import Finding


class TextLine(BaseModel):
    """One visual line and the raw characters read from it."""

    model_config = ConfigDict(extra="forbid")

    text: str
    bbox: BoundingBox
    font_size: float | None = None
    font_name: str | None = None


class TextBlock(BaseModel):
    """A PDF text block in reading order."""

    model_config = ConfigDict(extra="forbid")

    id: str
    page: int = Field(ge=1)
    bbox: BoundingBox
    lines: list[TextLine]
    text: str
    raw_text: str
    font_size: float | None = None
    role: str = "body"
    column: int = 0
    reading_order: int = 0


class PageInfo(BaseModel):
    """Geometry of one page."""

    model_config = ConfigDict(extra="forbid")

    number: int = Field(ge=1)
    width: float
    height: float
    rotation: int = 0


class RasterPlacement(BaseModel):
    """A placed embedded raster image. Bytes are saved later."""

    model_config = ConfigDict(extra="forbid")

    xref: int
    page: int = Field(ge=1)
    bbox: BoundingBox
    width: int = Field(ge=0)
    height: int = Field(ge=0)
    digest_hint: str | None = None


class VectorRegion(BaseModel):
    """A cluster of vector drawings that may need a rendered clip."""

    model_config = ConfigDict(extra="forbid")

    id: str
    page: int = Field(ge=1)
    bbox: BoundingBox
    drawing_count: int = Field(ge=1)


class Extraction(BaseModel):
    """Technical extract of one PDF."""

    model_config = ConfigDict(extra="forbid")

    source_id: str
    page_count: int
    metadata: dict[str, str] = Field(default_factory=dict)
    pages: list[PageInfo]
    blocks: list[TextBlock]
    images: list[RasterPlacement]
    vectors: list[VectorRegion]
    anomalies: list[Finding] = Field(default_factory=list)
    extra: dict[str, Any] = Field(default_factory=dict)
