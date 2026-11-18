"""Optional checks against the official PDFs.

These tests run only when the files are present locally. They are not part of
CI and they do not claim a result when the files are absent.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from tests.conftest import BINNEN_PDF, SEE_PDF

from elwis_parser.config import Settings
from elwis_parser.pipeline import parse_pdf
from elwis_parser.sources.registry import VERIFIED_SOURCES
from elwis_parser.utils.hashing import sha256_file

pytestmark = pytest.mark.integration

SEE_SOURCE = next(item for item in VERIFIED_SOURCES if item.id == "sbf-see-2023-08-01")
BINNEN_SOURCE = next(item for item in VERIFIED_SOURCES if item.id == "sbf-binnen-2023-08-01")


def _counts(path: Path, exam: str, tmp_path: Path) -> dict[str, int]:
    destination, report = parse_pdf(
        path,
        exam,
        tmp_path / exam,
        settings=Settings(),
        source_url="https://www.elwis.de/",
        overwrite=True,
    )
    assert report.error_count == 0, [
        finding.message for finding in report.findings if finding.severity.value == "error"
    ]
    import json

    payload = json.loads(destination.read_text(encoding="utf-8"))
    counts: dict[str, int] = {}
    for catalog in payload["catalogs"]:
        roles = {}
        for question in payload["questions"]:
            if catalog["id"] not in question["catalog_ids"]:
                continue
            role = question["metadata"].get("navigation_role", question["question_type"])
            roles[role] = roles.get(role, 0) + 1
        counts[catalog["id"]] = roles
    return counts


@pytest.mark.skipif(not SEE_PDF.is_file(), reason="Official SBF See PDF is not in data/sources")
def test_official_see_catalog(tmp_path: Path) -> None:
    assert sha256_file(SEE_PDF) == SEE_SOURCE.sha256
    counts = _counts(SEE_PDF, "sbf-see", tmp_path)
    assert counts["sbf_see_basis"]["single_choice"] == 72
    assert counts["sbf_see_specific"]["single_choice"] == 213
    assert counts["sbf_see_navigation"]["prompt_pool"] == 15
    assert counts["sbf_see_navigation"]["task_variant"] == 15


@pytest.mark.skipif(
    not BINNEN_PDF.is_file(), reason="Official SBF Binnen PDF is not in data/sources"
)
def test_official_binnen_catalog(tmp_path: Path) -> None:
    assert sha256_file(BINNEN_PDF) == BINNEN_SOURCE.sha256
    counts = _counts(BINNEN_PDF, "sbf-binnen", tmp_path)
    assert counts["sbf_binnen_basis"]["single_choice"] == 72
    assert counts["sbf_binnen_specific"]["single_choice"] == 181
    assert counts["sbf_binnen_sailing"]["single_choice"] == 47


@pytest.mark.skipif(
    not (SEE_PDF.is_file() and BINNEN_PDF.is_file()),
    reason="Both official PDFs are required",
)
def test_basis_questions_share_ids(tmp_path: Path) -> None:
    from elwis_parser.exporters.json_exporter import read_export

    see_path, _see = parse_pdf(SEE_PDF, "sbf-see", tmp_path / "see", settings=Settings())
    binnen_path, _binnen = parse_pdf(
        BINNEN_PDF, "sbf-binnen", tmp_path / "binnen", settings=Settings()
    )
    see = read_export(see_path)
    binnen = read_export(binnen_path)
    see_basis = {item.id for item in see.questions if "sbf_see_basis" in item.catalog_ids}
    binnen_basis = {item.id for item in binnen.questions if "sbf_binnen_basis" in item.catalog_ids}
    assert len(see_basis & binnen_basis) == 72
