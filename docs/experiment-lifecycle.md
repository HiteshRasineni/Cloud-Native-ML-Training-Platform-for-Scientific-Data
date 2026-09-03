# Experiment lifecycle

`POST /experiments` validates and stores the experiment, creates one `Job` row with the requested `resources.workers`, and queues the job in Redis. The scheduler records each launch attempt as a separate `Worker` row and passes its generated `WORKER_ID` to the local Docker container.

The enforced experiment transitions are:

`CREATED -> VALIDATING -> VALIDATED -> QUEUED -> SCHEDULING -> RUNNING -> CHECKPOINTING -> COMPLETED`

`RUNNING -> RETRYING -> SCHEDULING` is used when a retryable worker fails. Any terminal failure ends in `FAILED`. Every accepted transition is appended to `experiment_transitions` and is available from `GET /experiments/{id}/history`; invalid transitions are rejected by the scheduler state machine.

The job is completed only after all worker rows are `COMPLETED`. A retry creates new worker rows only for failed workers; successful workers are retained. The backend exposes aggregate job data, per-worker status, and failures from `GET /experiments/{id}`.

Workers send independent heartbeats to `POST /workers/{id}/heartbeat` at `HEARTBEAT_INTERVAL_SECONDS` (default 10 seconds). The scheduler heartbeat monitor scans every `HEARTBEAT_SCAN_INTERVAL_SECONDS` (default 10) and marks workers without a heartbeat for `HEARTBEAT_TIMEOUT_SECONDS` (default 30) as failed.
# Experiment lifecycle

1. Submit spec (YAML/JSON) via `POST /experiments` � validated by Pydantic schemas.
2. Backend persists to PostgreSQL (`experiments` table, Alembic-managed) with status `QUEUED` and pushes `{experiment_id, spec}` to the Redis list `experiments:queued`.
3. Scheduler pops the job: `QUEUED -> SCHEDULING`, launches a worker container via `LocalDockerExecutor` with `EXPERIMENT_ID`/`EXPERIMENT_SPEC` env vars, then `SCHEDULING -> RUNNING`.
4. Worker runs the workload, publishing per-epoch metrics to `experiment:<id>:progress` in Redis.
5. On container exit, scheduler sets `COMPLETED` or `FAILED` (with retry per `retry.max_attempts`; a retry requeues to `QUEUED` and increments `attempts`).
