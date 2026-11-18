"""Validation rules that do not need a PDF."""

from elwis_parser.models import (
    Answer,
    Catalog,
    ExamParseResult,
    Question,
    QuestionType,
    SourceDocument,
    SourceReference,
)
from elwis_parser.validation import validate_result


def _question(**overrides: object) -> Question:
    payload: dict[str, object] = {
        "id": "q1",
        "original_number": "1",
        "question_type": QuestionType.SINGLE_CHOICE,
        "text": "Frage?",
        "answers": [
            Answer(
                id="q1:answer:1",
                text="a",
                original_position=1,
                is_correct=True,
                metadata={"label": "a"},
            ),
            Answer(id="q1:answer:2", text="b", original_position=2, metadata={"label": "b"}),
            Answer(id="q1:answer:3", text="c", original_position=3, metadata={"label": "c"}),
            Answer(id="q1:answer:4", text="d", original_position=4, metadata={"label": "d"}),
        ],
        "correct_answer_ids": ["q1:answer:1"],
        "catalog_ids": ["sbf_see_basis"],
        "source_reference": SourceReference(source_id="src:1", page=2, original_number="1"),
    }
    payload.update(overrides)
    return Question.model_validate(payload)


def test_duplicate_ids_and_empty_text_are_errors() -> None:
    source = SourceDocument(
        id="src:1",
        sha256="abc",
        filename="a.pdf",
        parser_version="0.1.0",
        publisher="Verlag",
        title="Titel",
        metadata={"answer_a_stated_in_document": True},
    )
    empty = _question(id="q1", text="  ")
    duplicate = _question(id="q1", original_number="2")
    result = ExamParseResult(
        examination_id="sbf_see",
        catalogs=[
            Catalog(
                id="sbf_see_basis",
                examination_id="sbf_see",
                name="Basisfragen",
                source_id="src:1",
                question_ids=["q1", "q1"],
            )
        ],
        questions=[empty, duplicate],
        sources=[source],
    )
    report = validate_result(result)
    codes = {finding.code for finding in report.findings}
    assert "EMPTY_QUESTION_TEXT" in codes
    assert "DUPLICATE_ID" in codes
    assert report.status == "failed"


def test_missing_image_reference_is_an_error() -> None:
    source = SourceDocument(
        id="src:1",
        sha256="abc",
        filename="a.pdf",
        parser_version="0.1.0",
        publisher="Verlag",
        title="Titel",
        metadata={"answer_a_stated_in_document": True},
    )
    question = _question(image_ids=["missing"])
    result = ExamParseResult(
        examination_id="sbf_see",
        catalogs=[
            Catalog(
                id="sbf_see_basis",
                examination_id="sbf_see",
                name="Basisfragen",
                source_id="src:1",
                question_ids=[question.id],
            )
        ],
        questions=[question],
        sources=[source],
    )
    report = validate_result(result)
    assert any(finding.code == "MISSING_IMAGE_REFERENCE" for finding in report.findings)
