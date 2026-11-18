"""Shared pytest helpers."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pytest
from tests.pdf_factory import build_pdf

from elwis_parser.config import Settings

OFFICIAL_DIR = Path("data/sources")
SEE_PDF = OFFICIAL_DIR / "Fragenkatalog-See-August-2023.pdf"
BINNEN_PDF = OFFICIAL_DIR / "Fragenkatalog-Binnen-August-2023.pdf"


@pytest.fixture
def settings() -> Settings:
    """Default resource limits."""
    return Settings()


@pytest.fixture
def fixed_time() -> datetime:
    """A clock value that must not affect question ids."""
    return datetime.fromisoformat("2026-11-15T12:00:00+00:00")


def single_choice_pages() -> list[list[str]]:
    """A two-page synthetic SBF-style catalog."""
    return [
        [
            "Basisfragen",
            "Anmerkung:",
            "Antwort a ist immer die richtige.",
            "1. Synthetische Testfrage eins?",
            "a. Erste Antwort",
            "b. Zweite Antwort",
            "c. Dritte Antwort",
            "d. Vierte Antwort",
        ],
        [
            "2. Synthetische Testfrage mit",
            "Zeilenumbruch?",
            "a. Alpha Antwort",
            "b. Beta Antwort",
            "c. Gamma Antwort",
            "d. Delta Antwort",
            "Spezifische Fragen See",
            "3. Frage nach dem Abschnittswechsel?",
            "a. See eins",
            "b. See zwei",
            "c. See drei",
            "d. See vier",
        ],
    ]


def write_choice_pdf(path: Path, *, image: bool = False) -> None:
    """Write the synthetic single-choice catalog."""
    build_pdf(path, single_choice_pages(), image=image, header="SYNTHETIC HEADER")
