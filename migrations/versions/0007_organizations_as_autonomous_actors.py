"""Add organizations as autonomous actors.

Revision ID: 0007
Revises: 0006
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0007"
down_revision: str | Sequence[str] | None = "0006"
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
        "organization_identities",
        sa.Column("identity_id", sa.String(36), primary_key=True),
        sa.Column("organization_id", sa.String(36), nullable=False, unique=True),
        sa.Column("display_name", sa.Text(), nullable=False),
        sa.Column("purpose", sa.Text(), nullable=False),
        sa.Column("history", sa.Text(), nullable=True),
        sa.Column("interests", sa.JSON(), nullable=False),
        sa.Column("relationships", sa.JSON(), nullable=False),
        sa.Column("territory_references", sa.JSON(), nullable=False),
        sa.Column("internal_conflicts", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        *_provenance_columns(),
    )
    op.create_table(
        "organization_governance",
        sa.Column("governance_id", sa.String(36), primary_key=True),
        sa.Column("organization_id", sa.String(36), nullable=False, unique=True),
        sa.Column("system", sa.Text(), nullable=False),
        sa.Column("decision_rules", sa.JSON(), nullable=False),
        sa.Column("role_definitions", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        *_provenance_columns(),
    )
    op.create_table(
        "organization_memberships",
        sa.Column("membership_id", sa.String(36), primary_key=True),
        sa.Column("organization_id", sa.String(36), nullable=False),
        sa.Column("character_id", sa.String(36), nullable=False),
        sa.Column("formal_roles", sa.JSON(), nullable=False),
        sa.Column("informal_roles", sa.JSON(), nullable=False),
        sa.Column("effective_influence", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        *_provenance_columns(),
        sa.UniqueConstraint(
            "organization_id", "character_id", name="uq_organization_membership"
        ),
    )
    op.create_index(
        "ix_organization_memberships_character",
        "organization_memberships",
        ["character_id"],
    )
    op.create_table(
        "organization_authority_grants",
        sa.Column("grant_id", sa.String(36), primary_key=True),
        sa.Column("organization_id", sa.String(36), nullable=False),
        sa.Column("character_id", sa.String(36), nullable=False),
        sa.Column("role_code", sa.String(128), nullable=False),
        sa.Column("permission_codes", sa.JSON(), nullable=False),
        sa.Column("formal", sa.Boolean(), nullable=False),
        sa.Column("basis", sa.Text(), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        *_provenance_columns(),
    )
    op.create_index(
        "ix_organization_authority_principal",
        "organization_authority_grants",
        ["organization_id", "character_id"],
    )
    op.create_table(
        "organization_motives",
        sa.Column("motive_id", sa.String(36), primary_key=True),
        sa.Column("organization_id", sa.String(36), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("internal_supporters", sa.JSON(), nullable=False),
        sa.Column("internal_opposition", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        *_provenance_columns(),
    )
    op.create_index(
        "ix_organization_motives_organization",
        "organization_motives",
        ["organization_id"],
    )
    op.create_table(
        "organization_goals",
        sa.Column("goal_id", sa.String(36), primary_key=True),
        sa.Column("organization_id", sa.String(36), nullable=False),
        sa.Column("motive_id", sa.String(36), nullable=True),
        sa.Column("parent_goal_id", sa.String(36), nullable=True),
        sa.Column("desired_outcome", sa.Text(), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        *_provenance_columns(),
    )
    op.create_index(
        "ix_organization_goals_organization",
        "organization_goals",
        ["organization_id"],
    )
    op.create_table(
        "organization_plans",
        sa.Column("plan_id", sa.String(36), primary_key=True),
        sa.Column("organization_id", sa.String(36), nullable=False),
        sa.Column("goal_id", sa.String(36), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        *_provenance_columns(),
    )
    op.create_index(
        "ix_organization_plans_organization",
        "organization_plans",
        ["organization_id"],
    )
    op.create_table(
        "organization_plan_steps",
        sa.Column("step_id", sa.String(36), primary_key=True),
        sa.Column("plan_id", sa.String(36), nullable=False),
        sa.Column("sequence", sa.Integer(), nullable=False),
        sa.Column("action_intent", sa.Text(), nullable=False),
        sa.Column("required_capabilities", sa.JSON(), nullable=False),
        sa.Column("required_resources", sa.JSON(), nullable=False),
        sa.Column("required_knowledge_fact_keys", sa.JSON(), nullable=False),
        sa.Column("resource_effects", sa.JSON(), nullable=False),
        sa.Column("responsible_character_id", sa.String(36), nullable=True),
        sa.Column("required_permission_codes", sa.JSON(), nullable=False),
        sa.Column("resolution_reason", sa.Text(), nullable=True),
        sa.Column("status", sa.String(32), nullable=False),
        *_provenance_columns(),
        sa.UniqueConstraint(
            "plan_id",
            "sequence",
            name="uq_organization_plan_step_sequence",
        ),
    )
    op.create_index(
        "ix_organization_plan_steps_plan",
        "organization_plan_steps",
        ["plan_id"],
    )
    op.create_table(
        "organization_decision_proposals",
        sa.Column("proposal_id", sa.String(36), primary_key=True),
        sa.Column("request_id", sa.String(36), nullable=False, unique=True),
        sa.Column("organization_id", sa.String(36), nullable=False),
        sa.Column("responsible_character_id", sa.String(36), nullable=True),
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
        *_provenance_columns(),
    )
    op.create_index(
        "ix_organization_decision_proposals_organization",
        "organization_decision_proposals",
        ["organization_id"],
    )


def downgrade() -> None:
    op.drop_table("organization_decision_proposals")
    op.drop_table("organization_plan_steps")
    op.drop_table("organization_plans")
    op.drop_table("organization_goals")
    op.drop_table("organization_motives")
    op.drop_table("organization_authority_grants")
    op.drop_table("organization_memberships")
    op.drop_table("organization_governance")
    op.drop_table("organization_identities")
