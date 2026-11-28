from enum import Enum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from .character import RecordProvenance


class HealthConditionCategory(str, Enum):
    DISEASE = "disease"
    INFECTION = "infection"
    INJURY = "injury"
    DISABILITY = "disability"
    AGING = "aging"
    RECOVERY = "recovery"
    REHABILITATION = "rehabilitation"
    OTHER = "other"


class HealthConditionStatus(str, Enum):
    ACTIVE = "active"
    RECOVERING = "recovering"
    CHRONIC = "chronic"
    RESOLVED = "resolved"


class HealthCondition(BaseModel):
    model_config = ConfigDict(frozen=True)

    condition_id: UUID
    code: str
    category: HealthConditionCategory
    severity: str | None = None
    status: HealthConditionStatus = HealthConditionStatus.ACTIVE
    description: str | None = None
    cause: str
    metadata: dict[str, str] = Field(default_factory=dict)

    @field_validator("code", "cause")
    @classmethod
    def require_non_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Health condition fields cannot be blank")
        return value


class HealthState(BaseModel):
    model_config = ConfigDict(frozen=True)

    state_id: UUID
    character_id: UUID
    species_id: UUID | None = None
    physical_integrity: str
    consciousness: str
    ability_to_act: str
    ability_to_fight: str
    conditions: tuple[HealthCondition, ...] = ()
    provenance: RecordProvenance

    @model_validator(mode="after")
    def health_dimensions_are_distinct_and_condition_ids_unique(self) -> "HealthState":
        dimensions = (
            self.physical_integrity,
            self.consciousness,
            self.ability_to_act,
            self.ability_to_fight,
        )
        if any(not dimension.strip() for dimension in dimensions):
            raise ValueError("Health dimensions cannot be blank")
        ids = [condition.condition_id for condition in self.conditions]
        if len(ids) != len(set(ids)):
            raise ValueError("Health condition IDs must be unique")
        return self


class HealthConditionChangePayload(BaseModel):
    model_config = ConfigDict(frozen=True)

    character_id: UUID
    cause: str
    add_conditions: tuple[HealthCondition, ...] = ()
    remove_condition_ids: tuple[UUID, ...] = ()
    dimension_changes: dict[str, str] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_change(self) -> "HealthConditionChangePayload":
        if not self.cause.strip():
            raise ValueError("Health condition change cause cannot be blank")
        if not self.add_conditions and not self.remove_condition_ids and not self.dimension_changes:
            raise ValueError("Health condition change requires an explicit payload")
        supported = {
            "physical_integrity",
            "consciousness",
            "ability_to_act",
            "ability_to_fight",
        }
        if not set(self.dimension_changes).issubset(supported):
            raise ValueError("Health change contains an unsupported dimension")
        if any(not value.strip() for value in self.dimension_changes.values()):
            raise ValueError("Health dimension changes cannot be blank")
        return self

