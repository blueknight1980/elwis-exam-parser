"""Known examinations and source records.

Download URLs are included only when a fetch during development returned a
PDF. Checksums belong to the bytes retrieved on the recorded date. ELWIS can
replace a file; a mismatch means the pin must be reviewed, not ignored.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ExaminationSpec:
    """One examination the data model knows about."""

    id: str
    name: str
    parser_implemented: bool
    notes: str


@dataclass(frozen=True)
class SourceRecord:
    """A catalog file that can be supplied locally or downloaded."""

    id: str
    examination_id: str
    title: str
    publisher: str
    download_url: str | None
    filename: str
    document_date: str | None
    sha256: str | None
    verified_on: str | None
    notes: str


EXAMINATIONS: tuple[ExaminationSpec, ...] = (
    ExaminationSpec(
        id="sbf_see",
        name="Sportbootführerschein See",
        parser_implemented=True,
        notes=(
            "Single-choice sections and navigation tasks are parsed from the "
            "August 2023 ELWIS PDF layout that was inspected in this project."
        ),
    ),
    ExaminationSpec(
        id="sbf_binnen",
        name="Sportbootführerschein Binnen",
        parser_implemented=True,
        notes=(
            "Basis, inland, and sailing sections are parsed from the August "
            "2023 ELWIS PDF layout that was inspected in this project."
        ),
    ),
    ExaminationSpec(
        id="src",
        name="SRC",
        parser_implemented=False,
        notes="No parser. The question format is not assumed from the SBF catalogs.",
    ),
    ExaminationSpec(
        id="ubi",
        name="UBI",
        parser_implemented=False,
        notes="No parser. The question format is not assumed from the SBF catalogs.",
    ),
    ExaminationSpec(
        id="lrc",
        name="LRC",
        parser_implemented=False,
        notes="No parser. The question format is not assumed from the SBF catalogs.",
    ),
    ExaminationSpec(
        id="fkn",
        name="FKN",
        parser_implemented=False,
        notes="No parser. The question format is not assumed from the SBF catalogs.",
    ),
    ExaminationSpec(
        id="sks",
        name="SKS",
        parser_implemented=False,
        notes="Reserved for free-text questions and sample answers. No parser yet.",
    ),
)

# SHA-256 values are of the PDFs fetched from www.elwis.de on 2026-11-15.
VERIFIED_SOURCES: tuple[SourceRecord, ...] = (
    SourceRecord(
        id="sbf-see-2023-08-01",
        examination_id="sbf_see",
        title=(
            "Fragen- und Antwortenkatalog für den amtlichen Sportbootführerschein "
            "mit dem Geltungsbereich Seeschifffahrtsstraßen"
        ),
        publisher="Wasserstraßen- und Schifffahrtsverwaltung des Bundes",
        download_url=(
            "https://www.elwis.de/DE/Sportschifffahrt/Sportbootfuehrerscheine/"
            "Fragenkatalog-See/Fragenkatalog-See-August-2023.pdf"
            "?__blob=publicationFile&v=13"
        ),
        filename="Fragenkatalog-See-August-2023.pdf",
        document_date="2023-08-01",
        sha256="34b5b68917e964f577223004bc3be9e2d513e23d20792853052a01c3d80226da",
        verified_on="2026-11-15",
        notes=(
            "The publication-file URL returned a PDF on 2026-11-15. "
            "The v= parameter can change when ELWIS replaces the file. "
            "The path without __blob=publicationFile is an HTML page, not the PDF."
        ),
    ),
    SourceRecord(
        id="sbf-binnen-2023-08-01",
        examination_id="sbf_binnen",
        title=(
            "Fragen- und Antwortenkatalog für den amtlichen Sportbootführerschein "
            "mit dem Geltungsbereich Binnenschifffahrtsstraßen"
        ),
        publisher="Wasserstraßen- und Schifffahrtsverwaltung des Bundes",
        download_url=(
            "https://www.elwis.de/DE/Sportschifffahrt/Sportbootfuehrerscheine/"
            "Fragenkatalog-Binnen/Fragenkatalog-Binnen-August-2023.pdf"
            "?__blob=publicationFile&v=9"
        ),
        filename="Fragenkatalog-Binnen-August-2023.pdf",
        document_date="2023-08-01",
        sha256="5e03fc0dbf4fb9a22b7dd1875856436cc18adbe8619b1635bb6ef017568ddd70",
        verified_on="2026-11-15",
        notes=(
            "The publication-file URL returned a PDF on 2026-11-15. "
            "The v= parameter can change when ELWIS replaces the file."
        ),
    ),
)

ALLOWED_DOWNLOAD_HOSTS = frozenset({"www.elwis.de"})

_EXAM_BY_ID = {item.id: item for item in EXAMINATIONS}
_SOURCE_BY_ID = {item.id: item for item in VERIFIED_SOURCES}

CLI_EXAM_ALIASES = {
    "sbf-see": "sbf_see",
    "sbf_see": "sbf_see",
    "sbf-binnen": "sbf_binnen",
    "sbf_binnen": "sbf_binnen",
    "src": "src",
    "ubi": "ubi",
    "lrc": "lrc",
    "fkn": "fkn",
    "sks": "sks",
}


def normalize_exam_id(value: str) -> str:
    """Map a CLI examination name to its canonical id."""
    key = value.strip().casefold().replace(" ", "_")
    canonical = CLI_EXAM_ALIASES.get(key)
    if canonical is None:
        known = ", ".join(sorted(CLI_EXAM_ALIASES))
        raise KeyError(f"Unknown examination {value!r}. Known names: {known}")
    return canonical


def get_examination(exam_id: str) -> ExaminationSpec:
    """Return one examination specification."""
    try:
        return _EXAM_BY_ID[exam_id]
    except KeyError as exc:
        raise KeyError(f"Unknown examination id {exam_id!r}") from exc


def get_source(source_id: str) -> SourceRecord:
    """Return one verified source record."""
    try:
        return _SOURCE_BY_ID[source_id]
    except KeyError as exc:
        raise KeyError(f"Unknown source id {source_id!r}") from exc
