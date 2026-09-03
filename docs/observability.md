# Observability

Phase 4 uses direct Prometheus scraping for long-running services and Pushgateway for short-lived workers. Prometheus scrapes every five seconds. Grafana is available at `http://localhost:3001`; its datasource and dashboards are provisioned from `infrastructure/grafana/`.

## Metrics

| Metric | Meaning | Dashboard use |
| --- | --- | --- |
| `http_requests_total{method,handler,status}` | API response count by method, route template, and status | Platform Overview request rate and status pie |
| `http_request_duration_seconds{handler}` | API request duration histogram | Platform Overview p95 latency |
| `http_errors_total{path,status_code}` | API responses with status 400 or higher | Platform Overview error rate |
| `experiments_submitted_total` | Experiments accepted by the API | Experiment Activity submissions |
| `scheduler_jobs_queued` | Current Redis queue depth | Scheduler State queued series |
| `scheduler_jobs_running` | Jobs currently being polled | Scheduler State running series |
| `scheduler_jobs_completed_total` | Terminal successful jobs | Scheduler State completed rate |
| `scheduler_jobs_failed_total` | Terminal failed jobs | Scheduler State failed rate |
| `scheduler_job_retries_total{error_type}` | Retry events classified by failure type | Scheduler State retry series |
| `scheduler_job_duration_seconds` | Scheduling-to-terminal job duration histogram | Scheduler State average duration and Experiment Activity time-to-completion |
| `worker_active{job,worker_id}` | 1 while a worker is active, 0 on normal exit | Worker Health active workers |
| `worker_failures_total{error_type}` | Workload-side failures | Worker Health failure series |
| `worker_heartbeat_failures_total` | Failed heartbeat sends | Worker Health heartbeat failure rate |
| `worker_training_epoch_duration_seconds` | Training time per epoch | Experiment Activity average and p95 epoch duration |
| `container_cpu_usage_seconds_total{container_label_platform_worker_id}` | cAdvisor CPU usage for labeled worker containers | Worker Health per-worker CPU |
| `container_memory_working_set_bytes{container_label_platform_worker_id}` | cAdvisor working-set memory for worker containers | Worker Health per-worker memory |

The backend uses `prometheus-fastapi-instrumentator` for request counters and duration histograms, plus a small middleware counter for errors. Scheduler metrics are updated at queue consumption, lifecycle terminal transitions, and retry decisions. Worker metrics are pushed at activation, each heartbeat interval, failure, and exit.

## Manual verification

Start the observability stack with `docker compose up -d --build`. Open `http://localhost:9090/targets` and confirm backend, scheduler, pushgateway, and cAdvisor are up. Open Grafana at `http://localhost:3001`; the four dashboards are under the `Cloud ML Platform` folder.

Submit several experiments through the frontend or `POST /experiments`, including one with an invalid training configuration to produce a retry/failure. Within a few scrape intervals, verify request rate and errors in Platform Overview, retry and duration changes in Scheduler State, active/failure/heartbeat and container resource series in Worker Health, and submitted/completion/epoch timing in Experiment Activity.