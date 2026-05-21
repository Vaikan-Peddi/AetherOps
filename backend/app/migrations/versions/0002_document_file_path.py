"""add document file path

Revision ID: 0002_document_file_path
Revises: 0001_initial_schema
Create Date: 2026-05-21
"""

from alembic import op
import sqlalchemy as sa


revision = "0002_document_file_path"
down_revision = "0001_initial_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("documents", sa.Column("file_path", sa.String(length=1024), nullable=True))


def downgrade() -> None:
    op.drop_column("documents", "file_path")
