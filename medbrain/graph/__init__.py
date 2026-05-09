"""Knowledge graph: SQL claims -> networkx graph -> menu queries.

Note on graphify: spec §7.3 named graphify (github.com/safishamsi/graphify).
We use a SQL-direct networkx builder instead because:
  1. SQL claims hold structured qualifiers/grades/supersession that prose-extraction
     would lose.
  2. The user's `/graphify` skill is a Claude Code skill (not a Python lib), unsuitable
     for in-process graph construction.
  3. Internal builder = zero external runtime dep + deterministic + qualifier-preserving.
The output shape (graph.json, communities.json, audit.json) is graphify-compatible
so the menu primitives are stable across builder swaps.
"""
