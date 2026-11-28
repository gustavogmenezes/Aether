from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from uuid import uuid4

import pytest
from sqlalchemy import func, select

from aether.application import GeographyService, MobilityService, TemporalAdvanceService
from aether.contracts import (
    ActorReference,
    ActorType,
    AdvanceUntilEventCommand,
    ClaimSemantics,
    ControlStatus,
    JourneyStatus,
    Location,
    LocationType,
    RecordProvenance,
    ResourceBalance,
    ResourceCharge,
    ResourceKind,
    ResourceOwnerKind,
    StartJourneyCommand,
    TerritoryClaim,
    TransportMode,
    TransportRoute,
    TransportRouteSegment,
    TravelParticipant,
    TravelParticipantType,
)
from aether.domain import ResourceInvariantError, WorldClockState
from aether.engines import RouteSelection
from aether.infrastructure import Database, SqlAlchemySimulationUnitOfWork
from aether.infrastructure.models import (
    EventLedgerModel,
    PlayerKnowledgeModel,
)


def provenance(now: datetime) -> RecordProvenance:
    return RecordProvenance(
        source_type="test",
        source_id="geography-mobility",
        created_at=now,
        updated_at=now,
        version=1,
    )


def seed_world(tmp_path: Path):
    database = Database.from_path(tmp_path / "mobility.db")
    database.create_schema()
    now = datetime(2026, 4, 1, 8, tzinfo=UTC)
    world_id = uuid4()
    timeline_id = uuid4()
    actor = ActorReference(actor_type=ActorType.ORGANIZATION, actor_id=uuid4())
    parent = Location(
        location_id=uuid4(),
        world_id=world_id,
        name="North Reach",
        location_type=LocationType.REGION,
        terrain=("mountain",),
        climate=("cold",),
        hydrology=("river",),
        population_density="sparse",
        strategic_tags=("pass",),
        risk_tags=("rockfall",),
        provenance=provenance(now),
    )
    start = Location(
        location_id=uuid4(),
        world_id=world_id,
        name="Ash Gate",
        location_type=LocationType.POINT_OF_INTEREST,
        parent_location_id=parent.location_id,
        provenance=provenance(now),
    )
    middle = Location(
        location_id=uuid4(),
        world_id=world_id,
        name="Ferry Landing",
        location_type=LocationType.POINT_OF_INTEREST,
        parent_location_id=parent.location_id,
        provenance=provenance(now),
    )
    end = Location(
        location_id=uuid4(),
        world_id=world_id,
        name="Riverwatch",
        location_type=LocationType.CITY,
        parent_location_id=parent.location_id,
        provenance=provenance(now),
    )
    route = TransportRoute(
        route_id=uuid4(),
        world_id=world_id,
        name="Ash-River road",
        start_location_id=start.location_id,
        end_location_id=end.location_id,
        modes=(TransportMode.TERRESTRIAL,),
        availability="open in fair weather",
        provenance=provenance(now),
    )
    first = TransportRouteSegment(
        segment_id=uuid4(),
        route_id=route.route_id,
        sequence=0,
        start_location_id=start.location_id,
        end_location_id=middle.location_id,
        physical_distance=Decimal("40"),
        distance_unit="km",
        base_duration=timedelta(hours=3),
        mode=TransportMode.TERRESTRIAL,
        costs=(ResourceCharge(resource_code="coin", quantity=Decimal("2")),),
        capacity="two wagons",
        availability="open",
        resource_consumption=(
            ResourceCharge(resource_code="fodder", quantity=Decimal("3")),
        ),
        risk_tags=("bandits",),
        provenance=provenance(now),
    )
    second = first.model_copy(
        update={
            "segment_id": uuid4(),
            "sequence": 1,
            "start_location_id": middle.location_id,
            "end_location_id": end.location_id,
            "physical_distance": Decimal("10"),
            "base_duration": timedelta(hours=5),
            "costs": (
                ResourceCharge(resource_code="coin", quantity=Decimal("1")),
            ),
            "resource_consumption": (
                ResourceCharge(resource_code="fodder", quantity=Decimal("1")),
            ),
        }
    )
    with SqlAlchemySimulationUnitOfWork(database.session_factory) as uow:
        uow.repository.create_clock(
            WorldClockState(world_id, timeline_id, now, version=0)
        )
        for location in (parent, start, middle, end):
            uow.repository.create_location(location)
        uow.repository.create_transport_route(route)
        uow.repository.create_transport_route_segment(first)
        uow.repository.create_transport_route_segment(second)
        for code, quantity in (("coin", "20"), ("fodder", "10")):
            uow.repository.create_resource_balance(
                ResourceBalance(
                    balance_id=uuid4(),
                    owner_kind=ResourceOwnerKind.ORGANIZATION,
                    owner_id=actor.actor_id,
                    resource_code=code,
                    resource_kind=ResourceKind.MATERIAL,
                    quantity=Decimal(quantity),
                    reserved=Decimal("0"),
                    version=0,
                )
            )
    command = StartJourneyCommand(
        journey_id=uuid4(),
        world_id=world_id,
        timeline_id=timeline_id,
        participants=(
            TravelParticipant(
                actor=actor,
                participant_type=TravelParticipantType.FLEET,
            ),
        ),
        route_id=route.route_id,
        segment_ids=(first.segment_id, second.segment_id),
        resource_owner=actor,
        provenance=provenance(now),
    )
    return (
        database,
        now,
        world_id,
        timeline_id,
        actor,
        parent,
        start,
        middle,
        end,
        route,
        first,
        second,
        command,
    )


