from collections.abc import Iterator
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from uuid import UUID, uuid4

import pytest

from aether.application import SimulationTierService
from aether.contracts import (
    CharacterIdentity,
    Goal,
    GoalStatus,
    MaterializationSpecification,
    Plan,
    PlanStatus,
    Population,
    PopulationCohort,
    RecordProvenance,
    Relationship,
    SimulationTier,
    SimulationTierTransitionRequest,
    TierTransitionOperation,
)
from aether.domain import SimulationTierTransitionError, StaleWorldStateError
from aether.infrastructure import Database, SqlAlchemySimulationUnitOfWork


@pytest.fixture
def database(tmp_path: Path) -> Iterator[Database]:
    database = Database.from_path(tmp_path / "tiers.db")
    database.create_schema()
    yield database
    database.dispose()


def provenance(now: datetime, version: int = 1) -> RecordProvenance:
    return RecordProvenance(
        source_type="explicit-caller",
        source_id="tier-test",
        created_at=now,
        updated_at=now,
        version=version,
    )


def setup_population(database: Database):
    now = datetime(2026, 7, 1, tzinfo=UTC)
    world_id = uuid4()
    population = Population(
        population_id=uuid4(),
        world_id=world_id,
        species_id=uuid4(),
        location_id=uuid4(),
        name="Garrison",
        cohorts=(
            PopulationCohort(
                cohort_id=uuid4(),
                lifecycle_stage="adult",
                count=Decimal("4"),
            ),
        ),
        provenance=provenance(now),
    )
    with SqlAlchemySimulationUnitOfWork(database.session_factory) as uow:
        # Population is aggregate authority; species/location FK enforcement is not
        # enabled by the in-memory SQLite test connection.
        uow.repository.create_population(population)
    return population, now


def materialization_request(
    population: Population,
    now: datetime,
    *,
    count: int = 2,
    request_id: UUID | None = None,
) -> SimulationTierTransitionRequest:
    character_ids = tuple(uuid4() for _ in range(count))
    specifications = tuple(
        MaterializationSpecification(
            character_id=character_id,
            identity=CharacterIdentity(
                identity_id=uuid4(),
                character_id=character_id,
                display_name=f"Caller supplied {index}",
                defining_attributes={"cohort": "soldier"},
                provenance=provenance(now),
            ),
            cohort_id=population.cohorts[0].cohort_id,
            compatible_traits={"cohort": "soldier"},
            supplied_species_id=population.species_id,
            supplied_location_id=population.location_id,
            supplied_lifecycle_stage="adult",
        )
        for index, character_id in enumerate(character_ids)
    )
    return SimulationTierTransitionRequest(
        request_id=request_id or uuid4(),
        world_id=population.world_id,
        operation=TierTransitionOperation.MATERIALIZE,
        target_tier=SimulationTier.TIER_2,
        character_ids=character_ids,
        resolution_reason="Explicit interaction with named members.",
        requested_at=now,
        provenance=provenance(now),
        population_id=population.population_id,
        expected_population_version=population.provenance.version,
        requested_count=count,
        materializations=specifications,
    )


def test_materialization_preserves_count_is_idempotent_and_prevents_duplicates(
    database: Database,
) -> None:
    population, now = setup_population(database)
    service = SimulationTierService(
        lambda: SqlAlchemySimulationUnitOfWork(database.session_factory)
    )
    request = materialization_request(population, now)

    first = service.transition(request)
    replay = service.transition(request)

    assert first.materialized_individual_links == replay.materialized_individual_links
    with SqlAlchemySimulationUnitOfWork(database.session_factory) as uow:
        stored_population = uow.repository.get_population(population.population_id)
        links = uow.repository.list_aggregate_population_source_links(
            population.population_id
        )
        assert stored_population is not None
        assert stored_population.total_count == Decimal("4")
        assert links[0].materialized_count == 2
        assert links[0].remaining_aggregate_count == Decimal("2")

    duplicate = materialization_request(
        population, now, count=2, request_id=uuid4()
    )
    duplicate = duplicate.model_copy(
        update={
            "character_ids": request.character_ids[:1],
            "requested_count": 1,
            "materializations": request.materializations[:1],
        }
    )
    with pytest.raises(SimulationTierTransitionError, match="already exists"):
        service.transition(duplicate)


