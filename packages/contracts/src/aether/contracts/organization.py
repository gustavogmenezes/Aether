from enum import Enum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from .character import (
    GoalStatus,
    PlanStatus,
    PlanStepStatus,
    RecordProvenance,
)
from .resources import ResourceEffect


class OrganizationStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    DISSOLVED = "dissolved"
    ARCHIVED = "archived"


class MembershipStatus(str, Enum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    ENDED = "ended"


class OrganizationIdentity(BaseModel):
    model_config = ConfigDict(frozen=True)

    identity_id: UUID
    organization_id: UUID
    display_name: str
    purpose: str
    history: str | None = None
    interests: tuple[str, ...] = ()
    relationships: tuple[str, ...] = ()
    territory_references: tuple[str, ...] = ()
    internal_conflicts: tuple[str, ...] = ()
    status: OrganizationStatus = OrganizationStatus.ACTIVE
    provenance: RecordProvenance


class OrganizationRole(BaseModel):
    model_config = ConfigDict(frozen=True)

    role_code: str
    description: str
    permission_codes: tuple[str, ...] = ()

    @field_validator("role_code")
    @classmethod
    def role_code_must_not_be_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Organization role code cannot be blank")
        return value


class OrganizationGovernance(BaseModel):
    model_config = ConfigDict(frozen=True)

    governance_id: UUID
    organization_id: UUID
    system: str
    decision_rules: tuple[str, ...] = ()
    role_definitions: tuple[OrganizationRole, ...] = ()
    status: OrganizationStatus = OrganizationStatus.ACTIVE
    provenance: RecordProvenance


class OrganizationMembership(BaseModel):
    model_config = ConfigDict(frozen=True)

    membership_id: UUID
    organization_id: UUID
    character_id: UUID
    formal_roles: tuple[str, ...] = ()
    informal_roles: tuple[str, ...] = ()
    effective_influence: tuple[str, ...] = ()
    status: MembershipStatus = MembershipStatus.ACTIVE
    provenance: RecordProvenance


class OrganizationAuthorityGrant(BaseModel):
    model_config = ConfigDict(frozen=True)

    grant_id: UUID
    organization_id: UUID
    character_id: UUID
    role_code: str
    permission_codes: tuple[str, ...] = ()
    formal: bool = True
    basis: str
    status: OrganizationStatus = OrganizationStatus.ACTIVE
    provenance: RecordProvenance


class OrganizationMotive(BaseModel):
    model_config = ConfigDict(frozen=True)

    motive_id: UUID
    organization_id: UUID
    description: str
    internal_supporters: tuple[str, ...] = ()
    internal_opposition: tuple[str, ...] = ()
    status: OrganizationStatus = OrganizationStatus.ACTIVE
    provenance: RecordProvenance


class OrganizationGoal(BaseModel):
    model_config = ConfigDict(frozen=True)

    goal_id: UUID
    organization_id: UUID
    motive_id: UUID | None = None
    parent_goal_id: UUID | None = None
    desired_outcome: str
    status: GoalStatus = GoalStatus.ACTIVE
    provenance: RecordProvenance


class OrganizationPlan(BaseModel):
    model_config = ConfigDict(frozen=True)

    plan_id: UUID
    organization_id: UUID
    goal_id: UUID
    name: str
    status: PlanStatus = PlanStatus.DRAFT
    provenance: RecordProvenance


class OrganizationPlanStep(BaseModel):
    model_config = ConfigDict(frozen=True)

    step_id: UUID
    plan_id: UUID
    sequence: int = Field(ge=0)
    action_intent: str
    required_capabilities: tuple[str, ...] = ()
    required_resources: tuple[str, ...] = ()
    required_knowledge_fact_keys: tuple[str, ...] = ()
    resource_effects: tuple[ResourceEffect, ...] = ()
    responsible_character_id: UUID | None = None
    required_permission_codes: tuple[str, ...] = ()
    resolution_reason: str | None = None
    status: PlanStepStatus = PlanStepStatus.PENDING
    provenance: RecordProvenance
