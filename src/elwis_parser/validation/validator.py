"""Validation rules for parsed catalogs."""

from __future__ import annotations

from collections.abc import Mapping

from elwis_parser.models import (
    Catalog,
    ExamParseResult,
    Finding,
    ImageAsset,
    Question,
    QuestionType,
    Severity,
    SourceDocument,
    ValidationReport,
)


def validate_result(result: ExamParseResult) -> ValidationReport:
    """Validate questions, catalogs, images, and document-stated counts."""
    findings: list[Finding] = list(result.findings)
    questions = result.questions
    catalogs = {catalog.id: catalog for catalog in result.catalogs}
    images = {image.id: image for image in result.images}
    sources = {source.id: source for source in result.sources}

    _unique(findings, [question.id for question in questions], "question")
    _unique(findings, [catalog.id for catalog in result.catalogs], "catalog")
    _unique(findings, [image.id for image in result.images], "image")
    answer_ids = [answer.id for question in questions for answer in question.answers]
    _unique(findings, answer_ids, "answer")

    rule_stated = any(
        bool(source.metadata.get("answer_a_stated_in_document")) for source in result.sources
    )
    single_choice = [
        question for question in questions if question.question_type is QuestionType.SINGLE_CHOICE
    ]
    if single_choice and rule_stated:
        findings.append(
            Finding(
                code="CORRECTNESS_RULE_FROM_DOCUMENT",
                severity=Severity.INFO,
                message="The document states that answer a is the correct answer. That rule was applied.",
                entity_type="examination",
                entity_id=result.examination_id,
            )
        )
    if single_choice and not rule_stated:
        findings.append(
            Finding(
                code="CORRECTNESS_RULE_NOT_IN_DOCUMENT",
                severity=Severity.WARNING,
                message=(
                    "The document does not state which answer is correct. "
                    "No answer was marked correct."
                ),
                entity_type="examination",
                entity_id=result.examination_id,
            )
        )

    for question in questions:
        _validate_question(findings, question, catalogs, images, sources, rule_stated)
    for catalog in result.catalogs:
        _validate_catalog(findings, catalog, questions)
    for image in result.images:
        _validate_image(findings, image, questions)
    for source in result.sources:
        _validate_source(findings, source)
    return ValidationReport(findings=findings)


def _validate_question(
    findings: list[Finding],
    question: Question,
    catalogs: Mapping[str, Catalog],
    images: Mapping[str, ImageAsset],
    sources: Mapping[str, SourceDocument],
    rule_stated: bool,
) -> None:
    page = question.source_reference.page
    source_id = question.source_reference.source_id
    if not question.original_number.strip():
        _add(
            findings,
            "MISSING_QUESTION_NUMBER",
            Severity.ERROR,
            "Question number is empty.",
            question,
            page,
        )
    if not question.text.strip():
        _add(
            findings,
            "EMPTY_QUESTION_TEXT",
            Severity.ERROR,
            "Question text is empty.",
            question,
            page,
        )
    if source_id not in sources:
        _add(
            findings,
            "MISSING_SOURCE_REFERENCE",
            Severity.ERROR,
            "Question does not reference a known source document.",
            question,
            page,
        )
    for catalog_id in question.catalog_ids:
        if catalog_id not in catalogs:
            _add(
                findings,
                "INVALID_CATALOG_REFERENCE",
                Severity.ERROR,
                f"Unknown catalog {catalog_id}.",
                question,
                page,
            )
    for image_id in question.image_ids:
        if image_id not in images:
            _add(
                findings,
                "MISSING_IMAGE_REFERENCE",
                Severity.ERROR,
                f"Unknown image {image_id}.",
                question,
                page,
            )
    if question.question_type is QuestionType.SINGLE_CHOICE:
        _validate_single_choice(findings, question, rule_stated)
    if question.metadata.get("navigation_role") == "task_variant":
        parts = question.navigation.parts if question.navigation else []
        if not parts:
            _add(
                findings,
                "INCOMPLETE_QUESTION",
                Severity.ERROR,
                "Navigation task has no parts.",
                question,
                page,
            )
    correct_from_flags = [answer.id for answer in question.answers if answer.is_correct]
    if correct_from_flags != question.correct_answer_ids:
        _add(
            findings,
            "INCONSISTENT_CORRECTNESS",
            Severity.ERROR,
            "correct_answer_ids does not match the answer flags.",
            question,
            page,
        )
    for answer in question.answers:
        if not answer.text.strip():
            _add(
                findings,
                "EMPTY_ANSWER_TEXT",
                Severity.ERROR,
                f"Answer {answer.original_position} is empty.",
                question,
                page,
            )


