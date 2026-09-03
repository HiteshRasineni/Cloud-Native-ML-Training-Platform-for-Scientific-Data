"""Tests for experiment spec validation and state transition logic."""
import pytest

from app.schemas.experiment import ExperimentCreate, ExperimentSpec
from app.services import experiment_service

def valid_spec_dict() -> dict:
    return {
        "experiment": {"name": "cms-normalizing-flow-study"},
        "dataset": {"name": "cms-run2015", "version": "v1"},
        "model": {"type": "normalizing-flow"},
        "resources": {"workers": 1, "cpu": "2", "memory": "4Gi"},
        "training": {"epochs": 10, "batch_size": 64, "learning_rate": 0.0001},
        "checkpointing": {"enabled": False, "interval": 1},
        "retry": {"max_attempts": 3},
    }


# ---------- Spec validation ----------


def test_valid_spec_parses():
    spec = ExperimentSpec(**valid_spec_dict())
    assert spec.experiment.name == "cms-normalizing-flow-study"
    assert spec.resources.memory == "4Gi"
    assert spec.training.epochs == 10
    assert spec.model.architecture == {}


def test_invalid_memory_unit_rejected():
    bad = valid_spec_dict()
    bad["resources"]["memory"] = "4TB"
    with pytest.raises(ValueError):
        ExperimentSpec(**bad)


def test_invalid_model_type_rejected():
    bad = valid_spec_dict()
    bad["model"]["type"] = "gpt-99"
    with pytest.raises(ValueError):
        ExperimentSpec(**bad)


def test_negative_epochs_rejected():
    bad = valid_spec_dict()
    bad["training"]["epochs"] = 0
    with pytest.raises(ValueError):
        ExperimentSpec(**bad)


# ---------- State transitions ----------


def test_create_experiment_defaults_to_queued(db_session, registered_dataset):
    exp = experiment_service.create_experiment(db_session, ExperimentCreate(spec=ExperimentSpec(**valid_spec_dict())))
    assert exp.id
    assert exp.status == "QUEUED"
    assert exp.attempts == 0


def test_happy_path_transitions(db_session, registered_dataset):
    exp = experiment_service.create_experiment(db_session, ExperimentCreate(spec=ExperimentSpec(**valid_spec_dict())))
    for status in ("SCHEDULING", "RUNNING", "COMPLETED"):
        experiment_service.transition(db_session, exp.id, status)
    assert experiment_service.get_experiment(db_session, exp.id).status == "COMPLETED"


def test_invalid_transition_raises(db_session, registered_dataset):
    exp = experiment_service.create_experiment(db_session, ExperimentCreate(spec=ExperimentSpec(**valid_spec_dict())))
    with pytest.raises(experiment_service.InvalidTransitionError):
        experiment_service.transition(db_session, exp.id, "COMPLETED")


def test_can_transition_table():
    from app.models.experiment import ExperimentStatus as S

    assert experiment_service.can_transition(S.CREATED, S.VALIDATING)
    assert experiment_service.can_transition(S.VALIDATING, S.VALIDATED)
    assert experiment_service.can_transition(S.VALIDATED, S.QUEUED)
    assert experiment_service.can_transition(S.QUEUED, S.SCHEDULING)
    assert not experiment_service.can_transition(S.COMPLETED, S.RUNNING)
    assert experiment_service.can_transition(S.RUNNING, S.RETRYING)  # worker failed -> retry
    assert experiment_service.can_transition(S.RETRYING, S.SCHEDULING)  # relaunch
    assert experiment_service.can_transition(S.FAILED, S.RETRYING)
