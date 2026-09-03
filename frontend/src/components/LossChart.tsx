"use client";
import { MetricPoint } from "../types";

export function LossChart({ points }: { points: MetricPoint[] }) {
  if (points.length < 2) return <p>Not enough metric points yet (need at least 2 epochs).</p>;
  const w = 640, h = 240, pad = 30;
  const xs = points.map((p) => p.step);
  const ys = points.map((p) => p.value);
  const xMin = Math.min(...xs), xMax = Math.max(...xs);
  const yMin = Math.min(...ys), yMax = Math.max(...ys);
  const sx = (s: number) => pad + ((s - xMin) / Math.max(xMax - xMin, 1)) * (w - 2 * pad);
  const sy = (v: number) => h - pad - ((v - yMin) / Math.max(yMax - yMin, 1e-9)) * (h - 2 * pad);
  const path = points.map((p, i) => `${i === 0 ? "M" : "L"} ${sx(p.step).toFixed(1)} ${sy(p.value).toFixed(1)}`).join(" ");
  return (
    <svg width={w} height={h} style={{ border: "1px solid #ccc" }}>
      <path d={path} fill="none" stroke="steelblue" strokeWidth={2} />
      <text x={pad} y={16} fontSize={12}>{`loss`}</text>
      <text x={w - pad} y={h - 6} fontSize={12} textAnchor="end">{`epoch ${xMax}`}</text>
      <text x={pad} y={h - 6} fontSize={12}>{yMin.toFixed(4)}</text>
      <text x={pad} y={pad - 8} fontSize={12}>{yMax.toFixed(4)}</text>
    </svg>
  );
}
