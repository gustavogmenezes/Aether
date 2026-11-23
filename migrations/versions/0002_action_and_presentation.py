"""Create action presentation and knowledge state.

Revision ID: 0002
Revises: 0001
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0002"
down_revision: str | Sequence[str] | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "narrative_presentations",
        sa.Column("presentation_id", sa.String(36), nullable=False),
        sa.Column("simulation_run_id", sa.String(36), nullable=False),
        sa.Column("protagonist_character_id", sa.String(36), nullable=False),
        sa.Column("narrative_time", sa.DateTime(), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("generated_content", sa.Text(), nullable=False),
        sa.Column("delivered_content", sa.Text(), nullable=True),
        sa.Column("confirmed_fact_ids", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("delivered_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(
            ["simulation_run_id"],
            ["simulation_runs.simulation_run_id"],
        ),
        sa.PrimaryKeyConstraint("presentation_id"),
        sa.UniqueConstraint("simulation_run_id"),
    )
    op.create_table(
        "player_knowledge",
        sa.Column("knowledge_id", sa.String(36), nullable=False),
        sa.Column("simulation_run_id", sa.String(36), nullable=False),
        sa.Column("player_id", sa.String(128), nullable=False),
        sa.Column("fact_key", sa.String(512), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("source_presentation_id", sa.String(36), nullable=False),
        sa.Column("acquired_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["simulation_run_id"],
            ["simulation_runs.simulation_run_id"],
        ),
        sa.ForeignKeyConstraint(
            ["source_presentation_id"],
            ["narrative_presentations.presentation_id"],
        ),
        sa.PrimaryKeyConstraint("knowledge_id"),
    )
    op.create_index(
        "ix_player_knowledge_player",
        "player_knowledge",
        ["player_id", "acquired_at"],
    )
    op.create_table(
        "narrative_states",
        sa.Column("state_id", sa.String(36), nullable=False),
        sa.Column("simulation_run_id", sa.String(36), nullable=False),
        sa.Column("protagonist_character_id", sa.String(36), nullable=False),
        sa.Column("scene_summary", sa.Text(), nullable=False),
        sa.Column("narrative_time", sa.DateTime(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["simulation_run_id"],
            ["simulation_runs.simulation_run_id"],
        ),
        sa.PrimaryKeyConstraint("state_id"),
    )
    op.create_index(
        "ix_narrative_states_protagonist_time",
        "narrative_states",
        ["protagonist_character_id", "narrative_time"],
    )


def downgrade() -> None:
    op.drop_table("narrative_states")
    op.drop_table("player_knowledge")
    op.drop_table("narrative_presentations")
