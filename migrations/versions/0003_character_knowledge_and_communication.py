"""Create character knowledge and communication state.

Revision ID: 0003
Revises: 0002
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0003"
down_revision: str | Sequence[str] | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "character_knowledge",
        sa.Column("knowledge_id", sa.String(36), nullable=False),
        sa.Column("character_id", sa.String(36), nullable=False),
        sa.Column("fact_key", sa.String(512), nullable=False),
        sa.Column("statement", sa.Text(), nullable=False),
        sa.Column("source_event_id", sa.String(36), nullable=True),
        sa.Column("acquisition_event_id", sa.String(36), nullable=True),
        sa.Column("acquired_at", sa.DateTime(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("epistemic_status", sa.String(32), nullable=False),
        sa.Column("temporal_scope", sa.Text(), nullable=True),
        sa.Column("visible_in_character_context", sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint("knowledge_id"),
    )
    op.create_index(
        "ix_character_knowledge_character_time",
        "character_knowledge",
        ["character_id", "acquired_at"],
    )
    op.create_index(
        "ix_character_knowledge_fact",
        "character_knowledge",
        ["fact_key"],
    )
    op.create_table(
        "information_transmissions",
        sa.Column("transmission_id", sa.String(36), nullable=False),
        sa.Column("source_event_id", sa.String(36), nullable=True),
        sa.Column("sender_character_id", sa.String(36), nullable=True),
        sa.Column("recipient_character_id", sa.String(36), nullable=False),
        sa.Column("fact_key", sa.String(512), nullable=False),
        sa.Column("statement", sa.Text(), nullable=False),
        sa.Column("medium", sa.String(32), nullable=False),
        sa.Column("nature", sa.String(32), nullable=False),
        sa.Column("sent_at", sa.DateTime(), nullable=False),
        sa.Column("arrival_at", sa.DateTime(), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("perceived_reliability", sa.Float(), nullable=False),
        sa.Column("alterations", sa.JSON(), nullable=False),
        sa.Column("sender_intent", sa.Text(), nullable=True),
        sa.Column("reach", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("transmission_id"),
    )
    op.create_index(
        "ix_information_transmissions_arrival",
        "information_transmissions",
        ["status", "arrival_at"],
    )


def downgrade() -> None:
    op.drop_table("information_transmissions")
    op.drop_table("character_knowledge")
