"""Add geography, territory, infrastructure, and mobility.

Revision ID: 0008
Revises: 0007
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0008"
down_revision: str | Sequence[str] | None = "0007"
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
        "locations",
        sa.Column("location_id", sa.String(36), primary_key=True),
        sa.Column("world_id", sa.String(36), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("location_type", sa.String(32), nullable=False),
        sa.Column(
            "parent_location_id",
            sa.String(36),
            sa.ForeignKey("locations.location_id"),
            nullable=True,
        ),
        sa.Column("terrain", sa.JSON(), nullable=False),
        sa.Column("climate", sa.JSON(), nullable=False),
        sa.Column("hydrology", sa.JSON(), nullable=False),
        sa.Column("flora_fauna", sa.JSON(), nullable=False),
        sa.Column("natural_resources", sa.JSON(), nullable=False),
        sa.Column("population_density", sa.Text(), nullable=True),
        sa.Column("strategic_tags", sa.JSON(), nullable=False),
        sa.Column("risk_tags", sa.JSON(), nullable=False),
        sa.Column("barrier_tags", sa.JSON(), nullable=False),
        *_provenance_columns(),
    )
    op.create_index(
        "ix_locations_world_parent",
        "locations",
        ["world_id", "parent_location_id"],
    )
    op.create_table(
        "territory_claims",
        sa.Column("claim_id", sa.String(36), primary_key=True),
        sa.Column(
            "location_id",
            sa.String(36),
            sa.ForeignKey("locations.location_id"),
            nullable=False,
        ),
        sa.Column("semantics", sa.String(32), nullable=False),
        sa.Column("owner_actor_type", sa.String(32), nullable=True),
        sa.Column("owner_actor_id", sa.String(36), nullable=True),
        sa.Column("controller_actor_type", sa.String(32), nullable=True),
        sa.Column("controller_actor_id", sa.String(36), nullable=True),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("basis", sa.Text(), nullable=False),
        *_provenance_columns(),
    )
    op.create_table(
        "infrastructure_nodes",
        sa.Column("node_id", sa.String(36), primary_key=True),
        sa.Column("world_id", sa.String(36), nullable=False),
        sa.Column(
            "location_id",
            sa.String(36),
            sa.ForeignKey("locations.location_id"),
            nullable=False,
        ),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("node_type", sa.String(128), nullable=False),
        sa.Column("availability", sa.Text(), nullable=False),
        sa.Column("capacity", sa.Text(), nullable=True),
        sa.Column("safety_tags", sa.JSON(), nullable=False),
        sa.Column("risk_tags", sa.JSON(), nullable=False),
        *_provenance_columns(),
    )
    op.create_table(
        "infrastructure_facilities",
        sa.Column("facility_id", sa.String(36), primary_key=True),
        sa.Column(
            "node_id",
            sa.String(36),
            sa.ForeignKey("infrastructure_nodes.node_id"),
            nullable=False,
        ),
        sa.Column(
            "location_id",
            sa.String(36),
            sa.ForeignKey("locations.location_id"),
            nullable=False,
        ),
        sa.Column("facility_type", sa.String(128), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("availability", sa.Text(), nullable=False),
        sa.Column("capacity", sa.Text(), nullable=True),
        sa.Column("resource_consumption", sa.JSON(), nullable=False),
        sa.Column("safety_tags", sa.JSON(), nullable=False),
        sa.Column("risk_tags", sa.JSON(), nullable=False),
        *_provenance_columns(),
    )
    op.create_table(
        "transport_routes",
        sa.Column("route_id", sa.String(36), primary_key=True),
        sa.Column("world_id", sa.String(36), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column(
            "start_location_id",
            sa.String(36),
            sa.ForeignKey("locations.location_id"),
            nullable=False,
        ),
        sa.Column(
            "end_location_id",
            sa.String(36),
            sa.ForeignKey("locations.location_id"),
            nullable=False,
        ),
        sa.Column("modes", sa.JSON(), nullable=False),
        sa.Column("availability", sa.Text(), nullable=False),
        *_provenance_columns(),
    )
    op.create_table(
        "transport_route_segments",
        sa.Column("segment_id", sa.String(36), primary_key=True),
        sa.Column(
            "route_id",
            sa.String(36),
            sa.ForeignKey("transport_routes.route_id"),
            nullable=False,
        ),
        sa.Column("sequence", sa.Integer(), nullable=False),
        sa.Column(
            "start_location_id",
            sa.String(36),
            sa.ForeignKey("locations.location_id"),
            nullable=False,
        ),
        sa.Column(
            "end_location_id",
            sa.String(36),
            sa.ForeignKey("locations.location_id"),
            nullable=False,
        ),
        sa.Column("physical_distance", sa.Numeric(24, 8), nullable=False),
        sa.Column("distance_unit", sa.String(64), nullable=False),
        sa.Column("base_duration_microseconds", sa.Integer(), nullable=False),
        sa.Column("mode", sa.String(32), nullable=False),
        sa.Column("costs", sa.JSON(), nullable=False),
        sa.Column("capacity", sa.Text(), nullable=True),
        sa.Column("availability", sa.Text(), nullable=False),
        sa.Column("resource_consumption", sa.JSON(), nullable=False),
        sa.Column("safety_tags", sa.JSON(), nullable=False),
        sa.Column("risk_tags", sa.JSON(), nullable=False),
        *_provenance_columns(),
        sa.UniqueConstraint(
            "route_id", "sequence", name="uq_route_segment_sequence"
        ),
    )
    op.create_table(
        "actor_positions",
        sa.Column("actor_type", sa.String(32), primary_key=True),
        sa.Column("actor_id", sa.String(36), primary_key=True),
        sa.Column(
            "location_id",
            sa.String(36),
            sa.ForeignKey("locations.location_id"),
            nullable=False,
        ),
        sa.Column("journey_id", sa.String(36), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False),
    )
    op.create_table(
        "journeys",
        sa.Column("journey_id", sa.String(36), primary_key=True),
        sa.Column("world_id", sa.String(36), nullable=False),
        sa.Column(
            "timeline_id",
            sa.String(36),
            sa.ForeignKey("world_clocks.timeline_id"),
            nullable=False,
        ),
        sa.Column("participants", sa.JSON(), nullable=False),
        sa.Column("start_location_id", sa.String(36), nullable=False),
        sa.Column("end_location_id", sa.String(36), nullable=False),
        sa.Column(
            "route_id",
            sa.String(36),
            sa.ForeignKey("transport_routes.route_id"),
            nullable=False,
        ),
        sa.Column("segment_ids", sa.JSON(), nullable=False),
        sa.Column("resource_owner", sa.JSON(), nullable=True),
        sa.Column("costs", sa.JSON(), nullable=False),
        sa.Column("resource_consumption", sa.JSON(), nullable=False),
        sa.Column("started_at", sa.DateTime(), nullable=False),
        sa.Column("expected_arrival_at", sa.DateTime(), nullable=False),
        sa.Column("arrived_at", sa.DateTime(), nullable=True),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column(
            "scheduled_event_id",
            sa.String(36),
            nullable=False,
            unique=True,
        ),
        *_provenance_columns(),
    )


def downgrade() -> None:
    op.drop_table("journeys")
    op.drop_table("actor_positions")
    op.drop_table("transport_route_segments")
    op.drop_table("transport_routes")
    op.drop_table("infrastructure_facilities")
    op.drop_table("infrastructure_nodes")
    op.drop_table("territory_claims")
    op.drop_table("locations")
