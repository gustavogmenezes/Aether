from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import UUID, uuid4

from sqlalchemy import func, select

from aether.application import KnowledgeService, TemporalAdvanceService
from aether.contracts import (
    AdvanceTimeCommand,
    CommunicationMedium,
    EpistemicStatus,
    InformationNature,
    InformationTransmission,
    PerceptionEvidence,
)
from aether.domain import WorldClockState
from aether.infrastructure import Database, SqlAlchemySimulationUnitOfWork
from aether.infrastructure.models import (
    CharacterKnowledgeModel,
    InformationTransmissionModel,
)


def setup_database(tmp_path: Path) -> tuple[Database, UUID, UUID, datetime]:
    database = Database.from_path(tmp_path / "knowledge.db")
    database.create_schema()
    world_id = uuid4()
    timeline_id = uuid4()
    initial = datetime(2026, 1, 1, 12, tzinfo=UTC)
    with SqlAlchemySimulationUnitOfWork(database.session_factory) as uow:
        uow.repository.create_clock(
            WorldClockState(world_id, timeline_id, initial, version=0)
        )
    return database, world_id, timeline_id, initial


def test_transmission_does_not_create_knowledge_before_arrival(
    tmp_path: Path,
) -> None:
    database, world_id, timeline_id, initial = setup_database(tmp_path)
    recipient_id = uuid4()
    uow_factory = lambda: SqlAlchemySimulationUnitOfWork(database.session_factory)
    knowledge = KnowledgeService(uow_factory)
    knowledge.send(
        InformationTransmission(
            transmission_id=uuid4(),
            source_event_id=uuid4(),
            sender_character_id=uuid4(),
            recipient_character_id=recipient_id,
            fact_key="market-fire",
            statement="The eastern market burned.",
            medium=CommunicationMedium.PHYSICAL,
            nature=InformationNature.FACT,
            sent_at=initial,
            arrival_at=initial + timedelta(minutes=10),
            perceived_reliability=0.9,
        )
    )

    TemporalAdvanceService(uow_factory).advance_time(
        AdvanceTimeCommand(
            simulation_run_id=uuid4(),
            world_id=world_id,
            timeline_id=timeline_id,
            duration=timedelta(minutes=5),
        )
    )
    assert knowledge.character_context(recipient_id, as_of=initial + timedelta(minutes=5)) == ()

    TemporalAdvanceService(uow_factory).advance_time(
        AdvanceTimeCommand(
            simulation_run_id=uuid4(),
            world_id=world_id,
            timeline_id=timeline_id,
            duration=timedelta(minutes=5),
        )
    )

    context = knowledge.character_context(
        recipient_id,
        as_of=initial + timedelta(minutes=10),
    )
    assert context == (
        "market-fire:The eastern market burned.[known;confidence=0.90]",
    )
    with database.session_factory() as session:
        transmission = session.scalar(select(InformationTransmissionModel))
        assert transmission is not None
        assert transmission.status == "interpreted"
    database.dispose()


def test_perception_filter_preserves_character_isolation(
    tmp_path: Path,
) -> None:
    database, _, _, initial = setup_database(tmp_path)
    observer_id = uuid4()
    other_character_id = uuid4()
    knowledge = KnowledgeService(
        lambda: SqlAlchemySimulationUnitOfWork(database.session_factory)
    )

    assert (
        knowledge.perceive(
            PerceptionEvidence(
                event_id=uuid4(),
                observer_character_id=observer_id,
                fact_key="bell-ringing",
                statement="The watch bell rang three times.",
                observed_at=initial,
                base_confidence=1,
                perceptible=True,
            )
        )
        is not None
    )

    assert knowledge.character_context(observer_id, as_of=initial)
    assert knowledge.character_context(other_character_id, as_of=initial) == ()
    with database.session_factory() as session:
        stored = session.scalar(select(CharacterKnowledgeModel))
        assert stored is not None
        assert stored.epistemic_status == EpistemicStatus.KNOWN.value
        assert session.scalar(select(func.count(CharacterKnowledgeModel.knowledge_id))) == 1
    database.dispose()


def test_action_narrator_receives_only_protagonist_knowledge(
    tmp_path: Path,
) -> None:
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
    )

    database, world_id, timeline_id, initial = setup_database(tmp_path)
    protagonist_id = uuid4()
    other_id = uuid4()
    uow_factory = lambda: SqlAlchemySimulationUnitOfWork(database.session_factory)
    knowledge = KnowledgeService(uow_factory)
    knowledge.perceive(
        PerceptionEvidence(
            event_id=uuid4(),
            observer_character_id=protagonist_id,
            fact_key="seen-door",
            statement="The eastern door is open.",
            observed_at=initial,
            base_confidence=1,
            perceptible=True,
        )
    )
    knowledge.perceive(
        PerceptionEvidence(
            event_id=uuid4(),
            observer_character_id=other_id,
            fact_key="hidden-door",
            statement="The western vault is open.",
            observed_at=initial,
            base_confidence=1,
            perceptible=True,
        )
    )

    class CapturingNarrator(TemplateNarrator):
        context: NarrativeContext | None = None

        def narrate(self, context: NarrativeContext) -> NarrativeDraft:
            self.context = context
            return super().narrate(context)

    narrator = CapturingNarrator()
    action_service = ActionExecutionService(
        uow_factory,
        TemporalAdvanceService(uow_factory),
        DeterministicGameMaster(),
        DeterministicActionValidator(),
        narrator,
        DirectPresentationDelivery(),
    )
    action_service.execute(
        PlayerInput(
            input_id=uuid4(),
            simulation_run_id=uuid4(),
            world_id=world_id,
            timeline_id=timeline_id,
            protagonist_character_id=protagonist_id,
            mode=ExperienceMode.PLAYER_CHARACTER,
            text="wait for 1 second",
        )
    )

    assert narrator.context is not None
    serialized = narrator.context.model_dump_json()
    assert "seen-door" in serialized
    assert "hidden-door" not in serialized
    assert "western vault" not in serialized
    database.dispose()
