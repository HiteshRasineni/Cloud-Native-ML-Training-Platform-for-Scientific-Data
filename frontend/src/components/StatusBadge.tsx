import { isPulsing, statusTone, toneClass } from "../lib/format";

/** Colored lifecycle-state badge with an optional pulse dot for active states. */
export function StatusBadge({ status, className = "" }: { status: string; className?: string }) {
  const tone = statusTone(status);
  return (
    <span
      className={`chip ${toneClass(status)} ${className}`}
      title={`status: ${status}`}
      data-status={status}
    >
      <span
        className={`inline-block h-1.5 w-1.5 rounded-full ${
          isPulsing(status) ? "animate-pulse-soft " : ""
        }${
          tone === "success"
            ? "bg-emerald-400"
            : tone === "danger"
            ? "bg-rose-400"
            : tone === "warn"
            ? "bg-amber-400"
            : tone === "info"
            ? "bg-sky-400"
            : tone === "accent"
            ? "bg-accent-soft"
            : "bg-slate-400"
        }`}
      />
      {status}
    </span>
  );
}

/** Small monospace badge for retryable / format / booleans. */
export function BoolBadge({ on, onLabel = "yes", offLabel = "no" }: { on: boolean; onLabel?: string; offLabel?: string }) {
  return (
    <span className={`chip border ${on ? "border-emerald-400/30 bg-emerald-400/10 text-emerald-300" : "border-white/10 bg-white/5 text-slate-400"}`}>
      {on ? onLabel : offLabel}
    </span>
  );
}
