# Changelogs

Append-only log of build progress. Newest at top.

---

## 2026-05-04

### Phase 6 complete (build) — active learning loop
- `medbrain/agents/active_learner.py`:
  - `pick_next(qfile)` — priority asc, created asc; only `open` status; returns None if none.
  - `run_once(dry_run, regen)` — load questions.md, pick, flip `open → in_progress` via atomic write, hand `Q.body` as topic to existing `Researcher.ingest_topic()`. Status stays `in_progress` after ingest; Brain decides resolution next pass.
  - `run_batch(max_questions, regen)` — loop until `max_questions` reached or no open Qs left.
  - **Two-step lifecycle:** active learner = "I tried"; Brain = "did the try work?". Honest signal separation.
- `scripts/active_learner.py`: CLI with `--max N` (default 1), `--dry-run`, `--no-regen`, `--check` (exit 0 if open Q exists, prints next pick).
- `prompts/brain_questions.md`: extended **Status changes** section with explicit in_progress evaluation rules. Brain LLM must evaluate every in_progress question against changed notes — resolve only if new evidence convincingly answers the specific clinical question; partial/off-target evidence keeps it in_progress; demoted to open if proven non-question.
- No code change in `medbrain/agents/brain.py` needed: existing prompt context already passed `[q for q in qfile.questions if q.status != "resolved"]`, so in_progress Qs were already in scope. The prompt change alone teaches the LLM what to do with them.
- `tests/test_active_learner.py` — 9 tests: pick_next none/highest-priority/oldest-tiebreak/skip-non-open, run_once no-open short-circuit, dry-run no flip, real run flips + delegates with regen=True, ingest exception captured but status still flipped (caller can re-open), batch stops on no-more-open.
- 79/79 tests green (previously 70).

### Phase 5 complete (build) — Dream agent: compact + derivative + decay
- `medbrain/dream/snapshot.py` — `take_snapshot()` copies concepts/, notes/, derivative/, archive/, brain.db into `brain/.dream-snapshots/<utc-iso>/`. `restore()` overwrites. `gc_old(keep=3)` retains N newest. `list_snapshots()` newest-first.
- `medbrain/dream/compactor.py` — per-file LLM rewrite with citation-set gate. Skips files < 256 bytes or with no `[c:<id>]` tokens. Rejects rewrites that drop/add citations or fail to shrink. Atomic write on pass.
- `prompts/dream_compact.md` — hard-rule prompt: preserve every citation, no new claims, no softening, keep supersession + contradictions visible.
- `medbrain/dream/derivative.py` — generates flashcards/mnemonics/analogies/gaps per entity (one LLM call per type) into `brain/derivative/<type>/<slug>.md`. Pulls existing concept synthesis + claim set as input. Renders LLM JSON to Markdown.
- `prompts/dream_{flashcards,mnemonics,analogies,gaps}.md` — strict JSON schema each. All require `[c:<id>]` citations to existing claim_ids; refuse to invent.
- `medbrain/dream/decay.py` — salience-based decay (per-entity, not per-claim — adapted to existing `Salience` schema). `ensure_salience_rows()` backfills missing entities. `run_decay(unread_threshold_days=180, decay_step=0.1, archive_floor=0.3)` decays idle rows, archives entities at floor — dumps claims to `brain/archive/claims_<ts>.jsonl`, deletes claims + EvidenceLedger + Salience rows. `touch(entity)` bumps last_accessed/query_count.
- `medbrain/agents/dream.py` — `run_dream(skip=(), dry_run=False, keep_snapshots=3)` orchestrator: snapshot → compact → derivative → decay → record. On unhandled exception: restore from snapshot, set `restored=1` on DreamRun. `is_due(cadence_days=7)` reads last successful run. Dry-run is no-op (no snapshot, no DreamRun row).
- `scripts/dream.py` — CLI with `--check` (cadence-due exit code), `--force`, `--dry-run`, `--cadence-days N`, `--skip {compact|derivative|decay}` (repeatable), `--keep-snapshots N`. README documents Windows Task Scheduler + cron recipes.
- `medbrain/api/menu.py` — `lookup`/`neighborhood` call `_touch_salience(key)`; `evidence_pack` touches all subject+object entities of returned claims. Decay now has real read signal.
- New SQL table `dream_runs` (DreamRun model): started_at, completed_at, files_compacted/skipped, derivatives_written, entities_decayed/archived, snapshot_path, restored (0/1), error.
- `tests/test_dream.py` — 18 tests: citation regex, citation-match true/false (drop + add), compact-skip-small, compact-rejects-drift, compact-writes-when-smaller, snapshot round-trip, snapshot GC keeps newest N, decay row backfill, decay step (0.9 after one pass), decay archives + writes JSONL + DELETEs, touch creates+bumps, is_due true on first run, is_due false when recent, dry-run is no-op, skip-all-stages still records DreamRun.
- 70/70 tests green (previously 52).

