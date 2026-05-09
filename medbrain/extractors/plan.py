"""LLM research planner: natural-language topic -> PubMed search plan."""

from __future__ import annotations

from enum import Enum
from pathlib import Path

from pydantic import BaseModel, Field, ValidationError

from medbrain.llm import LLMError, call_json

PROMPT_PATH = Path(__file__).resolve().parent.parent.parent / "prompts" / "research_plan.md"


class Scope(str, Enum):
    VERY_BROAD = "very_broad"
    BROAD = "broad"
    FOCUSED = "focused"
    SPECIFIC = "specific"


class QueryItem(BaseModel):
    subtopic: str = "overall"
    pubmed_query: str
    max_papers: int = Field(default=5, ge=1, le=50)
    rationale: str = ""


class StopCriteria(BaseModel):
    max_total_papers: int = Field(default=30, ge=1)
    saturation_window: int = Field(default=3, ge=1)
    duplicate_ratio_threshold: float = Field(default=0.7, ge=0.0, le=1.0)


class ResearchPlan(BaseModel):
    topic: str
    scope: Scope
    decomposition: list[str] = Field(default_factory=list)
    queries: list[QueryItem]
    stop_criteria: StopCriteria = Field(default_factory=StopCriteria)
    notes: str = ""


def _load_prompt() -> str:
    return PROMPT_PATH.read_text(encoding="utf-8")


_USER_SCHEMA_REMINDER = (
    "Required top-level keys (all five MUST appear): topic, scope, decomposition, queries, stop_criteria. "
    "Optional: notes. Do not invent other keys (no `summary`, no `background`, no `key_rct_findings`, "
    "no `landmark_references`, no `clinical_bottom_line`, etc.). "
    "Each entry of `queries` MUST be an object with EXACTLY these keys: "
    "`subtopic` (string), `pubmed_query` (string — DO NOT abbreviate to `q`), "
    "`max_papers` (integer >= 1), `rationale` (string). "
    "Do NOT use alternate field names like `q`, `query`, `search`, `source`. "
    "Output the JSON object only, no analysis, no fenced prose.\n\n"
)


def _validation_feedback(err: ValidationError) -> str:
    missing = []
    for e in err.errors():
        if e.get("type") == "missing":
            missing.append(".".join(str(p) for p in e.get("loc", [])))
    if missing:
        return (
            f"Your previous response was REJECTED — these required fields were missing: {missing}. "
            "Re-output the FULL JSON object with EVERY required top-level key "
            "(topic, scope, decomposition, queries, stop_criteria). Do not include any other top-level keys."
        )
    return f"Your previous response was REJECTED with validation errors: {err}."


def plan_research(topic: str) -> ResearchPlan:
    """Ask LLM to plan how to research a topic. Returns validated ResearchPlan.

    One automatic retry on schema-validation failure, with explicit feedback so the
    LLM has a chance to correct (claude-sonnet-4-6 likes to dump medical analysis
    instead of a search plan; the retry prompt names the missing keys directly).
    """
    topic = topic.strip()
    if not topic:
        raise ValueError("topic must be non-empty")

    system = _load_prompt()
    user_base = f"{_USER_SCHEMA_REMINDER}# Topic\n{topic}"

    last_err: ValidationError | None = None
    for attempt in range(2):
        user = user_base if attempt == 0 else (
            user_base + "\n\n# Retry feedback\n" + _validation_feedback(last_err)  # type: ignore[arg-type]
        )
        raw = call_json(system, user, timeout=120.0)
        try:
            return ResearchPlan.model_validate(raw)
        except ValidationError as e:
            last_err = e
            continue

    raise LLMError(f"Planner returned invalid plan after retry: {last_err}")
