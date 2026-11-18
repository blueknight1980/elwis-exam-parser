"""Download policy. Tests do not contact ELWIS."""

from pathlib import Path

import httpx
import pytest

from elwis_parser.config import Settings
from elwis_parser.exceptions import ConfigurationError, SourceError
from elwis_parser.sources.downloader import download_pdf, validate_download_url
from elwis_parser.utils.hashing import sha256_bytes


def test_rejects_host_outside_allowlist() -> None:
    with pytest.raises(ConfigurationError):
        validate_download_url("https://example.com/file.pdf", {"www.elwis.de"})


def test_rejects_http_and_credentials() -> None:
    with pytest.raises(ConfigurationError):
        validate_download_url("http://www.elwis.de/file.pdf", {"www.elwis.de"})
    with pytest.raises(ConfigurationError):
        validate_download_url("https://user:pass@www.elwis.de/file.pdf", {"www.elwis.de"})


def test_download_checks_checksum_and_pdf_header(tmp_path: Path) -> None:
    body = b"%PDF-1.4\n%synthetic\n"
    digest = sha256_bytes(body)

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.host == "www.elwis.de"
        return httpx.Response(200, content=body, headers={"content-type": "application/pdf"})

    client = httpx.Client(transport=httpx.MockTransport(handler))
    path, actual = download_pdf(
        "https://www.elwis.de/catalog.pdf",
        tmp_path / "catalog.pdf",
        settings=Settings(),
        expected_sha256=digest,
        client=client,
    )
    assert actual == digest
    assert path.read_bytes() == body


def test_download_rejects_html(tmp_path: Path) -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, content=b"<html></html>", headers={"content-type": "text/html"})

    client = httpx.Client(transport=httpx.MockTransport(handler))
    with pytest.raises(SourceError):
        download_pdf(
            "https://www.elwis.de/catalog.pdf",
            tmp_path / "catalog.pdf",
            settings=Settings(),
            client=client,
        )
