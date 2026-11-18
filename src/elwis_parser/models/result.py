"""In-memory result of a parse, before export."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from elwis_parser.models.catalog import Catalog
from elwis_parser.models.common import PageSpan
from elwis_parser.models.image import ImageAsset
from elwis_parser.models.question import Question
from elwis_parser.models.report import Finding
from elwis_parser.models.source_document import SourceDocument


class ExamParseResult(BaseModel):
    """Catalogs, questions, and layout spans produced from one document."""

    model_config = ConfigDict(extra="forbid")

    examination_id: str
    catalogs: list[Catalog] = Field(default_factory=list)
    questions: list[Question] = Field(default_factory=list)
    images: list[ImageAsset] = Field(default_factory=list)
    sources: list[SourceDocument] = Field(default_factory=list)
    findings: list[Finding] = Field(default_factory=list)
    layouts: dict[str, list[PageSpan]] = Field(default_factory=dict)
    preamble: list[str] = Field(default_factory=list)
