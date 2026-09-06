import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { fetchSkill, runSkill } from "../api";
import { ResultView } from "../components/ResultView";
import { loadProgress, markComplete } from "../progress";
import type { RunResult, Skill } from "../types";

export function SkillDetailPage() {
  const { id = "" } = useParams();
  const [skill, setSkill] = useState<Skill | null>(null);
  const [result, setResult] = useState<RunResult | null>(null);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [done, setDone] = useState(false);

  useEffect(() => {
    setResult(null);
    setError(null);
    setDone(loadProgress().has(id));
    fetchSkill(id)
      .then(setSkill)
      .catch((e) => setError(e instanceof Error ? e.message : "Not found"));
  }, [id]);

  async function onRun() {
    setRunning(true);
    setError(null);
    try {
      const out = await runSkill(id);
      setResult(out);
      markComplete(id);
      setDone(true);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Run failed");
    } finally {
      setRunning(false);
    }
  }

  if (!skill && !error) return <p className="muted">Loading…</p>;
  if (!skill) {
    return (
      <p className="error" role="alert">
        {error}
      </p>
    );
  }

  return (
    <article className="detail">
      <p>
        <Link to="/">← Catalog</Link>
      </p>
      <div className="badges">
        <span className="badge cat">{skill.category}</span>
        <span className="badge diff">{skill.difficulty}</span>
        <span className="badge">{skill.dataset}</span>
        {done && <span className="badge ok">Completed</span>}
      </div>
      <h1>{skill.name}</h1>
      <p className="lede">{skill.description}</p>

      <h2>Code sketch</h2>
      <pre className="code">
        <code>{skill.snippet}</code>
      </pre>

      <button type="button" className="btn primary" onClick={() => void onRun()} disabled={running}>
        {running ? "Running…" : "Run exercise"}
      </button>

      {error && (
        <p className="error" role="alert">
          {error}
        </p>
      )}
      {result && (
        <section className="panel" aria-live="polite">
          <h2>Result</h2>
          <ResultView result={result} />
        </section>
      )}
    </article>
  );
}
