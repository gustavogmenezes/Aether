from datetime import datetime, timedelta
from decimal import Decimal
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from .character import RecordProvenance
from .geography import ActorReference


class TransportMode(str, Enum):
    TERRESTRIAL = "terrestrial"
    AQUATIC = "aquatic"
    AERIAL = "aerial"
    RAIL = "rail"
    SPACE = "space"
    MAGICAL = "magical"
    SUPERNATURAL = "supernatural"
    BIOLOGICAL = "biological"
    OTHER = "other"


class TravelParticipantType(str, Enum):
    INDIVIDUAL = "individual"
    GROUP = "group"
    CARAVAN = "caravan"
    FLEET = "fleet"
    ARMY = "army"
    MIGRATION = "migration"
    EVACUATION = "evacuation"


class JourneyStatus(str, Enum):
    SCHEDULED = "scheduled"
    IN_TRANSIT = "in-transit"
    ARRIVED = "arrived"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ResourceCharge(BaseModel):
    model_config = ConfigDict(frozen=True)

    resource_code: str
    quantity: Decimal = Field(gt=0)

    @field_validator("resource_code")
    @classmethod
    def resource_code_cannot_be_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Resource charge code cannot be blank")
        return value


class TransportRouteSegment(BaseModel):
    model_config = ConfigDict(frozen=True)

    segment_id: UUID
    route_id: UUID
    sequence: int = Field(ge=0)
    start_location_id: UUID
    end_location_id: UUID
    physical_distance: Decimal = Field(gt=0)
    distance_unit: str
    base_duration: timedelta
    mode: TransportMode
    costs: tuple[ResourceCharge, ...] = ()
    capacity: str | None = None
    availability: str
    resource_consumption: tuple[ResourceCharge, ...] = ()
    safety_tags: tuple[str, ...] = ()
    risk_tags: tuple[str, ...] = ()
    provenance: RecordProvenance

    @model_validator(mode="after")
    def segment_has_valid_endpoints_and_duration(self) -> "TransportRouteSegment":
        if self.start_location_id == self.end_location_id:
            raise ValueError("Transport segment endpoints must differ")
        if self.base_duration <= timedelta(0):
            raise ValueError("Transport segment base duration must be positive")
        if not self.distance_unit.strip():
            raise ValueError("Transport segment distance unit cannot be blank")
        return self


class TransportRoute(BaseModel):
    model_config = ConfigDict(frozen=True)

    route_id: UUID
    world_id: UUID
    name: str
    start_location_id: UUID
    end_location_id: UUID
    modes: tuple[TransportMode, ...]
    availability: str
    provenance: RecordProvenance


class TravelParticipant(BaseModel):
    model_config = ConfigDict(frozen=True)

    actor: ActorReference
    participant_type: TravelParticipantType


class Journey(BaseModel):
    model_config = ConfigDict(frozen=True)

    journey_id: UUID
    world_id: UUID
    timeline_id: UUID
    participants: tuple[TravelParticipant, ...]
    start_location_id: UUID
    end_location_id: UUID
    route_id: UUID
    segment_ids: tuple[UUID, ...]
    resource_owner: ActorReference | None = None
    costs: tuple[ResourceCharge, ...] = ()
    resource_consumption: tuple[ResourceCharge, ...] = ()
    started_at: datetime
    expected_arrival_at: datetime
    arrived_at: datetime | None = None
    status: JourneyStatus
    scheduled_event_id: UUID
    provenance: RecordProvenance

    @model_validator(mode="after")
    def journey_has_valid_inputs(self) -> "Journey":
        if not self.participants:
            raise ValueError("Journey requires at least one participant")
        if not self.segment_ids:
            raise ValueError("Journey requires selected route segments")
        for value in (self.started_at, self.expected_arrival_at):
            if value.tzinfo is None or value.utcoffset() is None:
                raise ValueError("Journey timestamps must include a UTC offset")
        if self.expected_arrival_at <= self.started_at:
            raise ValueError("Journey arrival must be later than departure")
        if self.arrived_at is not None and (
            self.arrived_at.tzinfo is None or self.arrived_at.utcoffset() is None
        ):
            raise ValueError("Journey arrival timestamp must include a UTC offset")
        if (self.costs or self.resource_consumption) and self.resource_owner is None:
            raise ValueError("Charged journeys require an explicit resource owner")
        return self


class JourneyScheduleResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    journey: Journey
    total_distance: Decimal
    distance_unit: str
    total_duration: timedelta
    idempotent_replay: bool = False


class StartJourneyCommand(BaseModel):
    model_config = ConfigDict(frozen=True)

    journey_id: UUID
    world_id: UUID
    timeline_id: UUID
    participants: tuple[TravelParticipant, ...]
    route_id: UUID
    segment_ids: tuple[UUID, ...]
    resource_owner: ActorReference | None = None
    provenance: RecordProvenance

    @model_validator(mode="after")
    def journey_command_has_participants_and_segments(self) -> "StartJourneyCommand":
        if not self.participants or not self.segment_ids:
            raise ValueError("Start journey requires participants and segments")
        return self
