import { useMemo, useState } from "react";

export interface SeriesPoint { step: number; value: number }
export interface Series { name: string; color: string; points: SeriesPoint[] }

const PAD = { top: 16, right: 16, bottom: 34, left: 56 };
const W = 760;

/** Dependency-free SVG line chart with gridlines, gradient area and a hover
 * crosshair + readout. Responsive via viewBox. */
export function LossChart({ series, yLabel = "loss", xLabel = "epoch", height = 280, emptyHint = "No metrics yet." }: {
  series: Series[]; yLabel?: string; xLabel?: string; height?: number; emptyHint?: string;
}) {
  const [hover, setHover] = useState<number | null>(null);
  const plotW = W - PAD.left - PAD.right;
  const plotH = height - PAD.top - PAD.bottom;

  const model = useMemo(() => {
    const live = series.filter((s) => s.points.length > 0);
    if (live.length === 0) return null;
    const xs = live.flatMap((s) => s.points.map((p) => p.step));
    const ys = live.flatMap((s) => s.points.map((p) => p.value));
    const xMin = Math.min(...xs), xMax = Math.max(...xs);
    let yMin = Math.min(...ys), yMax = Math.max(...ys);
    if (yMin === yMax) { const p = Math.abs(yMin) * 0.05 || 0.5; yMin -= p; yMax += p; }
    else { const p = (yMax - yMin) * 0.12; yMin -= p; yMax += p; }
    const sx = (x: number) => PAD.left + ((x - xMin) / (xMax - xMin || 1)) * plotW;
    const sy = (y: number) => PAD.top + plotH - ((y - yMin) / (yMax - yMin)) * plotH;
    const yTicks = Array.from({ length: 6 }, (_, i) => yMin + ((yMax - yMin) * i) / 5);
    const xTicks = uniqueTicks(xMin, xMax, 6);
    return { xMin, xMax, yMin, sx, sy, yTicks, xTicks, live };
  }, [series, plotH, plotW]);

  if (!model) {
    return (
      <div className="flex h-40 items-center justify-center rounded-xl border border-dashed border-white/10 bg-white/[0.02] text-sm text-slate-500">
        {emptyHint}
      </div>
    );
  }
  const { sx, sy, yTicks, xTicks } = model;
  const inRange = hover != null && hover >= model.xMin && hover <= model.xMax;

  return (
    <div className="relative">
      <svg
        viewBox={`0 0 ${W} ${height}`} className="w-full"
        onMouseLeave={() => setHover(null)}
        onMouseMove={(e) => {
          const rect = e.currentTarget.getBoundingClientRect();
          const px = ((e.clientX - rect.left) / rect.width) * W;
          setHover(Math.round(model.xMin + ((px - PAD.left) / plotW) * (model.xMax - model.xMin || 1)));
        }}
      >
        <defs>
          {model.live.map((s) => (
            <linearGradient key={s.name} id={`grad-${slug(s.name)}`} x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor={s.color} stopOpacity="0.28" />
              <stop offset="100%" stopColor={s.color} stopOpacity="0" />
            </linearGradient>
          ))}
        </defs>
        {yTicks.map((t) => (
          <g key={`y${t}`}>
            <line x1={PAD.left} x2={W - PAD.right} y1={sy(t)} y2={sy(t)} stroke="rgba(255,255,255,0.06)" />
            <text x={PAD.left - 8} y={sy(t)} textAnchor="end" dominantBaseline="middle" className="fill-slate-500 text-[10px]">{fmt(t)}</text>
          </g>
        ))}
        {xTicks.map((t) => (
          <text key={`x${t}`} x={sx(t)} y={height - PAD.bottom + 16} textAnchor="middle" className="fill-slate-500 text-[10px]">{t}</text>
        ))}
        <text x={PAD.left + plotW / 2} y={height - 4} textAnchor="middle" className="fill-slate-600 text-[10px] uppercase tracking-wide">{xLabel}</text>
        <text x={13} y={PAD.top + plotH / 2} textAnchor="middle" className="fill-slate-600 text-[10px] uppercase tracking-wide" transform={`rotate(-90 13 ${PAD.top + plotH / 2})`}>{yLabel}</text>
        {model.live.map((s) => {
          const sorted = [...s.points].sort((a, b) => a.step - b.step);
          const line = sorted.map((p, i) => `${i === 0 ? "M" : "L"}${sx(p.step).toFixed(1)},${sy(p.value).toFixed(1)}`).join(" ");
          const area = `${line} L${sx(sorted.at(-1)!.step).toFixed(1)},${sy(model.yMin)} L${sx(sorted[0].step).toFixed(1)},${sy(model.yMin)} Z`;
          const last = sorted.at(-1)!;
          return (
            <g key={s.name}>
              <path d={area} fill={`url(#grad-${slug(s.name)})`} />
              <path d={line} fill="none" stroke={s.color} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
              <circle cx={sx(last.step)} cy={sy(last.value)} r="3.5" fill={s.color} stroke="#0a0e17" strokeWidth="1.5" />
            </g>
          );
        })}
        {inRange && <line x1={sx(hover!)} x2={sx(hover!)} y1={PAD.top} y2={PAD.top + plotH} stroke="rgba(129,140,248,0.5)" strokeDasharray="3 3" />}
      </svg>
      <div className="mt-1 flex flex-wrap items-center justify-between gap-2 text-xs">
        <div className="flex flex-wrap items-center gap-4">
          {model.live.map((s) => {
            const last = [...s.points].sort((a, b) => a.step - b.step).at(-1);
            return (
              <span key={s.name} className="flex items-center gap-1.5 text-slate-400">
                <span className="inline-block h-2 w-2 rounded-full" style={{ background: s.color }} />
                {s.name}<span className="font-mono text-slate-200">{last ? fmt(last.value) : "-"}</span>
              </span>
            );
          })}
        </div>
        {inRange && (
          <span className="font-mono text-slate-500">
            {xLabel} {hover}: {model.live.map((s) => { const p = nearest(s.points, hover!); return p ? `${s.name}=${fmt(p.value)}` : null; }).filter(Boolean).join("  ")}
          </span>
        )}
      </div>
    </div>
  );
}


