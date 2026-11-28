from decimal import Decimal
from uuid import uuid4

from aether.contracts import (
    AggregatePopulationSourceLink,
    MaterializedIndividualLink,
    RecordProvenance,
    SimulationTier,
    SimulationTierState,
    SimulationTierTransitionRequest,
    SimulationTierTransitionResult,
    TierTransitionOperation,
    TierTransitionResultStatus,
)
from aether.domain import (
    SimulationTierTransitionError,
    StaleWorldStateError,
)
from aether.domain.ports import SimulationUnitOfWorkFactory
from aether.engines import (
    SimulationTierEngine,
    SimulationTierValidationError,
)


class SimulationTierService:
    def __init__(
        self,
        unit_of_work_factory: SimulationUnitOfWorkFactory,
        engine: SimulationTierEngine | None = None,
    ) -> None:
        self._unit_of_work_factory = unit_of_work_factory
        self._engine = engine or SimulationTierEngine()

    def transition(
        self,
        request: SimulationTierTransitionRequest,
    ) -> SimulationTierTransitionResult:
        with self._unit_of_work_factory() as unit_of_work:
            existing_result = unit_of_work.repository.get_tier_transition_result(
                request.request_id
            )
            if existing_result is not None:
                if existing_result.request != request:
                    raise SimulationTierTransitionError(
                        "Request ID already represents a different tier transition"
                    )
                return existing_result.model_copy(
                    update={"status": TierTransitionResultStatus.REPLAYED}
                )

            if request.operation == TierTransitionOperation.MATERIALIZE:
                result = self._materialize(unit_of_work, request)
            else:
                result = self._change_resolution(unit_of_work, request)
            unit_of_work.repository.save_tier_transition_result(result)
            unit_of_work.commit()
            return result

    def _materialize(
        self,
        unit_of_work,
        request: SimulationTierTransitionRequest,
    ) -> SimulationTierTransitionResult:
        assert request.population_id is not None
        population = unit_of_work.repository.get_population(request.population_id)
        if population is None:
            raise SimulationTierTransitionError(
                "Materialization source population was not found"
            )
        if population.provenance.version != request.expected_population_version:
            raise StaleWorldStateError(
                "Population version does not match materialization request"
            )
        source_links = unit_of_work.repository.list_aggregate_population_source_links(
            population.population_id
        )
        try:
            self._engine.validate_materialization(request, population, source_links)
        except SimulationTierValidationError as error:
            raise SimulationTierTransitionError(str(error)) from error
        self._validate_history_events(unit_of_work, request)

        links_by_cohort = {link.cohort_id: link for link in source_links}
        tier_states: list[SimulationTierState] = []
        individual_links: list[MaterializedIndividualLink] = []
        for specification in request.materializations:
            existing_link = (
                unit_of_work.repository.get_materialized_individual_link(
                    specification.character_id
                )
            )
            if existing_link is not None:
                raise SimulationTierTransitionError(
                    "Materialized character link already exists"
                )
            existing_identity = unit_of_work.repository.get_character_identity(
                specification.character_id
            )
            if existing_identity is not None:
                if existing_identity != specification.identity:
                    raise SimulationTierTransitionError(
                        "Caller-supplied identity conflicts with the existing character"
                    )
            else:
                unit_of_work.repository.create_character_identity(specification.identity)
            if unit_of_work.repository.get_simulation_tier_state(
                specification.character_id
            ) is not None:
                raise SimulationTierTransitionError(
                    "Materialized character already has a tier state"
                )
            tier_state = self._new_state(request, specification.character_id)
            tier_states.append(tier_state)
            unit_of_work.repository.create_simulation_tier_state(tier_state)
            individual_link = MaterializedIndividualLink(
                link_id=uuid4(),
                world_id=request.world_id,
                population_id=population.population_id,
                cohort_id=specification.cohort_id,
                character_id=specification.character_id,
                compatible_traits=specification.compatible_traits,
                history_event_ids=specification.history_event_ids,
                provenance=self._provenance(request, 1),
            )
            individual_links.append(individual_link)
            unit_of_work.repository.create_materialized_individual_link(individual_link)

        updated_source_links = []
        for cohort_id, cohort in (
            (item.cohort_id, item) for item in population.cohorts
        ):
            added = sum(
                item.cohort_id == cohort_id for item in request.materializations
            )
            if not added:
                continue
            existing = links_by_cohort.get(cohort_id)
            if existing is None:
                updated = AggregatePopulationSourceLink(
                    link_id=uuid4(),
                    population_id=population.population_id,
                    cohort_id=cohort_id,
                    aggregate_count=cohort.count,
                    materialized_count=added,
                    population_version=population.provenance.version,
                    provenance=self._provenance(request, 1),
                )
                expected_version = None
            else:
                updated = existing.model_copy(
                    update={
                        "aggregate_count": cohort.count,
                        "materialized_count": existing.materialized_count + added,
                        "population_version": population.provenance.version,
                        "provenance": self._next_provenance(
                            existing.provenance, request
                        ),
                    }
                )
                expected_version = existing.provenance.version
            if Decimal(updated.materialized_count) > cohort.count:
                raise SimulationTierTransitionError(
                    "Materialization would exceed source cohort count"
                )
            unit_of_work.repository.save_aggregate_population_source_link(
                updated, expected_version
            )
            updated_source_links.append(updated)

        return SimulationTierTransitionResult(
            result_id=uuid4(),
            request=request,
            status=TierTransitionResultStatus.APPLIED,
            tier_states_after=tuple(tier_states),
            aggregate_source_links=tuple(updated_source_links),
            materialized_individual_links=tuple(individual_links),
            applied_at=request.requested_at,
        )

    def _change_resolution(
        self,
        unit_of_work,
        request: SimulationTierTransitionRequest,
    ) -> SimulationTierTransitionResult:
        before: list[SimulationTierState] = []
        after: list[SimulationTierState] = []
        for character_id in request.character_ids:
            state = unit_of_work.repository.get_simulation_tier_state(character_id)
            if state is None:
                raise SimulationTierTransitionError(
                    "Resolution transition requires an existing tier state"
                )
            if state.world_id != request.world_id:
                raise SimulationTierTransitionError("Tier state belongs to another world")
            expected = request.expected_tier_versions[character_id]
            if state.provenance.version != expected:
                raise StaleWorldStateError(
                    "Simulation tier version does not match transition request"
                )
            if not self._valid_resolution_change(request, state.tier):
                raise SimulationTierTransitionError(
                    "Requested operation does not explicitly change tier resolution"
                )
            before.append(state)
            changed = state.model_copy(
                update={
                    "tier": request.target_tier,
                    "resolution_reason": request.resolution_reason,
                    "provenance": self._next_provenance(state.provenance, request),
                }
            )
            after.append(changed)
            unit_of_work.repository.save_simulation_tier_state(
                changed, expected_version=expected
            )
        return SimulationTierTransitionResult(
            result_id=uuid4(),
            request=request,
            status=TierTransitionResultStatus.APPLIED,
            tier_states_before=tuple(before),
            tier_states_after=tuple(after),
            applied_at=request.requested_at,
        )

    @staticmethod
    def _valid_resolution_change(
        request: SimulationTierTransitionRequest, current: SimulationTier
    ) -> bool:
        rank = {
            SimulationTier.TIER_1: 1,
            SimulationTier.TIER_2: 2,
            SimulationTier.TIER_3: 3,
        }
        if request.operation == TierTransitionOperation.PROMOTE:
            return rank[request.target_tier] < rank[current]
        if request.operation in {
            TierTransitionOperation.DEMOTE,
            TierTransitionOperation.CONSOLIDATE,
        }:
            return rank[request.target_tier] > rank[current]
        return False

    @staticmethod
    def _validate_history_events(unit_of_work, request: SimulationTierTransitionRequest):
        for specification in request.materializations:
            for event_id in specification.history_event_ids:
                event = unit_of_work.repository.get_event(event_id)
                if event is None or event.world_id != request.world_id:
                    raise SimulationTierTransitionError(
                        "Materialization history references an unknown or foreign event"
                    )

    @staticmethod
    def _new_state(
        request: SimulationTierTransitionRequest, character_id
    ) -> SimulationTierState:
        return SimulationTierState(
            state_id=uuid4(),
            world_id=request.world_id,
            entity_type="character",
            entity_id=character_id,
            tier=request.target_tier,
            resolution_reason=request.resolution_reason,
            provenance=SimulationTierService._provenance(request, 1),
        )

    @staticmethod
    def _provenance(
        request: SimulationTierTransitionRequest, version: int
    ) -> RecordProvenance:
        timestamp = request.requested_at
        return RecordProvenance(
            source_type=request.provenance.source_type,
            source_id=request.provenance.source_id,
            origin_event_id=request.provenance.origin_event_id,
            created_at=timestamp,
            updated_at=timestamp,
            version=version,
        )

    @staticmethod
    def _next_provenance(
        current: RecordProvenance, request: SimulationTierTransitionRequest
    ) -> RecordProvenance:
        return RecordProvenance(
            source_type=current.source_type,
            source_id=current.source_id,
            origin_event_id=request.provenance.origin_event_id,
            created_at=current.created_at,
            updated_at=request.requested_at,
            version=current.version + 1,
        )
