"""Sportbootführerschein See parser."""

from __future__ import annotations

from elwis_parser.models import ExamParseResult, Extraction, SourceDocument
from elwis_parser.parsers.base import BaseExamParser
from elwis_parser.parsers.sbf_layout import parse_sbf


class SbfSeeParser(BaseExamParser):
    """Parse the SBF See catalog layout."""

    examination_id = "sbf_see"

    def parse(self, source: SourceDocument, extraction: Extraction) -> ExamParseResult:
        """Parse basis questions, sea questions, and navigation tasks."""
        return parse_sbf(source, extraction, self.examination_id)
