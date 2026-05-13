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

### ~~Brain ↔ active_learner format mismatch~~ — RESOLVED 2026-05-13 via path A

Resolved by rewriting `prompts/brain_questions.md` to emit qid blocks, patching
`medbrain/agents/brain.py` to parse + merge LLM output through
`questions_io.QuestionsFile`, and updating
`medbrain/tui/screens.py:_read_open_questions` to parse qid blocks. Defence in
depth: even if the LLM violates the "re-emit human Qs verbatim" rule,
`QuestionsFile.merge()` enforces human-source protection. 101/101 tests green.

Original gap (kept for context):

**Spec ref:** §7.2 + Phase 6 design.
**Discovered:** 2026-05-13 while wiring human-question protection.
**Gap:** `medbrain/agents/brain.py` writes `brain/questions.md` using the freeform "Answerable / Gaps" format from `prompts/brain_questions.md` (priorities `[P1] Q:`, no qid). `medbrain/agents/active_learner.py` reads `brain/questions.md` via `questions_io.QuestionsFile.parse`, which expects `## Q-YYYY-MM-DD-NNN` H2 blocks with `priority/status/created/topic/source` fields. Brain's output never produces qid blocks, so active_learner sees **zero open questions** even after a successful Brain run. Manually-added qid blocks (human-authored) work; Brain-emitted gaps are dead weight in the autonomous loop.
**Why it matters:** Without this fix, the textbook re-run will ingest evidence, Brain will generate "Gaps requiring new research" prose, but the active learner will never pick those gaps up and re-research. Self-extending loop is broken.
**Proposed resolution (two paths):**
- **(A) Change Brain's questions prompt to emit qid blocks.** Rewrite `prompts/brain_questions.md` so the output is a sequence of `## Q-YYYY-MM-DD-NNN` blocks with the field/body format `questions_io` parses. Drop the "Answerable / Gaps" sectioning (or keep it as a comment preamble). Active learner loop closes immediately. Risk: the freeform format is also consumed by the TUI for human reading; need to verify TUI still works (`medbrain/tui/screens.py:124` reads `(priority, text)` lines — appears to expect prose, not qid blocks, so changing format may break TUI display).
- **(B) Adapter layer.** Keep Brain's freeform output, add `medbrain/agents/questions_adapter.py` that parses the freeform "Gaps" section and emits qid blocks into a separate `brain/questions_inbox.md` that active_learner reads. Two files, more moving parts, no TUI breakage.
**Recommendation:** (A). Single source of truth. Fix TUI parser at the same time.

---

## Resolved

- **2026-05-01 — LLM library choice.** Initially picked anthropic SDK, REVERSED same day per user. Final: Claude CLI subprocess (`medbrain/llm.py`). No API key. Reserves option of giving agents the full Claude Code tool environment without rewiring.
