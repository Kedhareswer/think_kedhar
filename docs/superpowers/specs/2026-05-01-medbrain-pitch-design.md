# MedBrain Investor Pitch — Replay HTML Design Spec

**Date:** 2026-05-01
**Status:** Approved for implementation
**Artifact:** `medbrain-pitch.html` (single self-contained file, root of repo or `.tmp/`)
**Reference engine:** `neo-replay.html` (existing scripted-replay HTML in this repo)

---

## 1. Goal

Single-file scripted "video" HTML that depicts MedBrain's essence and behaviour to an investor audience. No captions. Pure visuals: animated cursor, typed input, streaming output, "thinking" UI, focus zoom, fade-in claim cards, knowledge-graph build. Investor watches; never clicks. Replay button on demand.

The pitch is **not** a UI tour. It is a visualization of the substrate (claims, supersession ledger, four-agent loop, retrieval primitives) — the thing under the CDS, not a CDS itself.

## 2. Constraints

- Single HTML file. No build step. No external CSS, JS, fonts, or images. Inline SVG only. Open in any modern browser, double-click to play.
- Self-contained ≤ 60 KB.
- Visual language matches `neo-replay.html` (palette, typography, motion curves) so the pitch lives in the same family as the consumer (Neo CDS) demo.
- Length: ~2:30 total. Length is not a hard cap — clarity wins over brevity.
- Pure visuals. No subtitle/caption track. On-screen text is part of the simulated UI (terminal output, file labels, mono captions inside frames). No narrator-voice text strip.
- Stage 1440 × 900, transform-pan camera (matches `neo-replay`).
- Plays automatically on load, no user interaction required to start.

## 3. Tokens

Lifted from `neo-replay.html`:

```
--bg          #fafafa
--surface     #ffffff
--text        #1a1a1a
--gray-2      #f3f3f3
--gray-3      #e6e6e6
--gray-4      #d4d4d4
--gray-9      #6f6f6f
--gray-12     #2a2a2a
--accent      #2563eb
--good        #16a34a
--warn        #d97706
--bad         #dc2626

--font-mono   "JetBrains Mono", ui-monospace, "SF Mono", Menlo, Consolas, monospace
--font-sans   -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif
```

Claim-card chip colors (predicate / category) reuse `neo-replay`'s entity palette:

| Category | bg | fg |
|---|---|---|
| condition | `#FFCDD2` | `#B71C1C` |
| medication | `#C8E6C9` | `#1B5E20` |
| dosage | `#E1BEE7` | `#4A148C` |
| test | `#BBDEFB` | `#0D47A1` |
| risk_factor | `#FFCCBC` | `#BF360C` |
| symptom | `#FFF9C4` | `#F57F17` |
| context | `#E0E0E0` | `#37474F` |
| vital | `#B2DFDB` | `#004D40` |
| anatomy | `#D7CCC8` | `#3E2723` |
| duration | `#D7CCC8` | `#4E342E` |

## 4. Architecture (file shape)

Single `.html` file with three sections, mirroring `neo-replay.html`:

1. **`<style>`** — tokens, stage layout, scene-specific component CSS, animations.
2. **`<body>`** — minimal HUD (progress bar + replay button), `#stage-wrap` + `#stage`, scene-mounted DOM containers (terminal, claim grid, agent-loop diagram, graph svg, ask card), inline SVG cursor.
3. **`<script>`** — content constants, scene engine (cursor mover, camera panner, typer, streamer, fader), `SCENES` array, `play()` driver.

### Engine primitives (reused from `neo-replay.html`, copied verbatim where unchanged)

