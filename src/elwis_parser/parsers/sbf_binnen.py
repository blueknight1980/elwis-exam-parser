"""Sportbootführerschein Binnen parser."""

from __future__ import annotations

from elwis_parser.models import ExamParseResult, Extraction, SourceDocument
from elwis_parser.parsers.base import BaseExamParser
from elwis_parser.parsers.sbf_layout import parse_sbf


class SbfBinnenParser(BaseExamParser):
    """Parse the SBF Binnen catalog layout."""

    examination_id = "sbf_binnen"

    def parse(self, source: SourceDocument, extraction: Extraction) -> ExamParseResult:
        """Parse basis questions, inland questions, and sailing questions."""
        return parse_sbf(source, extraction, self.examination_id)
