import { useEffect, useRef } from "react";
import type { GraphData } from "../types";

type SimNode = {
  id: string;
  label: string;
  count: number;
  x: number;
  y: number;
  vx: number;
  vy: number;
};

type SimEdge = {
  source: string;
  target: string;
  lift: number;
  confidence: number;
};

type Props = { data: GraphData };

export function ForceGraph({ data }: Props) {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const width = canvas.clientWidth;
    const height = canvas.clientHeight;
    canvas.width = width * devicePixelRatio;
    canvas.height = height * devicePixelRatio;
    ctx.setTransform(devicePixelRatio, 0, 0, devicePixelRatio, 0, 0);

    const nodes: SimNode[] = data.nodes.map((n, i) => {
      const angle = (2 * Math.PI * i) / Math.max(data.nodes.length, 1);
      return {
        ...n,
        x: width / 2 + Math.cos(angle) * 120,
        y: height / 2 + Math.sin(angle) * 120,
        vx: 0,
        vy: 0,
      };
    });
    const nodeMap = new Map(nodes.map((n) => [n.id, n]));
    const edges: SimEdge[] = data.edges.map((e) => ({
      source: e.source,
      target: e.target,
      lift: e.lift,
      confidence: e.confidence,
    }));

    const maxLift = Math.max(...edges.map((e) => e.lift), 1);
    let frame = 0;
    let raf = 0;
    let running = true;

    const tick = () => {
      if (!running) return;
      frame += 1;
      // Forces
      for (let i = 0; i < nodes.length; i++) {
        for (let j = i + 1; j < nodes.length; j++) {
          const a = nodes[i];
          const b = nodes[j];
          let dx = a.x - b.x;
          let dy = a.y - b.y;
          let dist = Math.hypot(dx, dy) || 0.01;
          const rep = 2200 / (dist * dist);
          dx /= dist;
          dy /= dist;
          a.vx += dx * rep;
          a.vy += dy * rep;
          b.vx -= dx * rep;
          b.vy -= dy * rep;
        }
      }
      for (const e of edges) {
        const a = nodeMap.get(e.source);
        const b = nodeMap.get(e.target);
        if (!a || !b) continue;
        const dx = b.x - a.x;
        const dy = b.y - a.y;
        const dist = Math.hypot(dx, dy) || 0.01;
        const desired = 90;
        const force = (dist - desired) * 0.02 * (0.5 + e.lift / maxLift);
        const fx = (dx / dist) * force;
        const fy = (dy / dist) * force;
        a.vx += fx;
        a.vy += fy;
        b.vx -= fx;
        b.vy -= fy;
      }
      // Center gravity
      for (const n of nodes) {
        n.vx += (width / 2 - n.x) * 0.005;
        n.vy += (height / 2 - n.y) * 0.005;
        n.vx *= 0.85;
        n.vy *= 0.85;
        n.x += n.vx;
        n.y += n.vy;
        n.x = Math.max(24, Math.min(width - 24, n.x));
        n.y = Math.max(24, Math.min(height - 24, n.y));
      }

      ctx.clearRect(0, 0, width, height);
      for (const e of edges) {
        const a = nodeMap.get(e.source);
        const b = nodeMap.get(e.target);
        if (!a || !b) continue;
        const w = 0.6 + (e.lift / maxLift) * 4;
        ctx.beginPath();
        ctx.strokeStyle = `rgba(14, 116, 144, ${0.25 + (e.confidence || 0) * 0.5})`;
        ctx.lineWidth = w;
        ctx.moveTo(a.x, a.y);
        ctx.lineTo(b.x, b.y);
        ctx.stroke();
      }
      for (const n of nodes) {
        const r = 8 + Math.min(10, Math.sqrt(n.count) / 3);
        ctx.beginPath();
        ctx.fillStyle = "#0e7490";
        ctx.arc(n.x, n.y, r, 0, Math.PI * 2);
        ctx.fill();
        ctx.fillStyle = "#0f172a";
        ctx.font = "11px Manrope, sans-serif";
        ctx.fillText(n.label.replaceAll("_", " "), n.x + r + 3, n.y + 3);
      }

      if (frame < 240) raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);

    return () => {
      running = false;
      cancelAnimationFrame(raf);
    };
  }, [data]);

  return (
    <section className="panel" aria-labelledby="graph-title">
      <h2 id="graph-title">Co-purchase network</h2>
      <p className="muted">Edge thickness ∝ lift · opacity ∝ confidence. Drag not required — force layout settles automatically.</p>
      <canvas ref={canvasRef} className="graph-canvas" role="img" aria-label="Item association force graph" />
    </section>
  );
}
