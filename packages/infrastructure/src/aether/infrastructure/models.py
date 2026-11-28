from datetime import UTC, datetime
from typing import Any
from decimal import Decimal

from sqlalchemy import (
    JSON,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    Numeric,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.types import TypeDecorator


class Base(DeclarativeBase):
    pass


class UTCDateTime(TypeDecorator[datetime]):
    impl = DateTime(timezone=True)
    cache_ok = True

    def process_bind_param(
        self,
        value: datetime | None,
        dialect: object,
    ) -> datetime | None:
        if value is None:
            return None
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("Database timestamps must include a UTC offset")
        return value.astimezone(UTC).replace(tzinfo=None)

    def process_result_value(
        self,
        value: datetime | None,
        dialect: object,
    ) -> datetime | None:
        if value is None:
            return None
        if value.tzinfo is None:
            return value.replace(tzinfo=UTC)
        return value.astimezone(UTC)


class WorldClockModel(Base):
    __tablename__ = "world_clocks"

    world_id: Mapped[str] = mapped_column(String(36), nullable=False)
    timeline_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    current_time: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    __table_args__ = (
        Index("ix_world_clocks_world_id", "world_id"),
    )


class ScheduledEventModel(Base):
    __tablename__ = "scheduled_events"

    event_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    world_id: Mapped[str] = mapped_column(String(36), nullable=False)
    timeline_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("world_clocks.timeline_id"),
        nullable=False,
    )
    scheduled_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)
    event_type: Mapped[str] = mapped_column(String(128), nullable=False)
    source_type: Mapped[str] = mapped_column(String(128), nullable=False)
    source_id: Mapped[str] = mapped_column(String(256), nullable=False)
    caused_by: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    payload_version: Mapped[str] = mapped_column(String(32), nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    interruption_class: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending")
    failure_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    __table_args__ = (
        Index(
            "ix_scheduled_events_timeline_due",
            "timeline_id",
            "scheduled_at",
            "status",
        ),
    )


class EventLedgerModel(Base):
    __tablename__ = "event_ledger"

    event_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    world_id: Mapped[str] = mapped_column(String(36), nullable=False)
    timeline_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("world_clocks.timeline_id"),
        nullable=False,
    )
    occurred_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)
    recorded_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)
    sequence: Mapped[int] = mapped_column(Integer, nullable=False)
    event_type: Mapped[str] = mapped_column(String(128), nullable=False)
    source_type: Mapped[str] = mapped_column(String(128), nullable=False)
    source_id: Mapped[str] = mapped_column(String(256), nullable=False)
    caused_by: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    payload_version: Mapped[str] = mapped_column(String(32), nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    interruption_class: Mapped[str] = mapped_column(String(32), nullable=False)

    __table_args__ = (
        Index("ix_event_ledger_timeline_order", "timeline_id", "occurred_at", "sequence"),
        Index("ix_event_ledger_world_type", "world_id", "event_type"),
        UniqueConstraint(
            "timeline_id",
            "sequence",
            name="uq_event_ledger_timeline_sequence",
        ),
    )


class SimulationRunModel(Base):
    __tablename__ = "simulation_runs"

    simulation_run_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    operation: Mapped[str] = mapped_column(String(64), nullable=False)
    world_id: Mapped[str] = mapped_column(String(36), nullable=False)
    timeline_id: Mapped[str] = mapped_column(String(36), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    initial_time: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)
    target_time: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)
    final_time: Mapped[datetime | None] = mapped_column(UTCDateTime(), nullable=True)
    processed_event_ids: Mapped[list[str]] = mapped_column(
        JSON,
        nullable=False,
        default=list,
    )
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)

    __table_args__ = (
        Index("ix_simulation_runs_timeline_status", "timeline_id", "status"),
    )


class PublicChannelModel(Base):
    __tablename__ = "public_channels"

    channel_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    world_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)


class PublicInformationModel(Base):
    __tablename__ = "public_information"

    publication_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    world_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    channel_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    published_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)


class CollectiveReceptionModel(Base):
    __tablename__ = "collective_receptions"

    reception_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    publication_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    population_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    received_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)


class CreativeWorkModel(Base):
    __tablename__ = "creative_works"

    work_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    world_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)


class LeisureRoutineModel(Base):
    __tablename__ = "leisure_routines"

    routine_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    actor_type: Mapped[str] = mapped_column(String(32), nullable=False)
    actor_id: Mapped[str] = mapped_column(String(36), nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)


class VisualIdentityModel(Base):
    __tablename__ = "visual_identities"

    identity_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    actor_type: Mapped[str] = mapped_column(String(32), nullable=False)
    actor_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)


class SonicIdentityModel(Base):
    __tablename__ = "sonic_identities"

    identity_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    actor_type: Mapped[str] = mapped_column(String(32), nullable=False)
    actor_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)


class GeneratedAssetModel(Base):
    __tablename__ = "generated_assets"

    asset_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    actor_type: Mapped[str] = mapped_column(String(32), nullable=False)
    actor_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    kind: Mapped[str] = mapped_column(String(32), nullable=False)
    canonical_identity_id: Mapped[str] = mapped_column(String(36), nullable=False)
    filesystem_reference: Mapped[str] = mapped_column(Text, nullable=False)
    generated_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)


class CanonicalProposalModel(Base):
    __tablename__ = "canonical_proposals"

    proposal_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    world_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    entity_type: Mapped[str] = mapped_column(String(128), nullable=False)
    entity_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)


