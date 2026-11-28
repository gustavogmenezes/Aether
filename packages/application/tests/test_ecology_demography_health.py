from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from uuid import uuid4

import pytest
from sqlalchemy import select

from aether.application import TemporalAdvanceService
from aether.contracts import (
    AdvanceTimeCommand,
    AdvanceUntilEventCommand,
    EcologicalProcess,
    HealthCondition,
    HealthConditionCategory,
    HealthState,
    LifecycleStage,
    Location,
    LocationType,
    Population,
    PopulationCohort,
    RecordProvenance,
    ScheduledEvent,
    Species,
)
from aether.domain import WorldClockState
from aether.infrastructure import Database, SqlAlchemySimulationUnitOfWork
from aether.infrastructure.models import (
    CharacterKnowledgeModel,
    EventLedgerModel,
    PlayerKnowledgeModel,
)


def provenance(now: datetime) -> RecordProvenance:
    return RecordProvenance(
        source_type="test",
        source_id="natural-systems",
        created_at=now,
        updated_at=now,
        version=1,
    )


def seed_natural_world(tmp_path: Path):
    now = datetime(2026, 4, 1, tzinfo=UTC)
    database = Database.from_path(tmp_path / "natural.db")
    database.create_schema()
    world_id, timeline_id = uuid4(), uuid4()
    location = Location(
        location_id=uuid4(),
        world_id=world_id,
        name="Fen",
        location_type=LocationType.REGION,
        provenance=provenance(now),
    )
    species = Species(
        species_id=uuid4(),
        world_id=world_id,
        name="Reedfolk",
        anatomy={"respiration": "branchial"},
        physiology={"temperature": "configured"},
        reproduction_model={"kind": "spore"},
        nutrition={"sources": ("mineral",)},
        habitat=("wetland",),
        senses=("vibration",),
        adaptations=("amphibious",),
        lifecycle_stages=(
            LifecycleStage(code="sprout", name="Sprout", sequence=0),
            LifecycleStage(code="mature", name="Mature", sequence=1),
        ),
        provenance=provenance(now),
    )
    population = Population(
        population_id=uuid4(),
        world_id=world_id,
        species_id=species.species_id,
        location_id=location.location_id,
        name="Eastern Reedfolk",
        cohorts=(
            PopulationCohort(
                cohort_id=uuid4(),
                lifecycle_stage="sprout",
                count=Decimal("8.5"),
                births=Decimal("1"),
            ),
            PopulationCohort(
                cohort_id=uuid4(),
                lifecycle_stage="mature",
                count=Decimal("20"),
            ),
        ),
        provenance=provenance(now),
    )
    process = EcologicalProcess(
        process_id=uuid4(),
        world_id=world_id,
        location_id=location.location_id,
        process_type="wetland-recovery",
        measures={"water-quality": Decimal("3")},
        population_links=(population.population_id,),
        resource_links=("water",),
        provenance=provenance(now),
    )
    character_id = uuid4()
    health = HealthState(
        state_id=uuid4(),
        character_id=character_id,
        species_id=species.species_id,
        physical_integrity="injured",
        consciousness="alert",
        ability_to_act="limited",
        ability_to_fight="capable",
        provenance=provenance(now),
    )
    with SqlAlchemySimulationUnitOfWork(database.session_factory) as uow:
        uow.repository.create_clock(
            WorldClockState(world_id, timeline_id, now, version=0)
        )
        uow.repository.create_location(location)
        uow.repository.create_species(species)
        uow.repository.create_population(population)
        uow.repository.create_ecological_process(process)
        uow.repository.create_health_state(health)
    return database, now, world_id, timeline_id, species, population, process, health


def test_health_keeps_biological_consciousness_and_combat_capability_separate() -> None:
    state = HealthState(
        state_id=uuid4(),
        character_id=uuid4(),
        physical_integrity="severely injured",
        consciousness="unconscious",
        ability_to_act="incapacitated",
        ability_to_fight="unavailable",
        provenance=provenance(datetime(2026, 1, 1, tzinfo=UTC)),
    )

    assert state.physical_integrity == "severely injured"
    assert state.consciousness == "unconscious"
    assert state.ability_to_act == "incapacitated"
    assert state.ability_to_fight == "unavailable"


