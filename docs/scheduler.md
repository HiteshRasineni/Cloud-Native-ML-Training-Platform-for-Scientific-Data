# Scheduler

- `app/queue_consumer.py` — main loop: BLPOP from Redis, drives the lifecycle.
- `app/state_machine.py` — allowed transitions: QUEUED?SCHEDULING?RUNNING?COMPLETED/FAILED; FAILED?QUEUED for retries.
- `app/retry_policy.py` — retries until `retry.max_attempts` is exhausted.
- `executors/base.py` — `Executor` interface (`launch`/`poll`/`cleanup`); `executors/local/` implements it with the Docker SDK; `executors/kubernetes/` will implement it in a later phase without changing the consumer.
- `app/heartbeat_monitor.py` — stub for worker liveness tracking (later phase).
