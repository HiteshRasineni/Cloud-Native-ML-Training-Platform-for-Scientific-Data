import { StatusBadge } from "./StatusBadge";
import { EmptyState } from "./Feedback";
import { cx, formatDateTime, ageSeconds } from "../lib/format";
import type { Failure, Transition, Worker } from "../types";

/** Vertical state-transition timeline (from -> to, with message + time). */
export function Timeline({ transitions }: { transitions: Transition[] }) {
  if (transitions.length === 0) {
    return <EmptyState title="No transitions recorded" hint="State changes appear here as the experiment moves through its lifecycle." />;
  }
  const ordered = [...transitions].sort(
    (a, b) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime()
  );
  return (
    <ol className="relative space-y-4 border-l border-white/10 pl-5">
      {ordered.map((t) => (
        <li key={t.id} className="relative">
          <span className="absolute -left-[27px] top-1 h-3 w-3 rounded-full border-2 border-ink-900 bg-accent-soft" />
          <div className="flex flex-wrap items-center gap-2">
            <StatusBadge status={t.to_status} />
            {t.from_status && (
              <span className="text-xs text-slate-500">
                from <span className="font-mono text-slate-400">{t.from_status}</span>
              </span>
            )}
            <span className="ml-auto text-xs text-slate-500" title={formatDateTime(t.created_at)}>
              {formatDateTime(t.created_at)}
            </span>
          </div>
          {t.message && <p className="mt-1 text-sm text-slate-400">{t.message}</p>}
        </li>
      ))}
    </ol>
  );
}

/** Freshness colour for a heartbeat timestamp. */
function heartbeatTone(seconds: number | null): string {
  if (seconds == null) return "text-slate-500";
  if (seconds <= 15) return "text-emerald-300";
  if (seconds <= 30) return "text-amber-300";
  return "text-rose-300";
}

/** Worker rows: id, status, container, heartbeat freshness. */
export function WorkerTable({ workers }: { workers: Worker[] }) {
  if (workers.length === 0) {
    return <EmptyState title="No workers yet" hint="Workers appear once the scheduler launches them for this job." />;
  }
  return (
    <div className="table-wrap">
      <table className="w-full border-collapse">
        <thead>
          <tr>
            <th className="th">Worker</th>
            <th className="th">Status</th>
            <th className="th">Hostname / container</th>
            <th className="th">Heartbeat</th>
          </tr>
        </thead>
        <tbody>
          {workers.map((w) => {
            const age = ageSeconds(w.heartbeat_time);
            return (
              <tr key={w.worker_id} className="border-t border-white/5 transition-colors hover:bg-white/[0.03]">
                <td className="td font-mono text-xs text-slate-300">{w.worker_id.slice(0, 12)}</td>
                <td className="td"><StatusBadge status={w.status} /></td>
                <td className="td text-slate-400">
                  {w.hostname ?? "-"}
                  <span className="text-slate-600"> / </span>
                  <span className="font-mono text-xs">{w.container_id ? w.container_id.slice(0, 12) : "-"}</span>
                </td>
                <td className={cx("td", heartbeatTone(age))}>
                  {age == null ? "-" : `${age}s ago`}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

/** Failure rows: type, message, retryable, timestamp. */
export function FailureList({ failures }: { failures: Failure[] }) {
  if (failures.length === 0) {
    return <EmptyState title="No failures recorded" hint="Classified failures (crashes, timeouts, storage errors) appear here." />;
  }
  return (
    <ul className="space-y-2">
      {failures.map((f) => (
        <li
          key={f.failure_id}
          className="flex flex-col gap-1 rounded-lg border border-rose-400/20 bg-rose-400/5 px-4 py-3"
        >
          <div className="flex items-center gap-2">
            <span className="chip border border-rose-400/30 bg-rose-400/10 font-mono text-rose-300">{f.error_type}</span>
            <span className={cx("chip border", f.retryable ? "border-amber-400/30 bg-amber-400/10 text-amber-300" : "border-white/10 bg-white/5 text-slate-400")}>
              {f.retryable ? "retryable" : "terminal"}
            </span>
            <span className="ml-auto text-xs text-slate-500">{formatDateTime(f.timestamp)}</span>
          </div>
          {f.error_message && <p className="text-sm text-slate-400">{f.error_message}</p>}
        </li>
      ))}
    </ul>
  );
}
