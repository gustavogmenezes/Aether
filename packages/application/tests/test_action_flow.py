from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import UUID, uuid4

import pytest
from sqlalchemy import func, select

from aether.application import (
    ActionExecutionService,
    DeterministicActionValidator,
    DeterministicGameMaster,
    DirectPresentationDelivery,
    TemplateNarrator,
    TemporalAdvanceService,
)
from aether.contracts import (
    ExperienceMode,
    NarrativeContext,
    NarrativeDraft,
    PlayerInput,
    PresentationStatus,
    ScheduledEvent,
)
from aether.domain import ActionValidationError, WorldClockState
from aether.infrastructure import Database, SqlAlchemySimulationUnitOfWork
from aether.infrastructure.models import (
    AgentProposalModel,
    EventLedgerModel,
    LlmInvocationModel,
    NarrativePresentationModel,
    NarrativeStateModel,
    PlayerKnowledgeModel,
)


def service(
    database: Database,
    *,
    narrator: object | None = None,
    delivery: object | None = None,
) -> ActionExecutionService:
    uow_factory = lambda: SqlAlchemySimulationUnitOfWork(database.session_factory)
    temporal = TemporalAdvanceService(uow_factory)
    return ActionExecutionService(
        uow_factory,
        temporal,
        DeterministicGameMaster(),
        DeterministicActionValidator(),
        narrator or TemplateNarrator(),
        delivery or DirectPresentationDelivery(),
    )


def setup_world(
    tmp_path: Path,
) -> tuple[Database, UUID, UUID, UUID, datetime]:
    database = Database.from_path(tmp_path / "action-flow.db")
    database.create_schema()
    world_id = uuid4()
    timeline_id = uuid4()
    protagonist_id = uuid4()
    initial_time = datetime(2026, 1, 1, 12, tzinfo=UTC)
    with SqlAlchemySimulationUnitOfWork(database.session_factory) as uow:
        uow.repository.create_clock(
            WorldClockState(world_id, timeline_id, initial_time, version=0)
        )
    return database, world_id, timeline_id, protagonist_id, initial_time


def player_input(
    world_id: UUID,
    timeline_id: UUID,
    protagonist_id: UUID,
    *,
    text: str = "wait for 5 seconds",
    run_id: UUID | None = None,
) -> PlayerInput:
    return PlayerInput(
        input_id=uuid4(),
        simulation_run_id=run_id or uuid4(),
        world_id=world_id,
        timeline_id=timeline_id,
        protagonist_character_id=protagonist_id,
        mode=ExperienceMode.PLAYER_CHARACTER,
        text=text,
    )


def test_action_advances_simulates_confirms_and_extracts_player_knowledge(
    tmp_path: Path,
) -> None:
    database, world_id, timeline_id, protagonist_id, initial_time = setup_world(
        tmp_path
    )
    action = player_input(world_id, timeline_id, protagonist_id)

    result = service(database).execute(action)

    assert "5 seconds" in result.content
    assert result.simulation_run_id == action.simulation_run_id
    with database.session_factory() as session:
        clock = WorldClockState(world_id, timeline_id, initial_time, 0)
        assert session.scalar(select(func.count(EventLedgerModel.event_id))) == 0
        assert (
            session.scalar(select(func.count(LlmInvocationModel.invocation_id)))
            == 1
        )
        assert session.scalar(select(func.count(AgentProposalModel.proposal_id))) == 1
        presentation = session.scalar(select(NarrativePresentationModel))
        assert presentation is not None
        assert presentation.status == PresentationStatus.CONFIRMED.value
        assert (
            session.scalar(select(func.count(PlayerKnowledgeModel.knowledge_id)))
            == 3
        )
        assert session.scalar(select(func.count(NarrativeStateModel.state_id))) == 1
    database.dispose()


def test_action_replay_does_not_advance_time_or_duplicate_presentation(
    tmp_path: Path,
) -> None:
    database, world_id, timeline_id, protagonist_id, initial_time = setup_world(
        tmp_path
    )
    action = player_input(world_id, timeline_id, protagonist_id)
    engine = service(database)

    first = engine.execute(action)
    replay = engine.execute(action)

    assert replay.idempotent_replay
    assert replay.presentation_id == first.presentation_id
    with database.session_factory() as session:
        assert (
            session.scalar(select(func.count(NarrativePresentationModel.presentation_id)))
            == 1
        )
        assert session.scalar(select(func.count(PlayerKnowledgeModel.knowledge_id))) == 3
    with SqlAlchemySimulationUnitOfWork(database.session_factory) as uow:
        clock = uow.repository.get_clock(world_id, timeline_id)
        assert clock is not None
        assert clock.current_time == initial_time + timedelta(seconds=5)
    database.dispose()


