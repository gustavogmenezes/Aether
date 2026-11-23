"""Create the transactional core schema.

Revision ID: 0001
Revises:
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0001"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "world_clocks",
        sa.Column("world_id", sa.String(36), nullable=False),
        sa.Column("timeline_id", sa.String(36), nullable=False),
        sa.Column("current_time", sa.DateTime(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("timeline_id"),
    )
    op.create_index("ix_world_clocks_world_id", "world_clocks", ["world_id"])

    op.create_table(
        "simulation_runs",
        sa.Column("simulation_run_id", sa.String(36), nullable=False),
        sa.Column("operation", sa.String(64), nullable=False),
        sa.Column("world_id", sa.String(36), nullable=False),
        sa.Column("timeline_id", sa.String(36), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("initial_time", sa.DateTime(), nullable=False),
        sa.Column("target_time", sa.DateTime(), nullable=False),
        sa.Column("final_time", sa.DateTime(), nullable=True),
        sa.Column("processed_event_ids", sa.JSON(), nullable=False),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("simulation_run_id"),
    )
    op.create_index(
        "ix_simulation_runs_timeline_status",
        "simulation_runs",
        ["timeline_id", "status"],
    )

    op.create_table(
        "scheduled_events",
        sa.Column("event_id", sa.String(36), nullable=False),
        sa.Column("world_id", sa.String(36), nullable=False),
        sa.Column("timeline_id", sa.String(36), nullable=False),
        sa.Column("scheduled_at", sa.DateTime(), nullable=False),
        sa.Column("event_type", sa.String(128), nullable=False),
        sa.Column("source_type", sa.String(128), nullable=False),
        sa.Column("source_id", sa.String(256), nullable=False),
        sa.Column("caused_by", sa.JSON(), nullable=False),
        sa.Column("priority", sa.Integer(), nullable=False),
        sa.Column("payload_version", sa.String(32), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("interruption_class", sa.String(32), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("failure_reason", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["timeline_id"], ["world_clocks.timeline_id"]),
        sa.PrimaryKeyConstraint("event_id"),
    )
    op.create_index(
        "ix_scheduled_events_timeline_due",
        "scheduled_events",
        ["timeline_id", "scheduled_at", "status"],
    )

    op.create_table(
        "event_ledger",
        sa.Column("event_id", sa.String(36), nullable=False),
        sa.Column("world_id", sa.String(36), nullable=False),
        sa.Column("timeline_id", sa.String(36), nullable=False),
        sa.Column("occurred_at", sa.DateTime(), nullable=False),
        sa.Column("recorded_at", sa.DateTime(), nullable=False),
        sa.Column("sequence", sa.Integer(), nullable=False),
        sa.Column("event_type", sa.String(128), nullable=False),
        sa.Column("source_type", sa.String(128), nullable=False),
        sa.Column("source_id", sa.String(256), nullable=False),
        sa.Column("caused_by", sa.JSON(), nullable=False),
        sa.Column("priority", sa.Integer(), nullable=False),
        sa.Column("payload_version", sa.String(32), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("interruption_class", sa.String(32), nullable=False),
        sa.ForeignKeyConstraint(["timeline_id"], ["world_clocks.timeline_id"]),
        sa.PrimaryKeyConstraint("event_id"),
        sa.UniqueConstraint(
            "timeline_id",
            "sequence",
            name="uq_event_ledger_timeline_sequence",
        ),
    )
    op.create_index(
        "ix_event_ledger_timeline_order",
        "event_ledger",
        ["timeline_id", "occurred_at", "sequence"],
    )
    op.create_index(
        "ix_event_ledger_world_type",
        "event_ledger",
        ["world_id", "event_type"],
    )

    op.create_table(
        "llm_invocations",
        sa.Column("invocation_id", sa.String(36), nullable=False),
        sa.Column("simulation_run_id", sa.String(36), nullable=False),
        sa.Column("requesting_agent", sa.String(128), nullable=False),
        sa.Column("requested_capability", sa.String(128), nullable=False),
        sa.Column("model", sa.String(256), nullable=False),
        sa.Column("model_version", sa.String(256), nullable=False),
        sa.Column("prompt_version", sa.String(128), nullable=False),
        sa.Column("context_hash", sa.String(128), nullable=False),
        sa.Column("inference_parameters", sa.JSON(), nullable=False),
        sa.Column("response_reference", sa.Text(), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("input_tokens", sa.Integer(), nullable=True),
        sa.Column("output_tokens", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(
            ["simulation_run_id"],
            ["simulation_runs.simulation_run_id"],
        ),
        sa.PrimaryKeyConstraint("invocation_id"),
    )
    op.create_index(
        "ix_llm_invocations_run",
        "llm_invocations",
        ["simulation_run_id"],
    )

    op.create_table(
        "agent_proposals",
        sa.Column("proposal_id", sa.String(36), nullable=False),
        sa.Column("simulation_run_id", sa.String(36), nullable=False),
        sa.Column("invocation_id", sa.String(36), nullable=False),
        sa.Column("proposal_type", sa.String(128), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("validation_status", sa.String(32), nullable=False),
        sa.Column("rejection_reason", sa.Text(), nullable=True),
        sa.Column("application_result", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["simulation_run_id"],
            ["simulation_runs.simulation_run_id"],
        ),
        sa.ForeignKeyConstraint(
            ["invocation_id"],
            ["llm_invocations.invocation_id"],
        ),
        sa.PrimaryKeyConstraint("proposal_id"),
    )
    op.create_index(
        "ix_agent_proposals_run",
        "agent_proposals",
        ["simulation_run_id"],
    )


def downgrade() -> None:
    op.drop_table("agent_proposals")
    op.drop_table("llm_invocations")
    op.drop_table("event_ledger")
    op.drop_table("scheduled_events")
    op.drop_table("simulation_runs")
    op.drop_table("world_clocks")
