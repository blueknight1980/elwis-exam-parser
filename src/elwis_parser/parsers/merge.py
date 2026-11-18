"""Merge questions that share an id across examinations."""

from __future__ import annotations

from elwis_parser.models import Catalog, ExamParseResult, Question


def merge_results(results: list[ExamParseResult]) -> ExamParseResult:
    """Union parse results.

    Questions with the same id keep one record. Catalog membership is united,
    so shared basis questions can point at more than one catalog.
    """
    if not results:
        raise ValueError("At least one parse result is required.")
    questions: dict[str, Question] = {}
    catalogs: dict[str, Catalog] = {}
    for result in results:
        for catalog in result.catalogs:
            existing = catalogs.get(catalog.id)
            if existing is None:
                catalogs[catalog.id] = catalog.model_copy(deep=True)
            else:
                for question_id in catalog.question_ids:
                    if question_id not in existing.question_ids:
                        existing.question_ids.append(question_id)
        for question in result.questions:
            current = questions.get(question.id)
            if current is None:
                questions[question.id] = question.model_copy(deep=True)
                continue
            for catalog_id in question.catalog_ids:
                if catalog_id not in current.catalog_ids:
                    current.catalog_ids.append(catalog_id)
            for image_id in question.image_ids:
                if image_id not in current.image_ids:
                    current.image_ids.append(image_id)
    examination_ids = {result.examination_id for result in results}
    examination_id = examination_ids.pop() if len(examination_ids) == 1 else "mixed"
    return ExamParseResult(
        examination_id=examination_id,
        catalogs=list(catalogs.values()),
        questions=list(questions.values()),
        sources=[source for result in results for source in result.sources],
        preamble=[line for result in results for line in result.preamble],
    )
