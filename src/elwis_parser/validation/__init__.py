"""Validation reports."""

from elwis_parser.models import Finding, Severity, ValidationReport
from elwis_parser.validation.validator import validate_result

__all__ = ["Finding", "Severity", "ValidationReport", "validate_result"]
