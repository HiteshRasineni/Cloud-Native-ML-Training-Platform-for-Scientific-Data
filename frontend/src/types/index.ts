export interface Dataset {
  dataset_id: string;
  name: string;
  version: string;
  format: string;
  storage_location: string;
  metadata: Record<string, unknown>;
  size: number | null;
  checksum: string | null;
  created_at: string;
}

export interface ExperimentSpec {
  experiment: { name: string };
  dataset: { name: string; version: string };
  model: { type: string; architecture?: { transforms?: number; hidden_features?: number } };
  resources: { workers: number; cpu: string; memory: string };
  training: { epochs: number; batch_size: number; learning_rate: number };
  checkpointing: { enabled: boolean; interval: number };
  retry: { max_attempts: number };
}

export interface Experiment {
  id: string;
  name: string;
  status: "CREATED" | "VALIDATING" | "VALIDATED" | "QUEUED" | "SCHEDULING" | "RUNNING" | "CHECKPOINTING" | "RETRYING" | "COMPLETED" | "FAILED";
  attempts: number;
  error_message: string | null;
  spec: ExperimentSpec;
  job: Job | null;
  workers: Worker[];
  failures: Failure[];
}

export interface Job { job_id: string; experiment_id: string; status: string; worker_count: number; retry_count: number; }
export interface Worker { worker_id: string; job_id: string; status: string; hostname: string | null; container_id: string | null; started_at: string | null; heartbeat_time: string | null; created_at: string; failures: Failure[]; }
export interface Failure { failure_id: string; job_id: string; worker_id: string | null; error_type: string; error_message: string | null; retryable: boolean; timestamp: string; }

export interface Artifact {
  artifact_id: string;
  experiment_id: string;
  artifact_type: string;
  storage_path: string;
  epoch: number | null;
  created_at: string;
}

export interface MetricPoint {
  step: number;
  value: number;
}

export interface MetricsResponse {
  run_id: string | null;
  metrics: Record<string, MetricPoint[]>;
}
