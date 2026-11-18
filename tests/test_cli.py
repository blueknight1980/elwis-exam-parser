"""Command-line behavior."""

from pathlib import Path

from tests.conftest import write_choice_pdf
from typer.testing import CliRunner

from elwis_parser.cli import app

runner = CliRunner()


def test_help_lists_commands() -> None:
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    for name in ("inspect", "extract", "parse", "validate", "export", "sources"):
        assert name in result.stdout


def test_version() -> None:
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert "elwis-exam-parser 0.1.0" in result.stdout


def test_inspect_missing_file() -> None:
    result = runner.invoke(app, ["inspect", "missing-file.pdf"])
    assert result.exit_code != 0


def test_parse_and_validate_and_export(tmp_path: Path) -> None:
    pdf = tmp_path / "see.pdf"
    write_choice_pdf(pdf)
    output = tmp_path / "parsed"
    parsed = runner.invoke(
        app,
        ["parse", str(pdf), "--exam", "sbf-see", "--output", str(output), "--publisher", "Test"],
    )
    assert parsed.exit_code == 0, parsed.stdout + parsed.stderr
    catalog = output / "catalog.json"
    validated = runner.invoke(app, ["validate", str(catalog)])
    assert validated.exit_code == 0, validated.stdout + validated.stderr
    csv_path = tmp_path / "out.csv"
    exported = runner.invoke(
        app,
        ["export", str(catalog), "--format", "csv", "--output", str(csv_path)],
    )
    assert exported.exit_code == 0, exported.stdout + exported.stderr
    assert csv_path.is_file()


def test_strict_refuses_incomplete_catalog(tmp_path: Path) -> None:
    from tests.pdf_factory import build_pdf

    pdf = tmp_path / "bad.pdf"
    build_pdf(pdf, [["Basisfragen", "1. Zu kurz?", "a. Nur diese"]])
    output = tmp_path / "bad-out"
    result = runner.invoke(
        app,
        ["parse", str(pdf), "--exam", "sbf-see", "--output", str(output), "--strict"],
    )
    assert result.exit_code == 2
    assert not (output / "catalog.json").exists()
    assert (output / "validation.json").exists()


def test_unknown_exam_is_rejected(tmp_path: Path) -> None:
    pdf = tmp_path / "see.pdf"
    write_choice_pdf(pdf)
    result = runner.invoke(
        app,
        ["parse", str(pdf), "--exam", "src", "--output", str(tmp_path / "out")],
    )
    assert result.exit_code == 1
    assert "No parser" in result.stderr


def test_sources_list() -> None:
    result = runner.invoke(app, ["sources", "list"])
    assert result.exit_code == 0
    assert "sbf_see" in result.stdout
    assert "sbf-see-2023-08-01" in result.stdout


def test_export_rejects_unknown_format(tmp_path: Path) -> None:
    catalog = tmp_path / "catalog.json"
    catalog.write_text("{}", encoding="utf-8")
    result = runner.invoke(
        app,
        ["export", str(catalog), "--format", "xml", "--output", str(tmp_path / "out.csv")],
    )
    assert result.exit_code == 1
