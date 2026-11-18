"""Catalog membership."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class Catalog(BaseModel):
    """A catalog or section that groups question ids."""

    model_config = ConfigDict(extra="forbid")

    id: str
    examination_id: str
    name: str
    version: str | None = None
    source_id: str
    question_ids: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
