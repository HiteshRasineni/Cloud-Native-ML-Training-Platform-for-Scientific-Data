"use client";
import { useCallback, useEffect, useState } from "react";
import { DatasetTable } from "../components/DatasetTable";
import { ExperimentForm } from "../components/ExperimentForm";
import { ExperimentTable } from "../components/ExperimentTable";
import { listDatasets, listExperiments } from "../api/client";
import { Dataset, Experiment } from "../types";

export default function Home() {
  const [experiments, setExperiments] = useState<Experiment[]>([]);
  const [datasets, setDatasets] = useState<Dataset[]>([]);

  const refresh = useCallback(async () => {
    try {
      setExperiments(await listExperiments());
      setDatasets(await listDatasets());
    } catch {
      /* backend not ready yet */
    }
  }, []);

  useEffect(() => {
    refresh();
    const id = setInterval(refresh, 3000);
    return () => clearInterval(id);
  }, [refresh]);

  return (
    <main style={{ maxWidth: 900, margin: "2rem auto", fontFamily: "sans-serif" }}>
      <h1>Cloud ML Platform</h1>
      <ExperimentForm datasets={datasets} onCreated={refresh} />
      <h2>Registered datasets</h2>
      <DatasetTable datasets={datasets} />
      <h2>Experiments</h2>
      <ExperimentTable experiments={experiments} />
      <p><a href="/workers">Worker monitoring</a></p>
      <p><a href="http://localhost:3001/d/platform-overview/platform-overview" target="_blank" rel="noreferrer">Grafana Platform Overview</a></p>
    </main>
  );
}
