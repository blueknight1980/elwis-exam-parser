"""Model behavior."""

from datetime import date, datetime

import pytest
from pydantic import ValidationError

from elwis_parser.models import (
    Answer,
    BoundingBox,
    Catalog,
    ImageAsset,
    ImageOrigin,
    Question,
    QuestionType,
    SourceReference,
)


def _reference() -> SourceReference:
    return SourceReference(source_id="src:test", page=1, pages=[1], original_number="1")


def test_single_choice_question_keeps_answer_order() -> None:
    answers = [
        Answer(id="q:answer:1", text="richtig", original_position=1, is_correct=True),
        Answer(id="q:answer:2", text="falsch", original_position=2),
    ]
    question = Question(
        id="q",
        original_number="1",
        question_type=QuestionType.SINGLE_CHOICE,
        text="Synthetische Frage?",
        answers=answers,
        correct_answer_ids=["q:answer:1"],
        catalog_ids=["sbf_see_basis"],
        source_reference=_reference(),
    )
    assert [answer.original_position for answer in question.answers] == [1, 2]
    assert question.answers[0].is_correct is True


def test_answer_position_must_be_positive() -> None:
    with pytest.raises(ValidationError):
        Answer(id="a", text="x", original_position=0)


def test_free_text_question_allows_no_answers() -> None:
    question = Question(
        id="free",
        original_number="1",
        question_type=QuestionType.FREE_TEXT,
        text="Beschreiben Sie das Zeichen.",
        source_reference=_reference(),
    )
    assert question.answers == []
    assert question.correct_answer_ids == []


def test_navigation_question_is_not_single_choice() -> None:
    question = Question(
        id="nav",
        original_number="1",
        question_type=QuestionType.NAVIGATION_TASK,
        text="Szenario",
        source_reference=_reference(),
    )
    assert question.question_type is QuestionType.NAVIGATION_TASK


def test_catalog_can_list_several_questions() -> None:
    catalog = Catalog(
        id="sbf_see_basis",
        examination_id="sbf_see",
        name="Basisfragen",
        version="2023-08-01",
        source_id="src:test",
        question_ids=["a", "b"],
    )
    assert catalog.question_ids == ["a", "b"]


def test_image_origin_includes_manual_redraw_for_later_assets() -> None:
    image = ImageAsset(
        id="img",
        filename="a.png",
        relative_path="images/a.png",
        mime_type="image/png",
        sha256="abc",
        source_page=1,
        source_document_id="src:test",
        bounding_box=BoundingBox(x0=0, y0=0, x1=1, y1=1),
        width=1,
        height=1,
        origin=ImageOrigin.MANUAL_REDRAW,
    )
    assert image.origin is ImageOrigin.MANUAL_REDRAW


def test_source_document_public_dict_hides_local_path() -> None:
    from elwis_parser.models import SourceDocument

    source = SourceDocument(
        id="src:abc",
        title="Titel",
        sha256="abc",
        filename="catalog.pdf",
        local_path="/tmp/secret/catalog.pdf",
        parser_version="0.1.0",
        document_date=date(2023, 8, 1),
        retrieved_at=datetime.fromisoformat("2026-11-15T00:00:00+00:00"),
    )
    public = source.public_dict()
    assert "local_path" not in public
    assert public["filename"] == "catalog.pdf"
