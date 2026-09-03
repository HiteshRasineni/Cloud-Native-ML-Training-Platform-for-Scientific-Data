"use client";
import Link from "next/link";
import { useRouter } from "next/router";
import { useCallback, useEffect, useState } from "react";
import { getExperiment, getMetrics, listArtifacts } from "../../api/client";
import { Artifact, Experiment, MetricsResponse } from "../../types";
import { LossChart } from "../../components/LossChart";

export default function ExperimentDetail() {
  const router = useRouter();
  const id = router.query.id as string;
  const [exp, setExp] = useState<Experiment | null>(null);
  const [metrics, setMetrics] = useState<MetricsResponse | null>(null);
  const [artifacts, setArtifacts] = useState<Artifact[]>([]);

  const refresh = useCallback(async () => {
    if (!id) return;
    try {
      setExp(await getExperiment(id));
      setMetrics(await getMetrics(id));
      setArtifacts(await listArtifacts(id));
    } catch {
      /* still starting */
    }
  }, [id]);

  useEffect(() => {
    refresh();
    const t = setInterval(refresh, 3000);
    return () => clearInterval(t);
  }, [refresh]);

  if (!exp) return <main style={{ margin: "2rem auto", maxWidth: 900, fontFamily: "sans-serif" }}>Loading...</main>;

  return (
    <main style={{ maxWidth: 900, margin: "2rem auto", fontFamily: "sans-serif" }}>
      <Link href="/">all experiments</Link>
      <h1>{exp.name}</h1>
      <p>
        <b>status:</b> <span style={{ color: exp.status === "RETRYING" ? "#b45309" : exp.status === "FAILED" ? "#b91c1c" : undefined }}>{exp.status}</span> | <b>attempts:</b> {exp.attempts} |{" "}
        <b>model:</b> {exp.spec.model.type} | <b>dataset:</b> {exp.spec.dataset.name}:{exp.spec.dataset.version}
      </p>
      {exp.error_message && <p style={{ color: "red" }}>{exp.error_message}</p>}

      <h2>Workers</h2>
      <table border={1} cellPadding={6} style={{ borderCollapse: "collapse", width: "100%" }}>
        <thead><tr><th>Worker</th><th>Status</th><th>Container</th><th>Last heartbeat</th></tr></thead>
        <tbody>{exp.workers.map((worker) => <tr key={worker.worker_id}>
          <td>{worker.worker_id.slice(0, 8)}</td><td>{worker.status}</td><td>{worker.container_id ?? "-"}</td><td>{worker.heartbeat_time ?? "-"}</td>
        </tr>)}</tbody>
      </table>

      <h2>Failures</h2>
      {exp.failures.length === 0 ? <p>No failures recorded.</p> : <table border={1} cellPadding={6} style={{ borderCollapse: "collapse", width: "100%" }}>
        <thead><tr><th>Type</th><th>Message</th><th>Retryable</th><th>Timestamp</th></tr></thead>
        <tbody>{exp.failures.map((failure) => <tr key={failure.failure_id}><td>{failure.error_type}</td><td>{failure.error_message ?? "-"}</td><td>{failure.retryable ? "yes" : "no"}</td><td>{failure.timestamp}</td></tr>)}</tbody>
      </table>}

      <h2>Loss curve (MLflow)</h2>
      {metrics?.metrics?.loss ? <LossChart points={metrics.metrics.loss} /> : <p>No metrics yet.</p>}

      <h2>Checkpoints and artifacts</h2>
      {artifacts.length === 0 ? (
        <p>No artifacts yet.</p>
      ) : (
        <table border={1} cellPadding={6} style={{ borderCollapse: "collapse", width: "100%" }}>
          <thead>
            <tr><th>Type</th><th>Epoch</th><th>Storage path</th></tr>
          </thead>
          <tbody>
            {artifacts.map((a) => (
              <tr key={a.artifact_id}>
                <td>{a.artifact_type}</td>
                <td>{a.epoch ?? "-"}</td>
                <td><code>{a.storage_path}</code></td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </main>
  );
}
