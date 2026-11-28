from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from .character import CharacterIdentity, RecordProvenance


class SimulationTier(str, Enum):
    TIER_1 = "tier-1"
    TIER_2 = "tier-2"
    TIER_3 = "tier-3"


class SimulationTierState(BaseModel):
    model_config = ConfigDict(frozen=True)

    state_id: UUID
    world_id: UUID
    entity_type: str
    entity_id: UUID
    tier: SimulationTier
    resolution_reason: str
    provenance: RecordProvenance

    @field_validator("entity_type", "resolution_reason")
    @classmethod
    def require_non_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Tier state fields cannot be blank")
        return value


class AggregatePopulationSourceLink(BaseModel):
    model_config = ConfigDict(frozen=True)

    link_id: UUID
    population_id: UUID
    cohort_id: UUID
    aggregate_count: Decimal = Field(ge=0)
    materialized_count: int = Field(ge=0)
    population_version: int = Field(ge=1)
    provenance: RecordProvenance

    @model_validator(mode="after")
    def validate_accounting(self) -> "AggregatePopulationSourceLink":
        if Decimal(self.materialized_count) > self.aggregate_count:
            raise ValueError("Materialized count cannot exceed aggregate count")
        return self

    @property
    def remaining_aggregate_count(self) -> Decimal:
        return self.aggregate_count - Decimal(self.materialized_count)


class MaterializedIndividualLink(BaseModel):
    model_config = ConfigDict(frozen=True)

    link_id: UUID
    world_id: UUID
    population_id: UUID
    cohort_id: UUID
    character_id: UUID
    compatible_traits: dict[str, Any] = Field(default_factory=dict)
    history_event_ids: tuple[UUID, ...] = ()
    provenance: RecordProvenance


class MaterializationSpecification(BaseModel):
    model_config = ConfigDict(frozen=True)

    character_id: UUID
    identity: CharacterIdentity
    cohort_id: UUID
    compatible_traits: dict[str, Any] = Field(default_factory=dict)
    history_event_ids: tuple[UUID, ...] = ()
    supplied_species_id: UUID | None = None
    supplied_location_id: UUID | None = None
    supplied_lifecycle_stage: str | None = None

    @model_validator(mode="after")
    def validate_character(self) -> "MaterializationSpecification":
        if self.identity.character_id != self.character_id:
            raise ValueError("Materialization identity does not match character ID")
        return self


class TierTransitionOperation(str, Enum):
    MATERIALIZE = "materialize"
    PROMOTE = "promote"
    DEMOTE = "demote"
    CONSOLIDATE = "consolidate"


class SimulationTierTransitionRequest(BaseModel):
    model_config = ConfigDict(frozen=True)

    request_id: UUID
    world_id: UUID
    operation: TierTransitionOperation
    target_tier: SimulationTier
    character_ids: tuple[UUID, ...]
    expected_tier_versions: dict[UUID, int] = Field(default_factory=dict)
    resolution_reason: str
    requested_at: datetime
    provenance: RecordProvenance
    population_id: UUID | None = None
    expected_population_version: int | None = None
    requested_count: int | None = None
    materializations: tuple[MaterializationSpecification, ...] = ()

    @field_validator("resolution_reason")
    @classmethod
    def require_reason(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("An explicit resolution reason is required")
        return value

    @model_validator(mode="after")
    def validate_shape(self) -> "SimulationTierTransitionRequest":
        if not self.character_ids:
            raise ValueError("A transition requires explicit character IDs")
        if len(self.character_ids) != len(set(self.character_ids)):
            raise ValueError("Transition character IDs must be unique")
        if self.operation == TierTransitionOperation.MATERIALIZE:
            if (
                self.population_id is None
                or self.expected_population_version is None
                or self.requested_count != len(self.materializations)
                or set(self.character_ids)
                != {item.character_id for item in self.materializations}
            ):
                raise ValueError("Materialization IDs, count, source, and version are required")
            if self.target_tier not in {SimulationTier.TIER_1, SimulationTier.TIER_2}:
                raise ValueError("Materialization requires individual Tier 1 or Tier 2")
        else:
            if self.materializations or self.population_id is not None:
                raise ValueError("Resolution-only transitions cannot materialize entities")
            if set(self.character_ids) != set(self.expected_tier_versions):
                raise ValueError("Every resolution transition requires an expected tier version")
        if any(version < 1 for version in self.expected_tier_versions.values()):
            raise ValueError("Expected tier versions must be positive")
        return self


class TierTransitionResultStatus(str, Enum):
    APPLIED = "applied"
    REPLAYED = "replayed"


class SimulationTierTransitionResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    result_id: UUID
    request: SimulationTierTransitionRequest
    status: TierTransitionResultStatus
    tier_states_before: tuple[SimulationTierState, ...] = ()
    tier_states_after: tuple[SimulationTierState, ...]
    aggregate_source_links: tuple[AggregatePopulationSourceLink, ...] = ()
    materialized_individual_links: tuple[MaterializedIndividualLink, ...] = ()
    applied_at: datetime
