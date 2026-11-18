# Sources

The tool reads local PDFs. Download is optional and only for URLs that were checked.

## Verified on 2026-11-15

Both files are the edition "Anzuwenden ab dem 01. August 2023" / "Stand: 01. August 2023". The PDF print stamp is a generation timestamp, not the edition date. The publisher line is the Wasserstraßen- und Schifffahrtsverwaltung des Bundes. The PDF author field `WSV.de` is stored separately and is not used as the publisher.

The HTML page without `?__blob=publicationFile` is not the PDF. A preview host that appears in the page chrome is not a public download URL and is not allowlisted.

| Record | File | SHA-256 |
| --- | --- | --- |
| `sbf-see-2023-08-01` | `Fragenkatalog-See-August-2023.pdf` | `34b5b68917e964f577223004bc3be9e2d513e23d20792853052a01c3d80226da` |
| `sbf-binnen-2023-08-01` | `Fragenkatalog-Binnen-August-2023.pdf` | `5e03fc0dbf4fb9a22b7dd1875856436cc18adbe8619b1635bb6ef017568ddd70` |

See URL, as fetched that day:

`https://www.elwis.de/DE/Sportschifffahrt/Sportbootfuehrerscheine/Fragenkatalog-See/Fragenkatalog-See-August-2023.pdf?__blob=publicationFile&v=13`

Binnen URL, as fetched that day:

`https://www.elwis.de/DE/Sportschifffahrt/Sportbootfuehrerscheine/Fragenkatalog-Binnen/Fragenkatalog-Binnen-August-2023.pdf?__blob=publicationFile&v=9`

The `v=` value can change when ELWIS replaces the file. If the bytes change, `sources fetch` fails the pinned checksum. Update the pin only after reviewing the new file. This repository does not claim these URLs are the latest edition forever.

Place the files in `data/sources/`. That directory is gitignored except for `.gitkeep`.

## What the August 2023 PDFs contain

The See PDF states basis questions 1–72, specific See questions 73–285, and navigation questions 286–300. It also contains 15 navigation task variants. The sentence in the file says that 9 of those 15 questions are selected for each variant. The integration test checks 72, 213, 15 prompts, and 15 variants, and it requires the validator to report no errors, which includes the 9-part check.

The Binnen PDF states 72 basis questions, specific inland questions 73–253, and sailing questions 254–300. The integration test checks 72, 181, and 47. Basis question ids that share the same number and normalized text match across the two files; the integration test expects all 72 to match.

Those figures were produced by this parser against those two files. They are not a hand audit of every answer line.

The same run reports zero validation errors and a number of warnings. Repeated stems such as "Welches Fahrzeug führt diese Lichter?" are real separate questions whose distinguishing content is the figure; the validator warns and does not merge or delete them. Vector clusters and a smaller number of raster placements that do not fall inside a question span are reported as `UNASSOCIATED_IMAGE` and are left out of the export. On 2026-11-15 that was 150 warnings for See and 95 for Binnen.

## Downloads

`download_pdf` allows only `https://www.elwis.de/`, refuses userinfo, checks every redirect, accepts `application/pdf` or `application/octet-stream`, requires a `%PDF` header, and enforces the timeout and size cap. `publication_links` can list candidate links from an HTML page you already have. It does not fetch the page.

## Adding a source

Add a `SourceRecord` only after a real response has been saved and hashed. Leave `download_url` empty when the link is not verified. A local path is enough for `parse`.
