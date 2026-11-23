from collections.abc import Iterator
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import pytest

from aether.contracts import (
    AgentProposalRecord,
    LlmInvocationRecord,
    SimulationRunRecord,
    SimulationRunStatus,
)
from aether.domain import StaleWorldStateError, WorldClockState
from aether.infrastructure import Database, SqlAlchemySimulationUnitOfWork


@pytest.fixture
def database(tmp_path: Path) -> Iterator[Database]:
    database = Database.from_path(tmp_path / "repository.db")
    database.create_schema()
    yield database
    database.dispose()


def prepared_run(*, initial_time: datetime) -> SimulationRunRecord:
    return SimulationRunRecord(
        simulation_run_id=uuid4(),
        operation="advance-time",
        world_id=uuid4(),
        timeline_id=uuid4(),
        status=SimulationRunStatus.PREPARED,
        initial_time=initial_time,
        target_time=initial_time,
        created_at=initial_time,
        updated_at=initial_time,
    )


def test_stale_clock_version_is_rejected(database: Database) -> None:
    initial_time = datetime(2026, 1, 1, tzinfo=UTC)
    clock = WorldClockState(uuid4(), uuid4(), initial_time, version=3)
    with SqlAlchemySimulationUnitOfWork(database.session_factory) as uow:
        uow.repository.create_clock(clock)

    with SqlAlchemySimulationUnitOfWork(database.session_factory) as uow:
        with pytest.raises(StaleWorldStateError):
            uow.repository.save_clock(
                clock.advance_to(initial_time),
                expected_version=clock.version + 1,
            )


def test_invocation_and_proposal_are_separately_persisted(
    database: Database,
) -> None:
    now = datetime(2026, 1, 1, tzinfo=UTC)
    run = prepared_run(initial_time=now)
    invocation = LlmInvocationRecord(
        invocation_id=uuid4(),
        simulation_run_id=run.simulation_run_id,
        requesting_agent="Game Master",
        requested_capability="action-interpretation",
        model="test-model",
        model_version="1.0",
        prompt_version="prompt-1",
        context_hash="context-hash",
        inference_parameters={"temperature": 0},
        response_reference="responses/one.json",
        status="completed",
        input_tokens=12,
        output_tokens=7,
        created_at=now,
        completed_at=now,
    )
    proposal = AgentProposalRecord(
        proposal_id=uuid4(),
        simulation_run_id=run.simulation_run_id,
        invocation_id=invocation.invocation_id,
        proposal_type="action",
        payload={"intent": "travel"},
        validation_status="validated",
        application_result={"event_id": str(uuid4())},
        created_at=now,
    )
    with SqlAlchemySimulationUnitOfWork(database.session_factory) as uow:
        uow.repository.create_run(run)
        uow.repository.create_invocation(invocation)
        uow.repository.create_proposal(proposal)

    with SqlAlchemySimulationUnitOfWork(database.session_factory) as uow:
        stored_invocation = uow.repository.get_invocation(invocation.invocation_id)
        stored_proposal = uow.repository.get_proposal(proposal.proposal_id)

    assert stored_invocation == invocation
    assert stored_proposal == proposal
