"""Navigation-task structure.

Navigation tasks are not single-choice questions. A task can contain a
scenario, ordered parts, and sample solutions when the source provides them.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class NavigationPart(BaseModel):
    """One numbered part of a navigation task."""

    model_config = ConfigDict(extra="forbid")

    id: str
    label: str
    prompt: str
    sample_solution: str | None = None
    image_ids: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class NavigationDetails(BaseModel):
    """Structured body of a navigation task variant."""

    model_config = ConfigDict(extra="forbid")

    title: str | None = None
    scenario: str = ""
    parts: list[NavigationPart] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
