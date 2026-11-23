"""Create personality, relationship, goal, plan, and NPC decision state.

Revision ID: 0004
Revises: 0003
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0004"
down_revision: str | Sequence[str] | None = "0003"
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
        "character_identities",
        sa.Column("identity_id", sa.String(36), nullable=False),
        sa.Column("character_id", sa.String(36), nullable=False, unique=True),
        sa.Column("display_name", sa.Text(), nullable=False),
        sa.Column("nature", sa.Text(), nullable=True),
        sa.Column("biography", sa.Text(), nullable=True),
        sa.Column("defining_attributes", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        *_provenance_columns(),
        sa.PrimaryKeyConstraint("identity_id"),
    )
    op.create_table(
        "personality_profiles",
        sa.Column("profile_id", sa.String(36), nullable=False),
        sa.Column("character_id", sa.String(36), nullable=False),
        sa.Column("traits", sa.JSON(), nullable=False),
        sa.Column("values", sa.JSON(), nullable=False),
        sa.Column("behavioral_tendencies", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        *_provenance_columns(),
        sa.PrimaryKeyConstraint("profile_id"),
    )
    op.create_index("ix_personality_profiles_character_id", "personality_profiles", ["character_id"])
    op.create_table(
        "psychological_states",
        sa.Column("state_id", sa.String(36), nullable=False),
        sa.Column("character_id", sa.String(36), nullable=False),
        sa.Column("observed_at", sa.DateTime(), nullable=False),
        sa.Column("emotions", sa.JSON(), nullable=False),
        sa.Column("behavioral_modes", sa.JSON(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("cause_event_ids", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        *_provenance_columns(),
        sa.PrimaryKeyConstraint("state_id"),
    )
    op.create_index("ix_psychological_states_character_id", "psychological_states", ["character_id"])
    op.create_table(
        "relationships",
        sa.Column("relationship_id", sa.String(36), nullable=False),
        sa.Column("source_character_id", sa.String(36), nullable=False),
        sa.Column("target_character_id", sa.String(36), nullable=False),
        sa.Column("dimensions", sa.JSON(), nullable=False),
        sa.Column("hidden", sa.Boolean(), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        *_provenance_columns(),
        sa.PrimaryKeyConstraint("relationship_id"),
        sa.UniqueConstraint(
            "source_character_id",
            "target_character_id",
            name="uq_relationship_direction",
        ),
    )
    op.create_index("ix_relationships_target", "relationships", ["target_character_id"])
    op.create_table(
        "motives",
        sa.Column("motive_id", sa.String(36), nullable=False),
        sa.Column("character_id", sa.String(36), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        *_provenance_columns(),
        sa.PrimaryKeyConstraint("motive_id"),
    )
    op.create_index("ix_motives_character_id", "motives", ["character_id"])
    op.create_table(
        "goals",
        sa.Column("goal_id", sa.String(36), nullable=False),
        sa.Column("character_id", sa.String(36), nullable=False),
        sa.Column("motive_id", sa.String(36), nullable=True),
        sa.Column("parent_goal_id", sa.String(36), nullable=True),
        sa.Column("desired_outcome", sa.Text(), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        *_provenance_columns(),
        sa.PrimaryKeyConstraint("goal_id"),
    )
    op.create_index("ix_goals_character_id", "goals", ["character_id"])
    op.create_table(
        "plans",
        sa.Column("plan_id", sa.String(36), nullable=False),
        sa.Column("character_id", sa.String(36), nullable=False),
        sa.Column("goal_id", sa.String(36), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        *_provenance_columns(),
        sa.PrimaryKeyConstraint("plan_id"),
    )
    op.create_index("ix_plans_character_id", "plans", ["character_id"])
    op.create_table(
        "plan_steps",
        sa.Column("step_id", sa.String(36), nullable=False),
        sa.Column("plan_id", sa.String(36), nullable=False),
        sa.Column("sequence", sa.Integer(), nullable=False),
        sa.Column("action_intent", sa.Text(), nullable=False),
        sa.Column("required_capabilities", sa.JSON(), nullable=False),
        sa.Column("required_resources", sa.JSON(), nullable=False),
        sa.Column("required_knowledge_fact_keys", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        *_provenance_columns(),
        sa.PrimaryKeyConstraint("step_id"),
        sa.UniqueConstraint("plan_id", "sequence", name="uq_plan_step_sequence"),
    )
    op.create_index("ix_plan_steps_plan_id", "plan_steps", ["plan_id"])
    op.create_table(
        "npc_decision_proposals",
        sa.Column("proposal_id", sa.String(36), nullable=False),
        sa.Column("request_id", sa.String(36), nullable=False, unique=True),
        sa.Column("character_id", sa.String(36), nullable=False),
        sa.Column("reaction", sa.Text(), nullable=False),
        sa.Column("decision_type", sa.String(32), nullable=False),
        sa.Column("target_plan_step_id", sa.String(36), nullable=True),
        sa.Column("rationale", sa.Text(), nullable=False),
        sa.Column("required_resources", sa.JSON(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("validation_requirements", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("rejection_reason", sa.Text(), nullable=True),
        sa.Column("context_hash", sa.String(128), nullable=False),
        sa.Column("context", sa.JSON(), nullable=False),
        sa.Column("application_result", sa.JSON(), nullable=True),
        sa.Column("source_type", sa.String(128), nullable=False),
        sa.Column("source_id", sa.Text(), nullable=False),
        sa.Column("origin_event_id", sa.String(36), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("proposal_id"),
    )
    op.create_index(
        "ix_npc_decision_proposals_character_id",
        "npc_decision_proposals",
        ["character_id"],
    )


def downgrade() -> None:
    op.drop_table("npc_decision_proposals")
    op.drop_table("plan_steps")
    op.drop_table("plans")
    op.drop_table("goals")
    op.drop_table("motives")
    op.drop_table("relationships")
    op.drop_table("psychological_states")
    op.drop_table("personality_profiles")
    op.drop_table("character_identities")
