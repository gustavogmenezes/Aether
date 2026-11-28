from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from aether.contracts import (
    LifecycleStage,
    Population,
    PopulationCohort,
    RecordProvenance,
    ScheduledEvent,
    Species,
)
from aether.engines import DeterministicScheduledEventResolver
from decimal import Decimal


def test_population_change_rejects_species_unknown_lifecycle_stage() -> None:
    now = datetime(2026, 1, 1, tzinfo=UTC)
    provenance = RecordProvenance(
        source_type="test",
        source_id="lifecycle",
        created_at=now,
        updated_at=now,
        version=1,
    )
    species = Species(
        species_id=uuid4(),
        world_id=uuid4(),
        name="Example",
        lifecycle_stages=(LifecycleStage(code="adult", name="Adult", sequence=0),),
        provenance=provenance,
    )
    population = Population(
        population_id=uuid4(),
        world_id=species.world_id,
        species_id=species.species_id,
        location_id=uuid4(),
        name="Outlier",
        cohorts=(
            PopulationCohort(
                cohort_id=uuid4(),
                lifecycle_stage="larva",
                count=Decimal("1"),
            ),
        ),
        provenance=provenance,
    )
    event = ScheduledEvent(
        event_id=uuid4(),
        world_id=species.world_id,
        timeline_id=uuid4(),
        scheduled_at=now + timedelta(days=1),
        event_type="population-change",
        source_type="test",
        source_id="stage",
        payload_version="1",
        payload={
            "population_id": str(population.population_id),
            "cause": "configured",
            "changes": [
                {
                    "cohort_id": str(population.cohorts[0].cohort_id),
                    "delta": "1",
                }
            ],
        },
    )

    with pytest.raises(ValueError, match="valid for its species"):
        DeterministicScheduledEventResolver().resolve_population_change(
            event, population, species
        )
