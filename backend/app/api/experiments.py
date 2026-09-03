"""Experiment API routes. Business logic lives in services/."""
import os

import httpx
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.core.metrics import experiments_submitted_total
from app.schemas.dataset import ArtifactCreate, ArtifactOut
from app.schemas.experiment import ExperimentCreate, ExperimentOut
from app.schemas.failure import FailureOut
from app.schemas.job import JobOut
from app.schemas.transition import TransitionOut
from app.schemas.worker import WorkerOut
from app.services import (
    artifact_service,
    dataset_service,
    experiment_service,
    failure_service,
    job_service,
    queue_service,
    transition_service,
    worker_service,
)

router = APIRouter(prefix="/experiments", tags=["experiments"])

MLFLOW_TRACKING_URI = os.getenv("MLFLOW_TRACKING_URI", "http://mlflow:5000")
MLFLOW_RUN_TAG = "platform_experiment_id"


def _enrich(exp: object, db: Session) -> ExperimentOut:
    """Attach the job, worker rows and failures to an ExperimentOut."""
    out = ExperimentOut.model_validate(exp)
    job = job_service.get_job_for_experiment(db, exp.id)
    if job is not None:
        out.job = JobOut.model_validate(job)
        out.workers = [
            WorkerOut.model_validate(w) for w in worker_service.list_workers_for_job(db, job.job_id)
        ]
        out.failures = [
            FailureOut.model_validate(f) for f in failure_service.list_for_job(db, job.job_id)
        ]
    return out


@router.post("", response_model=ExperimentOut, status_code=201)
def create_experiment(payload: ExperimentCreate, db: Session = Depends(get_db)) -> ExperimentOut:
    try:
        exp = experiment_service.create_experiment(db, payload)
    except dataset_service.DatasetNotFoundError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    job = job_service.create_job_for_experiment(
        db, exp, worker_count=payload.spec.resources.workers
    )
    experiments_submitted_total.inc()
    queue_service.enqueue_experiment(exp.id, job.job_id, exp.spec)
    return _enrich(exp, db)


@router.get("", response_model=list[ExperimentOut])
def list_experiments(db: Session = Depends(get_db)) -> list[ExperimentOut]:
    return [_enrich(e, db) for e in experiment_service.list_experiments(db)]


@router.get("/{experiment_id}", response_model=ExperimentOut)
def get_experiment(experiment_id: str, db: Session = Depends(get_db)) -> ExperimentOut:
    exp = experiment_service.get_experiment(db, experiment_id)
    if exp is None:
        raise HTTPException(status_code=404, detail="Experiment not found")
    return _enrich(exp, db)


@router.get("/{experiment_id}/history", response_model=list[TransitionOut])
def get_history(experiment_id: str, db: Session = Depends(get_db)) -> list[TransitionOut]:
    if experiment_service.get_experiment(db, experiment_id) is None:
        raise HTTPException(status_code=404, detail="Experiment not found")
    return [
        TransitionOut.model_validate(t)
        for t in transition_service.list_transitions(db, experiment_id)
    ]


@router.post("/{experiment_id}/artifacts", response_model=ArtifactOut, status_code=201)
def record_artifact(
    experiment_id: str, payload: ArtifactCreate, db: Session = Depends(get_db)
) -> ArtifactOut:
    if experiment_service.get_experiment(db, experiment_id) is None:
        raise HTTPException(status_code=404, detail="Experiment not found")
    art = artifact_service.record_artifact(db, experiment_id, payload.model_dump(exclude_none=True))
    return ArtifactOut.model_validate(art)


@router.get("/{experiment_id}/artifacts", response_model=list[ArtifactOut])
def list_artifacts(experiment_id: str, db: Session = Depends(get_db)) -> list[ArtifactOut]:
    return [
        ArtifactOut.model_validate(a)
        for a in artifact_service.list_artifacts(db, experiment_id)
    ]


@router.get("/{experiment_id}/metrics")
def get_metrics(experiment_id: str, db: Session = Depends(get_db)) -> dict:
    """Proxy to MLflow: per-epoch metric history for the experiment's run.

    The frontend never talks to MLflow directly; Postgres stays the source of
    truth for lifecycle state and MLflow owns ML metrics.
    """
    if experiment_service.get_experiment(db, experiment_id) is None:
        raise HTTPException(status_code=404, detail="Experiment not found")

    filter_str = f"tags.{MLFLOW_RUN_TAG} = '{experiment_id}'"
    with httpx.Client(timeout=10.0) as client:
        exps = client.get(
            f"{MLFLOW_TRACKING_URI}/api/2.0/mlflow/experiments/search",
            params={"max_results": 100},
        )
        exps.raise_for_status()
        experiment_ids = [e["experiment_id"] for e in exps.json().get("experiments", [])]
        if not experiment_ids:
            return {"run_id": None, "metrics": {}}

        search = client.post(
            f"{MLFLOW_TRACKING_URI}/api/2.0/mlflow/runs/search",
            json={"experiment_ids": experiment_ids, "filter": filter_str, "max_results": 1},
        )
        search.raise_for_status()
        runs = search.json().get("runs", [])
        if not runs:
            return {"run_id": None, "metrics": {}}
        run_id = runs[0]["info"]["run_id"]

        metrics: dict[str, list[dict]] = {}
        for key in ("loss", "epoch"):
            hist = client.get(
                f"{MLFLOW_TRACKING_URI}/api/2.0/mlflow/metrics/get-history",
                params={"run_id": run_id, "metric_key": key, "max_results": 10000},
            )
            if hist.status_code == 200:
                points = hist.json().get("metrics", [])
                metrics[key] = [{"step": p.get("step"), "value": p.get("value")} for p in points]
    return {"run_id": run_id, "metrics": metrics}
