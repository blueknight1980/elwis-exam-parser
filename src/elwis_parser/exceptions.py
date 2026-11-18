"""Project exceptions and process exit codes."""


class ElwisParserError(Exception):
    """Base error for expected parser failures."""

    exit_code = 3


class UsageError(ElwisParserError):
    """The invocation or a caller-supplied path is invalid."""

    exit_code = 1


class ConfigurationError(ElwisParserError):
    """A source, examination, or download policy is not usable."""

    exit_code = 1


class ValidationFailedError(ElwisParserError):
    """Validation reported one or more errors."""

    exit_code = 2


class SourceError(ElwisParserError):
    """A source file is missing, unreadable, or fails its checksum."""

    exit_code = 3


class PdfError(ElwisParserError):
    """A PDF cannot be opened or processed within the configured limits."""

    exit_code = 3


class ExportError(ElwisParserError):
    """An export file cannot be written."""

    exit_code = 3
