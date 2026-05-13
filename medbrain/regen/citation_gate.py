"""Citation-preservation gate for concept/topic regen.

Concept and topic notes are derivative artifacts — re-synthesized from the
SQL claim set on every regen. The LLM is told to cite every load-bearing
claim with `[c:<8char>]`. This gate verifies the contract before we replace
the existing markdown on disk:

  1. No fabricated citations: every `[c:<id>]` in the new body must match
     a real input claim_id (8-char prefix).
  2. Minimum coverage: at least `min_coverage` fraction of input claim_ids
     must be cited. Below that, the regen has likely collapsed too much
     nuance and should be rejected so the prior file stays as the better
     artifact.

The gate is conservative — failures keep the prior file intact rather than
overwriting with a degraded version. Callers should log failures and
re-attempt on the next regen tick.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from typing import Iterable

_CITATION_RE = re.compile(r"\[c:([0-9a-fA-F]{6,16})\]")


def extract_citations(text: str) -> set[str]:
    """Return the set of 8-char claim_id prefixes cited in the text."""
    return {m.group(1)[:8].lower() for m in _CITATION_RE.finditer(text)}


def _prefixes(claim_ids: Iterable[str]) -> set[str]:
    return {cid[:8].lower() for cid in claim_ids if cid}


@dataclass(frozen=True)
class GateResult:
    passed: bool
    reason: str
    coverage: float
    cited_count: int
    input_count: int
    missing_input_ids: frozenset[str]
    fabricated_ids: frozenset[str]


def check(
    *,
    body: str,
    input_claim_ids: Iterable[str],
    min_coverage: float = 0.5,
    require_any: bool = True,
) -> GateResult:
    """Verify the regenerated body preserves the input claim set.

    Args:
        body: the LLM-produced markdown about to be written.
        input_claim_ids: full claim_ids passed to the LLM as evidence.
        min_coverage: minimum fraction of input claim_ids that must be
            cited in the body. Default 0.5 — half the supplied evidence
            must be referenced. Tune up for safety-critical artifacts
            (drug dosing), down for sprawling synthesis pages.
        require_any: if True and input_claim_ids is non-empty, the body
            must contain at least one citation. Catches the "LLM
            forgot to cite anything" failure mode.

    Returns:
        GateResult with passed flag and diagnostic fields.

    Honors ``MEDBRAIN_REGEN_GATE_DISABLE=1`` (or "true") to short-circuit and
    always pass — used by unit tests that mock the LLM with citation-free
    bodies, and as an emergency escape if the gate over-rejects in prod.
    """
    if os.getenv("MEDBRAIN_REGEN_GATE_DISABLE", "").lower() in ("1", "true", "yes"):
        return GateResult(
            passed=True,
            reason="disabled via MEDBRAIN_REGEN_GATE_DISABLE",
            coverage=1.0,
            cited_count=0,
            input_count=0,
            missing_input_ids=frozenset(),
            fabricated_ids=frozenset(),
        )

    body_cites = extract_citations(body)
    inputs = _prefixes(input_claim_ids)

    if not inputs:
        return GateResult(
            passed=True,
            reason="no input claims to protect",
            coverage=1.0,
            cited_count=len(body_cites),
            input_count=0,
            missing_input_ids=frozenset(),
            fabricated_ids=frozenset(body_cites),
        )

    fabricated = body_cites - inputs
    cited_inputs = body_cites & inputs
    missing = inputs - body_cites
    coverage = len(cited_inputs) / len(inputs)

    if fabricated:
        return GateResult(
            passed=False,
            reason=f"fabricated citations: {sorted(fabricated)[:5]}",
            coverage=coverage,
            cited_count=len(cited_inputs),
            input_count=len(inputs),
            missing_input_ids=frozenset(missing),
            fabricated_ids=frozenset(fabricated),
        )

    if require_any and not cited_inputs:
        return GateResult(
            passed=False,
            reason="no input citations referenced",
            coverage=0.0,
            cited_count=0,
            input_count=len(inputs),
            missing_input_ids=frozenset(missing),
            fabricated_ids=frozenset(),
        )

    if coverage < min_coverage:
        return GateResult(
            passed=False,
            reason=f"coverage {coverage:.0%} < min {min_coverage:.0%}",
            coverage=coverage,
            cited_count=len(cited_inputs),
            input_count=len(inputs),
            missing_input_ids=frozenset(missing),
            fabricated_ids=frozenset(),
        )

    return GateResult(
        passed=True,
        reason="ok",
        coverage=coverage,
        cited_count=len(cited_inputs),
        input_count=len(inputs),
        missing_input_ids=frozenset(missing),
        fabricated_ids=frozenset(),
    )
