"""Register the sample HEP-like dataset (CMS ROOT format) in MinIO + via POST /datasets.

Runs inside the backend container:
    docker compose exec backend python scripts/register_root_dataset.py

Unlike the parquet sample, the ROOT file is written on demand (needs uproot),
so this script generates it locally, uploads it, and registers it as
cms-run2015-root:v1 with format=root. Dataset metadata records the TTree name
and the feature branches so the worker can parse it without guessing.
"""
import hashlib
import os
import subprocess
import sys

sys.path.insert(0, "/app")

from app.database.session import SessionLocal  # noqa: E402
from app.schemas.dataset import DatasetCreate  # noqa: E402
from app.services import dataset_service  # noqa: E402
from app.services.storage_service import split_s3_uri, upload_file  # noqa: E402

BUCKET = os.getenv("MINIO_BUCKET", "mlplatform")
LOCAL_ROOT = os.getenv("SAMPLE_ROOT_PATH", "/tmp/cms-run2015_v1.root")
GENERATOR = os.getenv(
    "SAMPLE_ROOT_GENERATOR", "/datasets/sample/generate_sample_root.py"
)
OBJECT_KEY = "datasets/cms-run2015-root/v1/data.root"
FEATURES = ["pt", "eta", "phi", "energy"]


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def ensure_root_file() -> None:
    if os.path.exists(LOCAL_ROOT):
        return
    subprocess.run(
        [sys.executable, GENERATOR, "--out", LOCAL_ROOT], check=True
    )


def main() -> None:
    ensure_root_file()
    uri = upload_file(LOCAL_ROOT, BUCKET, OBJECT_KEY)
    size = os.path.getsize(LOCAL_ROOT)
    checksum = sha256_file(LOCAL_ROOT)
    print(f"Uploaded {LOCAL_ROOT} -> {uri} ({size} bytes)")

    db = SessionLocal()
    try:
        ds = dataset_service.register_dataset(
            db,
            DatasetCreate(
                name="cms-run2015-root",
                version="v1",
                format="root",
                storage_location=uri,
                metadata={
                    "description": "Synthetic HEP-like event data in ROOT format",
                    "tree": "Events",
                    "features": FEATURES,
                    "rows": 5000,
                    "source": "generated",
                },
                size=size,
                checksum=checksum,
            ).model_dump(),
        )
        print(
            f"Registered dataset {ds.name}:{ds.version} ({ds.dataset_id}) "
            f"-> {split_s3_uri(uri)[1]}"
        )
    except ValueError as exc:
        print(f"Skipped registration: {exc}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
