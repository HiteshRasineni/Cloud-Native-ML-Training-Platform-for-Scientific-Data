# cloud-ml-platform

Cloud-native machine learning training platform for scientific workloads, demonstrated end-to-end on a synthetic high-energy-physics (HEP) dataset. Scientific ML carries the same production requirements as any other cloud-native system: reproducibility, failure recovery, and observability. A run must be reproducible, survive worker failures, and stay observable while it runs. This platform implements that discipline: a real model trains against object storage while its lifecycle, failures, and metrics flow through production-grade machinery. It is not a notebook wired to a GPU.

## Scope and isolation

- Scheduling, retries, heartbeats, failure recovery, and observability are generic, workload-agnostic machinery.
- HEP workload code lives only in `worker/workloads/normalizing_flow/`, behind the `Workload` interface.
- The scheduler, backend, and frontend never reference physics, tensor shapes, or training internals. Any registered workload runs without pipeline changes.

## Architecture

```text
Frontend (Next.js/TS, :3000)
   |  experiment form / dataset picker / workers / experiment detail
   v  REST
Backend (FastAPI, :8000)
   |  spec validation / dataset resolution / lifecycle persistence / queueing /
   |  artifact+transition records / MLflow metrics proxy
   +----> Postgres (lifecycle state)
   +----> Redis (queue / progress)
   +----> MLflow (:5000, experiment tracking)
   v
Scheduler (:8001)
   |  Redis consumer / state machine / failure classification / retry policy /
   |  heartbeat monitor / pluggable executor
   +---- EXECUTOR_BACKEND=local ------> LocalDockerExecutor ----> worker containers
   +---- EXECUTOR_BACKEND=kubernetes -> KubernetesExecutor ----> indexed batch/v1 Job,
   |                                                   one Pod per worker, per-job ConfigMap
   v
Worker (training-worker image)
   |  load dataset from MinIO / train / checkpoints to MinIO /
   |  per-epoch metrics to MLflow / metrics to Pushgateway /
   |  heartbeats to POST /workers/{id}/heartbeat
   v
MinIO (objects) + MLflow (tracking) + Pushgateway
   v
Prometheus (:9090) ----> Grafana (:3001, 4 provisioned dashboards)
```

## Technology stack

| Layer | Technology |
| --- | --- |
| Frontend | Next.js (React, TypeScript) |
| Backend | FastAPI, SQLAlchemy, Pydantic, Alembic, prometheus-fastapi-instrumentator |
| Scheduler | Python, Redis consumer, pluggable executors |
| Worker | Python, PyTorch (normalizing flow), Pandas/PyArrow, MLflow client |
| Database | PostgreSQL 16 (experiment lifecycle state) |
| Object storage | MinIO (S3-compatible) |
| Experiment tracking | MLflow (SQLite backend store, artifacts in MinIO) |
| Message queue | Redis (experiment/job queue, worker progress) |
| Metrics | Prometheus, Pushgateway, cAdvisor |
| Dashboards | Grafana (provisioned from repository dashboards) |
| Orchestration, local | Docker Compose, `LocalDockerExecutor` |
| Orchestration, cluster | Kubernetes, `KubernetesExecutor` (kind or minikube) |

## System components

| Component | Responsibility | Boundary it does not cross |
| --- | --- | --- |
| Frontend | Experiment submission, dataset picker, per-worker status, metric curves | No direct access to MLflow, Postgres, or MinIO; reads metrics only through the backend proxy |
| Backend | Spec validation, dataset resolution, lifecycle persistence, queueing, artifact/transition/failure records, MLflow metrics proxy | Never runs training code and inspects no dataset contents |
| Scheduler | Redis consumer, state machine, failure classification, retry/backoff, heartbeat monitor, pluggable executor | No knowledge of HEP or training internals; launches an image and enforces the lifecycle contract only |
| Worker | Loads the resolved dataset from MinIO, trains via the registered `Workload`, logs metrics, uploads checkpoints, sends heartbeats | Training parameters come from the spec, never hardcoded; executor-agnostic |
| Infrastructure | PostgreSQL (state), Redis (queue/progress), MinIO (objects), MLflow (tracking), Prometheus/Grafana/Pushgateway/cAdvisor (observability), K8s manifests | Config and secrets via ConfigMaps/Secrets; no real credentials committed |
## Local setup (Docker Compose)

