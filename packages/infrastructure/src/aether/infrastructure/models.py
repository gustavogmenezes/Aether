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
