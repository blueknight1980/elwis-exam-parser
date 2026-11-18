"""Source documents and the public source record written to exports."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class SourceDocument(BaseModel):
    """One input document and the facts known about it."""

    model_config = ConfigDict(extra="forbid")

    id: str
    title: str | None = None
    publisher: str | None = None
    source_url: str | None = None
    document_date: date | None = None
    retrieved_at: datetime | None = None
    sha256: str
    filename: str
    local_path: str | None = None
    parser_version: str
    media_type: str = "application/pdf"
    metadata: dict[str, Any] = Field(default_factory=dict)

    def public_dict(self) -> dict[str, Any]:
        """Return export fields without a local filesystem path."""
        payload = self.model_dump(mode="json", exclude={"local_path"})
        return payload
