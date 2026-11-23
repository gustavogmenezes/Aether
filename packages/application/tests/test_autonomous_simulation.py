from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import UUID, uuid4

import pytest
from sqlalchemy import select

from aether.application import TemporalAdvanceService
from aether.contracts import (
    AdvanceTimeCommand,
    AdvanceUntilEventCommand,
    Goal,
    GoalStatus,
    Plan,
    PlanStatus,
    PlanStep,
    PlanStepStatus,
    RecordProvenance,
    ScheduledEvent,
    ScheduledEventOutcome,
    ScheduledEventResolution,
)
from aether.domain import WorldClockState
from aether.engines import DeterministicScheduledEventResolver
from aether.infrastructure import Database, SqlAlchemySimulationUnitOfWork
from aether.infrastructure.models import EventLedgerModel, ScheduledEventModel


def setup_plan_event(
    tmp_path: Path,
) -> tuple[Database, UUID, UUID, UUID, UUID, datetime]:
    database = Database.from_path(tmp_path / "autonomy.db")
    database.create_schema()
    now = datetime(2026, 1, 1, 12, tzinfo=UTC)
    world_id = uuid4()
    timeline_id = uuid4()
    character_id = uuid4()
    provenance = RecordProvenance(
        source_type="test",
        source_id="autonomy",
        created_at=now,
        updated_at=now,
        version=1,
    )
    goal = Goal(
        goal_id=uuid4(),
        character_id=character_id,
        desired_outcome="Protect the signal pyre",
        status=GoalStatus.ACTIVE,
        provenance=provenance,
    )
    plan = Plan(
        plan_id=uuid4(),
        character_id=character_id,
        goal_id=goal.goal_id,
        name="Destroy the enemy beacon",
        status=PlanStatus.ACTIVE,
        provenance=provenance,
    )
    step = PlanStep(
        step_id=uuid4(),
        plan_id=plan.plan_id,
        sequence=0,
        action_intent="Destroy the enemy signal pyre",
        status=PlanStepStatus.SCHEDULED,
        provenance=provenance,
    )
    event = ScheduledEvent(
        event_id=uuid4(),
        world_id=world_id,
        timeline_id=timeline_id,
        scheduled_at=now + timedelta(minutes=10),
        event_type="npc-plan-step",
        source_type="npc-decision",
        source_id=str(uuid4()),
        payload_version="1",
        payload={
            "character_id": str(character_id),
            "plan_step_id": str(step.step_id),
            "decision_proposal_id": str(uuid4()),
        },
    )
    with SqlAlchemySimulationUnitOfWork(database.session_factory) as uow:
        uow.repository.create_clock(
            WorldClockState(world_id, timeline_id, now, version=0)
        )
        uow.repository.create_goal(goal)
        uow.repository.create_plan(plan)
        uow.repository.create_plan_step(step)
        uow.repository.schedule_event(event)
    return database, world_id, timeline_id, step.step_id, event.event_id, now


def test_due_npc_plan_step_produces_off_screen_consequence(
    tmp_path: Path,
) -> None:
    database, world_id, timeline_id, step_id, event_id, now = setup_plan_event(
        tmp_path
    )
    service = TemporalAdvanceService(
        lambda: SqlAlchemySimulationUnitOfWork(database.session_factory)
    )

    result = service.advance_time(
        AdvanceTimeCommand(
            simulation_run_id=uuid4(),
            world_id=world_id,
            timeline_id=timeline_id,
            duration=timedelta(minutes=10),
        )
    )

    assert result.processed_event_ids == (event_id,)
    with SqlAlchemySimulationUnitOfWork(database.session_factory) as uow:
        step = uow.repository.get_plan_step(step_id)
        assert step is not None
        assert step.status == PlanStepStatus.COMPLETED
        scheduled_status = uow.repository.get_scheduled_event_status(event_id)
        assert scheduled_status is not None and scheduled_status.value == "completed"
        ledger = uow.session.scalars(select(EventLedgerModel)).one()
        assert ledger.payload["resolution"] == "completed"
        assert ledger.payload["action_intent"] == "Destroy the enemy signal pyre"
        clock = uow.repository.get_clock(world_id, timeline_id)
        assert clock is not None and clock.current_time == now + timedelta(minutes=10)
    database.dispose()


