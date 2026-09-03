"""Shared pytest fixtures for backend tests (dedicated test database, with
per-test cleanup so duplicate-guard logic stays isolated)."""
import os
import sys

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models import Base
from app.services import dataset_service

TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL", "postgresql+psycopg2://mlplatform:mlplatform@localhost:5432/mlplatform_test"
)


@pytest.fixture(scope="session")
def engine():
    eng = create_engine(TEST_DATABASE_URL)
    Base.metadata.create_all(eng)
    yield eng
    Base.metadata.drop_all(eng)


@pytest.fixture
def db_session(engine):
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    # Wipe all rows after each test so duplicate-guard / state tests are isolated.
    for table in reversed(Base.metadata.sorted_tables):
        session.execute(table.delete())
    session.commit()
    session.close()


@pytest.fixture
def registered_dataset(db_session):
    """Register the canonical sample dataset (cms-run2015:v1)."""
    return dataset_service.register_dataset(
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
