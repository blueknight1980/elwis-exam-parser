"""Exam questions."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from elwis_parser.models.answer import Answer
from elwis_parser.models.common import QuestionType
from elwis_parser.models.navigation import NavigationDetails
from elwis_parser.models.source import SourceReference


class Question(BaseModel):
    """One catalog question, including navigation tasks."""

    model_config = ConfigDict(extra="forbid")

    id: str
    original_number: str
    question_type: QuestionType
    text: str
    answers: list[Answer] = Field(default_factory=list)
    correct_answer_ids: list[str] = Field(default_factory=list)
    image_ids: list[str] = Field(default_factory=list)
    catalog_ids: list[str] = Field(default_factory=list)
    source_reference: SourceReference
    navigation: NavigationDetails | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