class CanonicalRecordModel(Base):
    __tablename__ = "canonical_records"

    record_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    proposal_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    world_id: Mapped[str] = mapped_column(String(36), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(128), nullable=False)
    entity_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    level: Mapped[int] = mapped_column(Integer, nullable=False)
    revision: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    supersedes_record_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)

    __table_args__ = (
        Index(
            "ix_canonical_records_entity",
            "world_id",
            "entity_type",
            "entity_id",
            "revision",
        ),
        Index("ix_canonical_records_proposal", "proposal_id"),
    )


class LlmInvocationModel(Base):
    __tablename__ = "llm_invocations"

    invocation_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    simulation_run_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("simulation_runs.simulation_run_id"),
        nullable=False,
    )
    requesting_agent: Mapped[str] = mapped_column(String(128), nullable=False)
    requested_capability: Mapped[str] = mapped_column(String(128), nullable=False)
    model: Mapped[str] = mapped_column(String(256), nullable=False)
    model_version: Mapped[str] = mapped_column(String(256), nullable=False)
    prompt_version: Mapped[str] = mapped_column(String(128), nullable=False)
    context_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    inference_parameters: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    response_reference: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    input_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    output_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(
        UTCDateTime(),
        nullable=True,
    )

    __table_args__ = (
        Index("ix_llm_invocations_run", "simulation_run_id"),
    )


class AgentProposalModel(Base):
    __tablename__ = "agent_proposals"

    proposal_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    simulation_run_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("simulation_runs.simulation_run_id"),
        nullable=False,
    )
    invocation_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("llm_invocations.invocation_id"),
        nullable=False,
    )
    proposal_type: Mapped[str] = mapped_column(String(128), nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    validation_status: Mapped[str] = mapped_column(String(32), nullable=False)
    rejection_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    application_result: Mapped[dict[str, Any] | None] = mapped_column(
        JSON,
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)

    __table_args__ = (
        Index("ix_agent_proposals_run", "simulation_run_id"),
    )


class NarrativePresentationModel(Base):
    __tablename__ = "narrative_presentations"

    presentation_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    simulation_run_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("simulation_runs.simulation_run_id"),
        nullable=False,
        unique=True,
    )
    protagonist_character_id: Mapped[str] = mapped_column(String(36), nullable=False)
    narrative_time: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    generated_content: Mapped[str] = mapped_column(Text, nullable=False)
    delivered_content: Mapped[str | None] = mapped_column(Text, nullable=True)
    confirmed_fact_ids: Mapped[list[str]] = mapped_column(
        JSON,
        nullable=False,
        default=list,
    )
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)
    delivered_at: Mapped[datetime | None] = mapped_column(
        UTCDateTime(),
        nullable=True,
    )


class PlayerKnowledgeModel(Base):
    __tablename__ = "player_knowledge"

    knowledge_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    simulation_run_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("simulation_runs.simulation_run_id"),
        nullable=False,
    )
    player_id: Mapped[str] = mapped_column(String(128), nullable=False)
    fact_key: Mapped[str] = mapped_column(String(512), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    source_presentation_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("narrative_presentations.presentation_id"),
        nullable=False,
    )
    acquired_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)

    __table_args__ = (
        Index("ix_player_knowledge_player", "player_id", "acquired_at"),
    )


class NarrativeStateModel(Base):
    __tablename__ = "narrative_states"

    state_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    simulation_run_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("simulation_runs.simulation_run_id"),
        nullable=False,
    )
    protagonist_character_id: Mapped[str] = mapped_column(String(36), nullable=False)
    scene_summary: Mapped[str] = mapped_column(Text, nullable=False)
    narrative_time: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)

    __table_args__ = (
        Index(
            "ix_narrative_states_protagonist_time",
            "protagonist_character_id",
            "narrative_time",
        ),
    )


class CharacterKnowledgeModel(Base):
    __tablename__ = "character_knowledge"

    knowledge_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    character_id: Mapped[str] = mapped_column(String(36), nullable=False)
    fact_key: Mapped[str] = mapped_column(String(512), nullable=False)
    statement: Mapped[str] = mapped_column(Text, nullable=False)
    source_event_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    acquisition_event_id: Mapped[str | None] = mapped_column(
        String(36),
        nullable=True,
    )
    acquired_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)
    confidence: Mapped[float] = mapped_column(nullable=False)
    epistemic_status: Mapped[str] = mapped_column(String(32), nullable=False)
    temporal_scope: Mapped[str | None] = mapped_column(Text, nullable=True)
    visible_in_character_context: Mapped[bool] = mapped_column(
        nullable=False,
        default=True,
    )

    __table_args__ = (
        Index(
            "ix_character_knowledge_character_time",
            "character_id",
            "acquired_at",
        ),
        Index("ix_character_knowledge_fact", "fact_key"),
    )