def test_authorized_natural_events_update_state_ledger_and_not_player_knowledge(
    tmp_path: Path,
) -> None:
    database, now, world_id, timeline_id, _, population, process, health = (
        seed_natural_world(tmp_path)
    )
    event_at = now + timedelta(days=1)
    condition_id = uuid4()
    events = (
        ScheduledEvent(
            event_id=uuid4(),
            world_id=world_id,
            timeline_id=timeline_id,
            scheduled_at=event_at,
            event_type="population-change",
            source_type="natural-process",
            source_id="seasonal-births",
            payload_version="1",
            payload={
                "population_id": str(population.population_id),
                "cause": "configured seasonal hatching",
                "changes": [
                    {
                        "cohort_id": str(population.cohorts[0].cohort_id),
                        "delta": "2.5",
                        "birth_delta": "2.5",
                    }
                ],
            },
        ),
        ScheduledEvent(
            event_id=uuid4(),
            world_id=world_id,
            timeline_id=timeline_id,
            scheduled_at=event_at,
            event_type="ecological-process",
            source_type="natural-process",
            source_id="wetland-dynamics",
            payload_version="1",
            payload={
                "process_id": str(process.process_id),
                "target_location_id": str(process.location_id),
                "population_id": str(population.population_id),
                "cause": "configured restoration work",
                "deltas": {"water-quality": "1.25"},
            },
        ),
        ScheduledEvent(
            event_id=uuid4(),
            world_id=world_id,
            timeline_id=timeline_id,
            scheduled_at=event_at,
            event_type="health-condition-change",
            source_type="natural-process",
            source_id="infection-exposure",
            payload_version="1",
            payload={
                "character_id": str(health.character_id),
                "cause": "configured infection exposure",
                "add_conditions": [
                    HealthCondition(
                        condition_id=condition_id,
                        code="marsh-fever",
                        category=HealthConditionCategory.INFECTION,
                        cause="contaminated water",
                    ).model_dump(mode="json")
                ],
                "dimension_changes": {"consciousness": "feverish"},
            },
        ),
    )
    with SqlAlchemySimulationUnitOfWork(database.session_factory) as uow:
        for event in events:
            uow.repository.schedule_event(event)

    service = TemporalAdvanceService(
        lambda: SqlAlchemySimulationUnitOfWork(database.session_factory)
    )
    command = AdvanceUntilEventCommand(
        simulation_run_id=uuid4(),
        world_id=world_id,
        timeline_id=timeline_id,
        scheduled_event_id=events[-1].event_id,
    )
    result = service.advance_until_event(command)
    replay = service.advance_until_event(command)

    assert replay.idempotent_replay
    assert replay.processed_event_ids == result.processed_event_ids
    with SqlAlchemySimulationUnitOfWork(database.session_factory) as uow:
        stored_population = uow.repository.get_population(population.population_id)
        stored_process = uow.repository.get_ecological_process(process.process_id)
        stored_health = uow.repository.get_health_state(health.character_id)
        assert stored_population is not None and stored_population.total_count == Decimal(
            "31"
        )
        assert stored_process is not None
        assert stored_process.measures["water-quality"] == Decimal("4.25")
        assert stored_health is not None
        assert stored_health.physical_integrity == "injured"
        assert stored_health.consciousness == "feverish"
        assert stored_health.ability_to_fight == "capable"
        assert {item.condition_id for item in stored_health.conditions} == {condition_id}
        ledger = uow.session.scalars(select(EventLedgerModel)).all()
        assert len(ledger) == 3
        assert all(item.payload["cause"] for item in ledger)
        assert (
            uow.session.scalars(select(PlayerKnowledgeModel)).all()
            == []
        )
        assert uow.session.scalars(select(CharacterKnowledgeModel)).all() == []


