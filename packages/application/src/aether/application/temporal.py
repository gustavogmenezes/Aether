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
)
from aether.domain import (
    DuplicateSimulationRunError,
    InvalidTemporalAdvanceError,
    SimulationRunInProgressError,
    TimelineMismatchError,
    ScheduledEventResolverPort,
)
from aether.domain.ports import SimulationUnitOfWorkFactory
from aether.domain.simulation import ScheduledEventStatus
from aether.engines import (
    DeterministicScheduledEventResolver,
    EventOrderingEngine,
    PerceptionAndInterpretationEngine,
)


class TemporalAdvanceService:
    def __init__(
        self,
        unit_of_work_factory: SimulationUnitOfWorkFactory,
        *,
        ordering_engine: EventOrderingEngine | None = None,
        interpretation_engine: PerceptionAndInterpretationEngine | None = None,
        scheduled_resolver: ScheduledEventResolverPort | None = None,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self._unit_of_work_factory = unit_of_work_factory
        self._ordering_engine = ordering_engine or EventOrderingEngine()
        self._interpretation_engine = (
            interpretation_engine or PerceptionAndInterpretationEngine()
        )
        self._scheduled_resolver = (
            scheduled_resolver or DeterministicScheduledEventResolver()
        )
        self._clock = clock or (lambda: datetime.now(UTC))

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
                    if scheduled.event_type == "npc-plan-step":
                        payload_step_id = scheduled.payload.get("plan_step_id")
                        if not isinstance(payload_step_id, str):
                            raise ValueError(
                                "NPC plan-step event payload has no plan step ID"
                            )
                        plan_step = unit_of_work.repository.get_plan_step(
                            UUID(payload_step_id)
                        )
                        if plan_step is None:
                            raise ValueError(
                                "NPC plan-step event references an unknown plan step"
                            )
                        plan = unit_of_work.repository.get_plan(plan_step.plan_id)
                        payload_character_id = scheduled.payload.get("character_id")
                        if (
                            plan is None
                            or not isinstance(payload_character_id, str)
                            or plan.character_id != UUID(payload_character_id)
                        ):
                            raise ValueError(
                                "NPC plan-step event character does not own the plan"
                            )
                    resolution = self._scheduled_resolver.resolve(
                        scheduled,
                        plan_step,
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
                    if resolution.outcome == ScheduledEventOutcome.COMPLETED:
                        if resolution.plan_step_id is not None:
                            unit_of_work.repository.mark_plan_step_completed(
                                resolution.plan_step_id
                            )
                    elif resolution.outcome == ScheduledEventOutcome.FAILED:
                        if resolution.plan_step_id is None:
                            raise ValueError(
                                "Failed plan-step resolution requires a plan step ID"
                            )
                        unit_of_work.repository.mark_plan_step_failed(
                            resolution.plan_step_id,
                            resolution.reason or "Scheduled event resolution failed",
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
        plan = repository.get_plan(plan_step.plan_id)
        if plan is None:
            raise ValueError("Plan step owner could not be resolved")
        reservations = repository.list_resource_reservations(scheduled.event_id)
        reservation_by_code = {
            reservation.resource_code: reservation for reservation in reservations
        }
        changes: dict[str, str] = {}
        for code, delta in sorted(deltas.items()):
            if delta == 0:
                continue
            balance = repository.get_resource_balance(
                ResourceOwnerKind.CHARACTER,
                plan.character_id,
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
                owner_kind=ResourceOwnerKind.CHARACTER,
                owner_id=plan.character_id,
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