class InformationTransmissionModel(Base):
    __tablename__ = "information_transmissions"

    transmission_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    source_event_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    sender_character_id: Mapped[str | None] = mapped_column(
        String(36),
        nullable=True,
    )
    recipient_character_id: Mapped[str] = mapped_column(String(36), nullable=False)
    fact_key: Mapped[str] = mapped_column(String(512), nullable=False)
    statement: Mapped[str] = mapped_column(Text, nullable=False)
    medium: Mapped[str] = mapped_column(String(32), nullable=False)
    nature: Mapped[str] = mapped_column(String(32), nullable=False)
    sent_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)
    arrival_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    perceived_reliability: Mapped[float] = mapped_column(nullable=False)
    alterations: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    sender_intent: Mapped[str | None] = mapped_column(Text, nullable=True)
    reach: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_language_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    target_language_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    source_dialect_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    target_dialect_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    writing_system_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    presentation_language: Mapped[str | None] = mapped_column(Text, nullable=True)
    translation_semantics: Mapped[list[str]] = mapped_column(
        JSON, nullable=False, default=list
    )
    imperfect_translation: Mapped[bool] = mapped_column(nullable=False, default=False)

    __table_args__ = (
        Index(
            "ix_information_transmissions_arrival",
            "status",
            "arrival_at",
        ),
    )


class CharacterIdentityModel(Base):
    __tablename__ = "character_identities"

    identity_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    character_id: Mapped[str] = mapped_column(String(36), nullable=False, unique=True)
    display_name: Mapped[str] = mapped_column(Text, nullable=False)
    nature: Mapped[str | None] = mapped_column(Text, nullable=True)
    biography: Mapped[str | None] = mapped_column(Text, nullable=True)
    defining_attributes: Mapped[dict[str, str]] = mapped_column(JSON, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    source_type: Mapped[str] = mapped_column(String(128), nullable=False)
    source_id: Mapped[str] = mapped_column(Text, nullable=False)
    origin_event_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)


class PersonalityProfileModel(Base):
    __tablename__ = "personality_profiles"

    profile_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    character_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    traits: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    values: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    behavioral_tendencies: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    source_type: Mapped[str] = mapped_column(String(128), nullable=False)
    source_id: Mapped[str] = mapped_column(Text, nullable=False)
    origin_event_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)


class PsychologicalStateModel(Base):
    __tablename__ = "psychological_states"

    state_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    character_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    observed_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)
    emotions: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    behavioral_modes: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    cause_event_ids: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    source_type: Mapped[str] = mapped_column(String(128), nullable=False)
    source_id: Mapped[str] = mapped_column(Text, nullable=False)
    origin_event_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)


class RelationshipModel(Base):
    __tablename__ = "relationships"

    relationship_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    source_character_id: Mapped[str] = mapped_column(String(36), nullable=False)
    target_character_id: Mapped[str] = mapped_column(String(36), nullable=False)
    dimensions: Mapped[list[dict[str, Any]]] = mapped_column(JSON, nullable=False)
    hidden: Mapped[bool] = mapped_column(nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    source_type: Mapped[str] = mapped_column(String(128), nullable=False)
    source_id: Mapped[str] = mapped_column(Text, nullable=False)
    origin_event_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)

    __table_args__ = (
        UniqueConstraint(
            "source_character_id",
            "target_character_id",
            name="uq_relationship_direction",
        ),
        Index("ix_relationships_target", "target_character_id"),
    )


class MotiveModel(Base):
    __tablename__ = "motives"

    motive_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    character_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    source_type: Mapped[str] = mapped_column(String(128), nullable=False)
    source_id: Mapped[str] = mapped_column(Text, nullable=False)
    origin_event_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)


class GoalModel(Base):
    __tablename__ = "goals"

    goal_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    character_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    motive_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    parent_goal_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    desired_outcome: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    source_type: Mapped[str] = mapped_column(String(128), nullable=False)
    source_id: Mapped[str] = mapped_column(Text, nullable=False)
    origin_event_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)


class PlanModel(Base):
    __tablename__ = "plans"

    plan_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    character_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    goal_id: Mapped[str] = mapped_column(String(36), nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    source_type: Mapped[str] = mapped_column(String(128), nullable=False)
    source_id: Mapped[str] = mapped_column(Text, nullable=False)
    origin_event_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)


class PlanStepModel(Base):
    __tablename__ = "plan_steps"

    step_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    plan_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    sequence: Mapped[int] = mapped_column(Integer, nullable=False)
    action_intent: Mapped[str] = mapped_column(Text, nullable=False)
    required_capabilities: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    required_resources: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    required_knowledge_fact_keys: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    resource_effects: Mapped[list[dict[str, Any]]] = mapped_column(
        JSON,
        nullable=False,
        default=list,
    )
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    resolution_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_type: Mapped[str] = mapped_column(String(128), nullable=False)
    source_id: Mapped[str] = mapped_column(Text, nullable=False)
    origin_event_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)

    __table_args__ = (
        UniqueConstraint("plan_id", "sequence", name="uq_plan_step_sequence"),
    )


class NpcDecisionProposalModel(Base):
    __tablename__ = "npc_decision_proposals"

    proposal_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    request_id: Mapped[str] = mapped_column(String(36), nullable=False, unique=True)
    character_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    reaction: Mapped[str] = mapped_column(Text, nullable=False)
    decision_type: Mapped[str] = mapped_column(String(32), nullable=False)
    target_plan_step_id: Mapped[str | None] = mapped_column(
        String(36),
        nullable=True,
    )
    rationale: Mapped[str] = mapped_column(Text, nullable=False)
    required_resources: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    confidence: Mapped[float] = mapped_column(nullable=False)
    validation_requirements: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    rejection_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    context_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    context: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    application_result: Mapped[dict[str, str] | None] = mapped_column(
        JSON,
        nullable=True,
    )
    source_type: Mapped[str] = mapped_column(String(128), nullable=False)
    source_id: Mapped[str] = mapped_column(Text, nullable=False)
    origin_event_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)


