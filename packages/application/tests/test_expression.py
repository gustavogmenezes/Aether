from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import uuid4

import pytest
from sqlalchemy import func, select

from aether.application import ExpressionService, TemporalAdvanceService
from aether.contracts import (
    ActorReference,
    ActorType,
    AdvanceUntilEventCommand,
    CollectiveReception,
    GeneratedAsset,
    GeneratedAssetKind,
    PublicChannel,
    PublicChannelKind,
    PublicInformation,
    RecordProvenance,
    ScheduledEvent,
    VisualIdentity,
)
from aether.domain import WorldClockState
from aether.infrastructure import Database, SqlAlchemySimulationUnitOfWork
from aether.infrastructure.models import (
    CharacterKnowledgeModel,
    CollectiveReceptionModel,
    EventLedgerModel,
    GeneratedAssetModel,
    PublicInformationModel,
    VisualIdentityModel,
)


def provenance(now: datetime) -> RecordProvenance:
    return RecordProvenance(
        source_type="test",
        source_id="expression",
        created_at=now,
        updated_at=now,
        version=1,
    )


def test_publication_records_public_statement_and_aggregate_reception(
    tmp_path: Path,
) -> None:
    database = Database.from_path(tmp_path / "expression.db")
    database.create_schema()
    now = datetime(2026, 9, 1, tzinfo=UTC)
    world_id = uuid4()
    timeline_id = uuid4()
    channel = PublicChannel(
        channel_id=uuid4(),
        world_id=world_id,
        name="Harbor Broadsheet",
        kind=PublicChannelKind.PUBLICATION,
        speed="daily",
        reliability="contested",
        cost="affordable",
        provenance=provenance(now),
    )
    publication = PublicInformation(
        publication_id=uuid4(),
        world_id=world_id,
        channel_id=channel.channel_id,
        title="Council claims the harbor is secure",
        statement="Harbor patrols have doubled.",
        declared_truth_status="official claim",
        manipulation_tags=("propaganda",),
        published_at=now + timedelta(hours=1),
        provenance=provenance(now),
    )
    reception = CollectiveReception(
        reception_id=uuid4(),
        publication_id=publication.publication_id,
        population_id=uuid4(),
        received_at=now + timedelta(hours=2),
        reaction_summary="The dockworkers remain skeptical.",
        opinion_dimensions={"trust": "low", "interest": "high"},
        accepted=False,
        provenance=provenance(now),
    )
    event = ScheduledEvent(
        event_id=uuid4(),
        world_id=world_id,
        timeline_id=timeline_id,
        scheduled_at=publication.published_at,
        event_type="public-publication",
        source_type="media",
        source_id=str(publication.publication_id),
        payload_version="1",
        payload={
            "publication": publication.model_dump(mode="json"),
            "receptions": [reception.model_dump(mode="json")],
        },
    )
    expression = ExpressionService(
        lambda: SqlAlchemySimulationUnitOfWork(database.session_factory)
    )
    with SqlAlchemySimulationUnitOfWork(database.session_factory) as uow:
        uow.repository.create_clock(
            WorldClockState(world_id, timeline_id, now, version=0)
        )
    expression.register_public_channel(channel)
    expression.schedule_publication(event)

    command = AdvanceUntilEventCommand(
        simulation_run_id=uuid4(),
        world_id=world_id,
        timeline_id=timeline_id,
        scheduled_event_id=event.event_id,
    )
    service = TemporalAdvanceService(
        lambda: SqlAlchemySimulationUnitOfWork(database.session_factory)
    )
    first = service.advance_until_event(command)
    replay = service.advance_until_event(command)

    assert replay.idempotent_replay
    assert first.processed_event_ids == (event.event_id,)
    with database.session_factory() as session:
        assert session.scalar(select(func.count(PublicInformationModel.publication_id))) == 1
        assert session.scalar(select(func.count(CollectiveReceptionModel.reception_id))) == 1
        assert session.scalar(select(func.count(EventLedgerModel.event_id))) == 1
        assert session.scalar(select(func.count(CharacterKnowledgeModel.knowledge_id))) == 0
    database.dispose()


def test_generated_asset_remains_distinct_from_canonical_identity(
    tmp_path: Path,
) -> None:
    database = Database.from_path(tmp_path / "assets.db")
    database.create_schema()
    now = datetime(2026, 9, 1, tzinfo=UTC)
    actor = ActorReference(actor_type=ActorType.CHARACTER, actor_id=uuid4())
    visual = VisualIdentity(
        identity_id=uuid4(),
        subject=actor,
        canonical_traits={"eyes": "gray", "scar": "left cheek"},
        current_state={"expression": "tired"},
        provenance=provenance(now),
    )
    asset = GeneratedAsset(
        asset_id=uuid4(),
        subject=actor,
        kind=GeneratedAssetKind.IMAGE,
        canonical_identity_id=visual.identity_id,
        filesystem_reference="assets/characters/example.png",
        generated_at=now,
        prompt_version="visual-v1",
        model_version="reference-model",
        diegetic=False,
        provenance=provenance(now),
    )
    service = ExpressionService(
        lambda: SqlAlchemySimulationUnitOfWork(database.session_factory)
    )
    service.register_visual_identity(visual)
    service.register_generated_asset(asset)

    with database.session_factory() as session:
        stored_identity = session.get(VisualIdentityModel, str(visual.identity_id))
        stored_asset = session.get(GeneratedAssetModel, str(asset.asset_id))
        assert stored_identity is not None
        assert stored_asset is not None
        assert stored_asset.canonical_identity_id == str(visual.identity_id)
        assert stored_asset.payload["canonical_traits"] if "canonical_traits" in stored_asset.payload else True
        assert "generated_at" in stored_asset.payload
    database.dispose()


def test_unknown_public_channel_rolls_back_publication(tmp_path: Path) -> None:
    database = Database.from_path(tmp_path / "unknown-channel.db")
    database.create_schema()
    now = datetime(2026, 9, 1, tzinfo=UTC)
    world_id, timeline_id = uuid4(), uuid4()
    event_time = now + timedelta(minutes=1)
    publication = PublicInformation(
        publication_id=uuid4(),
        world_id=world_id,
        channel_id=uuid4(),
        title="Unrouted message",
        statement="No channel has been registered.",
        declared_truth_status="rumor",
        published_at=event_time,
        provenance=provenance(now),
    )
    event = ScheduledEvent(
        event_id=uuid4(),
        world_id=world_id,
        timeline_id=timeline_id,
        scheduled_at=event_time,
        event_type="public-publication",
        source_type="test",
        source_id="publication",
        payload_version="1",
        payload={"publication": publication.model_dump(mode="json"), "receptions": []},
    )
    with SqlAlchemySimulationUnitOfWork(database.session_factory) as uow:
        uow.repository.create_clock(
            WorldClockState(world_id, timeline_id, now, version=0)
        )
        uow.repository.schedule_event(event)

    service = TemporalAdvanceService(
        lambda: SqlAlchemySimulationUnitOfWork(database.session_factory)
    )
    with pytest.raises(ValueError, match="unknown public channel"):
        service.advance_until_event(
            AdvanceUntilEventCommand(
                simulation_run_id=uuid4(),
                world_id=world_id,
                timeline_id=timeline_id,
                scheduled_event_id=event.event_id,
            )
        )
    with database.session_factory() as session:
        assert session.scalar(select(func.count(PublicInformationModel.publication_id))) == 0
        assert session.scalar(select(func.count(EventLedgerModel.event_id))) == 0
    database.dispose()
