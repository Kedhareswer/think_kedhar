# MedBrain Investor Pitch Replay Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a single self-contained `medbrain-pitch.html` file that plays a 15-scene scripted "video" demonstrating MedBrain's essence and behaviour to investors, using the same engine pattern as the existing `neo-replay.html`.

**Architecture:** Single HTML file (no build, no deps, ~50KB). Three sections: `<style>` with tokens + scene-specific CSS, `<body>` with minimal HUD + 1440×900 stage + scene-mounted DOM containers + inline SVG cursor, `<script>` with engine primitives + content constants + `SCENES` async array + `play()` driver. Engine primitives lifted from `neo-replay.html` (camera pan via stage transform, cursor-mover, typer, streamer, fader). Each scene runs sequentially via `await sc.run()`.

**Tech Stack:** Vanilla HTML/CSS/JS only. Inline SVG for cursor + graph. CSS `@keyframes` for animations. `requestAnimationFrame` for counter ticks. No external assets. Reference: `d:\MedBrain\neo-replay.html` (existing replay HTML in this repo).

---

## File Structure

Single artifact at `d:\MedBrain\medbrain-pitch.html`. The plan adds scenes incrementally; each task commits a working file with one more scene playable. The file is structured as:

| Section | Lines (approx) | Responsibility |
|---|---|---|
| `<head>` + `<style>` | top ~250 lines | Tokens, stage geometry, HUD, cursor, agent boxes, terminal, claim cards, panel, file icons, graph SVG, retrieval grid, moat cards, status block, ask card, motion keyframes |
| `<body>` static markup | ~80 lines | HUD bar + stage wrap + stage + scene root containers + cursor SVG |
| `<script>` constants | ~150 lines | `AGENTS`, `STUDENT_LOG_LINES`, `CLAIMS`, `GATE_CHECKS`, `BRAIN_*`, `GRAPH_*`, `DREAM_CARDS`, `RETRIEVAL_PRIMITIVES`, `MOAT_CARDS`, `STATUS_DASHBOARD`, `ASK` |
| `<script>` engine | ~120 lines | `applyCamera`, `moveCursorTo`, `cursorOver`, `clickFx`, `wait`, `typeInto`, `streamText`, `fadeInCard`, `drawGraphEdge`, `popInNode`, `tickCounter`, `escapeHtml` |
| `<script>` SCENES | ~400 lines | 15 async scene runners |
| `<script>` driver | ~30 lines | `play()` walks SCENES, updates HUD, error-traps per scene |

We do **not** split into multiple files. Single-file constraint is part of the spec (no build, double-click to play).

---

## Tooling: how to "test" a visual scripted artifact

There is no unit-test framework here. Verification = open the file in a browser and watch. To make that fast and repeatable:

- Add `?scene=N` URL parameter support in `play()`. When set, jump straight to scene N (skip 0..N-1). This is part of Task 1 so every later scene is testable in isolation.
- Add `?dev=1` URL parameter to show a tiny dev panel (mono text, top-right, below HUD) listing `[1] [2] ... [15]` clickable jumps. Part of Task 1.
- "Test" = open `medbrain-pitch.html?scene=N&dev=1` in a browser, watch the scene run start-to-finish, confirm against spec section 5.<scene>.

These query parameters cost ~30 lines and make the rest of the plan dramatically faster to verify.

---

## Pre-build placeholders (locked from spec section 12)

Use these literal values in the `ASK` and `STATUS_DASHBOARD` constants:

| Constant | Value |
|---|---|
| `ASK.amount` | `"$1.5M"` |
| `ASK.months` | `"18 months"` |
| `ASK.email` | `"kedhareswer.12110626@gmail.com"` |
| `STATUS_DASHBOARD.claims` | `1247` (renders as `1,247` via `tickCounter`) |
| `STATUS_DASHBOARD.auto_promote_rate` | `"68%"` |
| `STATUS_DASHBOARD.pending_review` | `142` |

---

## Task 0: Scaffold the file with tokens, body skeleton, HUD, cursor, and engine primitives

**Files:**
- Create: `d:\MedBrain\medbrain-pitch.html`

**Goal:** Page loads, shows blank `#fafafa` stage with a HUD pill at top-center, a cursor SVG visible at top-left of the viewport, and `play()` runs a single placeholder scene that just waits 1s then logs "scene 0 done" to console. No actual content yet — just the chassis.

- [ ] **Step 1: Create the file with `<!DOCTYPE>`, `<head>`, `<style>` block containing tokens**

Open `d:\MedBrain\medbrain-pitch.html` and write:

```html
<!--
  MedBrain — Investor Pitch Replay
  Self-contained scripted "video" — open in any modern browser, double-click to play.
  No external CSS / JS / fonts / images. Reload to replay.
  See spec: docs/superpowers/specs/2026-05-01-medbrain-pitch-design.md
-->
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8" />
<title>MedBrain — Investor Pitch</title>
<style>
  :root {
    --bg: #fafafa;
    --surface: #ffffff;
    --text: #1a1a1a;
    --gray-2: #f3f3f3;
    --gray-3: #e6e6e6;
    --gray-4: #d4d4d4;
    --gray-9: #6f6f6f;
    --gray-12: #2a2a2a;
    --accent: #2563eb;
    --good: #16a34a;
    --warn: #d97706;
    --bad: #dc2626;
    --font-sans: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
    --font-mono: "JetBrains Mono", ui-monospace, "SF Mono", Menlo, Consolas, monospace;
  }
  * { box-sizing: border-box; }
  html, body { margin: 0; padding: 0; height: 100%; background: var(--bg); color: var(--text); font-family: var(--font-sans); overflow: hidden; }

  #stage-wrap { position: fixed; inset: 0; overflow: hidden; background: linear-gradient(180deg, #fafafa 0%, #f5f5f5 100%); }
  #stage {
    position: absolute; top: 0; left: 0;
    width: 1440px; height: 900px;
    transform-origin: 0 0;
    transition: transform 1200ms cubic-bezier(.65,.05,.36,1);
  }

  #cursor { position: fixed; top: 0; left: 0; width: 24px; height: 24px; pointer-events: none; z-index: 999; transform: translate(40px, 40px); transition: transform 900ms cubic-bezier(.65,.05,.36,1); }
  #cursor svg { display: block; filter: drop-shadow(0 2px 4px rgba(0,0,0,0.3)); }
  #cursor.click::before { content: ""; position: absolute; left: 4px; top: 4px; width: 16px; height: 16px; border-radius: 999px; border: 2px solid var(--accent); animation: clickRipple .55s ease-out; }

  #hud { position: fixed; top: 14px; left: 50%; transform: translateX(-50%); display: flex; align-items: center; gap: 14px; background: rgba(20,20,20,0.85); color: white; padding: 8px 14px; border-radius: 999px; font-family: var(--font-mono); font-size: 11px; letter-spacing: 0.06em; z-index: 1000; backdrop-filter: blur(8px); opacity: 0; transition: opacity 600ms ease; }
  #hud.shown { opacity: 1; }
  #hud .progress { width: 220px; height: 4px; background: #fff2; border-radius: 999px; overflow: hidden; }
  #hud .progress > .bar { height: 100%; width: 0%; background: linear-gradient(90deg, #6ee7b7 0%, #2563eb 100%); transition: width 200ms linear; }
  #hud .badge { padding: 3px 8px; border-radius: 999px; background: #ffffff14; font-size: 10px; }
  #replay-btn { background: #ffffff14; border: 1px solid #ffffff22; color: white; padding: 4px 10px; border-radius: 999px; font-family: var(--font-mono); font-size: 10px; cursor: pointer; }
  #replay-btn:hover { background: #ffffff22; }

  #devpanel { position: fixed; top: 60px; right: 14px; display: none; flex-direction: column; gap: 4px; background: rgba(20,20,20,0.85); color: white; padding: 10px; border-radius: 8px; font-family: var(--font-mono); font-size: 10px; z-index: 1000; }
  #devpanel.shown { display: flex; }
  #devpanel button { background: #ffffff14; border: 1px solid #ffffff22; color: white; padding: 3px 8px; border-radius: 4px; font-family: var(--font-mono); font-size: 10px; cursor: pointer; text-align: left; }

  @keyframes spin { to { transform: rotate(360deg); } }
  @keyframes pulse { 0%, 100% { opacity: 1; transform: scale(1); } 50% { opacity: 0.55; transform: scale(0.85); } }
  @keyframes caret { 50% { opacity: 0; } }
  @keyframes clickRipple { from { opacity: 0.9; transform: scale(0.6); } to { opacity: 0; transform: scale(2.2); } }
</style>
</head>
<body>

<div id="hud">
  <span class="progress"><span class="bar"></span></span>
  <span class="badge"><span id="step-num">0</span>/<span id="step-total">0</span></span>
  <button id="replay-btn" onclick="window.location.reload()">↻ Replay</button>
</div>

<div id="devpanel"></div>

<div id="stage-wrap">
  <div id="stage">
    <!-- Scene-mounted content goes here, added by later tasks -->
  </div>
</div>

<div id="cursor">
  <svg width="24" height="24" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
    <path d="M3 2 L3 18 L7.5 14 L10.5 21 L13 20 L10 13 L16 13 Z" fill="#1a1a1a" stroke="white" stroke-width="1.4" stroke-linejoin="round"/>
  </svg>
</div>

<script>
/* ────────────────────────────────────────────────────────────────────
   Engine primitives — cursor, camera, typing, streaming, fades
──────────────────────────────────────────────────────────────────── */

const $ = (id) => document.getElementById(id);
const stage = $('stage');
const cursor = $('cursor');
const stepNumEl = $('step-num');
const progressBar = document.querySelector('#hud .bar');

let stageTx = { sx: 1, tx: 0, ty: 0 };

function applyCamera({ scale = 1, tx = 0, ty = 0, ms = 1200 } = {}) {
  stage.style.transition = `transform ${ms}ms cubic-bezier(.65,.05,.36,1)`;
  stage.style.transform = `translate(${tx}px, ${ty}px) scale(${scale})`;
  stageTx = { sx: scale, tx, ty };
}

function moveCursorTo(viewportX, viewportY, ms = 800) {
  cursor.style.transition = `transform ${ms}ms cubic-bezier(.65,.05,.36,1)`;
  cursor.style.transform = `translate(${viewportX}px, ${viewportY}px)`;
}

function cursorOver(selector, opts = {}) {
  const el = document.querySelector(selector);
  if (!el) return Promise.resolve();
  const rect = el.getBoundingClientRect();
  const x = rect.left + (opts.dx != null ? opts.dx : rect.width / 2) - 6;
  const y = rect.top + (opts.dy != null ? opts.dy : rect.height / 2) - 6;
  moveCursorTo(x, y, opts.ms || 800);
  return wait(opts.ms || 800);
}

function clickFx() {
  cursor.classList.add('click');
  setTimeout(() => cursor.classList.remove('click'), 600);
}

const wait = (ms) => new Promise(r => setTimeout(r, ms));

async function typeInto(targetEl, text, perCharMs = 24) {
  targetEl.textContent = '';
  for (const ch of text) {
    targetEl.textContent += ch;
    if (ch === ' ' && Math.random() < 0.05) await wait(perCharMs * 6);
    else await wait(perCharMs + (Math.random() < 0.07 ? 80 : 0));
  }
}

async function streamText(targetEl, text, perCharMs = 14) {
  targetEl.textContent = '';
  for (const ch of text) {
    targetEl.textContent += ch;
    await wait(perCharMs + (Math.random() < 0.05 ? 90 : 0));
  }
}

function fadeInCard(el, ms = 450) {
  el.style.transition = `opacity ${ms}ms ease, transform ${ms}ms ease`;
  el.style.opacity = '0';
  el.style.transform = 'translateY(8px)';
  requestAnimationFrame(() => requestAnimationFrame(() => {
    el.style.opacity = '1';
    el.style.transform = 'translateY(0)';
  }));
}

function popInNode(el, ms = 320) {
  el.style.transition = `opacity ${ms}ms ease, transform ${ms}ms cubic-bezier(.34,1.4,.64,1)`;
  el.style.opacity = '0';
  el.style.transform = 'scale(0.6)';
  requestAnimationFrame(() => requestAnimationFrame(() => {
    el.style.opacity = '1';
    el.style.transform = 'scale(1)';
  }));
}

function drawGraphEdge(pathEl, ms = 600) {
  const len = pathEl.getTotalLength();
  pathEl.style.strokeDasharray = len;
  pathEl.style.strokeDashoffset = len;
  pathEl.style.transition = `stroke-dashoffset ${ms}ms cubic-bezier(.65,.05,.36,1)`;
  requestAnimationFrame(() => requestAnimationFrame(() => {
    pathEl.style.strokeDashoffset = '0';
  }));
}

function tickCounter(el, from, to, ms = 1500, formatter = (n) => Math.round(n).toLocaleString()) {
  const start = performance.now();
  function frame(now) {
    const t = Math.min(1, (now - start) / ms);
    const eased = 1 - Math.pow(1 - t, 3);
    el.textContent = formatter(from + (to - from) * eased);
    if (t < 1) requestAnimationFrame(frame);
  }
  requestAnimationFrame(frame);
}

function escapeHtml(s) {
  return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
}

/* ────────────────────────────────────────────────────────────────────
   Content constants — populated in later tasks
──────────────────────────────────────────────────────────────────── */

// AGENTS, STUDENT_LOG_LINES, CLAIMS, GATE_CHECKS, BRAIN_MEMORY_TEXT,
// BRAIN_QUESTIONS_TEXT, GRAPH_NODES, GRAPH_EDGES, DREAM_CARDS,
// RETRIEVAL_PRIMITIVES, MOAT_CARDS, STATUS_DASHBOARD, ASK
// — added by tasks 1..15

/* ────────────────────────────────────────────────────────────────────
   SCENES — populated by tasks 1..15
──────────────────────────────────────────────────────────────────── */

const SCENES = [
  {
    title: '0. Scaffold smoke test',
    run: async () => {
      console.log('scene 0 done');
      await wait(1000);
    },
  },
];

/* ────────────────────────────────────────────────────────────────────
   Driver
──────────────────────────────────────────────────────────────────── */

async function play(startAt = 0) {
  $('step-total').textContent = SCENES.length;
  for (let i = startAt; i < SCENES.length; i++) {
    const sc = SCENES[i];
    stepNumEl.textContent = (i + 1);
    progressBar.style.width = (((i + 1) / SCENES.length) * 100) + '%';
    try { await sc.run(); }
    catch (e) { console.error('scene-error', sc.title, e); }
  }
}

function readSceneParam() {
  const url = new URL(window.location.href);
  const n = parseInt(url.searchParams.get('scene') || '', 10);
  return Number.isFinite(n) && n >= 1 && n <= SCENES.length ? n - 1 : 0;
}

function setupDevPanel() {
  const url = new URL(window.location.href);
  if (url.searchParams.get('dev') !== '1') return;
  const panel = $('devpanel');
  panel.classList.add('shown');
  for (let i = 0; i < SCENES.length; i++) {
    const b = document.createElement('button');
    b.textContent = `[${i + 1}] ${SCENES[i].title}`;
    b.onclick = () => { window.location.href = `?scene=${i + 1}&dev=1`; };
    panel.appendChild(b);
  }
}

window.addEventListener('load', () => {
  moveCursorTo(60, 80, 0);
  setupDevPanel();
  setTimeout(() => $('hud').classList.add('shown'), 800);
  setTimeout(() => play(readSceneParam()), 1200);
});
</script>
</body>
</html>
```

