"""Parser interface.

Parsers receive an already extracted PDF. They do not open files and they do
not decide the JSON envelope.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from elwis_parser.models import ExamParseResult, Extraction, SourceDocument


class BaseExamParser(ABC):
    """Parse one examination from a technical extraction."""

    examination_id: str

    @abstractmethod
    def parse(self, source: SourceDocument, extraction: Extraction) -> ExamParseResult:
        """Return catalogs and questions for ``source``."""
