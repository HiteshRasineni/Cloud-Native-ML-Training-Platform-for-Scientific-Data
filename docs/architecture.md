# Architecture

## Components (Phase 4)

- **backend** - FastAPI. Validates experiment specs, resolves dataset references (`name:version`) against the `datasets` table, persists experiments (PostgreSQL, Alembic-managed), enqueues jobs on Redis, and records artifacts. Also proxies MLflow metrics to the frontend (`GET /experiments/{id}/metrics`) so the frontend never talks to MLflow directly. Exposes `POST /datasets`, `GET /datasets`, `GET /datasets/{id}`.
- **scheduler** - Redis consumer + lifecycle state machine. Remains workload-agnostic: it only launches worker containers, polls exit codes, and drives `QUEUED -> SCHEDULING -> RUNNING -> COMPLETED/FAILED` (with retries). Executors sit behind the `Executor` interface (local Docker now, Kubernetes later). It passes MinIO/S3 + MLflow env vars to launched workers.
- **worker** - Training containers. A workload registry maps `model.type` to a `Workload` implementation: `dummy` (no-op) and `normalizing-flow` (from-scratch RealNVP-style coupling flow in PyTorch, architecture params from the spec, never hardcoded). The worker downloads the resolved dataset from MinIO, trains, reports per-epoch metrics to MLflow + Redis, uploads checkpoints to MinIO via `runtime/checkpoint.py`, and records artifacts through the backend API.
- **frontend** - Next.js/TypeScript: registered-dataset list, dataset picker in the experiment form, experiment table, worker monitoring, and experiment detail pages. It links to the provisioned Grafana overview.
- **observability** - Prometheus scrapes the backend (`:8000/metrics`), scheduler (`:8001/metrics`), Pushgateway, and cAdvisor. Grafana (`:3001`) is provisioned from the repository dashboard JSON files. Workers push metrics to Pushgateway because their containers are short-lived; cAdvisor supplies per-container CPU and memory metrics.

## Data stores (responsibility separation)

| Store | Owns | Never stores |
|---|---|---|
| PostgreSQL | Experiment lifecycle + scheduling metadata, dataset registry, artifact index (source of truth for state) | ML metrics/params |
| MLflow (SQLite backend, docker volume) | ML params, per-epoch metrics, final model artifact | lifecycle state |
| MinIO | Datasets, checkpoints, model artifacts, logs (`experiments/{id}/{config,checkpoints,metrics,artifacts,logs}/`, `datasets/...`) | relational state |

The MLflow service uses SQLite for its backend store (simple, self-contained for single-node Phase 2; swap the URI to Postgres later without worker changes) and pushes its artifacts to the `mlflow` MinIO bucket. PostgreSQL never holds ML metrics; MLflow never holds lifecycle state.

## Dataset flow

1. `POST /datasets` registers a dataset (name, version, format, storage_location = MinIO URI, metadata, size, checksum).
2. `POST /experiments` references the dataset logically as `name:version`; the backend resolves it against the `datasets` table and embeds the resolved `storage_location` into the stored spec. Unregistered datasets are rejected with a 400.
3. The worker downloads from `storage_location` (a MinIO URI), never from a raw path.

## MinIO object layout

```
datasets/<name>/<version>/data.parquet
experiments/<experiment_id>/config/
experiments/<experiment_id>/checkpoints/epoch_<n>.pt
experiments/<experiment_id>/metrics/
experiments/<experiment_id>/artifacts/
experiments/<experiment_id>/logs/
```

## Sampling/running

- `make sample-dataset` generates `datasets/sample/cms-run2015_v1.parquet` (deterministic seed, ~5000 synthetic HEP-like rows: pt/eta/phi/energy/label).
- `make register-sample-dataset` uploads it to MinIO (`datasets/cms-run2015/v1/data.parquet`) and registers it via the backend as `cms-run2015:v1`.

## MLflow integration

Each worker run starts an MLflow run tagged with the platform experiment id. It logs training/architecture hyperparameters, per-epoch `loss` metrics, and the final model as an MLflow artifact. The frontend only ever reads metrics through the backend proxy endpoint.

## Phase 5 Kubernetes path

The scheduler selects `EXECUTOR_BACKEND=local` by default for Compose or `kubernetes` for a cluster. The Kubernetes executor creates an indexed `batch/v1 Job`, mounts a per-job ConfigMap containing the non-trivial experiment spec, and maps Pod phases back into the existing Job/Worker lifecycle. Its ServiceAccount is limited to managing Jobs, Pods, and ConfigMaps in the platform namespace. Heartbeats, failure classification, retry policy, Prometheus metrics, and Grafana dashboards are shared with the Compose path.

The deployment progression is:

```text
Local Docker Compose -> Containerized Services -> Kubernetes Deployment -> Distributed Job Execution
```

Compose does not import or require Kubernetes; the official client is installed only in the scheduler image and selected at startup through configuration.