---

## 2026-05-01

### Phase 4 complete — knowledge graph + 8-primitive retrieval menu
- Added `networkx` dep.
- `medbrain/graph/builder.py` — SQL claims → `nx.MultiDiGraph`. Nodes = entities (lowercased keys, `label` preserves original casing). Edges = one per claim, attrs include claim_id, predicate, qualifiers, certainty, evidence_grade, status, supersedes_id, valid_from/until, current, source. Default skips pending_review/rejected/archived (`include_review=True` to surface queue).
- `medbrain/graph/communities.py` — greedy modularity over undirected projection; community_id `cNNN`, label = top-degree member.
- `medbrain/graph/audit.py` — isolated nodes, low-grade-only entities, stub entities (deg ≤ 2), opposing-predicate contradictions on same (subject, object) pair.
- `medbrain/graph/persist.py` — atomic writes to `brain/graph/{graph.json, communities.json, audit.json, version.json}`; `read_graph/communities/audit` for the menu layer.
- `medbrain/agents/graphify.py` — `run_graphify()` orchestrator; produces `GraphifyResult` with node/edge/community/contradiction counts.
- **Spec deviation, documented in `medbrain/graph/__init__.py`:** spec §7.3 named `safishamsi/graphify`. We use a SQL-direct internal builder because (1) graphify operates on prose, but our claims are structured (qualifiers/grades/supersession would be lost on prose round-trip), (2) the user's `/graphify` is a Claude Code skill not a Python lib, (3) zero external runtime dep + deterministic. Output shape is graphify-compatible so the menu primitives are stable across builder swaps.
- `medbrain/api/menu.py` — 8 primitives per spec §9: `lookup`, `neighborhood` (1–3 hops), `path` (k shortest), `community` (by id or topic), `scoped` (population_region/pregnancy + setting_endemic/care_level + min_certainty + current_only), `recent` (since ISO date), `gaps` (audit + questions.md), `evidence_pack` (claim_ids → SQL provenance + source). Consistent envelope: `{version, primitive, args, data, derivative_included, generated_at}`.
- `medbrain/api/server.py` — FastAPI on 127.0.0.1:7117, no auth (v1, trusted local consumer). All 8 primitives exposed; GET for read primitives, POST for `evidence_pack` (claim_ids body).
- `scripts/graphify_run.py` — rebuild graph artifacts; `--include-review` flag.
- `scripts/api.py` — launch the API server.
- `tests/test_graph.py` — 14 tests: graph build, communities, audit (contradiction detection works on AL-treats-falciparum vs AL-causes-falciparum), graphify writer, all 8 menu primitives (region scope, certainty floor, recent date filter, evidence_pack provenance, missing-entity safe path, envelope shape).
- 52/52 tests green.

