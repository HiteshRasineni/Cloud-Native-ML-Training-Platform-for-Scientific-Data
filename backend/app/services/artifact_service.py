"""Artifact business logic."""
from sqlalchemy.orm import Session

from app.models.dataset import Artifact


def record_artifact(db: Session, experiment_id: str, payload: dict) -> Artifact:
    art = Artifact(experiment_id=experiment_id, **payload)
    db.add(art)
    db.commit()
    db.refresh(art)
    return art


def list_artifacts(db: Session, experiment_id: str) -> list[Artifact]:
    return (
        db.query(Artifact)
        .filter(Artifact.experiment_id == experiment_id)
        .order_by(Artifact.created_at)
        .all()
    )
