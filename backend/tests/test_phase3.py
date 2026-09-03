"""Tests for Phase 3: idempotent failure recording, job/worker/heartbeat, history."""
import pytest

from app.schemas.experiment import ExperimentCreate, ExperimentSpec
from app.services import (
    experiment_service,
    failure_service,
    job_service,
    transition_service,
    worker_service,
)


def valid_spec_dict() -> dict:
    return {
        "experiment": {"name": "phase3-test"},
        "dataset": {"name": "cms-run2015", "version": "v1"},
        "model": {"type": "dummy"},
        "resources": {"workers": 2, "cpu": "2", "memory": "4Gi"},
        "training": {"epochs": 2, "batch_size": 64, "learning_rate": 0.001},
        "checkpointing": {"enabled": False},
        "retry": {"max_attempts": 3},
    }


def _create_experiment(db_session, registered_dataset, workers: int = 1):
    spec = valid_spec_dict()
    spec["resources"]["workers"] = workers
    exp = experiment_service.create_experiment(
        db_session, ExperimentCreate(spec=ExperimentSpec(**spec))
    )
    job = job_service.create_job_for_experiment(db_session, exp, worker_count=workers)
    return exp, job


def test_idempotent_failure_recording(db_session, registered_dataset):
    exp, job = _create_experiment(db_session, registered_dataset)
    worker_service.register_worker(db_session, "w1", job.job_id, container_id="c1")
    f1 = failure_service.record_failure(
        db_session, job.job_id, "container_crash", worker_id="w1", error_message="boom"
    )
    # Same incident detected again -> returns existing, does not duplicate.
    f2 = failure_service.record_failure(
        db_session, job.job_id, "container_crash", worker_id="w1", error_message="boom"
    )
    assert f1.failure_id == f2.failure_id
    assert len(failure_service.list_for_job(db_session, job.job_id)) == 1


def test_distinct_workers_record_distinct_failures(db_session, registered_dataset):
    exp, job = _create_experiment(db_session, registered_dataset, workers=2)
    worker_service.register_worker(db_session, "w1", job.job_id, container_id="c1")
    worker_service.register_worker(db_session, "w2", job.job_id, container_id="c2")
    failure_service.record_failure(db_session, job.job_id, "container_crash", worker_id="w1")
    failure_service.record_failure(db_session, job.job_id, "container_crash", worker_id="w2")
    assert len(failure_service.list_for_job(db_session, job.job_id)) == 2


def test_retry_count_increment(db_session, registered_dataset):
    exp, job = _create_experiment(db_session, registered_dataset)
    assert job.retry_count == 0
    job_service.increment_retry(db_session, job.job_id)
    job_service.increment_retry(db_session, job.job_id)
    assert job_service.get_job(db_session, job.job_id).retry_count == 2


def test_heartbeat_updates_timestamp(db_session, registered_dataset):
    exp, job = _create_experiment(db_session, registered_dataset)
    worker = worker_service.register_worker(db_session, "wrk-1", job.job_id, container_id="c1")
    assert worker.heartbeat_time is None
    worker_service.heartbeat(db_session, "wrk-1")
    assert worker_service.get_worker(db_session, "wrk-1").heartbeat_time is not None


def test_transition_history_appended(db_session, registered_dataset):
    exp, job = _create_experiment(db_session, registered_dataset)
    experiment_service.transition(db_session, exp.id, "SCHEDULING")
    experiment_service.transition(db_session, exp.id, "RUNNING")
    history = transition_service.list_transitions(db_session, exp.id)
    assert [h.to_status for h in history] == ["SCHEDULING", "RUNNING"]


def test_job_status_lifecycle(db_session, registered_dataset):
    exp, job = _create_experiment(db_session, registered_dataset)
    job_service.set_status(db_session, job.job_id, "SCHEDULING")
    job_service.set_status(db_session, job.job_id, "COMPLETED")
    j = job_service.get_job(db_session, job.job_id)
    assert j.status == "COMPLETED"
    assert j.completed_at is not None


def test_invalid_transition_is_rejected(db_session, registered_dataset):
    exp, _ = _create_experiment(db_session, registered_dataset)
    with pytest.raises(experiment_service.InvalidTransitionError):
        experiment_service.transition(db_session, exp.id, "RUNNING")


def test_retry_exhaustion_is_not_retryable():
    assert experiment_service.can_transition("RUNNING", "RETRYING")
    assert not experiment_service.can_transition("COMPLETED", "RETRYING")
