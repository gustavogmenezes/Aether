"""Create canonical proposals and persistent approval history.

Revision ID: 0013
Revises: 0012
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0013"
down_revision: str | Sequence[str] | None = "0012"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "canonical_proposals",
        sa.Column("proposal_id", sa.String(36), nullable=False),
        sa.Column("world_id", sa.String(36), nullable=False),
        sa.Column("entity_type", sa.String(128), nullable=False),
        sa.Column("entity_id", sa.String(36), nullable=True),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.PrimaryKeyConstraint("proposal_id"),
    )
    op.create_index(
        "ix_canonical_proposals_world_id",
        "canonical_proposals",
        ["world_id"],
    )
    op.create_table(
        "canonical_records",
        sa.Column("record_id", sa.String(36), nullable=False),
        sa.Column("proposal_id", sa.String(36), nullable=False),
        sa.Column("world_id", sa.String(36), nullable=False),
        sa.Column("entity_type", sa.String(128), nullable=False),
        sa.Column("entity_id", sa.String(36), nullable=True),
        sa.Column("level", sa.Integer(), nullable=False),
        sa.Column("revision", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("supersedes_record_id", sa.String(36), nullable=True),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.PrimaryKeyConstraint("record_id"),
    )
    op.create_index(
        "ix_canonical_records_entity",
        "canonical_records",
        ["world_id", "entity_type", "entity_id", "revision"],
    )
    op.create_index(
        "ix_canonical_records_proposal",
        "canonical_records",
        ["proposal_id"],
    )


def downgrade() -> None:
    op.drop_table("canonical_records")
    op.drop_table("canonical_proposals")
