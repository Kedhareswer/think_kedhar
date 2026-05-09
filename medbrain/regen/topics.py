"""Predicate-based topic derivation.

A `topic` is a path under `notes/`, e.g. `treatment/artemether-lumefantrine`.
Each claim implies zero or more topics derived from its predicate + entity.
Brain may emit additional topic categories later; for v1 the mapping is fixed.
"""

from __future__ import annotations

from medbrain.enums import Predicate
from medbrain.regen.slug import slugify


def topics_for(predicate: Predicate, subject: str, obj: str) -> list[str]:
    """Return zero or more topic paths a claim contributes to.

    Mapping (v1):
      treats / recommends      -> treatment/<object>
      resists                  -> resistance/<object>            (subject = pathogen)
      causes                   -> etiology/<object>
      prevents                 -> prevention/<object>
      contraindicates          -> safety/<subject>
      requires                 -> diagnostics/<subject>
      co_occurs                -> associations/<subject>
      supersedes               -> (no topic; metadata only)
    """
    s = slugify(subject)
    o = slugify(obj)
    match predicate:
        case Predicate.TREATS | Predicate.RECOMMENDS:
            return [f"treatment/{o}"]
        case Predicate.RESISTS:
            return [f"resistance/{o}"]
        case Predicate.CAUSES:
            return [f"etiology/{o}"]
        case Predicate.PREVENTS:
            return [f"prevention/{o}"]
        case Predicate.CONTRAINDICATES:
            return [f"safety/{s}"]
        case Predicate.REQUIRES:
            return [f"diagnostics/{s}"]
        case Predicate.CO_OCCURS:
            return [f"associations/{s}"]
        case Predicate.SUPERSEDES:
            return []
    return []