/** Tiny inline sparkline for KPI cards. */
export function Sparkline({ points, color = "#818cf8", width = 96, height = 28 }: { points: SeriesPoint[]; color?: string; width?: number; height?: number }) {
  if (points.length < 2) return <div className="h-7" />;
  const xs = points.map((p) => p.step);
  const ys = points.map((p) => p.value);
  const xMin = Math.min(...xs), xMax = Math.max(...xs);
  const yMin = Math.min(...ys), yMax = Math.max(...ys);
  const sx = (x: number) => ((x - xMin) / (xMax - xMin || 1)) * (width - 2) + 1;
  const sy = (y: number) => height - 2 - ((y - yMin) / (yMax - yMin || 1)) * (height - 4);
  const d = points.map((p, i) => `${i === 0 ? "M" : "L"}${sx(p.step).toFixed(1)},${sy(p.value).toFixed(1)}`).join(" ");
  const last = points.at(-1)!;
  return (
    <svg width={width} height={height}>
      <path d={d} fill="none" stroke={color} strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
      <circle cx={sx(last.step)} cy={sy(last.value)} r="2.4" fill={color} />
    </svg>
  );
}

function nearest(points: SeriesPoint[], x: number): SeriesPoint | null {
  let best: SeriesPoint | null = null;
  let bestD = Infinity;
  for (const p of points) {
    const d = Math.abs(p.step - x);
    if (d < bestD) { bestD = d; best = p; }
  }
  return best;
}

function uniqueTicks(min: number, max: number, count: number): number[] {
  if (min === max) return [min];
  const raw = (max - min) / (count - 1);
  const mag = Math.pow(10, Math.floor(Math.log10(raw)));
  const norm = raw / mag;
  const step = (norm >= 5 ? 5 : norm >= 2 ? 2 : 1) * mag;
  const start = Math.ceil(min / step) * step;
  const ticks: number[] = [];
  for (let v = start; v <= max + 1e-9; v += step) ticks.push(Math.round(v * 1000) / 1000);
  return ticks;
}

function fmt(n: number): string {
  if (!Number.isFinite(n)) return "-";
  const abs = Math.abs(n);
  if (abs >= 1000) return (n / 1000).toFixed(abs >= 10000 ? 0 : 1) + "k";
  if (abs >= 1) return n.toFixed(abs >= 100 ? 0 : 1);
  return n.toPrecision(3);
}

function slug(s: string): string {
  return s.replace(/[^a-z0-9]+/gi, "-").toLowerCase();
}
