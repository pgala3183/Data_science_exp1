import json
from pathlib import Path

from app.registry import get_skill, list_skills, load_skills
from app.runners import RUNNERS, run_skill


def test_registry_count_and_fields():
    skills = load_skills()
    assert len(skills) >= 20
    required = {"id", "name", "category", "difficulty", "dataset", "description", "snippet", "script"}
    for s in skills:
        assert required <= set(s.keys())


def test_every_skill_has_runner():
    for s in load_skills():
        assert s["script"] in RUNNERS, f"Missing runner for {s['id']}"


def test_filter_by_category():
    eda = list_skills(category="EDA")
    assert eda and all(s["category"] == "EDA" for s in eda)


def test_run_one_skill():
    skill = get_skill("eda-describe-iris")
    assert skill is not None
    out = run_skill(skill["script"])
    assert out["kind"] == "table"
    assert len(out["rows"]) > 0


def test_skills_json_valid():
    path = Path(__file__).resolve().parents[1] / "app" / "skills.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    ids = [s["id"] for s in data]
    assert len(ids) == len(set(ids))