def _validate_single_choice(
    findings: list[Finding],
    question: Question,
    rule_stated: bool,
) -> None:
    page = question.source_reference.page
    if len(question.answers) != 4:
        _add(
            findings,
            "UNEXPECTED_ANSWER_COUNT",
            Severity.ERROR,
            f"Single-choice question has {len(question.answers)} answers; the SBF layout uses 4.",
            question,
            page,
        )
        return
    labels = [str(answer.metadata.get("label", "")) for answer in question.answers]
    if labels != ["a", "b", "c", "d"]:
        _add(
            findings,
            "UNEXPECTED_ANSWER_LABELS",
            Severity.WARNING,
            f"Answer labels are {labels}, expected a, b, c, d.",
            question,
            page,
        )
    if rule_stated and len(question.correct_answer_ids) != 1:
        _add(
            findings,
            "SINGLE_CHOICE_CORRECT_COUNT",
            Severity.ERROR,
            "Single-choice question does not have exactly one correct answer.",
            question,
            page,
        )


def _validate_catalog(
    findings: list[Finding],
    catalog: object,
    questions: list[Question],
) -> None:
    from elwis_parser.models import Catalog

    if not isinstance(catalog, Catalog):
        return
    members = [question for question in questions if catalog.id in question.catalog_ids]
    known = {question.id for question in questions}
    for question_id in catalog.question_ids:
        if question_id not in known:
            findings.append(
                Finding(
                    code="INVALID_CATALOG_REFERENCE",
                    severity=Severity.ERROR,
                    message=f"Catalog {catalog.id} lists unknown question {question_id}.",
                    entity_type="catalog",
                    entity_id=catalog.id,
                    source_id=catalog.source_id,
                )
            )
    counted = [
        question
        for question in members
        if question.metadata.get("navigation_role") != "task_variant"
    ]
    numbers: list[int] = []
    seen: set[int] = set()
    for question in counted:
        if not question.original_number.isdigit():
            findings.append(
                Finding(
                    code="QUESTION_NUMBER_GAP",
                    severity=Severity.WARNING,
                    message=f"Question number {question.original_number} is not numeric.",
                    entity_type="question",
                    entity_id=question.id,
                    source_id=catalog.source_id,
                    page=question.source_reference.page,
                )
            )
            continue
        number = int(question.original_number)
        if number in seen:
            findings.append(
                Finding(
                    code="DUPLICATE_QUESTION_NUMBER",
                    severity=Severity.ERROR,
                    message=f"Duplicate question number {number} in {catalog.id}.",
                    entity_type="question",
                    entity_id=question.id,
                    source_id=catalog.source_id,
                    page=question.source_reference.page,
                )
            )
        seen.add(number)
        numbers.append(number)
    ordered = sorted(seen)
    for previous, current in zip(ordered, ordered[1:], strict=False):
        if current != previous + 1:
            findings.append(
                Finding(
                    code="QUESTION_NUMBER_GAP",
                    severity=Severity.WARNING,
                    message=f"Question numbers jump from {previous} to {current} in {catalog.id}.",
                    entity_type="catalog",
                    entity_id=catalog.id,
                    source_id=catalog.source_id,
                )
            )
    stated_first = catalog.metadata.get("stated_first")
    stated_last = catalog.metadata.get("stated_last")
    if isinstance(stated_first, int) and isinstance(stated_last, int):
        expected = set(range(stated_first, stated_last + 1))
        if seen != expected:
            findings.append(
                Finding(
                    code="CATALOG_COUNT_MISMATCH",
                    severity=Severity.ERROR,
                    message=(
                        f"{catalog.name} states questions {stated_first}-{stated_last} "
                        f"({len(expected)} items) but {len(seen)} matching numbers were parsed."
                    ),
                    entity_type="catalog",
                    entity_id=catalog.id,
                    source_id=catalog.source_id,
                )
            )
    texts: dict[str, str] = {}
    for question in counted:
        normalized = " ".join(question.text.split()).casefold()
        if not normalized:
            continue
        earlier = texts.get(normalized)
        if earlier is not None:
            findings.append(
                Finding(
                    code="DUPLICATE_QUESTION_TEXT",
                    severity=Severity.WARNING,
                    message="Two questions in the catalog have the same text.",
                    entity_type="question",
                    entity_id=question.id,
                    source_id=catalog.source_id,
                    page=question.source_reference.page,
                )
            )
        texts[normalized] = question.id
    stated_parts = catalog.metadata.get("stated_parts_per_task")
    if isinstance(stated_parts, int):
        for question in members:
            if (
                question.metadata.get("navigation_role") != "task_variant"
                or not question.navigation
            ):
                continue
            count = len(question.navigation.parts)
            if count != stated_parts:
                findings.append(
                    Finding(
                        code="NAVIGATION_PART_COUNT",
                        severity=Severity.ERROR,
                        message=(
                            f"Navigationsaufgabe {question.original_number} has {count} parts; "
                            f"the document states {stated_parts}."
                        ),
                        entity_type="question",
                        entity_id=question.id,
                        source_id=catalog.source_id,
                        page=question.source_reference.page,
                    )
                )
    stated_variants = catalog.metadata.get("stated_variant_numbers")
    if isinstance(stated_variants, list) and all(isinstance(item, str) for item in stated_variants):
        parsed = [
            question.original_number
            for question in members
            if question.metadata.get("navigation_role") == "task_variant"
        ]
        if parsed != stated_variants:
            findings.append(
                Finding(
                    code="NAVIGATION_VARIANT_MISMATCH",
                    severity=Severity.ERROR,
                    message="Parsed navigation tasks do not match the task list in the document.",
                    entity_type="catalog",
                    entity_id=catalog.id,
                    source_id=catalog.source_id,
                )
            )


