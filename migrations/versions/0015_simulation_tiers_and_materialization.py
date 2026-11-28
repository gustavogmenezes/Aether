"""Persist explicit simulation-tier transitions and materialization links.

Revision ID: 0015
Revises: 0014
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0015"
down_revision: str | Sequence[str] | None = "0014"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "simulation_tier_states",
        sa.Column("entity_id", sa.String(36), nullable=False),
        sa.Column("world_id", sa.String(36), nullable=False),
        sa.Column("entity_type", sa.String(64), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.PrimaryKeyConstraint("entity_id"),
    )
    op.create_index(
        "ix_simulation_tier_states_world_id",
        "simulation_tier_states",
        ["world_id"],
    )
    op.create_table(
        "aggregate_population_source_links",
        sa.Column("population_id", sa.String(36), nullable=False),
        sa.Column("cohort_id", sa.String(36), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.PrimaryKeyConstraint("population_id", "cohort_id"),
    )
    op.create_table(
        "materialized_individual_links",
        sa.Column("character_id", sa.String(36), nullable=False),
        sa.Column("population_id", sa.String(36), nullable=False),
        sa.Column("cohort_id", sa.String(36), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.PrimaryKeyConstraint("character_id"),
    )
    op.create_index(
        "ix_materialized_individual_links_population_id",
        "materialized_individual_links",
        ["population_id"],
    )
    op.create_index(
        "ix_materialized_individual_links_cohort_id",
        "materialized_individual_links",
        ["cohort_id"],
    )
    op.create_table(
        "simulation_tier_transition_results",
        sa.Column("request_id", sa.String(36), nullable=False),
        sa.Column("world_id", sa.String(36), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.PrimaryKeyConstraint("request_id"),
    )
    op.create_index(
        "ix_simulation_tier_transition_results_world_id",
        "simulation_tier_transition_results",
        ["world_id"],
    )


def downgrade() -> None:
    op.drop_table("simulation_tier_transition_results")
    op.drop_table("materialized_individual_links")
    op.drop_table("aggregate_population_source_links")
    op.drop_table("simulation_tier_states")
