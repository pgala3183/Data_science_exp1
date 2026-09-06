import { useCallback, useEffect, useState } from "react";
import {
  Area,
  CartesianGrid,
  ComposedChart,
  Line,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { api } from "../api";
import { ConceptShell } from "../components/ConceptShell";
import { Quiz } from "../components/Quiz";
import { markVisited } from "../progress";
import { QUIZZES } from "../quizzes";

export function CltPage() {
  const [dist, setDist] = useState("exponential");
  const [n, setN] = useState(30);
  const [data, setData] = useState<Awaited<ReturnType<typeof api.clt>> | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => markVisited("clt"), []);

  const run = useCallback(() => {
    setError(null);
    api
      .clt({ dist, sample_size: n, n_samples: 2500 })
      .then(setData)
      .catch((e) => setError(e instanceof Error ? e.message : "Failed"));
  }, [dist, n]);

  useEffect(() => {
    run();
  }, [run]);

  const chart =
    data?.histogram.centers.map((c, i) => ({
      x: c,
      density: data.histogram.density[i],
    })) ?? [];

  const normal =
    data?.normal_curve.x.map((x, i) => ({
      x,
      normal: data.normal_curve.y[i],
    })) ?? [];

  // merge for ComposedChart — use separate series via nearest join
  const merged = chart.map((row) => {
    let best = normal[0];
    let bestD = Infinity;
    for (const p of normal) {
      const d = Math.abs(p.x - row.x);
      if (d < bestD) {
        bestD = d;
        best = p;
      }
    }
    return { ...row, normal: best?.normal ?? 0 };
  });

  return (
    <ConceptShell title="Central Limit Theorem">
      <p className="lede">
        Draw many samples of size <em>n</em>, plot the histogram of their <strong>means</strong>. Even
        from a skewed population, that sampling distribution approaches a normal with SE = σ/√n.
      </p>

      <section className="panel viz">
        <div className="sliders row">
          <label>
            Population
            <select value={dist} onChange={(e) => setDist(e.target.value)}>
              <option value="exponential">Exponential (skewed)</option>
              <option value="uniform">Uniform</option>
              <option value="bernoulli">Bernoulli(0.3)</option>
            </select>
          </label>
          <label>
            Sample size n = {n}
            <input
              type="range"
              min={2}
              max={120}
              value={n}
              onChange={(e) => setN(Number(e.target.value))}
            />
          </label>
          <button type="button" className="primary" onClick={run}>
            Resimulate
          </button>
        </div>
        {error && <p className="error">{error}</p>}
        {data && (
          <>
            <div className="metrics">
              <span>pop mean {data.population_mean.toFixed(3)}</span>
              <span>mean of means {data.sampling_mean.toFixed(3)}</span>
              <span>empirical SD {data.sampling_std.toFixed(3)}</span>
              <span>theory SE {data.theoretical_se.toFixed(3)}</span>
            </div>
            <div className="chart-box">
              <ResponsiveContainer width="100%" height={280}>
                <ComposedChart data={merged}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#d4c4a8" />
                  <XAxis dataKey="x" tick={{ fontSize: 11 }} />
                  <YAxis tick={{ fontSize: 11 }} />
                  <Tooltip />
                  <Area type="monotone" dataKey="density" fill="#e8a05c88" stroke="#c45c26" />
                  <Line type="monotone" dataKey="normal" stroke="#1f5c4a" dot={false} strokeWidth={2} />
                </ComposedChart>
              </ResponsiveContainer>
            </div>
            <p className="hint">Orange: simulated means. Green: Normal(μ, σ/√n). Increase n and watch it tighten.</p>
          </>
        )}
      </section>

      <Quiz conceptId="clt" questions={QUIZZES.clt} />
    </ConceptShell>
  );
}
