import { Artifact, Dataset, Experiment, MetricsResponse, Transition, Worker } from "../types";

const BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function getJson<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, { cache: "no-store" });
  if (!res.ok) throw new Error(`Request failed: ${res.status}`);
  return res.json();
}

async function postJson<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const detail = await res.text();
    throw new Error(detail || `Request failed: ${res.status}`);
  }
  return res.json();
}

async function deleteReq(path: string): Promise<void> {
  const res = await fetch(`${BASE_URL}${path}`, { method: "DELETE" });
  if (!res.ok) {
    const detail = await res.text();
    throw new Error(detail || `Request failed: ${res.status}`);
  }
}

export async function listExperiments(): Promise<Experiment[]> {
  return getJson<Experiment[]>("/experiments");
}

export async function getExperiment(id: string): Promise<Experiment> {
  return getJson<Experiment>(`/experiments/${id}`);
}

export async function createExperiment(spec: unknown): Promise<Experiment> {
  return postJson<Experiment>("/experiments", { spec });
}

export async function cancelExperiment(id: string): Promise<Experiment> {
  return postJson<Experiment>(`/experiments/${id}/cancel`, {});
}

export async function getHistory(id: string): Promise<Transition[]> {
  return getJson<Transition[]>(`/experiments/${id}/history`);
}

export async function listDatasets(): Promise<Dataset[]> {
  return getJson<Dataset[]>("/datasets");
}

export async function registerDataset(payload: unknown): Promise<Dataset> {
  return postJson<Dataset>("/datasets", payload);
}

export async function listWorkers(): Promise<Worker[]> {
  return getJson<Worker[]>("/workers");
}

export async function getMetrics(id: string): Promise<MetricsResponse> {
  return getJson<MetricsResponse>(`/experiments/${id}/metrics`);
}

export async function listArtifacts(id: string): Promise<Artifact[]> {
  return getJson<Artifact[]>(`/experiments/${id}/artifacts`);
}

export async function deleteDataset(id: string): Promise<void> {
  return deleteReq(`/datasets/${id}`);
}
