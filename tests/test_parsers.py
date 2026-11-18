"""Parser behavior on synthetic layouts."""

from pathlib import Path

from tests.conftest import write_choice_pdf
from tests.pdf_factory import build_pdf

from elwis_parser.config import Settings
from elwis_parser.models import PageSpan, Question, QuestionType, SourceReference
from elwis_parser.parsers.merge import merge_results
from elwis_parser.parsers.sbf_binnen import SbfBinnenParser
from elwis_parser.parsers.sbf_see import SbfSeeParser
from elwis_parser.pdf.backend import open_pdf
from elwis_parser.pdf.extractor import extract_document
from elwis_parser.pdf.images import associate_images, materialize_rasters
from elwis_parser.sources.local import load_local_pdf
from elwis_parser.validation import validate_result


def _parse(path: Path, parser, settings: Settings):
    source = load_local_pdf(path, settings=settings, publisher="Test", title="Synthese")
    document = open_pdf(path, settings)
    try:
        extraction = extract_document(document, source.id)
        result = parser.parse(source, extraction)
        images = materialize_rasters(
            document, extraction.images, source_id=source.id, settings=settings
        )
    finally:
        document.close()
    result.images = [
        asset for asset, _data in images if asset.metadata.get("role") != "page_chrome"
    ]
    result.findings.extend(associate_images(result.questions, result.layouts, result.images))
    return result


def test_see_parser_reads_sections_and_answer_a(tmp_path: Path, settings: Settings) -> None:
    pdf = tmp_path / "see.pdf"
    write_choice_pdf(pdf, image=True)
    result = _parse(pdf, SbfSeeParser(), settings)
    assert [question.original_number for question in result.questions] == ["1", "2", "3"]
    basis = [question for question in result.questions if "sbf_see_basis" in question.catalog_ids]
    specific = [
        question for question in result.questions if "sbf_see_specific" in question.catalog_ids
    ]
    assert [question.original_number for question in basis] == ["1", "2"]
    assert [question.original_number for question in specific] == ["3"]
    first = result.questions[0]
    assert first.answers[0].is_correct is True
    assert first.correct_answer_ids == [first.answers[0].id]
    assert "SYNTHETIC HEADER" not in first.text
    assert "Zeilenumbruch" in result.questions[1].text
    assert result.questions[0].image_ids
    report = validate_result(result)
    assert report.error_count == 0


def test_incomplete_answers_are_not_invented(tmp_path: Path, settings: Settings) -> None:
    pdf = tmp_path / "short.pdf"
    build_pdf(
        pdf,
        [
            [
                "Basisfragen",
                "1. Unvollständige synthetische Frage?",
                "a. Nur eins",
                "b. Nur zwei",
                "c. Nur drei",
            ]
        ],
    )
    result = _parse(pdf, SbfSeeParser(), settings)
    question = result.questions[0]
    assert len(question.answers) == 3
    assert question.correct_answer_ids == []
    assert all(answer.is_correct is False for answer in question.answers)
    report = validate_result(result)
    assert any(finding.code == "UNEXPECTED_ANSWER_COUNT" for finding in report.findings)


def test_navigation_task_is_not_single_choice(tmp_path: Path, settings: Settings) -> None:
    pdf = tmp_path / "nav.pdf"
    build_pdf(
        pdf,
        [
            [
                (37, "Navigationsaufgaben"),
                (
                    37,
                    "Aus den nachfolgenden 1 Fragen werden jeweils 1 Fragen für jede Navigationsaufgabe ausgewählt.",
                ),
                (37, "9. Wie lautet der synthetische Kurs?"),
                (37, "Navigationsaufgabe 1"),
                (72, "Ein synthetisches Boot fährt."),
                (50, "Nummer"),
                (120, "Aufgabenstellung"),
                (360, "Ergebnis"),
                (50, "1."),
                (120, "Wie lautet der synthetische Kurs?"),
                (360, "090 Grad"),
            ]
        ],
    )
    result = _parse(pdf, SbfSeeParser(), settings)
    roles = [question.metadata.get("navigation_role") for question in result.questions]
    assert roles == ["prompt_pool", "task_variant"]
    variant = result.questions[1]
    assert variant.question_type is QuestionType.NAVIGATION_TASK
    assert variant.answers == []
    assert variant.navigation is not None
    assert variant.navigation.parts[0].sample_solution == "090 Grad"
    assert "090" not in variant.navigation.parts[0].prompt


def test_binnen_sailing_section(tmp_path: Path, settings: Settings) -> None:
    pdf = tmp_path / "binnen.pdf"
    build_pdf(
        pdf,
        [
            [
                "Basisfragen",
                "Antwort a ist immer die richtige.",
                "1. Gemeinsame synthetische Basisfrage?",
                "a. Richtig",
                "b. Falsch eins",
                "c. Falsch zwei",
                "d. Falsch drei",
                "Spezifische Fragen Segeln",
                "2. Synthetische Segelfrage?",
                "a. Segel richtig",
                "b. Segel falsch eins",
                "c. Segel falsch zwei",
                "d. Segel falsch drei",
            ]
        ],
    )
    result = _parse(pdf, SbfBinnenParser(), settings)
    assert result.questions[0].catalog_ids == ["sbf_binnen_basis"]
    assert result.questions[1].catalog_ids == ["sbf_binnen_sailing"]


def test_shared_basis_ids_merge(tmp_path: Path, settings: Settings) -> None:
    pdf = tmp_path / "shared.pdf"
    build_pdf(
        pdf,
        [
            [
                "Basisfragen",
                "Antwort a ist immer die richtige.",
                "1. Gemeinsame synthetische Basisfrage?",
                "a. Richtig",
                "b. Falsch eins",
                "c. Falsch zwei",
                "d. Falsch drei",
            ]
        ],
    )
    see = _parse(pdf, SbfSeeParser(), settings)
    binnen = _parse(pdf, SbfBinnenParser(), settings)
    assert see.questions[0].id == binnen.questions[0].id
    merged = merge_results([see, binnen])
    assert len(merged.questions) == 1
    assert set(merged.questions[0].catalog_ids) == {"sbf_see_basis", "sbf_binnen_basis"}


def test_ambiguous_image_span_creates_a_finding() -> None:
    question_a = Question(
        id="a",
        original_number="1",
        question_type=QuestionType.SINGLE_CHOICE,
        text="A",
        source_reference=SourceReference(source_id="src", page=1),
    )
    question_b = Question(
        id="b",
        original_number="2",
        question_type=QuestionType.SINGLE_CHOICE,
        text="B",
        source_reference=SourceReference(source_id="src", page=1),
    )
    from elwis_parser.models import BoundingBox, ImageAsset, ImageOrigin

    image = ImageAsset(
        id="img",
        filename="a.png",
        relative_path="images/a.png",
        mime_type="image/png",
        sha256="abc",
        source_page=1,
        source_document_id="src",
        bounding_box=BoundingBox(x0=0, y0=10, x1=10, y1=20),
        width=10,
        height=10,
        origin=ImageOrigin.RASTER_ORIGINAL,
        metadata={"role": "content"},
    )
    findings = associate_images(
        [question_a, question_b],
        {
            "a": [PageSpan(page=1, y0=0, y1=30)],
            "b": [PageSpan(page=1, y0=0, y1=30)],
        },
        [image],
    )
    assert any(finding.code == "AMBIGUOUS_IMAGE" for finding in findings)
