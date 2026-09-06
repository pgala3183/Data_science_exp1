import { useEffect, useState } from "react";
import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Scatter,
  ScatterChart,
  Tooltip,
  XAxis,
  YAxis,
  ZAxis,
} from "recharts";
import { api } from "../api";
import { ConceptShell } from "../components/ConceptShell";
import { Quiz } from "../components/Quiz";
import { markVisited } from "../progress";
import { QUIZZES } from "../quizzes";

export function BiasVariancePage() {
  const [degree, setDegree] = useState(3);
  const [data, setData] = useState<Awaited<ReturnType<typeof api.biasVariance>> | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => markVisited("bias-variance"), []);

  useEffect(() => {
    setError(null);
    api
      .biasVariance({ degree, n_train: 45 })
      .then(setData)
      .catch((e) => setError(e instanceof Error ? e.message : "Failed"));
  }, [degree]);

  const fitSeries =
    data?.fit.x.map((x, i) => ({
      x,
      fit: data.fit.y[i],
      truth: data.truth.y[i],
    })) ?? [];

  const pts =
    data?.train_points.x.map((x, i) => ({
      x,
      y: data.train_points.y[i],
    })) ?? [];

  const err =
    data?.error_curves.degrees.map((d, i) => ({
      degree: d,
      train: data.error_curves.train_mse[i],
      test: data.error_curves.test_mse[i],
    })) ?? [];

  return (
    <ConceptShell title="Bias–Variance Tradeoff">
      <p className="lede">
        Fit polynomials of degree <em>d</em> to noisy samples from a sine wave. Low <em>d</em> underfits
        (bias); high <em>d</em> memorizes noise (variance). Watch train vs test MSE.
      </p>

      <section className="panel viz">
        <label>
          Polynomial degree d = {degree}
          <input
            type="range"
            min={0}
            max={12}
            value={degree}
            onChange={(e) => setDegree(Number(e.target.value))}
          />
        </label>
        {error && <p className="error">{error}</p>}
        {data && (
          <>
            <div className="metrics">
              <span>train MSE {data.train_mse.toFixed(3)}</span>
              <span>test MSE {data.test_mse.toFixed(3)}</span>
            </div>
            <div className="chart-row">
              <div className="chart-box">
                <h3>Data &amp; fit</h3>
                <ResponsiveContainer width="100%" height={280}>
                  <LineChart data={fitSeries}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#d4c4a8" />
                    <XAxis dataKey="x" tick={{ fontSize: 10 }} />
                    <YAxis tick={{ fontSize: 10 }} />
                    <Tooltip />
                    <Legend />
                    <Line type="monotone" dataKey="truth" stroke="#1f5c4a" dot={false} name="truth" />
                    <Line
                      type="monotone"
                      dataKey="fit"
                      stroke="#c45c26"
                      dot={false}
                      name={`poly d=${degree}`}
                    />
                  </LineChart>
                </ResponsiveContainer>
                <ResponsiveContainer width="100%" height={160}>
                  <ScatterChart margin={{ top: 8, right: 8, bottom: 8, left: 8 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#d4c4a8" />
                    <XAxis type="number" dataKey="x" name="x" />
                    <YAxis type="number" dataKey="y" name="y" />
                    <ZAxis range={[50, 50]} />
                    <Tooltip cursor={{ strokeDasharray: "3 3" }} />
                    <Scatter data={pts} fill="#8a4b2a" name="train points" />
                  </ScatterChart>
                </ResponsiveContainer>
              </div>
              <div className="chart-box">
                <h3>Error vs degree</h3>
                <ResponsiveContainer width="100%" height={360}>
                  <LineChart data={err}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#d4c4a8" />
                    <XAxis dataKey="degree" />
                    <YAxis />
                    <Tooltip />
                    <Legend />
                    <Line type="monotone" dataKey="train" stroke="#2a6f6f" name="train MSE" />
                    <Line type="monotone" dataKey="test" stroke="#c45c26" name="test MSE" />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </div>
          </>
        )}
      </section>

      <Quiz conceptId="bias-variance" questions={QUIZZES["bias-variance"]} />
    </ConceptShell>
  );
}