def _validate_image(
    findings: list[Finding],
    image: ImageAsset,
    questions: list[Question],
) -> None:
    known = {question.id for question in questions}
    for question_id in image.associated_question_ids:
        if question_id not in known:
            findings.append(
                Finding(
                    code="MISSING_IMAGE_REFERENCE",
                    severity=Severity.ERROR,
                    message=f"Image {image.id} references unknown question {question_id}.",
                    entity_type="image",
                    entity_id=image.id,
                    source_id=image.source_document_id,
                    page=image.source_page,
                )
            )
    path = image.relative_path
    if path.startswith("/") or ".." in path.split("/"):
        findings.append(
            Finding(
                code="UNSAFE_IMAGE_PATH",
                severity=Severity.ERROR,
                message=f"Image path is not a relative path inside the export: {path}",
                entity_type="image",
                entity_id=image.id,
                source_id=image.source_document_id,
                page=image.source_page,
            )
        )


def _validate_source(findings: list[Finding], source: object) -> None:
    from elwis_parser.models import SourceDocument

    if not isinstance(source, SourceDocument):
        return
    if not source.sha256 or not source.filename or not source.id:
        findings.append(
            Finding(
                code="INCOMPLETE_SOURCE",
                severity=Severity.ERROR,
                message="Source document is missing id, filename, or checksum.",
                entity_type="source",
                entity_id=source.id,
                source_id=source.id,
            )
        )
    if not source.publisher:
        findings.append(
            Finding(
                code="PUBLISHER_NOT_SET",
                severity=Severity.WARNING,
                message="Source publisher is not set.",
                entity_type="source",
                entity_id=source.id,
                source_id=source.id,
            )
        )
    if not source.title:
        findings.append(
            Finding(
                code="SOURCE_TITLE_NOT_SET",
                severity=Severity.WARNING,
                message="Source title is not set.",
                entity_type="source",
                entity_id=source.id,
                source_id=source.id,
            )
        )
    if not source.source_url:
        findings.append(
            Finding(
                code="SOURCE_URL_NOT_SET",
                severity=Severity.INFO,
                message="No source URL was configured for this local file.",
                entity_type="source",
                entity_id=source.id,
                source_id=source.id,
            )
        )


def _unique(findings: list[Finding], values: list[str], entity_type: str) -> None:
    seen: set[str] = set()
    for value in values:
        if value in seen:
            findings.append(
                Finding(
                    code="DUPLICATE_ID",
                    severity=Severity.ERROR,
                    message=f"Duplicate {entity_type} id {value}.",
                    entity_type=entity_type,
                    entity_id=value,
                )
            )
        seen.add(value)


def _add(
    findings: list[Finding],
    code: str,
    severity: Severity,
    message: str,
    question: Question,
    page: int | None,
) -> None:
    findings.append(
        Finding(
            code=code,
            severity=severity,
            message=message,
            entity_type="question",
            entity_id=question.id,
            source_id=question.source_reference.source_id,
            page=page,
        )
    )