Prerequisites: Docker with Compose v2 and GNU Make. The sample-data generator runs in a pinned Python container, so no local Python is required.

```bash
# clone and enter the repo
git clone <repo-url> cloud-ml-platform
cd cloud-ml-platform

# optional: copy the example env file (compose has safe defaults without it)
cp .env.example .env

# pre-build the worker image the scheduler launches on demand
docker compose build worker

# start the full stack
docker compose up --build -d

# migrations (the backend also runs alembic upgrade head on start)
docker compose exec backend alembic upgrade head
```

Register the sample dataset (`make register-sample-dataset` also generates the parquet if missing): it uploads `datasets/sample/cms-run2015_v1.parquet` to MinIO and registers `cms-run2015:v1` through the backend dataset registry.

```bash
make register-sample-dataset
```

| Service | URL |
| --- | --- |
| Frontend | http://localhost:3000 |
| API docs (Swagger) | http://localhost:8000/docs |
| Prometheus | http://localhost:9090 |
| Grafana | http://localhost:3001 |
| MLflow | http://localhost:5000 |
| MinIO console | http://localhost:9001 (`mlplatform` / `mlplatform-secret`) |

## How to submit an experiment

**Via the UI.** Open http://localhost:3000, select a registered dataset (`cms-run2015:v1`), choose `normalizing-flow`, set transforms, hidden features, and epochs, and submit. The form fills the `resources`, `training`, `checkpointing`, and `retry` blocks itself.

**Via the API.** `POST /experiments` accepts a body of `{"spec": {...}}`; the spec matches the schema below.

```bash
curl -X POST http://localhost:8000/experiments \
  -H "Content-Type: application/json" \
  -d '{
    "spec": {
      "experiment": {"name": "nf-quick-test"},
      "dataset": {"name": "cms-run2015", "version": "v1"},
      "model": {"type": "normalizing-flow", "architecture": {"transforms": 4, "hidden_features": 32}},
      "resources": {"workers": 2, "cpu": "1", "memory": "2Gi"},
      "training": {"epochs": 5, "batch_size": 128, "learning_rate": 0.001},
      "checkpointing": {"enabled": true, "interval": 1},
      "retry": {"max_attempts": 3}
    }
  }'
```

Returns `201` with the created experiment: aggregate status, job, per-worker rows, and failures. The experiment table and detail views poll `GET /experiments` and `GET /experiments/{id}`.
## Example experiment configuration

The fields below match the Pydantic schemas in `backend/app/schemas/experiment.py` exactly, including defaults and constraints. On the wire, the spec is wrapped under `spec`.

```yaml
spec:
  experiment:
    name: nf-hep-study            # str, 1-255 chars
  dataset:
    name: cms-run2015             # str; must be registered in the dataset registry
    version: v1                   # str
  model:
    type: normalizing-flow        # enum: normalizing-flow | classifier | dummy
    architecture:                 # dict, workload-specific, never hardcoded
      transforms: 4               # coupling transforms
      hidden_features: 32         # hidden units per coupling layer
  resources:
    workers: 2                    # int, 1-1024
    cpu: "1"                      # str, e.g. "1" or "500m"
    memory: 1Gi                   # str, must match ^\d+(Mi|Gi)$
  training:
    epochs: 5                     # int, 1-100000
    batch_size: 64                # int, 1-65536
    learning_rate: 0.001          # float, > 0
  checkpointing:
    enabled: true                 # bool
    interval: 1                   # int, >= 1 (save every N epochs)
  retry:
    max_attempts: 3               # int, 1-10
```

