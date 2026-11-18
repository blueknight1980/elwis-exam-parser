# ELWIS Exam Parser

A Python CLI that turns the official German Sportbootführerschein See and Binnen PDF catalogs into validated, versioned JSON. It preserves the original German wording, keeps shared basis-question IDs stable across catalogs, and models navigation exercises with their numbered parts and sample solutions.

## Try it with a synthetic PDF

With Python 3.12, run these commands from the repository root:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install .
python examples/build_synthetic_pdf.py data/sources/synthetic-see.pdf
elwis-parser parse data/sources/synthetic-see.pdf --exam sbf-see --output data/exports/demo
python -c 'import json; from pathlib import Path; data = json.loads(Path("data/exports/demo/catalog.json").read_text()); print(json.dumps(data["questions"][0], ensure_ascii=False, indent=2))'
```

The demo prints the first parsed question, including its four answers. The synthetic PDF and generated output stay in ignored directories.

### Run with Docker Compose

```bash
docker compose --env-file .docker/.env.example -f .docker/docker-compose.yml build
docker compose --env-file .docker/.env.example -f .docker/docker-compose.yml run --rm python elwis-parser --help
```

On Linux, if your UID or GID differs from 1000, copy `.docker/.env.example` to `.docker/.env`, set `DOCKER_UID` and `DOCKER_GID`, and pass that file as `--env-file`. The npm shortcuts also use `.docker/.env`.

## Parse an official catalog

The CLI downloads pinned August 2023 editions directly from ELWIS and verifies their SHA-256 checksums. Downloads and exports stay local.

```bash
elwis-parser sources fetch sbf-see-2023-08-01
elwis-parser parse data/sources/Fragenkatalog-See-August-2023.pdf --exam sbf-see --output data/exports/see --strict
elwis-parser validate data/exports/see/catalog.json
```

For Binnen, use source ID `sbf-binnen-2023-08-01`, filename `Fragenkatalog-Binnen-August-2023.pdf`, and exam `sbf-binnen`. A checksum mismatch stops the download. See the [source registry](docs/sources.md) and [CLI guide](docs/usage.md).

## How it works

- Extracts PDF text and image regions with PyMuPDF.
- Parses See and Binnen layouts into typed models and reports validation findings.
- Exports [versioned JSON](docs/export-schema-1.0.json) and supports CSV export for single-choice questions.

The supported layouts are the August 2023 editions. Radio and other exam types are outside this release's scope. See the [architecture](docs/architecture.md) and [data model](docs/data-model.md).

## Checks

```bash
python -m pip install ".[dev]"
ruff check .
ruff format --check .
mypy src
pytest
```

CI runs the synthetic tests. The optional integration tests also verify question counts and shared IDs when both official PDFs are present in `data/sources/`.

## License and sources

The original parser source is available under the [MIT License](LICENSE). PyMuPDF is separately available under [GNU AGPLv3 or a commercial license](https://pymupdf.readthedocs.io/en/latest/about.html#license-and-copyright). See the [license notes](docs/legal.md) for the combined program and catalog material.

This is an independent tool for working with the catalogs published by the German Federal Waterways and Shipping Administration through ELWIS.
