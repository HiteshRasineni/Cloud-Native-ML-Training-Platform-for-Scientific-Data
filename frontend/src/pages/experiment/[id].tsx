"use client";
import { useRouter } from "next/router";
import { useCallback, useEffect, useState } from "react";
import { getExperiment, getMetrics, listArtifacts, getHistory, cancelExperiment } from "../../api/client";
import { Artifact, Experiment, MetricsResponse, Transition } from "../../types";
import { LossChart } from "../../components/LossChart";
import { Timeline, WorkerTable, FailureList } from "../../components/ExperimentParts";
import { StatusBadge } from "../../components/StatusBadge";
import { EmptyState, Loading, Spinner } from "../../components/Feedback";
import { BackLink, KeyVal, Notice, PageHeader, Section, StatCard, Tabs } from "../../components/ui";
import { cx, formatDateTime, isActive, relativeTime, shortId } from "../../lib/format";

type TabKey = "overview" | "metrics" | "workers" | "failures" | "artifacts" | "history";

export default function ExperimentDetail() {
  const router = useRouter();
  const id = router.query.id as string;
  const [exp, setExp] = useState<Experiment | null>(null);
  const [metrics, setMetrics] = useState<MetricsResponse | null>(null);
  const [artifacts, setArtifacts] = useState<Artifact[]>([]);
  const [history, setHistory] = useState<Transition[]>([]);
  const [tab, setTab] = useState<TabKey>("overview");
  const [loading, setLoading] = useState(true);
  const [cancelling, setCancelling] = useState(false);

  const refresh = useCallback(async () => {
    if (!id) return;
    try {
      setExp(await getExperiment(id));
      setMetrics(await getMetrics(id));
      setArtifacts(await listArtifacts(id));
      setHistory(await getHistory(id));
    } catch {
      /* still starting */
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    refresh();
    const t = setInterval(refresh, 3000);
    return () => clearInterval(t);
  }, [refresh]);

  const cancel = useCallback(async () => {
    if (!id) return;
    setCancelling(true);
    try {
      await cancelExperiment(id);
      await refresh();
    } catch {
      /* ignore */
    } finally {
      setCancelling(false);
    }
  }, [id, refresh]);

  if (loading && !exp) {
    return (
      <>
        <BackLink href="/">All experiments</BackLink>
        <Loading label="Loading experiment" />
      </>
    );
  }
  if (!exp) {
    return (
      <>
        <BackLink href="/">All experiments</BackLink>
        <EmptyState title="Experiment not found" hint="It may have been removed, or the backend is unreachable." />
      </>
    );
  }

  const spec = exp.spec;
  const runningWorkers = exp.workers.filter((w) => w.status === "RUNNING").length;
  const lossPoints = metrics?.metrics?.loss ?? [];
  const lastLoss = lossPoints.length ? lossPoints[lossPoints.length - 1].value : null;
  const series = lossPoints.length ? [{ name: "loss", color: "#818cf8", points: lossPoints }] : [];

  const tabs: Array<{ key: TabKey; label: string; count?: number }> = [
    { key: "overview", label: "Overview" },
    { key: "metrics", label: "Metrics", count: lossPoints.length || undefined },
    { key: "workers", label: "Workers", count: exp.workers.length },
    { key: "failures", label: "Failures", count: exp.failures.length || undefined },
    { key: "artifacts", label: "Artifacts", count: artifacts.length || undefined },
    { key: "history", label: "History", count: history.length || undefined },
  ];

  return (
    <>
      <BackLink href="/">All experiments</BackLink>

      <PageHeader
        title={exp.name}
        subtitle={<span className="font-mono text-xs">{exp.id}</span>}
        actions={
          <>
            {isActive(exp.status) && (
              <button
                className="btn btn-ghost border-rose-400/30 text-rose-300 hover:bg-rose-400/10"
                onClick={cancel}
                disabled={cancelling}
              >
                {cancelling && <Spinner />}
                Cancel
              </button>
            )}
            <button className="btn btn-ghost" onClick={refresh}>
              {loading && <Spinner />}
              Refresh
            </button>
          </>
        }
      />

      <div className="mb-6 grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-5">
        <div className="card flex flex-col justify-center gap-2 p-4">
          <p className="text-xs font-medium uppercase tracking-wide text-slate-500">Status</p>
          <StatusBadge status={exp.status} className="w-fit text-sm" />
          <p className="text-xs text-slate-500">attempt {exp.attempts} / {spec.retry.max_attempts}</p>
        </div>
        <StatCard
          label="Model"
          value={spec.model.type}
          tone="accent"
          sub={
            spec.model.architecture?.transforms
              ? `${spec.model.architecture.transforms}×${spec.model.architecture.hidden_features ?? 32}`
              : undefined
          }
        />
        <StatCard
          label="Workers"
          value={`${runningWorkers}/${spec.resources.workers}`}
          tone="info"
          sub={`${spec.resources.cpu} cpu · ${spec.resources.memory}${spec.resources.gpu ? ` · ${spec.resources.gpu} gpu` : ""}`}
        />
        <StatCard
          label="Latest loss"
          value={lastLoss != null ? Number(lastLoss).toPrecision(4) : "—"}
          tone={lastLoss != null ? "success" : "info"}
          sub={lossPoints.length ? `${lossPoints.length} epochs` : "no metrics yet"}
        />
        <StatCard label="Created" value={relativeTime(exp.job?.created_at)} tone="neutral" sub={formatDateTime(exp.job?.created_at)} />
      </div>

      {exp.error_message && (
        <div className="mb-6">
          <Notice tone={exp.status === "FAILED" ? "danger" : "warn"}>{exp.error_message}</Notice>
        </div>
      )}

      <div className="mb-5">
        <Tabs tabs={tabs} active={tab} onChange={setTab} />
      </div>

      {tab === "overview" && (
        <div className="grid gap-5 lg:grid-cols-2">
          <Section title="Configuration">
            <KeyVal
              items={[
                { k: "Experiment", v: exp.name },
                { k: "Dataset", v: `${spec.dataset.name}:${spec.dataset.version}` },
                { k: "Format", v: spec.dataset.format ?? "—" },
                { k: "Model", v: spec.model.type },
                { k: "Transforms", v: spec.model.architecture?.transforms ?? "—" },
                { k: "Hidden features", v: spec.model.architecture?.hidden_features ?? "—" },
                { k: "Epochs", v: spec.training.epochs },
                { k: "Batch size", v: spec.training.batch_size },
                { k: "Learning rate", v: spec.training.learning_rate },
                { k: "Workers", v: spec.resources.workers },
                { k: "CPU / memory", v: `${spec.resources.cpu} / ${spec.resources.memory}` },
                { k: "GPU", v: spec.resources.gpu ?? 0 },
                { k: "Checkpointing", v: spec.checkpointing.enabled ? `every ${spec.checkpointing.interval} ep` : "off" },
                { k: "Retry attempts", v: spec.retry.max_attempts },
              ]}
            />
          </Section>
          <Section title="Storage">
            {spec.dataset.storage_location ? (
              <div className="space-y-2">
                <p className="text-xs uppercase tracking-wide text-slate-500">Dataset object</p>
                <code className="block break-all rounded-lg border border-white/10 bg-ink-850 px-3 py-2 font-mono text-xs text-slate-300">
                  {spec.dataset.storage_location}
                </code>
              </div>
            ) : (
              <EmptyState title="No storage location resolved" />
            )}
            {metrics?.run_id && (
              <div className="mt-4">
                <p className="text-xs uppercase tracking-wide text-slate-500">MLflow run</p>
                <a
                  className="link font-mono text-xs"
                  href={`${process.env.NEXT_PUBLIC_MLFLOW_URL || "http://localhost:5000"}/#/experiments/0/runs/${metrics.run_id}`}
                  target="_blank"
                  rel="noreferrer"
                >
                  {shortId(metrics.run_id, 12)} ↗
                </a>
              </div>
            )}
          </Section>
        </div>
      )}

      {tab === "metrics" && (
        <Section title="Loss curve" hint="Per-epoch training loss, proxied from MLflow.">
          {series.length ? (
            <LossChart series={series} yLabel="loss" xLabel="epoch" />
          ) : (
            <EmptyState
              title="No metrics yet"
              hint="Metrics stream in once the worker starts training. The chart appears after the first epoch."
            />
          )}
        </Section>
      )}

      {tab === "workers" && <WorkerTable workers={exp.workers} />}
      {tab === "failures" && <FailureList failures={exp.failures} />}
      {tab === "artifacts" && <ArtifactTable artifacts={artifacts} />}
      {tab === "history" && (
        <Section title="Lifecycle transitions" hint="Every state change, oldest first.">
          <Timeline transitions={history} />
        </Section>
      )}
    </>
  );
}


/** Artifacts table grouped by type with epoch + storage path. */
function ArtifactTable({ artifacts }: { artifacts: Artifact[] }) {
  if (artifacts.length === 0) {
    return <EmptyState title="No artifacts recorded" hint="Checkpoints and the final model appear here as the run progresses." />;
  }
  const ordered = [...artifacts].sort((a, b) => (a.epoch ?? -1) - (b.epoch ?? -1));
  return (
    <div className="table-wrap">
      <table className="w-full border-collapse">
        <thead>
          <tr>
            <th className="th">Type</th>
            <th className="th text-right">Epoch</th>
            <th className="th">Storage path</th>
            <th className="th">Created</th>
          </tr>
        </thead>
        <tbody>
          {ordered.map((a) => (
            <tr key={a.artifact_id} className="border-t border-white/5 transition-colors hover:bg-white/[0.03]">
              <td className="td">
                <span
                  className={cx(
                    "chip border",
                    a.artifact_type === "model"
                      ? "border-emerald-400/30 bg-emerald-400/10 text-emerald-300"
                      : a.artifact_type === "checkpoint"
                      ? "border-accent/30 bg-accent/10 text-accent-soft"
                      : "border-white/10 bg-white/5 text-slate-400"
                  )}
                >
                  {a.artifact_type}
                </span>
              </td>
              <td className="td text-right tabular-nums text-slate-400">{a.epoch ?? "—"}</td>
              <td className="td">
                <code className="font-mono text-xs text-slate-400" title={a.storage_path}>
                  {a.storage_path.replace(/^s3:\/\//, "")}
                </code>
              </td>
              <td className="td text-slate-500" title={formatDateTime(a.created_at)}>
                {relativeTime(a.created_at)}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

