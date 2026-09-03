"""Transition-history service: append + list per experiment."""
from sqlalchemy.orm import Session

from app.models.transition import ExperimentTransition


def append_transition(db: Session, experiment_id: str, from_status: str | None, to_status: str,
                      message: str | None = None) -> ExperimentTransition:
    tr = ExperimentTransition(
        experiment_id=experiment_id, from_status=from_status, to_status=to_status, message=message
    )
    db.add(tr)
    db.commit()
    db.refresh(tr)
    return tr


def list_transitions(db: Session, experiment_id: str) -> list[ExperimentTransition]:
    return (
        db.query(ExperimentTransition)
        .filter(ExperimentTransition.experiment_id == experiment_id)
        .order_by(ExperimentTransition.created_at)
        .all()
    )
