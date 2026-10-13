import { EmptyState } from "./Feedback";
import { BoolBadge } from "./StatusBadge";
import { cx, formatBytes, formatDateTime, relativeTime, shortId, shortUri } from "../lib/format";
import type { Dataset } from "../types";

const FORMAT_TONE: Record<string, string> = {
  parquet: "border-sky-400/30 bg-sky-400/10 text-sky-300",
  csv: "border-emerald-400/30 bg-emerald-400/10 text-emerald-300",
  root: "border-fuchsia-400/30 bg-fuchsia-400/10 text-fuchsia-300",
};

function formatTone(fmt: string): string {
  return FORMAT_TONE[fmt.toLowerCase()] ?? "border-white/10 bg-white/5 text-slate-300";
}

/** Registered-datasets table: name:version, format badge, size, location, metadata. */
export function DatasetTable({ datasets }: { datasets: Dataset[] }) {
  if (datasets.length === 0) {
    return (
      <div className="card p-6">
        <EmptyState
          title="No datasets registered"
          hint="Register one via POST /datasets (or `make register-sample-dataset`). An experiment can only reference a registered dataset name:version."
        />
      </div>
    );
  }

  return (
    <div className="table-wrap">
      <table className="w-full border-collapse">
        <thead>
          <tr>
            <th className="th">Dataset</th>
            <th className="th">Format</th>
            <th className="th text-right">Size</th>
            <th className="th">Location</th>
            <th className="th">Details</th>
            <th className="th">Created</th>
          </tr>
        </thead>
        <tbody>
          {datasets.map((ds) => (
            <tr key={ds.dataset_id} className="border-t border-white/5 transition-colors hover:bg-white/[0.03]">
              <td className="td">
                <div className="font-medium text-slate-100">
                  {ds.name}
                  <span className="text-slate-500">:{ds.version}</span>
                </div>
                <span className="font-mono text-[11px] text-slate-500">{shortId(ds.dataset_id)}</span>
              </td>
              <td className="td">
                <span className={cx("chip", formatTone(ds.format))}>{ds.format}</span>
              </td>
              <td className="td text-right tabular-nums text-slate-400">{formatBytes(ds.size)}</td>
              <td className="td">
                <code className="font-mono text-[11px] text-slate-400" title={ds.storage_location}>
                  {shortUri(ds.storage_location)}
                </code>
              </td>
              <td className="td">
                <div className="flex flex-wrap gap-1.5">
                  {typeof ds.metadata?.tree === "string" && <MetaChip label="tree" value={ds.metadata.tree} />}
                  {Array.isArray(ds.metadata?.features) && (
                    <MetaChip label="features" value={(ds.metadata.features as unknown[]).length} />
                  )}
                  {ds.metadata?.rows != null && <MetaChip label="rows" value={String(ds.metadata.rows)} />}
                  {ds.checksum && <MetaChip label="sha256" value={ds.checksum.slice(0, 8)} mono />}
                </div>
              </td>
              <td className="td text-slate-500" title={formatDateTime(ds.created_at)}>
                {relativeTime(ds.created_at)}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function MetaChip({ label, value, mono = false }: { label: string; value: string | number; mono?: boolean }) {
  return (
    <span className="chip border border-white/10 bg-white/5 text-slate-400" title={`${label}: ${value}`}>
      <span className="text-slate-500">{label}</span>
      <span className={cx(mono && "font-mono")}>{value}</span>
    </span>
  );
}

/** Re-export so detail pages can reuse the boolean chip without extra imports. */
export { BoolBadge };
