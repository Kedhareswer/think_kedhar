"""FastAPI server exposing the 8-primitive retrieval menu.

Local-only by default (127.0.0.1). v1 has no auth; document this in the spec.
Run: `python scripts/api.py` (or `python -m medbrain.api.server`).
"""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field

from medbrain.api import menu

app = FastAPI(title="MedBrain Retrieval Menu", version=menu.API_VERSION)


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "version": menu.API_VERSION}


@app.get("/lookup")
def get_lookup(entity: str = Query(..., min_length=1)) -> dict:
    try:
        return menu.lookup(entity)
    except menu.MenuError as e:
        raise HTTPException(status_code=409, detail=str(e))


@app.get("/neighborhood")
def get_neighborhood(
    entity: str = Query(..., min_length=1),
    hops: int = Query(1, ge=1, le=3),
) -> dict:
    try:
        return menu.neighborhood(entity, hops=hops)
    except menu.MenuError as e:
        raise HTTPException(status_code=409, detail=str(e))


@app.get("/path")
def get_path(
    from_: str = Query(..., alias="from", min_length=1),
    to: str = Query(..., min_length=1),
    max_paths: int = Query(3, ge=1, le=10),
) -> dict:
    try:
        return menu.path(from_, to, max_paths=max_paths)
    except menu.MenuError as e:
        raise HTTPException(status_code=409, detail=str(e))


@app.get("/community")
def get_community(
    community_id: str | None = None,
    topic: str | None = None,
) -> dict:
    if not community_id and not topic:
        raise HTTPException(status_code=400, detail="provide community_id or topic")
    try:
        return menu.community(community_id=community_id, topic=topic)
    except menu.MenuError as e:
        raise HTTPException(status_code=409, detail=str(e))


@app.get("/scoped")
def get_scoped(
    population_region: str | None = None,
    population_pregnancy: str | None = None,
    setting_endemic: str | None = None,
    setting_care_level: str | None = None,
    min_certainty: str | None = None,
    current_only: bool = True,
) -> dict:
    try:
        return menu.scoped(
            population_region=population_region,
            population_pregnancy=population_pregnancy,
            setting_endemic=setting_endemic,
            setting_care_level=setting_care_level,
            min_certainty=min_certainty,
            current_only=current_only,
        )
    except menu.MenuError as e:
        raise HTTPException(status_code=409, detail=str(e))


@app.get("/recent")
def get_recent(since: str = Query(..., min_length=4)) -> dict:
    try:
        return menu.recent(since)
    except menu.MenuError as e:
        raise HTTPException(status_code=409, detail=str(e))


@app.get("/gaps")
def get_gaps() -> dict:
    try:
        return menu.gaps()
    except menu.MenuError as e:
        raise HTTPException(status_code=409, detail=str(e))


class EvidencePackRequest(BaseModel):
    claim_ids: list[str] = Field(default_factory=list)


@app.post("/evidence_pack")
def post_evidence_pack(req: EvidencePackRequest) -> dict:
    return menu.evidence_pack(req.claim_ids)


def main() -> None:
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=7117, log_level="info")


if __name__ == "__main__":
    main()
