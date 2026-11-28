from collections.abc import Callable
from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID, uuid5

from aether.contracts import (
    AdvanceTimeCommand,
    AdvanceUntilEventCommand,
    ScheduledEvent,
    SimulationRunRecord,
    SimulationRunStatus,
    TemporalAdvanceResult,
    ScheduledEventOutcome,
    ResourceEffectOutcome,
    ResourceOwnerKind,
    ResourceTransaction,
    OrganizationPlanStep,
    ActorPosition,
    ActorReference,
    ActorType,
    AuthorityContext,
)
from aether.domain import (
    DuplicateSimulationRunError,
    InvalidTemporalAdvanceError,
    SimulationRunInProgressError,
    TimelineMismatchError,
    ScheduledEventResolverPort,
    CulturalScheduledEventResolverPort,
    LanguageCommunicationPort,
    validate_organization_authority,
    validate_institutional_authority,
    NormativeStrategicResolverPort,
    PublicExpressionResolverPort,
)
from aether.domain.ports import SimulationUnitOfWorkFactory
from aether.domain.simulation import ScheduledEventStatus
from aether.engines import (
    CulturalScheduledEventResolver,
    DeterministicScheduledEventResolver,
    EventOrderingEngine,
    LanguageCommunicationEngine,
    PerceptionAndInterpretationEngine,
    NormativeStrategicResolver,
    PublicExpressionResolver,
)


