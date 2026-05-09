"""Surface-form normalizer. Collapse near-duplicate entity strings to a canonical key
so we generate one concept page per real entity, not one per phrasing.

Heuristic only — strips parentheticals, qualifier clauses, punctuation, casing.
Does NOT do entity linking against a knowledge base; that's a future step.
"""

from __future__ import annotations

import re

_PAREN = re.compile(r"\s*\([^)]*\)|\s*\[[^\]]*\]")
_QUAL = re.compile(
    r"\b(with|carrying|in|from|having|exhibiting|expressing|bearing|"
    r"resistant to|sensitive to|treated with|tolerant to|"
    r"harbouring|harboring|containing|including|associated with)\b",
    re.IGNORECASE,
)
_PUNCT = re.compile(r"[^\w\s\-/.]+")
_WS = re.compile(r"\s+")


def canonicalize(name: str) -> str:
    """Return a canonical key for a free-text entity surface form.

    Examples
    --------
    >>> canonicalize("Plasmodium falciparum (Cambodian strains)")
    'plasmodium falciparum'
    >>> canonicalize("P. falciparum with kelch13 mutation")
    'p. falciparum'
    >>> canonicalize("CRISPR-Cas9 knockout of plasmepsin II")
    'crispr-cas9 knockout of plasmepsin ii'
    """
    s = name.strip().lower()
    s = _PAREN.sub("", s)
    s = _QUAL.split(s, maxsplit=1)[0]
    s = _PUNCT.sub(" ", s)
    s = _WS.sub(" ", s).strip(" -.,;:")
    return s
