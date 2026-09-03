"""Job API routes (internal failure-recording endpoint used by the scheduler)."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.failure import FailureCreate, FailureOut
from app.schemas.job import JobOut
from app.services import failure_service, job_service

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.post("/{job_id}/failures", response_model=FailureOut, status_code=201)
def record_failure(job_id: str, payload: FailureCreate, db: Session = Depends(get_db)) -> FailureOut:
    """Internal: scheduler records a failure (idempotent) for a job/worker."""
    if job_service.get_job(db, job_id) is None:
        raise HTTPException(status_code=404, detail="Job not found")
    failure = failure_service.record_failure(
        db,
        job_id,
        payload.error_type,
        error_message=payload.error_message,
        retryable=payload.retryable,
        worker_id=payload.worker_id,
        dedupe_key=payload.dedupe_key,
    )
    return FailureOut.model_validate(failure)


@router.get("/{job_id}", response_model=JobOut)
def get_job(job_id: str, db: Session = Depends(get_db)) -> JobOut:
    job = job_service.get_job(db, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return JobOut.model_validate(job)
