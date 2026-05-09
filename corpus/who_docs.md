# WHO Guideline Corpus (Phase 7)

**Status: deferred — blocked on Phase 1.5 (WHO PDF fetcher + pypdf parser).**

The Phase 7 spec calls for 3 WHO docs (1 current + 2 superseded versions of the same guideline) to exercise the `current` / `superseded` flag. The fetcher is not yet built (`medbrain/tools/` lacks `who.py`; `pypdf` not in deps).

## Planned trio (drop in once Phase 1.5 lands)

| slot | title | year | status |
|------|-------|------|--------|
| current     | WHO Guidelines for the Treatment of Malaria, 3rd ed. (or successor) | 2015+ | current     |
| superseded1 | WHO Guidelines for the Treatment of Malaria, 2nd ed.                | 2010  | superseded  |
| superseded2 | WHO Guidelines for the Treatment of Malaria, 1st ed.                | 2006  | superseded  |

## Acceptance once unblocked

- `python scripts/who_ingest.py <url-current>` → claims with `current=true`.
- Re-ingesting the older editions flips their claims to `current=false`, `supersedes_claim_id` set on the newer ones.
- Retrieval primitive `scoped(current_only=true)` excludes the superseded set.

## Workaround for Phase 7 acceptance now

The `guideline_proxy` topic in `corpus/topics.json` (T17 — IDSA candidiasis) lands a society-guideline-shaped paper through the existing PubMed path so the `recommends`/`current` flag logic still gets exercised on a real document — without blocking on the PDF fetcher.
