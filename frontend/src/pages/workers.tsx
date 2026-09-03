"use client";
import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { listWorkers } from "../api/client";
import { Worker } from "../types";

export default function WorkersPage() {
  const [workers, setWorkers] = useState<Worker[]>([]);
  const refresh = useCallback(async () => {
    try { setWorkers(await listWorkers()); } catch { /* backend may still be starting */ }
  }, []);
  useEffect(() => { refresh(); const timer = setInterval(refresh, 3000); return () => clearInterval(timer); }, [refresh]);

  return <main style={{ maxWidth: 1100, margin: "2rem auto", fontFamily: "sans-serif" }}>
    <Link href="/">all experiments</Link>
    <h1>Worker monitoring</h1>
    <table border={1} cellPadding={6} style={{ borderCollapse: "collapse", width: "100%" }}>
      <thead><tr><th>Worker</th><th>Status</th><th>Job</th><th>Last heartbeat</th><th>Hostname / container</th></tr></thead>
      <tbody>{workers.map((worker) => <tr key={worker.worker_id}>
        <td>{worker.worker_id.slice(0, 8)}</td>
        <td style={{ color: worker.status === "FAILED" ? "#b91c1c" : worker.status === "RUNNING" ? "#166534" : undefined }}>{worker.status}</td>
        <td>{worker.job_id.slice(0, 8)}</td><td>{worker.heartbeat_time ?? "-"}</td>
        <td>{worker.hostname ?? "-"} / {worker.container_id ?? "-"}</td>
      </tr>)}</tbody>
    </table>
  </main>;
}
