from collections import defaultdict
from collections.abc import Callable
from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID, uuid5

from aether.contracts import (
    ActorPosition,
    Journey,
    JourneyScheduleResult,
    JourneyStatus,
    ResourceOwnerKind,
    ResourceReservation,
    ScheduledEvent,
    StartJourneyCommand,
)
from aether.domain import (
    InvalidTemporalAdvanceError,
)
from aether.domain.ports import SimulationUnitOfWorkFactory
from aether.engines import GeographyHierarchyEngine, RouteSelection


class GeographyService:
    def __init__(self, unit_of_work_factory: SimulationUnitOfWorkFactory) -> None:
        self._unit_of_work_factory = unit_of_work_factory

    def create_location(self, location) -> None:
        with self._unit_of_work_factory() as unit_of_work:
            GeographyHierarchyEngine.validate_new_location(
                location, unit_of_work.repository.list_locations(location.world_id)
            )
            unit_of_work.repository.create_location(location)
            unit_of_work.commit()


class MobilityService:
    def __init__(
        self,
        unit_of_work_factory: SimulationUnitOfWorkFactory,
        *,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self._unit_of_work_factory = unit_of_work_factory
        self._clock = clock or (lambda: datetime.now(UTC))

    def start_journey(
        self, command: StartJourneyCommand
    ) -> JourneyScheduleResult:
        with self._unit_of_work_factory() as unit_of_work:
            repository = unit_of_work.repository
            existing = repository.get_journey(command.journey_id)
            if existing is not None:
                return self._existing_result(repository, command, existing)

            clock = repository.get_clock(command.world_id, command.timeline_id)
            route = repository.get_transport_route(command.route_id)
            if clock is None:
                raise InvalidTemporalAdvanceError("World clock was not found")
            if route is None:
                raise ValueError("Transport route was not found")
            if route.world_id != command.world_id:
                raise ValueError("Transport route belongs to another world")
            segments = repository.list_transport_route_segments(route.route_id)
            selection = RouteSelection.select(route, segments, command.segment_ids)
            for participant in command.participants:
                position = repository.get_actor_position(participant.actor)
                if (
                    position is not None
                    and position.location_id != route.start_location_id
                ):
                    raise ValueError("Journey participant is not at the route start")
                if position is not None and position.journey_id is not None:
                    raise ValueError("Journey participant is already in transit")

            scheduled_event_id = uuid5(
                UUID("7d4f2f87-7e8f-5d96-9845-6f8db4a8c65b"),
                str(command.journey_id),
            )
            if repository.get_scheduled_event(scheduled_event_id) is not None:
                raise ValueError("Travel arrival event ID is already in use")
            arrival = clock.current_time + selection.total_duration
            journey = Journey(
                journey_id=command.journey_id,
                world_id=command.world_id,
                timeline_id=command.timeline_id,
                participants=command.participants,
                start_location_id=route.start_location_id,
                end_location_id=route.end_location_id,
                route_id=route.route_id,
                segment_ids=command.segment_ids,
                resource_owner=command.resource_owner,
                costs=selection.charges,
                resource_consumption=selection.consumption,
                started_at=clock.current_time,
                expected_arrival_at=arrival,
                status=JourneyStatus.IN_TRANSIT,
                scheduled_event_id=scheduled_event_id,
                provenance=command.provenance,
            )
            event = ScheduledEvent(
                event_id=scheduled_event_id,
                world_id=command.world_id,
                timeline_id=command.timeline_id,
                scheduled_at=arrival,
                event_type="travel-arrival",
                source_type="journey",
                source_id=str(command.journey_id),
                payload_version="1",
                payload={"journey_id": str(command.journey_id)},
            )
            self._reserve_charges(repository, journey)
            repository.create_journey(journey)
            repository.schedule_event(event)
            for participant in command.participants:
                current = repository.get_actor_position(participant.actor)
                repository.save_actor_position(
                    ActorPosition(
                        actor=participant.actor,
                        location_id=route.start_location_id,
                        journey_id=journey.journey_id,
                        version=(current.version + 1) if current else 0,
                    )
                )
            unit_of_work.commit()
            return JourneyScheduleResult(
                journey=journey,
                total_distance=selection.total_distance,
                distance_unit=selection.distance_unit,
                total_duration=selection.total_duration,
            )

    @staticmethod
    def _reserve_charges(repository, journey: Journey) -> None:
        owner = journey.resource_owner
        if not owner:
            return
        totals: dict[str, Decimal] = defaultdict(Decimal)
        for charge in (*journey.costs, *journey.resource_consumption):
            totals[charge.resource_code] += charge.quantity
        owner_kind = ResourceOwnerKind(owner.actor_type.value)
        for code, quantity in sorted(totals.items()):
            repository.reserve_resource(
                ResourceReservation(
                    reservation_id=uuid5(
                        UUID("c8458a33-8e40-5070-91fb-55f0f95dcf4f"),
                        f"{journey.scheduled_event_id}:{owner_kind.value}:{owner.actor_id}:{code}",
                    ),
                    scheduled_event_id=journey.scheduled_event_id,
                    owner_kind=owner_kind,
                    owner_id=owner.actor_id,
                    resource_code=code,
                    quantity=quantity,
                )
            )

    @staticmethod
    def _existing_result(repository, command, journey) -> JourneyScheduleResult:
        route = repository.get_transport_route(command.route_id)
        if (
            journey.world_id != command.world_id
            or journey.timeline_id != command.timeline_id
            or journey.route_id != command.route_id
            or journey.segment_ids != command.segment_ids
            or journey.participants != command.participants
            or journey.resource_owner != command.resource_owner
            or journey.provenance != command.provenance
            or route is None
        ):
            raise ValueError("Journey ID is already associated with another command")
        selection = RouteSelection.select(
            route,
            repository.list_transport_route_segments(route.route_id),
            command.segment_ids,
        )
        return JourneyScheduleResult(
            journey=journey,
            total_distance=selection.total_distance,
            distance_unit=selection.distance_unit,
            total_duration=selection.total_duration,
            idempotent_replay=True,
        )
