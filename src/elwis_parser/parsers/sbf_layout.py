"""Shared parser for the SBF See and SBF Binnen PDF layout.

The rules were checked against the official August 2023 ELWIS PDFs fetched
on 2026-11-15. The same markers also parse the synthetic fixtures. Counts and
the answer-a rule are applied only when the document itself states them.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

from elwis_parser.models import (
    Answer,
    Catalog,
    ExamParseResult,
    Extraction,
    PageRegion,
    PageSpan,
    Question,
    QuestionType,
    SourceDocument,
    SourceReference,
)
from elwis_parser.parsers.lines import RawLine, flatten_lines
from elwis_parser.parsers.navigation import TaskBuilder, task_question
from elwis_parser.parsers.patterns import (
    ANSWER_RE,
    BREADCRUMBS,
    COORDINATE_RE,
    EDITION_RE,
    MONTHS,
    PAGE_COUNT_RE,
    POOL_RE,
    PRINT_STAMP_RE,
    QUESTION_RE,
    RANGE_RE,
    SECTION_TARGETS,
    TASK_RE,
    SectionTarget,
)
from elwis_parser.utils.hashing import stable_id
from elwis_parser.utils.text import join_wrapped_lines


@dataclass
class AnswerBuilder:
    """Accumulates one answer option."""

    label: str
    fragments: list[str] = field(default_factory=list)
    regions: list[PageRegion] = field(default_factory=list)
    block_ids: list[str] = field(default_factory=list)


@dataclass
class QuestionBuilder:
    """Accumulates one numbered question."""

    number: str
    section_key: str
    fragments: list[str] = field(default_factory=list)
    regions: list[PageRegion] = field(default_factory=list)
    block_ids: list[str] = field(default_factory=list)
    answers: list[AnswerBuilder] = field(default_factory=list)


@dataclass
class ParseState:
    """Mutable parse state for one document."""

    examination_id: str
    section_key: str | None = None
    question: QuestionBuilder | None = None
    task: TaskBuilder | None = None
    questions: list[Question] = field(default_factory=list)
    preamble: list[str] = field(default_factory=list)
    section_notes: dict[str, list[str]] = field(default_factory=dict)
    ranges: dict[str, tuple[int, int]] = field(default_factory=dict)
    pool_count: int | None = None
    parts_per_task: int | None = None
    answer_a_is_correct: bool = False
    document_date: date | None = None
    publisher: str | None = None
    toc_tasks: list[str] = field(default_factory=list)
    unknown_section: bool = False


def parse_sbf(
    source: SourceDocument,
    extraction: Extraction,
    examination_id: str,
) -> ExamParseResult:
    """Parse an SBF See or SBF Binnen extraction."""
    state = ParseState(examination_id=examination_id)
    lines = flatten_lines(extraction)
    _scan_document_facts(lines, state)
    _apply_document_facts(source, extraction, state)
    for line in lines:
        if _is_chrome(line) or line.role in {"header", "footer"}:
            continue
        heading = line.text.casefold().rstrip(" .:")
        if line.x < 48 and heading in SECTION_TARGETS:
            _close_open(state, source.id)
            if examination_id not in SECTION_TARGETS[heading]:
                state.unknown_section = True
                continue
            state.section_key = heading
            continue
        task_match = TASK_RE.match(line.text)
        if task_match and line.x < 48:
            _close_open(state, source.id)
            state.task = TaskBuilder(number=task_match.group(1))
            state.task.regions.append(line.region())
            state.task.block_ids.append(line.block_id)
            continue
        if task_match and line.x >= 48:
            state.toc_tasks.append(task_match.group(1))
            continue
        if state.task is not None:
            state.task.add_line(line)
            continue
        if COORDINATE_RE.match(line.text) or RANGE_RE.search(line.text):
            _add_note(state, line.text)
            continue
        question_match = QUESTION_RE.match(line.text)
        if question_match and line.x < 60:
            _close_question(state, source.id)
            state.question = QuestionBuilder(
                number=question_match.group(1),
                section_key=state.section_key or "",
            )
            state.question.fragments.append(question_match.group(2))
            state.question.regions.append(line.region())
            state.question.block_ids.append(line.block_id)
            continue
        answer_match = ANSWER_RE.match(line.text)
        if answer_match and state.question is not None:
            builder = AnswerBuilder(label=answer_match.group(1).casefold())
            builder.fragments.append(answer_match.group(2))
            builder.regions.append(line.region())
            builder.block_ids.append(line.block_id)
            state.question.answers.append(builder)
            continue
        _continue_line(state, line)
    _close_open(state, source.id)
    catalogs = _catalogs(state, source)
    for question in state.questions:
        for catalog in catalogs:
            if catalog.id in question.catalog_ids and question.id not in catalog.question_ids:
                catalog.question_ids.append(question.id)
    result = ExamParseResult(
        examination_id=examination_id,
        catalogs=catalogs,
        questions=state.questions,
        sources=[source],
        preamble=state.preamble,
    )
    result.layouts = _layouts(state.questions, extraction)
    return result


def _scan_document_facts(lines: list[RawLine], state: ParseState) -> None:
    for line in lines:
        if "Antwort a ist immer die richtige" in line.text:
            state.answer_a_is_correct = True
        if line.text.startswith("©"):
            state.publisher = line.text.lstrip("©").strip() or state.publisher
        edition = EDITION_RE.search(line.text)
        if edition and state.document_date is None:
            month = MONTHS.get(edition.group(2).casefold())
            if month is not None:
                state.document_date = date(int(edition.group(3)), month, int(edition.group(1)))
        found_range = RANGE_RE.search(line.text)
        if found_range:
            state.ranges[found_range.group(1).casefold()] = (
                int(found_range.group(2)),
                int(found_range.group(3)),
            )
        pool = POOL_RE.search(line.text)
        if pool:
            state.pool_count = int(pool.group(1))
            state.parts_per_task = int(pool.group(2))


def _apply_document_facts(
    source: SourceDocument,
    extraction: Extraction,
    state: ParseState,
) -> None:
    if source.title is None:
        source.title = extraction.metadata.get("title") or None
    if source.publisher is None and state.publisher:
        source.publisher = state.publisher
    if source.document_date is None and state.document_date is not None:
        source.document_date = state.document_date
    author = extraction.metadata.get("author")
    if author:
        source.metadata["pdf_author"] = author
    source.metadata["answer_a_stated_in_document"] = state.answer_a_is_correct
    if state.document_date is not None:
        source.metadata["edition_date"] = state.document_date.isoformat()


def _is_chrome(line: RawLine) -> bool:
    text = line.text.strip()
    folded = text.casefold()
    if line.y < 8:
        return True
    if text in {"Sie sind hier:", "Stand: 01. August 2023"} or text.startswith("Stand:"):
        return True
    if text.startswith("©") or text.startswith(("http://", "https://")):
        return True
    if text.startswith("ELWIS -") or PAGE_COUNT_RE.match(text) or PRINT_STAMP_RE.match(text):
        return True
    # Breadcrumbs repeat section names near the top, to the right of the
    # question column. Real section headings stay at the left margin.
    if line.y < 190 and folded in BREADCRUMBS and line.x >= 48:
        return True
    if line.y < 190 and TASK_RE.match(text) and line.x > 48:
        return True
    return False


def _continue_line(state: ParseState, line: RawLine) -> None:
    if state.question is not None and state.question.answers:
        answer = state.question.answers[-1]
        answer.fragments.append(line.text)
        answer.regions.append(line.region())
        answer.block_ids.append(line.block_id)
        return
    if state.question is not None:
        state.question.fragments.append(line.text)
        state.question.regions.append(line.region())
        state.question.block_ids.append(line.block_id)
        return
    _add_note(state, line.text)


def _add_note(state: ParseState, text: str) -> None:
    if state.section_key:
        state.section_notes.setdefault(state.section_key, []).append(text)
    else:
        state.preamble.append(text)


def _close_open(state: ParseState, source_id: str) -> None:
    _close_question(state, source_id)
    if state.task is not None:
        target = _target(state, "navigationsaufgaben")
        if target is None:
            target = _fallback_target(state)
        catalog_id, prefix, _name = target
        state.questions.append(
            task_question(
                state.task,
                source_id=source_id,
                catalog_id=catalog_id,
                id_prefix=prefix,
            )
        )
        state.task = None


def _close_question(state: ParseState, source_id: str) -> None:
    builder = state.question
    if builder is None:
        return
    state.question = None
    target = _target(state, builder.section_key)
    if target is None:
        target = _fallback_target(state)
    catalog_id, prefix, _name = target
    text = join_wrapped_lines(builder.fragments)
    navigation_role = None
    question_type = QuestionType.SINGLE_CHOICE
    if builder.section_key == "navigationsaufgaben" and not builder.answers:
        question_type = QuestionType.NAVIGATION_TASK
        navigation_role = "prompt_pool"
        prefix = f"{prefix}_prompt"
    question_id = stable_id(prefix, builder.number, text)
    answers: list[Answer] = []
    for position, answer in enumerate(builder.answers, start=1):
        answers.append(
            Answer(
                id=f"{question_id}:answer:{position}",
                text=join_wrapped_lines(answer.fragments),
                original_position=position,
                metadata={
                    "label": answer.label,
                    "original_fragments": answer.fragments,
                },
            )
        )
    correct: list[str] = []
    rule_name = None
    if (
        state.answer_a_is_correct
        and question_type is QuestionType.SINGLE_CHOICE
        and len(answers) == 4
    ):
        labeled = [answer for answer in answers if answer.metadata.get("label") == "a"]
        if len(labeled) == 1:
            labeled[0].is_correct = True
            correct = [labeled[0].id]
            rule_name = "answer_a_stated_in_document"
    pages = sorted({region.page for region in builder.regions})
    reference = SourceReference(
        source_id=source_id,
        page=pages[0] if pages else None,
        pages=pages,
        original_number=builder.number,
        bbox=builder.regions[0] if builder.regions else None,
        regions=builder.regions,
        text_block_ids=list(dict.fromkeys(builder.block_ids)),
    )
    metadata: dict[str, object] = {
        "section": builder.section_key,
        "original_fragments": builder.fragments,
        "answer_labels": [answer.metadata.get("label") for answer in answers],
        "parse_status": "complete",
    }
    if navigation_role:
        metadata["navigation_role"] = navigation_role
    if rule_name:
        metadata["correctness_rule"] = rule_name
    if question_type is QuestionType.SINGLE_CHOICE and len(answers) != 4:
        metadata["parse_status"] = "incomplete"
    state.questions.append(
        Question(
            id=question_id,
            original_number=builder.number,
            question_type=question_type,
            text=text,
            answers=answers,
            correct_answer_ids=correct,
            catalog_ids=[catalog_id],
            source_reference=reference,
            metadata=metadata,
        )
    )


def _target(state: ParseState, section_key: str) -> SectionTarget | None:
    mapping = SECTION_TARGETS.get(section_key, {})
    return mapping.get(state.examination_id)


def _fallback_target(state: ParseState) -> SectionTarget:
    catalog_id = f"{state.examination_id}_unsectioned"
    return (catalog_id, catalog_id, "Unsectioned")


def _catalogs(state: ParseState, source: SourceDocument) -> list[Catalog]:
    version = state.document_date.isoformat() if state.document_date else None
    ordered: list[str] = []
    for question in state.questions:
        for catalog_id in question.catalog_ids:
            if catalog_id not in ordered:
                ordered.append(catalog_id)
    catalogs: list[Catalog] = []
    for catalog_id in ordered:
        section_key = _section_for_catalog(state.examination_id, catalog_id)
        name = _catalog_name(state.examination_id, catalog_id)
        metadata: dict[str, object] = {}
        if section_key and section_key in state.ranges:
            first, last = state.ranges[section_key]
            metadata["stated_first"] = first
            metadata["stated_last"] = last
            metadata["stated_count"] = last - first + 1
        if section_key == "navigationsaufgaben":
            if state.pool_count is not None:
                metadata["stated_pool_count"] = state.pool_count
            if state.parts_per_task is not None:
                metadata["stated_parts_per_task"] = state.parts_per_task
            if state.toc_tasks:
                metadata["stated_variant_numbers"] = state.toc_tasks
        notes = state.section_notes.get(section_key or "", [])
        if notes:
            metadata["notes"] = notes
        if state.answer_a_is_correct:
            metadata["answer_a_stated_in_document"] = True
        catalogs.append(
            Catalog(
                id=catalog_id,
                examination_id=state.examination_id,
                name=name,
                version=version,
                source_id=source.id,
                metadata=metadata,
            )
        )
    return catalogs


def _section_for_catalog(examination_id: str, catalog_id: str) -> str | None:
    for section_key, mapping in SECTION_TARGETS.items():
        target = mapping.get(examination_id)
        if target and target[0] == catalog_id:
            return section_key
    return None


def _catalog_name(examination_id: str, catalog_id: str) -> str:
    for mapping in SECTION_TARGETS.values():
        target = mapping.get(examination_id)
        if target and target[0] == catalog_id:
            return target[2]
    return catalog_id


def _layouts(questions: list[Question], extraction: Extraction) -> dict[str, list[PageSpan]]:
    heights = {page.number: page.height for page in extraction.pages}
    first_y: dict[tuple[int, str], float] = {}
    for question in questions:
        for region in question.source_reference.regions:
            key = (region.page, question.id)
            current = first_y.get(key)
            if current is None or region.bbox.y0 < current:
                first_y[key] = region.bbox.y0
    by_page: dict[int, list[tuple[float, str]]] = {}
    for (page, question_id), y0 in first_y.items():
        by_page.setdefault(page, []).append((y0, question_id))
    layouts: dict[str, list[PageSpan]] = {question.id: [] for question in questions}
    for page, entries in by_page.items():
        entries.sort()
        height = heights.get(page, 842.0)
        for index, (y0, question_id) in enumerate(entries):
            y1 = entries[index + 1][0] if index + 1 < len(entries) else height - 12
            layouts[question_id].append(PageSpan(page=page, y0=y0, y1=max(y1, y0 + 1)))
    return layouts