def test_population_only_background_event_does_not_create_player_knowledge(
    tmp_path: Path,
) -> None:
    database, now, world_id, timeline_id, _, population, _, _ = seed_natural_world(
        tmp_path
    )
    event = ScheduledEvent(
        event_id=uuid4(),
        world_id=world_id,
        timeline_id=timeline_id,
        scheduled_at=now + timedelta(hours=1),
        event_type="population-change",
        source_type="observer",
        source_id="population-only",
        payload_version="1",
        payload={
            "population_id": str(population.population_id),
            "cause": "configured migration",
            "changes": [
                {
                    "lifecycle_stage": "mature",
                    "delta": "-2",
                    "migration_out_delta": "2",
                }
            ],
        },
    )
    with SqlAlchemySimulationUnitOfWork(database.session_factory) as uow:
        uow.repository.schedule_event(event)

    TemporalAdvanceService(
        lambda: SqlAlchemySimulationUnitOfWork(database.session_factory)
    ).advance_time(
        AdvanceTimeCommand(
            simulation_run_id=uuid4(),
            world_id=world_id,
            timeline_id=timeline_id,
            duration=timedelta(hours=1),
        )
    )

    with SqlAlchemySimulationUnitOfWork(database.session_factory) as uow:
        stored = uow.repository.get_population(population.population_id)
        assert stored is not None
        assert stored.aggregate_by_default
        assert stored.total_count == Decimal("26.5")
        assert stored.cohorts[1].migration_out == Decimal("2")
        assert uow.session.scalars(select(PlayerKnowledgeModel)).all() == []
        assert uow.session.scalars(select(CharacterKnowledgeModel)).all() == []


def test_negative_population_rolls_back_entire_authorized_interval(
    tmp_path: Path,
) -> None:
    database, now, world_id, timeline_id, _, population, process, _ = (
        seed_natural_world(tmp_path)
    )
    events = (
        ScheduledEvent(
            event_id=uuid4(),
            world_id=world_id,
            timeline_id=timeline_id,
            scheduled_at=now + timedelta(minutes=5),
            event_type="ecological-process",
            source_type="test",
            source_id="first",
            payload_version="1",
            payload={
                "process_id": str(process.process_id),
                "target_location_id": str(process.location_id),
                "cause": "configured process",
                "deltas": {"water-quality": "2"},
            },
        ),
        ScheduledEvent(
            event_id=uuid4(),
            world_id=world_id,
            timeline_id=timeline_id,
            scheduled_at=now + timedelta(minutes=10),
            event_type="population-change",
            source_type="test",
            source_id="invalid",
            payload_version="1",
            payload={
                "population_id": str(population.population_id),
                "cause": "configured mortality",
                "changes": [
                    {
                        "lifecycle_stage": "sprout",
                        "delta": "-9",
                        "mortality_delta": "9",
                    }
                ],
            },
        ),
    )
    with SqlAlchemySimulationUnitOfWork(database.session_factory) as uow:
        for event in events:
            uow.repository.schedule_event(event)

    with pytest.raises(ValueError, match="negative count"):
        TemporalAdvanceService(
            lambda: SqlAlchemySimulationUnitOfWork(database.session_factory)
        ).advance_time(
            AdvanceTimeCommand(
                simulation_run_id=uuid4(),
                world_id=world_id,
                timeline_id=timeline_id,
                duration=timedelta(minutes=10),
            )
        )

    with SqlAlchemySimulationUnitOfWork(database.session_factory) as uow:
        stored_process = uow.repository.get_ecological_process(process.process_id)
        stored_population = uow.repository.get_population(population.population_id)
        clock = uow.repository.get_clock(world_id, timeline_id)
        assert stored_process is not None and stored_process.measures[
            "water-quality"
        ] == Decimal("3")
        assert stored_population is not None
        assert stored_population.total_count == Decimal("28.5")
        assert clock is not None and clock.current_time == now
        assert uow.session.scalars(select(EventLedgerModel)).all() == []