def test_off_screen_events_are_not_sent_to_narrator(
    tmp_path: Path,
) -> None:
    database, world_id, timeline_id, protagonist_id, initial_time = setup_world(
        tmp_path
    )
    hidden_event_id = uuid4()
    with SqlAlchemySimulationUnitOfWork(database.session_factory) as uow:
        uow.repository.schedule_event(
            ScheduledEvent(
                event_id=hidden_event_id,
                world_id=world_id,
                timeline_id=timeline_id,
                scheduled_at=initial_time + timedelta(seconds=1),
                event_type="secret-patrol-movement",
                source_type="test",
                source_id="patrol",
                payload_version="1",
                payload={"secret": "The patrol moved toward the capital"},
            )
        )

    class CapturingNarrator(TemplateNarrator):
        context: NarrativeContext | None = None

        def narrate(self, context: NarrativeContext) -> NarrativeDraft:
            self.context = context
            return super().narrate(context)

    narrator = CapturingNarrator()
    action = player_input(world_id, timeline_id, protagonist_id)

    service(database, narrator=narrator).execute(action)

    assert narrator.context is not None
    serialized = narrator.context.model_dump_json()
    assert str(hidden_event_id) not in serialized
    assert "capital" not in serialized
    with database.session_factory() as session:
        assert session.scalar(select(func.count(EventLedgerModel.event_id))) == 1
    database.dispose()


def test_delivery_failure_preserves_run_and_resumes_without_re_simulation(
    tmp_path: Path,
) -> None:
    database, world_id, timeline_id, protagonist_id, initial_time = setup_world(
        tmp_path
    )

    class FailOnceDelivery(DirectPresentationDelivery):
        def __init__(self) -> None:
            self.failed = False

        def deliver(self, draft: NarrativeDraft):
            if not self.failed:
                self.failed = True
                raise RuntimeError("delivery interrupted")
            return super().deliver(draft)

    delivery = FailOnceDelivery()
    engine = service(database, delivery=delivery)
    action = player_input(world_id, timeline_id, protagonist_id)

    with pytest.raises(RuntimeError, match="delivery interrupted"):
        engine.execute(action)

    with SqlAlchemySimulationUnitOfWork(database.session_factory) as uow:
        assert uow.repository.get_clock(world_id, timeline_id).current_time == (
            initial_time + timedelta(seconds=5)
        )
        presentation = uow.repository.get_presentation_by_run(
            action.simulation_run_id
        )
        assert presentation is not None
        assert presentation.status == PresentationStatus.GENERATED

    result = engine.execute(action)

    assert result.idempotent_replay is False
    assert result.content
    with database.session_factory() as session:
        assert session.scalar(select(func.count(NarrativePresentationModel.presentation_id))) == 1
        assert session.scalar(select(func.count(PlayerKnowledgeModel.knowledge_id))) == 3
    database.dispose()


def test_narrator_cannot_introduce_unconfirmed_claims(tmp_path: Path) -> None:
    database, world_id, timeline_id, protagonist_id, _ = setup_world(tmp_path)

    class InventingNarrator:
        def narrate(self, context: NarrativeContext) -> NarrativeDraft:
            return NarrativeDraft(
                presentation_id=uuid4(),
                simulation_run_id=context.confirmed_action.simulation_run_id,
                content="A hidden dragon now rules the capital.",
                claims_supported_by_facts=("hidden-dragon-rules-capital",),
            )

    action = player_input(world_id, timeline_id, protagonist_id)
    engine = service(database, narrator=InventingNarrator())

    with pytest.raises(ActionValidationError, match="without a confirmed fact"):
        engine.execute(action)

    with database.session_factory() as session:
        assert session.scalar(select(func.count(NarrativePresentationModel.presentation_id))) == 0
        assert session.scalar(select(func.count(PlayerKnowledgeModel.knowledge_id))) == 0
    database.dispose()
