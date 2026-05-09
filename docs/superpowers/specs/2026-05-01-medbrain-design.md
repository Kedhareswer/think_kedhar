# MedBrain — Design Spec

**Date:** 2026-05-01
**Status:** Draft for review
**Scope:** v1 — perpetually-learning medical knowledge base for malaria, RAGed by an external CDS.

---

## 1. Goal

Replicate a doctor's mental model of a medical specialty: vast, growing, non-duplicating, with notes/memory/dream-cycle teasers, that learns continuously and never forgets (only supersedes). Consumed via RAG by a separate Clinical Decision Support system. **Not** a CDS itself — a substrate for one.

## 2. Scope

- **Input model:** natural-language research topic. Examples: `"what is malaria"`, `"artemisinin resistance in pregnancy"`, `"vaginal yeast infection treatment"`, `"virology overview"`. The Student agent plans + executes the research session (decomposes broad topics, runs PubMed searches, ingests top results, stops at saturation or paper-cap).
- **Specialty focus area:** malaria, but the architecture is **topic-agnostic** — it accepts any biomedical topic. Malaria is the v1 test focus because it stresses every architectural component (active resistance → supersession; multi-domain → dream cycle; strong evidence pyramid; geographic scoping; WHO update cadence).
- **Sources:** PubMed (abstracts via eutils esearch + efetch) + WHO guidelines (Phase 1.5).
- **Out of scope for v1:** ClinicalTrials.gov; DailyMed; case literature behind paywalls; entity normalization to UMLS CUIs (hooks reserved, populated in v2); a CDS interface (consumer is external).

The PubMed-only source mix forces a real claim schema (research findings + authoritative recommendations once WHO lands + supersession events). PMID is no longer the input contract — it is an internal unit. Per-PMID ingestion is exposed as a debug script (`scripts/ingest_pmid.py`) but normal use is `scripts/student.py "<topic>"`.

## 3. Architecture overview

Four agents, each on its own loop, communicating via SQL + filesystem:

```
Sources (PubMed RSS, WHO updates)
       │
       ▼
   STUDENT  (continuous, per-paper) — researches, extracts, regenerates concepts/notes
       │
       ▼
   brain.db  +  concepts/*.md  +  notes/*.md
       │
       ▼
   BRAIN    (hourly, after Student dirty count) — synthesizes memory.md, questions.md
       │
       ▼
   GRAPHIFY (hourly, after Brain) — rebuilds knowledge graph from .md corpus
       │
       ▼
   Retrieval menu  — exposed to CDS (8 named primitives)

   DREAM    (weekly) — compacts .md, generates derivative/, decays low-salience
```

Feedback loop: Brain's `questions.md` is Student's research backlog. Student picks gaps to actively investigate, not just whatever PubMed serves up.

## 4. Atomic unit — qualified claim

Source of truth. SQL row.

```
claim_id            uuid
subject_text        str
subject_concept_id  str   (nullable, reserved for v2 UMLS normalization)
predicate           enum  (treats, causes, resists, requires, contraindicates,
                           prevents, co-occurs, recommends, supersedes)
object_text         str
object_concept_id   str   (nullable)

qualifiers          JSON
  population: { age_range, pregnancy, region, immune_status, comorbidities[] }
  setting:    { care_level, endemic_status }
  dose_regimen: { drug, mg_per_kg, frequency, duration }
  comparator: str
  effect_size: { metric, value, ci_low, ci_high }

certainty           enum  (high, moderate, low, very_low)
temporal_validity   { valid_from, valid_until }   valid_until=NULL means current
source_id           FK    → sources table
evidence_grade      enum  (meta_analysis, RCT, cohort, case_control,
                           case_report, expert_opinion, guideline)
supersedes_id       uuid  (nullable, FK to claim_id of replaced claim)
status              enum  (auto_promoted, pending_review, rejected, archived)
ingested_at         timestamp
```

NULL qualifiers mean "unspecified, generic scope." Population/setting NULL is fine for older or thin papers; treated as universal-scope at retrieval time.

