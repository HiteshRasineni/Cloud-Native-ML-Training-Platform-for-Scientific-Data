"use client";
import { useState } from "react";
import { createExperiment } from "../api/client";

interface DatasetOption {
  name: string;
  version: string;
  format: string;
}

export function ExperimentForm({
  datasets,
  onCreated,
}: {
  datasets: DatasetOption[];
  onCreated: () => void;
}) {
  const [name, setName] = useState("nf-hep-study");
  const [datasetUri, setDatasetUri] = useState("");
  const [modelType, setModelType] = useState("normalizing-flow");
  const [transforms, setTransforms] = useState(4);
  const [hiddenFeatures, setHiddenFeatures] = useState(32);
  const [epochs, setEpochs] = useState(5);
  const [checkpointing, setCheckpointing] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!datasetUri) {
      setError("Register a dataset first (docker compose exec backend python scripts/register_sample_dataset.py)");
      return;
    }
    const [dsName, dsVersion] = datasetUri.split(":");
    setBusy(true);
    setError(null);
    try {
      await createExperiment({
        experiment: { name },
        dataset: { name: dsName, version: dsVersion },
        model: { type: modelType, architecture: { transforms, hidden_features: hiddenFeatures } },
        resources: { workers: 1, cpu: "2", memory: "4Gi" },
        training: { epochs, batch_size: 256, learning_rate: 0.001 },
        checkpointing: { enabled: checkpointing, interval: 1 },
        retry: { max_attempts: 3 },
      });
      onCreated();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setBusy(false);
    }
  };

  return (
    <form onSubmit={submit} style={{ display: "grid", gap: 8, margin: "1rem 0" }}>
      <label>
        Name: <input value={name} onChange={(e) => setName(e.target.value)} required />
      </label>
      <label>
        Dataset (name:version - must be registered):{" "}
        <select value={datasetUri} onChange={(e) => setDatasetUri(e.target.value)} required>
          <option value="">-- select a registered dataset --</option>
          {datasets.map((d) => (
            <option key={`${d.name}:${d.version}`} value={`${d.name}:${d.version}`}>
              {d.name}:{d.version} ({d.format})
            </option>
          ))}
        </select>
      </label>
      <label>
        Model type:{" "}
        <select value={modelType} onChange={(e) => setModelType(e.target.value)}>
          <option value="normalizing-flow">normalizing-flow</option>
          <option value="dummy">dummy</option>
        </select>
      </label>
      {modelType === "normalizing-flow" && (
        <>
          <label>
            Coupling transforms:{" "}
            <input type="number" min={1} max={16} value={transforms} onChange={(e) => setTransforms(Number(e.target.value))} />
          </label>
          <label>
            Hidden features:{" "}
            <input type="number" min={4} max={256} value={hiddenFeatures} onChange={(e) => setHiddenFeatures(Number(e.target.value))} />
          </label>
        </>
      )}
      <label>
        Epochs: <input type="number" min={1} max={200} value={epochs} onChange={(e) => setEpochs(Number(e.target.value))} />
      </label>
      <label>
        Checkpoint every epoch:{" "}
        <input type="checkbox" checked={checkpointing} onChange={(e) => setCheckpointing(e.target.checked)} />
      </label>
      <button type="submit" disabled={busy}>
        {busy ? "Submitting..." : "Submit experiment"}
      </button>
      {error && <p style={{ color: "red" }}>{error}</p>}
    </form>
  );
}