Note: the schema's `model.type` enum also allows `classifier` and `dummy`, but the worker registry implements only `normalizing-flow` and `dummy`. A spec naming an unimplemented type passes API validation and fails at run time; `dummy` is a no-op workload useful for platform testing.

## Screenshots and diagrams

Placeholders for captures from a running instance; intentionally not committed as fabricated images. Capture instructions: `docs/images/README.md`.

![Dashboard](docs/images/dashboard.png)

![Experiment Detail](docs/images/experiment-detail.png)

![Grafana Overview](docs/images/grafana-overview.png)
## Experiment lifecycle

Enforced by a single shared state machine (`scheduler/app/state_machine.py`). Every accepted transition is appended to `experiment_transitions` and exposed via `GET /experiments/{id}/history`; invalid transitions raise instead of being silently allowed.

```text
CREATED -> VALIDATING -> VALIDATED -> QUEUED -> SCHEDULING -> RUNNING -> COMPLETED
                                                       |          |
                                                       v          v
                                                     FAILED    RETRYING -> SCHEDULING
```

| State | Meaning and trigger |
| --- | --- |
| CREATED | Experiment row persisted after `POST /experiments` is accepted |
| VALIDATING | Spec validation and dataset resolution in progress |
| VALIDATED | Spec valid; dataset resolved to a MinIO storage location |
| QUEUED | Job waiting on the Redis queue (`experiments:queued`) |
| SCHEDULING | Scheduler claimed the job; the executor is launching workers |
| RUNNING | Workers active; per-epoch metrics and heartbeats flowing |
| CHECKPOINTING | A mid-run checkpoint save is in progress; returns to RUNNING |
| RETRYING | A retryable worker failure triggered backoff; the job returns to SCHEDULING |
| COMPLETED | All workers completed; terminal |
| FAILED | Non-retryable failure or retries exhausted; FAILED -> RETRYING is permitted while attempts remain |

Workers POST heartbeats to the backend's `POST /workers/{id}/heartbeat` every 10 seconds by default; the scheduler's heartbeat monitor scans every 10 seconds and marks workers silent for 30 seconds as failed (all thresholds configurable).

## Failure handling

Failures are recorded through `POST /jobs/{id}/failures` and classified by the generic classifier (`scheduler/app/failure_classifier.py`), driven by container exit signals and error-message keywords -- no HEP logic. Recording is idempotent per job and dedupe key.

| Error type | Retryable | Classification |
| --- | --- | --- |
| `container_crash` | yes | Non-zero exit or unexpected termination |
| `heartbeat_timeout` | yes | Last heartbeat older than the timeout threshold |
| `dataset_resolution_error` | no | Dataset or requested version cannot be resolved |
| `training_exception` | usually yes | Unhandled workload exception; clearly invalid config is non-retryable |
| `object_storage_unavailable` | yes | MinIO/object-storage connectivity failure |

On a retryable failure the scheduler relaunches only the failed workers with exponential backoff (2 seconds base, doubling, capped at 60 seconds), keeping successful workers and their checkpoints intact. When `retry_count` reaches `retry.max_attempts`, the experiment transitions to `FAILED`. Full logic: `docs/failure-handling.md`.
## Observability

Grafana is available at http://localhost:3001 after `docker compose up --build -d`, with the datasource and dashboards provisioned from `infrastructure/grafana/`. Prometheus scrapes the backend (`:8000/metrics`), the scheduler (`:8001/metrics`), Pushgateway, and cAdvisor. Workers push to Pushgateway because training containers are short-lived. Four dashboards are provisioned under the `Cloud ML Platform` folder:

| Dashboard | Shows |
| --- | --- |
| Platform Overview | API request rate, error rate, p95 latency |
| Scheduler State | Queue depth, running jobs, completion/failure rates, retries by error type, job duration |
| Worker Health | Per-worker active/failure/heartbeat series; cAdvisor CPU and memory for worker containers |
| Experiment Activity | Submissions, time-to-completion, per-epoch training duration |

