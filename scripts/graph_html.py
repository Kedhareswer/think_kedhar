"""CLI: render brain/graph/graph.json + communities.json -> brain/graph/graph.html.

Self-contained interactive D3 force-directed viewer. Open the file in any
browser. No HTTP server, no build step, no dependencies.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from medbrain import config


HTML_TEMPLATE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>MedBrain knowledge graph</title>
<style>
  :root { color-scheme: dark; }
  html, body { margin: 0; height: 100%; background: #0b0d12; color: #e6e9ef; font: 13px/1.4 system-ui, sans-serif; overflow: hidden; }
  #app { display: grid; grid-template-columns: 1fr 360px; height: 100vh; }
  #canvas { background: radial-gradient(circle at 50% 50%, #161a22 0%, #0b0d12 70%); }
  #side { background: #11141b; border-left: 1px solid #1e2230; padding: 16px; overflow-y: auto; }
  h1 { font-size: 14px; margin: 0 0 4px 0; letter-spacing: .04em; text-transform: uppercase; color: #8ea1c0; }
  .stat { display: flex; justify-content: space-between; padding: 4px 0; border-bottom: 1px dashed #1e2230; font-variant-numeric: tabular-nums; }
  .stat span:last-child { color: #62d4a8; }
  input[type=search] { width: 100%; padding: 8px 10px; background: #0b0d12; color: #e6e9ef; border: 1px solid #1e2230; border-radius: 4px; outline: none; }
  input[type=search]:focus { border-color: #62d4a8; }
  #detail { margin-top: 16px; padding-top: 12px; border-top: 1px solid #1e2230; }
  #detail h2 { font-size: 13px; margin: 0 0 6px 0; color: #ffd479; word-break: break-word; }
  .edge { padding: 6px 0; border-bottom: 1px dashed #1e2230; font-size: 12px; }
  .edge .pred { color: #8ea1c0; font-weight: 600; }
  .edge .cert { float: right; font-size: 10px; color: #62d4a8; }
  .edge a { color: #4a9eff; text-decoration: none; }
  .legend { font-size: 11px; color: #8ea1c0; margin-top: 12px; }
  .legend .row { display: flex; align-items: center; gap: 6px; padding: 2px 0; }
  .legend .swatch { width: 12px; height: 12px; border-radius: 50%; flex-shrink: 0; }
  text.label { font: 10px system-ui, sans-serif; fill: #c8d0e0; pointer-events: none; user-select: none; paint-order: stroke; stroke: #0b0d12; stroke-width: 3; stroke-linejoin: round; }
  .controls { position: absolute; bottom: 12px; left: 12px; background: rgba(17,20,27,.85); padding: 8px 12px; border-radius: 6px; display: flex; gap: 14px; font-size: 11px; }
  .controls label { display: flex; gap: 4px; align-items: center; cursor: pointer; }
  .controls input[type=range] { width: 100px; }
</style>
</head>
<body>
<div id="app">
  <div style="position: relative;">
    <svg id="canvas"></svg>
    <div class="controls">
      <label>min claims <input id="minClaims" type="range" min="1" max="10" value="1"></label>
      <label>charge <input id="charge" type="range" min="-800" max="-50" value="-200"></label>
      <label><input id="showLabels" type="checkbox" checked> labels</label>
    </div>
  </div>
  <div id="side">
    <h1>MedBrain graph</h1>
    <div class="stat"><span>nodes</span><span id="stat-nodes">–</span></div>
    <div class="stat"><span>edges</span><span id="stat-edges">–</span></div>
    <div class="stat"><span>communities</span><span id="stat-comms">–</span></div>
    <div class="stat"><span>generated</span><span id="stat-gen">–</span></div>
    <div style="margin-top: 14px;">
      <input id="search" type="search" placeholder="search entity…" autocomplete="off">
    </div>
    <div id="detail">
      <p style="color:#8ea1c0;font-size:12px;">click a node to inspect its claims.</p>
    </div>
    <div class="legend" id="legend"></div>
  </div>
</div>

<script src="https://cdn.jsdelivr.net/npm/d3@7"></script>
<script>
const GRAPH = __GRAPH_JSON__;
const COMMS = __COMMS_JSON__;

document.getElementById('stat-nodes').textContent = GRAPH.stats.node_count;
document.getElementById('stat-edges').textContent = GRAPH.stats.edge_count;
document.getElementById('stat-comms').textContent = COMMS.communities.length;
document.getElementById('stat-gen').textContent = (GRAPH.stats.generated_at || '').slice(0,16).replace('T',' ');

const PRED_COLORS = {
  treats: '#62d4a8', causes: '#ff7676', resists: '#ffd479', requires: '#8ea1c0',
  contraindicates: '#e066ff', prevents: '#4a9eff', co_occurs: '#a0a0a0',
  recommends: '#62d4a8', supersedes: '#ff9a4a',
};
const FALLBACK_PRED = '#666';

const nodeToComm = new Map();
COMMS.communities.forEach((c, i) => c.members.forEach(m => nodeToComm.set(m, i)));
const palette = d3.schemeTableau10.concat(d3.schemeSet3, d3.schemePaired);
const commColor = (i) => palette[i % palette.length];

const legend = document.getElementById('legend');
legend.innerHTML = '<div style="margin:8px 0 4px 0;">predicate</div>' +
  Object.entries(PRED_COLORS).map(([k,v]) =>
    `<div class="row"><span class="swatch" style="background:${v}"></span>${k}</div>`).join('');

const w = window.innerWidth - 360, h = window.innerHeight;
const svg = d3.select('#canvas').attr('viewBox', [0, 0, w, h]);
const g = svg.append('g');
svg.call(d3.zoom().scaleExtent([0.1, 8]).on('zoom', e => g.attr('transform', e.transform)));

const nodes = GRAPH.nodes.map(n => ({...n}));
const links = GRAPH.edges.map(e => ({...e}));

const sim = d3.forceSimulation(nodes)
  .force('link', d3.forceLink(links).id(d => d.id).distance(60).strength(0.4))
  .force('charge', d3.forceManyBody().strength(-200))
  .force('center', d3.forceCenter(w/2, h/2))
  .force('collide', d3.forceCollide().radius(d => 4 + Math.sqrt(d.claim_count||1) * 1.5));

const linkSel = g.append('g').attr('stroke-opacity', 0.35).selectAll('line')
  .data(links).join('line')
  .attr('stroke', d => PRED_COLORS[d.predicate] || FALLBACK_PRED)
  .attr('stroke-width', d => ({high:2.4, moderate:1.6, low:1, very_low:0.6}[d.certainty] || 1));

const nodeSel = g.append('g').selectAll('circle')
  .data(nodes).join('circle')
  .attr('r', d => 3 + Math.sqrt(d.claim_count||1) * 1.4)
  .attr('fill', d => commColor(nodeToComm.get(d.id) ?? 0))
  .attr('stroke', '#0b0d12').attr('stroke-width', 0.8)
  .style('cursor','pointer')
  .call(drag(sim))
  .on('click', (e, d) => showDetail(d))
  .on('mouseover', (e, d) => { nodeSel.attr('opacity', n => isNeighbor(n,d) ? 1 : 0.15); linkSel.attr('opacity', l => l.source.id===d.id||l.target.id===d.id ? 0.9 : 0.05); })
  .on('mouseout', () => { nodeSel.attr('opacity', 1); linkSel.attr('opacity', null); });

nodeSel.append('title').text(d => `${d.label}\\nclaims: ${d.claim_count}`);

const labelSel = g.append('g').selectAll('text')
  .data(nodes).join('text')
  .attr('class','label')
  .attr('dx', 8).attr('dy', 3)
  .text(d => d.label.length > 30 ? d.label.slice(0,28)+'…' : d.label);

sim.on('tick', () => {
  linkSel.attr('x1', d => d.source.x).attr('y1', d => d.source.y)
         .attr('x2', d => d.target.x).attr('y2', d => d.target.y);
  nodeSel.attr('cx', d => d.x).attr('cy', d => d.y);
  labelSel.attr('x', d => d.x).attr('y', d => d.y);
});

function drag(sim) {
  return d3.drag()
    .on('start', e => { if (!e.active) sim.alphaTarget(0.3).restart(); e.subject.fx = e.subject.x; e.subject.fy = e.subject.y; })
    .on('drag', e => { e.subject.fx = e.x; e.subject.fy = e.y; })
    .on('end', e => { if (!e.active) sim.alphaTarget(0); e.subject.fx = null; e.subject.fy = null; });
}

function isNeighbor(n, d) {
  if (n.id === d.id) return true;
  return links.some(l => (l.source.id===d.id && l.target.id===n.id) || (l.target.id===d.id && l.source.id===n.id));
}

function showDetail(d) {
  const incident = links.filter(l => l.source.id===d.id || l.target.id===d.id);
  const html = [
    `<h2>${escapeHtml(d.label)}</h2>`,
    `<div style="font-size:11px;color:#8ea1c0;">claims: ${d.claim_count} · first seen ${(d.first_seen||'').slice(0,10)}</div>`,
    '<div style="margin-top:10px;">',
    ...incident.map(l => {
      const arrow = l.source.id===d.id ? '→' : '←';
      const other = l.source.id===d.id ? l.target.label : l.source.label;
      const url = l.source_url ? `<a href="${l.source_url}" target="_blank">PMID${l.source_external_id||''}</a>` : '';
      return `<div class="edge"><span class="cert">${l.certainty}</span><span class="pred">${l.predicate}</span> ${arrow} ${escapeHtml(other)}<br><small style="color:#666;">${url} · ${l.evidence_grade||''}</small></div>`;
    }),
    '</div>',
  ].join('');
  document.getElementById('detail').innerHTML = html;
}

function escapeHtml(s) { return String(s).replace(/[<>&\"]/g, c => ({'<':'&lt;','>':'&gt;','&':'&amp;','\"':'&quot;'}[c])); }

document.getElementById('search').addEventListener('input', e => {
  const q = e.target.value.toLowerCase();
  nodeSel.attr('opacity', n => !q || n.label.toLowerCase().includes(q) ? 1 : 0.1);
  labelSel.attr('opacity', n => !q || n.label.toLowerCase().includes(q) ? 1 : 0.1);
});

document.getElementById('minClaims').addEventListener('input', e => {
  const min = +e.target.value;
  nodeSel.attr('display', d => (d.claim_count||0) >= min ? null : 'none');
  labelSel.attr('display', d => (d.claim_count||0) >= min ? null : 'none');
  linkSel.attr('display', l => (l.source.claim_count||0) >= min && (l.target.claim_count||0) >= min ? null : 'none');
});

document.getElementById('charge').addEventListener('input', e => {
  sim.force('charge').strength(+e.target.value);
  sim.alpha(0.5).restart();
});

document.getElementById('showLabels').addEventListener('change', e => {
  labelSel.attr('display', e.target.checked ? null : 'none');
});

window.addEventListener('resize', () => {
  const W = window.innerWidth - 360, H = window.innerHeight;
  svg.attr('viewBox', [0, 0, W, H]);
  sim.force('center', d3.forceCenter(W/2, H/2)).alpha(0.3).restart();
});
</script>
</body>
</html>
"""


def main() -> int:
    graph_path = config.GRAPH_DIR / "graph.json"
    comms_path = config.GRAPH_DIR / "communities.json"
    out_path = config.GRAPH_DIR / "graph.html"

    if not graph_path.exists():
        print(f"missing {graph_path}; run scripts/graphify_run.py first")
        return 1
    if not comms_path.exists():
        print(f"missing {comms_path}; run scripts/graphify_run.py first")
        return 1

    graph_json = graph_path.read_text(encoding="utf-8")
    comms_json = comms_path.read_text(encoding="utf-8")

    html = HTML_TEMPLATE.replace("__GRAPH_JSON__", graph_json).replace(
        "__COMMS_JSON__", comms_json
    )
    out_path.write_text(html, encoding="utf-8")

    nodes = json.loads(graph_json)["stats"]["node_count"]
    edges = json.loads(graph_json)["stats"]["edge_count"]
    print(f"wrote {out_path}  ({nodes} nodes, {edges} edges)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
