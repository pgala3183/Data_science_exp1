import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { fetchCategories, fetchSkills } from "../api";
import { clearProgress, loadProgress } from "../progress";
import type { Skill } from "../types";
import { SkillCard } from "./SkillCard";

export function CatalogPage() {
  const [skills, setSkills] = useState<Skill[]>([]);
  const [categories, setCategories] = useState<string[]>([]);
  const [category, setCategory] = useState("");
  const [dataset, setDataset] = useState("");
  const [q, setQ] = useState("");
  const [progress, setProgress] = useState<Set<string>>(loadProgress());
  const [error, setError] = useState<string | null>(null);

  const datasets = useMemo(
    () => [...new Set(skills.map((s) => s.dataset))].sort(),
    [skills],
  );

  useEffect(() => {
    fetchCategories().then(setCategories).catch(() => setCategories([]));
  }, []);

  useEffect(() => {
    setError(null);
    fetchSkills({
      category: category || undefined,
      dataset: dataset || undefined,
      q: q || undefined,
    })
      .then(setSkills)
      .catch((e) => setError(e instanceof Error ? e.message : "Load failed"));
  }, [category, dataset, q]);

  const doneCount = [...progress].filter((id) => skills.some((s) => s.id === id)).length;

  return (
    <div>
      <header className="hero">
        <p className="eyebrow">Experiment 5</p>
        <h1>Data Science Skills Lab</h1>
        <p className="lede">
          A personal reference library of core skills — each with a small runnable exercise on a
          classic benchmark dataset.
        </p>
        <div className="progress-bar" aria-label="Progress">
          <div
            className="fill"
            style={{ width: `${skills.length ? (progress.size / Math.max(skills.length, 1)) * 100 : 0}%` }}
          />
        </div>
        <p className="meta">
          {progress.size} skills completed (saved locally)
          {category || dataset || q ? ` · showing ${doneCount} done in filter` : ""} ·{" "}
          <button
            type="button"
            className="linkish"
            onClick={() => {
              clearProgress();
              setProgress(new Set());
            }}
          >
            Reset progress
          </button>
        </p>
      </header>

      <div className="filters">
        <label>
          Search
          <input
            type="search"
            value={q}
            onChange={(e) => setQ(e.target.value)}
            placeholder="e.g. permutation, ROC, one-hot"
          />
        </label>
        <label>
          Category
          <select value={category} onChange={(e) => setCategory(e.target.value)}>
            <option value="">All</option>
            {categories.map((c) => (
              <option key={c} value={c}>
                {c}
              </option>
            ))}
          </select>
        </label>
        <label>
          Dataset
          <select value={dataset} onChange={(e) => setDataset(e.target.value)}>
            <option value="">All</option>
            {datasets.map((d) => (
              <option key={d} value={d}>
                {d}
              </option>
            ))}
          </select>
        </label>
      </div>

      {error && (
        <p className="error" role="alert">
          {error}
        </p>
      )}

      <div className="grid">
        {skills.map((s) => (
          <SkillCard key={s.id} skill={s} done={progress.has(s.id)} />
        ))}
      </div>
      {!skills.length && !error && <p className="muted">No skills match.</p>}
      <p className="muted foot">
        Tip: open a skill and hit <strong>Run</strong> to mark it complete.{" "}
        <Link to="/skills/eda-describe-iris">Try descriptive statistics →</Link>
      </p>
    </div>
  );
}
