"""Filesystem-safe slugify. Used for entity / topic filenames."""

from __future__ import annotations

import re
import unicodedata

_NON_ALNUM = re.compile(r"[^a-z0-9]+")
_DASHES = re.compile(r"-+")
_LEADING_TRAILING = re.compile(r"^-+|-+$")


def slugify(name: str, *, max_len: int = 80) -> str:
    """Lowercase, ASCII-fold, hyphenate. Returns 'unknown' for empty input."""
    if not name:
        return "unknown"
    s = unicodedata.normalize("NFKD", name)
    s = s.encode("ascii", "ignore").decode("ascii")
    s = s.lower()
    s = _NON_ALNUM.sub("-", s)
    s = _DASHES.sub("-", s)
    s = _LEADING_TRAILING.sub("", s)
    if not s:
        return "unknown"
    if len(s) > max_len:
        s = s[:max_len].rstrip("-")
    return s
