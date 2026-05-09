"""Read/write graph artifacts under brain/graph/."""

from __future__ import annotations

import json
from pathlib import Path

import networkx as nx

from medbrain import config
from medbrain.graph.builder import from_jsonable, to_jsonable
from medbrain.regen.atomic import atomic_write_text


def _path(name: str) -> Path:
    return config.GRAPH_DIR / name


def write_artifacts(g: nx.MultiDiGraph, communities: list[dict], audit_data: dict) -> None:
    config.GRAPH_DIR.mkdir(parents=True, exist_ok=True)
    atomic_write_text(_path("graph.json"), json.dumps(to_jsonable(g), indent=2, default=str))
    atomic_write_text(
        _path("communities.json"),
        json.dumps({"communities": communities, "count": len(communities)}, indent=2),
    )
    atomic_write_text(_path("audit.json"), json.dumps(audit_data, indent=2, default=str))
    atomic_write_text(_path("version.json"), json.dumps({"schema": "medbrain.graph/v1"}, indent=2))


def read_graph() -> nx.MultiDiGraph | None:
    p = _path("graph.json")
    if not p.exists():
        return None
    data = json.loads(p.read_text(encoding="utf-8"))
    return from_jsonable(data)


def read_communities() -> list[dict]:
    p = _path("communities.json")
    if not p.exists():
        return []
    return json.loads(p.read_text(encoding="utf-8")).get("communities", [])


def read_audit() -> dict:
    p = _path("audit.json")
    if not p.exists():
        return {}
    return json.loads(p.read_text(encoding="utf-8"))