class ResourceBalanceModel(Base):
    __tablename__ = "resource_balances"

    balance_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    owner_kind: Mapped[str] = mapped_column(String(32), nullable=False)
    owner_id: Mapped[str] = mapped_column(String(36), nullable=False)
    resource_code: Mapped[str] = mapped_column(String(256), nullable=False)
    resource_kind: Mapped[str] = mapped_column(String(32), nullable=False)
    quantity: Mapped[Decimal] = mapped_column(Numeric(24, 8), nullable=False)
    reserved: Mapped[Decimal] = mapped_column(Numeric(24, 8), nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False)

    __table_args__ = (
        UniqueConstraint(
            "owner_kind",
            "owner_id",
            "resource_code",
            name="uq_resource_balance_owner_code",
        ),
        Index("ix_resource_balances_owner", "owner_kind", "owner_id"),
    )


class ResourceReservationModel(Base):
    __tablename__ = "resource_reservations"

    reservation_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    scheduled_event_id: Mapped[str] = mapped_column(String(36), nullable=False)
    owner_kind: Mapped[str] = mapped_column(String(32), nullable=False)
    owner_id: Mapped[str] = mapped_column(String(36), nullable=False)
    resource_code: Mapped[str] = mapped_column(String(256), nullable=False)
    quantity: Mapped[Decimal] = mapped_column(Numeric(24, 8), nullable=False)
    applied: Mapped[bool] = mapped_column(nullable=False, default=False)
    cancelled: Mapped[bool] = mapped_column(nullable=False, default=False)

    __table_args__ = (
        Index("ix_resource_reservations_event", "scheduled_event_id"),
    )


class ResourceTransactionModel(Base):
    __tablename__ = "resource_transactions"

    transaction_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    owner_kind: Mapped[str] = mapped_column(String(32), nullable=False)
    owner_id: Mapped[str] = mapped_column(String(36), nullable=False)
    resource_code: Mapped[str] = mapped_column(String(256), nullable=False)
    delta: Mapped[Decimal] = mapped_column(Numeric(24, 8), nullable=False)
    resulting_quantity: Mapped[Decimal] = mapped_column(Numeric(24, 8), nullable=False)
    scheduled_event_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    event_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    simulation_run_id: Mapped[str | None] = mapped_column(
        String(36),
        nullable=True,
    )
    occurred_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)

    __table_args__ = (
        Index("ix_resource_transactions_event", "scheduled_event_id"),
        UniqueConstraint(
            "scheduled_event_id",
            "resource_code",
            name="uq_resource_transaction_event_code",
        ),
    )


class OrganizationIdentityModel(Base):
    __tablename__ = "organization_identities"

    identity_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    organization_id: Mapped[str] = mapped_column(
        String(36), nullable=False, unique=True
    )
    display_name: Mapped[str] = mapped_column(Text, nullable=False)
    purpose: Mapped[str] = mapped_column(Text, nullable=False)
    history: Mapped[str | None] = mapped_column(Text, nullable=True)
    interests: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    relationships: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    territory_references: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    internal_conflicts: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    source_type: Mapped[str] = mapped_column(String(128), nullable=False)
    source_id: Mapped[str] = mapped_column(Text, nullable=False)
    origin_event_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)


class OrganizationGovernanceModel(Base):
    __tablename__ = "organization_governance"

    governance_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    organization_id: Mapped[str] = mapped_column(
        String(36), nullable=False, unique=True
    )
    system: Mapped[str] = mapped_column(Text, nullable=False)
    decision_rules: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    role_definitions: Mapped[list[dict[str, Any]]] = mapped_column(
        JSON, nullable=False
    )
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    source_type: Mapped[str] = mapped_column(String(128), nullable=False)
    source_id: Mapped[str] = mapped_column(Text, nullable=False)
    origin_event_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)


class OrganizationMembershipModel(Base):
    __tablename__ = "organization_memberships"

    membership_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    organization_id: Mapped[str] = mapped_column(String(36), nullable=False)
    character_id: Mapped[str] = mapped_column(String(36), nullable=False)
    formal_roles: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    informal_roles: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    effective_influence: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    source_type: Mapped[str] = mapped_column(String(128), nullable=False)
    source_id: Mapped[str] = mapped_column(Text, nullable=False)
    origin_event_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)

    __table_args__ = (
        UniqueConstraint(
            "organization_id",
            "character_id",
            name="uq_organization_membership",
        ),
        Index("ix_organization_memberships_character", "character_id"),
    )


class OrganizationAuthorityGrantModel(Base):
    __tablename__ = "organization_authority_grants"

    grant_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    organization_id: Mapped[str] = mapped_column(String(36), nullable=False)
    character_id: Mapped[str] = mapped_column(String(36), nullable=False)
    role_code: Mapped[str] = mapped_column(String(128), nullable=False)
    permission_codes: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    formal: Mapped[bool] = mapped_column(nullable=False)
    basis: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    source_type: Mapped[str] = mapped_column(String(128), nullable=False)
    source_id: Mapped[str] = mapped_column(Text, nullable=False)
    origin_event_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)

    __table_args__ = (
        Index(
            "ix_organization_authority_principal",
            "organization_id",
            "character_id",
        ),
    )


