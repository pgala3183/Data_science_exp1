import { useEffect, useMemo, useRef, useState } from "react";
import { api } from "../api";
import { ConceptShell } from "../components/ConceptShell";
import { Quiz } from "../components/Quiz";
import { markVisited } from "../progress";
import { QUIZZES } from "../quizzes";

type Point = { w1: number; w2: number; loss: number };

export function GradientDescentPage() {
  const [lr, setLr] = useState(0.08);
  const [surface, setSurface] = useState<Awaited<ReturnType<typeof api.lossSurface>> | null>(null);
  const [path, setPath] = useState<Point[]>([]);
  const [frame, setFrame] = useState(0);
  const [playing, setPlaying] = useState(true);
  const raf = useRef<number | null>(null);

  useEffect(() => markVisited("gradient-descent"), []);

  useEffect(() => {
    api.lossSurface().then(setSurface).catch(() => setSurface(null));
  }, []);

  useEffect(() => {
    api
      .gd({ w1: -1.8, w2: 1.6, lr, steps: 100 })
      .then((r) => {
        setPath(r.path);
        setFrame(0);
        setPlaying(true);
      })
      .catch(() => setPath([]));
  }, [lr]);

  useEffect(() => {
    if (!playing || path.length < 2) return;
    let last = performance.now();
    const tick = (t: number) => {
      if (t - last > 40) {
        last = t;
        setFrame((f) => {
          if (f >= path.length - 1) {
            setPlaying(false);
            return f;
          }
          return f + 1;
        });
      }
      raf.current = requestAnimationFrame(tick);
    };
    raf.current = requestAnimationFrame(tick);
    return () => {
      if (raf.current) cancelAnimationFrame(raf.current);
    };
  }, [playing, path]);

  const contour = useMemo(() => {
    if (!surface) return [] as { x: number; y: number; v: number }[];
    const pts: { x: number; y: number; v: number }[] = [];
    const step = 2;
    for (let i = 0; i < surface.w2.length; i += step) {
      for (let j = 0; j < surface.w1.length; j += step) {
        pts.push({ x: surface.w1[j], y: surface.w2[i], v: surface.z[i][j] });
      }
    }
    return pts;
  }, [surface]);

  const W = 480;
  const H = 360;
  const xMin = -2.5,
    xMax = 3.5,
    yMin = -3,
    yMax = 2.5;
  const sx = (w1: number) => ((w1 - xMin) / (xMax - xMin)) * (W - 40) + 20;
  const sy = (w2: number) => H - 20 - ((w2 - yMin) / (yMax - yMin)) * (H - 40);

  const vmax = contour.reduce((m, p) => Math.max(m, p.v), 1);
  const cur = path[Math.min(frame, path.length - 1)];

  return (
    <ConceptShell title="Gradient Descent">
      <p className="lede">
        Loss is a landscape. The gradient points uphill — we step the opposite way. Change the{" "}
        <strong>learning rate</strong> and watch the ball race, crawl, or overshoot.
      </p>

      <section className="panel viz">
        <div className="sliders row">
          <label>
            Learning rate η = {lr.toFixed(3)}
            <input
              type="range"
              min={0.01}
              max={0.45}
              step={0.005}
              value={lr}
              onChange={(e) => setLr(Number(e.target.value))}
            />
          </label>
          <button type="button" className="primary" onClick={() => { setFrame(0); setPlaying(true); }}>
            Replay
          </button>
          <button type="button" onClick={() => setPlaying((p) => !p)}>
            {playing ? "Pause" : "Play"}
          </button>
        </div>

        <svg viewBox={`0 0 ${W} ${H}`} className="gd-svg" role="img" aria-label="Loss surface descent">
          {contour.map((p, i) => {
            const t = p.v / vmax;
            const col = `rgb(${40 + t * 160},${90 - t * 40},${70 + (1 - t) * 80})`;
            return <circle key={i} cx={sx(p.x)} cy={sy(p.y)} r={4.2} fill={col} opacity={0.85} />;
          })}
          {path.length > 1 && (
            <polyline
              fill="none"
              stroke="#f4e6c3"
              strokeWidth={2}
              points={path
                .slice(0, frame + 1)
                .map((p) => `${sx(p.w1)},${sy(p.w2)}`)
                .join(" ")}
            />
          )}
          {surface && (
            <circle
              cx={sx(surface.minimum.w1)}
              cy={sy(surface.minimum.w2)}
              r={6}
              fill="none"
              stroke="#f2d27a"
              strokeWidth={2}
            />
          )}
          {cur && (
            <circle cx={sx(cur.w1)} cy={sy(cur.w2)} r={8} fill="#ff6b3d" stroke="#fff" strokeWidth={2}>
              <animate attributeName="r" values="7;9;7" dur="0.6s" repeatCount="indefinite" />
            </circle>
          )}
        </svg>
        {cur && (
          <div className="metrics">
            <span>
              w=({cur.w1.toFixed(2)}, {cur.w2.toFixed(2)})
            </span>
            <span>loss {cur.loss.toFixed(3)}</span>
            <span>
              step {frame}/{Math.max(path.length - 1, 1)}
            </span>
          </div>
        )}
        <p className="hint">Try η ≈ 0.35 — the path may oscillate. Tiny η crawls. Gold ring ≈ basin.</p>
      </section>

      <Quiz conceptId="gradient-descent" questions={QUIZZES["gradient-descent"]} />
    </ConceptShell>
  );
}
