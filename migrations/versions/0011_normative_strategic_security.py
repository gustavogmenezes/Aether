"""Add normative, strategic, diplomatic, and security foundations.

Revision ID: 0011
Revises: 0010
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0011"
down_revision: str | Sequence[str] | None = "0010"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _json_table(name: str, key: str, columns: tuple[tuple, ...] = ()) -> None:
    op.create_table(
        name,
        sa.Column(key, sa.String(36), primary_key=True),
        *(sa.Column(column, type_, **options) for column, type_, options in columns),
        sa.Column("payload", sa.JSON(), nullable=False),
    )


def upgrade() -> None:
    _json_table(
        "normative_systems",
        "system_id",
        (
            ("world_id", sa.String(36), {"nullable": False}),
            ("kind", sa.String(32), {"nullable": False}),
        ),
    )
    op.create_index("ix_normative_systems_world_id", "normative_systems", ["world_id"])
    _json_table(
        "normative_rules",
        "rule_id",
        (("system_id", sa.String(36), {"nullable": False}),),
    )
    op.create_index("ix_normative_rules_system_id", "normative_rules", ["system_id"])
    _json_table(
        "offenses",
        "offense_id",
        (
            ("system_id", sa.String(36), {"nullable": False}),
            ("rule_id", sa.String(36), {"nullable": False}),
        ),
    )
    op.create_index("ix_offenses_system_id", "offenses", ["system_id"])
    _json_table(
        "legal_cases",
        "case_id",
        (
            ("world_id", sa.String(36), {"nullable": False}),
            ("system_id", sa.String(36), {"nullable": False}),
            ("status", sa.String(32), {"nullable": False}),
        ),
    )
    op.create_index("ix_legal_cases_world_id", "legal_cases", ["world_id"])
    _json_table(
        "investigations",
        "investigation_id",
        (
            ("case_id", sa.String(36), {"nullable": False}),
            ("organization_id", sa.String(36), {"nullable": False}),
            ("status", sa.String(32), {"nullable": False}),
        ),
    )
    op.create_index("ix_investigations_case_id", "investigations", ["case_id"])
    _json_table(
        "evidence_records",
        "evidence_id",
        (
            ("investigation_id", sa.String(36), {"nullable": False}),
            ("case_id", sa.String(36), {"nullable": False}),
            ("visibility", sa.String(32), {"nullable": False}),
        ),
    )
    op.create_index(
        "ix_evidence_records_investigation_id",
        "evidence_records",
        ["investigation_id"],
    )
    op.create_index("ix_evidence_records_case_id", "evidence_records", ["case_id"])
    _json_table(
        "legal_proceedings",
        "proceeding_id",
        (
            ("case_id", sa.String(36), {"nullable": False}),
            ("status", sa.String(32), {"nullable": False}),
        ),
    )
    op.create_index(
        "ix_legal_proceedings_case_id", "legal_proceedings", ["case_id"]
    )
    _json_table(
        "sanctions",
        "sanction_id",
        (
            ("case_id", sa.String(36), {"nullable": False}),
            ("proceeding_id", sa.String(36), {"nullable": False}),
            ("status", sa.String(32), {"nullable": False}),
        ),
    )
    op.create_index("ix_sanctions_case_id", "sanctions", ["case_id"])
    _json_table(
        "appeals",
        "appeal_id",
        (
            ("case_id", sa.String(36), {"nullable": False}),
            ("proceeding_id", sa.String(36), {"nullable": False}),
        ),
    )
    op.create_index("ix_appeals_case_id", "appeals", ["case_id"])
    _json_table(
        "organization_relations",
        "relation_id",
        (
            ("world_id", sa.String(36), {"nullable": False}),
            ("source_organization_id", sa.String(36), {"nullable": False}),
            ("target_organization_id", sa.String(36), {"nullable": False}),
        ),
    )
    op.create_index(
        "ix_organization_relations_world_id", "organization_relations", ["world_id"]
    )
    op.create_index(
        "uq_organization_relation_direction",
        "organization_relations",
        ["source_organization_id", "target_organization_id"],
        unique=True,
    )
    _json_table(
        "treaties",
        "treaty_id",
        (
            ("world_id", sa.String(36), {"nullable": False}),
            ("status", sa.String(32), {"nullable": False}),
        ),
    )
    op.create_index("ix_treaties_world_id", "treaties", ["world_id"])
    _json_table(
        "diplomatic_actions",
        "action_id",
        (
            ("world_id", sa.String(36), {"nullable": False}),
            ("source_organization_id", sa.String(36), {"nullable": False}),
            ("target_organization_id", sa.String(36), {"nullable": False}),
            ("status", sa.String(32), {"nullable": False}),
        ),
    )
    op.create_index(
        "ix_diplomatic_actions_world_id", "diplomatic_actions", ["world_id"]
    )
    _json_table(
        "strategic_conflicts",
        "conflict_id",
        (
            ("world_id", sa.String(36), {"nullable": False}),
            ("escalation_stage", sa.String(128), {"nullable": False}),
            ("status", sa.String(32), {"nullable": False}),
        ),
    )
    op.create_index(
        "ix_strategic_conflicts_world_id", "strategic_conflicts", ["world_id"]
    )
    _json_table(
        "security_threats",
        "threat_id",
        (
            ("world_id", sa.String(36), {"nullable": False}),
            ("status", sa.String(32), {"nullable": False}),
        ),
    )
    op.create_index("ix_security_threats_world_id", "security_threats", ["world_id"])
    _json_table(
        "security_incidents",
        "incident_id",
        (("threat_id", sa.String(36), {"nullable": False}),),
    )
    op.create_index(
        "ix_security_incidents_threat_id", "security_incidents", ["threat_id"]
    )
    _json_table(
        "intelligence_operations",
        "operation_id",
        (
            ("world_id", sa.String(36), {"nullable": False}),
            ("organization_id", sa.String(36), {"nullable": False}),
            ("status", sa.String(32), {"nullable": False}),
        ),
    )
    op.create_index(
        "ix_intelligence_operations_world_id",
        "intelligence_operations",
        ["world_id"],
    )
    _json_table(
        "security_resolutions",
        "resolution_id",
        (
            ("threat_id", sa.String(36), {"nullable": False}),
            ("source_event_id", sa.String(36), {"nullable": False}),
        ),
    )
    op.create_index(
        "ix_security_resolutions_threat_id", "security_resolutions", ["threat_id"]
    )
    op.create_index(
        "uq_security_resolutions_source_event_id",
        "security_resolutions",
        ["source_event_id"],
        unique=True,
    )


def downgrade() -> None:
    for table in (
        "security_resolutions",
        "intelligence_operations",
        "security_incidents",
        "security_threats",
        "strategic_conflicts",
        "diplomatic_actions",
        "treaties",
        "organization_relations",
        "appeals",
        "sanctions",
        "legal_proceedings",
        "evidence_records",
        "investigations",
        "legal_cases",
        "offenses",
        "normative_rules",
        "normative_systems",
    ):
        op.drop_table(table)
