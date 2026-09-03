"""Dataset API routes. Business logic lives in services/."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.dataset import DatasetCreate, DatasetOut
from app.services import dataset_service

router = APIRouter(prefix="/datasets", tags=["datasets"])


@router.post("", response_model=DatasetOut, status_code=201)
def register_dataset(payload: DatasetCreate, db: Session = Depends(get_db)) -> DatasetOut:
    try:
        ds = dataset_service.register_dataset(db, payload.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    return DatasetOut.model_validate(ds)


@router.get("", response_model=list[DatasetOut])
def list_datasets(db: Session = Depends(get_db)) -> list[DatasetOut]:
    return [DatasetOut.model_validate(d) for d in dataset_service.list_datasets(db)]


@router.get("/{dataset_id}", response_model=DatasetOut)
def get_dataset(dataset_id: str, db: Session = Depends(get_db)) -> DatasetOut:
    ds = dataset_service.get_dataset(db, dataset_id)
    if ds is None:
        raise HTTPException(status_code=404, detail="Dataset not found")
    return DatasetOut.model_validate(ds)
