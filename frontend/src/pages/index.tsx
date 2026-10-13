"use client";
import { useCallback, useEffect, useMemo, useState } from "react";
import { DatasetTable } from "../components/DatasetTable";
import { ExperimentForm } from "../components/ExperimentForm";
import { ExperimentTable } from "../components/ExperimentTable";
import { PageHeader, StatCard } from "../components/ui";
import { Spinner } from "../components/Feedback";
import { listDatasets, listExperiments } from "../api/client";
import { computeStats, isActive } from "../lib/format";
import { Dataset, Experiment } from "../types";

type StatusFilter = "all" | "active" | "completed" | "failed";

export default function Home() {
  const [experiments, setExperiments] = useState<Experiment[]>([]);
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [loading, setLoading] = useState(true);
  const [query, setQuery] = useState("");
  const [status, setStatus] = useState<StatusFilter>("all");

  const refresh = useCallback(async () => {
    try {
      const [exps, ds] = await Promise.all([listExperiments(), listDatasets()]);
      setExperiments(exps);
      setDatasets(ds);
    } catch {
      /* backend not ready yet */
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refresh();
    const id = setInterval(refresh, 3000);
    return () => clearInterval(id);
  }, [refresh]);

  const stats = useMemo(() => computeStats(experiments), [experiments]);

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    return experiments.filter((e) => {
      const matchQ =
        !q ||
        e.name.toLowerCase().includes(q) ||
        e.spec.model.type.toLowerCase().includes(q) ||
        `${e.spec.dataset.name}:${e.spec.dataset.version}`.toLowerCase().includes(q);
      const matchS =
        status === "all" ||
        (status === "active" && isActive(e.status)) ||
        (status === "completed" && e.status === "COMPLETED") ||
        (status === "failed" && e.status === "FAILED");
      return matchQ && matchS;
    });
  }, [experiments, query, status]);

  const FILTERS: { key: StatusFilter; label: string }[] = [
    { key: "all", label: "All" },
    { key: "active", label: "Active" },
    { key: "completed", label: "Completed" },
    { key: "failed", label: "Failed" },
  ];

  return (
    <>
      <PageHeader
        title="Experiments"
        subtitle="Reproducible, failure-resilient training runs on registered datasets."
        actions={
          <button className="btn btn-ghost" onClick={refresh}>
            {loading && <Spinner />}
            Refresh
          </button>
        }
      />

      <div className="mb-6 grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-5">
        <StatCard label="Total" value={stats.total} tone="neutral" />
        <StatCard label="Active" value={stats.active} tone="info" sub={`${stats.activeWorkers}/${stats.workers} workers`} />
        <StatCard label="Completed" value={stats.completed} tone="success" />
        <StatCard label="Failed" value={stats.failed} tone="danger" />
        <StatCard label="Datasets" value={datasets.length} tone="accent" />
      </div>

      <section className="mb-6">
        <h2 className="mb-3 text-sm font-semibold text-slate-200">New experiment</h2>
        <ExperimentForm datasets={datasets} onCreated={refresh} />
      </section>

      <section className="mb-6">
        <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
          <h2 className="text-sm font-semibold text-slate-200">
            Experiments{" "}
            <span className="font-normal text-slate-500">({filtered.length})</span>
          </h2>
          <div className="flex flex-wrap items-center gap-2">
            <input
              className="input w-56"
              placeholder="Search name / model / dataset…"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
            />
            <div className="flex overflow-hidden rounded-lg border border-white/10">
              {FILTERS.map((f) => (
                <button
                  key={f.key}
                  onClick={() => setStatus(f.key)}
                  className={`px-3 py-1.5 text-xs font-medium transition-colors ${
                    status === f.key
                      ? "bg-accent/20 text-accent-soft"
                      : "text-slate-400 hover:bg-white/5"
                  }`}
                >
                  {f.label}
                </button>
              ))}
            </div>
          </div>
        </div>
        <ExperimentTable experiments={filtered} />
      </section>

      <section>
        <h2 className="mb-3 text-sm font-semibold text-slate-200">Registered datasets</h2>
        <DatasetTable datasets={datasets} />
      </section>
    </>
  );
}