- `applyCamera({ scale, tx, ty, ms })` — pan + zoom via `#stage` transform with cubic-bezier(.65,.05,.36,1) easing.
- `moveCursorTo(x, y, ms)` — viewport-coord cursor translate.
- `cursorOver(selector, opts)` — viewport-rect lookup + cursor move.
- `clickFx()` — ripple ring on cursor.
- `typeInto(el, text, perCharMs)` — char-by-char with random jitter for human feel.
- `streamText(elId, text, perCharMs)` — same, for streaming agent output.
- `wait(ms)` — promise sleep.
- `SCENES = [{ run: async () => { ... } }, ...]` — sequential scene queue, `play()` walks it.
- HUD progress bar updates per-scene index.

### Engine additions specific to this pitch

- `fadeInCard(el, ms = 450)` — opacity + translateY(8px → 0).
- `drawGraphEdge(svg, from, to, ms)` — SVG path stroke-dasharray reveal.
- `popInNode(svgNode, ms)` — opacity + scale(0.6 → 1).
- `tickCounter(el, from, to, ms)` — numeric ramp using `requestAnimationFrame`.

## 5. Scene-by-scene spec

Frame size assumption: 1440 × 900 stage. Coordinates below are stage-space.

### Scene 1 — Cold open (4s)

- Empty bg `#fafafa`. No HUD chrome visible yet (HUD hidden first 2s).
- Centered: `MEDBRAIN` wordmark, large mono caps, letter-spacing 0.18em, ink color, fade in over 800ms.
- Tagline beneath, sans, 18px, `--gray-9`: types char-by-char `"A medical brain that never stops learning."` (28ms/char).
- Hold 1s after typing finishes.

### Scene 2 — Problem (6s)

- Wordmark slides up to y=200 (200ms ease).
- Two stat blocks fade in side-by-side at y=380:
  - Left, dim (`--gray-9`): label `MEDIAN DOCTOR'S KNOWLEDGE` (mono, 11px, letter-spacing 0.12em) over big number `17 YEARS OUT OF DATE` (sans, 36px, ink).
  - Right, accent: label `NEW MEDICAL EVIDENCE` over `1 PAPER / 30 SEC` with `tickCounter` flipping a counter beside it (`+12, +13, +14...` over 4s simulating live increments).
- Hold 1.5s.

### Scene 3 — Architecture reveal (8s)

- Camera pans up 60px (`applyCamera({tx:0,ty:-60})`) to make room.
- Four agent boxes appear in a clockwise loop diagram centered at y=520:

  ```
       ┌─ STUDENT ─┐         ┌─ BRAIN ─┐
       │ continuous │  ───►  │ hourly  │
       └────────────┘         └─────────┘
              ▲                    │
              │                    ▼
       ┌── DREAM ───┐         ┌─ GRAPHIFY ┐
       │  weekly    │  ◄───   │  hourly   │
       └────────────┘         └───────────┘
  ```

  Each box: white surface, 1px gray-3 border, 14px radius. Inside: agent name (mono caps, 13px, ink), cadence label (mono, 10px, gray-9), one-line role (sans, 12px, gray-12, e.g. `fetches sources, extracts qualified claims`).

- Boxes pop in sequentially (one every 350ms). Arrows draw in last via SVG stroke-dasharray (800ms total).
- Hold 2.5s.

### Scene 4 — Zoom: STUDENT (10s)

- `applyCamera({ scale: 1.6, tx: -380, ty: -160, ms: 900 })` to push STUDENT box to fill viewport.
- Box morphs into a fake terminal: dark `--gray-12` bg, mono text. Header line: `medbrain $ ` then cursor moves to terminal area, click ripple, `typeInto` the command:

  ```
  python scripts/student.py "artemisinin resistance in pregnancy"
  ```

  (16ms/char). Press-enter visual: brief flash on prompt.

### Scene 5 — Student streams (18s)

Mono lines stream into terminal (one per ~1.5s, `streamText` for each line, then newline):

```
[plan] decomposing topic → 3 sub-questions
[search] PubMed esearch: "artemisinin resistance pregnancy" → 247 hits
[rerank] selecting top 12 by recency × evidence_grade
[fetch] efetch abstract 1/12 (PMID 38117392)
[fetch] efetch abstract 2/12 (PMID 37994551)
[fetch] efetch abstract 3/12 (PMID 37811204)
[think] ● ● ●           ← pulse-dot animation runs 1.2s
[extract] parsing claims with qualifiers...
```

