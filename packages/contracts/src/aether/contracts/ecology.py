from decimal import Decimal
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from .character import RecordProvenance


class OrganismKind(str, Enum):
    BIOLOGICAL = "biological"
    ARTIFICIAL = "artificial"
    EXTRATERRESTRIAL = "extraterrestrial"
    SUPERNATURAL = "supernatural"


class LifecycleStage(BaseModel):
    model_config = ConfigDict(frozen=True)

    code: str
    name: str
    sequence: int = Field(ge=0)
    description: str | None = None
    characteristics: dict[str, Any] = Field(default_factory=dict)

    @field_validator("code", "name")
    @classmethod
    def require_non_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Lifecycle stage fields cannot be blank")
        return value


class Species(BaseModel):
    model_config = ConfigDict(frozen=True)

    species_id: UUID
    world_id: UUID
    name: str
    organism_kind: OrganismKind = OrganismKind.BIOLOGICAL
    anatomy: Any = Field(default_factory=dict)
    physiology: Any = Field(default_factory=dict)
    reproduction_model: Any = Field(default_factory=dict)
    nutrition: Any = Field(default_factory=dict)
    habitat: tuple[str, ...] = ()
    senses: tuple[str, ...] = ()
    adaptations: tuple[str, ...] = ()
    lifecycle_stages: tuple[LifecycleStage, ...] = ()
    resource_links: tuple[str, ...] = ()
    provenance: RecordProvenance

    @field_validator("name")
    @classmethod
    def require_name(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Species name cannot be blank")
        return value

    @model_validator(mode="after")
    def lifecycle_codes_are_unique_and_ordered(self) -> "Species":
        codes = [stage.code for stage in self.lifecycle_stages]
        sequences = [stage.sequence for stage in self.lifecycle_stages]
        if len(codes) != len(set(codes)):
            raise ValueError("Species lifecycle stage codes must be unique")
        if sequences != sorted(sequences):
            raise ValueError("Species lifecycle stages must be ordered by sequence")
        return self


NatureDefinition = Species
Nature = Species


class PopulationCohort(BaseModel):
    model_config = ConfigDict(frozen=True)

    cohort_id: UUID
    lifecycle_stage: str
    count: Decimal = Field(ge=0)
    births: Decimal = Field(default=Decimal("0"), ge=0)
    mortality: Decimal = Field(default=Decimal("0"), ge=0)
    migration_in: Decimal = Field(default=Decimal("0"), ge=0)
    migration_out: Decimal = Field(default=Decimal("0"), ge=0)


class Population(BaseModel):
    model_config = ConfigDict(frozen=True)

    population_id: UUID
    world_id: UUID
    species_id: UUID
    location_id: UUID
    name: str
    cohorts: tuple[PopulationCohort, ...] = ()
    aggregate_by_default: bool = True
    resource_links: tuple[str, ...] = ()
    provenance: RecordProvenance

    @model_validator(mode="after")
    def cohort_ids_and_stages_are_unique(self) -> "Population":
        ids = [cohort.cohort_id for cohort in self.cohorts]
        stages = [cohort.lifecycle_stage for cohort in self.cohorts]
        if len(ids) != len(set(ids)):
            raise ValueError("Population cohort IDs must be unique")
        if len(stages) != len(set(stages)):
            raise ValueError("Population lifecycle stages must be unique")
        return self

    @property
    def total_count(self) -> Decimal:
        return sum((cohort.count for cohort in self.cohorts), start=Decimal("0"))


class Habitat(BaseModel):
    model_config = ConfigDict(frozen=True)

    habitat_id: UUID
    world_id: UUID
    location_id: UUID
    name: str
    habitat_type: str
    habitability: dict[str, Any] = Field(default_factory=dict)
    species_ids: tuple[UUID, ...] = ()
    resources: tuple[str, ...] = ()
    resource_links: tuple[str, ...] = ()
    characteristics: dict[str, Any] = Field(default_factory=dict)
    provenance: RecordProvenance


class EcologicalProcess(BaseModel):
    model_config = ConfigDict(frozen=True)

    process_id: UUID
    world_id: UUID
    location_id: UUID
    process_type: str
    measures: dict[str, Decimal] = Field(default_factory=dict)
    population_links: tuple[UUID, ...] = ()
    resource_links: tuple[str, ...] = ()
    status: str = "active"
    provenance: RecordProvenance


class PopulationChangeEntry(BaseModel):
    model_config = ConfigDict(frozen=True)

    cohort_id: UUID | None = None
    lifecycle_stage: str | None = None
    delta: Decimal
    birth_delta: Decimal = Decimal("0")
    mortality_delta: Decimal = Decimal("0")
    migration_in_delta: Decimal = Decimal("0")
    migration_out_delta: Decimal = Decimal("0")

    @model_validator(mode="after")
    def target_is_configured(self) -> "PopulationChangeEntry":
        if self.cohort_id is None and not self.lifecycle_stage:
            raise ValueError("Population change requires a cohort or lifecycle stage")
        return self


class PopulationChangePayload(BaseModel):
    model_config = ConfigDict(frozen=True)

    population_id: UUID
    cause: str
    changes: tuple[PopulationChangeEntry, ...]
    target_location_id: UUID | None = None

    @model_validator(mode="after")
    def validate_payload(self) -> "PopulationChangePayload":
        if not self.cause.strip():
            raise ValueError("Population change cause cannot be blank")
        if not self.changes:
            raise ValueError("Population change requires explicit changes")
        return self


class EcologicalProcessChangePayload(BaseModel):
    model_config = ConfigDict(frozen=True)

    process_id: UUID
    target_location_id: UUID
    cause: str
    deltas: dict[str, Decimal]
    population_id: UUID | None = None
    resource_links: tuple[str, ...] = ()

    @model_validator(mode="after")
    def validate_payload(self) -> "EcologicalProcessChangePayload":
        if not self.cause.strip():
            raise ValueError("Ecological process cause cannot be blank")
        if not self.deltas:
            raise ValueError("Ecological process requires explicit signed deltas")
        return self

