import { useState } from "react";
import { Spinner } from "./Feedback";
import { createExperiment } from "../api/client";
import type { Dataset } from "../types";

const MODEL_TYPES = [
  { value: "normalizing-flow", label: "Normalizing Flow", hint: "RealNVP density model (PyTorch, CPU/GPU)" },
  { value: "classifier", label: "Classifier", hint: "Supervised classifier (coming soon)" },
  { value: "dummy", label: "Dummy", hint: "No-op smoke-test workload" },
];

interface FormState {
  name: string;
  datasetKey: string;
  modelType: string;
  transforms: number;
  hidden_features: number;
  workers: number;
  cpu: string;
  memory: string;
  gpu: number;
  epochs: number;
  batch_size: number;
  learning_rate: number;
  checkpointing: boolean;
  interval: number;
  max_attempts: number;
}

const initial: FormState = {
  name: "",
  datasetKey: "",
  modelType: "normalizing-flow",
  transforms: 4,
  hidden_features: 32,
  workers: 1,
  cpu: "1",
  memory: "1Gi",
  gpu: 0,
  epochs: 10,
  batch_size: 128,
  learning_rate: 0.001,
  checkpointing: true,
  interval: 1,
  max_attempts: 3,
};

/** Full experiment submission form. Builds the nested spec and POSTs /experiments. */
export function ExperimentForm({ datasets, onCreated }: { datasets: Dataset[]; onCreated: () => void }) {
  const [form, setForm] = useState<FormState>(initial);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const set = <K extends keyof FormState>(key: K, value: FormState[K]) =>
    setForm((f) => ({ ...f, [key]: value }));

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    if (!form.datasetKey) {
      setError("Select a dataset first.");
      return;
    }
    const [name, version] = form.datasetKey.split("::");
    setSubmitting(true);
    try {
      const spec = {
        experiment: { name: form.name.trim() || `exp-${Date.now().toString(36)}` },
        dataset: { name, version },
        model: {
          type: form.modelType,
          architecture:
            form.modelType === "normalizing-flow"
              ? { transforms: Number(form.transforms), hidden_features: Number(form.hidden_features) }
              : {},
        },
        resources: { workers: Number(form.workers), cpu: form.cpu, memory: form.memory, gpu: Number(form.gpu) },
        training: { epochs: Number(form.epochs), batch_size: Number(form.batch_size), learning_rate: Number(form.learning_rate) },
        checkpointing: { enabled: form.checkpointing, interval: Number(form.interval) },
        retry: { max_attempts: Number(form.max_attempts) },
      };
      await createExperiment(spec);
      setForm({ ...initial });
      onCreated();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create experiment");
    } finally {
      setSubmitting(false);
    }
  };

  const isNF = form.modelType === "normalizing-flow";

  return (
    <form onSubmit={submit} className="card animate-fade-in p-5">
      <div className="grid gap-5 md:grid-cols-2">
        <div className="space-y-4">
          <Field label="Experiment name" hint="Leave blank to auto-generate">
            <input className="input" placeholder="e.g. nf-baseline-v1" value={form.name} onChange={(e) => set("name", e.target.value)} />
          </Field>
          <Field label="Dataset">
            <select className="input" value={form.datasetKey} onChange={(e) => set("datasetKey", e.target.value)} required>
              <option value="">Select a registered dataset...</option>
              {datasets.map((d) => (
                <option key={d.dataset_id} value={`${d.name}::${d.version}`}>
                  {d.name}:{d.version} ({d.format})
                </option>
              ))}
            </select>
            {datasets.length === 0 && (
              <p className="mt-1 text-xs text-amber-300/80">
                No datasets registered yet - run <code className="text-amber-200">make register-sample-dataset</code>.
              </p>
            )}
          </Field>
          <Field label="Model">
            <select className="input" value={form.modelType} onChange={(e) => set("modelType", e.target.value)}>
              {MODEL_TYPES.map((m) => (
                <option key={m.value} value={m.value}>
                  {m.label}
                </option>
              ))}
            </select>
            <p className="mt-1 text-xs text-slate-500">{MODEL_TYPES.find((m) => m.value === form.modelType)?.hint}</p>
          </Field>
          {isNF && (
            <div className="grid grid-cols-2 gap-3">
              <Field label="Transforms">
                <input className="input" type="number" min={1} max={32} value={form.transforms} onChange={(e) => set("transforms", Number(e.target.value))} />
              </Field>
              <Field label="Hidden features">
                <input className="input" type="number" min={4} max={512} value={form.hidden_features} onChange={(e) => set("hidden_features", Number(e.target.value))} />
              </Field>
            </div>
          )}
        </div>

        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-3">
            <Field label="Workers">
              <input className="input" type="number" min={1} max={64} value={form.workers} onChange={(e) => set("workers", Number(e.target.value))} />
            </Field>
            <Field label="GPUs / worker">
              <input className="input" type="number" min={0} max={8} value={form.gpu} onChange={(e) => set("gpu", Number(e.target.value))} />
            </Field>
            <Field label="CPU">
              <input className="input" value={form.cpu} onChange={(e) => set("cpu", e.target.value)} />
            </Field>
            <Field label="Memory">
              <input className="input" value={form.memory} onChange={(e) => set("memory", e.target.value)} />
            </Field>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <Field label="Epochs">
              <input className="input" type="number" min={1} value={form.epochs} onChange={(e) => set("epochs", Number(e.target.value))} />
            </Field>
            <Field label="Batch size">
              <input className="input" type="number" min={1} value={form.batch_size} onChange={(e) => set("batch_size", Number(e.target.value))} />
            </Field>
          </div>
          <Field label="Learning rate">
            <input className="input" type="number" step="any" min={0} value={form.learning_rate} onChange={(e) => set("learning_rate", Number(e.target.value))} />
          </Field>
          <div className="grid grid-cols-2 gap-3">
            <Field label="Checkpoint every N epochs">
              <input className="input" type="number" min={1} disabled={!form.checkpointing} value={form.interval} onChange={(e) => set("interval", Number(e.target.value))} />
            </Field>
            <Field label="Retry attempts">
              <input className="input" type="number" min={1} max={10} value={form.max_attempts} onChange={(e) => set("max_attempts", Number(e.target.value))} />
            </Field>
          </div>
          <label className="flex cursor-pointer items-center gap-2 text-sm text-slate-300">
            <input type="checkbox" className="h-4 w-4 rounded border-white/20 bg-ink-850 accent-accent" checked={form.checkpointing} onChange={(e) => set("checkpointing", e.target.checked)} />
            Enable checkpointing
          </label>
        </div>
      </div>

      {error && (
        <p className="mt-4 rounded-lg border border-rose-400/30 bg-rose-400/10 px-3 py-2 text-sm text-rose-300">{error}</p>
      )}

      <div className="mt-5 flex items-center justify-end gap-3">
        <button type="button" className="btn btn-ghost" onClick={() => setForm(initial)} disabled={submitting}>
          Reset
        </button>
        <button type="submit" className="btn btn-primary" disabled={submitting || datasets.length === 0}>
          {submitting && <Spinner />}
          {submitting ? "Submitting..." : "Submit experiment"}
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