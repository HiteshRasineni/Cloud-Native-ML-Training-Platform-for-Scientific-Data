"""create datasets and artifacts tables

Revision ID: 0002_datasets
Revises: 0001_initial
Create Date: 2026-02-01
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0002_datasets"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "datasets",
        sa.Column("dataset_id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False, index=True),
        sa.Column("version", sa.String(64), nullable=False, index=True),
        sa.Column("format", sa.String(32), nullable=False),
        sa.Column("storage_location", sa.Text, nullable=False),
        sa.Column("metadata", postgresql.JSONB, nullable=False),
        sa.Column("size", sa.BigInteger, nullable=True),
        sa.Column("checksum", sa.String(128), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("name", "version", name="uq_dataset_name_version"),
    )
    op.create_table(
        "artifacts",
        sa.Column("artifact_id", sa.String(36), primary_key=True),
        sa.Column("experiment_id", sa.String(36), sa.ForeignKey("experiments.id"), nullable=False, index=True),
        sa.Column("artifact_type", sa.String(64), nullable=False),
        sa.Column("storage_path", sa.Text, nullable=False),
        sa.Column("epoch", sa.Integer, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("artifacts")
    op.drop_table("datasets")
