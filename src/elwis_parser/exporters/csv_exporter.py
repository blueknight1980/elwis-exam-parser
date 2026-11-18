"""CSV export of questions and answers."""

from __future__ import annotations

import csv
from pathlib import Path

from elwis_parser.models import ExportDocument
from elwis_parser.utils.paths import ensure_within


def write_csv(document: ExportDocument, path: Path) -> None:
    """Write one row per answer, or per navigation part.

    Questions without answers get a single row so the question is still present.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    ensure_within(path.parent, path)
    fieldnames = [
        "question_id",
        "original_number",
        "question_type",
        "catalog_ids",
        "question_text",
        "answer_position",
        "answer_id",
        "answer_text",
        "is_correct",
        "sample_solution",
        "image_ids",
        "source_id",
        "page",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for question in document.questions:
            catalogs = "|".join(question.catalog_ids)
            images = "|".join(question.image_ids)
            source_id = question.source_reference.source_id
            page = question.source_reference.page or ""
            if question.navigation and question.navigation.parts:
                for part in question.navigation.parts:
                    writer.writerow(
                        {
                            "question_id": question.id,
                            "original_number": question.original_number,
                            "question_type": question.question_type.value,
                            "catalog_ids": catalogs,
                            "question_text": question.text,
                            "answer_position": part.label,
                            "answer_id": part.id,
                            "answer_text": part.prompt,
                            "is_correct": "",
                            "sample_solution": part.sample_solution or "",
                            "image_ids": images,
                            "source_id": source_id,
                            "page": page,
                        }
                    )
                continue
            if not question.answers:
                writer.writerow(
                    {
                        "question_id": question.id,
                        "original_number": question.original_number,
                        "question_type": question.question_type.value,
                        "catalog_ids": catalogs,
                        "question_text": question.text,
                        "answer_position": "",
                        "answer_id": "",
                        "answer_text": "",
                        "is_correct": "",
                        "sample_solution": "",
                        "image_ids": images,
                        "source_id": source_id,
                        "page": page,
                    }
                )
                continue
            for answer in question.answers:
                writer.writerow(
                    {
                        "question_id": question.id,
                        "original_number": question.original_number,
                        "question_type": question.question_type.value,
                        "catalog_ids": catalogs,
                        "question_text": question.text,
                        "answer_position": answer.original_position,
                        "answer_id": answer.id,
                        "answer_text": answer.text,
                        "is_correct": "true" if answer.is_correct else "false",
                        "sample_solution": "",
                        "image_ids": "|".join(answer.image_ids) or images,
                        "source_id": source_id,
                        "page": page,
                    }
                )
