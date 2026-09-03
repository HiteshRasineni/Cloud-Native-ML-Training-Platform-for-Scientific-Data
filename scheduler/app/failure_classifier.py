"""Generic failure classification.

The scheduler stays workload-agnostic: classification is driven by keywords /
container signals, not by any HEP/normalizing-flow specifics. See
docs/failure-handling.md for the full documented classification logic.

Defined error_types (with retryable flag):
    container_crash            (True)   non-zero exit / unexpected termination
    heartbeat_timeout          (True)   missed heartbeats past threshold
    dataset_resolution_error   (False)  dataset/version not found
    training_exception         (True)   unhandled exception inside the workload
    config_error               (False)  clearly a bad hyperparameter/config
    object_storage_unavailable (True)   MinIO connection failure
    launch_error               (True)   executor failed to start the worker
"""
from typing import Final

CONTAINER_CRASH: Final[str] = "container_crash"
HEARTBEAT_TIMEOUT: Final[str] = "heartbeat_timeout"
DATASET_RESOLUTION_ERROR: Final[str] = "dataset_resolution_error"
TRAINING_EXCEPTION: Final[str] = "training_exception"
CONFIG_ERROR: Final[str] = "config_error"
OBJECT_STORAGE_UNAVAILABLE: Final[str] = "object_storage_unavailable"
LAUNCH_ERROR: Final[str] = "launch_error"

# Retryability table (generic, documented).
RETRYABLE_BY_TYPE: Final[dict[str, bool]] = {
    CONTAINER_CRASH: True,
    HEARTBEAT_TIMEOUT: True,
    DATASET_RESOLUTION_ERROR: False,
    TRAINING_EXCEPTION: True,
    CONFIG_ERROR: False,
    OBJECT_STORAGE_UNAVAILABLE: True,
    LAUNCH_ERROR: True,
}

# Keyword hints (lowercased) for classifying an exception/error message.
_DATASET_HINTS = ("dataset", "not found", "not registered", "resolve")
_STORAGE_HINTS = ("s3", "minio", "endpoint", "connection refused", "credentials",
                  "unable to locate", "bucket")
_CONFIG_HINTS = ("invalid hyperparameter", "learning_rate", "batch_size", "epochs",
                 "architecture", "unsupported", "not a valid value", "expected 1 argument")


def retryable_for(error_type: str) -> bool:
    return RETRYABLE_BY_TYPE.get(error_type, True)


def classify_container_crash() -> tuple[str, str, bool]:
    return CONTAINER_CRASH, "worker container exited unexpectedly (non-zero code)", True


def classify_heartbeat_timeout() -> tuple[str, str, bool]:
    return HEARTBEAT_TIMEOUT, "worker heartbeat timed out", True


def classify_launch_error() -> tuple[str, str, bool]:
    return LAUNCH_ERROR, "failed to launch worker container", True


def classify_exception(message: str) -> tuple[str, str, bool]:
    """Classify an arbitrary error string into (error_type, message, retryable)."""
    lowered = (message or "").lower()
    if all(h in lowered for h in _DATASET_HINTS):
        return DATASET_RESOLUTION_ERROR, message, False
    if any(h in lowered for h in _STORAGE_HINTS):
        return OBJECT_STORAGE_UNAVAILABLE, message, True
    if any(h in lowered for h in _CONFIG_HINTS):
        return CONFIG_ERROR, message, False
    return TRAINING_EXCEPTION, message, True