## 5. Trust posture

Tiered autonomy with dream-cycle firewall.

**Evidence grade ranking** (high → low, used for auto-promote gate):
`meta_analysis` > `RCT` > `guideline` > `cohort` > `case_control` > `case_report` > `expert_opinion`. Note: `guideline` is treated as high-quality because WHO malaria guidelines are consensus expert review of underlying RCTs/MAs; the source ledger still records the underlying citations.

**Auto-promote** when ALL: evidence_grade ∈ {`meta_analysis`, `RCT`, `guideline`, `cohort`}, no contradictions detected, all entities already known to brain, ≥3 qualifier fields populated.

**Queue for review** otherwise. Status = `pending_review`. Lives in same table; retrieval excludes by default.

**Auto-reject** review-queue claims after 90 days unreviewed.

**Dream firewall:** synthetic outputs from Dream agent (analogies, mnemonics, flashcards, abstracted patterns) live in `derivative/` namespace. Never auto-promote to primary. Never feed back as evidence. Always tagged at retrieval time.

## 6. Storage layout

```
brain/
├── brain.db                       # SQL: claims, sources, evidence ledger, dirty tracker
├── concepts/                      # one file per entity (drug, organism, gene, syndrome)
│   ├── chloroquine.md
│   ├── artemisinin.md
│   ├── p_falciparum.md
│   └── pfkelch13.md
├── notes/                         # synthesized topic notes
│   ├── treatment/
│   │   ├── uncomplicated_falciparum.md
│   │   └── severe_malaria.md
│   ├── resistance/
│   │   ├── artemisinin_resistance.md
│   │   └── chloroquine_resistance.md
│   └── epidemiology/
├── memory.md                      # Brain output: cross-concept synthesis
├── questions.md                   # Brain output: gaps + research backlog
├── derivative/                    # Dream output, firewalled per §5
│   ├── flashcards/
│   ├── mnemonics/
│   ├── analogies/
│   └── gaps/
├── archive/                       # decayed claims/notes (Dream rotation)
├── changelog/
│   └── YYYY-MM-DD.md              # what changed each day
└── graph/
    ├── graph.json                 # graphify output
    ├── communities.json           # clustered topics
    ├── audit.json                 # gaps / sparse regions
    └── graph.html                 # debug visualization
```

SQL is source of truth. `.md` files are derived views, regenerated by Student. Graph is derived from `.md`, regenerated by Graphify step.

## 7. Agents

### 7.1 Student — researcher

**Trigger:** natural-language topic input (CLI arg, scheduled topic queue, OR top unprocessed question pulled from `questions.md`). Brain emits questions in `questions.md` with explicit priority (1=high, 2=med, 3=low) and `status` (open/in_progress/resolved); Student picks highest-priority `open` question, marks it `in_progress`, treats the question text as a research topic.

**Topic flow (added):**
1. **Plan** the research session via LLM (`prompts/research_plan.md`): classify scope (very_broad / broad / focused / specific), decompose if broad, generate PubMed search queries with field tags + MeSH, set `max_papers` per query and `stop_criteria` (saturation window + duplicate ratio + global cap).
2. **For each query:** PubMed esearch → list of PMIDs → per-PMID ingest loop, stopping early when the saturation window crosses the duplicate-ratio threshold or the global paper cap is hit.

**Per-PMID inner loop (unchanged from prior spec):**

**Process:**
1. Fetch source (PubMed eutils for abstracts; HTTP + PDF parser for WHO docs).
2. LLM-extract qualified claims per §4 schema.
3. Novelty gate: dedup against existing claims, contradiction check, evidence grade from publication type metadata.
4. Per §5 trust posture: insert with status=`auto_promoted` or `pending_review`.
5. Mark dirty entities (subject + object) and dirty topics in `dirty_tracker` table.
6. Regenerate `concepts/<entity>.md` for each dirty entity from full claim set.
7. Regenerate `notes/<topic>.md` for each dirty topic.
8. Atomic file write: `.tmp` + rename, to avoid Brain reading partial files.

