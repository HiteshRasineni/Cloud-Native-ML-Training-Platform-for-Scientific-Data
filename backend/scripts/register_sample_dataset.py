"""Register the sample HEP-like dataset in MinIO and via POST /datasets.

Runs inside the backend container:
    docker compose exec backend python scripts/register_sample_dataset.py
"""
import hashlib
import os
import sys

sys.path.insert(0, "/app")

from app.database.session import SessionLocal  # noqa: E402
from app.schemas.dataset import DatasetCreate  # noqa: E402
from app.services import dataset_service  # noqa: E402
from app.services.storage_service import split_s3_uri, upload_file  # noqa: E402

BUCKET = os.getenv("MINIO_BUCKET", "mlplatform")
LOCAL_PARQUET = os.getenv(
    "SAMPLE_PARQUET_PATH", "/datasets/sample/cms-run2015_v1.parquet"
)
OBJECT_KEY = "datasets/cms-run2015/v1/data.parquet"


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> None:
    if not os.path.exists(LOCAL_PARQUET):
        print(f"Sample parquet not found at {LOCAL_PARQUET}; run `make sample-dataset` first.")
        sys.exit(1)

    uri = upload_file(LOCAL_PARQUET, BUCKET, OBJECT_KEY)
    size = os.path.getsize(LOCAL_PARQUET)
    checksum = sha256_file(LOCAL_PARQUET)
    print(f"Uploaded {LOCAL_PARQUET} -> {uri} ({size} bytes)")

    db = SessionLocal()
    try:
        ds = dataset_service.register_dataset(
            db,
            DatasetCreate(
                name="cms-run2015",
                version="v1",
                format="parquet",
                storage_location=uri,
                metadata={
                    "description": "Synthetic HEP-like event data (pt/eta/phi/energy/label)",
                    "rows": 5000,
                    "source": "generated",
                },
                size=size,
                checksum=checksum,
            ).model_dump(),
        )
        print(f"Registered dataset {ds.name}:{ds.version} ({ds.dataset_id}) -> {split_s3_uri(uri)[1]}")
    except ValueError as exc:
        print(f"Skipped registration: {exc}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
