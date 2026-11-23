"""Add auditable plan-step resolution reasons.

Revision ID: 0005
Revises: 0004
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0005"
down_revision: str | Sequence[str] | None = "0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "plan_steps",
        sa.Column("resolution_reason", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("plan_steps", "resolution_reason")