class OrganizationMotiveModel(Base):
    __tablename__ = "organization_motives"

    motive_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    organization_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    internal_supporters: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    internal_opposition: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    source_type: Mapped[str] = mapped_column(String(128), nullable=False)
    source_id: Mapped[str] = mapped_column(Text, nullable=False)
    origin_event_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)


class OrganizationGoalModel(Base):
    __tablename__ = "organization_goals"

    goal_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    organization_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    motive_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    parent_goal_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    desired_outcome: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    source_type: Mapped[str] = mapped_column(String(128), nullable=False)
    source_id: Mapped[str] = mapped_column(Text, nullable=False)
    origin_event_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)


class OrganizationPlanModel(Base):
    __tablename__ = "organization_plans"

    plan_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    organization_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    goal_id: Mapped[str] = mapped_column(String(36), nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    source_type: Mapped[str] = mapped_column(String(128), nullable=False)
    source_id: Mapped[str] = mapped_column(Text, nullable=False)
    origin_event_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)


class OrganizationPlanStepModel(Base):
    __tablename__ = "organization_plan_steps"

    step_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    plan_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    sequence: Mapped[int] = mapped_column(Integer, nullable=False)
    action_intent: Mapped[str] = mapped_column(Text, nullable=False)
    required_capabilities: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    required_resources: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    required_knowledge_fact_keys: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    resource_effects: Mapped[list[dict[str, Any]]] = mapped_column(
        JSON, nullable=False
    )
    responsible_character_id: Mapped[str | None] = mapped_column(
        String(36), nullable=True
    )
    required_permission_codes: Mapped[list[str]] = mapped_column(
        JSON, nullable=False
    )
    resolution_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    source_type: Mapped[str] = mapped_column(String(128), nullable=False)
    source_id: Mapped[str] = mapped_column(Text, nullable=False)
    origin_event_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)

    __table_args__ = (
        UniqueConstraint(
            "plan_id",
            "sequence",
            name="uq_organization_plan_step_sequence",
        ),
    )


class OrganizationDecisionProposalModel(Base):
    __tablename__ = "organization_decision_proposals"

    proposal_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    request_id: Mapped[str] = mapped_column(String(36), nullable=False, unique=True)
    organization_id: Mapped[str] = mapped_column(
        String(36), nullable=False, index=True
    )
    responsible_character_id: Mapped[str | None] = mapped_column(
        String(36), nullable=True
    )
    reaction: Mapped[str] = mapped_column(Text, nullable=False)
    decision_type: Mapped[str] = mapped_column(String(32), nullable=False)
    target_plan_step_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    rationale: Mapped[str] = mapped_column(Text, nullable=False)
    required_resources: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    confidence: Mapped[float] = mapped_column(nullable=False)
    validation_requirements: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    rejection_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    context_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    context: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    application_result: Mapped[dict[str, str] | None] = mapped_column(
        JSON, nullable=True
    )
    source_type: Mapped[str] = mapped_column(String(128), nullable=False)
    source_id: Mapped[str] = mapped_column(Text, nullable=False)
    origin_event_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)


class LocationModel(Base):
    __tablename__ = "locations"

    location_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    world_id: Mapped[str] = mapped_column(String(36), nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    location_type: Mapped[str] = mapped_column(String(32), nullable=False)
    parent_location_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("locations.location_id"), nullable=True
    )
    terrain: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    climate: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    hydrology: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    flora_fauna: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    natural_resources: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    population_density: Mapped[str | None] = mapped_column(Text, nullable=True)
    strategic_tags: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    risk_tags: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    barrier_tags: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    source_type: Mapped[str] = mapped_column(String(128), nullable=False)
    source_id: Mapped[str] = mapped_column(Text, nullable=False)
    origin_event_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)

    __table_args__ = (Index("ix_locations_world_parent", "world_id", "parent_location_id"),)


class TerritoryClaimModel(Base):
    __tablename__ = "territory_claims"

    claim_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    location_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("locations.location_id"), nullable=False
    )
    semantics: Mapped[str] = mapped_column(String(32), nullable=False)
    owner_actor_type: Mapped[str | None] = mapped_column(String(32), nullable=True)
    owner_actor_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    controller_actor_type: Mapped[str | None] = mapped_column(String(32), nullable=True)
    controller_actor_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    basis: Mapped[str] = mapped_column(Text, nullable=False)
    source_type: Mapped[str] = mapped_column(String(128), nullable=False)
    source_id: Mapped[str] = mapped_column(Text, nullable=False)
    origin_event_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)


class InfrastructureNodeModel(Base):
    __tablename__ = "infrastructure_nodes"

    node_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    world_id: Mapped[str] = mapped_column(String(36), nullable=False)
    location_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("locations.location_id"), nullable=False
    )
    name: Mapped[str] = mapped_column(Text, nullable=False)
    node_type: Mapped[str] = mapped_column(String(128), nullable=False)
    availability: Mapped[str] = mapped_column(Text, nullable=False)
    capacity: Mapped[str | None] = mapped_column(Text, nullable=True)
    safety_tags: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    risk_tags: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    source_type: Mapped[str] = mapped_column(String(128), nullable=False)
    source_id: Mapped[str] = mapped_column(Text, nullable=False)
    origin_event_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)