- [ ] **Step 2: Open the file in a browser to verify scaffold**

Run (Windows): `start "" "d:\MedBrain\medbrain-pitch.html"`

Expected: Blank `#fafafa` page, dark HUD pill fades in at top-center showing `1/1` and `↻ Replay` button. Cursor SVG visible at viewport (60,80). Console shows `scene 0 done`.

- [ ] **Step 3: Verify URL parameters**

Open `d:\MedBrain\medbrain-pitch.html?scene=1&dev=1` (paste path with query into browser).
Expected: Same as step 2, plus a small dev panel at top-right listing `[1] 0. Scaffold smoke test`.

- [ ] **Step 4: Commit**

Run from `d:\MedBrain`:

```bash
git add medbrain-pitch.html docs/superpowers/specs/2026-05-01-medbrain-pitch-design.md docs/superpowers/plans/2026-05-01-medbrain-pitch.md
git commit -m "feat(pitch): scaffold investor pitch replay HTML with engine primitives"
```

---

## Task 1: Scene 1 — Cold open (wordmark + tagline)

**Files:**
- Modify: `d:\MedBrain\medbrain-pitch.html` (replace `SCENES[0]` placeholder, add scene-1 DOM container, add scene-1 CSS)

- [ ] **Step 1: Add scene-1 CSS inside the existing `<style>` block, just before `@keyframes spin`**

```css
  /* Scene 1 — cold open */
  .s1-stage { position: absolute; inset: 0; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 18px; }
  .s1-wordmark { font-family: var(--font-mono); font-size: 64px; letter-spacing: 0.18em; color: var(--text); opacity: 0; transition: opacity 800ms ease, transform 600ms cubic-bezier(.65,.05,.36,1); }
  .s1-wordmark.shown { opacity: 1; }
  .s1-wordmark.up { transform: translateY(-200px); }
  .s1-tagline { font-family: var(--font-sans); font-size: 18px; color: var(--gray-9); min-height: 24px; }
```

- [ ] **Step 2: Add the scene-1 DOM container inside `#stage`, replacing the comment**

Replace `<!-- Scene-mounted content goes here, added by later tasks -->` with:

```html
    <div class="s1-stage" id="s1">
      <div class="s1-wordmark" id="s1-wordmark">MEDBRAIN</div>
      <div class="s1-tagline" id="s1-tagline"></div>
    </div>
```

- [ ] **Step 3: Replace the placeholder `SCENES[0]` with the real scene 1**

Find `const SCENES = [` and replace the entire array contents with:

```javascript
const SCENES = [
  {
    title: '1. Cold open',
    run: async () => {
      const wm = $('s1-wordmark');
      const tl = $('s1-tagline');
      wm.classList.add('shown');
      await wait(800);
      await typeInto(tl, 'A medical brain that never stops learning.', 28);
      await wait(1000);
    },
  },
];
```

- [ ] **Step 4: Verify scene 1 in browser**

Open `d:\MedBrain\medbrain-pitch.html?dev=1`.
Expected: HUD shows `1/1`. Centered `MEDBRAIN` wordmark fades in over ~800ms. Tagline `A medical brain that never stops learning.` types underneath char-by-char with subtle jitter. Holds 1s. Total ~3s.

- [ ] **Step 5: Commit**

```bash
git add medbrain-pitch.html
git commit -m "feat(pitch): scene 1 cold open with wordmark and tagline"
```

---

## Task 2: Scene 2 — Problem (two stat blocks + ticking counter)

**Files:**
- Modify: `d:\MedBrain\medbrain-pitch.html`

- [ ] **Step 1: Add scene-2 CSS just after the `.s1-tagline` rule**

```css
  /* Scene 2 — problem */
  .s2-stage { position: absolute; inset: 0; display: flex; align-items: center; justify-content: center; gap: 96px; opacity: 0; transition: opacity 600ms ease; }
  .s2-stage.shown { opacity: 1; }
  .s2-stat { display: flex; flex-direction: column; align-items: flex-start; gap: 10px; max-width: 380px; }
  .s2-stat .label { font-family: var(--font-mono); font-size: 11px; letter-spacing: 0.12em; }
  .s2-stat .value { font-family: var(--font-sans); font-size: 36px; font-weight: 600; line-height: 1.1; }
  .s2-stat.dim .label { color: var(--gray-9); }
  .s2-stat.dim .value { color: var(--gray-9); }
  .s2-stat.lit .label { color: var(--accent); }
  .s2-stat.lit .value { color: var(--text); }
  .s2-stat .ticker { font-family: var(--font-mono); font-size: 14px; color: var(--accent); margin-top: 4px; }
```

- [ ] **Step 2: Add scene-2 DOM container inside `#stage` (after the `s1` container)**

```html
    <div class="s2-stage" id="s2" style="display:none;">
      <div class="s2-stat dim">
        <div class="label">MEDIAN DOCTOR'S KNOWLEDGE</div>
        <div class="value">17 years out of date</div>
      </div>
      <div class="s2-stat lit">
        <div class="label">NEW MEDICAL EVIDENCE</div>
        <div class="value">1 paper / 30 sec</div>
        <div class="ticker"><span id="s2-tick">0</span> papers since you started reading</div>
      </div>
    </div>
```

- [ ] **Step 3: Append scene 2 to the SCENES array**

Inside `const SCENES = [...]`, add a new object after scene 1:

```javascript
  {
    title: '2. Problem',
    run: async () => {
      $('s1-wordmark').classList.add('up');
      await wait(400);
      $('s1').style.display = 'none';
      $('s2').style.display = 'flex';
      requestAnimationFrame(() => $('s2').classList.add('shown'));
      await wait(600);
      const tickEl = $('s2-tick');
      tickCounter(tickEl, 0, 200, 5500);
      await wait(5500);
      await wait(500);
    },
  },
```

- [ ] **Step 4: Verify scene 2 in browser**

Open `d:\MedBrain\medbrain-pitch.html?dev=1` and watch through scene 1 → 2.
Then open `d:\MedBrain\medbrain-pitch.html?scene=2&dev=1` to jump straight in.
Expected: Two stat blocks side-by-side. Left dim "17 years out of date". Right accent "1 paper / 30 sec" with ticker counting 0 → 200 over ~5.5s.

- [ ] **Step 5: Commit**

```bash
git add medbrain-pitch.html
git commit -m "feat(pitch): scene 2 problem stats with ticking counter"
```

---

## Task 3: Scene 3 — Architecture reveal (4-agent loop diagram)

**Files:**
- Modify: `d:\MedBrain\medbrain-pitch.html`

- [ ] **Step 1: Add `AGENTS` constant and scene-3 CSS**

In the constants section (after the comment block) insert:

