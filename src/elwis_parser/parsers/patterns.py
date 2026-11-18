"""Patterns for the ELWIS sport-boat catalog PDFs inspected in this project."""

from __future__ import annotations

import re

QUESTION_RE = re.compile(r"^(\d+)\.\s+(\S.*)$")
ANSWER_RE = re.compile(r"^([a-dA-D])[.)]\s+(\S.*)$")
COORDINATE_RE = re.compile(r"^\d+\.\s+N\d+°")
TASK_RE = re.compile(r"^Navigationsaufgabe\s+(\d+)\s*$")
PART_RE = re.compile(r"^\d+\.$")
RANGE_RE = re.compile(
    r"(Basisfragen|Spezifische Fragen See|Spezifische Fragen Binnen|"
    r"Spezifische Fragen Segeln|Navigationsaufgaben)"
    r".*?Frage\s+(\d+)\s+bis\s+Frage\s+(\d+)",
    re.IGNORECASE,
)
POOL_RE = re.compile(
    r"Aus den nachfolgenden\s+(\d+)\s+Fragen werden jeweils\s+(\d+)\s+Fragen",
    re.IGNORECASE,
)
EDITION_RE = re.compile(
    r"(?:Anzuwenden ab dem|Stand:)\s+(\d{1,2})\.?\s+([A-Za-zäöüÄÖÜ]+)\s+(\d{4})"
)
PAGE_COUNT_RE = re.compile(r"^\d+ von \d+$")
PRINT_STAMP_RE = re.compile(r"^\d{2}\.\d{2}\.\d{4}, \d{2}:\d{2}$")

HEADINGS = {
    "basisfragen",
    "spezifische fragen see",
    "spezifische fragen binnen",
    "spezifische fragen segeln",
    "navigationsaufgaben",
}

BREADCRUMBS = HEADINGS | {
    "elwis",
    "sportschifffahrt",
    "sportbootführerscheine",
    "fragenkatalog see",
    "fragenkatalog binnen",
}

MONTHS = {
    "januar": 1,
    "februar": 2,
    "märz": 3,
    "maerz": 3,
    "april": 4,
    "mai": 5,
    "juni": 6,
    "juli": 7,
    "august": 8,
    "september": 9,
    "oktober": 10,
    "november": 11,
    "dezember": 12,
}

TABLE_LABELS = {"Nummer", "Aufgabenstellung", "Ergebnis"}

# catalog id, stable question-id prefix, display name
SectionTarget = tuple[str, str, str]

SECTION_TARGETS: dict[str, dict[str, SectionTarget]] = {
    "basisfragen": {
        "sbf_see": ("sbf_see_basis", "sbf_basis", "Basisfragen"),
        "sbf_binnen": ("sbf_binnen_basis", "sbf_basis", "Basisfragen"),
    },
    "spezifische fragen see": {
        "sbf_see": ("sbf_see_specific", "sbf_see_specific", "Spezifische Fragen See"),
    },
    "spezifische fragen binnen": {
        "sbf_binnen": ("sbf_binnen_specific", "sbf_binnen_specific", "Spezifische Fragen Binnen"),
    },
    "spezifische fragen segeln": {
        "sbf_binnen": ("sbf_binnen_sailing", "sbf_binnen_sailing", "Spezifische Fragen Segeln"),
    },
    "navigationsaufgaben": {
        "sbf_see": ("sbf_see_navigation", "sbf_see_navigation", "Navigationsaufgaben"),
    },
}
