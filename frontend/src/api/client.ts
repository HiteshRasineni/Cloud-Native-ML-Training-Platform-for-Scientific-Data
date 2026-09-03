import { Artifact, Dataset, Experiment, MetricsResponse, Worker } from "../types";

const BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function listExperiments(): Promise<Experiment[]> {
  const res = await fetch(`${BASE_URL}/experiments`);
  if (!res.ok) throw new Error(`Failed to list experiments: ${res.status}`);
  return res.json();
}

export async function getExperiment(id: string): Promise<Experiment> {
  const res = await fetch(`${BASE_URL}/experiments/${id}`);
  if (!res.ok) throw new Error(`Failed to get experiment: ${res.status}`);
  return res.json();
}

export async function createExperiment(spec: unknown): Promise<Experiment> {
  const res = await fetch(`${BASE_URL}/experiments`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ spec }),
  });
  if (!res.ok) {
    const detail = await res.text();
    throw new Error(detail || `Failed to create experiment: ${res.status}`);
  }
  return res.json();
}

export async function listDatasets(): Promise<Dataset[]> {
  const res = await fetch(`${BASE_URL}/datasets`);
  if (!res.ok) throw new Error(`Failed to list datasets: ${res.status}`);
  return res.json();
}

export async function listWorkers(): Promise<Worker[]> {
  const res = await fetch(`${BASE_URL}/workers`);
  if (!res.ok) throw new Error(`Failed to list workers: ${res.status}`);
  return res.json();
}

export interface DatasetLite {
  dataset_id: string;
  name: string;
  version: string;
  format: string;
}

export async function getMetrics(id: string): Promise<MetricsResponse> {
  const res = await fetch(`${BASE_URL}/experiments/${id}/metrics`);
  if (!res.ok) throw new Error(`Failed to get metrics: ${res.status}`);
  return res.json();
}

export async function listArtifacts(id: string): Promise<Artifact[]> {
  const res = await fetch(`${BASE_URL}/experiments/${id}/artifacts`);
  if (!res.ok) throw new Error(`Failed to list artifacts: ${res.status}`);
  return res.json();
}
