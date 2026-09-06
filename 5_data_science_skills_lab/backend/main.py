"""Data Science Skills Lab API."""

from __future__ import annotations

import sys
import traceback
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

BACKEND_DIR = Path(__file__).resolve().parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.config import PORT  # noqa: E402
from app.datasets import ensure_data  # noqa: E402
from app.registry import categories, get_skill, list_skills  # noqa: E402
from app.runners import run_skill  # noqa: E402


@asynccontextmanager
async def lifespan(_app: FastAPI):
    ensure_data()
    yield


app = FastAPI(
    title="Data Science Skills Lab",
    description="Catalog of runnable mini-exercises on classic datasets",
    version="1.0.0",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"ok": True, "port": PORT, "n_skills": len(list_skills())}


@app.get("/categories")
def get_categories():
    return {"categories": categories()}


@app.get("/skills")
def skills(
    category: str | None = None,
    dataset: str | None = None,
    q: str | None = Query(None, description="Search name/description"),
):
    return {"skills": list_skills(category=category, dataset=dataset, q=q)}


@app.get("/skills/{skill_id}")
def skill_detail(skill_id: str):
    skill = get_skill(skill_id)
    if not skill:
        raise HTTPException(404, "Skill not found")
    return skill


@app.post("/skills/{skill_id}/run")
def skill_run(skill_id: str):
    skill = get_skill(skill_id)
    if not skill:
        raise HTTPException(404, "Skill not found")
    try:
        result = run_skill(skill["script"])
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(
            500,
            detail={"error": str(exc), "trace": traceback.format_exc().splitlines()[-5:]},
        ) from exc
    return {"skill_id": skill_id, "dataset": skill["dataset"], "result": result}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=PORT, reload=True)