**Cadence:** continuous; per-paper transaction.

**Failure mode:** per-paper error logged, paper skipped, loop continues.

**Implementation:** Claude Code subprocess (matches existing student-session pattern in heartbeat).

### 7.2 Brain — synthesizer

**Trigger:** scheduled hourly OR `dirty_tracker` row count exceeds threshold.

**Process:**
1. Read `dirty_tracker`; pull list of entities + topics changed since last Brain run.
2. Read changed `concepts/*.md` + `notes/*.md`.
3. Read current `memory.md`, `questions.md`.
4. LLM pass: cross-link entities, identify big-picture patterns, detect gaps and contradictions.
5. Update `memory.md` with cross-concept synthesis observations.
6. Update `questions.md`: add new gaps, mark resolved questions, prioritize backlog.
7. Clear processed rows from `dirty_tracker`.

**Cadence:** hourly.

**Failure mode:** Brain crash doesn't block Student. `memory.md` may be stale; reads still work from `concepts/*.md`.

### 7.3 Graphify — graph builder

**Trigger:** scheduled hourly, after Brain run completes.

**Process:**
1. Read all `concepts/*.md`, `notes/*.md`, `memory.md`.
2. Run graphify → produces `graph/graph.json`, `communities.json`, `audit.json`, `graph.html`.
3. Post-process: decorate graph nodes with structured qualifier attributes from SQL claims (so `scoped` retrieval primitive can filter precisely on population/setting/certainty).
4. Atomic replace of `graph/` artifacts.

**Cadence:** hourly, after Brain.

**Failure mode:** graph build failure → previous graph artifacts retained; CDS still queryable against last-known-good graph.

**Dependency:** graphify pinned version. Graph schema versioned in `graph/version.json`.

### 7.4 Dream — compactor

**Trigger:** weekly (Sunday night) OR total `.md` token count exceeds threshold.

**Process:**
1. Operate on a git branch (rollback-safe).
2. Read every `.md` file.
3. Identify redundancy across files (same claim phrased multiply).
4. Rewrite each file: same info density, fewer tokens.
5. Generate firewalled artifacts:
   - `derivative/flashcards/*.md` — spaced-repetition cards.
   - `derivative/mnemonics/*.md` — pattern-recall aids.
   - `derivative/analogies/*.md` — cross-domain links.
   - `derivative/gaps/*.md` — synthesized from `questions.md` + graph audit.
6. Decay: claims/notes with salience score below threshold (no queries, no citations, no recent updates) move to `archive/`. Never deletion.
7. Commit branch; if QA passes, merge to main.

**Cadence:** weekly.

**Failure mode:** branch operation; if output looks wrong, branch discarded; main brain unchanged.

## 8. Orchestration

Three independent loops, shared filesystem + SQL.

- Student: subprocess, triggered by RSS poller / file watcher / questions.md picker.
- Brain: cron hourly.
- Graphify: cron hourly, offset 15min after Brain.
- Dream: cron weekly Sunday 23:00.

No message queue. Coordination via `dirty_tracker` table + atomic `.md` writes (`.tmp` + rename) + git branches for Dream rollback.

Backpressure: if Student outpaces Brain, `dirty_tracker` accumulates; Brain processes the backlog on its next run. No queue overflow.

## 9. Retrieval API — closed menu (v1.0)

Brain exposes 8 named primitives. CDS calls one or composes several. Stable contract; additive evolution.

| # | Primitive | Input | Returns |
|---|-----------|-------|---------|
| 1 | `lookup` | entity name | full subgraph for one entity (concept.md content + 1-hop neighbors + claim_ids) |
| 2 | `neighborhood` | entity, hops (1–3) | N-hop subgraph |
| 3 | `path` | entity_a, entity_b | shortest path(s) between two entities |
| 4 | `community` | community_id or topic | cluster graphify identified |
| 5 | `scoped` | filter spec (population, setting, certainty, current_only) | subgraph filtered by qualifiers |
| 6 | `recent` | since_date | nodes/edges changed since date |
| 7 | `gaps` | (none) | graphify audit output — sparse regions + questions.md content |
| 8 | `evidence_pack` | claim_ids[] | full SQL provenance for each claim (source, grade, certainty, supersession chain) |

