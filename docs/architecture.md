# Architecture

`elwis-exam-parser` is a local extraction and validation tool. It is developed independently of ELWIS and is not an official ELWIS application. It does not train candidates and it does not store a database.

## Pipeline

1. **Sources** open a local PDF or, for a pinned record, download one URL. Downloads are limited to `https://www.elwis.de/`, reject credentials, re-check redirects, require a PDF header, and stop at a size cap.
2. **PDF extraction** reads metadata, text blocks, raster placements, and vector clusters. It does not decide what a question is.
3. **Parsers** turn that geometry into catalogs, questions, answers, and navigation tasks. SBF See and SBF Binnen share one layout parser. Other examinations have model ids only.
4. **Images** are written from original raster bytes when the stream is a plain PNG, JPEG, JPEG 2000, or TIFF without a mask. Otherwise the placement is rendered. Vector groups are rendered as a clipped PNG. The header logo is marked as page chrome and left out of the export.
5. **Validation** checks the parse result and returns findings. It does not rewrite question text.
6. **Export** writes schema 1.0 JSON. CSV is a secondary view of the same document.

`parse` is the command that runs steps 2 through 6. `inspect` and `extract` stop before interpretation.

## Extension points

A new examination adds a `BaseExamParser` and a registry entry. The PDF extractor, the JSON envelope, and the validator stay in place. Question types already include `single_choice`, `multiple_choice`, `free_text`, and `navigation_task`. SRC, UBI, LRC, FKN, and SKS are registered without extraction rules. Their formats are not copied from the SBF catalogs.

Shared basis questions use the id prefix `sbf_basis`. Catalog membership is a separate list, so the same question can belong to See and Binnen. `merge_results` unions those memberships.

## Identifiers

Question, answer, and image ids are derived from content and position, not from the clock. `exported_at` and `retrieved_at` may change between runs. The question id does not.

Basis ids look like `sbf_basis:1:<12 hex chars>`. Answer ids append `:answer:<position>`. Image ids include the file digest, page, and placement index. Source ids use the first 16 hex chars of the PDF SHA-256.

## Text

Original fragments stay in question and answer metadata. The displayed string is joined only to undo PDF line wrapping: soft hyphens are removed, a hyphen before a lowercase continuation is a wrapped word, and a hyphen before an uppercase continuation is kept. Spelling is not corrected.

## What was checked against official PDFs

On 2026-11-15 the August 2023 See and Binnen publication files were fetched from `www.elwis.de`. The parser rules (question column, answer labels, section headings, the sentence that answer `a` is correct, and the navigation table) come from those files. Optional integration tests assert the section counts and require zero validation errors. They run only when the PDFs are on disk. They do not prove that every line of every question was compared by hand with the printed page.

No newer catalog edition was identified in that fetch. That is not proof that no later edition exists.
