from datetime import datetime
from uuid import UUID

from aether.contracts import (
    PlanStep,
    PlanStepStatus,
    OrganizationPlanStep,
    Journey,
    JourneyStatus,
    ScheduledEvent,
    ScheduledEventOutcome,
    ScheduledEventResolution,
    Population,
    PopulationChangePayload,
    Species,
    PopulationCohort,
    EcologicalProcess,
    EcologicalProcessChangePayload,
    HealthState,
    HealthConditionChangePayload,
)


class DeterministicScheduledEventResolver:
    def resolve(
        self,
        event: ScheduledEvent,
        plan_step: PlanStep | OrganizationPlanStep | None,
    ) -> ScheduledEventResolution:
        if event.event_type not in {"npc-plan-step", "organization-plan-step"}:
            return ScheduledEventResolution(
                scheduled_event_id=event.event_id,
                outcome=ScheduledEventOutcome.UNCHANGED,
                payload=dict(event.payload),
            )

        payload_step_id = event.payload.get("plan_step_id")
        owner_key = (
            "character_id"
            if event.event_type == "npc-plan-step"
            else "organization_id"
        )
        if not isinstance(payload_step_id, str) or not isinstance(
            event.payload.get(owner_key), str
        ):
            raise ValueError("Plan-step event payload is incomplete")
        if plan_step is None:
            raise ValueError("Plan-step event references an unknown plan step")
        if UUID(payload_step_id) != plan_step.step_id:
            raise ValueError("Plan-step event and stored step do not match")
        if plan_step.status != PlanStepStatus.SCHEDULED:
            raise ValueError("Only scheduled plan steps can be resolved")

        return ScheduledEventResolution(
            scheduled_event_id=event.event_id,
            outcome=ScheduledEventOutcome.COMPLETED,
            payload={
                **event.payload,
                "resolution": "completed",
                "action_intent": plan_step.action_intent,
            },
            plan_step_id=plan_step.step_id,
            reason="Deterministic plan-step execution completed",
        )

    def resolve_journey(
        self,
        event: ScheduledEvent,
        journey: Journey,
    ) -> ScheduledEventResolution:
        payload_journey_id = event.payload.get("journey_id")
        if event.event_type != "travel-arrival" or not isinstance(
            payload_journey_id, str
        ):
            raise ValueError("Travel-arrival event references an unknown journey")
        if UUID(payload_journey_id) != journey.journey_id:
            raise ValueError("Travel-arrival event and journey do not match")
        if journey.scheduled_event_id != event.event_id:
            raise ValueError("Travel-arrival event does not belong to the journey")
        if journey.status != JourneyStatus.IN_TRANSIT:
            raise ValueError("Only in-transit journeys can arrive")
        return ScheduledEventResolution(
            scheduled_event_id=event.event_id,
            outcome=ScheduledEventOutcome.COMPLETED,
            payload={
                **event.payload,
                "start_location_id": str(journey.start_location_id),
                "end_location_id": str(journey.end_location_id),
                "resolution": "arrived",
            },
            journey_id=journey.journey_id,
            reason="Configured route duration completed",
        )

    def resolve_population_change(
        self,
        event: ScheduledEvent,
        population: Population,
        species: Species,
    ) -> ScheduledEventResolution:
        payload = PopulationChangePayload.model_validate(event.payload)
        if event.event_type != "population-change":
            raise ValueError("Population resolver received a different event type")
        if payload.population_id != population.population_id:
            raise ValueError("Population event target does not match its population")
        if (
            population.world_id != event.world_id
            or species.world_id != event.world_id
            or population.species_id != species.species_id
        ):
            raise ValueError("Population event belongs to another world or species")
        if (
            payload.target_location_id is not None
            and payload.target_location_id != population.location_id
        ):
            raise ValueError("Population event target location does not match")
        stages = {stage.code for stage in species.lifecycle_stages}
        cohorts_by_id = {cohort.cohort_id: cohort for cohort in population.cohorts}
        replacements: dict[UUID, PopulationCohort] = {}
        changed_cohort_ids: set[UUID] = set()
        for change in payload.changes:
            cohort = (
                cohorts_by_id.get(change.cohort_id)
                if change.cohort_id is not None
                else next(
                    (
                        item
                        for item in population.cohorts
                        if item.lifecycle_stage == change.lifecycle_stage
                    ),
                    None,
                )
            )
            if cohort is None:
                raise ValueError("Population change references an unknown cohort")
            if cohort.cohort_id in changed_cohort_ids:
                raise ValueError("Population event changes the same cohort more than once")
            changed_cohort_ids.add(cohort.cohort_id)
            if change.cohort_id is not None and change.lifecycle_stage is not None:
                if change.lifecycle_stage != cohort.lifecycle_stage:
                    raise ValueError("Population change cohort and stage do not match")
            if cohort.lifecycle_stage not in stages:
                raise ValueError("Population cohort is not valid for its species")
            updated_count = cohort.count + change.delta
            if updated_count < 0:
                raise ValueError("Population change would produce a negative count")
            updated = PopulationCohort(
                cohort_id=cohort.cohort_id,
                lifecycle_stage=cohort.lifecycle_stage,
                count=updated_count,
                births=cohort.births + change.birth_delta,
                mortality=cohort.mortality + change.mortality_delta,
                migration_in=cohort.migration_in + change.migration_in_delta,
                migration_out=cohort.migration_out + change.migration_out_delta,
            )
            replacements[updated.cohort_id] = updated
        cohorts = tuple(replacements.get(cohort.cohort_id, cohort) for cohort in population.cohorts)
        updated_population = population.model_copy(
            update={
                "cohorts": cohorts,
                "provenance": self._advanced_provenance(
                    population.provenance,
                    event.event_id,
                    event.scheduled_at,
                ),
            }
        )
        return ScheduledEventResolution(
            scheduled_event_id=event.event_id,
            outcome=ScheduledEventOutcome.COMPLETED,
            payload={
                **event.payload,
                "resolution": "applied",
                "total_count": str(updated_population.total_count),
            },
            population=updated_population,
            reason="Explicit population consequences applied",
        )

    def resolve_ecological_process(
        self,
        event: ScheduledEvent,
        process: EcologicalProcess,
    ) -> ScheduledEventResolution:
        payload = EcologicalProcessChangePayload.model_validate(event.payload)
        if event.event_type != "ecological-process":
            raise ValueError("Ecological resolver received a different event type")
        if payload.process_id != process.process_id:
            raise ValueError("Ecological event target does not match its process")
        if (
            process.world_id != event.world_id
            or payload.target_location_id != process.location_id
        ):
            raise ValueError("Ecological event belongs to another location or world")
        if payload.population_id is not None and (
            payload.population_id not in process.population_links
        ):
            raise ValueError("Ecological event references an unlinked population")
        measures = dict(process.measures)
        for key, delta in payload.deltas.items():
            measures[key] = measures.get(key, 0) + delta
        updated = process.model_copy(
            update={
                "measures": measures,
                "resource_links": tuple(
                    dict.fromkeys((*process.resource_links, *payload.resource_links))
                ),
                "provenance": self._advanced_provenance(
                    process.provenance, event.event_id, event.scheduled_at
                ),
            }
        )
        return ScheduledEventResolution(
            scheduled_event_id=event.event_id,
            outcome=ScheduledEventOutcome.COMPLETED,
            payload={
                **event.payload,
                "resolution": "applied",
                "resulting_measures": {
                    key: str(value) for key, value in sorted(measures.items())
                },
            },
            ecological_process=updated,
            reason="Explicit ecological consequences applied",
        )

    def resolve_health_condition_change(
        self,
        event: ScheduledEvent,
        state: HealthState,
    ) -> ScheduledEventResolution:
        payload = HealthConditionChangePayload.model_validate(event.payload)
        if event.event_type != "health-condition-change":
            raise ValueError("Health resolver received a different event type")
        if payload.character_id != state.character_id:
            raise ValueError("Health event target does not match its character")
        existing = {item.condition_id: item for item in state.conditions}
        for condition_id in payload.remove_condition_ids:
            if condition_id not in existing:
                raise ValueError("Health event references an unknown condition")
            del existing[condition_id]
        for condition in payload.add_conditions:
            if condition.condition_id in existing:
                raise ValueError("Health event would duplicate a condition")
            existing[condition.condition_id] = condition
        values = {
            "physical_integrity": state.physical_integrity,
            "consciousness": state.consciousness,
            "ability_to_act": state.ability_to_act,
            "ability_to_fight": state.ability_to_fight,
        }
        values.update(payload.dimension_changes)
        updated = HealthState(
            state_id=state.state_id,
            character_id=state.character_id,
            species_id=state.species_id,
            physical_integrity=values["physical_integrity"],
            consciousness=values["consciousness"],
            ability_to_act=values["ability_to_act"],
            ability_to_fight=values["ability_to_fight"],
            conditions=tuple(existing.values()),
            provenance=self._advanced_provenance(
                state.provenance, event.event_id, event.scheduled_at
            ),
        )
        return ScheduledEventResolution(
            scheduled_event_id=event.event_id,
            outcome=ScheduledEventOutcome.COMPLETED,
            payload={**event.payload, "resolution": "applied"},
            health_state=updated,
            reason="Explicit health consequences applied",
        )

    @staticmethod
    def _advanced_provenance(provenance, origin_event_id: UUID, updated_at: datetime):
        return provenance.model_copy(
            update={
                "origin_event_id": origin_event_id,
                "updated_at": updated_at,
                "version": provenance.version + 1,
            }
        )
