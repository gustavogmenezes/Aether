"""Persist cultures, social groups, affiliations, and cultural change history.

Revision ID: 0016
Revises: 0015
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0016"
down_revision: str | Sequence[str] | None = "0015"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "culture_definitions",
        sa.Column("culture_id", sa.String(36), nullable=False),
        sa.Column("world_id", sa.String(36), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.PrimaryKeyConstraint("culture_id"),
    )
    op.create_index(
        "ix_culture_definitions_world_id",
        "culture_definitions",
        ["world_id"],
    )

    op.create_table(
        "social_groups",
        sa.Column("group_id", sa.String(36), nullable=False),
        sa.Column("world_id", sa.String(36), nullable=False),
        sa.Column("semantic_category", sa.String(128), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.PrimaryKeyConstraint("group_id"),
    )
    op.create_index(
        "ix_social_groups_world_id",
        "social_groups",
        ["world_id"],
    )

    op.create_table(
        "individual_cultural_affiliations",
        sa.Column("affiliation_id", sa.String(36), nullable=False),
        sa.Column("character_id", sa.String(36), nullable=False),
        sa.Column("target_type", sa.String(32), nullable=False),
        sa.Column("target_id", sa.String(36), nullable=False),
        sa.Column("visibility", sa.String(32), nullable=False),
        sa.Column("effective_from", sa.DateTime(timezone=True), nullable=False),
        sa.Column("effective_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.PrimaryKeyConstraint("affiliation_id"),
    )
    op.create_index(
        "ix_individual_cultural_affiliations_character_id",
        "individual_cultural_affiliations",
        ["character_id"],
    )
    op.create_index(
        "ix_individual_cultural_affiliations_target_id",
        "individual_cultural_affiliations",
        ["target_id"],
    )
    op.create_index(
        "ix_cultural_affiliations_character_effective",
        "individual_cultural_affiliations",
        ["character_id", "effective_from", "effective_until"],
    )

    op.create_table(
        "cultural_change_records",
        sa.Column("record_id", sa.String(36), nullable=False),
        sa.Column("world_id", sa.String(36), nullable=False),
        sa.Column("target_type", sa.String(32), nullable=False),
        sa.Column("target_id", sa.String(36), nullable=False),
        sa.Column("source_event_id", sa.String(36), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("cause_tags", sa.JSON(), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.PrimaryKeyConstraint("record_id"),
    )
    op.create_index(
        "ix_cultural_change_records_world_id",
        "cultural_change_records",
        ["world_id"],
    )
    op.create_index(
        "ix_cultural_change_records_target_id",
        "cultural_change_records",
        ["target_id"],
    )
    op.create_index(
        "ix_cultural_change_records_source_event_id",
        "cultural_change_records",
        ["source_event_id"],
    )
    op.create_index(
        "ix_cultural_change_target_time",
        "cultural_change_records",
        ["target_type", "target_id", "occurred_at"],
    )


def downgrade() -> None:
    op.drop_table("cultural_change_records")
    op.drop_table("individual_cultural_affiliations")
    op.drop_table("social_groups")
    op.drop_table("culture_definitions")