```javascript
const AGENTS = [
  { id: 'student',  name: 'STUDENT',  cadence: 'continuous', role: 'fetches sources, extracts qualified claims', x: 360, y: 360 },
  { id: 'brain',    name: 'BRAIN',    cadence: 'hourly',     role: 'synthesizes patterns, emits research backlog', x: 820, y: 360 },
  { id: 'graphify', name: 'GRAPHIFY', cadence: 'hourly',     role: 'rebuilds knowledge graph, exposes retrieval', x: 820, y: 580 },
  { id: 'dream',    name: 'DREAM',    cadence: 'weekly',     role: 'compacts, generates derivatives, decays', x: 360, y: 580 },
];
```

In `<style>` after scene-2 CSS:

```css
  /* Scene 3 — architecture loop */
  .s3-stage { position: absolute; inset: 0; opacity: 0; transition: opacity 500ms ease; }
  .s3-stage.shown { opacity: 1; }
  .agent-box { position: absolute; width: 280px; padding: 18px 20px; background: var(--surface); border: 1px solid var(--gray-3); border-radius: 14px; opacity: 0; }
  .agent-box .name { font-family: var(--font-mono); font-size: 13px; letter-spacing: 0.14em; color: var(--text); }
  .agent-box .cadence { font-family: var(--font-mono); font-size: 10px; letter-spacing: 0.1em; color: var(--gray-9); margin-top: 6px; }
  .agent-box .role { font-family: var(--font-sans); font-size: 12px; color: var(--gray-12); margin-top: 10px; line-height: 1.5; }
  .s3-arrows { position: absolute; inset: 0; pointer-events: none; }
  .s3-arrows path { fill: none; stroke: var(--gray-4); stroke-width: 1.5; }
```

- [ ] **Step 2: Add scene-3 DOM after the `s2` container**

```html
    <div class="s3-stage" id="s3" style="display:none;">
      <svg class="s3-arrows" viewBox="0 0 1440 900" preserveAspectRatio="none" width="1440" height="900">
        <path id="s3-arrow-1" d="M 640 410 Q 730 410 800 410" marker-end="url(#s3-head)"/>
        <path id="s3-arrow-2" d="M 960 460 Q 960 520 960 580" marker-end="url(#s3-head)"/>
        <path id="s3-arrow-3" d="M 800 630 Q 730 630 640 630" marker-end="url(#s3-head)"/>
        <path id="s3-arrow-4" d="M 480 580 Q 480 520 480 460" marker-end="url(#s3-head)"/>
        <defs><marker id="s3-head" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse"><path d="M 0 0 L 10 5 L 0 10 z" fill="var(--gray-4)"/></marker></defs>
      </svg>
      <div class="agent-box" id="ab-student"  style="left:360px; top:360px;"><div class="name">STUDENT</div><div class="cadence">CONTINUOUS</div><div class="role">fetches sources, extracts qualified claims</div></div>
      <div class="agent-box" id="ab-brain"    style="left:820px; top:360px;"><div class="name">BRAIN</div><div class="cadence">HOURLY</div><div class="role">synthesizes patterns, emits research backlog</div></div>
      <div class="agent-box" id="ab-graphify" style="left:820px; top:580px;"><div class="name">GRAPHIFY</div><div class="cadence">HOURLY</div><div class="role">rebuilds knowledge graph, exposes retrieval</div></div>
      <div class="agent-box" id="ab-dream"    style="left:360px; top:580px;"><div class="name">DREAM</div><div class="cadence">WEEKLY</div><div class="role">compacts, generates derivatives, decays low-salience</div></div>
    </div>
```

- [ ] **Step 3: Append scene 3 to SCENES**

```javascript
  {
    title: '3. Architecture loop',
    run: async () => {
      $('s2').classList.remove('shown');
      await wait(400);
      $('s2').style.display = 'none';
      $('s3').style.display = 'block';
      requestAnimationFrame(() => $('s3').classList.add('shown'));
      applyCamera({ scale: 1, tx: 0, ty: -60, ms: 800 });
      await wait(400);
      const order = ['ab-student', 'ab-brain', 'ab-graphify', 'ab-dream'];
      for (const id of order) {
        fadeInCard($(id), 450);
        await wait(350);
      }
      await wait(200);
      ['s3-arrow-1', 's3-arrow-2', 's3-arrow-3', 's3-arrow-4'].forEach(id => drawGraphEdge(document.getElementById(id), 800));
      await wait(900);
      await wait(2500);
    },
  },
```

- [ ] **Step 4: Verify scene 3 in browser**

Open `d:\MedBrain\medbrain-pitch.html?scene=3&dev=1`.
Expected: Camera nudges up. Four agent boxes pop in clockwise (Student → Brain → Graphify → Dream). Four SVG arrows draw between them forming a loop. Holds 2.5s.

- [ ] **Step 5: Commit**

```bash
git add medbrain-pitch.html
git commit -m "feat(pitch): scene 3 architecture loop with four agent boxes"
```

---

## Task 4: Scene 4 — Zoom STUDENT into terminal + type command

**Files:**
- Modify: `d:\MedBrain\medbrain-pitch.html`

- [ ] **Step 1: Add scene-4 CSS**

```css
  /* Scene 4-5 — STUDENT terminal */
  .term { position: absolute; left: 360px; top: 360px; width: 720px; height: 440px; background: var(--gray-12); border-radius: 14px; padding: 22px 26px; font-family: var(--font-mono); font-size: 13px; color: #e6e6e6; overflow: hidden; opacity: 0; transition: opacity 400ms ease; }
  .term.shown { opacity: 1; }
  .term .prompt { color: var(--gray-4); }
  .term .cmd { color: white; }
  .term .line { line-height: 1.7; white-space: pre-wrap; }
  .term .line.dim { color: var(--gray-4); }
  .term .line.warn { color: #f59e0b; }
  .term .line.good { color: #6ee7b7; }
  .term .pulse-dots { display: inline-block; }
  .term .pulse-dots span { animation: pulse 1.2s ease-in-out infinite; }
  .term .pulse-dots span:nth-child(2) { animation-delay: 0.2s; }
  .term .pulse-dots span:nth-child(3) { animation-delay: 0.4s; }
```

- [ ] **Step 2: Add terminal DOM inside the `s3` container at the end (so it overlays the STUDENT box on zoom)**

Place this just before `</div>` that closes `<div class="s3-stage">`:

```html
      <div class="term" id="s4-term">
        <div class="line"><span class="prompt">medbrain $ </span><span class="cmd" id="s4-cmd"></span></div>
        <div id="s4-output"></div>
      </div>
```

- [ ] **Step 3: Append scene 4 to SCENES**

```javascript
  {
    title: '4. Zoom STUDENT — terminal command',
    run: async () => {
      applyCamera({ scale: 1.6, tx: -380, ty: -160, ms: 900 });
      await wait(950);
      const term = $('s4-term');
      term.classList.add('shown');
      await wait(300);
      const r = term.getBoundingClientRect();
      moveCursorTo(r.left + 80, r.top + 30, 700);
      await wait(750);
      clickFx();
      await typeInto($('s4-cmd'), 'python scripts/student.py "artemisinin resistance in pregnancy"', 16);
      await wait(400);
    },
  },
```

- [ ] **Step 4: Verify scene 4 in browser**

Open `d:\MedBrain\medbrain-pitch.html?scene=4&dev=1`.
Expected: Camera zooms to STUDENT box area; dark terminal panel fades in over the STUDENT box. Cursor moves into terminal, click ripple, then types `python scripts/student.py "artemisinin resistance in pregnancy"`.

- [ ] **Step 5: Commit**

```bash
git add medbrain-pitch.html
git commit -m "feat(pitch): scene 4 STUDENT terminal with command typing"
```

---

## Task 5: Scene 5 — Student streams plan + search + fetch + thinking + extract

**Files:**
- Modify: `d:\MedBrain\medbrain-pitch.html`

- [ ] **Step 1: Add `STUDENT_LOG_LINES` constant**

In the constants section after `AGENTS`:

```javascript
const STUDENT_LOG_LINES = [
  { cls: 'dim',  text: '[plan] decomposing topic → 3 sub-questions' },
  { cls: '',     text: '[search] PubMed esearch: "artemisinin resistance pregnancy" → 247 hits' },
  { cls: '',     text: '[rerank] selecting top 12 by recency × evidence_grade' },
  { cls: 'dim',  text: '[fetch] efetch abstract 1/12 (PMID 38117392)' },
  { cls: 'dim',  text: '[fetch] efetch abstract 2/12 (PMID 37994551)' },
  { cls: 'dim',  text: '[fetch] efetch abstract 3/12 (PMID 37811204)' },
  { cls: 'warn', text: '[think] ● ● ●', isThink: true },
  { cls: 'good', text: '[extract] parsing claims with qualifiers...' },
];
```

- [ ] **Step 2: Append scene 5 to SCENES**

```javascript
  {
    title: '5. STUDENT streams',
    run: async () => {
      const out = $('s4-output');
      for (const line of STUDENT_LOG_LINES) {
        const div = document.createElement('div');
        div.className = 'line ' + (line.cls || '');
        out.appendChild(div);
        if (line.isThink) {
          div.innerHTML = '<span class="prompt">[think] </span><span class="pulse-dots"><span>●</span> <span>●</span> <span>●</span></span>';
          await wait(1200);
        } else {
          await streamText(div, line.text, 12);
          await wait(280);
        }
      }
      await wait(800);
    },
  },
```

- [ ] **Step 3: Verify scene 5 in browser**

Open `d:\MedBrain\medbrain-pitch.html?scene=5&dev=1`.
Expected: Terminal already showing the typed command (scene 4 ran first internally — but jumping to scene 5 skips scenes 1–4. To see this scene properly, we either start from scene 4 or accept that the terminal will show only the streamed output. **For verification, watch from scene 4:** open `?scene=4&dev=1` and watch through 4→5.) Lines stream in one by one with mono jitter. Pulse dots animate during `[think]` line. Last good-color line `[extract] parsing claims with qualifiers...` appears.

- [ ] **Step 4: Fix `?scene=N` to also run prerequisite DOM-state from earlier scenes (one-line patch)**

Some scenes depend on DOM state set up by earlier scenes (e.g. scene 5 needs the terminal visible). To make `?scene=N` always work, modify `play()` to "fast-forward" prior scenes by running their `run()` instantly when `startAt > 0`. Replace `play()` with:

```javascript
async function play(startAt = 0) {
  $('step-total').textContent = SCENES.length;
  // Fast-forward prior scenes (no awaits inside — best-effort prep of DOM).
  // Each scene is responsible for being idempotent under fast-forward.
  for (let i = 0; i < startAt; i++) {
    const sc = SCENES[i];
    stepNumEl.textContent = (i + 1);
    progressBar.style.width = (((i + 1) / SCENES.length) * 100) + '%';
    try { await Promise.race([sc.run(), wait(50)]); } catch (e) { /* ignore in ff */ }
  }
  for (let i = startAt; i < SCENES.length; i++) {
    const sc = SCENES[i];
    stepNumEl.textContent = (i + 1);
    progressBar.style.width = (((i + 1) / SCENES.length) * 100) + '%';
    try { await sc.run(); }
    catch (e) { console.error('scene-error', sc.title, e); }
  }
}
```

