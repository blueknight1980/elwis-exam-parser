"""The committed JSON Schema must match the export model."""

import json
from pathlib import Path

from elwis_parser.models.export import ExportDocument

SCHEMA_PATH = Path("docs/export-schema-1.0.json")


def test_export_schema_matches_the_model() -> None:
    committed = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    assert committed == ExportDocument.model_json_schema()
