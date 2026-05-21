"""phase 2 foundations

Revision ID: 0003_phase2_foundations
Revises: 0002_document_file_path
Create Date: 2026-05-21
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0003_phase2_foundations"
down_revision = "0002_document_file_path"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TYPE workflowactiontype ADD VALUE IF NOT EXISTS 'SUMMARIZE'")
    op.execute("ALTER TYPE workflowactiontype ADD VALUE IF NOT EXISTS 'CHAT'")
    op.execute("ALTER TYPE workflowactiontype ADD VALUE IF NOT EXISTS 'WEBHOOK'")
    op.execute("ALTER TYPE workflowactiontype ADD VALUE IF NOT EXISTS 'CONDITION'")
    op.execute("ALTER TYPE workflowactiontype ADD VALUE IF NOT EXISTS 'DELAY'")
    op.execute("ALTER TYPE workflowactiontype ADD VALUE IF NOT EXISTS 'HUMAN_APPROVAL'")

    op.add_column("documents", sa.Column("progress_percent", sa.Integer(), server_default="0", nullable=False))
    op.add_column("documents", sa.Column("current_step", sa.String(length=255), nullable=True))
    op.add_column(
        "workflows",
        sa.Column("graph_json", postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb"), nullable=False),
    )
    op.add_column("workflow_runs", sa.Column("progress_percent", sa.Integer(), server_default="0", nullable=False))
    op.add_column("workflow_runs", sa.Column("current_step", sa.String(length=255), nullable=True))

    messagerole = postgresql.ENUM("SYSTEM", "USER", "ASSISTANT", "TOOL", name="messagerole", create_type=False)
    messagerole.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "conversations",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("metadata_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_conversations_organization_id", "conversations", ["organization_id"])

    op.create_table(
        "messages",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("conversation_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("role", messagerole, nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("provider", sa.String(length=100), nullable=True),
        sa.Column("model", sa.String(length=255), nullable=True),
        sa.Column("token_count", sa.Integer(), nullable=False),
        sa.Column("metadata_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["conversation_id"], ["conversations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_messages_conversation_id", "messages", ["conversation_id"])
    op.create_index("ix_messages_organization_id", "messages", ["organization_id"])

    op.create_table(
        "evaluation_runs",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("question", sa.Text(), nullable=False),
        sa.Column("answer", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("metrics", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_evaluation_runs_organization_id", "evaluation_runs", ["organization_id"])


def downgrade() -> None:
    op.drop_table("evaluation_runs")
    op.drop_table("messages")
    op.drop_table("conversations")
    op.drop_column("workflow_runs", "current_step")
    op.drop_column("workflow_runs", "progress_percent")
    op.drop_column("workflows", "graph_json")
    op.drop_column("documents", "current_step")
    op.drop_column("documents", "progress_percent")
    postgresql.ENUM(name="messagerole").drop(op.get_bind(), checkfirst=True)
