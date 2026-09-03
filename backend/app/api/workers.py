"""Worker API routes (list/detail/heartbeat). Heartbeat is internal, not frontend-facing."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.worker import HeartbeatResponse, WorkerOut
from app.services import failure_service, worker_service

router = APIRouter(prefix="/workers", tags=["workers"])


@router.get("", response_model=list[WorkerOut])
def list_workers(db: Session = Depends(get_db)) -> list[WorkerOut]:
    out = []
    for w in worker_service.list_workers(db):
        obj = WorkerOut.model_validate(w)
        obj.failures = failure_service.list_for_worker(db, w.worker_id)
        out.append(obj)
    return out


@router.get("/{worker_id}", response_model=WorkerOut)
def get_worker(worker_id: str, db: Session = Depends(get_db)) -> WorkerOut:
    w = worker_service.get_worker(db, worker_id)
    if w is None:
        raise HTTPException(status_code=404, detail="Worker not found")
    obj = WorkerOut.model_validate(w)
    obj.failures = failure_service.list_for_worker(db, worker_id)
    return obj


@router.post("/{worker_id}/heartbeat", response_model=HeartbeatResponse)
def heartbeat(worker_id: str, db: Session = Depends(get_db)) -> HeartbeatResponse:
    """Internal: called by the worker itself on a background thread."""
    w = worker_service.heartbeat(db, worker_id)
    if w is None:
        raise HTTPException(status_code=404, detail="Worker not found")
    return HeartbeatResponse(worker_id=worker_id, status=w.status)
