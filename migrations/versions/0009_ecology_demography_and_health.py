"""Add ecology, demography, species, and health state persistence.

Revision ID: 0009
Revises: 0008
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0009"
down_revision: str | Sequence[str] | None = "0008"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _provenance_columns() -> list[sa.Column]:
    return [
        sa.Column("source_type", sa.String(128), nullable=False),
        sa.Column("source_id", sa.Text(), nullable=False),
        sa.Column("origin_event_id", sa.String(36), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    ]


def upgrade() -> None:
    op.create_table(
        "species",
        sa.Column("species_id", sa.String(36), primary_key=True),
        sa.Column("world_id", sa.String(36), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("organism_kind", sa.String(32), nullable=False),
        sa.Column("anatomy", sa.JSON(), nullable=False),
        sa.Column("physiology", sa.JSON(), nullable=False),
        sa.Column("reproduction_model", sa.JSON(), nullable=False),
        sa.Column("nutrition", sa.JSON(), nullable=False),
        sa.Column("habitat", sa.JSON(), nullable=False),
        sa.Column("senses", sa.JSON(), nullable=False),
        sa.Column("adaptations", sa.JSON(), nullable=False),
        sa.Column("lifecycle_stages", sa.JSON(), nullable=False),
        sa.Column("resource_links", sa.JSON(), nullable=False),
        *_provenance_columns(),
    )
    op.create_index("ix_species_world_id", "species", ["world_id"])
    op.create_table(
        "ecological_habitats",
        sa.Column("habitat_id", sa.String(36), primary_key=True),
        sa.Column("world_id", sa.String(36), nullable=False),
        sa.Column(
            "location_id",
            sa.String(36),
            sa.ForeignKey("locations.location_id"),
            nullable=False,
        ),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("habitat_type", sa.String(128), nullable=False),
        sa.Column("habitability", sa.JSON(), nullable=False),
        sa.Column("species_ids", sa.JSON(), nullable=False),
        sa.Column("resources", sa.JSON(), nullable=False),
        sa.Column("resource_links", sa.JSON(), nullable=False),
        sa.Column("characteristics", sa.JSON(), nullable=False),
        *_provenance_columns(),
    )
    op.create_index(
        "ix_ecological_habitats_world_id", "ecological_habitats", ["world_id"]
    )
    op.create_table(
        "populations",
        sa.Column("population_id", sa.String(36), primary_key=True),
        sa.Column("world_id", sa.String(36), nullable=False),
        sa.Column(
            "species_id",
            sa.String(36),
            sa.ForeignKey("species.species_id"),
            nullable=False,
        ),
        sa.Column(
            "location_id",
            sa.String(36),
            sa.ForeignKey("locations.location_id"),
            nullable=False,
        ),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("cohorts", sa.JSON(), nullable=False),
        sa.Column("aggregate_by_default", sa.Boolean(), nullable=False),
        sa.Column("resource_links", sa.JSON(), nullable=False),
        *_provenance_columns(),
    )
    op.create_index("ix_populations_world_id", "populations", ["world_id"])
    op.create_table(
        "ecological_processes",
        sa.Column("process_id", sa.String(36), primary_key=True),
        sa.Column("world_id", sa.String(36), nullable=False),
        sa.Column(
            "location_id",
            sa.String(36),
            sa.ForeignKey("locations.location_id"),
            nullable=False,
        ),
        sa.Column("process_type", sa.String(128), nullable=False),
        sa.Column("measures", sa.JSON(), nullable=False),
        sa.Column("population_links", sa.JSON(), nullable=False),
        sa.Column("resource_links", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        *_provenance_columns(),
    )
    op.create_index(
        "ix_ecological_processes_world_id", "ecological_processes", ["world_id"]
    )
    op.create_table(
        "health_states",
        sa.Column("state_id", sa.String(36), primary_key=True),
        sa.Column("character_id", sa.String(36), nullable=False, unique=True),
        sa.Column("species_id", sa.String(36), nullable=True),
        sa.Column("physical_integrity", sa.Text(), nullable=False),
        sa.Column("consciousness", sa.Text(), nullable=False),
        sa.Column("ability_to_act", sa.Text(), nullable=False),
        sa.Column("ability_to_fight", sa.Text(), nullable=False),
        sa.Column("conditions", sa.JSON(), nullable=False),
        *_provenance_columns(),
    )


def downgrade() -> None:
    op.drop_table("health_states")
    op.drop_index("ix_ecological_processes_world_id", table_name="ecological_processes")
    op.drop_table("ecological_processes")
    op.drop_index("ix_populations_world_id", table_name="populations")
    op.drop_table("populations")
    op.drop_index("ix_ecological_habitats_world_id", table_name="ecological_habitats")
    op.drop_table("ecological_habitats")
    op.drop_index("ix_species_world_id", table_name="species")
    op.drop_table("species")