class InfrastructureFacilityModel(Base):
    __tablename__ = "infrastructure_facilities"

    facility_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    node_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("infrastructure_nodes.node_id"), nullable=False
    )
    location_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("locations.location_id"), nullable=False
    )
    facility_type: Mapped[str] = mapped_column(String(128), nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    availability: Mapped[str] = mapped_column(Text, nullable=False)
    capacity: Mapped[str | None] = mapped_column(Text, nullable=True)
    resource_consumption: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    safety_tags: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    risk_tags: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    source_type: Mapped[str] = mapped_column(String(128), nullable=False)
    source_id: Mapped[str] = mapped_column(Text, nullable=False)
    origin_event_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)


class TransportRouteModel(Base):
    __tablename__ = "transport_routes"

    route_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    world_id: Mapped[str] = mapped_column(String(36), nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    start_location_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("locations.location_id"), nullable=False
    )
    end_location_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("locations.location_id"), nullable=False
    )
    modes: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    availability: Mapped[str] = mapped_column(Text, nullable=False)
    source_type: Mapped[str] = mapped_column(String(128), nullable=False)
    source_id: Mapped[str] = mapped_column(Text, nullable=False)
    origin_event_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)


class TransportRouteSegmentModel(Base):
    __tablename__ = "transport_route_segments"

    segment_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    route_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("transport_routes.route_id"), nullable=False
    )
    sequence: Mapped[int] = mapped_column(Integer, nullable=False)
    start_location_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("locations.location_id"), nullable=False
    )
    end_location_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("locations.location_id"), nullable=False
    )
    physical_distance: Mapped[Decimal] = mapped_column(Numeric(24, 8), nullable=False)
    distance_unit: Mapped[str] = mapped_column(String(64), nullable=False)
    base_duration_microseconds: Mapped[int] = mapped_column(Integer, nullable=False)
    mode: Mapped[str] = mapped_column(String(32), nullable=False)
    costs: Mapped[list[dict[str, str]]] = mapped_column(JSON, nullable=False)
    capacity: Mapped[str | None] = mapped_column(Text, nullable=True)
    availability: Mapped[str] = mapped_column(Text, nullable=False)
    resource_consumption: Mapped[list[dict[str, str]]] = mapped_column(
        JSON, nullable=False
    )
    safety_tags: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    risk_tags: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    source_type: Mapped[str] = mapped_column(String(128), nullable=False)
    source_id: Mapped[str] = mapped_column(Text, nullable=False)
    origin_event_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)

    __table_args__ = (
        UniqueConstraint("route_id", "sequence", name="uq_route_segment_sequence"),
    )


class ActorPositionModel(Base):
    __tablename__ = "actor_positions"

    actor_type: Mapped[str] = mapped_column(String(32), primary_key=True)
    actor_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    location_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("locations.location_id"), nullable=False
    )
    journey_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False)


class JourneyModel(Base):
    __tablename__ = "journeys"

    journey_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    world_id: Mapped[str] = mapped_column(String(36), nullable=False)
    timeline_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("world_clocks.timeline_id"), nullable=False
    )
    participants: Mapped[list[dict[str, str]]] = mapped_column(JSON, nullable=False)
    start_location_id: Mapped[str] = mapped_column(String(36), nullable=False)
    end_location_id: Mapped[str] = mapped_column(String(36), nullable=False)
    route_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("transport_routes.route_id"), nullable=False
    )
    segment_ids: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    resource_owner: Mapped[dict[str, str] | None] = mapped_column(JSON, nullable=True)
    costs: Mapped[list[dict[str, str]]] = mapped_column(JSON, nullable=False)
    resource_consumption: Mapped[list[dict[str, str]]] = mapped_column(
        JSON, nullable=False
    )
    started_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)
    expected_arrival_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)
    arrived_at: Mapped[datetime | None] = mapped_column(UTCDateTime(), nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    scheduled_event_id: Mapped[str] = mapped_column(String(36), nullable=False, unique=True)
    source_type: Mapped[str] = mapped_column(String(128), nullable=False)
    source_id: Mapped[str] = mapped_column(Text, nullable=False)
    origin_event_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)


class SpeciesModel(Base):
    __tablename__ = "species"

    species_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    world_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    organism_kind: Mapped[str] = mapped_column(String(32), nullable=False)
    anatomy: Mapped[Any] = mapped_column(JSON, nullable=False)
    physiology: Mapped[Any] = mapped_column(JSON, nullable=False)
    reproduction_model: Mapped[Any] = mapped_column(JSON, nullable=False)
    nutrition: Mapped[Any] = mapped_column(JSON, nullable=False)
    habitat: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    senses: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    adaptations: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    lifecycle_stages: Mapped[list[dict[str, Any]]] = mapped_column(JSON, nullable=False)
    resource_links: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    source_type: Mapped[str] = mapped_column(String(128), nullable=False)
    source_id: Mapped[str] = mapped_column(Text, nullable=False)
    origin_event_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)


class HabitatModel(Base):
    __tablename__ = "ecological_habitats"

    habitat_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    world_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    location_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("locations.location_id"), nullable=False
    )
    name: Mapped[str] = mapped_column(Text, nullable=False)
    habitat_type: Mapped[str] = mapped_column(String(128), nullable=False)
    habitability: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    species_ids: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    resources: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    resource_links: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    characteristics: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    source_type: Mapped[str] = mapped_column(String(128), nullable=False)
    source_id: Mapped[str] = mapped_column(Text, nullable=False)
    origin_event_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)


