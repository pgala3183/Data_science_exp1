"""Skills registry loaded from skills.json."""

from __future__ import annotations

import json
from functools import lru_cache

from app.config import SKILLS_PATH


@lru_cache(maxsize=1)
def load_skills() -> list[dict]:
    return json.loads(SKILLS_PATH.read_text(encoding="utf-8"))


def list_skills(
    *,
    category: str | None = None,
    dataset: str | None = None,
    q: str | None = None,
) -> list[dict]:
    skills = load_skills()
    if category:
        skills = [s for s in skills if s["category"].lower() == category.lower()]
    if dataset:
        skills = [s for s in skills if s["dataset"].lower() == dataset.lower()]
    if q:
        ql = q.lower()
        skills = [
            s
            for s in skills
            if ql in s["name"].lower()
            or ql in s["description"].lower()
            or ql in s["category"].lower()
        ]
    return skills


def get_skill(skill_id: str) -> dict | None:
    for s in load_skills():
        if s["id"] == skill_id:
            return s
    return None


def categories() -> list[str]:
    return sorted({s["category"] for s in load_skills()})
