"use client";
import { useCallback, useEffect, useMemo, useState } from "react";
import { listWorkers } from "../api/client";
import { Worker } from "../types";
import { StatusBadge } from "../components/StatusBadge";
import { EmptyState, Loading, Spinner } from "../components/Feedback";
import { PageHeader, Section, StatCard } from "../components/ui";
import { ageSeconds, cx, formatDateTime, relativeTime, shortId } from "../lib/format";

function heartbeatTone(seconds: number | null): string {
  if (seconds == null) return "text-slate-500";
  if (seconds <= 15) return "text-emerald-300";
  if (seconds <= 30) return "text-amber-300";
  return "text-rose-300";
}

export default function WorkersPage() {
  const [workers, setWorkers] = useState<Worker[]>([]);
  const [loading, setLoading] = useState(true);
  const [status, setStatus] = useState<string>("all");

  const refresh = useCallback(async () => {
    try {
      setWorkers(await listWorkers());
    } catch {
      /* backend may still be starting */
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refresh();
    const timer = setInterval(refresh, 3000);
    return () => clearInterval(timer);
  }, [refresh]);

  const stats = useMemo(() => {
    const by = (s: string) => workers.filter((w) => w.status === s).length;
    const running = by("RUNNING");
    const stale = workers.filter((w) => {
      const age = ageSeconds(w.heartbeat_time);
      return w.status === "RUNNING" && age != null && age > 30;
    }).length;
    return { total: workers.length, running, completed: by("COMPLETED"), failed: by("FAILED"), stale };
  }, [workers]);

  const filtered = useMemo(
    () => (status === "all" ? workers : workers.filter((w) => w.status === status)),
    [workers, status]
  );

  const FILTERS: Array<{ key: string; label: string }> = [
    { key: "all", label: "All" },
    { key: "RUNNING", label: "Running" },
    { key: "COMPLETED", label: "Completed" },
    { key: "FAILED", label: "Failed" },
  ];

  return (
    <>
      <PageHeader
        title="Workers"
        subtitle="Live view of training workers across all jobs, with heartbeat freshness."
        actions={
          <button className="btn btn-ghost" onClick={refresh}>
            {loading && <Spinner />}
            Refresh
          </button>
        }
      />

      <div className="mb-6 grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-5">
        <StatCard label="Total workers" value={stats.total} tone="neutral" />
        <StatCard label="Running" value={stats.running} tone="info" sub="active heartbeats" />
        <StatCard label="Completed" value={stats.completed} tone="success" />
        <StatCard label="Failed" value={stats.failed} tone="danger" />
        <StatCard
          label="Stale heartbeats"
          value={stats.stale}
          tone={stats.stale > 0 ? "warn" : "success"}
          sub={stats.stale > 0 ? "> 30s — will be retried" : "all fresh"}
        />
      </div>

      <Section
        title="All workers"
        hint="Green heartbeat < 15s, amber < 30s, red > 30s (timeout)."
        actions={
          <div className="flex overflow-hidden rounded-lg border border-white/10">
            {FILTERS.map((f) => (
              <button
                key={f.key}
                onClick={() => setStatus(f.key)}
                className={cx(
                  "px-3 py-1.5 text-xs font-medium transition-colors",
                  status === f.key ? "bg-accent/20 text-accent-soft" : "text-slate-400 hover:bg-white/5"
                )}
              >
                {f.label}
              </button>
            ))}
          </div>
        }
      >
        {loading && workers.length === 0 ? (
          <Loading label="Loading workers" />
        ) : filtered.length === 0 ? (
          <EmptyState
            title="No workers"
            hint="Workers appear once the scheduler launches them for a queued experiment. Submit an experiment from the Experiments page."
          />
        ) : (
          <div className="table-wrap">
            <table className="w-full border-collapse">
              <thead>
                <tr>
                  <th className="th">Worker</th>
                  <th className="th">Status</th>
                  <th className="th">Job</th>
                  <th className="th">Hostname / container</th>
                  <th className="th">Heartbeat</th>
                  <th className="th">Started</th>
                </tr>
              </thead>
              <tbody>
                {filtered.map((w) => {
                  const age = ageSeconds(w.heartbeat_time);
                  return (
                    <tr key={w.worker_id} className="border-t border-white/5 transition-colors hover:bg-white/[0.03]">
                      <td className="td font-mono text-xs text-slate-300">{shortId(w.worker_id, 12)}</td>
                      <td className="td">
                        <StatusBadge status={w.status} />
                      </td>
                      <td className="td">
                        <span
                          className="cursor-default font-mono text-xs text-accent-soft"
                          title={`Job ID: ${w.job_id}`}
                        >
                          {shortId(w.job_id, 8)}
                        </span>
                      </td>
                      <td className="td text-slate-400">
                        {w.hostname ?? "—"}
                        <span className="text-slate-600"> / </span>
                        <span className="font-mono text-xs">{w.container_id ? shortId(w.container_id, 12) : "—"}</span>
                      </td>
                      <td className={cx("td", heartbeatTone(age))}>{age == null ? "—" : `${age}s ago`}</td>
                      <td className="td text-slate-500" title={formatDateTime(w.started_at)}>
                        {relativeTime(w.started_at)}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </Section>
    </>
  );
}