class PopulationModel(Base):
    __tablename__ = "populations"

    population_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    world_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    species_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("species.species_id"), nullable=False
    )
    location_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("locations.location_id"), nullable=False
    )
    name: Mapped[str] = mapped_column(Text, nullable=False)
    cohorts: Mapped[list[dict[str, Any]]] = mapped_column(JSON, nullable=False)
    aggregate_by_default: Mapped[bool] = mapped_column(nullable=False, default=True)
    resource_links: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    source_type: Mapped[str] = mapped_column(String(128), nullable=False)
    source_id: Mapped[str] = mapped_column(Text, nullable=False)
    origin_event_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)


class EcologicalProcessModel(Base):
    __tablename__ = "ecological_processes"

    process_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    world_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    location_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("locations.location_id"), nullable=False
    )
    process_type: Mapped[str] = mapped_column(String(128), nullable=False)
    measures: Mapped[dict[str, str]] = mapped_column(JSON, nullable=False)
    population_links: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    resource_links: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    source_type: Mapped[str] = mapped_column(String(128), nullable=False)
    source_id: Mapped[str] = mapped_column(Text, nullable=False)
    origin_event_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)


class HealthStateModel(Base):
    __tablename__ = "health_states"

    state_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    character_id: Mapped[str] = mapped_column(String(36), nullable=False, unique=True)
    species_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    physical_integrity: Mapped[str] = mapped_column(Text, nullable=False)
    consciousness: Mapped[str] = mapped_column(Text, nullable=False)
    ability_to_act: Mapped[str] = mapped_column(Text, nullable=False)
    ability_to_fight: Mapped[str] = mapped_column(Text, nullable=False)
    conditions: Mapped[list[dict[str, Any]]] = mapped_column(JSON, nullable=False)
    source_type: Mapped[str] = mapped_column(String(128), nullable=False)
    source_id: Mapped[str] = mapped_column(Text, nullable=False)
    origin_event_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)


class KnowledgeArtifactModel(Base):
    __tablename__ = "knowledge_artifacts"

    artifact_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    world_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    state: Mapped[str] = mapped_column(String(32), nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)


class TechnologyModel(Base):
    __tablename__ = "technologies"

    technology_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    world_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    state: Mapped[str] = mapped_column(String(32), nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)


class KnowledgeLifecycleRecordModel(Base):
    __tablename__ = "knowledge_lifecycle_records"

    record_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    entity_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    actor_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    state: Mapped[str] = mapped_column(String(32), nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)


class LanguageModel(Base):
    __tablename__ = "languages"

    language_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    world_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)


class DialectModel(Base):
    __tablename__ = "dialects"

    dialect_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    language_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("languages.language_id"), nullable=False, index=True
    )
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)


class WritingSystemModel(Base):
    __tablename__ = "writing_systems"

    writing_system_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    world_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)


class CharacterLanguageProficiencyModel(Base):
    __tablename__ = "character_language_proficiencies"

    proficiency_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    character_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    language_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("languages.language_id"), nullable=False, index=True
    )
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)

    __table_args__ = (
        UniqueConstraint(
            "character_id", "language_id", name="uq_character_language_proficiency"
        ),
    )


class EducationProgramModel(Base):
    __tablename__ = "education_programs"

    program_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    world_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    organization_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)


class EducationEnrollmentModel(Base):
    __tablename__ = "education_enrollments"

    enrollment_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    program_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("education_programs.program_id"),
        nullable=False,
        index=True,
    )
    character_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)


class LearningOpportunityModel(Base):
    __tablename__ = "learning_opportunities"

    opportunity_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    program_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    participant_character_id: Mapped[str] = mapped_column(
        String(36), nullable=False, index=True
    )
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)


class AssessmentOutcomeModel(Base):
    __tablename__ = "learning_assessment_outcomes"

    outcome_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    enrollment_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("education_enrollments.enrollment_id"),
        nullable=False,
        index=True,
    )
    character_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    source_event_id: Mapped[str] = mapped_column(String(36), nullable=False, unique=True)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)


class ReligionTraditionModel(Base):
    __tablename__ = "religion_traditions"

    tradition_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    world_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    organization_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)


class IndividualBeliefRecordModel(Base):
    __tablename__ = "individual_belief_records"

    belief_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    character_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    tradition_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)


class RitualCompletionModel(Base):
    __tablename__ = "religious_ritual_completions"

    completion_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    tradition_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("religion_traditions.tradition_id"),
        nullable=False,
        index=True,
    )
    actor_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    source_event_id: Mapped[str] = mapped_column(String(36), nullable=False, unique=True)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)


class MetaphysicalTruthModel(Base):
    __tablename__ = "metaphysical_truths"

    truth_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    world_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    disclosure_class: Mapped[str] = mapped_column(String(64), nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)


class NormativeSystemModel(Base):
    __tablename__ = "normative_systems"
    system_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    world_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    kind: Mapped[str] = mapped_column(String(32), nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)


class NormativeRuleModel(Base):
    __tablename__ = "normative_rules"
    rule_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    system_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)


class OffenseModel(Base):
    __tablename__ = "offenses"
    offense_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    system_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    rule_id: Mapped[str] = mapped_column(String(36), nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)


class LegalCaseModel(Base):
    __tablename__ = "legal_cases"
    case_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    world_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    system_id: Mapped[str] = mapped_column(String(36), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)


