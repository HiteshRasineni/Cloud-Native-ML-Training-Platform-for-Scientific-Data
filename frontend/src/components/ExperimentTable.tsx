import type React from "react";
import Link from "next/link";
import { StatusBadge } from "./StatusBadge";
import { EmptyState } from "./Feedback";
import { cx, formatDateTime, isPulsing, relativeTime, shortId } from "../lib/format";
import type { Experiment } from "../types";

type SortKey = "created" | "name" | "status";

/** Rich experiments table with search + status filter + sort. */
export function ExperimentTable({
  experiments,
  onOpen,
}: {
  experiments: Experiment[];
  onOpen?: (id: string) => void;
}) {
  return (
    <div className="table-wrap">
      <table className="w-full border-collapse">
        <thead>
          <tr>
            <th className="th">Name</th>
            <th className="th">Status</th>
            <th className="th">Model</th>
            <th className="th">Dataset</th>
            <th className="th text-right">Workers</th>
            <th className="th text-right">Epochs</th>
            <th className="th">Created</th>
          </tr>
        </thead>
        <tbody>
          {experiments.map((exp) => {
            const running = exp.workers.filter((w) => w.status === "RUNNING").length;
            return (
              <tr
                key={exp.id}
                onClick={() => (onOpen ? onOpen(exp.id) : undefined)}
                className={cx(
                  "border-t border-white/5 transition-colors",
                  onOpen ? "cursor-pointer hover:bg-white/[0.03]" : "hover:bg-white/[0.03]"
                )}
              >
                <td className="td">
                  <Link
                    href={`/experiment/${exp.id}`}
                  onClick={(e: React.MouseEvent) => e.stopPropagation()}
                    className="font-medium text-slate-100 hover:text-accent-soft"
                  >
                    {exp.name}
                  </Link>
                  <span className="ml-2 font-mono text-[11px] text-slate-500">{shortId(exp.id)}</span>
                </td>
                <td className="td">
                  <span className="flex items-center gap-2">
                    {isPulsing(exp.status) && (
                      <span className="inline-block h-1.5 w-1.5 animate-pulse-soft rounded-full bg-emerald-400" />
                    )}
                    <StatusBadge status={exp.status} />
                  </span>
                </td>
                <td className="td text-slate-400">{exp.spec.model.type}</td>
                <td className="td">
                  <span className="font-mono text-xs text-slate-400">
                    {exp.spec.dataset.name}:{exp.spec.dataset.version}
                  </span>
                </td>
                <td className="td text-right tabular-nums text-slate-300">
                  {running > 0 ? (
                    <span className="text-emerald-300">
                      {running}
                      <span className="text-slate-500">/{exp.spec.resources.workers}</span>
                    </span>
                  ) : (
                    <span className="text-slate-400">{exp.spec.resources.workers}</span>
                  )}
                </td>
                <td className="td text-right tabular-nums text-slate-300">{exp.spec.training.epochs}</td>
                <td className="td text-slate-500" title={formatDateTime(exp.job?.created_at)}>
                  {relativeTime(exp.job?.created_at)}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>

      {experiments.length === 0 && (
        <div className="p-6">
          <EmptyState
            title="No experiments match"
            hint="Submit an experiment using the form above, or clear your filters."
          />
        </div>
      )}
    </div>
  );
}