This isn't perfect (some scenes have long awaits inside that won't finish in 50ms) but it sets up DOM containers (display flips, classList.add) so later scenes have something to attach to. Verify scene 5 again with `?scene=5&dev=1` — terminal should now show the typed command at start of streaming.

- [ ] **Step 5: Commit**

```bash
git add medbrain-pitch.html
git commit -m "feat(pitch): scene 5 STUDENT log streaming with thinking dots and fast-forward"
```

---

## Task 6: Scene 6 — Three claim cards fly in

**Files:**
- Modify: `d:\MedBrain\medbrain-pitch.html`

- [ ] **Step 1: Add `CLAIMS` constant**

In constants section:

```javascript
const CLAIMS = [
  {
    subject:    { text: 'Plasmodium falciparum', cat: 'condition' },
    predicate:  'resists',
    object:     { text: 'artemether', cat: 'medication' },
    qualifiers: [
      ['population',     'pregnancy (T2-T3)'],
      ['region',         'Greater Mekong'],
      ['evidence_grade', 'RCT'],
      ['certainty',      'high'],
      ['dose_regimen',   '80 mg/kg · 3 days · oral'],
    ],
    initialStatus: 'pending_review',
    finalStatus:   'auto_promoted',
  },
  {
    subject:    { text: 'artemether-lumefantrine', cat: 'medication' },
    predicate:  'requires',
    object:     { text: 'food co-administration', cat: 'context' },
    qualifiers: [
      ['population',     'all adults'],
      ['evidence_grade', 'guideline'],
      ['certainty',      'high'],
      ['dose_regimen',   '6 doses over 3 days'],
    ],
    initialStatus: 'pending_review',
    finalStatus:   'auto_promoted',
  },
  {
    subject:    { text: 'severe falciparum malaria', cat: 'condition' },
    predicate:  'recommends',
    object:     { text: 'parenteral artesunate', cat: 'medication' },
    qualifiers: [
      ['population',     'parasitemia >5% OR cerebral signs'],
      ['evidence_grade', 'meta_analysis'],
      ['certainty',      'high'],
    ],
    initialStatus: 'pending_review',
    finalStatus:   'auto_promoted',
  },
];
```

- [ ] **Step 2: Add claim-card CSS using neo-replay chip palette**

```css
  /* Scene 6 — claim cards */
  .s6-stage { position: absolute; inset: 0; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 18px; opacity: 0; transition: opacity 500ms ease; padding-top: 40px; }
  .s6-stage.shown { opacity: 1; }
  .claim-card { width: 760px; background: var(--surface); border: 1px solid var(--gray-3); border-radius: 14px; padding: 18px 22px; opacity: 0; transition: opacity 450ms ease, transform 450ms ease; }
  .claim-card .triple { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; font-size: 14.5px; }
  .claim-card .pill { display: inline-flex; align-items: center; gap: 8px; padding: 4px 10px; border-radius: 6px; font-size: 14px; line-height: 1; }
  .claim-card .pill .badge { font-family: var(--font-mono); font-size: 9.5px; letter-spacing: 0.08em; padding: 2px 6px; border-radius: 4px; background: rgba(0,0,0,.08); color: rgba(0,0,0,.55); }
  .claim-card .pred { font-family: var(--font-mono); font-size: 11px; color: var(--gray-9); padding: 0 4px; }
  .claim-card .arrow { color: var(--gray-9); }
  .claim-card .quals { margin-top: 12px; font-family: var(--font-mono); font-size: 11px; color: var(--gray-12); display: grid; grid-template-columns: 140px 1fr; gap: 4px 14px; padding: 10px 12px; background: var(--gray-2); border-radius: 8px; }
  .claim-card .quals .k { color: var(--gray-9); letter-spacing: 0.08em; }
  .claim-card .status-row { margin-top: 12px; display: flex; align-items: center; gap: 8px; font-family: var(--font-mono); font-size: 11px; }
  .claim-card .status-row .from { color: var(--gray-9); }
  .claim-card .status-row .to { color: var(--good); font-weight: 600; }
  .pill.condition   { background: #FFCDD2; color: #B71C1C; }
  .pill.condition   .badge { background: rgba(183,28,28,.15); color: #B71C1C; }
  .pill.medication  { background: #C8E6C9; color: #1B5E20; }
  .pill.medication  .badge { background: rgba(27,94,32,.15); color: #1B5E20; }
  .pill.dosage      { background: #E1BEE7; color: #4A148C; }
  .pill.dosage      .badge { background: rgba(74,20,140,.15); color: #4A148C; }
  .pill.test        { background: #BBDEFB; color: #0D47A1; }
  .pill.test        .badge { background: rgba(13,71,161,.15); color: #0D47A1; }
  .pill.risk_factor { background: #FFCCBC; color: #BF360C; }
  .pill.risk_factor .badge { background: rgba(191,54,12,.15); color: #BF360C; }
  .pill.symptom     { background: #FFF9C4; color: #F57F17; }
  .pill.symptom     .badge { background: rgba(245,127,23,.15); color: #F57F17; }
  .pill.context     { background: #E0E0E0; color: #37474F; }
  .pill.context     .badge { background: rgba(55,71,79,.15); color: #37474F; }
  .pill.vital       { background: #B2DFDB; color: #004D40; }
  .pill.vital       .badge { background: rgba(0,77,64,.15); color: #004D40; }
  .pill.anatomy     { background: #D7CCC8; color: #3E2723; }
  .pill.anatomy     .badge { background: rgba(62,39,35,.15); color: #3E2723; }
  .pill.duration    { background: #D7CCC8; color: #4E342E; }
  .pill.duration    .badge { background: rgba(78,52,46,.15); color: #4E342E; }
```

- [ ] **Step 3: Add scene-6 DOM container after the `s3` container, inside `#stage`**

```html
    <div class="s6-stage" id="s6" style="display:none;">
      <div id="s6-cards"></div>
    </div>
```

- [ ] **Step 4: Append scene 6 to SCENES**

```javascript
  {
    title: '6. Claims emerge',
    run: async () => {
      $('s4-term').classList.remove('shown');
      $('s3').style.display = 'none';
      $('s6').style.display = 'flex';
      applyCamera({ scale: 1.0, tx: 0, ty: 0, ms: 900 });
      requestAnimationFrame(() => $('s6').classList.add('shown'));
      await wait(950);
      const host = $('s6-cards');
      host.innerHTML = '';
      for (const c of CLAIMS) {
        const card = document.createElement('div');
        card.className = 'claim-card';
        card.innerHTML = `
          <div class="triple">
            <span class="pill ${c.subject.cat}">${escapeHtml(c.subject.text)}<span class="badge">${c.subject.cat.toUpperCase()}</span></span>
            <span class="pred">─ ${c.predicate} →</span>
            <span class="pill ${c.object.cat}">${escapeHtml(c.object.text)}<span class="badge">${c.object.cat.toUpperCase()}</span></span>
          </div>
          <div class="quals">
            ${c.qualifiers.map(([k, v]) => `<span class="k">${k}</span><span>${escapeHtml(v)}</span>`).join('')}
          </div>
          <div class="status-row">
            <span class="from">status:</span> <span class="from">${c.initialStatus}</span> → <span class="to">${c.finalStatus} ✓</span>
          </div>
        `;
        host.appendChild(card);
        fadeInCard(card, 450);
        await wait(1200);
      }
      await wait(2000);
    },
  },
```

- [ ] **Step 5: Verify scene 6**

Open `d:\MedBrain\medbrain-pitch.html?scene=6&dev=1`.
Expected: Three claim cards stack vertically, each fading in with a 1.2s gap. Each shows subject pill (red/green/etc.) → predicate verb → object pill, qualifiers grid below in mono, status flips from `pending_review` to `auto_promoted ✓` (green).

- [ ] **Step 6: Commit**

```bash
git add medbrain-pitch.html
git commit -m "feat(pitch): scene 6 three qualified claim cards with chip palette"
```

---

## Task 7: Scene 7 — Auto-promote gate side panel

**Files:**
- Modify: `d:\MedBrain\medbrain-pitch.html`

- [ ] **Step 1: Add `GATE_CHECKS` constant**

```javascript
const GATE_CHECKS = [
  { text: 'evidence_grade ∈ {meta_analysis, RCT, guideline, cohort}', pass: true },
  { text: 'no contradictions detected',                              pass: true },
  { text: 'all entities known to brain',                             pass: true },
  { text: '≥3 qualifier fields populated',                           pass: true },
];
const GATE_FAIL_EXAMPLE = { text: 'certainty: low → BLOCKED', pass: false };
```

- [ ] **Step 2: Add scene-7 CSS**

```css
  /* Scene 7 — auto-promote gate */
  .s7-panel { position: absolute; right: 80px; top: 200px; width: 380px; background: var(--surface); border: 1px solid var(--gray-3); border-radius: 14px; padding: 22px 24px; opacity: 0; transform: translateX(40px); transition: opacity 500ms ease, transform 500ms cubic-bezier(.65,.05,.36,1); box-shadow: 0 12px 40px rgba(0,0,0,0.06); }
  .s7-panel.shown { opacity: 1; transform: translateX(0); }
  .s7-panel .head { font-family: var(--font-mono); font-size: 11px; letter-spacing: 0.14em; color: var(--gray-9); margin-bottom: 14px; }
  .s7-panel .row { display: flex; align-items: flex-start; gap: 10px; padding: 8px 0; font-family: var(--font-mono); font-size: 11.5px; line-height: 1.5; opacity: 0; transition: opacity 300ms ease; border-bottom: 1px solid var(--gray-2); }
  .s7-panel .row.shown { opacity: 1; }
  .s7-panel .row .mark { font-size: 14px; font-weight: 700; min-width: 16px; }
  .s7-panel .row.pass .mark { color: var(--good); }
  .s7-panel .row.fail .mark { color: var(--bad); }
  .s7-panel .verdict { margin-top: 14px; font-family: var(--font-mono); font-size: 14px; letter-spacing: 0.14em; padding: 10px 12px; border-radius: 6px; text-align: center; font-weight: 600; }
  .s7-panel .verdict.good { background: #ecfdf5; color: var(--good); }
  .s7-panel .verdict.warn { background: #fff7ed; color: var(--warn); }
  .claim-card.dimmed { opacity: 0.35; transition: opacity 400ms ease; }
  .claim-card.focus  { transform: scale(1.04); transition: transform 400ms ease; box-shadow: 0 12px 40px rgba(0,0,0,0.06); }
```

- [ ] **Step 3: Add scene-7 DOM container at end of `#stage`**

```html
    <div class="s7-panel" id="s7-panel">
      <div class="head">AUTO-PROMOTE GATE</div>
      <div id="s7-rows"></div>
      <div class="verdict good" id="s7-verdict" style="display:none;">→ AUTO_PROMOTED</div>
    </div>
```

- [ ] **Step 4: Append scene 7 to SCENES**