def test_materialization_only_occurs_through_explicit_request(database: Database) -> None:
    population, now = setup_population(database)
    service = SimulationTierService(
        lambda: SqlAlchemySimulationUnitOfWork(database.session_factory)
    )
    with SqlAlchemySimulationUnitOfWork(database.session_factory) as uow:
        assert not uow.repository.list_aggregate_population_source_links(
            population.population_id
        )
        assert uow.repository.get_character_identity(uuid4()) is None

    service.transition(materialization_request(population, now, count=1))
    with SqlAlchemySimulationUnitOfWork(database.session_factory) as uow:
        assert uow.repository.list_aggregate_population_source_links(
            population.population_id
        )[0].materialized_count == 1


def test_materialization_rejects_incompatible_constraints(database: Database) -> None:
    population, now = setup_population(database)
    request = materialization_request(population, now, count=1)
    incompatible = request.materializations[0].model_copy(
        update={"supplied_species_id": uuid4()}
    )
    request = request.model_copy(update={"materializations": (incompatible,)})
    service = SimulationTierService(
        lambda: SqlAlchemySimulationUnitOfWork(database.session_factory)
    )
    with pytest.raises(SimulationTierTransitionError, match="species"):
        service.transition(request)


def test_consolidation_preserves_entities_and_references(database: Database) -> None:
    population, now = setup_population(database)
    service = SimulationTierService(
        lambda: SqlAlchemySimulationUnitOfWork(database.session_factory)
    )
    materialization = service.transition(
        materialization_request(population, now, count=1)
    )
    character_id = materialization.request.character_ids[0]
    other_id = uuid4()
    relationship = Relationship(
        relationship_id=uuid4(),
        source_character_id=character_id,
        target_character_id=other_id,
        provenance=provenance(now),
    )
    goal = Goal(
        goal_id=uuid4(),
        character_id=character_id,
        desired_outcome="Hold the gate.",
        status=GoalStatus.ACTIVE,
        provenance=provenance(now),
    )
    plan = Plan(
        plan_id=uuid4(),
        character_id=character_id,
        goal_id=goal.goal_id,
        name="Watch",
        status=PlanStatus.ACTIVE,
        provenance=provenance(now),
    )
    with SqlAlchemySimulationUnitOfWork(database.session_factory) as uow:
        uow.repository.create_relationship(relationship)
        uow.repository.create_goal(goal)
        uow.repository.create_plan(plan)

    consolidation = SimulationTierTransitionRequest(
        request_id=uuid4(),
        world_id=population.world_id,
        operation=TierTransitionOperation.CONSOLIDATE,
        target_tier=SimulationTier.TIER_3,
        character_ids=(character_id,),
        expected_tier_versions={character_id: 1},
        resolution_reason="Explicit lower-resolution simulation request.",
        requested_at=now,
        provenance=provenance(now),
    )
    service.transition(consolidation)

    with SqlAlchemySimulationUnitOfWork(database.session_factory) as uow:
        assert uow.repository.get_character_identity(character_id) is not None
        assert uow.repository.get_materialized_individual_link(character_id) is not None
        tier_state = uow.repository.get_simulation_tier_state(character_id)
        assert tier_state is not None
        assert tier_state.tier == SimulationTier.TIER_3
        assert uow.repository.list_relationships(character_id) == (relationship,)
        assert uow.repository.get_goal(goal.goal_id) == goal
        assert uow.repository.get_plan(plan.plan_id) == plan


def test_stale_tier_version_is_rejected_and_repository_roundtrips(
    database: Database,
) -> None:
    population, now = setup_population(database)
    service = SimulationTierService(
        lambda: SqlAlchemySimulationUnitOfWork(database.session_factory)
    )
    initial = service.transition(materialization_request(population, now, count=1))
    character_id = initial.request.character_ids[0]
    request = SimulationTierTransitionRequest(
        request_id=uuid4(),
        world_id=population.world_id,
        operation=TierTransitionOperation.CONSOLIDATE,
        target_tier=SimulationTier.TIER_3,
        character_ids=(character_id,),
        expected_tier_versions={character_id: 9},
        resolution_reason="Explicit stale request.",
        requested_at=now,
        provenance=provenance(now),
    )
    with pytest.raises(StaleWorldStateError, match="version"):
        service.transition(request)
    with SqlAlchemySimulationUnitOfWork(database.session_factory) as uow:
        assert (
            uow.repository.get_tier_transition_result(initial.request.request_id)
            == initial
        )
