from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator
from .resources import ResourceEffect


class CharacterRecordStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    ARCHIVED = "archived"


class GoalStatus(str, Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    ABANDONED = "abandoned"
    BLOCKED = "blocked"


class PlanStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    COMPLETED = "completed"
    ABANDONED = "abandoned"
    FAILED = "failed"


class PlanStepStatus(str, Enum):
    PENDING = "pending"
    SCHEDULED = "scheduled"
    COMPLETED = "completed"
    ABANDONED = "abandoned"
    FAILED = "failed"


class RecordProvenance(BaseModel):
    model_config = ConfigDict(frozen=True)

    source_type: str
    source_id: str
    origin_event_id: UUID | None = None
    created_at: datetime
    updated_at: datetime
    version: int = Field(ge=1)

    @field_validator("source_type", "source_id")
    @classmethod
    def require_non_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Provenance fields cannot be blank")
        return value

    @field_validator("created_at", "updated_at")
    @classmethod
    def require_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("Provenance timestamps must include a UTC offset")
        return value


class CharacterIdentity(BaseModel):
    model_config = ConfigDict(frozen=True)

    identity_id: UUID
    character_id: UUID
    display_name: str
    nature: str | None = None
    biography: str | None = None
    defining_attributes: dict[str, str] = Field(default_factory=dict)
    status: CharacterRecordStatus = CharacterRecordStatus.ACTIVE
    provenance: RecordProvenance


class PersonalityProfile(BaseModel):
    model_config = ConfigDict(frozen=True)

    profile_id: UUID
    character_id: UUID
    traits: tuple[str, ...] = ()
    values: tuple[str, ...] = ()
    behavioral_tendencies: tuple[str, ...] = ()
    status: CharacterRecordStatus = CharacterRecordStatus.ACTIVE
    provenance: RecordProvenance


class PsychologicalState(BaseModel):
    model_config = ConfigDict(frozen=True)

    state_id: UUID
    character_id: UUID
    observed_at: datetime
    emotions: tuple[str, ...] = ()
    behavioral_modes: tuple[str, ...] = ()
    description: str | None = None
    cause_event_ids: tuple[UUID, ...] = ()
    status: CharacterRecordStatus = CharacterRecordStatus.ACTIVE
    provenance: RecordProvenance

    @field_validator("observed_at")
    @classmethod
    def require_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("Psychological state time must include a UTC offset")
        return value


class RelationshipDimension(BaseModel):
    model_config = ConfigDict(frozen=True)

    name: str
    disposition: str
    description: str | None = None


class Relationship(BaseModel):
    model_config = ConfigDict(frozen=True)

    relationship_id: UUID
    source_character_id: UUID
    target_character_id: UUID
    dimensions: tuple[RelationshipDimension, ...] = ()
    hidden: bool = False
    status: CharacterRecordStatus = CharacterRecordStatus.ACTIVE
    provenance: RecordProvenance

    @field_validator("target_character_id")
    @classmethod
    def require_distinct_characters(cls, value: UUID, info: Any) -> UUID:
        if value == info.data.get("source_character_id"):
            raise ValueError("A relationship must connect distinct characters")
        return value


class Motive(BaseModel):
    model_config = ConfigDict(frozen=True)

    motive_id: UUID
    character_id: UUID
    description: str
    status: CharacterRecordStatus = CharacterRecordStatus.ACTIVE
    provenance: RecordProvenance


class Goal(BaseModel):
    model_config = ConfigDict(frozen=True)

    goal_id: UUID
    character_id: UUID
    motive_id: UUID | None = None
    parent_goal_id: UUID | None = None
    desired_outcome: str
    status: GoalStatus = GoalStatus.ACTIVE
    provenance: RecordProvenance


class Plan(BaseModel):
    model_config = ConfigDict(frozen=True)

    plan_id: UUID
    character_id: UUID
    goal_id: UUID
    name: str
    status: PlanStatus = PlanStatus.DRAFT
    provenance: RecordProvenance


class PlanStep(BaseModel):
    model_config = ConfigDict(frozen=True)

    step_id: UUID
    plan_id: UUID
    sequence: int = Field(ge=0)
    action_intent: str
    required_capabilities: tuple[str, ...] = ()
    required_resources: tuple[str, ...] = ()
    required_knowledge_fact_keys: tuple[str, ...] = ()
    resource_effects: tuple[ResourceEffect, ...] = ()
    resolution_reason: str | None = None
    status: PlanStepStatus = PlanStepStatus.PENDING
    provenance: RecordProvenance
