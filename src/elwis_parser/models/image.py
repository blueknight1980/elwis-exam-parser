"""Extracted image files."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from elwis_parser.models.common import BoundingBox, ImageOrigin


class ImageAsset(BaseModel):
    """One placed image and the file written for it."""

    model_config = ConfigDict(extra="forbid")

    id: str
    filename: str
    relative_path: str
    mime_type: str
    sha256: str
    source_page: int = Field(ge=1)
    source_document_id: str
    bounding_box: BoundingBox
    width: int = Field(ge=0)
    height: int = Field(ge=0)
    origin: ImageOrigin
    associated_question_ids: list[str] = Field(default_factory=list)
    associated_answer_ids: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