- Pulse dot uses CSS `@keyframes pulse` (already in `neo-replay`).
- Auto-scroll terminal to keep latest line in view.

### Scene 6 — Claims emerge (14s)

- Camera pulls back slightly (`scale: 1.3, tx: -260, ty: -100`).
- Three claim cards fly in from terminal bottom (one every 1.2s). Each card layout (left → right pills with arrow separators):

  ```
  ┌────────────────────────────────────────────────────────────┐
  │  [Plasmodium falciparum]  ──resists──►  [artemether]       │
  │   condition (red chip)                  medication (green) │
  │  ─────────────────────────────────────────────────────────│
  │  qualifiers:  population: pregnancy · region: SE Asia      │
  │               evidence_grade: RCT  · certainty: high       │
  │               dose_regimen: 80mg/kg · 3 days · oral        │
  │  status:  pending_review  →  auto_promoted ✓               │
  └────────────────────────────────────────────────────────────┘
  ```

  Predicates as `→` arrow with the verb (mono, 11px, gray-9) inline.

- Each card fades in via `fadeInCard`, then 500ms later cursor lands on the qualifiers row (focus zoom: scale 1.05 just on that one card via CSS).

### Scene 7 — Auto-promote gate (10s)

- One card highlight-zooms (`scale: 1.15`, others dim to opacity 0.4).
- Side panel slides in from right (320px wide, surface, gray-3 border):

  ```
  AUTO-PROMOTE GATE
  ─────────────────
  evidence_grade ∈ {meta_analysis, RCT, guideline, cohort}   ✓
  no contradictions detected                                 ✓
  all entities known to brain                                ✓
  ≥3 qualifier fields populated                              ✓
  ─────────────────
  → AUTO_PROMOTED          (good color, 14px mono caps)
  ```

  Each check ticks in sequentially (300ms apart, `--good` fade-in).

- A second claim shown briefly fails one check (`certainty: low` on one row in red), status flips to `PENDING_REVIEW` (warn color).
- Side panel slides out.

### Scene 8 — Supersession (10s)

- Card stack metaphor: an older claim card is already faintly visible in background. New claim links to it via SVG arrow labeled `supersedes_id`.
- Old card fades to opacity 0.5, gets `archived` badge (gray-9 mono caps), but remains on screen.
- Mono caption appears below stack (centered, 13px, ink): `Never forgets. Only supersedes.`
- Hold 2s.

### Scene 9 — Zoom: BRAIN (16s)

- Camera returns to loop diagram (`applyCamera` to center, scale 1), then zooms to BRAIN box (`scale: 1.6, tx: 380, ty: -160`).
- Hourly tick visual: clock icon SVG sweeps once.
- `memory.md` file icon appears (gray-3 border rectangle with `MD` badge, mono filename label).
- Synthesis streams into the file body:

  ```
  ## Cross-concept patterns
  - artemisinin resistance correlates with K13 mutation
    in 4/12 claim clusters (high confidence)
  - pregnancy + endemic-region claims cluster around
    artemether-lumefantrine adjusted dosing
  ```

- Then `questions.md` file icon spawns beside it. Streams research backlog:

  ```
  ## Research backlog
  - what is the K13 prevalence in Greater Mekong 2025?
  - any RCT data on AL adjusted dosing in T1?
  ```

- Animated arrow draws from `questions.md` back to STUDENT box (faint dotted line, `--gray-4`), labeled `feedback loop`.

### Scene 10 — Zoom: GRAPHIFY (12s)

- Camera moves to GRAPHIFY box (`scale: 1.6, tx: 380, ty: 80`), expands.
- Inline SVG canvas (full viewport area). Nodes pop in via `popInNode` at staggered positions (60ms apart, ~30 nodes total).
  - Node = small circle + tiny label (sans, 9px).
  - Color hint: condition nodes red-tinted, medication green, etc. (very low saturation, 12% opacity over fill).
