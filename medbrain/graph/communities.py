"""Community detection over the knowledge graph.

Greedy modularity over the undirected projection of the multigraph.
Returns each community as a list of node IDs plus a label derived from the
top-degree node in the community.
"""

from __future__ import annotations

import networkx as nx
from networkx.algorithms.community import greedy_modularity_communities


def detect(g: nx.MultiDiGraph) -> list[dict]:
    if g.number_of_nodes() == 0:
        return []

    # Project to simple undirected graph for modularity. Edge weight = parallel-edge count.
    h = nx.Graph()
    h.add_nodes_from(g.nodes(data=True))
    for u, v in g.edges():
        if h.has_edge(u, v):
            h[u][v]["weight"] += 1
        else:
            h.add_edge(u, v, weight=1)

    try:
        comms = list(greedy_modularity_communities(h, weight="weight"))
    except Exception:
        # Single-node or trivial-graph fallback.
        comms = [set(g.nodes())]

    out: list[dict] = []
    for i, c in enumerate(comms):
        members = sorted(c)
        if not members:
            continue
        # Label = highest-degree node (in original directed graph).
        top = max(members, key=lambda n: g.degree(n))
        out.append(
            {
                "community_id": f"c{i:03d}",
                "label": g.nodes[top].get("label", top),
                "size": len(members),
                "members": members,
            }
        )
    return out
