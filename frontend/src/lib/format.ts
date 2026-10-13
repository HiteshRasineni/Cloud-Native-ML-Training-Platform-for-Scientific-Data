/** Formatting + presentation helpers shared across the UI. */
import type { Experiment } from "../types";

export function cx(...parts: Array<string | false | null | undefined>): string {
  return parts.filter(Boolean).join(" ");
}

export function shortId(id: string, chars = 8): string {
  if (!id) return "-";
  return id.length <= chars ? id : id.slice(0, chars);
}

export function shortUri(uri: string): string {
  return uri.replace(/^s3:\/\//, "");
}

export function relativeTime(iso: string | null | undefined): string {
  if (!iso) return "-";
  const then = new Date(iso).getTime();
  if (Number.isNaN(then)) return "-";
  const secs = Math.round((Date.now() - then) / 1000);
  if (secs < 5) return "just now";
  if (secs < 60) return `${secs}s ago`;
  const mins = Math.round(secs / 60);
  if (mins < 60) return `${mins}m ago`;
  const hours = Math.round(mins / 60);
  if (hours < 48) return `${hours}h ago`;
  const days = Math.round(hours / 24);
  return `${days}d ago`;
}

/** Seconds since a heartbeat/start timestamp (for freshness colouring). */
export function ageSeconds(iso: string | null | undefined): number | null {
  if (!iso) return null;
  const then = new Date(iso).getTime();
  if (Number.isNaN(then)) return null;
  return Math.round((Date.now() - then) / 1000);
}

export function formatBytes(n: number | null | undefined): string {
  if (n == null || Number.isNaN(n)) return "-";
  const units = ["B", "KB", "MB", "GB", "TB"];
  let v = n;
  let i = 0;
  while (v >= 1024 && i < units.length - 1) {
    v /= 1024;
    i += 1;
  }
  return `${v >= 10 || i === 0 ? Math.round(v) : v.toFixed(1)} ${units[i]}`;
}

export function formatDateTime(iso: string | null | undefined): string {
  if (!iso) return "-";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return "-";
  return d.toLocaleString(undefined, {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });
}

export type StatusTone = "neutral" | "info" | "warn" | "danger" | "success" | "accent";

const STATUS_TONE: Record<string, StatusTone> = {
  CREATED: "neutral",
  VALIDATING: "info",
  VALIDATED: "info",
  QUEUED: "info",
  SCHEDULING: "accent",
  RUNNING: "success",
  CHECKPOINTING: "accent",
  RETRYING: "warn",
  COMPLETED: "success",
  FAILED: "danger",
};

const TONE_CLASS: Record<StatusTone, string> = {
  neutral: "border-white/10 bg-white/5 text-slate-300",
  info: "border-sky-400/30 bg-sky-400/10 text-sky-300",
  accent: "border-accent/30 bg-accent/10 text-accent-soft",
  warn: "border-amber-400/30 bg-amber-400/10 text-amber-300",
  danger: "border-rose-400/30 bg-rose-400/10 text-rose-300",
  success: "border-emerald-400/30 bg-emerald-400/10 text-emerald-300",
};

export function statusTone(status: string): StatusTone {
  return STATUS_TONE[status] ?? "neutral";
}

export function toneClass(status: string): string {
  return TONE_CLASS[statusTone(status)];
}

/** Lifecycle states considered "active" (still moving toward a terminal state). */
const ACTIVE = new Set(["CREATED", "VALIDATING", "VALIDATED", "QUEUED", "SCHEDULING", "RUNNING", "CHECKPOINTING", "RETRYING"]);

export function isActive(status: string): boolean {
  return ACTIVE.has(status);
}

/** True when the status should get a subtle pulse indicator. */
export function isPulsing(status: string): boolean {
  return status === "RUNNING" || status === "SCHEDULING" || status === "RETRYING" || status === "CHECKPOINTING";
}

export interface ExperimentStats {
  total: number;
  active: number;
  completed: number;
  failed: number;
  workers: number;
  activeWorkers: number;
}

export function computeStats(experiments: Experiment[]): ExperimentStats {
  let active = 0;
  let completed = 0;
  let failed = 0;
  let workers = 0;
  let activeWorkers = 0;
  for (const e of experiments) {
    if (e.status === "COMPLETED") completed += 1;
    else if (e.status === "FAILED") failed += 1;
    else if (isActive(e.status)) active += 1;
    for (const w of e.workers ?? []) {
      workers += 1;
      if (w.status === "RUNNING") activeWorkers += 1;
    }
  }
  return { total: experiments.length, active, completed, failed, workers, activeWorkers };
}
