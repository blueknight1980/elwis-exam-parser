# Data model

Public JSON is an `ExportDocument`. The JSON Schema generated from that model is `docs/export-schema-1.0.json`. Field names are stable and contain no Python-only types beyond ISO datetimes and ordinary JSON.

## Export document

| Field | Meaning |
| --- | --- |
| `schema_version` | `1.0` |
| `parser_version` | Package version that wrote the file |
| `exported_at` | UTC timestamp of the export |
| `examination` | `sbf_see` or `sbf_binnen` for the implemented parsers |
| `catalogs` | Part catalogs in document order |
| `questions` | Questions in document order |
| `images` | Assets referenced by those questions |
| `sources` | Source records without local filesystem paths |
| `validation` | Error, warning, and info counts plus the finding list |
| `metadata` | Parser notes that are not part of a question |

## Examination

Known ids: `sbf_see`, `sbf_binnen`, `src`, `ubi`, `lrc`, `fkn`, `sks`. Only the two SBF ids have parsers.

## Catalog

`id`, `examination_id`, `name`, `version`, `source_id`, `question_ids`, and `metadata`.

Implemented catalog ids:

| Id | Contents |
| --- | --- |
| `sbf_see_basis` | See basis questions |
| `sbf_see_specific` | Specific See questions |
| `sbf_see_navigation` | Navigation prompt pool and task variants |
| `sbf_binnen_basis` | Binnen basis questions |
| `sbf_binnen_specific` | Specific inland questions |
| `sbf_binnen_sailing` | Sailing questions |

When the PDF states a range such as "Frage 1 bis Frage 72", that range is stored as `stated_first`, `stated_last`, and `stated_count`. Validation compares it with the parsed questions. Navigation task variants are not counted as pool questions.

For the August 2023 files inspected on 2026-11-15 the stated ranges match these counts: See 72 basis, 213 specific, 15 pool prompts and 15 task variants; Binnen 72 basis, 181 specific, 47 sailing. The integration tests check those counts. They are properties of that edition, not hardcoded success.

## Question

`id`, `original_number`, `question_type`, `text`, `answers`, `correct_answer_ids`, `image_ids`, `catalog_ids`, `source_reference`, optional `navigation`, and `metadata`.

`single_choice` is the SBF answer layout: four options labeled `a` through `d` when the page follows the inspected catalog. `navigation_task` is used for a pool prompt that has no answers and for each Navigationsaufgabe. A task is not converted into single-choice options. `multiple_choice` and `free_text` exist for later examinations and are not emitted by the SBF parsers.

The number and letter prefixes are removed from `text`. The raw line fragments remain in `metadata.original_fragments`.

Correctness is set only when the PDF itself says that answer `a` is the correct one. The rule marks the option labeled `a`. If the sentence is absent, no option is marked correct and validation reports `CORRECTNESS_RULE_NOT_IN_DOCUMENT`.

## Answer

`id`, `text`, `image_ids`, `original_position`, `is_correct`, and `metadata`. Position follows the PDF order.

## Navigation

`NavigationDetails` holds the scenario text, ordered parts, and notes. Each `NavigationPart` has its original label, prompt, and `sample_solution`. The solution is the "Ergebnis" column. It is not stored as a single-choice answer.

The August 2023 See PDF says that 9 of the following 15 questions are selected for each task. The parser records that sentence and validation expects 9 parts on each variant. The chart D49 is cited in the PDF and is not embedded in it. A solution that says the chart must be consulted is kept as printed.

## Image

`id`, `filename`, `relative_path`, `mime_type`, `sha256`, `source_page`, `source_document_id`, `bounding_box`, `width`, `height`, `origin`, and association lists.

`origin` is `raster_original` or `rendered_region`. `manual_redraw` is reserved and is never written by the extractor. Repeated placements of one PDF object share a SHA-256 and keep separate ids. Association uses the vertical span from a question to the next question on the same page. An image that matches none or more than one question produces `UNASSOCIATED_IMAGE` or `AMBIGUOUS_IMAGE`. The header logo is excluded.

Public exports use paths relative to the output directory. Absolute local paths are omitted.

## Source

`SourceDocument` records title, publisher, URL, document date, retrieval time, SHA-256, parser version, and the local path used during processing. `public_dict()` drops the local path before export.

`SourceReference` on a question records the source id, pages, original number, and the text-block regions the lines came from.

## Findings

Each finding has `code`, `severity` (`info`, `warning`, `error`), `message`, entity type and id, source id, and page when known. `--strict` refuses to write `catalog.json` when any error is present. `validate` exits with code 2 in that case even after a file was written without `--strict`.
