import { useState } from "react";
import { Spinner } from "./Feedback";
import { registerDataset } from "../api/client";

const FORMATS = ["parquet", "csv", "root", "hdf5", "json", "npz"];

interface DatasetFormState {
  name: string;
  version: string;
  format: string;
  storage_location: string;
  size: string;
  tree: string;
  rows: string;
}

const initial: DatasetFormState = {
  name: "",
  version: "v1",
  format: "parquet",
  storage_location: "",
  size: "",
  tree: "",
  rows: "",
};

/** Inline form for registering a new dataset. Calls POST /datasets. */
export function DatasetForm({ onCreated }: { onCreated: () => void }) {
  const [form, setForm] = useState<DatasetFormState>(initial);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [open, setOpen] = useState(false);

  const set = <K extends keyof DatasetFormState>(key: K, value: DatasetFormState[K]) =>
    setForm((f) => ({ ...f, [key]: value }));

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    if (!form.name.trim()) { setError("Dataset name is required."); return; }
    if (!form.storage_location.trim()) { setError("Storage location is required."); return; }

    const metadata: Record<string, unknown> = {};
    if (form.tree.trim()) metadata.tree = form.tree.trim();
    if (form.rows.trim()) metadata.rows = Number(form.rows);

    setSubmitting(true);
    try {
      await registerDataset({
        name: form.name.trim(),
        version: form.version.trim() || "v1",
        format: form.format,
        storage_location: form.storage_location.trim(),
        size: form.size ? Number(form.size) : null,
        metadata: Object.keys(metadata).length ? metadata : {},
      });
      setForm(initial);
      setOpen(false);
      onCreated();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to register dataset");
    } finally {
      setSubmitting(false);
    }
  };

  if (!open) {
    return (
      <button className="btn btn-ghost" onClick={() => setOpen(true)}>
        <svg className="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <path strokeLinecap="round" strokeLinejoin="round" d="M12 5v14M5 12h14" />
        </svg>
        Register dataset
      </button>
    );
  }

  return (
    <form onSubmit={submit} className="card animate-fade-in p-5">
      <div className="mb-4 flex items-center justify-between">
        <h3 className="text-sm font-semibold text-slate-200">Register a new dataset</h3>
        <button
          type="button"
          className="text-slate-500 transition-colors hover:text-slate-300"
          onClick={() => { setOpen(false); setForm(initial); setError(null); }}
        >
          <svg className="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        {/* Left column */}
        <div className="space-y-4">
          <Field label="Dataset name" hint="Logical name — referenced by experiments">
            <input
              className="input"
              placeholder="e.g. higgs-tau-tau"
              value={form.name}
              onChange={(e) => set("name", e.target.value)}
              required
            />
          </Field>

          <div className="grid grid-cols-2 gap-3">
            <Field label="Version">
              <input
                className="input"
                placeholder="v1"
                value={form.version}
                onChange={(e) => set("version", e.target.value)}
              />
            </Field>
            <Field label="Format">
              <select className="input" value={form.format} onChange={(e) => set("format", e.target.value)}>
                {FORMATS.map((f) => (
                  <option key={f} value={f}>{f}</option>
                ))}
              </select>
            </Field>
          </div>

          <Field label="Storage location" hint="S3 / MinIO path, e.g. s3://datasets/higgs/v1/data.parquet">
            <input
              className="input"
              placeholder="s3://datasets/..."
              value={form.storage_location}
              onChange={(e) => set("storage_location", e.target.value)}
              required
            />
          </Field>
        </div>

        {/* Right column — optional metadata */}
        <div className="space-y-4">
          <Field label="File size (bytes)" hint="Optional — used for display only">
            <input
              className="input"
              type="number"
              min={0}
              placeholder="e.g. 104857600"
              value={form.size}
              onChange={(e) => set("size", e.target.value)}
            />
          </Field>
          <Field label="ROOT tree name" hint="For ROOT files only">
            <input
              className="input"
              placeholder="e.g. Events"
              value={form.tree}
              onChange={(e) => set("tree", e.target.value)}
            />
          </Field>
          <Field label="Row count" hint="Optional, stored in metadata">
            <input
              className="input"
              type="number"
              min={0}
              placeholder="e.g. 1000000"
              value={form.rows}
              onChange={(e) => set("rows", e.target.value)}
            />
          </Field>
        </div>
      </div>

      {error && (
        <p className="mt-4 rounded-lg border border-rose-400/30 bg-rose-400/10 px-3 py-2 text-sm text-rose-300">
          {error}
        </p>
      )}

      <div className="mt-5 flex items-center justify-end gap-3">
        <button
          type="button"
          className="btn btn-ghost"
          onClick={() => { setOpen(false); setForm(initial); setError(null); }}
          disabled={submitting}
        >
          Cancel
        </button>
        <button type="submit" className="btn btn-primary" disabled={submitting}>
          {submitting && <Spinner />}
          {submitting ? "Registering…" : "Register dataset"}
        </button>
      </div>
    </form>
  );
}

function Field({ label, hint, children }: { label: string; hint?: string; children: React.ReactNode }) {
  return (
    <label className="block">
      <span className="label">{label}</span>
      {children}
      {hint && <span className="mt-1 block text-xs text-slate-500">{hint}</span>}
    </label>
  );
}
