"""Parser lookup."""

from __future__ import annotations

from elwis_parser.exceptions import ConfigurationError
from elwis_parser.parsers.base import BaseExamParser
from elwis_parser.parsers.sbf_binnen import SbfBinnenParser
from elwis_parser.parsers.sbf_see import SbfSeeParser
from elwis_parser.sources.registry import get_examination

_PARSERS: dict[str, type[BaseExamParser]] = {
    "sbf_see": SbfSeeParser,
    "sbf_binnen": SbfBinnenParser,
}


def get_parser(examination_id: str) -> BaseExamParser:
    """Return the parser for an examination, or explain why none exists."""
    parser_type = _PARSERS.get(examination_id)
    if parser_type is None:
        try:
            spec = get_examination(examination_id)
        except KeyError as exc:
            raise ConfigurationError(str(exc)) from exc
        raise ConfigurationError(
            f"No parser is implemented for {spec.name} ({spec.id}). {spec.notes}"
        )
    return parser_type()
