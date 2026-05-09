"""LLM extractor: source text -> validated ExtractedClaim list."""

from __future__ import annotations

from pathlib import Path

from pydantic import ValidationError

from medbrain.extractors.schema import ExtractedClaim
from medbrain.llm import LLMError, call_json

PROMPT_PATH = Path(__file__).resolve().parent.parent.parent / "prompts" / "student_extract.md"


def _load_prompt() -> str:
    return PROMPT_PATH.read_text(encoding="utf-8")


def extract_from_pubmed_abstract(
    title: str,
    abstract: str,
    *,
    publication_types: list[str] | None = None,
) -> list[ExtractedClaim]:
    """Run the extractor against a PubMed abstract."""
    if not abstract.strip():
        return []

    system = _load_prompt()
    user_parts = [f"# Title\n{title}\n", f"# Abstract\n{abstract}\n"]
    if publication_types:
        user_parts.append(f"# Publication types\n{', '.join(publication_types)}")
    user_parts.append(
        "# Task\n"
        "Extract atomic qualified medical claims from the abstract above. "
        "Return a JSON ARRAY (not a paper-summary object). "
        "Each element MUST be an object with exactly these keys: "
        "subject, predicate, object, qualifiers, certainty, evidence_note.\n\n"
        "STRICT FIELD CONSTRAINTS:\n"
        "- `predicate` MUST be EXACTLY one of: treats, causes, resists, requires, "
        "contraindicates, prevents, co_occurs, recommends, supersedes. "
        "Map free-text relations to the closest enum. NO other values allowed. "
        "If you cannot map cleanly, drop the claim.\n"
        "- `certainty` MUST be EXACTLY one of: high, moderate, low, very_low. "
        "NO other values (no 'established', no 'low-to-moderate').\n"
        "- `qualifiers` MUST be an object with the nested shape: "
        "{population:{age_range, pregnancy, region, immune_status, comorbidities}, "
        "setting:{care_level, endemic_status}, "
        "dose_regimen:{drug, mg_per_kg, frequency, duration}, "
        "comparator, effect_size:{metric, value, ci_low, ci_high}}. "
        "Use null for unknown leaf values. DO NOT use a flat free-form qualifiers object.\n"
        "- `subject` and `object` MUST be non-empty strings.\n\n"
        "DO NOT summarize the paper. DO NOT return {\"title\":...,\"key_findings\":...}. "
        "DO NOT return an array of strings. "
        "If no qualified claims exist, return [].\n"
        "Your output MUST start with `[` and end with `]`. Output ONLY the JSON array, nothing else."
    )
    user = "\n".join(user_parts)

    try:
        raw = call_json(system, user)
    except LLMError:
        raise

    if isinstance(raw, dict):
        for key in ("claims", "items", "data", "results", "extractions"):
            if isinstance(raw.get(key), list):
                raw = raw[key]
                break
        else:
            list_vals = [v for v in raw.values() if isinstance(v, list)]
            if len(list_vals) == 1:
                raw = list_vals[0]

    if not isinstance(raw, list):
        raise ValueError(f"Extractor returned non-list: {type(raw).__name__}")

    out: list[ExtractedClaim] = []
    for i, item in enumerate(raw):
        try:
            out.append(ExtractedClaim.model_validate(item))
        except ValidationError as e:
            # Skip malformed claims, don't fail the whole batch.
            print(f"[extract] skipped claim {i}: {e}")
            continue
    return out
