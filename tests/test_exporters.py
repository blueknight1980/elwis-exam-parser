"""JSON and CSV exports."""

import json
from pathlib import Path

from tests.conftest import write_choice_pdf

from elwis_parser.exporters.csv_exporter import write_csv
from elwis_parser.exporters.json_exporter import read_export
from elwis_parser.pipeline import parse_pdf


def test_export_is_utf8_and_has_no_local_path(tmp_path: Path, settings, fixed_time) -> None:
    pdf = tmp_path / "see.pdf"
    write_choice_pdf(pdf)
    output = tmp_path / "out"
    destination, report = parse_pdf(
        pdf,
        "sbf-see",
        output,
        settings=settings,
        title="Synthese",
        publisher="Testverlag",
        exported_at=fixed_time,
    )
    raw = destination.read_text(encoding="utf-8")
    payload = json.loads(raw)
    assert payload["schema_version"] == "1.0"
    assert payload["examination"] == "sbf_see"
    assert "local_path" not in raw
    assert str(pdf) not in raw
    for image in payload["images"]:
        assert image["relative_path"].startswith("images/")
        assert not str(image["relative_path"]).startswith("/")
    again, _report = parse_pdf(
        pdf,
        "sbf_see",
        tmp_path / "out2",
        settings=settings,
        title="Synthese",
        publisher="Testverlag",
        exported_at=fixed_time.replace(year=2030),
    )
    second = json.loads(again.read_text(encoding="utf-8"))
    assert [item["id"] for item in payload["questions"]] == [
        item["id"] for item in second["questions"]
    ]
    loaded = read_export(destination)
    assert "Zeilenumbruch" in loaded.questions[1].text
    assert report.error_count == 0


def test_csv_contains_answers(tmp_path: Path, settings, fixed_time) -> None:
    pdf = tmp_path / "see.pdf"
    write_choice_pdf(pdf)
    destination, _report = parse_pdf(
        pdf,
        "sbf-see",
        tmp_path / "out",
        settings=settings,
        publisher="Testverlag",
        title="Synthese",
        exported_at=fixed_time,
    )
    csv_path = tmp_path / "questions.csv"
    write_csv(read_export(destination), csv_path)
    text = csv_path.read_text(encoding="utf-8")
    assert "Erste Antwort" in text
    assert "question_id" in text.splitlines()[0]