### Phase 3 complete — Brain agent (memory.md + questions.md)
- New SQL table `brain_runs` (BrainRun model): tracks started_at, completed_at, concepts_read, topics_read, questions_added/resolved, error.
- `medbrain/agents/questions_io.py` — Question + QuestionsFile dataclasses; parse/serialize stable-ID `Q-YYYY-MM-DD-NNN` blocks; merge updates without losing creation timestamps; sort by priority then status.
- `prompts/brain_synthesize.md` — full-file rewrite prompt for memory.md (Active themes / Cross-concept observations / Supersession trail / Confidence map / Recent activity).
- `prompts/brain_questions.md` — JSON delta prompt for questions.md (`new_questions[]` + `updates[]`); never rewrites whole list; conservative bar for "real gap"; status flips to `resolved` only when evidence answers it.
- `medbrain/agents/brain.py` — `run_brain(force_full=...)`. Pulls `.md` files modified since last completed BrainRun, packs concepts + topics into prompt context, calls synthesis + gap-detect, atomic-writes memory.md and merges questions.md.
- `scripts/brain.py` — CLI; `--full` ignores last-run cutoff.
- 7 new tests in `tests/test_brain.py`: round-trip parser, merge semantics, qid auto-increment, sort order, end-to-end with mocked LLM, no-change short-circuit (LLM not called when nothing dirty).
- 38/38 tests green.

### Phase 2 complete — concepts/notes regeneration
- `medbrain/regen/slug.py` — ASCII-fold + hyphen slugifier; "P. falciparum" → "p-falciparum"; max_len truncation; "" → "unknown".
- `medbrain/regen/atomic.py` — `.tmp` + `os.replace` atomic write; mkdir parents.
- `medbrain/regen/topics.py` — fixed predicate→topic map: treats/recommends → treatment/<obj>; resists → resistance/<obj>; causes → etiology; prevents → prevention; contraindicates → safety/<subj>; requires → diagnostics/<subj>; co_occurs → associations/<subj>; supersedes → none.
- `prompts/concept_note.md` — concept-note synthesizer; structured Markdown with inline `[c:<id>]` citations; supersession-aware; ≤600 word target; no hallucination rule.
- `prompts/topic_note.md` — same shape for topic notes; ≤800 words.
- `medbrain/regen/concepts.py` — pulls all claims for entity (subject OR object), sends LLM, atomic-writes `concepts/<slug>.md`.
- `medbrain/regen/notes.py` — pulls claims that map to a topic (re-derives via predicate mapper), atomic-writes `notes/<topic>.md`.
- `medbrain/regen/coordinator.py` — `regenerate_dirty()` walks `dirty_tracker`, dispatches per row, marks `processed_at` on success.
- Hooked Student to mark topic dirty (in addition to entity) using `topics_for()`.
- Hooked Researcher tail: `ingest_topic(..., regen=True)` runs `regenerate_dirty()` after the ingest loop if any claim was inserted.
- `scripts/regen.py` — standalone CLI for catch-up regen.
- `scripts/student.py` — `--no-regen` flag for ingest-only debug; output now reports regen counts + first 10 paths.
- `tests/test_regen.py` — 11 tests: slug edge cases, atomic write idempotency, topic mapping per predicate, end-to-end regen with mocked LLM, dirty_tracker.processed_at marking, no-claim entity skipped.
- Fix: `medbrain/regen/{concepts,notes}.py` now reference `medbrain.config` namespace at call-time (not module-level import) so test fixtures that monkeypatch `BRAIN_DIR` + reload config actually take effect.
- All 31 tests green.

### Input-model rewire — natural-language topic, not PMID
- User correction: input is a research topic, not a PMID. PMID was a leaky implementation detail.
- Added `medbrain/tools/pubmed.py:search(query, retmax)` — eutils esearch wrapper.
- Added `prompts/research_plan.md` — LLM planner prompt (scope classifier + decomposer + query generator + stop criteria).
- Added `medbrain/extractors/plan.py` — pydantic ResearchPlan / QueryItem / StopCriteria; `plan_research(topic)` returns validated plan.
- Added `medbrain/agents/researcher.py` — `ingest_topic(topic)`: plan → for each query (esearch → per-PMID Student loop) with saturation early-stop and global paper cap.
- Rewired `scripts/student.py` to take a topic string. Added `--plan-only` flag for plan inspection.
- Added `scripts/ingest_pmid.py` — kept the per-PMID path as a debug entrypoint.
- Added 7 tests in `tests/test_researcher.py` (saturation logic, plan validation, stop-criteria clamping).
- Spec §2 + §7.1 updated: input model is topic; malaria stays the v1 focus area but architecture is topic-agnostic.
- 20/20 tests green.

