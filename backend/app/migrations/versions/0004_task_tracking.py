"""task tracking ids

Revision ID: 0004_task_tracking
Revises: 0003_phase2_foundations
Create Date: 2026-05-21
"""

from alembic import op
import sqlalchemy as sa


revision = "0004_task_tracking"
down_revision = "0003_phase2_foundations"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("documents", sa.Column("celery_task_id", sa.String(length=255), nullable=True))
    op.create_index("ix_documents_celery_task_id", "documents", ["celery_task_id"])
    op.add_column("workflow_runs", sa.Column("celery_task_id", sa.String(length=255), nullable=True))
    op.create_index("ix_workflow_runs_celery_task_id", "workflow_runs", ["celery_task_id"])


def downgrade() -> None:
    op.drop_index("ix_workflow_runs_celery_task_id", table_name="workflow_runs")
    op.drop_column("workflow_runs", "celery_task_id")
    op.drop_index("ix_documents_celery_task_id", table_name="documents")
    op.drop_column("documents", "celery_task_id")
