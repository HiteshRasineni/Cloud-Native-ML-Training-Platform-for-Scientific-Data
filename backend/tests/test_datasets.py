"""Tests for dataset resolution, checkpoint paths, and normalizing flow shapes."""
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services import dataset_service


# ---------- Dataset resolution ----------


def test_resolve_registered_dataset(db_session, registered_dataset):
    ds = dataset_service.resolve(db_session, "cms-run2015", "v1")
    assert ds.name == "cms-run2015"
    assert ds.version == "v1"
    assert ds.storage_location.startswith("s3://")


def test_resolve_missing_dataset_raises(db_session):
    with pytest.raises(dataset_service.DatasetNotFoundError):
        dataset_service.resolve(db_session, "does-not-exist", "v1")


def test_resolve_wrong_version_raises(db_session, registered_dataset):
    with pytest.raises(dataset_service.DatasetNotFoundError):
        dataset_service.resolve(db_session, "cms-run2015", "v99")


def test_duplicate_dataset_rejected(db_session, registered_dataset):
    with pytest.raises(ValueError, match="already registered"):
        dataset_service.register_dataset(
            db_session,
            {
                "name": "cms-run2015",
                "version": "v1",
                "format": "parquet",
                "storage_location": "s3://mlplatform/datasets/cms-run2015/v1/data.parquet",
                "metadata": {},
                "size": None,
                "checksum": None,
            },
        )


def test_dataset_uri_parse():
    name, version = dataset_service.parse_dataset_uri("cms-run2015:v1")
    assert name == "cms-run2015"
    assert version == "v1"


def test_dataset_uri_parse_invalid():
    with pytest.raises(ValueError):
        dataset_service.parse_dataset_uri("no-colon")


# ---------- Experiment creation resolves dataset ----------


def test_create_experiment_resolves_storage_location(db_session, registered_dataset):
    from app.schemas.experiment import ExperimentCreate, ExperimentSpec
    from app.services import experiment_service

    spec = ExperimentSpec(
        **{
            "experiment": {"name": "nf-test"},
            "dataset": {"name": "cms-run2015", "version": "v1"},
            "model": {"type": "normalizing-flow"},
            "resources": {"workers": 1, "cpu": "2", "memory": "4Gi"},
            "training": {"epochs": 3, "batch_size": 64, "learning_rate": 0.001},
            "checkpointing": {"enabled": False},
            "retry": {"max_attempts": 3},
        }
    )
    exp = experiment_service.create_experiment(db_session, ExperimentCreate(spec=spec))
    assert exp.spec["dataset"]["storage_location"].startswith("s3://")


def test_create_experiment_rejects_unregistered_dataset(db_session):
    from app.schemas.experiment import ExperimentCreate, ExperimentSpec
    from app.services import experiment_service

    spec = ExperimentSpec(
        **{
            "experiment": {"name": "nf-test"},
            "dataset": {"name": "not-registered", "version": "v1"},
            "model": {"type": "normalizing-flow"},
            "resources": {"workers": 1, "cpu": "2", "memory": "4Gi"},
            "training": {"epochs": 3, "batch_size": 64, "learning_rate": 0.001},
            "checkpointing": {"enabled": False},
            "retry": {"max_attempts": 3},
        }
    )
    with pytest.raises(dataset_service.DatasetNotFoundError):
        experiment_service.create_experiment(db_session, ExperimentCreate(spec=spec))
