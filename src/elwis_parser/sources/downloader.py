"""Guarded HTTP downloads.

Only HTTPS URLs whose host is on the allowlist are fetched. Redirects that
leave the allowlist are rejected. The response body is capped.
"""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path
from urllib.parse import urlsplit

import httpx

from elwis_parser.config import Settings
from elwis_parser.exceptions import ConfigurationError, SourceError
from elwis_parser.sources.registry import ALLOWED_DOWNLOAD_HOSTS
from elwis_parser.utils.hashing import sha256_bytes
from elwis_parser.utils.paths import ensure_within, safe_filename


def validate_download_url(url: str, allowed_hosts: Iterable[str]) -> str:
    """Return the hostname when ``url`` is allowed, otherwise raise."""
    parsed = urlsplit(url)
    host = parsed.hostname
    allowed = {item.casefold() for item in allowed_hosts}
    if parsed.scheme != "https" or host is None or host.casefold() not in allowed:
        raise ConfigurationError(
            "Refusing download. The URL must be HTTPS and its host must be on the allowlist."
        )
    if parsed.username or parsed.password:
        raise ConfigurationError("Refusing download URL that contains credentials.")
    return host


def download_pdf(
    url: str,
    destination: Path,
    *,
    settings: Settings,
    allowed_hosts: Iterable[str] | None = None,
    expected_sha256: str | None = None,
    client: httpx.Client | None = None,
) -> tuple[Path, str]:
    """Download one PDF and return its path and SHA-256 digest.

    ``destination`` must already be the final file path inside the directory
    the caller chose. The write stays inside that parent directory.
    """
    hosts = ALLOWED_DOWNLOAD_HOSTS if allowed_hosts is None else allowed_hosts
    validate_download_url(url, hosts)
    parent = destination.parent
    parent.mkdir(parents=True, exist_ok=True)
    filename = safe_filename(destination.name)
    target = ensure_within(parent, parent / filename)
    owns_client = client is None
    http = client or httpx.Client(
        timeout=settings.http_timeout_seconds,
        follow_redirects=True,
        headers={"User-Agent": settings.user_agent},
    )
    temporary = target.with_suffix(target.suffix + ".part")
    try:
        with http.stream("GET", url) as response:
            final_host = validate_download_url(str(response.url), hosts)
            if final_host.casefold() not in {item.casefold() for item in hosts}:
                raise ConfigurationError("Redirect left the download allowlist.")
            response.raise_for_status()
            content_type = response.headers.get("content-type", "")
            if (
                content_type
                and "pdf" not in content_type.casefold()
                and "octet-stream" not in content_type.casefold()
            ):
                raise SourceError(f"Download did not return a PDF (content-type {content_type!r}).")
            chunks: list[bytes] = []
            total = 0
            for chunk in response.iter_bytes():
                total += len(chunk)
                if total > settings.max_download_bytes:
                    raise SourceError(
                        f"Download exceeded {settings.max_download_bytes} bytes and was discarded."
                    )
                chunks.append(chunk)
        data = b"".join(chunks)
        if not data.startswith(b"%PDF"):
            raise SourceError("Download does not start with a PDF header.")
        digest = sha256_bytes(data)
        if expected_sha256 and digest != expected_sha256:
            raise SourceError(
                "Downloaded SHA-256 does not match the pinned checksum. "
                f"Expected {expected_sha256}, got {digest}. "
                "The published file may have changed and needs a reviewed pin update."
            )
        temporary.write_bytes(data)
        temporary.replace(target)
        return target, digest
    except httpx.HTTPError as exc:
        raise SourceError(f"Download failed: {exc}") from exc
    finally:
        temporary.unlink(missing_ok=True)
        if owns_client:
            http.close()
