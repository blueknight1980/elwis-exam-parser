"""Validation findings and reports."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from elwis_parser.models.common import Severity


class Finding(BaseModel):
    """One structured validation or parse finding."""

    model_config = ConfigDict(extra="forbid")

    code: str
    severity: Severity
    message: str
    entity_type: str | None = None
    entity_id: str | None = None
    source_id: str | None = None
    page: int | None = Field(default=None, ge=1)


class ValidationReport(BaseModel):
    """Aggregate of findings for one parse or one exported document."""

    model_config = ConfigDict(extra="forbid")

    findings: list[Finding] = Field(default_factory=list)

    @property
    def error_count(self) -> int:
        """Number of error findings."""
        return sum(1 for finding in self.findings if finding.severity is Severity.ERROR)

    @property
    def warning_count(self) -> int:
        """Number of warning findings."""
        return sum(1 for finding in self.findings if finding.severity is Severity.WARNING)

    @property
    def info_count(self) -> int:
        """Number of info findings."""
        return sum(1 for finding in self.findings if finding.severity is Severity.INFO)

    @property
    def status(self) -> str:
        """``failed`` when any error is present, otherwise ``passed``."""
        if self.error_count:
            return "failed"
        return "passed"

    def summary(self) -> dict[str, object]:
        """Machine-readable counts plus the finding list."""
        return {
            "status": self.status,
            "errors": self.error_count,
            "warnings": self.warning_count,
            "info": self.info_count,
            "findings": [finding.model_dump(mode="json") for finding in self.findings],
        }