```javascript
  {
    title: '7. Auto-promote gate',
    run: async () => {
      const cards = document.querySelectorAll('.claim-card');
      cards.forEach((c, i) => { if (i !== 0) c.classList.add('dimmed'); });
      cards[0]?.classList.add('focus');
      await wait(400);
      const panel = $('s7-panel');
      panel.classList.add('shown');
      const rowsHost = $('s7-rows');
      rowsHost.innerHTML = '';
      for (const ck of GATE_CHECKS) {
        const row = document.createElement('div');
        row.className = 'row ' + (ck.pass ? 'pass' : 'fail');
        row.innerHTML = `<span class="mark">${ck.pass ? '✓' : '✗'}</span><span>${escapeHtml(ck.text)}</span>`;
        rowsHost.appendChild(row);
        requestAnimationFrame(() => row.classList.add('shown'));
        await wait(320);
      }
      await wait(400);
      const verdict = $('s7-verdict');
      verdict.style.display = 'block';
      fadeInCard(verdict, 350);
      await wait(1400);
      verdict.textContent = '→ PENDING_REVIEW';
      verdict.classList.remove('good');
      verdict.classList.add('warn');
      const failRow = document.createElement('div');
      failRow.className = 'row fail';
      failRow.innerHTML = `<span class="mark">✗</span><span>${escapeHtml(GATE_FAIL_EXAMPLE.text)}</span>`;
      rowsHost.appendChild(failRow);
      requestAnimationFrame(() => failRow.classList.add('shown'));
      await wait(1800);
      panel.classList.remove('shown');
      cards.forEach(c => { c.classList.remove('dimmed'); c.classList.remove('focus'); });
      await wait(500);
    },
  },
```

- [ ] **Step 5: Verify scene 7**

Open `d:\MedBrain\medbrain-pitch.html?scene=7&dev=1`.
Expected: First claim card highlights, others dim. Right-side panel slides in. Four green ✓ checks tick in. `→ AUTO_PROMOTED` verdict appears in green. Then verdict flips to `→ PENDING_REVIEW` (warn amber) and a red ✗ row appears below. Panel slides out.

- [ ] **Step 6: Commit**

```bash
git add medbrain-pitch.html
git commit -m "feat(pitch): scene 7 auto-promote gate panel with verdict flip"
```

---

## Task 8: Scene 8 — Supersession (old claim archived)

**Files:**
- Modify: `d:\MedBrain\medbrain-pitch.html`

- [ ] **Step 1: Add scene-8 CSS**

```css
  /* Scene 8 — supersession */
  .s8-stage { position: absolute; inset: 0; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 14px; opacity: 0; transition: opacity 500ms ease; }
  .s8-stage.shown { opacity: 1; }
  .s8-old { width: 600px; opacity: 0; transition: opacity 400ms ease; }
  .s8-old .claim-card { background: var(--gray-2); border-style: dashed; }
  .s8-old.shown { opacity: 0.5; }
  .s8-arrow { font-family: var(--font-mono); font-size: 11px; color: var(--gray-9); padding: 6px 10px; border: 1px solid var(--gray-3); border-radius: 4px; background: var(--surface); opacity: 0; transition: opacity 400ms ease; }
  .s8-arrow.shown { opacity: 1; }
  .s8-new { width: 600px; opacity: 0; transition: opacity 400ms ease; }
  .s8-new.shown { opacity: 1; }
  .s8-caption { font-family: var(--font-mono); font-size: 13px; letter-spacing: 0.06em; color: var(--text); opacity: 0; transition: opacity 600ms ease; margin-top: 18px; }
  .s8-caption.shown { opacity: 1; }
  .s8-archived-badge { display: inline-block; font-family: var(--font-mono); font-size: 9px; letter-spacing: 0.14em; padding: 2px 6px; border: 1px solid var(--gray-9); color: var(--gray-9); border-radius: 4px; margin-left: 8px; }
```

- [ ] **Step 2: Add scene-8 DOM**

```html
    <div class="s8-stage" id="s8" style="display:none;">
      <div class="s8-old" id="s8-old">
        <div class="claim-card">
          <div class="triple">
            <span class="pill condition">Plasmodium falciparum<span class="badge">CONDITION</span></span>
            <span class="pred">─ treats →</span>
            <span class="pill medication">chloroquine<span class="badge">MEDICATION</span></span>
          </div>
          <div class="quals">
            <span class="k">evidence_grade</span><span>RCT (1995)</span>
            <span class="k">valid_until</span><span>2003</span>
          </div>
          <div class="status-row">
            <span class="from">status:</span> <span class="from">archived</span><span class="s8-archived-badge">ARCHIVED</span>
          </div>
        </div>
      </div>
      <div class="s8-arrow" id="s8-arrow">supersedes_id ↓</div>
      <div class="s8-new" id="s8-new">
        <div class="claim-card">
          <div class="triple">
            <span class="pill condition">Plasmodium falciparum<span class="badge">CONDITION</span></span>
            <span class="pred">─ resists →</span>
            <span class="pill medication">chloroquine<span class="badge">MEDICATION</span></span>
          </div>
          <div class="quals">
            <span class="k">evidence_grade</span><span>meta_analysis</span>
            <span class="k">valid_from</span><span>2003</span>
            <span class="k">certainty</span><span>high</span>
          </div>
          <div class="status-row">
            <span class="from">status:</span> <span class="to">auto_promoted ✓</span>
          </div>
        </div>
      </div>
      <div class="s8-caption" id="s8-caption">Never forgets. Only supersedes.</div>
    </div>
```

- [ ] **Step 3: Append scene 8 to SCENES**

```javascript
  {
    title: '8. Supersession',
    run: async () => {
      $('s6').style.display = 'none';
      $('s8').style.display = 'flex';
      requestAnimationFrame(() => $('s8').classList.add('shown'));
      await wait(500);
      $('s8-old').classList.add('shown');
      await wait(800);
      $('s8-arrow').classList.add('shown');
      await wait(600);
      $('s8-new').classList.add('shown');
      await wait(900);
      $('s8-caption').classList.add('shown');
      await wait(2400);
    },
  },
```

- [ ] **Step 4: Verify scene 8**

Open `d:\MedBrain\medbrain-pitch.html?scene=8&dev=1`.
Expected: Old claim card (dashed border, gray background, "ARCHIVED" badge) appears at half opacity. `supersedes_id ↓` arrow label fades in. New claim (full opacity, status `auto_promoted ✓`) appears below. Caption `Never forgets. Only supersedes.` types in. Holds 2.4s.

- [ ] **Step 5: Commit**

```bash
git add medbrain-pitch.html
git commit -m "feat(pitch): scene 8 supersession with archived predecessor"
```

---

## Task 9: Scene 9 — Zoom BRAIN (memory.md + questions.md + feedback arrow)

**Files:**
- Modify: `d:\MedBrain\medbrain-pitch.html`

- [ ] **Step 1: Add `BRAIN_MEMORY_TEXT` and `BRAIN_QUESTIONS_TEXT` constants**

```javascript
const BRAIN_MEMORY_TEXT = `## Cross-concept patterns

- artemisinin resistance correlates with K13 mutation
  in 4/12 claim clusters (high confidence)

- pregnancy + endemic-region claims cluster around
  artemether-lumefantrine adjusted dosing`;

const BRAIN_QUESTIONS_TEXT = `## Research backlog

- what is the K13 prevalence in Greater Mekong 2025?
- any RCT data on AL adjusted dosing in T1?`;
```

- [ ] **Step 2: Add scene-9 CSS**

```css
  /* Scene 9 — BRAIN files */
  .s9-stage { position: absolute; inset: 0; display: flex; align-items: center; justify-content: center; gap: 32px; opacity: 0; transition: opacity 500ms ease; }
  .s9-stage.shown { opacity: 1; }
  .md-file { width: 420px; min-height: 320px; background: var(--surface); border: 1px solid var(--gray-3); border-radius: 12px; padding: 18px 22px; opacity: 0; transform: translateY(8px); transition: opacity 450ms ease, transform 450ms ease; }
  .md-file.shown { opacity: 1; transform: translateY(0); }
  .md-file .filebar { display: flex; align-items: center; gap: 10px; padding-bottom: 12px; border-bottom: 1px solid var(--gray-3); margin-bottom: 14px; }
  .md-file .filebar .icon { font-family: var(--font-mono); font-size: 9px; letter-spacing: 0.1em; padding: 3px 6px; background: var(--gray-12); color: white; border-radius: 4px; }
  .md-file .filebar .name { font-family: var(--font-mono); font-size: 12px; color: var(--text); }
  .md-file .body { font-family: var(--font-mono); font-size: 12px; line-height: 1.7; color: var(--gray-12); white-space: pre-wrap; min-height: 200px; }
  .s9-feedback { position: absolute; bottom: 90px; left: 50%; transform: translateX(-50%); font-family: var(--font-mono); font-size: 11px; color: var(--gray-9); opacity: 0; transition: opacity 600ms ease; padding: 6px 12px; border: 1px dashed var(--gray-4); border-radius: 999px; background: var(--surface); }
  .s9-feedback.shown { opacity: 1; }
```

- [ ] **Step 3: Add scene-9 DOM**

```html
    <div class="s9-stage" id="s9" style="display:none;">
      <div class="md-file" id="s9-memory">
        <div class="filebar"><span class="icon">MD</span><span class="name">memory.md</span></div>
        <div class="body" id="s9-memory-body"></div>
      </div>
      <div class="md-file" id="s9-questions">
        <div class="filebar"><span class="icon">MD</span><span class="name">questions.md</span></div>
        <div class="body" id="s9-questions-body"></div>
      </div>
      <div class="s9-feedback" id="s9-feedback">questions.md → feeds STUDENT backlog</div>
    </div>
```

- [ ] **Step 4: Append scene 9 to SCENES**

```javascript
  {
    title: '9. BRAIN synthesis',
    run: async () => {
      $('s8').style.display = 'none';
      $('s9').style.display = 'flex';
      requestAnimationFrame(() => $('s9').classList.add('shown'));
      await wait(500);
      $('s9-memory').classList.add('shown');
      await wait(500);
      await streamText($('s9-memory-body'), BRAIN_MEMORY_TEXT, 8);
      await wait(700);
      $('s9-questions').classList.add('shown');
      await wait(500);
      await streamText($('s9-questions-body'), BRAIN_QUESTIONS_TEXT, 8);
      await wait(600);
      $('s9-feedback').classList.add('shown');
      await wait(2200);
    },
  },
```

- [ ] **Step 5: Verify scene 9**

Open `d:\MedBrain\medbrain-pitch.html?scene=9&dev=1`.
Expected: Two file-icon panels side by side. Left = `memory.md` streams in synthesis text. Right = `questions.md` streams in research backlog. Below them: dashed feedback pill `questions.md → feeds STUDENT backlog`.

- [ ] **Step 6: Commit**

```bash
git add medbrain-pitch.html
git commit -m "feat(pitch): scene 9 BRAIN memory/questions files with feedback loop"
```

---

## Task 10: Scene 10 — Zoom GRAPHIFY (knowledge graph build)

**Files:**
- Modify: `d:\MedBrain\medbrain-pitch.html`

- [ ] **Step 1: Add `GRAPH_NODES` and `GRAPH_EDGES` constants**

