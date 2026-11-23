"""Create resource balances, reservations, and transactions.

Revision ID: 0006
Revises: 0005
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0006"
down_revision: str | Sequence[str] | None = "0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "plan_steps",
        sa.Column(
            "resource_effects",
            sa.JSON(),
            nullable=False,
            server_default="[]",
        ),
    )
    op.create_table(
        "resource_balances",
        sa.Column("balance_id", sa.String(36), nullable=False),
        sa.Column("owner_kind", sa.String(32), nullable=False),
        sa.Column("owner_id", sa.String(36), nullable=False),
        sa.Column("resource_code", sa.String(256), nullable=False),
        sa.Column("resource_kind", sa.String(32), nullable=False),
        sa.Column("quantity", sa.Numeric(24, 8), nullable=False),
        sa.Column("reserved", sa.Numeric(24, 8), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("balance_id"),
        sa.UniqueConstraint(
            "owner_kind",
            "owner_id",
            "resource_code",
            name="uq_resource_balance_owner_code",
        ),
    )
    op.create_index(
        "ix_resource_balances_owner",
        "resource_balances",
        ["owner_kind", "owner_id"],
    )
    op.create_table(
        "resource_reservations",
        sa.Column("reservation_id", sa.String(36), nullable=False),
        sa.Column("scheduled_event_id", sa.String(36), nullable=False),
        sa.Column("owner_kind", sa.String(32), nullable=False),
        sa.Column("owner_id", sa.String(36), nullable=False),
        sa.Column("resource_code", sa.String(256), nullable=False),
        sa.Column("quantity", sa.Numeric(24, 8), nullable=False),
        sa.Column("applied", sa.Boolean(), nullable=False),
        sa.Column("cancelled", sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint("reservation_id"),
    )
    op.create_index(
        "ix_resource_reservations_event",
        "resource_reservations",
        ["scheduled_event_id"],
    )
    op.create_table(
        "resource_transactions",
        sa.Column("transaction_id", sa.String(36), nullable=False),
        sa.Column("owner_kind", sa.String(32), nullable=False),
        sa.Column("owner_id", sa.String(36), nullable=False),
        sa.Column("resource_code", sa.String(256), nullable=False),
        sa.Column("delta", sa.Numeric(24, 8), nullable=False),
        sa.Column("resulting_quantity", sa.Numeric(24, 8), nullable=False),
        sa.Column("scheduled_event_id", sa.String(36), nullable=True),
        sa.Column("event_id", sa.String(36), nullable=True),
        sa.Column("simulation_run_id", sa.String(36), nullable=True),
        sa.Column("occurred_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("transaction_id"),
        sa.UniqueConstraint(
            "scheduled_event_id",
            "resource_code",
            name="uq_resource_transaction_event_code",
        ),
    )
    op.create_index(
        "ix_resource_transactions_event",
        "resource_transactions",
        ["scheduled_event_id"],
    )


def downgrade() -> None:
    op.drop_table("resource_transactions")
    op.drop_table("resource_reservations")
    op.drop_table("resource_balances")
    op.drop_column("plan_steps", "resource_effects")
