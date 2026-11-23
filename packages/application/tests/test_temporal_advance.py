from collections.abc import Iterator
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import UUID, uuid4

import pytest
from sqlalchemy import func, select

from aether.application import TemporalAdvanceService
from aether.contracts import (
    AdvanceTimeCommand,
    AdvanceUntilEventCommand,
    ScheduledEvent,
)
from aether.contracts import SimulationRunStatus
from aether.domain import (
    CausalOrderingError,
    ScheduledEventStatus,
    WorldClockState,
)
from aether.engines import EventOrderingEngine
from aether.infrastructure import (
    Database,
    SqlAlchemySimulationUnitOfWork,
)
from aether.infrastructure.models import EventLedgerModel


@pytest.fixture
def database(tmp_path: Path) -> Iterator[Database]:
    database = Database.from_path(tmp_path / "aether-test.db")
    database.create_schema()
    yield database
    database.dispose()


@pytest.fixture
def world(
    database: Database,
) -> tuple[Database, UUID, UUID, datetime]:
    world_id = uuid4()
    timeline_id = uuid4()
    initial_time = datetime(2026, 1, 1, 12, tzinfo=UTC)
    with SqlAlchemySimulationUnitOfWork(database.session_factory) as uow:
        uow.repository.create_clock(
            WorldClockState(
                world_id=world_id,
                timeline_id=timeline_id,
                current_time=initial_time,
                version=0,
            )
        )
    return database, world_id, timeline_id, initial_time


def schedule(
    database: Database,
    world_id: UUID,
    timeline_id: UUID,
    at: datetime,
    *,
    priority: int = 0,
) -> UUID:
    event_id = uuid4()
    with SqlAlchemySimulationUnitOfWork(database.session_factory) as uow:
        uow.repository.schedule_event(
            ScheduledEvent(
                event_id=event_id,
                world_id=world_id,
                timeline_id=timeline_id,
                scheduled_at=at,
                event_type="patrol-arrives",
                source_type="test",
                source_id="patrol",
                priority=priority,
                payload_version="1",
                payload={"strength": 12},
            )
        )
    return event_id


def test_advance_processes_due_events_and_updates_clock_atomically(
    world: tuple[Database, UUID, UUID, datetime],
) -> None:
    database, world_id, timeline_id, initial_time = world
    due_id = schedule(database, world_id, timeline_id, initial_time + timedelta(minutes=5))
    future_id = schedule(
        database,
        world_id,
        timeline_id,
        initial_time + timedelta(minutes=20),
    )
    service = TemporalAdvanceService(
        lambda: SqlAlchemySimulationUnitOfWork(database.session_factory)
    )
    run_id = uuid4()

    result = service.advance_time(
        AdvanceTimeCommand(
            simulation_run_id=run_id,
            world_id=world_id,
            timeline_id=timeline_id,
            duration=timedelta(minutes=10),
        )
    )

    assert result.final_time == initial_time + timedelta(minutes=10)
    assert result.processed_event_ids == (due_id,)
    with SqlAlchemySimulationUnitOfWork(database.session_factory) as uow:
        assert uow.repository.get_clock(world_id, timeline_id).current_time == result.final_time
        assert uow.repository.get_run(run_id).status == SimulationRunStatus.COMPLETED
        assert uow.repository.get_scheduled_event_status(due_id).value == "completed"
        assert uow.repository.get_scheduled_event_status(future_id).value == "pending"
        count = uow.session.scalar(select(func.count(EventLedgerModel.event_id)))
        assert count == 1


def test_completed_run_is_replayed_without_duplicate_effects(
    world: tuple[Database, UUID, UUID, datetime],
) -> None:
    database, world_id, timeline_id, initial_time = world
    schedule(database, world_id, timeline_id, initial_time + timedelta(seconds=1))
    service = TemporalAdvanceService(
        lambda: SqlAlchemySimulationUnitOfWork(database.session_factory)
    )
    command = AdvanceTimeCommand(
        simulation_run_id=uuid4(),
        world_id=world_id,
        timeline_id=timeline_id,
        duration=timedelta(seconds=2),
    )

    first = service.advance_time(command)
    replay = service.advance_time(command)

    assert replay.idempotent_replay
    assert replay.processed_event_ids == first.processed_event_ids
    with database.session_factory() as session:
        assert session.scalar(select(func.count(EventLedgerModel.event_id))) == 1


def test_advance_until_event_processes_all_prior_events_and_stops_at_target(
    world: tuple[Database, UUID, UUID, datetime],
) -> None:
    database, world_id, timeline_id, initial_time = world
    prior_id = schedule(
        database,
        world_id,
        timeline_id,
        initial_time + timedelta(seconds=1),
    )
    target_id = schedule(
        database,
        world_id,
        timeline_id,
        initial_time + timedelta(seconds=5),
        priority=10,
    )
    future_id = schedule(
        database,
        world_id,
        timeline_id,
        initial_time + timedelta(seconds=9),
    )
    service = TemporalAdvanceService(
        lambda: SqlAlchemySimulationUnitOfWork(database.session_factory)
    )

    result = service.advance_until_event(
        AdvanceUntilEventCommand(
            simulation_run_id=uuid4(),
            world_id=world_id,
            timeline_id=timeline_id,
            scheduled_event_id=target_id,
        )
    )

    assert result.final_time == initial_time + timedelta(seconds=5)
    assert set(result.processed_event_ids) == {prior_id, target_id}
    with SqlAlchemySimulationUnitOfWork(database.session_factory) as uow:
        assert uow.repository.get_scheduled_event_status(
            target_id
        ) == ScheduledEventStatus.COMPLETED
        future_status = uow.repository.get_scheduled_event_status(
            future_id
        )
        assert future_status == ScheduledEventStatus.PENDING
        ledger_times = tuple(
            row[0]
            for row in uow.session.execute(
                select(EventLedgerModel.occurred_at).order_by(
                    EventLedgerModel.occurred_at,
                    EventLedgerModel.sequence,
                )
            ).all()
        )
        assert ledger_times == (
            initial_time + timedelta(seconds=1),
            initial_time + timedelta(seconds=5),
        )


def test_failure_rolls_back_clock_ledger_and_schedule_state(
    world: tuple[Database, UUID, UUID, datetime],
) -> None:
    database, world_id, timeline_id, initial_time = world
    schedule(database, world_id, timeline_id, initial_time + timedelta(seconds=1))

    class FailingOrderingEngine(EventOrderingEngine):
        def order(self, events: tuple[ScheduledEvent, ...]) -> tuple[ScheduledEvent, ...]:
            raise CausalOrderingError("Injected ordering failure")

    service = TemporalAdvanceService(
        lambda: SqlAlchemySimulationUnitOfWork(database.session_factory),
        ordering_engine=FailingOrderingEngine(),
    )
    run_id = uuid4()

    with pytest.raises(CausalOrderingError):
        service.advance_time(
            AdvanceTimeCommand(
                simulation_run_id=run_id,
                world_id=world_id,
                timeline_id=timeline_id,
                duration=timedelta(seconds=2),
            )
        )

    with SqlAlchemySimulationUnitOfWork(database.session_factory) as uow:
        assert uow.repository.get_clock(world_id, timeline_id).current_time == initial_time
        assert uow.repository.get_run(run_id).status == SimulationRunStatus.FAILED
        assert uow.session.scalar(select(func.count(EventLedgerModel.event_id))) == 0
