# Gaps

Known holes, deferred decisions, things the spec didn't pin down. One section per gap. Resolve and move to changelogs when answered.

---

## Open

### Extraction prompt design

**Spec ref:** §14 (deferred to writing-plans).
**Gap:** No concrete LLM prompt yet for PubMed-abstract → qualified-claim JSON. Edge cases: multi-claim abstracts, nested findings, negations ("did not show benefit"), implicit population scoping.
**Proposed resolution:** First-pass prompt during Phase 1; iterate against 5-PMID test set. Prompt lives in `prompts/student_extract.md`.

### WHO PDF parsing strategy

**Spec ref:** §7.1.
**Gap:** WHO malaria guidelines are long PDFs with tables, footnotes, recommendation grades inline. `pypdf` text extraction may lose table structure. Recommendation extraction needs to preserve "evidence grade" assigned by WHO panel.
**Proposed resolution:** Try `pypdf` first; if table extraction is poor, escalate to `pdfplumber` or `unstructured`. Last resort: vision-LLM on rendered pages.

### ~~Graphify version pin~~ — RESOLVED via spec deviation

**Spec ref:** §7.3, §13 risks.
**Resolution (2026-05-01):** Did NOT pin graphify. Built SQL-direct networkx graph instead. Rationale documented in `medbrain/graph/__init__.py` and `.workspace/learnings.md`. Output shape is graphify-compatible if a future swap is needed.

### Dirty-tracker batch size for Brain trigger

**Spec ref:** §7.2.
**Gap:** "Hourly OR dirty_tracker exceeds threshold" — what threshold? Too small = constant Brain runs. Too large = stale memory.md.
**Proposed resolution:** Start at 25 dirty entities. Tune empirically in Phase 7.

### Auto-promote thresholds

**Spec ref:** §5.
**Gap:** "≥3 qualifier fields populated" — is this calibrated? Some valid claims naturally have <3 (e.g., a generic mechanism claim).
**Proposed resolution:** Track auto-promote vs review-queue rates during Phase 1; tune if review queue overflows or auto-promote misses obvious low-confidence cases.

### Test corpus selection

**Spec ref:** §14.
**Gap:** Need 50 PMIDs that cover: RCT, cohort, case report, contradicting findings, regional spread (Mekong + Africa), pediatric, pregnancy, supersession (older + newer guideline-cited paper).
**Proposed resolution:** Curate during Phase 7. Seed list will go in `tests/fixtures/test_corpus.csv`.

### Concept-name canonicalization (without UMLS)

**Spec ref:** §4 (concept_id reserved for v2).
**Gap:** Without UMLS, "P. falciparum" / "Plasmodium falciparum" / "P falciparum" all create different concept files. Pure surface-form leads to fragmentation.
**Proposed resolution:** v1 lightweight: maintain `aliases.json` per entity (manual + LLM-suggested); when extracting, check aliases before creating new concept file. v2 swaps in UMLS lookup.

### Salience initialization

**Spec ref:** §10.
**Gap:** New entity has zero query_count / citation_count → score = 0 → instantly archive-eligible. Need a grace period or default score.
**Proposed resolution:** New entities start with `score = 1.0` for 30 days; decay only kicks in after.

---

## Resolved

- **2026-05-01 — LLM library choice.** Initially picked anthropic SDK, REVERSED same day per user. Final: Claude CLI subprocess (`medbrain/llm.py`). No API key. Reserves option of giving agents the full Claude Code tool environment without rewiring.
