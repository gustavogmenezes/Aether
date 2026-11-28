"""Create public culture, creative expression, and identity assets.

Revision ID: 0012
Revises: 0011
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0012"
down_revision: str | Sequence[str] | None = "0011"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "public_channels",
        sa.Column("channel_id", sa.String(36), nullable=False),
        sa.Column("world_id", sa.String(36), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.PrimaryKeyConstraint("channel_id"),
    )
    op.create_index("ix_public_channels_world_id", "public_channels", ["world_id"])
    op.create_table(
        "public_information",
        sa.Column("publication_id", sa.String(36), nullable=False),
        sa.Column("world_id", sa.String(36), nullable=False),
        sa.Column("channel_id", sa.String(36), nullable=False),
        sa.Column("published_at", sa.DateTime(), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.PrimaryKeyConstraint("publication_id"),
    )
    op.create_index(
        "ix_public_information_world_id", "public_information", ["world_id"]
    )
    op.create_index(
        "ix_public_information_channel_id", "public_information", ["channel_id"]
    )
    op.create_table(
        "collective_receptions",
        sa.Column("reception_id", sa.String(36), nullable=False),
        sa.Column("publication_id", sa.String(36), nullable=False),
        sa.Column("population_id", sa.String(36), nullable=False),
        sa.Column("received_at", sa.DateTime(), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.PrimaryKeyConstraint("reception_id"),
    )
    op.create_index(
        "ix_collective_receptions_publication_id",
        "collective_receptions",
        ["publication_id"],
    )
    op.create_index(
        "ix_collective_receptions_population_id",
        "collective_receptions",
        ["population_id"],
    )
    op.create_table(
        "creative_works",
        sa.Column("work_id", sa.String(36), nullable=False),
        sa.Column("world_id", sa.String(36), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.PrimaryKeyConstraint("work_id"),
    )
    op.create_index("ix_creative_works_world_id", "creative_works", ["world_id"])
    op.create_table(
        "leisure_routines",
        sa.Column("routine_id", sa.String(36), nullable=False),
        sa.Column("actor_type", sa.String(32), nullable=False),
        sa.Column("actor_id", sa.String(36), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.PrimaryKeyConstraint("routine_id"),
    )
    op.create_table(
        "visual_identities",
        sa.Column("identity_id", sa.String(36), nullable=False),
        sa.Column("actor_type", sa.String(32), nullable=False),
        sa.Column("actor_id", sa.String(36), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.PrimaryKeyConstraint("identity_id"),
    )
    op.create_index(
        "ix_visual_identities_actor_id", "visual_identities", ["actor_id"]
    )
    op.create_table(
        "sonic_identities",
        sa.Column("identity_id", sa.String(36), nullable=False),
        sa.Column("actor_type", sa.String(32), nullable=False),
        sa.Column("actor_id", sa.String(36), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.PrimaryKeyConstraint("identity_id"),
    )
    op.create_index("ix_sonic_identities_actor_id", "sonic_identities", ["actor_id"])
    op.create_table(
        "generated_assets",
        sa.Column("asset_id", sa.String(36), nullable=False),
        sa.Column("actor_type", sa.String(32), nullable=False),
        sa.Column("actor_id", sa.String(36), nullable=False),
        sa.Column("kind", sa.String(32), nullable=False),
        sa.Column("canonical_identity_id", sa.String(36), nullable=False),
        sa.Column("filesystem_reference", sa.Text(), nullable=False),
        sa.Column("generated_at", sa.DateTime(), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.PrimaryKeyConstraint("asset_id"),
    )
    op.create_index(
        "ix_generated_assets_actor_id", "generated_assets", ["actor_id"]
    )


def downgrade() -> None:
    op.drop_table("generated_assets")
    op.drop_table("sonic_identities")
    op.drop_table("visual_identities")
    op.drop_table("leisure_routines")
    op.drop_table("creative_works")
    op.drop_table("collective_receptions")
    op.drop_table("public_information")
    op.drop_table("public_channels")