- Edges draw via `drawGraphEdge` (60ms apart, ~50 edges).
- Counter top-right: `0 → 47 nodes` then `0 → 132 edges` (live tick).
- Subtle camera orbit (rotate 0 → 4° and back, 4s, ease).

### Scene 11 — Zoom: DREAM (10s)

- Camera moves to DREAM box (`scale: 1.6, tx: -380, ty: 80`).
- Weekly tick: large clock spins once.
- Card stack appears, four card types fan out:
  - `flashcard` — Q/A pair (mono).
  - `mnemonic` — short verse (sans italic).
  - `analogy` — one-liner.
  - `gap` — `MISSING: <topic>` (warn color).
- All four cards have warn-color border + `derivative/` badge.
- Mono caption beneath (12px, ink): `Synthetic. Tagged at retrieval. Never feeds back as evidence.`

### Scene 12 — Output: 8-primitive menu (10s)

- Camera pulls all the way back (`scale: 1, tx: 0, ty: 0`).
- Loop diagram fades to opacity 0.3.
- New panel center-screen: 8 mono buttons in 2 columns:

  ```
  get_concept                    find_supersession_chain
  query_with_qualifiers          traverse_graph
  list_recent_promotions         get_evidence_ledger
  search_questions               get_derivatives
  ```

  Each button: surface bg, gray-3 border, 999px radius, 13px mono.

- Right of panel: small Neo logo (placeholder, just text `NEO CDS`) connects via dotted line.
- Mono caption beneath: `Any CDS plugs in. We are the substrate.`

### Scene 13 — Moat (10s)

- Three numbered cards fade in left-to-right (300ms stagger):

  ```
  ┌──────────────────────┐  ┌──────────────────────┐  ┌──────────────────────┐
  │ 01                    │  │ 02                    │  │ 03                    │
  │ QUALIFIED CLAIMS      │  │ SUPERSESSION LEDGER   │  │ DREAM FIREWALL        │
  │ ────                  │  │ ────                  │  │ ────                  │
  │ Structured triples    │  │ Old evidence stays    │  │ Synthetic outputs     │
  │ with population,      │  │ archived, never       │  │ never auto-promote;   │
  │ region, dose,         │  │ deleted. New supersedes;│ │ never feed back as    │
  │ evidence grade.       │  │ both retrievable.     │  │ evidence.             │
  │                       │  │                       │  │                       │
  │ Not a vector blob.    │  │ Not a delete-and-     │  │ Hallucination cannot  │
  │                       │  │ replace.              │  │ pollute primary.      │
  └───────────────────────┘  └───────────────────────┘  └──────────────────────┘
  ```

  Each card 320px wide. Numbers in accent color, mono, 11px caps. Title sans 18px ink. Body sans 13px gray-12.

- Hold 3.5s.

### Scene 14 — Status (8s)

- Card array clears.
- Mono dashboard appears as one block:

  ```
  ──────────────────────────────────────────
   DOMAIN              malaria
   CLAIMS              <tickCounter 0 → 1,247>
   SOURCES             PubMed · WHO · DailyMed
   AUTO-PROMOTE RATE   68%
   PENDING REVIEW      142
   LAST INGESTION      2 min ago
  ──────────────────────────────────────────
  ```

  All values mono. Counter ramps over 2.5s.

- Hold 2s.

### Scene 15 — Ask (8s)

- Stage clears (everything fades to opacity 0).
- Single line center-screen, sans 24px ink:

  ```
  Seed round — $1.5M for 18 months.
  ```

