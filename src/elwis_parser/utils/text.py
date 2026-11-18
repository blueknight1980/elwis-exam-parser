"""Documented technical text normalization.

The rules below remove PDF line-wrap artifacts. They do not correct spelling,
punctuation, or wording.

* A soft hyphen (U+00AD) is removed.
* A line-ending hyphen followed by a lowercase letter is a wrapped word: the
  hyphen is dropped and the parts are concatenated.
* A line-ending hyphen followed by an uppercase letter is kept, so a compound
  such as ``Hand-`` + ``Peilkompass`` stays ``Hand-Peilkompass``.
* Other wrapped lines are joined with a single space.
* Runs of ASCII spaces and tabs are collapsed. Non-breaking spaces are kept.
"""

from __future__ import annotations

import re

_SOFT_HYPHEN = "\u00ad"
_SPACE_RUN = re.compile(r"[ \t]+")


def clean_fragment(text: str) -> str:
    """Strip one fragment and remove soft hyphens."""
    return text.replace(_SOFT_HYPHEN, "").strip()


def join_wrapped_lines(lines: list[str]) -> str:
    """Join visual line wraps using the rules in the module docstring."""
    parts = [clean_fragment(line) for line in lines]
    parts = [part for part in parts if part]
    if not parts:
        return ""
    result = parts[0]
    for part in parts[1:]:
        if result.endswith("-") and part[:1].islower():
            result = result[:-1] + part
        elif result.endswith("-"):
            result = result + part
        else:
            result = f"{result} {part}"
    return _SPACE_RUN.sub(" ", result).strip()
