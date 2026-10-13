import Link from "next/link";
import type { ReactNode } from "react";
import { cx } from "../lib/format";

/** Page title block with optional subtitle and right-aligned actions. */
export function PageHeader({
  title,
  subtitle,
  actions,
}: {
  title: ReactNode;
  subtitle?: ReactNode;
  actions?: ReactNode;
}) {
  return (
    <div className="mb-6 flex flex-wrap items-end justify-between gap-4">
      <div className="min-w-0">
        <h1 className="text-2xl font-semibold tracking-tight text-slate-100">{title}</h1>
        {subtitle && <p className="mt-1 text-sm text-slate-400">{subtitle}</p>}
      </div>
      {actions && <div className="flex items-center gap-2">{actions}</div>}
    </div>
  );
}

/** Small metric tile for dashboards / summary rows. */
export function StatCard({
  label,
  value,
  sub,
  tone = "neutral",
  icon,
}: {
  label: string;
  value: ReactNode;
  sub?: ReactNode;
  tone?: "neutral" | "success" | "danger" | "warn" | "accent" | "info";
  icon?: ReactNode;
}) {
  const valueTone: Record<string, string> = {
    neutral: "text-slate-100",
    success: "text-emerald-300",
    danger: "text-rose-300",
    warn: "text-amber-300",
    accent: "text-accent-soft",
    info: "text-sky-300",
  };
  return (
    <div className="card flex items-center gap-3 p-4">
      {icon && (
        <span
          className={cx(
            "grid h-10 w-10 shrink-0 place-items-center rounded-lg",
            tone === "success" && "bg-emerald-400/10 text-emerald-300",
            tone === "danger" && "bg-rose-400/10 text-rose-300",
            tone === "warn" && "bg-amber-400/10 text-amber-300",
            tone === "accent" && "bg-accent/10 text-accent-soft",
            tone === "info" && "bg-sky-400/10 text-sky-300",
            tone === "neutral" && "bg-white/5 text-slate-400"
          )}
        >
          {icon}
        </span>
      )}
      <div className="min-w-0">
        <p className="text-xs font-medium uppercase tracking-wide text-slate-500">{label}</p>
        <p className={cx("truncate text-xl font-semibold tabular-nums", valueTone[tone])}>{value}</p>
        {sub && <p className="truncate text-xs text-slate-500">{sub}</p>}
      </div>
    </div>
  );
}

/** Section with a heading + optional right-side control, wraps a card body. */
export function Section({
  title,
  hint,
  actions,
  children,
  bodyClassName = "",
}: {
  title: ReactNode;
  hint?: ReactNode;
  actions?: ReactNode;
  children: ReactNode;
  bodyClassName?: string;
}) {
  return (
    <section className="card overflow-hidden">
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-white/5 px-5 py-3">
        <div className="min-w-0">
          <h2 className="text-sm font-semibold text-slate-200">{title}</h2>
          {hint && <p className="text-xs text-slate-500">{hint}</p>}
        </div>
        {actions && <div className="flex items-center gap-2">{actions}</div>}
      </div>
      <div className={cx("p-5", bodyClassName)}>{children}</div>
    </section>
  );
}

/** Key/value grid for spec details. */
export function KeyVal({ items }: { items: Array<{ k: string; v: ReactNode }> }) {
  return (
    <dl className="grid grid-cols-2 gap-x-6 gap-y-3 sm:grid-cols-3">
      {items.map((it) => (
        <div key={it.k} className="min-w-0">
          <dt className="text-xs uppercase tracking-wide text-slate-500">{it.k}</dt>
          <dd className="truncate text-sm font-medium text-slate-200" title={typeof it.v === "string" ? it.v : undefined}>
            {it.v}
          </dd>
        </div>
      ))}
    </dl>
  );
}

/** Simple accessible tab bar. */
export function Tabs<T extends string>({
  tabs,
  active,
  onChange,
}: {
  tabs: Array<{ key: T; label: string; count?: number }>;
  active: T;
  onChange: (key: T) => void;
}) {
  return (
    <div className="flex flex-wrap gap-1 border-b border-white/10">
      {tabs.map((t) => {
        const on = t.key === active;
        return (
          <button
            key={t.key}
            type="button"
            onClick={() => onChange(t.key)}
            className={cx(
              "-mb-px flex items-center gap-1.5 border-b-2 px-3 py-2 text-sm font-medium transition-colors",
              on
                ? "border-accent text-accent-soft"
                : "border-transparent text-slate-400 hover:text-slate-200"
            )}
            aria-current={on ? "page" : undefined}
          >
            {t.label}
            {t.count != null && (
              <span
                className={cx(
                  "rounded-full px-1.5 py-0.5 text-[10px] tabular-nums",
                  on ? "bg-accent/20 text-accent-soft" : "bg-white/5 text-slate-400"
                )}
              >
                {t.count}
              </span>
            )}
          </button>
        );
      })}
    </div>
  );
}

/** Back link with a chevron. */
export function BackLink({ href, children }: { href: string; children: ReactNode }) {
  return (
    <Link href={href} className="mb-4 inline-flex items-center gap-1 text-sm text-slate-400 transition-colors hover:text-accent-soft">
      <svg className="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <path strokeLinecap="round" strokeLinejoin="round" d="M15 19l-7-7 7-7" />
      </svg>
      {children}
    </Link>
  );
}

/** Inline error / notice banner. */
export function Notice({ tone = "danger", children }: { tone?: "danger" | "warn" | "info"; children: ReactNode }) {
  const map = {
    danger: "border-rose-400/30 bg-rose-400/10 text-rose-300",
    warn: "border-amber-400/30 bg-amber-400/10 text-amber-300",
    info: "border-sky-400/30 bg-sky-400/10 text-sky-300",
  } as const;
  return <p className={cx("rounded-lg border px-3 py-2 text-sm", map[tone])}>{children}</p>;
}
