"""MinIO/S3 storage helpers (worker side)."""
import os
import tempfile

import boto3
from botocore.client import Config


def get_s3_client():
    return boto3.client(
        "s3",
        endpoint_url=os.getenv("MINIO_ENDPOINT", "http://minio:9000"),
        aws_access_key_id=os.getenv("MINIO_ROOT_USER", "mlplatform"),
        aws_secret_access_key=os.getenv("MINIO_ROOT_PASSWORD", "mlplatform-secret"),
        region_name=os.getenv("MINIO_REGION", "us-east-1"),
        config=Config(signature_version="s3v4"),
    )


def split_s3_uri(uri: str) -> tuple[str, str]:
    """'s3://bucket/key' -> ('bucket', 'key')."""
    if not uri.startswith("s3://"):
        raise ValueError(f"Not an s3:// URI: {uri}")
    rest = uri[5:]
    bucket, _, key = rest.partition("/")
    return bucket, key


def download_to_temp(s3_uri: str) -> str:
    """Download an S3 object to a temp file and return the local path."""
    bucket, key = split_s3_uri(s3_uri)
    suffix = os.path.splitext(key)[1] or ".tmp"
    fd, local_path = tempfile.mkstemp(suffix=suffix)
    os.close(fd)
    get_s3_client().download_file(bucket, key, local_path)
    return local_path


def upload_file(local_path: str, s3_uri: str) -> None:
    """Upload a local file to an s3:// URI."""
    bucket, key = split_s3_uri(s3_uri)
    get_s3_client().upload_file(local_path, bucket, key)
