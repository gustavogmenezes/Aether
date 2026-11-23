from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from .character import (
    CharacterIdentity,
    Goal,
    Motive,
    PersonalityProfile,
    Plan,
    PlanStep,
    PsychologicalState,
    RecordProvenance,
    Relationship,
)
from .knowledge import KnowledgeContextEntry


class NpcDecisionType(str, Enum):
    EXECUTE_PLAN_STEP = "execute-plan-step"
    DEFER = "defer"
    REACT = "react"
    REVISE_PLAN = "revise-plan"


class NpcDecisionProposalStatus(str, Enum):
    PROPOSED = "proposed"
    VALIDATED = "validated"
    REJECTED = "rejected"


class CapabilityAvailability(BaseModel):
    model_config = ConfigDict(frozen=True)

    name: str
    available: bool
    notes: str | None = None


class ResourceAvailability(BaseModel):
    model_config = ConfigDict(frozen=True)

    name: str
    available: bool
    notes: str | None = None


class DecisionCircumstance(BaseModel):
    model_config = ConfigDict(frozen=True)

    fact_key: str
    statement: str
    observed_at: datetime

    @field_validator("observed_at")
    @classmethod
    def require_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("Circumstance time must include a UTC offset")
        return value


class NpcPlanContext(BaseModel):
    model_config = ConfigDict(frozen=True)

    plan: Plan
    steps: tuple[PlanStep, ...] = ()


class NpcDecisionContext(BaseModel):
    model_config = ConfigDict(frozen=True)

    request_id: UUID
    character_id: UUID
    as_of: datetime
    identity: CharacterIdentity
    personality: PersonalityProfile | None = None
    psychological_state: PsychologicalState | None = None
    knowledge: tuple[KnowledgeContextEntry, ...] = ()
    capabilities: tuple[CapabilityAvailability, ...] = ()
    resources: tuple[ResourceAvailability, ...] = ()
    motives: tuple[Motive, ...] = ()
    goals: tuple[Goal, ...] = ()
    plans: tuple[NpcPlanContext, ...] = ()
    relationships: tuple[Relationship, ...] = ()
    circumstances: tuple[DecisionCircumstance, ...] = ()

    @field_validator("as_of")
    @classmethod
    def require_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("Decision context time must include a UTC offset")
        return value


class NpcDecisionProposal(BaseModel):
    model_config = ConfigDict(frozen=True)

    proposal_id: UUID
    request_id: UUID
    character_id: UUID
    reaction: str
    decision_type: NpcDecisionType
    target_plan_step_id: UUID | None
    rationale: str
    required_resources: tuple[str, ...] = ()
    confidence: float = Field(ge=0, le=1)
    validation_requirements: tuple[str, ...] = ()
    status: NpcDecisionProposalStatus = NpcDecisionProposalStatus.PROPOSED
    rejection_reason: str | None = None
    context_hash: str
    application_result: dict[str, str] | None = None
    provenance: RecordProvenance


class NpcDecisionResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    proposal: NpcDecisionProposal
    idempotent_replay: bool = False


class PlanStepScheduleResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    proposal_id: UUID
    plan_step_id: UUID
    scheduled_event_id: UUID
    idempotent_replay: bool = False
