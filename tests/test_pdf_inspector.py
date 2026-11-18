"""PDF inspection and extraction on synthetic files."""

from pathlib import Path

from tests.pdf_factory import build_pdf

from elwis_parser.pdf.backend import open_pdf
from elwis_parser.pdf.extractor import extract_document
from elwis_parser.pdf.inspector import inspection_payload


def test_inspector_reports_pages_and_text(tmp_path: Path, settings) -> None:
    pdf = tmp_path / "sample.pdf"
    build_pdf(pdf, [["Erste Zeile", "Zweite Zeile"], ["Nur zweite Seite"]], header="KOPF")
    document = open_pdf(pdf, settings)
    try:
        extraction = extract_document(document, "src:test")
    finally:
        document.close()
    payload = inspection_payload(extraction)
    assert payload["page_count"] == 2
    assert payload["block_count"] >= 2
    page = inspection_payload(extraction, page=2)
    assert page["selected_page"] == 2
    assert any("zweite Seite" in block["text"] for block in page["blocks"])


def test_running_header_is_marked(tmp_path: Path, settings) -> None:
    pdf = tmp_path / "header.pdf"
    build_pdf(pdf, [["Frage"], ["Frage"]], header="KOPF")
    document = open_pdf(pdf, settings)
    try:
        extraction = extract_document(document, "src:test")
    finally:
        document.close()
    headers = [block for block in extraction.blocks if block.role == "header"]
    assert headers
    assert all(block.text == "KOPF" for block in headers)


def test_raster_and_vector_are_detected(tmp_path: Path, settings) -> None:
    pdf = tmp_path / "graphics.pdf"
    build_pdf(pdf, [["Abbildung"]], image=True, vector=True)
    document = open_pdf(pdf, settings)
    try:
        extraction = extract_document(document, "src:test")
    finally:
        document.close()
    assert extraction.images
    assert extraction.vectors
