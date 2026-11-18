# Usage

The command is `elwis-parser`. Expected failures print a message and an exit code. A usage or configuration error exits 1. Validation errors exit 2. A PDF or source failure exits 3. Typer's own usage errors can still exit 2.

Global options, placed before the command: `--verbose` and `--quiet`.

```bash
elwis-parser --help
elwis-parser version
elwis-parser inspect data/sources/Fragenkatalog-See-August-2023.pdf
elwis-parser inspect data/sources/Fragenkatalog-See-August-2023.pdf --page 12
elwis-parser inspect data/sources/Fragenkatalog-See-August-2023.pdf --page 12 --json
elwis-parser extract data/sources/Fragenkatalog-See-August-2023.pdf --output data/extracted/see
elwis-parser parse data/sources/Fragenkatalog-See-August-2023.pdf \
  --exam sbf-see --output data/exports/see --overwrite
elwis-parser validate data/exports/see/catalog.json
elwis-parser export data/exports/see/catalog.json --format csv \
  --output data/exports/see/questions.csv
elwis-parser sources list
elwis-parser sources verify --directory data/sources
```

`parse` accepts `--strict`, `--overwrite`, `--source-url`, `--publisher`, `--title`, and `--document-date`. `--strict` writes `validation.json` and does not write `catalog.json` when the report contains errors.

`sources verify` only hashes local files. `sources fetch <source-id>` downloads one pinned URL. A checksum mismatch is a failure. Do not delete the pin to make a changed file pass.

`inspect --render-dir` needs `--page` and writes a PNG preview of that page.

## Docker

The Compose project name is `elwisexamparser`. The service is `python`. The repository is mounted at `/app`.

```bash
docker compose --env-file .docker/.env.example -f .docker/docker-compose.yml build
docker compose --env-file .docker/.env.example -f .docker/docker-compose.yml run --rm python \
  elwis-parser version
```

Copy `.docker/.env.example` to `.docker/.env` when the host UID is not 1000, then use the npm scripts in `package.json` (`npm run docker:build`, `npm run docker:up`). The image installs the project for the unprivileged user `developer`. `PYTHONPATH=/app/src` lets the mounted tree override the copy baked into the image.

## Local Python

The package requires Python 3.12. On a machine that only has another version, use the Docker image above.

```bash
python3.12 -m pip install ".[dev]"
ruff check .
ruff format --check .
mypy src
pytest
```

`pytest` always runs the synthetic tests. The official-PDF tests skip themselves when `data/sources/` does not contain the pinned files. A skip is not a successful parse of an official catalog.

## Synthetic trial

```bash
python examples/build_synthetic_pdf.py
elwis-parser parse examples/synthetic-see.pdf --exam sbf-see \
  --output examples/out --overwrite
```

That PDF is invented marker text. It is not an official result.

## Limits

Environment variables, all optional:

| Variable | Default |
| --- | --- |
| `ELWIS_MAX_PDF_BYTES` | 30 MiB |
| `ELWIS_MAX_PDF_PAGES` | 1000 |
| `ELWIS_MAX_DOWNLOAD_BYTES` | 30 MiB |
| `ELWIS_MAX_IMAGE_BYTES` | 80 MiB |
| `ELWIS_HTTP_TIMEOUT` | 30 seconds |

Encrypted PDFs are rejected. PDF JavaScript is not executed.
