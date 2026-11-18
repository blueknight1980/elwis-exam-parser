"""Answer options."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class Answer(BaseModel):
    """One answer option in its original position."""

    model_config = ConfigDict(extra="forbid")

    id: str
    text: str
    image_ids: list[str] = Field(default_factory=list)
    original_position: int = Field(ge=1)
    is_correct: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)