def test_hierarchy_and_formal_effective_control_remain_separate(tmp_path: Path) -> None:
    database, now, world_id, _, _, parent, _, _, _, _, _, _, _ = seed_world(
        tmp_path
    )
    geography = GeographyService(
        lambda: SqlAlchemySimulationUnitOfWork(database.session_factory)
    )
    city = Location(
        location_id=uuid4(),
        world_id=world_id,
        name="East Ward",
        location_type=LocationType.NEIGHBORHOOD,
        parent_location_id=parent.location_id,
        provenance=provenance(now),
    )
    geography.create_location(city)
    owner = ActorReference(actor_type=ActorType.CHARACTER, actor_id=uuid4())
    controller = ActorReference(actor_type=ActorType.ORGANIZATION, actor_id=uuid4())
    with SqlAlchemySimulationUnitOfWork(database.session_factory) as uow:
        uow.repository.create_territory_claim(
            TerritoryClaim(
                claim_id=uuid4(),
                location_id=city.location_id,
                semantics=ClaimSemantics.FORMAL,
                owner=owner,
                controller=owner,
                status=ControlStatus.CONTROLLED,
                basis="charter",
                provenance=provenance(now),
            )
        )
        uow.repository.create_territory_claim(
            TerritoryClaim(
                claim_id=uuid4(),
                location_id=city.location_id,
                semantics=ClaimSemantics.EFFECTIVE,
                controller=controller,
                status=ControlStatus.OCCUPIED,
                basis="current garrison",
                provenance=provenance(now),
            )
        )
    with SqlAlchemySimulationUnitOfWork(database.session_factory) as uow:
        stored_city = uow.repository.get_location(city.location_id)
        assert stored_city is not None
        assert stored_city.parent_location_id == parent.location_id
        claims = uow.repository.list_territory_claims(city.location_id)
        assert {(item.semantics, item.status) for item in claims} == {
            (ClaimSemantics.FORMAL, ControlStatus.CONTROLLED),
            (ClaimSemantics.EFFECTIVE, ControlStatus.OCCUPIED),
        }
        assert claims[0].owner != claims[1].controller
    database.dispose()


def test_route_sums_explicit_distance_and_duration_and_rejects_gaps(
    tmp_path: Path,
) -> None:
    data = seed_world(tmp_path)
    database, _, _, _, _, _, _, _, _, route, first, second, _ = data
    selection = RouteSelection.select(route, (first, second), (first.segment_id, second.segment_id))
    assert selection.total_distance == Decimal("50")
    assert selection.total_duration == timedelta(hours=8)

    disconnected = second.model_copy(
        update={"start_location_id": uuid4()}
    )
    with pytest.raises(ValueError, match="disconnected"):
        RouteSelection.select(
            route, (first, disconnected), (first.segment_id, disconnected.segment_id)
        )
    database.dispose()