def test_autonomous_failure_updates_plan_and_ledger_atomically(
    tmp_path: Path,
) -> None:
    database, world_id, timeline_id, step_id, event_id, _ = setup_plan_event(
        tmp_path
    )

    class FailingResolver(DeterministicScheduledEventResolver):
        def resolve(self, event, plan_step):
            assert plan_step is not None
            return ScheduledEventResolution(
                scheduled_event_id=event.event_id,
                outcome=ScheduledEventOutcome.FAILED,
                payload={
                    **event.payload,
                    "resolution": "failed",
                    "action_intent": plan_step.action_intent,
                },
                plan_step_id=plan_step.step_id,
                reason="The objective was no longer reachable",
            )

    service = TemporalAdvanceService(
        lambda: SqlAlchemySimulationUnitOfWork(database.session_factory),
        scheduled_resolver=FailingResolver(),
    )
    service.advance_time(
        AdvanceTimeCommand(
            simulation_run_id=uuid4(),
            world_id=world_id,
            timeline_id=timeline_id,
            duration=timedelta(minutes=10),
        )
    )

    with SqlAlchemySimulationUnitOfWork(database.session_factory) as uow:
        step = uow.repository.get_plan_step(step_id)
        assert step is not None and step.status == PlanStepStatus.FAILED
        model = uow.session.get(ScheduledEventModel, str(event_id))
        assert model is not None and model.status == "completed"
        ledger = uow.session.scalars(select(EventLedgerModel)).one()
        assert ledger.payload["resolution"] == "failed"
    database.dispose()


def test_resolver_error_rolls_back_event_clock_and_plan_state(
    tmp_path: Path,
) -> None:
    database, world_id, timeline_id, step_id, _, now = setup_plan_event(tmp_path)

    class BrokenResolver:
        def resolve(self, event, plan_step):
            raise RuntimeError("resolver interrupted")

    service = TemporalAdvanceService(
        lambda: SqlAlchemySimulationUnitOfWork(database.session_factory),
        scheduled_resolver=BrokenResolver(),
    )

    with pytest.raises(RuntimeError, match="resolver interrupted"):
        service.advance_time(
            AdvanceTimeCommand(
                simulation_run_id=uuid4(),
                world_id=world_id,
                timeline_id=timeline_id,
                duration=timedelta(minutes=10),
            )
        )

    with SqlAlchemySimulationUnitOfWork(database.session_factory) as uow:
        step = uow.repository.get_plan_step(step_id)
        clock = uow.repository.get_clock(world_id, timeline_id)
        assert step is not None and step.status == PlanStepStatus.SCHEDULED
        assert clock is not None and clock.current_time == now
        assert tuple(uow.session.scalars(select(EventLedgerModel)).all()) == ()
    database.dispose()


def test_autonomous_event_is_idempotent_on_run_replay(
    tmp_path: Path,
) -> None:
    database, world_id, timeline_id, step_id, event_id, _ = setup_plan_event(
        tmp_path
    )
    service = TemporalAdvanceService(
        lambda: SqlAlchemySimulationUnitOfWork(database.session_factory)
    )
    command = AdvanceTimeCommand(
        simulation_run_id=uuid4(),
        world_id=world_id,
        timeline_id=timeline_id,
        duration=timedelta(minutes=10),
    )

    first = service.advance_time(command)
    replay = service.advance_time(command)

    assert replay.idempotent_replay
    assert first.processed_event_ids == replay.processed_event_ids == (event_id,)
    with SqlAlchemySimulationUnitOfWork(database.session_factory) as uow:
        assert uow.repository.get_plan_step(step_id).status == PlanStepStatus.COMPLETED
        assert len(uow.session.scalars(select(EventLedgerModel)).all()) == 1
    database.dispose()


def test_advance_until_event_runs_the_targeted_world_consequence(
    tmp_path: Path,
) -> None:
    database, world_id, timeline_id, step_id, event_id, now = setup_plan_event(
        tmp_path
    )
    service = TemporalAdvanceService(
        lambda: SqlAlchemySimulationUnitOfWork(database.session_factory)
    )

    result = service.advance_until_event(
        AdvanceUntilEventCommand(
            simulation_run_id=uuid4(),
            world_id=world_id,
            timeline_id=timeline_id,
            scheduled_event_id=event_id,
        )
    )

    assert result.processed_event_ids == (event_id,)
    assert result.final_time == now + timedelta(minutes=10)
    with SqlAlchemySimulationUnitOfWork(database.session_factory) as uow:
        assert uow.repository.get_plan_step(step_id).status == PlanStepStatus.COMPLETED
    database.dispose()
