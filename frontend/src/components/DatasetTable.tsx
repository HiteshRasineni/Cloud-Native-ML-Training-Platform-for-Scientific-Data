"use client";
import { Dataset } from "../types";

export function DatasetTable({ datasets }: { datasets: Dataset[] }) {
  if (datasets.length === 0) {
    return <p>No registered datasets yet. Register one with <code>docker compose exec backend python scripts/register_sample_dataset.py</code>.</p>;
  }
  return (
    <table border={1} cellPadding={8} style={{ width: "100%", borderCollapse: "collapse" }}>
      <thead>
        <tr>
          <th>Name:Version</th>
          <th>Format</th>
          <th>Storage location</th>
          <th>Rows</th>
        </tr>
      </thead>
      <tbody>
        {datasets.map((d) => (
          <tr key={d.dataset_id}>
            <td>{d.name}:{d.version}</td>
            <td>{d.format}</td>
            <td><code>{d.storage_location}</code></td>
            <td>{d.metadata?.rows != null ? String(d.metadata.rows) : "—"}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}