Metric-by-metric detail: `docs/observability.md`.

## Kubernetes

One codebase, two execution backends, selected by the `EXECUTOR_BACKEND` config value (`local` by default, or `kubernetes`). The Kubernetes Python client ships only in the scheduler image; the Compose stack never requires a cluster. Docker Compose remains the default local workflow.

| Executor | Launches workers | Config delivery |
| --- | --- | --- |
| `LocalDockerExecutor` (`local`) | Docker containers via the Docker socket (`cloud-ml-platform-worker:latest`) | Environment variables |
| `KubernetesExecutor` (`kubernetes`) | Indexed `batch/v1` Job, one Pod per worker (`platform/training-worker:latest`) | Per-job ConfigMap mounted into each Pod |

Local-cluster demo (kind shown; minikube is analogous):

```bash
kind create cluster --name cloud-ml
make k8s-up                 # build images, load into kind, kubectl apply -k infrastructure/kubernetes
kubectl -n cloud-ml get pods
kubectl -n cloud-ml port-forward svc/frontend 3000:3000 &
kubectl -n cloud-ml port-forward svc/grafana 3001:3000
```

Heartbeats, failure classification, retry policy, and observability are identical across executors; only the launch mechanism changes. The implemented migration path:

```text
Local Docker Compose -> Containerized Services -> Kubernetes Deployment -> Distributed Job Execution
```

Full walk-through including minikube and teardown: `docs/deployment.md`.
## Scientific workload demonstration

- The sample dataset (`datasets/sample/`) is synthetic HEP-like event data (columns `pt`, `eta`, `phi`, `energy`, `label`), generated deterministically from a fixed seed with loosely separated signal/background populations. `make sample-dataset` generates it; `make register-sample-dataset` uploads it to MinIO as `datasets/cms-run2015/v1/data.parquet` and registers `cms-run2015:v1` through the backend dataset registry.
- The shipped workload (`worker/workloads/normalizing_flow/`) is a from-scratch RealNVP-style coupling flow in PyTorch. It downloads the resolved dataset from MinIO, trains a density model over the kinematic features, logs per-epoch loss and hyperparameters to MLflow, uploads checkpoints to MinIO under `experiments/{id}/checkpoints/`, and records artifacts through the backend API.
- Domain isolation is the point: HEP code exists only behind the `Workload` interface (`setup`, `train_epoch`, `teardown`) and the registry that maps `model.type` to a class. The scheduler and backend exchange only object URIs and a versioned spec -- no physics, tensor shapes, or Python imports cross the pipeline. A classifier or an entirely different scientific domain's workload could run unchanged at the platform layer.

## Future work (not yet implemented)

Honest extensions from the design blueprint, framed as not-yet-built rather than partially present:

- GPU scheduling -- device affinity and node selection are out of scope; resources are CPU/memory strings only.
- Authentication and authorization -- the API and UI have no auth today.
- Autoscaling -- no metric-driven worker scaling policy.
- Distributed PyTorch (DDP/torchrun) -- workers run independently; the completion index drives wiring only.
- Arbitrary workload plugins -- new workloads require a registry entry and a worker image rebuild.
- Worker nodes outside Docker and Kubernetes -- the two executors are the only launch paths.
- Managed cloud services -- the K8s manifests run Postgres/Redis/MinIO in-cluster; managed equivalents are a future profile.

## Documentation index

- `docs/architecture.md` -- components, data-store separation, object layout, dataset flow
- `docs/deployment.md` -- Compose and Kubernetes deployment, kind/minikube, port-forwards
- `docs/failure-handling.md` -- classification table, retry semantics
- `docs/observability.md` -- metric inventory, scrape/push model
- `docs/experiment-lifecycle.md` -- state machine detail, heartbeat thresholds
- `docs/scheduler.md` -- scheduler design
- `docs/images/README.md` -- how to capture the screenshot placeholders