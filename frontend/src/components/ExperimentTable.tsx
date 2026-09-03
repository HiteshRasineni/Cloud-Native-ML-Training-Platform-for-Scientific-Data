"use client";
import Link from "next/link";
import { Experiment } from "../types";

export function ExperimentTable({ experiments }: { experiments: Experiment[] }) {
  return (
    <table border={1} cellPadding={8} style={{ width: "100%", borderCollapse: "collapse" }}>
      <thead>
        <tr>
          <th>ID</th>
          <th>Name</th>
          <th>Model</th>
          <th>Status</th>
          <th>Attempts</th>
        </tr>
      </thead>
      <tbody>
        {experiments.map((e) => (
          <tr key={e.id}>
            <td>
              <Link href={`/experiment/${e.id}`}>{e.id.slice(0, 8)}</Link>
            </td>
            <td>{e.name}</td>
            <td>{e.spec.model.type}</td>
            <td>{e.status}</td>
            <td>{e.attempts}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