All return a consistent JSON envelope:

```json
{
  "version": "1.0",
  "primitive": "lookup",
  "args": { "entity": "artemether-lumefantrine" },
  "data": { ... primitive-specific payload ... },
  "derivative_included": false,
  "generated_at": "2026-05-01T14:00:00Z"
}
```

`derivative_included` defaults false. CDS opts in explicitly to receive Dream-derived content (always tagged in payload per §5 firewall).

## 10. Database schema

SQL (SQLite v1, Postgres-compatible). SQLAlchemy models, no .sql file (per existing heartbeat convention).

**Tables:**

- `claims` — qualified claims per §4.
- `sources` — PubMed PMID, WHO doc ID, retrieval URL, fetched_at, source_type.
- `evidence_ledger` — claim_id → source_id → evidence_grade → ingested_at; version-controlled (insert-only).
- `dirty_tracker` — entity, topic, marked_at, processed_at (NULL until Brain processes it).
- `review_queue` — view: claims WHERE status='pending_review'.
- `salience` — entity → query_count, citation_count, last_accessed. Salience score (used by Dream decay): `score = log(1 + query_count) + 0.5 * log(1 + citation_count) + recency_factor`, where `recency_factor = exp(-days_since_last_access / 90)`. Score below 0.1 triggers archive on Dream run.

## 11. Implementation phases (high-level only; detailed plan in writing-plans output)

Phase 1: Schema migration heartbeat → qualified claim. Backfill existing claims with NULL qualifiers.
Phase 2: Student rewrite — concepts/*.md and notes/*.md regeneration on dirty entity.
Phase 3: Brain agent — hourly synthesis to memory.md, questions.md.
Phase 4: Graphify integration + retrieval menu (8 primitives).
Phase 5: Dream agent — weekly compaction + derivative generation.
Phase 6: questions.md feedback into Student backlog (active learning loop).

## 12. Out of scope

- CDS itself.
- UMLS / SNOMED / ICD entity normalization (v2).
- Multi-specialty (replicate per specialty in v3).
- Web UI for review queue (v2; CLI suffices for v1).
- Distributed deployment (single-host v1).
- Real-time API (graph rebuilt hourly; sub-hour freshness deferred).
- Authentication on retrieval menu (v1 assumes trusted local consumer).

## 13. Risks and mitigations

| Risk | Mitigation |
|------|------------|
| LLM hallucinates qualifier values | Validate against source text; flag with low certainty if extraction unsure |
| Graphify upstream changes break menu | Pin version; thin wrapper translates menu primitives → graphify queries |
| Review queue grows unbounded | 90-day auto-reject; Brain agent surfaces oldest items in questions.md |
| Dream cycle pollutes primary | §5 firewall: always tagged, separate namespace, never auto-promotes |
| Student loops forever on a hard paper | Per-paper timeout + retry budget; logged failure, skip |
| Concept.md write race vs Brain read | Atomic write (.tmp + rename); Brain reads checksum, retries if mismatched |
| graph.json freshness lag (up to 1hr) | Acceptable for KB use case; documented in retrieval contract |
| Salience decay loses important cold facts | Never deletion — `archive/` retains; salience can be boosted by Brain re-citation |

## 14. Open items deferred to writing-plans

- Concrete extraction prompts for Student (PubMed abstract → claims; WHO PDF → claims).
- Brain prompt for synthesis pass.
- Dream compaction prompt (preserves info density rule).
- Graphify post-processor for qualifier decoration.
- Cron / orchestrator script structure.
- Retrieval menu HTTP/JSON-RPC choice.
- Test corpus for end-to-end validation (which 50 PMIDs exercise every architectural component).
