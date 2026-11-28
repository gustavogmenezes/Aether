from enum import Enum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from .character import RecordProvenance


class LocationType(str, Enum):
    WORLD = "world"
    PLANET = "planet"
    CONTINENT = "continent"
    REGION = "region"
    COUNTRY = "country"
    PROVINCE = "province"
    CITY = "city"
    NEIGHBORHOOD = "neighborhood"
    PROPERTY = "property"
    POINT_OF_INTEREST = "point-of-interest"
    OTHER = "other"


class ActorType(str, Enum):
    CHARACTER = "character"
    ORGANIZATION = "organization"


class ControlStatus(str, Enum):
    CONTROLLED = "controlled"
    CONTESTED = "contested"
    OCCUPIED = "occupied"
    SHARED = "shared"


class ClaimSemantics(str, Enum):
    FORMAL = "formal"
    EFFECTIVE = "effective"


class ActorReference(BaseModel):
    model_config = ConfigDict(frozen=True)

    actor_type: ActorType
    actor_id: UUID


class Location(BaseModel):
    model_config = ConfigDict(frozen=True)

    location_id: UUID
    world_id: UUID
    name: str
    location_type: LocationType
    parent_location_id: UUID | None = None
    terrain: tuple[str, ...] = ()
    climate: tuple[str, ...] = ()
    hydrology: tuple[str, ...] = ()
    flora_fauna: tuple[str, ...] = ()
    natural_resources: tuple[str, ...] = ()
    population_density: str | None = None
    strategic_tags: tuple[str, ...] = ()
    risk_tags: tuple[str, ...] = ()
    barrier_tags: tuple[str, ...] = ()
    provenance: RecordProvenance

    @field_validator("name")
    @classmethod
    def name_cannot_be_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Location name cannot be blank")
        return value

    @model_validator(mode="after")
    def root_cannot_parent_itself(self) -> "Location":
        if self.parent_location_id == self.location_id:
            raise ValueError("Location cannot be its own parent")
        return self


class Region(Location):
    @model_validator(mode="after")
    def region_has_regional_type(self) -> "Region":
        if self.location_type not in {
            LocationType.CONTINENT,
            LocationType.REGION,
            LocationType.COUNTRY,
            LocationType.PROVINCE,
            LocationType.CITY,
        }:
            raise ValueError("Region requires a regional location type")
        return self


class PointOfInterest(Location):
    @model_validator(mode="after")
    def poi_has_poi_type(self) -> "PointOfInterest":
        if self.location_type != LocationType.POINT_OF_INTEREST:
            raise ValueError("Point of interest requires point-of-interest type")
        return self


class TerritoryClaim(BaseModel):
    model_config = ConfigDict(frozen=True)

    claim_id: UUID
    location_id: UUID
    semantics: ClaimSemantics
    owner: ActorReference | None = None
    controller: ActorReference | None = None
    status: ControlStatus
    basis: str
    provenance: RecordProvenance

    @model_validator(mode="after")
    def claim_requires_an_actor_and_basis(self) -> "TerritoryClaim":
        if self.owner is None and self.controller is None:
            raise ValueError("Territory claim requires an owner or controller")
        if not self.basis.strip():
            raise ValueError("Territory claim basis cannot be blank")
        return self


class InfrastructureNode(BaseModel):
    model_config = ConfigDict(frozen=True)

    node_id: UUID
    world_id: UUID
    location_id: UUID
    name: str
    node_type: str
    availability: str
    capacity: str | None = None
    safety_tags: tuple[str, ...] = ()
    risk_tags: tuple[str, ...] = ()
    provenance: RecordProvenance


class InfrastructureFacility(BaseModel):
    model_config = ConfigDict(frozen=True)

    facility_id: UUID
    node_id: UUID
    location_id: UUID
    facility_type: str
    name: str
    availability: str
    capacity: str | None = None
    resource_consumption: tuple[str, ...] = ()
    safety_tags: tuple[str, ...] = ()
    risk_tags: tuple[str, ...] = ()
    provenance: RecordProvenance


class ActorPosition(BaseModel):
    model_config = ConfigDict(frozen=True)

    actor: ActorReference
    location_id: UUID
    journey_id: UUID | None = None
    version: int = Field(ge=0)
