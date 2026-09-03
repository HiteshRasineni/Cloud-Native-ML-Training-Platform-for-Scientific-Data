export interface ExperimentSpec {
  experiment: { name: string };
  dataset: { name: string; version: string };
  model: { type: string };
  resources: { workers: number; cpu: string; memory: string };
  training: { epochs: number; batch_size: number; learning_rate: number };
  checkpointing: { enabled: boolean };
  retry: { max_attempts: number };
}

export interface Experiment {
  id: string;
  name: string;
  status: "QUEUED" | "SCHEDULING" | "RUNNING" | "COMPLETED" | "FAILED";
  attempts: number;
  error_message: string | null;
  spec: ExperimentSpec;
}
