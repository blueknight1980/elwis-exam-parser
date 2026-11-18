"""Navigation-task assembly.

A navigation task is a scenario plus a table of prompts and sample solutions.
It is not converted into single-choice answers.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from elwis_parser.models import (
    NavigationDetails,
    NavigationPart,
    PageRegion,
    Question,
    QuestionType,
    SourceReference,
)
from elwis_parser.parsers.lines import RawLine
from elwis_parser.parsers.patterns import PART_RE, TABLE_LABELS
from elwis_parser.utils.hashing import stable_id
from elwis_parser.utils.text import join_wrapped_lines


@dataclass
class PartBuilder:
    """Accumulates one table row."""

    label: str
    prompt: list[str] = field(default_factory=list)
    solution: list[str] = field(default_factory=list)
    regions: list[PageRegion] = field(default_factory=list)


@dataclass
class TaskBuilder:
    """Accumulates one Navigationsaufgabe."""

    number: str
    scenario: list[str] = field(default_factory=list)
    parts: list[PartBuilder] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    regions: list[PageRegion] = field(default_factory=list)
    block_ids: list[str] = field(default_factory=list)
    in_table: bool = False
    current: PartBuilder | None = None

    def add_line(self, line: RawLine) -> None:
        """Consume one line that belongs to this task."""
        self.regions.append(line.region())
        self.block_ids.append(line.block_id)
        if line.text in TABLE_LABELS:
            self.in_table = True
            return
        if PART_RE.fullmatch(line.text) and line.x < 80:
            self.in_table = True
            self.current = PartBuilder(label=line.text)
            self.parts.append(self.current)
            self.current.regions.append(line.region())
            return
        if not self.in_table or self.current is None:
            self.scenario.append(line.text)
            return
        if line.x >= 300:
            self.current.solution.append(line.text)
        elif line.x < 70:
            self.notes.append(line.text)
        else:
            self.current.prompt.append(line.text)
        self.current.regions.append(line.region())


def task_question(
    task: TaskBuilder,
    *,
    source_id: str,
    catalog_id: str,
    id_prefix: str,
) -> Question:
    """Build the question record for one navigation task variant."""
    scenario = join_wrapped_lines(task.scenario)
    parts: list[NavigationPart] = []
    for index, part in enumerate(task.parts, start=1):
        label = part.label.rstrip(".")
        prompt = join_wrapped_lines(part.prompt)
        solution = join_wrapped_lines(part.solution) or None
        parts.append(
            NavigationPart(
                id=f"placeholder-{index}",
                label=label,
                prompt=prompt,
                sample_solution=solution,
                metadata={"original_fragments": part.prompt, "solution_fragments": part.solution},
            )
        )
    text = scenario
    question_id = stable_id(f"{id_prefix}_task", task.number, text or task.number)
    for navigation_part in parts:
        navigation_part.id = f"{question_id}:part:{navigation_part.label}"
    pages = sorted({region.page for region in task.regions})
    reference = SourceReference(
        source_id=source_id,
        page=pages[0] if pages else None,
        pages=pages,
        original_number=task.number,
        bbox=task.regions[0] if task.regions else None,
        regions=task.regions,
        text_block_ids=list(dict.fromkeys(task.block_ids)),
    )
    return Question(
        id=question_id,
        original_number=task.number,
        question_type=QuestionType.NAVIGATION_TASK,
        text=text,
        catalog_ids=[catalog_id],
        source_reference=reference,
        navigation=NavigationDetails(
            title=f"Navigationsaufgabe {task.number}",
            scenario=scenario,
            parts=parts,
            notes=task.notes,
        ),
        metadata={
            "navigation_role": "task_variant",
            "original_fragments": task.scenario,
            "parse_status": "complete" if parts else "incomplete",
        },
    )