class InvestigationModel(Base):
    __tablename__ = "investigations"
    investigation_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    case_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    organization_id: Mapped[str] = mapped_column(String(36), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)


class EvidenceRecordModel(Base):
    __tablename__ = "evidence_records"
    evidence_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    investigation_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    case_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    visibility: Mapped[str] = mapped_column(String(32), nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)


class LegalProceedingModel(Base):
    __tablename__ = "legal_proceedings"
    proceeding_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    case_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)


class SanctionModel(Base):
    __tablename__ = "sanctions"
    sanction_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    case_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    proceeding_id: Mapped[str] = mapped_column(String(36), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)


class AppealModel(Base):
    __tablename__ = "appeals"
    appeal_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    case_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    proceeding_id: Mapped[str] = mapped_column(String(36), nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)


class OrganizationRelationModel(Base):
    __tablename__ = "organization_relations"
    relation_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    world_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    source_organization_id: Mapped[str] = mapped_column(String(36), nullable=False)
    target_organization_id: Mapped[str] = mapped_column(String(36), nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    __table_args__ = (
        UniqueConstraint(
            "source_organization_id",
            "target_organization_id",
            name="uq_organization_relation_direction",
        ),
    )


class TreatyModel(Base):
    __tablename__ = "treaties"
    treaty_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    world_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)


class DiplomaticActionModel(Base):
    __tablename__ = "diplomatic_actions"
    action_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    world_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    source_organization_id: Mapped[str] = mapped_column(String(36), nullable=False)
    target_organization_id: Mapped[str] = mapped_column(String(36), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)


class StrategicConflictModel(Base):
    __tablename__ = "strategic_conflicts"
    conflict_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    world_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    escalation_stage: Mapped[str] = mapped_column(String(128), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)


class SecurityThreatModel(Base):
    __tablename__ = "security_threats"
    threat_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    world_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)


class SecurityIncidentModel(Base):
    __tablename__ = "security_incidents"
    incident_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    threat_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)


class IntelligenceOperationModel(Base):
    __tablename__ = "intelligence_operations"
    operation_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    world_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    organization_id: Mapped[str] = mapped_column(String(36), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)


class SecurityResolutionModel(Base):
    __tablename__ = "security_resolutions"
    resolution_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    threat_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    source_event_id: Mapped[str] = mapped_column(String(36), nullable=False, unique=True)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)


class CharacterSheetModel(Base):
    __tablename__ = "character_sheets"
    character_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    world_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    ruleset_id: Mapped[str] = mapped_column(String(128), nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)


class CharacterProgressionEvidenceModel(Base):
    __tablename__ = "character_progression_evidence"
    evidence_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    character_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    world_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)


class CharacterProgressionProposalModel(Base):
    __tablename__ = "character_progression_proposals"
    proposal_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    request_id: Mapped[str] = mapped_column(String(36), nullable=False, unique=True)
    character_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    world_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)


class CharacterProgressionValidationModel(Base):
    __tablename__ = "character_progression_validations"
    validation_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    proposal_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)


class CharacterProgressionApplicationModel(Base):
    __tablename__ = "character_progression_applications"
    application_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    proposal_id: Mapped[str] = mapped_column(String(36), nullable=False, unique=True)
    character_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)


class SimulationTierStateModel(Base):
    __tablename__ = "simulation_tier_states"

    entity_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    world_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    entity_type: Mapped[str] = mapped_column(String(64), nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)


class AggregatePopulationSourceLinkModel(Base):
    __tablename__ = "aggregate_population_source_links"

    population_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    cohort_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)


class MaterializedIndividualLinkModel(Base):
    __tablename__ = "materialized_individual_links"

    character_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    population_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    cohort_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)


class SimulationTierTransitionResultModel(Base):
    __tablename__ = "simulation_tier_transition_results"

    request_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    world_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)


class CultureDefinitionModel(Base):
    __tablename__ = "culture_definitions"

    culture_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    world_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)


class SocialGroupModel(Base):
    __tablename__ = "social_groups"

    group_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    world_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    semantic_category: Mapped[str] = mapped_column(String(128), nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)


class IndividualCulturalAffiliationModel(Base):
    __tablename__ = "individual_cultural_affiliations"

    affiliation_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    character_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    target_type: Mapped[str] = mapped_column(String(32), nullable=False)
    target_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    visibility: Mapped[str] = mapped_column(String(32), nullable=False)
    effective_from: Mapped[datetime] = mapped_column(
        UTCDateTime(), nullable=False
    )
    effective_until: Mapped[datetime | None] = mapped_column(
        UTCDateTime(), nullable=True
    )
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)

    __table_args__ = (
        Index(
            "ix_cultural_affiliations_character_effective",
            "character_id",
            "effective_from",
            "effective_until",
        ),
    )


class CulturalChangeRecordModel(Base):
    __tablename__ = "cultural_change_records"

    record_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    world_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    target_type: Mapped[str] = mapped_column(String(32), nullable=False)
    target_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    source_event_id: Mapped[str] = mapped_column(
        String(36), nullable=False, index=True
    )
    occurred_at: Mapped[datetime] = mapped_column(
        UTCDateTime(), nullable=False
    )
    cause_tags: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)

    __table_args__ = (
        Index(
            "ix_cultural_change_target_time",
            "target_type",
            "target_id",
            "occurred_at",
        ),
    )
