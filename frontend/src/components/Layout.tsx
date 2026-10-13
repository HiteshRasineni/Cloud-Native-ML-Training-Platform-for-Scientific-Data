import Link from "next/link";
import { useRouter } from "next/router";
import type { ReactNode } from "react";
import { cx } from "../lib/format";

const NAV = [
  { href: "/", label: "Experiments", icon: <IconFlask /> },
  { href: "/workers", label: "Workers", icon: <IconCube /> },
  { href: "/datasets", label: "Datasets", icon: <IconDatabase /> },
];

/** App shell: fixed sidebar + top bar wrapping every page. */
export function Layout({ children }: { children: ReactNode }) {
  const router = useRouter();

  return (
    <div className="flex min-h-screen">
      {/* Sidebar */}
      <aside className="fixed inset-y-0 left-0 z-30 hidden w-60 flex-col border-r border-white/5 bg-ink-900/80 backdrop-blur md:flex">
        <Link href="/" className="flex items-center gap-2.5 px-5 py-5">
          <span className="grid h-9 w-9 place-items-center rounded-lg bg-gradient-to-br from-accent to-accent-strong text-white shadow-glow">
            <IconLogo />
          </span>
          <span className="text-sm font-semibold leading-tight text-slate-100">
            Cloud&nbsp;ML
            <span className="block text-[11px] font-normal text-slate-500">
              Training Platform
            </span>
          </span>
        </Link>

        <nav className="flex flex-col gap-1 px-3">
          {NAV.map((item) => {
            const active = item.href === "/" ? router.pathname === "/" : router.pathname.startsWith(item.href);
            return (
              <Link
                key={item.href}
                href={item.href}
                className={cx(
                  "flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors",
                  active
                    ? "bg-accent/15 text-accent-soft"
                    : "text-slate-400 hover:bg-white/5 hover:text-slate-200"
                )}
              >
                <span className={cx("h-4 w-4", active ? "text-accent-soft" : "text-slate-500")}>{item.icon}</span>
                {item.label}
              </Link>
            );
          })}
        </nav>

        <div className="mt-auto px-3 pb-5">
          <div className="rounded-lg border border-white/5 bg-white/[0.02] p-3 text-[11px] leading-relaxed text-slate-500">
            <p className="mb-1 font-medium text-slate-400">Observability</p>
            <a
              className="link block"
              href={process.env.NEXT_PUBLIC_GRAFANA_URL || "http://localhost:3001"}
              target="_blank"
              rel="noreferrer"
            >
              Grafana dashboards ↗
            </a>
            <a
              className="link block"
              href={process.env.NEXT_PUBLIC_MLFLOW_URL || "http://localhost:5000"}
              target="_blank"
              rel="noreferrer"
            >
              MLflow tracking ↗
            </a>
          </div>
        </div>
      </aside>

      {/* Main column */}
      <div className="flex min-w-0 flex-1 flex-col md:pl-60">
        {/* Mobile top bar */}
        <header className="sticky top-0 z-20 flex items-center justify-between border-b border-white/5 bg-ink-950/80 px-4 py-3 backdrop-blur md:hidden">
          <Link href="/" className="flex items-center gap-2 text-sm font-semibold text-slate-100">
            <span className="grid h-7 w-7 place-items-center rounded-md bg-gradient-to-br from-accent to-accent-strong text-white">
              <IconLogo />
            </span>
            Cloud ML
          </Link>
          <nav className="flex gap-4 text-sm">
            <Link className={cx(router.pathname === "/" ? "text-accent-soft" : "text-slate-400")} href="/">
              Experiments
            </Link>
            <Link className={cx(router.pathname.startsWith("/workers") ? "text-accent-soft" : "text-slate-400")} href="/workers">
              Workers
            </Link>
            <Link className={cx(router.pathname.startsWith("/datasets") ? "text-accent-soft" : "text-slate-400")} href="/datasets">
              Datasets
            </Link>
          </nav>
        </header>

        <main className="mx-auto w-full max-w-6xl flex-1 px-4 py-6 md:px-8 md:py-8">{children}</main>
      </div>
    </div>
  );
}

function IconLogo() {
  return (
    <svg className="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <path strokeLinecap="round" strokeLinejoin="round" d="M4 7h16M4 12h10M4 17h7" />
      <circle cx="18" cy="16" r="3" />
    </svg>
  );
}

function IconFlask() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" className="h-full w-full">
      <path strokeLinecap="round" strokeLinejoin="round" d="M9 3h6M10 3v5l-5 9a2 2 0 0 0 1.8 3h10.4A2 2 0 0 0 19 17l-5-9V3" />
    </svg>
  );
}

function IconCube() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" className="h-full w-full">
      <path strokeLinecap="round" strokeLinejoin="round" d="M12 3l8 4.5v9L12 21l-8-4.5v-9L12 3z" />
      <path strokeLinecap="round" strokeLinejoin="round" d="M4 7.5l8 4.5 8-4.5M12 12v9" />
    </svg>
  );
}

function IconDatabase() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" className="h-full w-full">
      <ellipse cx="12" cy="6" rx="8" ry="3" />
      <path strokeLinecap="round" d="M4 6v6c0 1.66 3.58 3 8 3s8-1.34 8-3V6" />
      <path strokeLinecap="round" d="M4 12v6c0 1.66 3.58 3 8 3s8-1.34 8-3v-6" />
    </svg>
  );
}
