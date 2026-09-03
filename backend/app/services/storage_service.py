"""MinIO/S3 storage helpers (backend side: used by registration scripts)."""
import os

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


def upload_file(local_path: str, bucket: str, key: str) -> str:
    """Upload a file and return its s3:// URI."""
    s3 = get_s3_client()
    s3.upload_file(local_path, bucket, key)
    return f"s3://{bucket}/{key}"


def split_s3_uri(uri: str) -> tuple[str, str]:
    """'s3://bucket/key' -> ('bucket', 'key')."""
    if not uri.startswith("s3://"):
        raise ValueError(f"Not an s3:// URI: {uri}")
    rest = uri[5:]
    bucket, _, key = rest.partition("/")
    return bucket, key
