import { useMemo } from "react";
import { Link, useLocation } from "react-router-dom";
import { CONCEPT_META } from "../types";
import { loadProgress, progressFraction } from "../progress";

export function LandingPage() {
  const location = useLocation();
  const progress = useMemo(() => loadProgress(), [location.key]);

  const overall = useMemo(() => {
    const vals = CONCEPT_META.map((c) => progressFraction(progress, c.id));
    return vals.reduce((a, b) => a + b, 0) / vals.length;
  }, [progress]);

  return (
    <div className="landing">
      <header className="hero">
        <p className="eyebrow">Experiment 8</p>
        <h1>Data Science Visual Mastery</h1>
        <p className="lede">
          Interactive explainers for the math you actually use — priors, sampling distributions,
          descent paths, overfit curves, and threshold tradeoffs.
        </p>
        <div className="overall">
          <div className="overall-track" aria-hidden>
            <div className="overall-fill" style={{ width: `${overall * 100}%` }} />
          </div>
          <span>{Math.round(overall * 100)}% mastered on this device</span>
        </div>
      </header>

      <ul className="concept-grid">
        {CONCEPT_META.map((c) => {
          const frac = progressFraction(progress, c.id);
          return (
            <li key={c.id}>
              <Link to={`/${c.id}`} className="concept-card">
                <h2>{c.title}</h2>
                <p>{c.blurb}</p>
                <div className="mini-track">
                  <div className="mini-fill" style={{ width: `${frac * 100}%` }} />
                </div>
                <span className="pct">{Math.round(frac * 100)}%</span>
              </Link>
            </li>
          );
        })}
      </ul>
    </div>
  );
}
