"""Dataset business logic: registration, lookup, and name:version resolution."""
from sqlalchemy.orm import Session

from app.models.dataset import Dataset


class DatasetNotFoundError(Exception):
    """Raised when a dataset reference (name:version) cannot be resolved."""


def dataset_uri(name: str, version: str) -> str:
    """Logical identifier for a dataset: name:version (never a raw path)."""
    return f"{name}:{version}"


def parse_dataset_uri(uri: str) -> tuple[str, str]:
    """Parse 'name:version' into (name, version). Raises ValueError if malformed."""
    if uri.count(":") != 1 or not uri.split(":")[0] or not uri.split(":")[1]:
        raise ValueError(f"Invalid dataset reference {uri!r}; expected 'name:version'")
    name, version = uri.split(":")
    return name, version


def register_dataset(db: Session, payload: dict) -> Dataset:
    existing = db.query(Dataset).filter(
        Dataset.name == payload["name"], Dataset.version == payload["version"]
    ).first()
    if existing is not None:
        raise ValueError(f"Dataset {dataset_uri(payload['name'], payload['version'])} is already registered")
    fields = {k: v for k, v in payload.items() if k != "metadata"}
    ds = Dataset(meta=payload.get("metadata", {}), **fields)
    db.add(ds)
    db.commit()
    db.refresh(ds)
    return ds


def list_datasets(db: Session) -> list[Dataset]:
    return db.query(Dataset).order_by(Dataset.created_at.desc()).all()


def get_dataset(db: Session, dataset_id: str) -> Dataset | None:
    return db.get(Dataset, dataset_id)


def resolve(db: Session, name: str, version: str) -> Dataset:
    """Resolve name:version to the registered Dataset (raises if missing)."""
    ds = (
        db.query(Dataset)
        .filter(Dataset.name == name, Dataset.version == version)
        .first()
    )
    if ds is None:
        raise DatasetNotFoundError(
            f"Dataset {dataset_uri(name, version)} is not registered. "
            "Register it first via POST /datasets."
        )
    return ds
