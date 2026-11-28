"""Add knowledge lifecycle, language, education, and belief persistence.

Revision ID: 0010
Revises: 0009
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0010"
down_revision: str | Sequence[str] | None = "0009"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("information_transmissions") as batch:
        for name in (
            "source_language_id",
            "target_language_id",
            "source_dialect_id",
            "target_dialect_id",
            "writing_system_id",
        ):
            batch.add_column(sa.Column(name, sa.String(36), nullable=True))
        batch.add_column(sa.Column("presentation_language", sa.Text(), nullable=True))
        batch.add_column(
            sa.Column(
                "translation_semantics",
                sa.JSON(),
                nullable=False,
                server_default="[]",
            )
        )
        batch.add_column(
            sa.Column(
                "imperfect_translation",
                sa.Boolean(),
                nullable=False,
                server_default=sa.false(),
            )
        )

    for name, key, scoped in (
        ("knowledge_artifacts", "artifact_id", True),
        ("technologies", "technology_id", True),
    ):
        op.create_table(
            name,
            sa.Column(key, sa.String(36), primary_key=True),
            sa.Column("world_id", sa.String(36), nullable=False),
            sa.Column("state", sa.String(32), nullable=False),
            sa.Column("payload", sa.JSON(), nullable=False),
        )
        if scoped:
            op.create_index(f"ix_{name}_world_id", name, ["world_id"])

    op.create_table(
        "knowledge_lifecycle_records",
        sa.Column("record_id", sa.String(36), primary_key=True),
        sa.Column("entity_id", sa.String(36), nullable=False),
        sa.Column("actor_id", sa.String(36), nullable=True),
        sa.Column("state", sa.String(32), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
    )
    op.create_index(
        "ix_knowledge_lifecycle_records_entity_id",
        "knowledge_lifecycle_records",
        ["entity_id"],
    )
    op.create_index(
        "ix_knowledge_lifecycle_records_actor_id",
        "knowledge_lifecycle_records",
        ["actor_id"],
    )

    op.create_table(
        "languages",
        sa.Column("language_id", sa.String(36), primary_key=True),
        sa.Column("world_id", sa.String(36), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
    )
    op.create_index("ix_languages_world_id", "languages", ["world_id"])
    op.create_table(
        "dialects",
        sa.Column("dialect_id", sa.String(36), primary_key=True),
        sa.Column(
            "language_id",
            sa.String(36),
            sa.ForeignKey("languages.language_id"),
            nullable=False,
        ),
        sa.Column("payload", sa.JSON(), nullable=False),
    )
    op.create_index("ix_dialects_language_id", "dialects", ["language_id"])
    op.create_table(
        "writing_systems",
        sa.Column("writing_system_id", sa.String(36), primary_key=True),
        sa.Column("world_id", sa.String(36), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
    )
    op.create_index(
        "ix_writing_systems_world_id", "writing_systems", ["world_id"]
    )
    op.create_table(
        "character_language_proficiencies",
        sa.Column("proficiency_id", sa.String(36), primary_key=True),
        sa.Column("character_id", sa.String(36), nullable=False),
        sa.Column(
            "language_id",
            sa.String(36),
            sa.ForeignKey("languages.language_id"),
            nullable=False,
        ),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.UniqueConstraint(
            "character_id",
            "language_id",
            name="uq_character_language_proficiency",
        ),
    )
    op.create_index(
        "ix_character_language_proficiencies_character_id",
        "character_language_proficiencies",
        ["character_id"],
    )
    op.create_index(
        "ix_character_language_proficiencies_language_id",
        "character_language_proficiencies",
        ["language_id"],
    )

    op.create_table(
        "education_programs",
        sa.Column("program_id", sa.String(36), primary_key=True),
        sa.Column("world_id", sa.String(36), nullable=False),
        sa.Column("organization_id", sa.String(36), nullable=True),
        sa.Column("payload", sa.JSON(), nullable=False),
    )
    op.create_index(
        "ix_education_programs_world_id", "education_programs", ["world_id"]
    )
    op.create_table(
        "education_enrollments",
        sa.Column("enrollment_id", sa.String(36), primary_key=True),
        sa.Column(
            "program_id",
            sa.String(36),
            sa.ForeignKey("education_programs.program_id"),
            nullable=False,
        ),
        sa.Column("character_id", sa.String(36), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
    )
    op.create_index(
        "ix_education_enrollments_program_id",
        "education_enrollments",
        ["program_id"],
    )
    op.create_index(
        "ix_education_enrollments_character_id",
        "education_enrollments",
        ["character_id"],
    )
    op.create_table(
        "learning_opportunities",
        sa.Column("opportunity_id", sa.String(36), primary_key=True),
        sa.Column("program_id", sa.String(36), nullable=True),
        sa.Column("participant_character_id", sa.String(36), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
    )
    op.create_index(
        "ix_learning_opportunities_program_id",
        "learning_opportunities",
        ["program_id"],
    )
    op.create_index(
        "ix_learning_opportunities_participant_character_id",
        "learning_opportunities",
        ["participant_character_id"],
    )
    op.create_table(
        "learning_assessment_outcomes",
        sa.Column("outcome_id", sa.String(36), primary_key=True),
        sa.Column(
            "enrollment_id",
            sa.String(36),
            sa.ForeignKey("education_enrollments.enrollment_id"),
            nullable=False,
        ),
        sa.Column("character_id", sa.String(36), nullable=False),
        sa.Column("source_event_id", sa.String(36), nullable=False, unique=True),
        sa.Column("payload", sa.JSON(), nullable=False),
    )
    op.create_index(
        "ix_learning_assessment_outcomes_enrollment_id",
        "learning_assessment_outcomes",
        ["enrollment_id"],
    )
    op.create_index(
        "ix_learning_assessment_outcomes_character_id",
        "learning_assessment_outcomes",
        ["character_id"],
    )

    op.create_table(
        "religion_traditions",
        sa.Column("tradition_id", sa.String(36), primary_key=True),
        sa.Column("world_id", sa.String(36), nullable=False),
        sa.Column("organization_id", sa.String(36), nullable=True),
        sa.Column("payload", sa.JSON(), nullable=False),
    )
    op.create_index(
        "ix_religion_traditions_world_id", "religion_traditions", ["world_id"]
    )
    op.create_table(
        "individual_belief_records",
        sa.Column("belief_id", sa.String(36), primary_key=True),
        sa.Column("character_id", sa.String(36), nullable=False),
        sa.Column("tradition_id", sa.String(36), nullable=True),
        sa.Column("payload", sa.JSON(), nullable=False),
    )
    op.create_index(
        "ix_individual_belief_records_character_id",
        "individual_belief_records",
        ["character_id"],
    )
    op.create_table(
        "religious_ritual_completions",
        sa.Column("completion_id", sa.String(36), primary_key=True),
        sa.Column(
            "tradition_id",
            sa.String(36),
            sa.ForeignKey("religion_traditions.tradition_id"),
            nullable=False,
        ),
        sa.Column("actor_id", sa.String(36), nullable=False),
        sa.Column("source_event_id", sa.String(36), nullable=False, unique=True),
        sa.Column("payload", sa.JSON(), nullable=False),
    )
    op.create_index(
        "ix_religious_ritual_completions_tradition_id",
        "religious_ritual_completions",
        ["tradition_id"],
    )
    op.create_index(
        "ix_religious_ritual_completions_actor_id",
        "religious_ritual_completions",
        ["actor_id"],
    )
    op.create_table(
        "metaphysical_truths",
        sa.Column("truth_id", sa.String(36), primary_key=True),
        sa.Column("world_id", sa.String(36), nullable=False),
        sa.Column("disclosure_class", sa.String(64), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
    )
    op.create_index(
        "ix_metaphysical_truths_world_id",
        "metaphysical_truths",
        ["world_id"],
    )


def downgrade() -> None:
    for table in (
        "metaphysical_truths",
        "religious_ritual_completions",
        "individual_belief_records",
        "religion_traditions",
        "learning_assessment_outcomes",
        "learning_opportunities",
        "education_enrollments",
        "education_programs",
        "character_language_proficiencies",
        "writing_systems",
        "dialects",
        "languages",
        "knowledge_lifecycle_records",
        "technologies",
        "knowledge_artifacts",
    ):
        op.drop_table(table)
    with op.batch_alter_table("information_transmissions") as batch:
        for name in (
            "imperfect_translation",
            "translation_semantics",
            "presentation_language",
            "writing_system_id",
            "target_dialect_id",
            "source_dialect_id",
            "target_language_id",
            "source_language_id",
        ):
            batch.drop_column(name)
