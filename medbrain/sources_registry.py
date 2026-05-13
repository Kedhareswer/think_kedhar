"""Trusted data sources — single registry every agent and exporter consults.

Every claim that enters the knowledge base MUST cite at least one source from
this registry. The registry assigns each source a stable short_code (used in
the Master sheet's `Sources` column) and records the access mechanism, evidence
tier, and license posture so reviewers can trace any cell back to a verifiable
origin.

Tiers (used by the auto-promote gate in §5 of the design spec):
  tier_1 — peer-reviewed primary literature or authoritative guideline
  tier_2 — curated database derived from peer-reviewed primary
  tier_3 — government / professional-body operational data
  tier_4 — community / encyclopedic (treat as starting point, not evidence)

Access:
  api      — programmatic, callable from an agent loop
  mcp      — exposed as a Model Context Protocol server (Claude Code tool)
  manual   — needs human-curated CSV / scrape

Every agent prompt that asks the LLM to invoke a connector must reference the
short_code declared here so the Sources cell stays consistent.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


Tier = Literal["tier_1", "tier_2", "tier_3", "tier_4"]
Access = Literal["api", "mcp", "manual"]


@dataclass(frozen=True)
class Source:
    short_code: str          # what appears in Sources column, e.g. "PubMed"
    name: str                # human-readable full name
    url: str                 # canonical URL
    tier: Tier
    access: Access
    description: str         # one-liner reviewers can scan
    populates: tuple[str, ...]   # which Master-sheet columns/sheets it feeds


REGISTRY: list[Source] = [
    # ===== tier 1 — peer-reviewed primary literature =====
    Source(
        short_code="PubMed",
        name="PubMed (NCBI/NLM, U.S. National Library of Medicine)",
        url="https://pubmed.ncbi.nlm.nih.gov",
        tier="tier_1",
        access="mcp",
        description="Peer-reviewed biomedical literature. Primary source for all clinical claims. Accessed via the PubMed MCP connector (article search, full-text fetch, related-article walk).",
        populates=("Conditions/Causes", "Conditions/Treatment", "Conditions/Prevention",
                   "Conditions/Outlook", "Medications/Mechanism", "Medications/Side Effects",
                   "Lab tests/Interpretation"),
    ),
    Source(
        short_code="WHO",
        name="World Health Organization guidelines",
        url="https://www.who.int/publications/guidelines",
        tier="tier_1",
        access="manual",
        description="WHO clinical and public-health guidelines. Authoritative for treatment standards-of-care and prevention recommendations. Currently scraped manually; planned MCP integration.",
        populates=("Conditions/Treatment", "Conditions/Prevention", "Medications/Indication",
                   "Medications/Dosage"),
    ),
    Source(
        short_code="ClinicalTrials",
        name="ClinicalTrials.gov (NIH/NLM trial registry)",
        url="https://clinicaltrials.gov",
        tier="tier_1",
        access="mcp",
        description="Registry of FDA-regulated clinical studies worldwide. Use for evidence-strength claims about an intervention. Accessed via the Clinical Trials MCP connector.",
        populates=("Conditions/Treatment", "Medications/Indication"),
    ),

    # ===== tier 2 — curated databases =====
    Source(
        short_code="ChEMBL",
        name="ChEMBL (EMBL-EBI bioactive-compound database)",
        url="https://www.ebi.ac.uk/chembl",
        tier="tier_2",
        access="mcp",
        description="Curated database of bioactive molecules. Use for drug mechanism-of-action, target binding, ADMET properties. Each ChEMBL record traces back to its primary literature. Accessed via the ChEMBL MCP connector.",
        populates=("Medications/Mechanism", "Medications/Indication", "Medications/Drug Class",
                   "Medications/Drug Interactions"),
    ),
    Source(
        short_code="ICD-10",
        name="ICD-10-CM / ICD-10-PCS (2026 code set)",
        url="https://www.cdc.gov/nchs/icd/icd-10-cm",
        tier="tier_2",
        access="mcp",
        description="Official diagnosis (CM) and inpatient procedure (PCS) code system. Use to populate the System and Condition canonical codes. Accessed via the ICD-10 MCP connector.",
        populates=("Conditions/System", "Conditions/Tags", "SurgeriesProcedures/Top Level Category"),
    ),
    Source(
        short_code="MedlinePlus",
        name="MedlinePlus (NIH consumer health information)",
        url="https://medlineplus.gov",
        tier="tier_2",
        access="manual",
        description="Plain-language patient-facing summaries. Use as the model for The Gist column tone. Reference Master sheet cites MedlinePlus heavily.",
        populates=("Conditions/Overview", "Conditions/The Gist", "Conditions/Symptoms",
                   "Medications/The Gist"),
    ),

    # ===== tier 3 — operational / regulatory data =====
    Source(
        short_code="NAFDAC",
        name="National Agency for Food and Drug Administration and Control (Nigeria)",
        url="https://nafdac.gov.ng",
        tier="tier_3",
        access="manual",
        description="Nigerian drug regulatory authority. Source of NAFDAC numbers and approved brand names in Nigeria. Currently a manual lookup; eventual scraper planned.",
        populates=("Medications/NAFDAC number", "Medications/BRAND NAMES in Nigeria"),
    ),
    Source(
        short_code="FMOH-MFL",
        name="Federal Ministry of Health — Nigeria Master Facility List",
        url="https://hfr.health.gov.ng",
        tier="tier_3",
        access="manual",
        description="Nigerian facility registry. Source of the 50k-row Hospital Addressbook. CSV import planned.",
        populates=("Hospital Addressbook/*",),
    ),
    Source(
        short_code="MDCN",
        name="Medical and Dental Council of Nigeria",
        url="https://mdcn.gov.ng",
        tier="tier_3",
        access="manual",
        description="Nigerian provider-type and specialty registry. Source of Provider type & Specialty sheet.",
        populates=("Provider type & Specialty/*",),
    ),

    # ===== tier 4 — encyclopedic (only as orientation, never sole source) =====
    Source(
        short_code="Wikipedia",
        name="Wikipedia (English medical articles)",
        url="https://en.wikipedia.org",
        tier="tier_4",
        access="manual",
        description="Encyclopedic overview. Allowed ONLY as an orientation source and ONLY when a tier_1 or tier_2 source is co-cited. Never the sole source for a clinical claim.",
        populates=(),
    ),
]


def by_short_code(code: str) -> Source | None:
    for s in REGISTRY:
        if s.short_code.lower() == code.lower():
            return s
    return None


def trusted_for(column: str) -> list[Source]:
    """Return registry entries that declare they populate the given Master-sheet column.

    `column` matches `populates` entries either exactly (`Conditions/Overview`)
    or by sheet wildcard (`Hospital Addressbook/*` for any column on that sheet).
    """
    out: list[Source] = []
    for s in REGISTRY:
        for p in s.populates:
            if p == column:
                out.append(s); break
            if p.endswith("/*") and column.startswith(p[:-1]):
                out.append(s); break
    return out


def registry_markdown() -> str:
    """Render the registry as a Markdown table for inclusion in prompts and docs."""
    lines = [
        "| Code | Source | Tier | Access | Use for |",
        "| --- | --- | --- | --- | --- |",
    ]
    for s in REGISTRY:
        cols = ", ".join(s.populates) if s.populates else "—"
        lines.append(f"| `{s.short_code}` | {s.name} | {s.tier} | {s.access} | {cols} |")
    return "\n".join(lines)


if __name__ == "__main__":
    print(registry_markdown())
