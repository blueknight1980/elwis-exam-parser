"""Versioned JSON export document."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from elwis_parser.models.catalog import Catalog
from elwis_parser.models.image import ImageAsset
from elwis_parser.models.question import Question


class ExportDocument(BaseModel):
    """Stable JSON document for downstream applications."""

    model_config = ConfigDict(extra="forbid")

    schema_version: str
    parser_version: str
    exported_at: datetime
    examination: str
    catalogs: list[Catalog]
    questions: list[Question]
    images: list[ImageAsset]
    sources: list[dict[str, Any]]
    validation: dict[str, Any]
    metadata: dict[str, Any] = Field(default_factory=dict)
