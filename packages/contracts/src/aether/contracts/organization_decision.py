from datetime import datetime
from enum import Enum
from hashlib import sha256
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from .character import RecordProvenance
from .npc_decision import CapabilityAvailability, DecisionCircumstance, ResourceAvailability
from .organization import (
    OrganizationAuthorityGrant,
    OrganizationGoal,
    OrganizationGovernance,
    OrganizationIdentity,
    OrganizationMembership,
    OrganizationMotive,
    OrganizationPlan,
    OrganizationPlanStep,
)


class OrganizationDecisionType(str, Enum):
    EXECUTE_PLAN_STEP = "execute-plan-step"
    DEFER = "defer"
    REACT = "react"
    REVISE_PLAN = "revise-plan"


class OrganizationDecisionProposalStatus(str, Enum):
    PROPOSED = "proposed"
    VALIDATED = "validated"
    REJECTED = "rejected"


class OrganizationPlanContext(BaseModel):
    model_config = ConfigDict(frozen=True)

    plan: OrganizationPlan
    steps: tuple[OrganizationPlanStep, ...] = ()


class OrganizationDecisionContext(BaseModel):
    model_config = ConfigDict(frozen=True)

    request_id: UUID
    organization_id: UUID
    as_of: datetime
    identity: OrganizationIdentity
    governance: OrganizationGovernance
    memberships: tuple[OrganizationMembership, ...] = ()
    authority_grants: tuple[OrganizationAuthorityGrant, ...] = ()
    facts: tuple[DecisionCircumstance, ...] = ()
    capabilities: tuple[CapabilityAvailability, ...] = ()
    resources: tuple[ResourceAvailability, ...] = ()
    motives: tuple[OrganizationMotive, ...] = ()
    goals: tuple[OrganizationGoal, ...] = ()
    plans: tuple[OrganizationPlanContext, ...] = ()
    circumstances: tuple[DecisionCircumstance, ...] = ()

    @field_validator("as_of")
    @classmethod
    def require_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("Organization decision context time must include a UTC offset")
        return value


class OrganizationDecisionProposal(BaseModel):
    model_config = ConfigDict(frozen=True)

    proposal_id: UUID
    request_id: UUID
    organization_id: UUID
    responsible_character_id: UUID | None = None
    reaction: str
    decision_type: OrganizationDecisionType
    target_plan_step_id: UUID | None
    rationale: str
    required_resources: tuple[str, ...] = ()
    confidence: float = Field(ge=0, le=1)
    validation_requirements: tuple[str, ...] = ()
    status: OrganizationDecisionProposalStatus = (
        OrganizationDecisionProposalStatus.PROPOSED
    )
    rejection_reason: str | None = None
    context_hash: str
    application_result: dict[str, str] | None = None
    provenance: RecordProvenance


class OrganizationDecisionResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    proposal: OrganizationDecisionProposal
    idempotent_replay: bool = False


class OrganizationPlanStepScheduleResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    proposal_id: UUID
    plan_step_id: UUID
    scheduled_event_id: UUID
    idempotent_replay: bool = False


def organization_context_hash(context: OrganizationDecisionContext) -> str:
    return sha256(context.model_dump_json().encode("utf-8")).hexdigest()
