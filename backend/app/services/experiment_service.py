"""Experiment business logic: persistence + state transitions."""
from typing import Any

from sqlalchemy.orm import Session

from app.models.experiment import VALID_TRANSITIONS, Experiment, ExperimentStatus
from app.schemas.experiment import ExperimentCreate


class InvalidTransitionError(Exception):
    """Raised when a state transition is not allowed."""


def can_transition(current: str, new: str) -> bool:
    return new in VALID_TRANSITIONS.get(current, set())


def create_experiment(db: Session, payload: ExperimentCreate) -> Experiment:
    """Validate + persist. Resolves the dataset reference (name:version) to a
    registered Dataset and embeds its storage_location in the stored spec so
    workers never deal with logical identifiers they cannot resolve."""
    from app.services import dataset_service

    ds = dataset_service.resolve(db, payload.spec.dataset.name, payload.spec.dataset.version)
    spec = payload.spec.model_dump()
    spec["dataset"]["storage_location"] = ds.storage_location
    exp = Experiment(
        name=payload.spec.experiment.name,
        status=ExperimentStatus.QUEUED,
        spec=spec,
        checkpointing_enabled=payload.spec.checkpointing.enabled,
    )
    db.add(exp)
    db.commit()
    db.refresh(exp)
    return exp


def list_experiments(db: Session) -> list[Experiment]:
    return db.query(Experiment).order_by(Experiment.created_at.desc()).all()


def get_experiment(db: Session, experiment_id: str) -> Experiment | None:
    return db.get(Experiment, experiment_id)


def transition(db: Session, experiment_id: str, new_status: str, error_message: str | None = None) -> Experiment | None:
    from app.services import transition_service

    exp = get_experiment(db, experiment_id)
    if exp is None:
        return None
    old_status = exp.status
    if not can_transition(old_status, new_status):
        raise InvalidTransitionError(
            f"Invalid transition {old_status} -> {new_status} for experiment {experiment_id}"
        )
    exp.status = new_status
    exp.error_message = error_message
    if new_status == ExperimentStatus.QUEUED:
        exp.attempts += 1
    db.commit()
    db.refresh(exp)
    transition_service.append_transition(db, experiment_id, old_status, new_status, error_message)
    return exp
