"""create jobs, workers, failures, experiment_transitions tables

Revision ID: 0003_phase3
Revises: 0002_datasets
Create Date: 2026-03-01
"""
from alembic import op
import sqlalchemy as sa

revision = "0003_phase3"
down_revision = "0002_datasets"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "jobs",
        sa.Column("job_id", sa.String(36), primary_key=True),
        sa.Column("experiment_id", sa.String(36), sa.ForeignKey("experiments.id"), nullable=False, index=True),
        sa.Column("status", sa.String(32), nullable=False, server_default="CREATED"),
        sa.Column("worker_count", sa.Integer, nullable=False, server_default="1"),
        sa.Column("retry_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error_message", sa.Text, nullable=True),
    )
    op.create_table(
        "workers",
        sa.Column("worker_id", sa.String(36), primary_key=True),
        sa.Column("job_id", sa.String(36), sa.ForeignKey("jobs.job_id"), nullable=False, index=True),
        sa.Column("status", sa.String(32), nullable=False, server_default="CREATED"),
        sa.Column("hostname", sa.String(255), nullable=True),
        sa.Column("container_id", sa.String(128), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("heartbeat_time", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "failures",
        sa.Column("failure_id", sa.String(36), primary_key=True),
        sa.Column("job_id", sa.String(36), sa.ForeignKey("jobs.job_id"), nullable=False, index=True),
        sa.Column("worker_id", sa.String(36), sa.ForeignKey("workers.worker_id"), nullable=True, index=True),
        sa.Column("error_type", sa.String(64), nullable=False),
        sa.Column("error_message", sa.Text, nullable=True),
        sa.Column("retryable", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("dedupe_key", sa.String(128), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("job_id", "dedupe_key", name="uq_failure_job_dedupe"),
    )
    op.create_table(
        "experiment_transitions",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("experiment_id", sa.String(36), sa.ForeignKey("experiments.id"), nullable=False, index=True),
        sa.Column("from_status", sa.String(32), nullable=True),
        sa.Column("to_status", sa.String(32), nullable=False),
        sa.Column("message", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("experiment_transitions")
    op.drop_table("failures")
    op.drop_table("workers")
    op.drop_table("jobs")