```javascript
// Hand-laid 30-node layout fitting a 1200×600 area centered on stage
const GRAPH_NODES = [
  { id: 'pf',     label: 'P. falciparum',    cat: 'condition',   x: 600, y: 300 },
  { id: 'pv',     label: 'P. vivax',         cat: 'condition',   x: 760, y: 220 },
  { id: 'pm',     label: 'P. malariae',      cat: 'condition',   x: 920, y: 280 },
  { id: 'sev',    label: 'severe malaria',   cat: 'condition',   x: 460, y: 220 },
  { id: 'unc',    label: 'uncomplicated',    cat: 'condition',   x: 460, y: 380 },
  { id: 'al',     label: 'artemether-lume',  cat: 'medication',  x: 320, y: 300 },
  { id: 'art',    label: 'artesunate',       cat: 'medication',  x: 220, y: 220 },
  { id: 'qn',     label: 'quinine',          cat: 'medication',  x: 220, y: 380 },
  { id: 'cq',     label: 'chloroquine',      cat: 'medication',  x: 280, y: 100 },
  { id: 'pyr',    label: 'pyrimethamine',    cat: 'medication',  x: 380, y: 80  },
  { id: 'k13',    label: 'K13 mutation',     cat: 'risk_factor', x: 760, y: 380 },
  { id: 'preg',   label: 'pregnancy',        cat: 'context',     x: 600, y: 460 },
  { id: 'mek',    label: 'Greater Mekong',   cat: 'context',     x: 920, y: 440 },
  { id: 'rdt',    label: 'RDT',              cat: 'test',        x: 700, y: 540 },
  { id: 'smear',  label: 'blood smear',      cat: 'test',        x: 540, y: 560 },
  { id: 'fever',  label: 'fever',            cat: 'symptom',     x: 1080, y: 360 },
  { id: 'chills', label: 'chills',           cat: 'symptom',     x: 1080, y: 460 },
  { id: 'hb',     label: 'low Hb',           cat: 'symptom',     x: 1060, y: 200 },
  { id: 'who',    label: 'WHO 2024',         cat: 'context',     x: 380, y: 540 },
  { id: 'cdc',    label: 'CDC',              cat: 'context',     x: 240, y: 480 },
  { id: 'dur3',   label: '3 days',           cat: 'duration',    x: 100, y: 280 },
  { id: 'pk',     label: 'parasitemia >5%',  cat: 'vital',       x: 380, y: 160 },
  { id: 'cer',    label: 'cerebral signs',   cat: 'vital',       x: 580, y: 80  },
  { id: 'jaund',  label: 'jaundice',         cat: 'symptom',     x: 720, y: 100 },
  { id: 'kid',    label: 'AKI',              cat: 'condition',   x: 880, y: 100 },
  { id: 'ruq',    label: 'RUQ tenderness',   cat: 'symptom',     x: 1020, y: 100 },
  { id: 'rea',    label: 'travel hist.',     cat: 'risk_factor', x: 100, y: 460 },
  { id: 'ic',     label: 'immunocomp.',      cat: 'risk_factor', x: 100, y: 380 },
  { id: 'kid2',   label: 'renal fn',         cat: 'test',        x: 1180, y: 280 },
  { id: 'dur24',  label: '24h fluid',        cat: 'duration',    x: 1180, y: 380 },
];
const GRAPH_EDGES = [
  ['al','unc'], ['art','sev'], ['qn','sev'], ['cq','pf'], ['pyr','pf'],
  ['k13','pf'], ['preg','unc'], ['mek','pf'], ['rdt','pf'], ['smear','pf'],
  ['fever','pf'], ['chills','pf'], ['hb','sev'], ['who','al'], ['cdc','al'],
  ['dur3','al'], ['pk','sev'], ['cer','sev'], ['jaund','sev'], ['kid','sev'],
  ['ruq','unc'], ['rea','pf'], ['ic','sev'], ['kid2','sev'], ['dur24','sev'],
  ['unc','pf'], ['sev','pf'], ['pv','rdt'], ['pm','smear'], ['preg','al'],
  ['cq','rea'], ['art','dur3'], ['al','preg'], ['k13','mek'], ['hb','jaund'],
  ['ruq','fever'], ['cer','cer'], ['fever','rdt'], ['chills','rdt'], ['who','cdc'],
  ['who','art'], ['cdc','rea'], ['pk','smear'], ['kid','kid2'], ['preg','dur24'],
  ['art','dur24'], ['ic','rea'], ['mek','cdc'], ['k13','art'], ['k13','al'],
];
```

- [ ] **Step 2: Add scene-10 CSS**

```css
  /* Scene 10 — graph */
  .s10-stage { position: absolute; inset: 0; opacity: 0; transition: opacity 500ms ease; }
  .s10-stage.shown { opacity: 1; }
  #s10-svg { width: 100%; height: 100%; }
  .s10-stage .node { transition: opacity 320ms ease, transform 320ms cubic-bezier(.34,1.4,.64,1); transform-origin: center; transform-box: fill-box; }
  .s10-stage .edge { stroke: var(--gray-4); stroke-width: 1; fill: none; opacity: 0.6; }
  .s10-stage .label { font-family: var(--font-mono); font-size: 9px; fill: var(--gray-12); }
  .s10-counter { position: absolute; top: 60px; right: 80px; font-family: var(--font-mono); font-size: 13px; color: var(--gray-12); text-align: right; line-height: 1.6; }
  .s10-counter .k { color: var(--gray-9); font-size: 10px; letter-spacing: 0.12em; }
```

Add a category fill mapping in the same `<style>` block:

```css
  .node-condition   { fill: #FFCDD2; stroke: #B71C1C; }
  .node-medication  { fill: #C8E6C9; stroke: #1B5E20; }
  .node-test        { fill: #BBDEFB; stroke: #0D47A1; }
  .node-risk_factor { fill: #FFCCBC; stroke: #BF360C; }
  .node-symptom     { fill: #FFF9C4; stroke: #F57F17; }
  .node-context     { fill: #E0E0E0; stroke: #37474F; }
  .node-vital       { fill: #B2DFDB; stroke: #004D40; }
  .node-duration    { fill: #D7CCC8; stroke: #4E342E; }
```

- [ ] **Step 3: Add scene-10 DOM**

```html
    <div class="s10-stage" id="s10" style="display:none;">
      <svg id="s10-svg" viewBox="0 0 1440 720" preserveAspectRatio="xMidYMid meet">
        <g id="s10-edges"></g>
        <g id="s10-nodes"></g>
      </svg>
      <div class="s10-counter">
        <div><span class="k">NODES</span> <span id="s10-nodes-count">0</span></div>
        <div><span class="k">EDGES</span> <span id="s10-edges-count">0</span></div>
      </div>
    </div>
```

- [ ] **Step 4: Append scene 10 to SCENES**

```javascript
  {
    title: '10. GRAPHIFY — knowledge graph',
    run: async () => {
      $('s9').style.display = 'none';
      $('s10').style.display = 'block';
      requestAnimationFrame(() => $('s10').classList.add('shown'));
      const svg = $('s10-svg');
      const nodesG = $('s10-nodes');
      const edgesG = $('s10-edges');
      nodesG.innerHTML = '';
      edgesG.innerHTML = '';
      const nodeById = {};
      for (const n of GRAPH_NODES) nodeById[n.id] = n;
      // Pop nodes
      for (let i = 0; i < GRAPH_NODES.length; i++) {
        const n = GRAPH_NODES[i];
        const g = document.createElementNS('http://www.w3.org/2000/svg', 'g');
        g.setAttribute('class', 'node');
        g.setAttribute('transform', `translate(${n.x}, ${n.y})`);
        const c = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
        c.setAttribute('r', '8');
        c.setAttribute('class', `node-${n.cat}`);
        c.setAttribute('stroke-width', '1.5');
        const t = document.createElementNS('http://www.w3.org/2000/svg', 'text');
        t.setAttribute('class', 'label');
        t.setAttribute('x', '12');
        t.setAttribute('y', '4');
        t.textContent = n.label;
        g.appendChild(c);
        g.appendChild(t);
        nodesG.appendChild(g);
        popInNode(g, 280);
        $('s10-nodes-count').textContent = i + 1;
        await wait(60);
      }
      await wait(200);
      // Draw edges
      for (let i = 0; i < GRAPH_EDGES.length; i++) {
        const [from, to] = GRAPH_EDGES[i];
        const a = nodeById[from], b = nodeById[to];
        if (!a || !b) continue;
        const p = document.createElementNS('http://www.w3.org/2000/svg', 'path');
        p.setAttribute('class', 'edge');
        p.setAttribute('d', `M ${a.x} ${a.y} Q ${(a.x + b.x) / 2} ${(a.y + b.y) / 2 - 30} ${b.x} ${b.y}`);
        edgesG.appendChild(p);
        drawGraphEdge(p, 500);
        $('s10-edges-count').textContent = i + 1;
        await wait(45);
      }
      await wait(2000);
    },
  },
```

- [ ] **Step 5: Verify scene 10**

Open `d:\MedBrain\medbrain-pitch.html?scene=10&dev=1`.
Expected: Empty SVG canvas. 30 nodes pop in one-by-one with category-tinted fills. Top-right counter increments `0 → 30`. Then 50 curved edges draw between them, edges counter increments. Holds 2s.

- [ ] **Step 6: Commit**

```bash
git add medbrain-pitch.html
git commit -m "feat(pitch): scene 10 GRAPHIFY knowledge graph build animation"
```

---

## Task 11: Scene 11 — Zoom DREAM (derivative artifacts + firewall caption)

**Files:**
- Modify: `d:\MedBrain\medbrain-pitch.html`

- [ ] **Step 1: Add `DREAM_CARDS` constant**

```javascript
const DREAM_CARDS = [
  { type: 'flashcard', label: 'FLASHCARD', body: 'Q: First-line for uncomplicated falciparum?\nA: Artemether-lumefantrine, 6 doses over 3 days, with food.' },
  { type: 'mnemonic', label: 'MNEMONIC',  body: '"AL with food, three days through —\nfalciparum needs them all to do."' },
  { type: 'analogy',  label: 'ANALOGY',   body: 'Artemisinin combo : malaria :: HAART : HIV — no monotherapy survives selection pressure.' },
  { type: 'gap',      label: 'GAP',       body: 'MISSING: artesunate dosing in third-trimester pregnancy — no RCT in corpus.' },
];
```

- [ ] **Step 2: Add scene-11 CSS**

```css
  /* Scene 11 — DREAM */
  .s11-stage { position: absolute; inset: 0; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 16px; opacity: 0; transition: opacity 500ms ease; padding-top: 40px; }
  .s11-stage.shown { opacity: 1; }
  .s11-grid { display: grid; grid-template-columns: 320px 320px; gap: 16px; }
  .deriv-card { background: var(--surface); border: 1px solid var(--warn); border-radius: 12px; padding: 14px 16px; opacity: 0; }
  .deriv-card .head { display: flex; justify-content: space-between; align-items: center; padding-bottom: 8px; border-bottom: 1px solid var(--gray-3); margin-bottom: 8px; }
  .deriv-card .head .label { font-family: var(--font-mono); font-size: 10px; letter-spacing: 0.14em; color: var(--warn); }
  .deriv-card .head .ns { font-family: var(--font-mono); font-size: 9px; letter-spacing: 0.1em; color: var(--gray-9); padding: 2px 6px; border: 1px solid var(--warn); border-radius: 4px; }
  .deriv-card .body { font-family: var(--font-mono); font-size: 11px; line-height: 1.6; color: var(--gray-12); white-space: pre-wrap; }
  .s11-caption { font-family: var(--font-mono); font-size: 12px; color: var(--text); opacity: 0; transition: opacity 600ms ease; margin-top: 16px; }
  .s11-caption.shown { opacity: 1; }
```

