"""Provenance for a question or answer."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from elwis_parser.models.common import PageRegion


class SourceReference(BaseModel):
    """Where an extracted item was read."""

    model_config = ConfigDict(extra="forbid")

    source_id: str
    page: int | None = Field(default=None, ge=1)
    pages: list[int] = Field(default_factory=list)
    original_number: str | None = None
    bbox: PageRegion | None = None
    regions: list[PageRegion] = Field(default_factory=list)
    text_block_ids: list[str] = Field(default_factory=list)