- Beneath, mono 12px gray-9: `kedhareswer.12110626@gmail.com` (user's email from auto-memory; replace if user prefers different contact).
- Replay button glows (subtle accent ring pulse).
- Hold indefinitely; HUD shows `↻ Replay`.

## 6. HUD

- Top-center, hidden first 2s, then fades in. Mirrors `neo-replay.html` HUD but minus the scene-title text label (per "no captions" constraint). Keeps:
  - 4px progress bar (220px wide, gradient `#6ee7b7 → #2563eb`).
  - Step counter `N/15` (mono 10px, dim).
  - `↻ Replay` button (reloads page).
- Backdrop blur, `rgba(20,20,20,0.85)` pill, white text.

## 7. Cursor

- Inline SVG (same shape as `neo-replay`). Position: fixed, z-index 999.
- Drop-shadow filter for visibility on light bg.
- `click` class adds 16px accent ripple ring (`@keyframes clickRipple`).
- Default move ease: 900ms cubic-bezier(.65,.05,.36,1).

## 8. Content constants (in JS)

- `AGENTS` — array of 4 `{ name, cadence, role, x, y }`.
- `STUDENT_LOG_LINES` — array of streamed terminal strings.
- `CLAIMS` — array of 3 `{ subject, predicate, object, qualifiers, status_initial, status_final }`.
- `GATE_CHECKS` — 4 lines for scene 7 panel.
- `BRAIN_MEMORY_TEXT`, `BRAIN_QUESTIONS_TEXT` — markdown bodies for scene 9.
- `GRAPH_NODES` — array of `{ id, label, category, x, y }` (~30 nodes laid out for visual balance).
- `GRAPH_EDGES` — array of `[fromId, toId]` (~50 edges).
- `DREAM_CARDS` — 4 `{ type, body }`.
- `RETRIEVAL_PRIMITIVES` — 8 strings.
- `MOAT_CARDS` — 3 `{ num, title, body, footer }`.
- `STATUS_DASHBOARD` — keyed object for the status block.
- `ASK` — `{ amount, months, email }`.

All content static, illustrative where real data unavailable. Numbers chosen to feel plausible, not real.

## 9. Motion principles

- Default ease: cubic-bezier(.65,.05,.36,1).
- Default fade-in: 450ms.
- Camera pan: 900–1200ms.
- Typing: 16–28ms/char with rare jitter (5–7% chance of +80ms pause).
- Streaming agent text: 12–18ms/char.
- One element holds focus at a time. Side elements dim (opacity 0.4) when not the subject.
- No bouncy springs. No long lingering shimmers. No more than one motion at a time except scene-7 stagger and scene-10 graph build.

## 10. Failure modes

- If a scene throws, log to console, continue to next scene (matches `neo-replay.html`'s try/catch in `play()`).
- No animation depends on real network or backend. Everything is timing-driven.
- Replay button = `window.location.reload()`. Idempotent.

## 11. Out of scope (v1 of pitch)

- Audio narration, music, voiceover.
- Captions / subtitle track.
- Multiple language versions.
- Mobile / responsive layout. Stage is fixed 1440 × 900; users zoom out browser if their screen is smaller. (Future: scale-to-fit wrapper.)
- Real DB-driven counters.
- Click interactivity (`?dev=1` skip-to-scene buttons can be added later but are not required).

## 12. Numbers to fill before build

| Var | Default placeholder | User-supplied? |
|---|---|---|
| `ASK.amount` | `$1.5M` | If user has different number, swap before build. |
| `ASK.months` | `18 months` | Same. |
| `ASK.email` | `kedhareswer.12110626@gmail.com` (from auto-memory) | Confirm or override. |
| `STATUS.claims` | `1,247` (illustrative) | Replace if real DB count exists. |
| `STATUS.auto_promote_rate` | `68%` | Same. |
| `STATUS.pending_review` | `142` | Same. |

If user does not supply alternates before build, placeholders ship as-is.

## 13. File location

- Output file: `d:\MedBrain\medbrain-pitch.html` (root, sibling of existing `neo-replay.html` and `medbrain-replay.html`).
- Self-contained — opens via `file://` double-click. No server required.
