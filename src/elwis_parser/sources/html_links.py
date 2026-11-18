"""Find publication links in an HTML catalog page.

The function does not download anything and does not decide that a link is
the current official edition. A returned URL still has to be fetched through
the download guard and checked against a pinned checksum.
"""

from __future__ import annotations

from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from elwis_parser.sources.registry import ALLOWED_DOWNLOAD_HOSTS


def publication_links(html: str, *, page_url: str) -> list[str]:
    """Return absolute HTTPS publication links from ``html``.

    Links are kept when they point at an allowed host and either end in
    ``.pdf`` or use the ELWIS ``publicationFile`` query. Other hosts,
    credentials, and non-PDF links are ignored.
    """
    soup = BeautifulSoup(html, "html.parser")
    found: list[str] = []
    for anchor in soup.find_all("a", href=True):
        raw = anchor.get("href")
        if not isinstance(raw, str) or not raw.strip():
            continue
        absolute = urljoin(page_url, raw.strip())
        parsed = urlparse(absolute)
        host = parsed.hostname or ""
        if parsed.scheme != "https" or host not in ALLOWED_DOWNLOAD_HOSTS:
            continue
        if parsed.username or parsed.password:
            continue
        path = parsed.path.casefold()
        if not path.endswith(".pdf") and "publicationfile" not in parsed.query.casefold():
            continue
        if absolute not in found:
            found.append(absolute)
    return found
