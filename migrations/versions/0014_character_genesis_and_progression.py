"""Persist Character Genesis sheets and immutable progression evidence.

Revision ID: 0014
Revises: 0013
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0014"
down_revision: str | Sequence[str] | None = "0013"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "character_sheets",
        sa.Column("character_id", sa.String(36), nullable=False),
        sa.Column("world_id", sa.String(36), nullable=False),
        sa.Column("ruleset_id", sa.String(128), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.PrimaryKeyConstraint("character_id"),
    )
    op.create_index(
        "ix_character_sheets_world_id", "character_sheets", ["world_id"]
    )
    op.create_table(
        "character_progression_evidence",
        sa.Column("evidence_id", sa.String(36), nullable=False),
        sa.Column("character_id", sa.String(36), nullable=False),
        sa.Column("world_id", sa.String(36), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.PrimaryKeyConstraint("evidence_id"),
    )
    op.create_index(
        "ix_character_progression_evidence_character_id",
        "character_progression_evidence",
        ["character_id"],
    )
    op.create_index(
        "ix_character_progression_evidence_world_id",
        "character_progression_evidence",
        ["world_id"],
    )
    op.create_table(
        "character_progression_proposals",
        sa.Column("proposal_id", sa.String(36), nullable=False),
        sa.Column("request_id", sa.String(36), nullable=False),
        sa.Column("character_id", sa.String(36), nullable=False),
        sa.Column("world_id", sa.String(36), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.PrimaryKeyConstraint("proposal_id"),
        sa.UniqueConstraint("request_id", name="uq_progression_request"),
    )
    op.create_index(
        "ix_character_progression_proposals_character_id",
        "character_progression_proposals",
        ["character_id"],
    )
    op.create_index(
        "ix_character_progression_proposals_world_id",
        "character_progression_proposals",
        ["world_id"],
    )
    op.create_table(
        "character_progression_validations",
        sa.Column("validation_id", sa.String(36), nullable=False),
        sa.Column("proposal_id", sa.String(36), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.PrimaryKeyConstraint("validation_id"),
    )
    op.create_index(
        "ix_character_progression_validations_proposal_id",
        "character_progression_validations",
        ["proposal_id"],
    )
    op.create_table(
        "character_progression_applications",
        sa.Column("application_id", sa.String(36), nullable=False),
        sa.Column("proposal_id", sa.String(36), nullable=False),
        sa.Column("character_id", sa.String(36), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.PrimaryKeyConstraint("application_id"),
        sa.UniqueConstraint("proposal_id", name="uq_progression_application"),
    )
    op.create_index(
        "ix_character_progression_applications_character_id",
        "character_progression_applications",
        ["character_id"],
    )


def downgrade() -> None:
    op.drop_table("character_progression_applications")
    op.drop_table("character_progression_validations")
    op.drop_table("character_progression_proposals")
    op.drop_table("character_progression_evidence")
    op.drop_table("character_sheets")
