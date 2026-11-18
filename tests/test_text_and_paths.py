"""Text and checksum helpers."""

import pytest

from elwis_parser.exceptions import UsageError
from elwis_parser.utils.hashing import sha256_bytes, stable_id
from elwis_parser.utils.paths import ensure_within, safe_filename
from elwis_parser.utils.text import join_wrapped_lines


def test_join_drops_hyphen_before_lowercase() -> None:
    assert join_wrapped_lines(["Sportboot-", "führerschein"]) == "Sportbootführerschein"


def test_join_keeps_hyphen_before_uppercase() -> None:
    assert join_wrapped_lines(["Hand-", "Peilkompass"]) == "Hand-Peilkompass"


def test_join_uses_space_for_normal_wraps() -> None:
    assert join_wrapped_lines(["foo", "bar"]) == "foo bar"


def test_stable_id_ignores_surrounding_whitespace() -> None:
    assert stable_id("sbf_basis", "1", "Text  hier") == stable_id("sbf_basis", "1", "Text hier")


def test_sha256_is_hex() -> None:
    assert len(sha256_bytes(b"abc")) == 64


def test_safe_filename_rejects_traversal() -> None:
    assert "/" not in safe_filename("../secret.pdf")
    with pytest.raises(UsageError):
        safe_filename("...")


def test_ensure_within_rejects_escape(tmp_path) -> None:
    with pytest.raises(UsageError):
        ensure_within(tmp_path, tmp_path / ".." / "outside.txt")
