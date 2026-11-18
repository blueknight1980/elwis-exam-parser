"""Runtime limits. Values can be overridden with environment variables."""

from __future__ import annotations

import os
from dataclasses import dataclass


def _int_env(name: str, default: int) -> int:
    raw = os.environ.get(name)
    if raw is None or raw.strip() == "":
        return default
    try:
        return int(raw)
    except ValueError as exc:
        message = f"Environment variable {name} must be an integer"
        raise ValueError(message) from exc


def _float_env(name: str, default: float) -> float:
    raw = os.environ.get(name)
    if raw is None or raw.strip() == "":
        return default
    try:
        return float(raw)
    except ValueError as exc:
        message = f"Environment variable {name} must be a number"
        raise ValueError(message) from exc


@dataclass(frozen=True)
class Settings:
    """Resource limits for downloads and PDF processing."""

    max_pdf_bytes: int = 30 * 1024 * 1024
    max_pdf_pages: int = 1000
    max_download_bytes: int = 30 * 1024 * 1024
    max_image_bytes: int = 80 * 1024 * 1024
    http_timeout_seconds: float = 30.0
    user_agent: str = "elwis-exam-parser/0.1.0 (local catalog extraction)"

    @classmethod
    def from_env(cls) -> Settings:
        """Build settings from the current environment."""
        return cls(
            max_pdf_bytes=_int_env("ELWIS_MAX_PDF_BYTES", 30 * 1024 * 1024),
            max_pdf_pages=_int_env("ELWIS_MAX_PDF_PAGES", 1000),
            max_download_bytes=_int_env("ELWIS_MAX_DOWNLOAD_BYTES", 30 * 1024 * 1024),
            max_image_bytes=_int_env("ELWIS_MAX_IMAGE_BYTES", 80 * 1024 * 1024),
            http_timeout_seconds=_float_env("ELWIS_HTTP_TIMEOUT", 30.0),
        )


DEFAULT_SETTINGS = Settings()