def test_journey_reserves_resources_arrives_only_when_time_is_authorized(
    tmp_path: Path,
) -> None:
    (
        database,
        now,
        world_id,
        timeline_id,
        actor,
        _,
        _,
        _,
        end,
        _,
        _,
        _,
        command,
    ) = seed_world(tmp_path)
    mobility = MobilityService(
        lambda: SqlAlchemySimulationUnitOfWork(database.session_factory)
    )
    result = mobility.start_journey(command)
    replay = mobility.start_journey(command)

    assert result.total_distance == Decimal("50")
    assert result.total_duration == timedelta(hours=8)
    assert replay.idempotent_replay
    with SqlAlchemySimulationUnitOfWork(database.session_factory) as uow:
        stored_clock = uow.repository.get_clock(world_id, timeline_id)
        stored_journey = uow.repository.get_journey(command.journey_id)
        stored_position = uow.repository.get_actor_position(actor)
        assert stored_clock is not None and stored_clock.current_time == now
        assert stored_journey is not None
        assert stored_position is not None
        assert stored_journey.status == JourneyStatus.IN_TRANSIT
        assert stored_position.location_id == result.journey.start_location_id
        coin = uow.repository.get_resource_balance(
            ResourceOwnerKind.ORGANIZATION, actor.actor_id, "coin"
        )
        fodder = uow.repository.get_resource_balance(
            ResourceOwnerKind.ORGANIZATION, actor.actor_id, "fodder"
        )
        assert coin is not None and fodder is not None
        assert coin.quantity == Decimal("20") and coin.reserved == Decimal("3")
        assert fodder.quantity == Decimal("10") and fodder.reserved == Decimal("4")
        assert uow.session.scalar(select(func.count(EventLedgerModel.event_id))) == 0

    temporal = TemporalAdvanceService(
        lambda: SqlAlchemySimulationUnitOfWork(database.session_factory)
    )
    advance_command = AdvanceUntilEventCommand(
        simulation_run_id=uuid4(),
        world_id=world_id,
        timeline_id=timeline_id,
        scheduled_event_id=result.journey.scheduled_event_id,
    )
    first_advance = temporal.advance_until_event(advance_command)
    replay_advance = temporal.advance_until_event(
        advance_command
    )
    assert replay_advance.idempotent_replay
    assert replay_advance.processed_event_ids == first_advance.processed_event_ids

    with SqlAlchemySimulationUnitOfWork(database.session_factory) as uow:
        arrived_position = uow.repository.get_actor_position(actor)
        arrived_journey = uow.repository.get_journey(command.journey_id)
        coin = uow.repository.get_resource_balance(
            ResourceOwnerKind.ORGANIZATION, actor.actor_id, "coin"
        )
        fodder = uow.repository.get_resource_balance(
            ResourceOwnerKind.ORGANIZATION, actor.actor_id, "fodder"
        )
        assert arrived_position is not None and arrived_journey is not None
        assert coin is not None and fodder is not None
        assert arrived_position.location_id == end.location_id
        assert arrived_position.journey_id is None
        assert arrived_journey.status == JourneyStatus.ARRIVED
        assert coin.quantity == Decimal("17")
        assert fodder.quantity == Decimal("6")
        assert uow.session.scalar(select(func.count(EventLedgerModel.event_id))) == 1
        assert (
            uow.session.scalar(select(func.count(PlayerKnowledgeModel.knowledge_id)))
            == 0
        )
    database.dispose()


def test_arrival_failure_rolls_back_positions_resources_and_journey(
    tmp_path: Path,
) -> None:
    database, now, world_id, timeline_id, actor, _, start, _, _, _, _, _, command = (
        seed_world(tmp_path)
    )
    result = MobilityService(
        lambda: SqlAlchemySimulationUnitOfWork(database.session_factory)
    ).start_journey(command)

    class FailingTravelResolver:
        def resolve(self, event, plan_step, journey=None):
            raise RuntimeError("travel resolution interrupted")

    temporal = TemporalAdvanceService(
        lambda: SqlAlchemySimulationUnitOfWork(database.session_factory),
        scheduled_resolver=FailingTravelResolver(),
    )
    with pytest.raises(RuntimeError, match="interrupted"):
        temporal.advance_until_event(
            AdvanceUntilEventCommand(
                simulation_run_id=uuid4(),
                world_id=world_id,
                timeline_id=timeline_id,
                scheduled_event_id=result.journey.scheduled_event_id,
            )
        )
    with SqlAlchemySimulationUnitOfWork(database.session_factory) as uow:
        stored_clock = uow.repository.get_clock(world_id, timeline_id)
        stored_position = uow.repository.get_actor_position(actor)
        stored_journey = uow.repository.get_journey(command.journey_id)
        assert stored_clock is not None and stored_clock.current_time == now
        assert stored_position is not None and stored_journey is not None
        assert stored_position.location_id == start.location_id
        assert stored_journey.status == JourneyStatus.IN_TRANSIT
        balance = uow.repository.get_resource_balance(
            ResourceOwnerKind.ORGANIZATION, actor.actor_id, "coin"
        )
        assert balance is not None
        assert balance.quantity == Decimal("20")
        assert balance.reserved == Decimal("3")
        assert not uow.repository.list_resource_transactions(
            result.journey.scheduled_event_id
        )
    database.dispose()


def test_journey_rejects_insufficient_reserved_resources(tmp_path: Path) -> None:
    data = seed_world(tmp_path)
    database, _, _, _, actor, _, _, _, _, _, _, _, command = data
    with SqlAlchemySimulationUnitOfWork(database.session_factory) as uow:
        balance = uow.repository.get_resource_balance(
            ResourceOwnerKind.ORGANIZATION, actor.actor_id, "coin"
        )
        assert balance is not None
    empty = command.model_copy(
        update={
            "journey_id": uuid4(),
            "resource_owner": ActorReference(
                actor_type=ActorType.CHARACTER, actor_id=uuid4()
            ),
        }
    )
    with pytest.raises((ValueError, ResourceInvariantError), match="Resource balance|Insufficient"):
        MobilityService(
            lambda: SqlAlchemySimulationUnitOfWork(database.session_factory)
        ).start_journey(empty)
    database.dispose()
