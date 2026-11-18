"""Path checks for output files and downloads."""

from __future__ import annotations

import re
from pathlib import Path

from elwis_parser.exceptions import UsageError

_SAFE_NAME = re.compile(r"[^A-Za-z0-9._-]+")


def safe_filename(name: str) -> str:
    """Return a single path segment derived from ``name``."""
    cleaned = _SAFE_NAME.sub("_", name).strip("._")
    if not cleaned or cleaned in {".", ".."}:
        raise UsageError(f"Unsafe filename: {name!r}")
    return cleaned


def ensure_within(base: Path, candidate: Path) -> Path:
    """Resolve ``candidate`` and require it to stay inside ``base``."""
    base_resolved = base.resolve()
    resolved = candidate.resolve()
    if not resolved.is_relative_to(base_resolved):
        raise UsageError(f"Path escapes the output directory: {candidate}")
    return resolved
