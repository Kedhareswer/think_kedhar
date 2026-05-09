"""Pydantic schema for LLM-extracted claim payloads. Validates extractor output."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field, field_validator

from medbrain.enums import Certainty, Predicate


class Population(BaseModel):
    age_range: str | None = None
    pregnancy: str | None = None
    region: str | None = None
    immune_status: str | None = None
    comorbidities: list[str] = Field(default_factory=list)

    @field_validator("comorbidities", mode="before")
    @classmethod
    def _coerce_comorbidities(cls, v: Any) -> list[str]:
        if v is None:
            return []
        if isinstance(v, str):
            return [s.strip() for s in v.split(",") if s.strip()]
        if isinstance(v, list):
            return [str(s).strip() for s in v if str(s).strip()]
        return []


class Setting(BaseModel):
    care_level: str | None = None
    endemic_status: str | None = None


class DoseRegimen(BaseModel):
    drug: str | None = None
    mg_per_kg: float | None = None
    frequency: str | None = None
    duration: str | None = None


class EffectSize(BaseModel):
    metric: str | None = None
    value: float | None = None
    ci_low: float | None = None
    ci_high: float | None = None


class Qualifiers(BaseModel):
    population: Population = Field(default_factory=Population)
    setting: Setting = Field(default_factory=Setting)
    dose_regimen: DoseRegimen = Field(default_factory=DoseRegimen)
    comparator: str | None = None
    effect_size: EffectSize = Field(default_factory=EffectSize)

    def to_storage(self) -> dict[str, Any]:
        return self.model_dump(exclude_none=False)

    def populated_count(self) -> int:
        """Count of qualifier fields with non-empty values. Used for auto-promote rule."""
        n = 0
        for k, v in self.population.model_dump().items():
            if v not in (None, "", []):
                n += 1
        for k, v in self.setting.model_dump().items():
            if v is not None and v != "":
                n += 1
        for k, v in self.dose_regimen.model_dump().items():
            if v is not None and v != "":
                n += 1
        if self.comparator:
            n += 1
        es = self.effect_size.model_dump()
        if es.get("value") is not None or es.get("metric"):
            n += 1
        return n


class ExtractedClaim(BaseModel):
    subject: str
    predicate: Predicate
    object: str
    qualifiers: Qualifiers = Field(default_factory=Qualifiers)
    certainty: Certainty = Certainty.MODERATE
    evidence_note: str = ""

    @field_validator("subject", "object")
    @classmethod
    def _strip_nonempty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("subject/object cannot be empty")
        return v
