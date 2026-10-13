"use client";
import { useCallback, useEffect, useMemo, useState } from "react";
import { listDatasets } from "../api/client";
import { Dataset } from "../types";
import { DatasetTable } from "../components/DatasetTable";
import { DatasetForm } from "../components/DatasetForm";
import { EmptyState, Loading, Spinner } from "../components/Feedback";
import { PageHeader, Section, StatCard } from "../components/ui";
import { formatBytes } from "../lib/format";

export default function DatasetsPage() {
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [loading, setLoading] = useState(true);
  const [query, setQuery] = useState("");

  const refresh = useCallback(async () => {
    try {
      setDatasets(await listDatasets());
    } catch {
      /* backend may still be starting */
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  const stats = useMemo(() => {
    const totalSize = datasets.reduce((acc, d) => acc + (d.size ?? 0), 0);
    const formats = new Set(datasets.map((d) => d.format.toLowerCase()));
    return { total: datasets.length, formats: formats.size, totalSize };
  }, [datasets]);

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return datasets;
    return datasets.filter(
      (d) =>
        d.name.toLowerCase().includes(q) ||
        d.version.toLowerCase().includes(q) ||
        d.format.toLowerCase().includes(q) ||
        d.storage_location.toLowerCase().includes(q)
    );
  }, [datasets, query]);

  return (
    <>
      <PageHeader
        title="Datasets"
        subtitle="Versioned dataset registry. Experiments reference datasets by name:version, resolved to a MinIO object."
        actions={
          <button className="btn btn-ghost" onClick={refresh}>
            {loading && <Spinner />}
            Refresh
          </button>
        }
      />

      <div className="mb-6 grid grid-cols-2 gap-3 sm:grid-cols-3">
        <StatCard label="Registered datasets" value={stats.total} tone="accent" />
        <StatCard label="Distinct formats" value={stats.formats} tone="info" sub="parquet / csv / root" />
        <StatCard label="Total size" value={formatBytes(stats.totalSize)} tone="neutral" />
      </div>

      <section className="mb-6">
        <h2 className="mb-3 text-sm font-semibold text-slate-200">Register a dataset</h2>
        <DatasetForm onCreated={refresh} />
      </section>

      <Section
        title="All datasets"
        hint="Register via the form above, POST /datasets, or `make register-sample-dataset`."
        actions={
          <input
            className="input w-64"
            placeholder="Search name / format / location…"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
        }
      >
        {loading && datasets.length === 0 ? (
          <Loading label="Loading datasets" />
        ) : filtered.length === 0 ? (
          <EmptyState
            title={datasets.length === 0 ? "No datasets registered" : "No datasets match your search"}
            hint="A dataset must be registered before an experiment can reference it by name:version."
          />
        ) : (
          <DatasetTable datasets={filtered} />
        )}
      </Section>
    </>
  );
}