- [ ] **Step 3: Add scene-11 DOM**

```html
    <div class="s11-stage" id="s11" style="display:none;">
      <div class="s11-grid" id="s11-grid"></div>
      <div class="s11-caption" id="s11-caption">Synthetic. Tagged at retrieval. Never feeds back as evidence.</div>
    </div>
```

- [ ] **Step 4: Append scene 11 to SCENES**

```javascript
  {
    title: '11. DREAM — derivatives',
    run: async () => {
      $('s10').style.display = 'none';
      $('s11').style.display = 'flex';
      requestAnimationFrame(() => $('s11').classList.add('shown'));
      await wait(500);
      const grid = $('s11-grid');
      grid.innerHTML = '';
      for (const c of DREAM_CARDS) {
        const card = document.createElement('div');
        card.className = 'deriv-card';
        card.innerHTML = `
          <div class="head"><span class="label">${c.label}</span><span class="ns">derivative/</span></div>
          <div class="body">${escapeHtml(c.body)}</div>
        `;
        grid.appendChild(card);
        fadeInCard(card, 400);
        await wait(350);
      }
      await wait(500);
      $('s11-caption').classList.add('shown');
      await wait(2400);
    },
  },
```

- [ ] **Step 5: Verify scene 11**

Open `d:\MedBrain\medbrain-pitch.html?scene=11&dev=1`.
Expected: 2×2 grid of cards (flashcard, mnemonic, analogy, gap) each with warn-color border and `derivative/` namespace badge. Cards fade in one-by-one. Caption beneath: `Synthetic. Tagged at retrieval. Never feeds back as evidence.`

- [ ] **Step 6: Commit**

```bash
git add medbrain-pitch.html
git commit -m "feat(pitch): scene 11 DREAM derivative cards with firewall caption"
```

---

## Task 12: Scene 12 — Output 8-primitive retrieval menu

**Files:**
- Modify: `d:\MedBrain\medbrain-pitch.html`

- [ ] **Step 1: Add `RETRIEVAL_PRIMITIVES` constant**

```javascript
const RETRIEVAL_PRIMITIVES = [
  'get_concept',
  'find_supersession_chain',
  'query_with_qualifiers',
  'traverse_graph',
  'list_recent_promotions',
  'get_evidence_ledger',
  'search_questions',
  'get_derivatives',
];
```

- [ ] **Step 2: Add scene-12 CSS**

```css
  /* Scene 12 — retrieval menu */
  .s12-stage { position: absolute; inset: 0; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 24px; opacity: 0; transition: opacity 500ms ease; }
  .s12-stage.shown { opacity: 1; }
  .s12-row { display: flex; align-items: center; gap: 28px; }
  .s12-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px 22px; }
  .s12-prim { font-family: var(--font-mono); font-size: 14px; padding: 10px 18px; border: 1px solid var(--gray-3); border-radius: 999px; background: var(--surface); color: var(--text); opacity: 0; }
  .s12-line { width: 80px; height: 1px; background: var(--gray-4); border-top: 1px dashed var(--gray-4); border-style: dashed; }
  .s12-cds { font-family: var(--font-mono); font-size: 14px; padding: 12px 22px; border: 1px solid var(--gray-12); border-radius: 999px; color: var(--text); background: var(--gray-2); opacity: 0; }
  .s12-cds.shown, .s12-prim.shown { opacity: 1; }
  .s12-caption { font-family: var(--font-mono); font-size: 13px; letter-spacing: 0.06em; color: var(--text); opacity: 0; transition: opacity 600ms ease; }
  .s12-caption.shown { opacity: 1; }
```

- [ ] **Step 3: Add scene-12 DOM**

```html
    <div class="s12-stage" id="s12" style="display:none;">
      <div class="s12-row">
        <div class="s12-grid" id="s12-grid"></div>
        <div class="s12-line"></div>
        <div class="s12-cds" id="s12-cds">NEO CDS</div>
      </div>
      <div class="s12-caption" id="s12-caption">Any CDS plugs in. We are the substrate.</div>
    </div>
```

- [ ] **Step 4: Append scene 12 to SCENES**

```javascript
  {
    title: '12. Retrieval primitives',
    run: async () => {
      $('s11').style.display = 'none';
      $('s12').style.display = 'flex';
      requestAnimationFrame(() => $('s12').classList.add('shown'));
      await wait(500);
      const grid = $('s12-grid');
      grid.innerHTML = '';
      for (const p of RETRIEVAL_PRIMITIVES) {
        const b = document.createElement('div');
        b.className = 's12-prim';
        b.textContent = p;
        grid.appendChild(b);
        fadeInCard(b, 280);
        await wait(160);
      }
      await wait(400);
      fadeInCard($('s12-cds'), 400);
      await wait(700);
      $('s12-caption').classList.add('shown');
      await wait(2400);
    },
  },
```

- [ ] **Step 5: Verify scene 12**

Open `d:\MedBrain\medbrain-pitch.html?scene=12&dev=1`.
Expected: 2-column list of 8 mono pills (`get_concept`, `find_supersession_chain`, etc.) appears one-by-one. Right of them: a `NEO CDS` pill connected by dashed line. Caption beneath: `Any CDS plugs in. We are the substrate.`

- [ ] **Step 6: Commit**

```bash
git add medbrain-pitch.html
git commit -m "feat(pitch): scene 12 8-primitive retrieval menu with CDS connector"
```

---

## Task 13: Scene 13 — Moat (3 numbered cards)

**Files:**
- Modify: `d:\MedBrain\medbrain-pitch.html`

- [ ] **Step 1: Add `MOAT_CARDS` constant**

```javascript
const MOAT_CARDS = [
  {
    num: '01',
    title: 'QUALIFIED CLAIMS',
    body: 'Structured triples with population, region, dose, evidence grade.',
    footer: 'Not a vector blob.',
  },
  {
    num: '02',
    title: 'SUPERSESSION LEDGER',
    body: 'Old evidence stays archived, never deleted. New supersedes; both retrievable.',
    footer: 'Not a delete-and-replace.',
  },
  {
    num: '03',
    title: 'DREAM FIREWALL',
    body: 'Synthetic outputs never auto-promote; never feed back as evidence.',
    footer: 'Hallucination cannot pollute primary.',
  },
];
```

- [ ] **Step 2: Add scene-13 CSS**

```css
  /* Scene 13 — moat */
  .s13-stage { position: absolute; inset: 0; display: flex; align-items: center; justify-content: center; gap: 24px; opacity: 0; transition: opacity 500ms ease; }
  .s13-stage.shown { opacity: 1; }
  .moat-card { width: 320px; min-height: 280px; background: var(--surface); border: 1px solid var(--gray-3); border-radius: 14px; padding: 26px 28px; display: flex; flex-direction: column; gap: 14px; opacity: 0; }
  .moat-card .num { font-family: var(--font-mono); font-size: 11px; letter-spacing: 0.14em; color: var(--accent); }
  .moat-card .title { font-family: var(--font-sans); font-size: 18px; font-weight: 700; color: var(--text); letter-spacing: 0.04em; }
  .moat-card .rule { width: 36px; height: 1px; background: var(--gray-3); }
  .moat-card .body { font-family: var(--font-sans); font-size: 13px; line-height: 1.6; color: var(--gray-12); }
  .moat-card .footer { font-family: var(--font-mono); font-size: 11px; color: var(--gray-9); margin-top: auto; padding-top: 12px; border-top: 1px solid var(--gray-3); }
```

- [ ] **Step 3: Add scene-13 DOM**

```html
    <div class="s13-stage" id="s13" style="display:none;">
      <div id="s13-host" style="display:flex; gap:24px;"></div>
    </div>
```

- [ ] **Step 4: Append scene 13 to SCENES**

```javascript
  {
    title: '13. Moat',
    run: async () => {
      $('s12').style.display = 'none';
      $('s13').style.display = 'flex';
      requestAnimationFrame(() => $('s13').classList.add('shown'));
      await wait(500);
      const host = $('s13-host');
      host.innerHTML = '';
      for (const m of MOAT_CARDS) {
        const c = document.createElement('div');
        c.className = 'moat-card';
        c.innerHTML = `
          <div class="num">${m.num}</div>
          <div class="title">${escapeHtml(m.title)}</div>
          <div class="rule"></div>
          <div class="body">${escapeHtml(m.body)}</div>
          <div class="footer">${escapeHtml(m.footer)}</div>
        `;
        host.appendChild(c);
        fadeInCard(c, 450);
        await wait(300);
      }
      await wait(3500);
    },
  },
```

- [ ] **Step 5: Verify scene 13**

Open `d:\MedBrain\medbrain-pitch.html?scene=13&dev=1`.
Expected: Three side-by-side cards. Each has accent-color number (01/02/03), serif-bold title, body text, and italic-mono footer. Cards fade in left-to-right.

- [ ] **Step 6: Commit**

```bash
git add medbrain-pitch.html
git commit -m "feat(pitch): scene 13 moat cards"
```

---

## Task 14: Scene 14 — Status dashboard

**Files:**
- Modify: `d:\MedBrain\medbrain-pitch.html`

- [ ] **Step 1: Add `STATUS_DASHBOARD` constant**

```javascript
const STATUS_DASHBOARD = [
  ['DOMAIN',             'malaria'],
  ['CLAIMS',             { kind: 'tick', from: 0, to: 1247 }],
  ['SOURCES',            'PubMed · WHO · DailyMed'],
  ['AUTO-PROMOTE RATE',  '68%'],
  ['PENDING REVIEW',     '142'],
  ['LAST INGESTION',     '2 min ago'],
];
```

- [ ] **Step 2: Add scene-14 CSS**

```css
  /* Scene 14 — status dashboard */
  .s14-stage { position: absolute; inset: 0; display: flex; align-items: center; justify-content: center; opacity: 0; transition: opacity 500ms ease; }
  .s14-stage.shown { opacity: 1; }
  .s14-block { background: var(--surface); border: 1px solid var(--gray-3); border-radius: 14px; padding: 28px 32px; min-width: 520px; }
  .s14-block .row { display: grid; grid-template-columns: 220px 1fr; gap: 12px; padding: 10px 0; font-family: var(--font-mono); font-size: 13px; border-bottom: 1px solid var(--gray-2); }
  .s14-block .row:last-child { border-bottom: none; }
  .s14-block .row .k { color: var(--gray-9); letter-spacing: 0.12em; font-size: 11px; align-self: center; }
  .s14-block .row .v { color: var(--text); }
```

- [ ] **Step 3: Add scene-14 DOM**