class TemporalAdvanceService:
    def __init__(
        self,
        unit_of_work_factory: SimulationUnitOfWorkFactory,
        *,
        ordering_engine: EventOrderingEngine | None = None,
        interpretation_engine: PerceptionAndInterpretationEngine | None = None,
        scheduled_resolver: ScheduledEventResolverPort | None = None,
        cultural_resolver: CulturalScheduledEventResolverPort | None = None,
        language_engine: LanguageCommunicationPort | None = None,
        clock: Callable[[], datetime] | None = None,
        normative_resolver: NormativeStrategicResolverPort | None = None,
        expression_resolver: PublicExpressionResolverPort | None = None,
    ) -> None:
        self._unit_of_work_factory = unit_of_work_factory
        self._ordering_engine = ordering_engine or EventOrderingEngine()
        self._interpretation_engine = (
            interpretation_engine or PerceptionAndInterpretationEngine()
        )
        self._scheduled_resolver = (
            scheduled_resolver or DeterministicScheduledEventResolver()
        )
        self._cultural_resolver = cultural_resolver or CulturalScheduledEventResolver()
        self._language_engine = language_engine or LanguageCommunicationEngine()
        self._clock = clock or (lambda: datetime.now(UTC))
        self._normative_resolver = normative_resolver or NormativeStrategicResolver()
        self._expression_resolver = expression_resolver or PublicExpressionResolver()

    def advance_time(self, command: AdvanceTimeCommand) -> TemporalAdvanceResult:
        with self._unit_of_work_factory() as unit_of_work:
            existing = unit_of_work.repository.get_run(command.simulation_run_id)
            if existing is not None:
                if existing.status == SimulationRunStatus.PREPARED:
                    self._validate_prepared_time_run(existing, command)
                else:
                    return self._replay_or_raise(
                        existing,
                        command.world_id,
                        command.timeline_id,
                    )
            else:
                clock = unit_of_work.repository.get_clock(
                    command.world_id,
                    command.timeline_id,
                )
                if clock is None:
                    raise InvalidTemporalAdvanceError("World clock was not found")
                target_time = clock.current_time + command.duration
                run = self._new_run(
                    simulation_run_id=command.simulation_run_id,
                    operation="advance-time",
                    world_id=command.world_id,
                    timeline_id=command.timeline_id,
                    initial_time=clock.current_time,
                    target_time=target_time,
                )
                unit_of_work.repository.create_run(run)
                unit_of_work.commit()

        return self._apply_run(command.simulation_run_id)

    def prepare_time(self, command: AdvanceTimeCommand) -> SimulationRunRecord:
        with self._unit_of_work_factory() as unit_of_work:
            existing = unit_of_work.repository.get_run(command.simulation_run_id)
            if existing is not None:
                if existing.status != SimulationRunStatus.PREPARED:
                    self._replay_or_raise(
                        existing,
                        command.world_id,
                        command.timeline_id,
                    )
                self._validate_prepared_time_run(existing, command)
                return existing

            clock = unit_of_work.repository.get_clock(
                command.world_id,
                command.timeline_id,
            )
            if clock is None:
                raise InvalidTemporalAdvanceError("World clock was not found")
            run = self._new_run(
                simulation_run_id=command.simulation_run_id,
                operation="advance-time",
                world_id=command.world_id,
                timeline_id=command.timeline_id,
                initial_time=clock.current_time,
                target_time=clock.current_time + command.duration,
            )
            unit_of_work.repository.create_run(run)
            unit_of_work.commit()
            return run

    def result_for_completed_run(
        self,
        run: SimulationRunRecord,
    ) -> TemporalAdvanceResult:
        if run.status != SimulationRunStatus.COMPLETED:
            raise SimulationRunInProgressError(
                f"Simulation run {run.simulation_run_id} is {run.status.value}"
            )
        return self._completed_result(run)

    def advance_until_event(
        self,
        command: AdvanceUntilEventCommand,
    ) -> TemporalAdvanceResult:
        with self._unit_of_work_factory() as unit_of_work:
            existing = unit_of_work.repository.get_run(command.simulation_run_id)
            if existing is not None:
                return self._replay_or_raise(existing, command.world_id, command.timeline_id)

            clock = unit_of_work.repository.get_clock(
                command.world_id,
                command.timeline_id,
            )
            target_event = unit_of_work.repository.get_scheduled_event(
                command.scheduled_event_id
            )
            target_status = unit_of_work.repository.get_scheduled_event_status(
                command.scheduled_event_id
            )
            if clock is None:
                raise InvalidTemporalAdvanceError("World clock was not found")
            if target_event is None or target_status is None:
                raise InvalidTemporalAdvanceError("Scheduled target event was not found")
            self._validate_target_event(command, clock.current_time, target_event)
            if target_status != ScheduledEventStatus.PENDING:
                raise InvalidTemporalAdvanceError("Target event is not pending")

            run = self._new_run(
                simulation_run_id=command.simulation_run_id,
                operation="advance-until-event",
                world_id=command.world_id,
                timeline_id=command.timeline_id,
                initial_time=clock.current_time,
                target_time=target_event.scheduled_at,
            )
            unit_of_work.repository.create_run(run)
            unit_of_work.commit()

        return self._apply_run(command.simulation_run_id)

    def _apply_run(self, simulation_run_id: UUID) -> TemporalAdvanceResult:
        try:
            with self._unit_of_work_factory() as unit_of_work:
                run = unit_of_work.repository.get_run(simulation_run_id)
                if run is None:
                    raise KeyError(f"Unknown simulation run {simulation_run_id}")
                if run.status != SimulationRunStatus.PREPARED:
                    raise SimulationRunInProgressError(
                        f"Simulation run {simulation_run_id} is {run.status.value}"
                    )
                clock = unit_of_work.repository.get_clock(
                    run.world_id,
                    run.timeline_id,
                )
                if clock is None:
                    raise InvalidTemporalAdvanceError("World clock was not found")
                if clock.current_time != run.initial_time:
                    raise InvalidTemporalAdvanceError(
                        "World clock no longer matches the prepared run"
                    )

                unit_of_work.repository.update_run(
                    simulation_run_id,
                    status=SimulationRunStatus.RUNNING,
                )
                unit_of_work.commit()

                due_events = unit_of_work.repository.list_due_scheduled_events(
                    run.world_id,
                    run.timeline_id,
                    after=clock.current_time,
                    through=run.target_time,
                )
                ordered_events = self._ordering_engine.order(due_events)
                materialized = self._ordering_engine.materialize(
                    ordered_events,
                    recorded_at=self._clock(),
                    first_sequence=unit_of_work.repository.get_latest_event_sequence(
                        run.world_id,
                        run.timeline_id,
                    )
                    + 1,
                )
                for scheduled, event in zip(ordered_events, materialized, strict=True):
                    plan_step = None
                    journey = None
                    population = None
                    species = None
                    ecological_process = None
                    health_state = None
                    knowledge_artifact = None
                    technology = None
                    education_enrollment = None
                    education_program = None
                    learning_opportunity = None
                    religion_tradition = None
                    normative_resolution = None
                    expression_resolution = None
                    if scheduled.event_type in {
                        "legal-proceeding-transition",
                        "treaty-change",
                        "strategic-escalation",
                        "investigation-completion",
                        "security-resolution",
                    }:
                        normative_resolution = self._resolve_normative_event(
                            scheduled, unit_of_work.repository
                        )
                    if scheduled.event_type == "public-publication":
                        publication_payload = scheduled.payload.get("publication")
                        if not isinstance(publication_payload, dict):
                            raise ValueError("Publication event has no publication")
                        channel_id = publication_payload.get("channel_id")
                        if not isinstance(channel_id, str):
                            raise ValueError("Publication event has no channel ID")
                        if (
                            unit_of_work.repository.get_public_channel(UUID(channel_id))
                            is None
                        ):
                            raise ValueError(
                                "Publication references an unknown public channel"
                            )
                        expression_resolution = (
                            self._expression_resolver.resolve_publication(scheduled)
                        )
                    if scheduled.event_type == "travel-arrival":
                        payload_journey_id = scheduled.payload.get("journey_id")
                        if not isinstance(payload_journey_id, str):
                            raise ValueError("Travel-arrival event has no journey ID")
                        journey = unit_of_work.repository.get_journey(
                            UUID(payload_journey_id)
                        )
                        if journey is None:
                            raise ValueError(
                                "Travel-arrival event references an unknown journey"
                            )
                        if (
                            journey.world_id != run.world_id
                            or journey.timeline_id != run.timeline_id
                        ):
                            raise ValueError(
                                "Travel-arrival belongs to another world or timeline"
                            )
                    if scheduled.event_type in {
                        "npc-plan-step",
                        "organization-plan-step",
                    }:
                        payload_step_id = scheduled.payload.get("plan_step_id")
                        if not isinstance(payload_step_id, str):
                            raise ValueError(
                                "Plan-step event payload has no plan step ID"
                            )
                        step_id = UUID(payload_step_id)
                        is_organization = (
                            scheduled.event_type == "organization-plan-step"
                        )
                        plan_step = (
                            unit_of_work.repository.get_organization_plan_step(step_id)
                            if is_organization
                            else unit_of_work.repository.get_plan_step(step_id)
                        )
                        if plan_step is None:
                            raise ValueError(
                                "Plan-step event references an unknown plan step"
                            )
                        if is_organization:
                            if not isinstance(plan_step, OrganizationPlanStep):
                                raise ValueError(
                                    "Organization event loaded a non-organization step"
                                )
                            plan = unit_of_work.repository.get_organization_plan(
                                plan_step.plan_id
                            )
                            payload_owner = scheduled.payload.get("organization_id")
                            payload_responsible = scheduled.payload.get(
                                "responsible_character_id"
                            )
                            if (
                                plan is None
                                or not isinstance(payload_owner, str)
                                or plan.organization_id != UUID(payload_owner)
                                or not isinstance(payload_responsible, str)
                            ):
                                raise ValueError(
                                    "Organization event does not own the plan"
                                )
                            responsible_id = UUID(payload_responsible)
                            membership = (
                                unit_of_work.repository.get_organization_membership(
                                    plan.organization_id, responsible_id
                                )
                            )
                            grants = (
                                unit_of_work.repository
                                .list_organization_authority_grants(
                                    plan.organization_id, responsible_id
                                )
                            )
                            validate_organization_authority(
                                membership, grants, plan_step
                            )
                        else:
                            plan = unit_of_work.repository.get_plan(plan_step.plan_id)
                            payload_owner = scheduled.payload.get("character_id")
                            if (
                                plan is None
                                or not isinstance(payload_owner, str)
                                or plan.character_id != UUID(payload_owner)
                            ):
                                raise ValueError(
                                    "NPC plan-step event character does not own the plan"
                                )
                    if scheduled.event_type == "population-change":
                        payload_population_id = scheduled.payload.get("population_id")
                        if not isinstance(payload_population_id, str):
                            raise ValueError("Population event has no population ID")
                        population = unit_of_work.repository.get_population(
                            UUID(payload_population_id)
                        )
                        if population is None:
                            raise ValueError(
                                "Population event references an unknown population"
                            )
                        species = unit_of_work.repository.get_species(
                            population.species_id
                        )
                        if species is None:
                            raise ValueError(
                                "Population event references an unknown species"
                            )
                    elif scheduled.event_type == "ecological-process":
                        payload_process_id = scheduled.payload.get("process_id")
                        if not isinstance(payload_process_id, str):
                            raise ValueError(
                                "Ecological event has no process ID"
                            )
                        ecological_process = (
                            unit_of_work.repository.get_ecological_process(
                                UUID(payload_process_id)
                            )
                        )
                        if ecological_process is None:
                            raise ValueError(
                                "Ecological event references an unknown process"
                            )
                    elif scheduled.event_type == "health-condition-change":
                        payload_character_id = scheduled.payload.get("character_id")
                        if not isinstance(payload_character_id, str):
                            raise ValueError("Health event has no character ID")
                        health_state = unit_of_work.repository.get_health_state(
                            UUID(payload_character_id)
                        )
                        if health_state is None:
                            raise ValueError(
                                "Health event references an unknown health state"
                            )
                    elif scheduled.event_type == "knowledge-transmission":
                        payload_id = scheduled.payload.get("artifact_id")
                        if not isinstance(payload_id, str):
                            raise ValueError("Knowledge event has no artifact ID")
                        knowledge_artifact = (
                            unit_of_work.repository.get_knowledge_artifact(
                                UUID(payload_id)
                            )
                        )
                        if knowledge_artifact is None:
                            raise ValueError(
                                "Knowledge event references an unknown artifact"
                            )
                    elif scheduled.event_type == "technology-use-completion":
                        payload_id = scheduled.payload.get("technology_id")
                        if not isinstance(payload_id, str):
                            raise ValueError("Technology event has no technology ID")
                        technology = unit_of_work.repository.get_technology(
                            UUID(payload_id)
                        )
                        if technology is None:
                            raise ValueError(
                                "Technology event references an unknown technology"
                            )
                    elif scheduled.event_type == "learning-assessment":
                        payload_id = scheduled.payload.get("enrollment_id")
                        opportunity_id = scheduled.payload.get("opportunity_id")
                        if not isinstance(payload_id, str):
                            raise ValueError("Assessment event has no enrollment ID")
                        education_enrollment = (
                            unit_of_work.repository.get_education_enrollment(
                                UUID(payload_id)
                            )
                        )
                        if education_enrollment is None:
                            raise ValueError(
                                "Assessment references an unknown enrollment"
                            )
                        education_program = (
                            unit_of_work.repository.get_education_program(
                                education_enrollment.program_id
                            )
                        )
                        if education_program is None:
                            raise ValueError(
                                "Assessment references an unknown education program"
                            )
                        if opportunity_id is not None:
                            if not isinstance(opportunity_id, str):
                                raise ValueError(
                                    "Assessment opportunity ID is invalid"
                                )
                            learning_opportunity = (
                                unit_of_work.repository.get_learning_opportunity(
                                    UUID(opportunity_id)
                                )
                            )
                            if learning_opportunity is None:
                                raise ValueError(
                                    "Assessment references an unknown opportunity"
                                )
                    elif scheduled.event_type == "religious-ritual":
                        payload_id = scheduled.payload.get("tradition_id")
                        if not isinstance(payload_id, str):
                            raise ValueError("Ritual event has no tradition ID")
                        religion_tradition = (
                            unit_of_work.repository.get_religion_tradition(
                                UUID(payload_id)
                            )
                        )
                        if religion_tradition is None:
                            raise ValueError(
                                "Ritual event references an unknown tradition"
                            )
                    if expression_resolution is not None:
                        resolution = expression_resolution
                    elif normative_resolution is not None:
                        resolution = normative_resolution
                    elif knowledge_artifact is not None:
                        resolution = (
                            self._cultural_resolver.resolve_knowledge_transmission(
                                scheduled, knowledge_artifact
                            )
                        )
                    elif technology is not None:
                        resolution = self._cultural_resolver.resolve_technology_use(
                            scheduled, technology
                        )
                    elif education_enrollment is not None and education_program is not None:
                        resolution = (
                            self._cultural_resolver.resolve_learning_assessment(
                                scheduled,
                                education_enrollment,
                                education_program,
                                learning_opportunity,
                            )
                        )
                    elif religion_tradition is not None:
                        resolution = self._cultural_resolver.resolve_religious_ritual(
                            scheduled, religion_tradition
                        )
                    elif population is not None and species is not None:
                        resolver = getattr(
                            self._scheduled_resolver, "resolve_population_change", None
                        )
                        if resolver is None:
                            raise ValueError(
                                "Scheduled resolver does not support population changes"
                            )
                        resolution = resolver(scheduled, population, species)
                    elif ecological_process is not None:
                        resolver = getattr(
                            self._scheduled_resolver, "resolve_ecological_process", None
                        )
                        if resolver is None:
                            raise ValueError(
                                "Scheduled resolver does not support ecological processes"
                            )
                        resolution = resolver(scheduled, ecological_process)
                    elif health_state is not None:
                        resolver = getattr(
                            self._scheduled_resolver,
                            "resolve_health_condition_change",
                            None,
                        )
                        if resolver is None:
                            raise ValueError(
                                "Scheduled resolver does not support health changes"
                            )
                        resolution = resolver(scheduled, health_state)
                    elif journey is None:
                        resolution = self._scheduled_resolver.resolve(
                            scheduled,
                            plan_step,
                        )
                    else:
                        journey_resolver = getattr(
                            self._scheduled_resolver,
                            "resolve_journey",
                            None,
                        )
                        resolution = (
                            journey_resolver(scheduled, journey)
                            if journey_resolver is not None
                            else self._scheduled_resolver.resolve(
                                scheduled, None
                            )
                        )
                    if resolution.scheduled_event_id != scheduled.event_id:
                        raise ValueError("Resolver returned a different scheduled event")
                    if (
                        resolution.plan_step_id is not None
                        and plan_step is not None
                        and resolution.plan_step_id != plan_step.step_id
                    ):
                        raise ValueError(
                            "Resolver returned a plan step different from the intent"
                        )
                    if (
                        resolution.journey_id is not None
                        and journey is not None
                        and resolution.journey_id != journey.journey_id
                    ):
                        raise ValueError(
                            "Resolver returned a journey different from the intent"
                        )
                    if (
                        resolution.population is None
                        and scheduled.event_type == "population-change"
                    ):
                        raise ValueError("Population resolution has no resulting state")
                    if (
                        resolution.ecological_process is None
                        and scheduled.event_type == "ecological-process"
                    ):
                        raise ValueError("Ecological resolution has no resulting state")
                    if (
                        resolution.health_state is None
                        and scheduled.event_type == "health-condition-change"
                    ):
                        raise ValueError("Health resolution has no resulting state")
                    if resolution.outcome == ScheduledEventOutcome.COMPLETED:
                        if resolution.plan_step_id is not None:
                            if isinstance(plan_step, OrganizationPlanStep):
                                unit_of_work.repository.mark_organization_plan_step_completed(
                                    resolution.plan_step_id
                                )
                            else:
                                unit_of_work.repository.mark_plan_step_completed(
                                    resolution.plan_step_id
                                )
                        if (
                            resolution.population is not None
                            and population is not None
                        ):
                            unit_of_work.repository.save_population(
                                resolution.population,
                                population.provenance.version,
                            )
                        if (
                            resolution.ecological_process is not None
                            and ecological_process is not None
                        ):
                            unit_of_work.repository.save_ecological_process(
                                resolution.ecological_process,
                                ecological_process.provenance.version,
                            )
                        if resolution.health_state is not None and health_state is not None:
                            unit_of_work.repository.save_health_state(
                                resolution.health_state,
                                health_state.provenance.version,
                            )
                        if (
                            resolution.knowledge_artifact is not None
                            and knowledge_artifact is not None
                        ):
                            unit_of_work.repository.save_knowledge_artifact(
                                resolution.knowledge_artifact,
                                knowledge_artifact.provenance.version,
                            )
                        if resolution.technology is not None and technology is not None:
                            unit_of_work.repository.save_technology(
                                resolution.technology,
                                technology.provenance.version,
                            )
                        for record in resolution.lifecycle_records:
                            unit_of_work.repository.create_knowledge_lifecycle_record(
                                record
                            )
                        for outcome in resolution.assessment_outcomes:
                            unit_of_work.repository.create_assessment_outcome(outcome)
                        for completion in resolution.ritual_completions:
                            unit_of_work.repository.create_ritual_completion(
                                completion
                            )
                        if resolution.legal_case is not None:
                            unit_of_work.repository.save_legal_case(
                                resolution.legal_case,
                                resolution.legal_case.provenance.version - 1,
                            )
                        if resolution.legal_proceeding is not None:
                            unit_of_work.repository.save_legal_proceeding(
                                resolution.legal_proceeding,
                                resolution.legal_proceeding.provenance.version - 1,
                            )
                        for sanction in resolution.sanctions:
                            unit_of_work.repository.create_sanction(sanction)
                        if resolution.investigation is not None:
                            unit_of_work.repository.save_investigation(
                                resolution.investigation,
                                resolution.investigation.provenance.version - 1,
                            )
                        for evidence in resolution.evidence_records:
                            unit_of_work.repository.create_evidence(evidence)
                        if resolution.treaty is not None:
                            unit_of_work.repository.save_treaty(
                                resolution.treaty,
                                resolution.treaty.provenance.version - 1,
                            )
                        if resolution.strategic_conflict is not None:
                            unit_of_work.repository.save_strategic_conflict(
                                resolution.strategic_conflict,
                                resolution.strategic_conflict.provenance.version - 1,
                            )
                        if resolution.security_threat is not None:
                            unit_of_work.repository.save_security_threat(
                                resolution.security_threat,
                                resolution.security_threat.provenance.version - 1,
                            )
                        if resolution.publication is not None:
                            unit_of_work.repository.create_public_information(
                                resolution.publication
                            )
                        for reception in resolution.collective_receptions:
                            unit_of_work.repository.create_collective_reception(
                                reception
                            )
                        if resolution.intelligence_operation is not None:
                            unit_of_work.repository.save_intelligence_operation(
                                resolution.intelligence_operation,
                                resolution.intelligence_operation.provenance.version - 1,
                            )
                        for security_resolution in resolution.security_resolutions:
                            unit_of_work.repository.create_security_resolution(
                                security_resolution
                            )
                        for knowledge in resolution.character_knowledge:
                            unit_of_work.repository.create_character_knowledge(
                                knowledge
                            )
                    elif resolution.outcome == ScheduledEventOutcome.FAILED:
                        if resolution.plan_step_id is None:
                            raise ValueError(
                                "Failed plan-step resolution requires a plan step ID"
                            )
                        reason = (
                            resolution.reason or "Scheduled event resolution failed"
                        )
                        if isinstance(plan_step, OrganizationPlanStep):
                            unit_of_work.repository.mark_organization_plan_step_failed(
                                resolution.plan_step_id, reason
                            )
                        else:
                            unit_of_work.repository.mark_plan_step_failed(
                                resolution.plan_step_id, reason
                            )
                    elif resolution.plan_step_id is not None:
                        raise ValueError(
                            "Unchanged resolution cannot specify a plan-step transition"
                        )
                    resource_changes = self._apply_resource_effects(
                        unit_of_work.repository,
                        run,
                        scheduled,
                        event,
                        plan_step,
                        resolution.outcome,
                    )
                    if journey is not None:
                        if resolution.outcome != ScheduledEventOutcome.COMPLETED:
                            raise ValueError("Travel-arrival must resolve as completed")
                        unit_of_work.repository.mark_journey_arrived(
                            journey.journey_id, scheduled.scheduled_at
                        )
                        for participant in journey.participants:
                            current = unit_of_work.repository.get_actor_position(
                                participant.actor
                            )
                            if (
                                current is None
                                or current.journey_id != journey.journey_id
                            ):
                                raise ValueError(
                                    "Journey participant position changed in transit"
                                )
                            unit_of_work.repository.save_actor_position(
                                ActorPosition(
                                    actor=participant.actor,
                                    location_id=journey.end_location_id,
                                    version=current.version + 1,
                                )
                            )
                        resource_changes.update(
                            self._apply_journey_resource_effects(
                                unit_of_work.repository,
                                run,
                                scheduled,
                                event,
                                journey,
                            )
                        )
                    unit_of_work.repository.append_event(
                        event.model_copy(
                            update={
                                "payload": {
                                    **resolution.payload,
                                    "resource_changes": resource_changes,
                                },
                            }
                        )
                    )
                    unit_of_work.repository.mark_scheduled_event_completed(
                        event.event_id
                    )

                due_transmissions = (
                    unit_of_work.repository.list_due_transmissions(
                        run.target_time,
                        after=clock.current_time,
                    )
                )
                for transmission in due_transmissions:
                    language_id = (
                        transmission.target_language_id
                        or transmission.source_language_id
                    )
                    proficiency = (
                        unit_of_work.repository.get_character_language_proficiency(
                            transmission.recipient_character_id,
                            language_id,
                        )
                        if language_id is not None
                        else None
                    )
                    if not self._language_engine.can_interpret(
                        transmission, proficiency
                    ):
                        unit_of_work.repository.mark_transmission_failed(
                            transmission.transmission_id
                        )
                        continue
                    knowledge = self._interpretation_engine.interpret(transmission)
                    unit_of_work.repository.create_character_knowledge(knowledge)
                    unit_of_work.repository.mark_transmission_interpreted(
                        transmission.transmission_id
                    )

                advanced_clock = clock.advance_to(run.target_time)
                unit_of_work.repository.save_clock(advanced_clock, clock.version)
                processed_ids = tuple(event.event_id for event in materialized)
                completed = unit_of_work.repository.update_run(
                    simulation_run_id,
                    status=SimulationRunStatus.COMPLETED,
                    final_time=run.target_time,
                    processed_event_ids=processed_ids,
                )
                unit_of_work.commit()
                return self._completed_result(completed)
        except Exception as error:
            try:
                self._record_failure(simulation_run_id, error)
            except Exception as recovery_error:
                raise RuntimeError(
                    "Simulation failed and its recovery state could not be persisted"
                ) from recovery_error
            raise

    @staticmethod
    def _apply_resource_effects(
        repository,
        run: SimulationRunRecord,
        scheduled: ScheduledEvent,
        event,
        plan_step,
        outcome: ScheduledEventOutcome,
    ) -> dict[str, str]:
        if plan_step is None:
            return {}
        if outcome == ScheduledEventOutcome.UNCHANGED:
            return {}
        expected = (
            ResourceEffectOutcome.COMPLETED
            if outcome == ScheduledEventOutcome.COMPLETED
            else ResourceEffectOutcome.FAILED
        )
        deltas: dict[str, Decimal] = {}
        for effect in plan_step.resource_effects:
            if effect.on_outcome == expected:
                deltas[effect.resource_code] = (
                    deltas.get(effect.resource_code, Decimal(0)) + effect.delta
                )
        if isinstance(plan_step, OrganizationPlanStep):
            plan = repository.get_organization_plan(plan_step.plan_id)
            if plan is None:
                raise ValueError("Plan step owner could not be resolved")
            owner_kind = ResourceOwnerKind.ORGANIZATION
            owner_id = plan.organization_id
        else:
            plan = repository.get_plan(plan_step.plan_id)
            if plan is None:
                raise ValueError("Plan step owner could not be resolved")
            owner_kind = ResourceOwnerKind.CHARACTER
            owner_id = plan.character_id
        reservations = repository.list_resource_reservations(scheduled.event_id)
        reservation_by_code = {
            reservation.resource_code: reservation for reservation in reservations
        }
        changes: dict[str, str] = {}
        for code, delta in sorted(deltas.items()):
            if delta == 0:
                continue
            balance = repository.get_resource_balance(
                owner_kind,
                owner_id,
                code,
            )
            if balance is None:
                raise ValueError(f"Resource balance {code} was not found")
            resulting = balance.quantity + delta
            transaction = ResourceTransaction(
                transaction_id=uuid5(
                    UUID("2028b0b3-60c8-45c0-89db-4f07a0ab8ca3"),
                    f"{scheduled.event_id}:{code}",
                ),
                owner_kind=owner_kind,
                owner_id=owner_id,
                resource_code=code,
                delta=delta,
                resulting_quantity=resulting,
                scheduled_event_id=scheduled.event_id,
                event_id=event.event_id,
                simulation_run_id=run.simulation_run_id,
                occurred_at=scheduled.scheduled_at,
            )
            repository.apply_resource_transaction(transaction)
            changes[code] = str(delta)
        for code, reservation in reservation_by_code.items():
            if code not in deltas or deltas[code] >= 0:
                repository.release_resource_reservation(
                    reservation.reservation_id,
                    cancelled=True,
                )
        return changes

    @staticmethod
    def _apply_journey_resource_effects(
        repository,
        run: SimulationRunRecord,
        scheduled: ScheduledEvent,
        event,
        journey,
    ) -> dict[str, str]:
        owner = journey.resource_owner
        if owner is None:
            return {}
        totals: dict[str, Decimal] = {}
        for charge in (*journey.costs, *journey.resource_consumption):
            totals[charge.resource_code] = (
                totals.get(charge.resource_code, Decimal(0)) - charge.quantity
            )
        changes: dict[str, str] = {}
        owner_kind = ResourceOwnerKind(owner.actor_type.value)
        for code, delta in sorted(totals.items()):
            balance = repository.get_resource_balance(
                owner_kind, owner.actor_id, code
            )
            if balance is None:
                raise ValueError(f"Resource balance {code} was not found")
            resulting = balance.quantity + delta
            repository.apply_resource_transaction(
                ResourceTransaction(
                    transaction_id=uuid5(
                        UUID("2028b0b3-60c8-45c0-89db-4f07a0ab8ca3"),
                        f"{scheduled.event_id}:journey:{code}",
                    ),
                    owner_kind=owner_kind,
                    owner_id=owner.actor_id,
                    resource_code=code,
                    delta=delta,
                    resulting_quantity=resulting,
                    scheduled_event_id=scheduled.event_id,
                    event_id=event.event_id,
                    simulation_run_id=run.simulation_run_id,
                    occurred_at=scheduled.scheduled_at,
                )
            )
            changes[code] = str(delta)
        return changes

    def _record_failure(self, simulation_run_id: UUID, error: Exception) -> None:
        with self._unit_of_work_factory() as unit_of_work:
            run = unit_of_work.repository.get_run(simulation_run_id)
            if run is not None and run.status != SimulationRunStatus.COMPLETED:
                unit_of_work.repository.update_run(
                    simulation_run_id,
                    status=SimulationRunStatus.FAILED,
                    error=f"{type(error).__name__}: {error}",
                )
                unit_of_work.commit()

    def _resolve_normative_event(self, event: ScheduledEvent, repository):
        authority = AuthorityContext.model_validate(event.payload.get("authority"))
        membership = repository.get_organization_membership(
            authority.organization_id, authority.actor_id
        )
        grants = repository.list_organization_authority_grants(
            authority.organization_id, authority.actor_id
        )
        position = repository.get_actor_position(
            ActorReference(actor_type=ActorType.CHARACTER, actor_id=authority.actor_id)
        )
        validate_institutional_authority(authority, membership, grants, position)

        if event.event_type == "legal-proceeding-transition":
            case = repository.get_legal_case(UUID(event.payload["case_id"]))
            proceeding = repository.get_legal_proceeding(
                UUID(event.payload["proceeding_id"])
            )
            if case is None or proceeding is None:
                raise ValueError("Legal event references an unknown case or proceeding")
            system = repository.get_normative_system(case.system_id)
            if system is None:
                raise ValueError("Legal event references an unknown normative system")
            system = self._with_jurisdiction_descendants(system, repository)
            return self._normative_resolver.resolve_legal_proceeding(
                event, system, case, proceeding
            )
        if event.event_type == "investigation-completion":
            investigation = repository.get_investigation(
                UUID(event.payload["investigation_id"])
            )
            if investigation is None:
                raise ValueError("Investigation event references an unknown investigation")
            case = repository.get_legal_case(investigation.case_id)
            if case is None:
                raise ValueError("Investigation event references an unknown case")
            system = repository.get_normative_system(case.system_id)
            if system is None:
                raise ValueError("Investigation event references an unknown normative system")
            system = self._with_jurisdiction_descendants(system, repository)
            return self._normative_resolver.resolve_investigation(
                event, system, case, investigation
            )
        if event.event_type == "treaty-change":
            treaty = repository.get_treaty(UUID(event.payload["treaty_id"]))
            if treaty is None:
                raise ValueError("Treaty event references an unknown treaty")
            return self._normative_resolver.resolve_treaty(event, treaty)
        if event.event_type == "strategic-escalation":
            conflict = repository.get_strategic_conflict(
                UUID(event.payload["conflict_id"])
            )
            if conflict is None:
                raise ValueError("Strategic event references an unknown conflict")
            return self._normative_resolver.resolve_strategic_escalation(event, conflict)
        if event.event_type == "security-resolution":
            threat = repository.get_security_threat(UUID(event.payload["threat_id"]))
            operation_id = event.payload.get("operation_id")
            incident_id = event.payload.get("incident_id")
            operation = (
                repository.get_intelligence_operation(UUID(operation_id))
                if isinstance(operation_id, str)
                else None
            )
            incident = (
                repository.get_security_incident(UUID(incident_id))
                if isinstance(incident_id, str)
                else None
            )
            if threat is None:
                raise ValueError("Security event references an unknown threat")
            if operation_id is not None and operation is None:
                raise ValueError("Security event references an unknown operation")
            if incident_id is not None and incident is None:
                raise ValueError("Security event references an unknown incident")
            return self._normative_resolver.resolve_security(
                event, threat, operation, incident
            )
        raise ValueError("Unsupported normative event")

    @staticmethod
    def _with_jurisdiction_descendants(system, repository):
        if not system.jurisdiction.include_descendants:
            return system
        locations = repository.list_locations(system.world_id)
        accepted = set(system.jurisdiction.location_ids)
        changed = True
        while changed:
            changed = False
            for location in locations:
                if (
                    location.location_id not in accepted
                    and location.parent_location_id in accepted
                ):
                    accepted.add(location.location_id)
                    changed = True
        return system.model_copy(
            update={
                "jurisdiction": system.jurisdiction.model_copy(
                    update={"location_ids": tuple(accepted)}
                )
            }
        )

    def _new_run(
        self,
        *,
        simulation_run_id: UUID,
        operation: str,
        world_id: UUID,
        timeline_id: UUID,
        initial_time: datetime,
        target_time: datetime,
    ) -> SimulationRunRecord:
        now = self._clock()
        return SimulationRunRecord(
            simulation_run_id=simulation_run_id,
            operation=operation,
            world_id=world_id,
            timeline_id=timeline_id,
            status=SimulationRunStatus.PREPARED,
            initial_time=initial_time,
            target_time=target_time,
            created_at=now,
            updated_at=now,
        )

    @staticmethod
    def _validate_target_event(
        command: AdvanceUntilEventCommand,
        initial_time: datetime,
        event: ScheduledEvent,
    ) -> None:
        if event.world_id != command.world_id or event.timeline_id != command.timeline_id:
            raise TimelineMismatchError(
                "Scheduled target event belongs to another world or timeline"
            )
        if event.scheduled_at <= initial_time:
            raise InvalidTemporalAdvanceError(
                "AdvanceUntil target must be later than the current world time"
            )

    @staticmethod
    def _replay_or_raise(
        run: SimulationRunRecord,
        world_id: UUID,
        timeline_id: UUID,
    ) -> TemporalAdvanceResult:
        if run.world_id != world_id or run.timeline_id != timeline_id:
            raise TimelineMismatchError(
                "Simulation run belongs to another world or timeline"
            )
        if run.status == SimulationRunStatus.COMPLETED:
            result = TemporalAdvanceService._completed_result(run)
            return result.model_copy(update={"idempotent_replay": True})
        if run.status in {
            SimulationRunStatus.PREPARED,
            SimulationRunStatus.RUNNING,
        }:
            raise SimulationRunInProgressError(
                f"Simulation run {run.simulation_run_id} is {run.status.value}"
            )
        raise DuplicateSimulationRunError(
            f"Simulation run {run.simulation_run_id} previously failed"
        )

    @staticmethod
    def _validate_prepared_time_run(
        run: SimulationRunRecord,
        command: AdvanceTimeCommand,
    ) -> None:
        if (
            run.world_id != command.world_id
            or run.timeline_id != command.timeline_id
            or run.operation != "advance-time"
            or run.target_time != run.initial_time + command.duration
        ):
            raise DuplicateSimulationRunError(
                "Simulation run ID is already associated with a different operation"
            )

    @staticmethod
    def _completed_result(run: SimulationRunRecord) -> TemporalAdvanceResult:
        if run.final_time is None:
            raise InvalidTemporalAdvanceError("Completed run has no final time")
        return TemporalAdvanceResult(
            simulation_run_id=run.simulation_run_id,
            initial_time=run.initial_time,
            final_time=run.final_time,
            processed_event_ids=run.processed_event_ids,
        )
