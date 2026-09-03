# Failure handling

Failures are stored in the backend through `POST /jobs/{id}/failures` and are exposed on experiment and worker responses. Recording is idempotent per job and incident dedupe key, so a container poll and heartbeat scan cannot double-count one failure.

| Error type | Retryable | Classification |
| --- | --- | --- |
| `container_crash` | yes | Non-zero exit or unexpected container termination. |
| `heartbeat_timeout` | yes | Last heartbeat is older than the configured timeout. |
| `dataset_resolution_error` | no | Dataset or requested version cannot be resolved. |
| `training_exception` | usually yes | Unhandled workload exception; an immediate, clearly invalid configuration error is treated as non-retryable. |
| `object_storage_unavailable` | yes | MinIO/object-storage connection failure. |

For a retryable worker failure, the scheduler increments `Job.retry_count` once, transitions the experiment through `RETRYING`, applies exponential backoff (2 seconds, doubling, capped at 60), and relaunches only failed workers. When `retry_count` reaches `retry.max_attempts`, the experiment becomes `FAILED` and all remaining running worker rows are marked failed. Non-retryable failures fail immediately.

Worker IDs and failure dedupe keys make repeated detection safe. Retries never recreate a completed experiment or overwrite a completed worker's checkpoint path; successful workers remain complete while replacement workers receive new IDs.
# Failure handling

Phase 1: if the worker container exits non-zero, the scheduler consults the retry policy; if attempts remain, the experiment returns to `QUEUED` and the job is re-enqueued. Once `max_attempts` is reached, status is `FAILED` with an error message. Worker crashes without exit (node loss) will be handled by the heartbeat monitor in a later phase.