### LLM backend swap — Claude CLI, not Anthropic SDK
- User correction: brain system uses Claude CLI subprocess, not the SDK.
- Rewrote `medbrain/llm.py` to spawn `claude --print --model <m> --append-system-prompt <s> --output-format text <user>`.
- `shutil.which("claude")` resolves the npm-installed `.cmd` on Windows; `shell=False` works.
- Env scrub strips `CLAUDECODE`, `CLAUDE_CODE_*`, `ANTHROPIC_API_KEY` before spawn.
- Dropped `anthropic` from pyproject deps. `pip uninstall anthropic` succeeded.
- `.env.example` no longer requires API key. README updated.
- 13/13 tests still green (LLM-dependent paths weren't tested live).

### Phase 1 complete (build) — ingestion primitives wired
- `medbrain/llm.py` — Anthropic SDK wrapper with retry on 429/5xx, JSON helper that strips ``` fences.
- `medbrain/tools/pubmed.py` — eutils `efetch` for one PMID, lxml XML parser into `PubMedArticle` dataclass (title, abstract, pub types, date, authors, MeSH).
- `medbrain/tools/publication_type.py` — PubMed publication-type → EvidenceGrade mapper, picks strongest grade across multiple types.
- `prompts/student_extract.md` — extractor prompt with strict JSON schema, qualifier rules, predicate enum mapping, certainty grading.
- `medbrain/extractors/schema.py` — pydantic models (Population, Setting, DoseRegimen, EffectSize, Qualifiers, ExtractedClaim) with `populated_count()` for auto-promote rule.
- `medbrain/extractors/claims.py` — calls LLM, validates each claim, skips malformed ones (don't fail batch).
- `medbrain/extractors/novelty.py` — dedup key (subject+predicate+object+region+endemic+pregnancy), opposing-predicate contradiction check, auto-promote routing per spec §5.
- `medbrain/agents/student.py` — orchestrates fetch → extract → novelty gate → insert + evidence ledger entry + dirty tracker marks.
- `scripts/student.py` — CLI entrypoint.
- `tests/test_phase1.py` — 10 tests: pub-type mapping, qualifier counting, dedup, region distinction, contradiction detection, auto-promote rules, XML parsing.
- All 13 tests green (3 from Phase 0 + 10 new). CLI loads (`--help` works). Live ingest requires user-set `ANTHROPIC_API_KEY`.

### Phase 0 complete — project skeleton + schema
- `pyproject.toml` with deps (sqlalchemy, anthropic, httpx, pypdf, fastapi, uvicorn, lxml, pydantic).
- Directory tree: `medbrain/{agents,tools,api,extractors}/`, `scripts/`, `prompts/`, `tests/`.
- `medbrain/enums.py` — Predicate, EvidenceGrade (+ HIGH_GRADES set), Certainty, ClaimStatus, SourceType.
- `medbrain/models.py` — Source, Claim, EvidenceLedger, DirtyTracker, Salience (per spec §4 + §10).
- `medbrain/db.py` — engine, SessionFactory, `init_schema()`, `session_scope()`.
- `medbrain/config.py` — env-driven paths, `ensure_brain_dirs()`.
- `scripts/init_db.py` — idempotent init.
- `tests/test_models.py` — 3 tests, all green: schema creation, claim round-trip, dirty-tracker round-trip.
- `.venv` created, `pip install -e ".[dev]"` succeeded.
- Smoke test: `python scripts/init_db.py` produces `brain/brain.db` with all 5 tables; `pytest` passes.
- Fixed `datetime.utcnow()` deprecation → `datetime.now(UTC)`.

### Brainstorming + spec
- Q1–Q7 locked (malaria depth-first; PubMed+WHO; qualified-claim schema; tiered autonomy + dream firewall; batched consolidation; three independent agent loops; graphify substrate + 8-primitive menu).
- Design spec: `docs/superpowers/specs/2026-05-01-medbrain-design.md`.
- Self-review fixes: evidence-grade ordering explicit; questions.md priority/status spec; salience score formula.

### Cleanup
- Removed `medbrain/` (old heartbeat) and `files_unzipped.zip_unzipped/` (old planning docs).
- `.workspace/` initialized for build-only tracking.
