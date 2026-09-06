import { useMemo, useState } from "react";
import { ConceptShell } from "../components/ConceptShell";
import { Quiz } from "../components/Quiz";
import { markVisited } from "../progress";
import { QUIZZES } from "../quizzes";
import { useEffect } from "react";

/** Medical test vignette: disease prior, test sensitivity & FPR → posterior. */
export function BayesPage() {
  const [prior, setPrior] = useState(0.01);
  const [sens, setSens] = useState(0.9);
  const [fpr, setFpr] = useState(0.05);

  useEffect(() => markVisited("bayes"), []);

  const { posterior, jointPos, jointFalse } = useMemo(() => {
    const likePos = sens; // P(T+|D)
    const likeFalse = fpr; // P(T+|¬D)
    const jp = prior * likePos;
    const jf = (1 - prior) * likeFalse;
    const post = jp / (jp + jf || 1e-12);
    return { posterior: post, jointPos: jp, jointFalse: jf };
  }, [prior, sens, fpr]);

  const W = 420;
  const H = 160;

  return (
    <ConceptShell title="Bayes' Theorem">
      <p className="lede">
        Start with a <strong>prior</strong> belief. Multiply by how likely the evidence is under each
        hypothesis (<strong>likelihood</strong>). Normalize — that&apos;s the <strong>posterior</strong>.
      </p>
      <p className="formula mono">
        P(D|T+) = P(T+|D) P(D) / [P(T+|D)P(D) + P(T+|¬D)P(¬D)]
      </p>

      <section className="panel viz">
        <div className="sliders">
          <label>
            Prior P(disease) = {prior.toFixed(3)}
            <input
              type="range"
              min={0.001}
              max={0.5}
              step={0.001}
              value={prior}
              onChange={(e) => setPrior(Number(e.target.value))}
            />
          </label>
          <label>
            Sensitivity P(T+|D) = {sens.toFixed(2)}
            <input
              type="range"
              min={0.5}
              max={1}
              step={0.01}
              value={sens}
              onChange={(e) => setSens(Number(e.target.value))}
            />
          </label>
          <label>
            False positive rate P(T+|¬D) = {fpr.toFixed(2)}
            <input
              type="range"
              min={0.001}
              max={0.4}
              step={0.001}
              value={fpr}
              onChange={(e) => setFpr(Number(e.target.value))}
            />
          </label>
        </div>

        <svg viewBox={`0 0 ${W} ${H}`} className="bayes-svg" role="img" aria-label="Prior to posterior bars">
          <text x="10" y="24" className="svg-label">
            Prior
          </text>
          <rect x="90" y="8" width={prior * 280} height="22" fill="#c45c26" rx="4" />
          <text x="10" y="64" className="svg-label">
            × Likelihood mass
          </text>
          <rect x="90" y="48" width={Math.min(jointPos * 800, 280)} height="14" fill="#2a6f6f" rx="3" />
          <rect x="90" y="66" width={Math.min(jointFalse * 800, 280)} height="14" fill="#8a8a6a" rx="3" />
          <text x="10" y="118" className="svg-label">
            Posterior
          </text>
          <rect x="90" y="102" width={posterior * 280} height="28" fill="#1f7a4c" rx="4" />
          <text x="90" y="150" className="svg-label">
            P(D|T+) = {(posterior * 100).toFixed(1)}%
          </text>
        </svg>
        <p className="hint">
          Drag prior down (rarer disease) and watch the posterior shrink even with a good test — base
          rates bite.
        </p>
      </section>

      <Quiz conceptId="bayes" questions={QUIZZES.bayes} />
    </ConceptShell>
  );
}