```html
    <div class="s14-stage" id="s14" style="display:none;">
      <div class="s14-block" id="s14-block"></div>
    </div>
```

- [ ] **Step 4: Append scene 14 to SCENES**

```javascript
  {
    title: '14. Status',
    run: async () => {
      $('s13').style.display = 'none';
      $('s14').style.display = 'flex';
      requestAnimationFrame(() => $('s14').classList.add('shown'));
      await wait(500);
      const block = $('s14-block');
      block.innerHTML = '';
      for (const [k, v] of STATUS_DASHBOARD) {
        const row = document.createElement('div');
        row.className = 'row';
        row.innerHTML = `<span class="k">${k}</span><span class="v"></span>`;
        block.appendChild(row);
        fadeInCard(row, 280);
        const valEl = row.querySelector('.v');
        if (typeof v === 'object' && v.kind === 'tick') {
          tickCounter(valEl, v.from, v.to, 2200);
        } else {
          valEl.textContent = v;
        }
        await wait(220);
      }
      await wait(2200);
    },
  },
```

- [ ] **Step 5: Verify scene 14**

Open `d:\MedBrain\medbrain-pitch.html?scene=14&dev=1`.
Expected: Single mono dashboard block. Six rows fade in. The `CLAIMS` row's value ticks from `0` to `1,247` over ~2.2s. Holds ~2.2s.

- [ ] **Step 6: Commit**

```bash
git add medbrain-pitch.html
git commit -m "feat(pitch): scene 14 status dashboard with tick counter"
```

---

## Task 15: Scene 15 — Ask card + replay glow

**Files:**
- Modify: `d:\MedBrain\medbrain-pitch.html`

- [ ] **Step 1: Add `ASK` constant**

```javascript
const ASK = {
  amount: '$1.5M',
  months: '18 months',
  email:  'kedhareswer.12110626@gmail.com',
};
```

- [ ] **Step 2: Add scene-15 CSS (and replay-glow keyframe)**

```css
  /* Scene 15 — ask */
  .s15-stage { position: absolute; inset: 0; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 18px; opacity: 0; transition: opacity 700ms ease; }
  .s15-stage.shown { opacity: 1; }
  .s15-ask { font-family: var(--font-sans); font-size: 30px; font-weight: 600; color: var(--text); letter-spacing: 0.01em; }
  .s15-email { font-family: var(--font-mono); font-size: 13px; color: var(--gray-9); }
  #replay-btn.glow { animation: replayGlow 1.6s ease-in-out infinite; }
  @keyframes replayGlow { 0%, 100% { box-shadow: 0 0 0 0 rgba(37,99,235,0.0); } 50% { box-shadow: 0 0 0 6px rgba(37,99,235,0.4); } }
```

- [ ] **Step 3: Add scene-15 DOM**

```html
    <div class="s15-stage" id="s15" style="display:none;">
      <div class="s15-ask" id="s15-ask"></div>
      <div class="s15-email" id="s15-email"></div>
    </div>
```

- [ ] **Step 4: Append scene 15 to SCENES (final scene)**

```javascript
  {
    title: '15. Ask',
    run: async () => {
      $('s14').style.display = 'none';
      $('s15').style.display = 'flex';
      requestAnimationFrame(() => $('s15').classList.add('shown'));
      await wait(700);
      $('s15-ask').textContent = `Seed round — ${ASK.amount} for ${ASK.months}.`;
      $('s15-email').textContent = ASK.email;
      await wait(800);
      $('replay-btn').classList.add('glow');
      // Hold final state until reload.
    },
  },
```

- [ ] **Step 5: Verify scene 15**

Open `d:\MedBrain\medbrain-pitch.html?scene=15&dev=1`.
Expected: Centered single line `Seed round — $1.5M for 18 months.` with mono email below. Replay button in HUD pulses with accent-colored glow ring.

- [ ] **Step 6: Commit**

```bash
git add medbrain-pitch.html
git commit -m "feat(pitch): scene 15 ask card with replay glow"
```

---

## Task 16: End-to-end pass + transition fixes + final polish

**Files:**
- Modify: `d:\MedBrain\medbrain-pitch.html`

This task watches the whole pitch start-to-finish, then patches anything that looks rough at scene boundaries (stale DOM showing through, abrupt camera jumps, leftover cursor positions).

- [ ] **Step 1: Watch full playback once**

Open `d:\MedBrain\medbrain-pitch.html` (no query string). Watch all 15 scenes in order without intervening. Note any of:
- A previous scene's container is still visible behind the current scene (`display: none` was missed).
- Camera state from a zoomed scene carries into a non-zoom scene (e.g. scene 6 starts zoomed because scene 4/5 left scale 1.6).
- Cursor stays in a stale position across scene boundaries.
- Pause feels too long (>1s gap between scenes 5→6, 9→10, etc.).

- [ ] **Step 2: Add a single `resetStageBetweenScenes()` helper and call it inside scene runners that need a clean slate**

Add to engine primitives section:

```javascript
function resetStageBetweenScenes() {
  applyCamera({ scale: 1, tx: 0, ty: 0, ms: 600 });
}
```

Call it at the top of scenes 6, 8, 9, 11, 12, 13, 14, 15 (i.e. any scene that starts with a camera-1.0 expectation). Example for scene 6:

```javascript
    run: async () => {
      $('s4-term').classList.remove('shown');
      $('s3').style.display = 'none';
      $('s6').style.display = 'flex';
      resetStageBetweenScenes();
      await wait(650);
      // ...rest
    },
```

Apply the same pattern to the listed scenes. Where the scene previously did its own `applyCamera({ scale: 1, ... })` call, replace it with `resetStageBetweenScenes()`.

- [ ] **Step 3: Hide all prior scene containers before showing the next**

Add to engine primitives section:

```javascript
const ALL_SCENE_IDS = ['s1','s2','s3','s6','s8','s9','s10','s11','s12','s13','s14','s15'];
function showOnly(id) {
  for (const sid of ALL_SCENE_IDS) {
    const el = $(sid);
    if (!el) continue;
    el.style.display = (sid === id) ? (sid === 's3' || sid === 's10' ? 'block' : 'flex') : 'none';
    if (sid !== id) el.classList.remove('shown');
  }
}
```

Replace the per-scene `display: none` / `display: flex/block` toggles at the top of every scene from 2 onwards with one `showOnly('sN')` call. Example for scene 2:

```javascript
    run: async () => {
      $('s1-wordmark').classList.add('up');
      await wait(400);
      showOnly('s2');
      requestAnimationFrame(() => $('s2').classList.add('shown'));
      // ...rest
    },
```

Note: Scene 4 (terminal) overlays scene 3, not replaces it — keep scene 3 visible during scene 4. Don't apply `showOnly` for scene 4. Same for scene 5 and 7 (they overlay scenes 4 and 6 respectively).

- [ ] **Step 4: Watch full playback again, verify smooth scene transitions**

Open `d:\MedBrain\medbrain-pitch.html`. Confirm:
- No flash of stale content at scene boundaries.
- Camera always returns to (0,0,scale 1) before scenes that aren't zoomed.
- Total runtime ~2:15–2:45.
- Scene 15 holds; replay button glows.
- `?dev=1` panel still works for jumping.

- [ ] **Step 5: Commit**

```bash
git add medbrain-pitch.html
git commit -m "feat(pitch): end-to-end pass with showOnly helper and camera reset"
```

---

## Task 17: README pointer (optional, low-cost)

**Files:**
- Modify: `d:\MedBrain\README.md`

- [ ] **Step 1: Append a one-line pointer at the bottom of `README.md`**

Add at end of file:

```markdown

## Investor pitch

Open [`medbrain-pitch.html`](./medbrain-pitch.html) in a browser. ~2:30 scripted replay. Reload to replay.
```

- [ ] **Step 2: Commit**

```bash
git add README.md
git commit -m "docs: link investor pitch replay from README"
```

---

## Self-Review

**Spec coverage check:**

| Spec section | Covered by task |
|---|---|
| 1. Goal | Whole plan |
| 2. Constraints | Task 0 (single file, no deps, 1440×900) |
| 3. Tokens | Task 0 (`<style>` `:root`) and Task 6 (chip palette) |
| 4. Architecture (file shape) | File Structure section + Task 0 |
| 5.1 Scene 1 cold open | Task 1 |
| 5.2 Scene 2 problem | Task 2 |
| 5.3 Scene 3 architecture loop | Task 3 |
| 5.4 Scene 4 STUDENT zoom | Task 4 |
| 5.5 Scene 5 STUDENT streams | Task 5 |
| 5.6 Scene 6 claims | Task 6 |
| 5.7 Scene 7 gate | Task 7 |
| 5.8 Scene 8 supersession | Task 8 |
| 5.9 Scene 9 BRAIN | Task 9 |
| 5.10 Scene 10 GRAPHIFY | Task 10 |
| 5.11 Scene 11 DREAM | Task 11 |
| 5.12 Scene 12 retrieval menu | Task 12 |
| 5.13 Scene 13 moat | Task 13 |
| 5.14 Scene 14 status | Task 14 |
| 5.15 Scene 15 ask | Task 15 |
| 6. HUD | Task 0 |
| 7. Cursor | Task 0 |
| 8. Content constants | Tasks 3, 5, 6, 7, 9, 10, 11, 12, 13, 14, 15 |
| 9. Motion principles | Task 0 (engine primitives) + scene tasks |
| 10. Failure modes | Task 0 (`play()` try/catch) |
| 11. Out of scope | n/a (not implemented, per spec) |
| 12. Pre-build placeholders | Tasks 14 & 15 |
| 13. File location | Task 0 |

All scenes covered. End-to-end polish covered by Task 16.

**Placeholder scan:** No "TBD" / "TODO" / "implement later" / vague handwave steps. Every code step has full code. Every command has expected output. Hand-laid graph node and edge data is included verbatim, not "fill in 30 nodes here."

**Type / name consistency:**
- Engine primitive names match across tasks: `applyCamera`, `moveCursorTo`, `cursorOver`, `clickFx`, `wait`, `typeInto`, `streamText`, `fadeInCard`, `popInNode`, `drawGraphEdge`, `tickCounter`, `escapeHtml`.
- Scene container ids: `s1`..`s15` (no `s4`, `s5`, `s7` — those overlay other scenes via `s4-term`, `s7-panel`).
- `ALL_SCENE_IDS` in Task 16 lists `s1, s2, s3, s6, s8, s9, s10, s11, s12, s13, s14, s15` — matches the actual rooted scene containers.
- Constants referenced in Task 6 (`CLAIMS`) define `subject.cat` strings (`condition`, `medication`, `context`); the chip CSS in Task 6 covers all of those plus extras for graph nodes used in Task 10.
- `GRAPH_NODES` categories in Task 10 are subset of node-* CSS classes added in same task.

No issues found.

---

## Execution Handoff

**Plan complete and saved to `docs/superpowers/plans/2026-05-01-medbrain-pitch.md`. Two execution options:**

**1. Subagent-Driven (recommended)** — I dispatch a fresh subagent per task, review between tasks, fast iteration.

**2. Inline Execution** — Execute tasks in this session using executing-plans, batch execution with checkpoints.

**Which approach?**
