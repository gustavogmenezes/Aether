from collections import defaultdict
from decimal import Decimal
from uuid import UUID

from aether.contracts import (
    AggregatePopulationSourceLink,
    MaterializationSpecification,
    Population,
    SimulationTierTransitionRequest,
)


class SimulationTierValidationError(ValueError):
    pass


class SimulationTierEngine:
    def validate_materialization(
        self,
        request: SimulationTierTransitionRequest,
        population: Population,
        existing_links: tuple[AggregatePopulationSourceLink, ...],
    ) -> None:
        if request.population_id != population.population_id:
            raise SimulationTierValidationError("Materialization source population mismatch")
        if request.world_id != population.world_id:
            raise SimulationTierValidationError("Materialization world mismatch")
        if population.provenance.version != request.expected_population_version:
            raise SimulationTierValidationError(
                "Population version does not match materialization request"
            )
        if request.requested_count is None or request.requested_count <= 0:
            raise SimulationTierValidationError(
                "Materialization count must be an explicit positive integer"
            )
        cohorts = {cohort.cohort_id: cohort for cohort in population.cohorts}
        counts: dict[UUID, int] = defaultdict(int)
        for specification in request.materializations:
            self._validate_specification(specification, population, cohorts)
            counts[specification.cohort_id] += 1
        accounted = {
            link.cohort_id: link.materialized_count for link in existing_links
        }
        for cohort_id, requested in counts.items():
            available = cohorts[cohort_id].count - Decimal(
                accounted.get(cohort_id, 0)
            )
            if Decimal(requested) > available:
                raise SimulationTierValidationError(
                    "Materialization would exceed the remaining aggregate cohort count"
                )

    @staticmethod
    def _validate_specification(
        specification: MaterializationSpecification,
        population: Population,
        cohorts: dict,
    ) -> None:
        if not specification.identity.display_name.strip():
            raise SimulationTierValidationError(
                "Materialization requires caller-supplied identity data"
            )
        cohort = cohorts.get(specification.cohort_id)
        if cohort is None:
            raise SimulationTierValidationError(
                "Materialization references a cohort outside the source population"
            )
        if (
            specification.supplied_species_id is not None
            and specification.supplied_species_id != population.species_id
        ):
            raise SimulationTierValidationError(
                "Caller-supplied species does not match the source population"
            )
        if (
            specification.supplied_location_id is not None
            and specification.supplied_location_id != population.location_id
        ):
            raise SimulationTierValidationError(
                "Caller-supplied location does not match the source population"
            )
        if (
            specification.supplied_lifecycle_stage is not None
            and specification.supplied_lifecycle_stage != cohort.lifecycle_stage
        ):
            raise SimulationTierValidationError(
                "Caller-supplied lifecycle stage does not match the source cohort"
            )
        identity_traits = specification.identity.defining_attributes
        for key, value in specification.compatible_traits.items():
            if key in identity_traits and identity_traits[key] != str(value):
                raise SimulationTierValidationError(
                    "Materialized trait contradicts caller-supplied identity data"
                )
