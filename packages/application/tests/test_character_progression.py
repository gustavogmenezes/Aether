from collections.abc import Iterator
from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID, uuid4

import pytest

from aether.application import CharacterGenesisService, CharacterProgressionService
from aether.contracts import (
    AttributeRating,
    CharacterIdentity,
    CharacterProgressionChange,
    CharacterProgressionEvidence,
    CharacterProgressionProposal,
    CharacterSheet,
    EventEnvelope,
    GenesisProvenance,
    InterruptionClass,
    Merit,
    PersonalityProfile,
    ProgressionChangeKind,
    ProgressionChangeOperation,
    RecordProvenance,
    SkillCategoryKind,
    SkillRating,
    Specialization,
    StorytellingCreationProfile,
)
from aether.domain import CharacterProgressionError, StaleWorldStateError
from aether.infrastructure import Database, SqlAlchemySimulationUnitOfWork
from aether.infrastructure.models import WorldClockModel


@pytest.fixture
def database(tmp_path: Path) -> Iterator[Database]:
    database = Database.from_path(tmp_path / "character-progression.db")
    database.create_schema()
    yield database
    database.dispose()


def profile() -> StorytellingCreationProfile:
    return StorytellingCreationProfile(
        profile_id=uuid4(),
        world_id=uuid4(),
        ruleset_id="world-storytelling",
        attribute_categories=("alpha", "beta", "gamma"),
        skill_categories=("mental", "physical", "social"),
        skill_category_kinds={
            "mental": SkillCategoryKind.MENTAL,
            "physical": SkillCategoryKind.PHYSICAL,
            "social": SkillCategoryKind.SOCIAL,
        },
    )


def sheet(item_profile: StorytellingCreationProfile) -> CharacterSheet:
    now = datetime(2026, 6, 1, tzinfo=UTC)
    return CharacterSheet(
        sheet_id=uuid4(),
        world_id=item_profile.world_id,
        character_id=uuid4(),
        ruleset_id=item_profile.ruleset_id,
        attributes=(
            AttributeRating(category="alpha", name="Strength", rating=5),
            AttributeRating(category="alpha", name="Resolve", rating=2),
            AttributeRating(category="beta", name="Memory", rating=5),
            AttributeRating(category="gamma", name="Presence", rating=4),
        ),
        skills=(
            SkillRating(category="mental", name="Lore", rating=5),
            SkillRating(category="mental", name="Focus", rating=5),
            SkillRating(category="mental", name="Recall", rating=1),
            SkillRating(category="physical", name="Stealth", rating=5),
            SkillRating(category="physical", name="Climb", rating=2),
            SkillRating(category="social", name="Persuasion", rating=4),
            SkillRating(category="social", name="Etiquette", rating=0),
        ),
        specializations=(
            Specialization(skill="Lore", name="History", level=2),
            Specialization(skill="Stealth", name="Footwork", level=1),
        ),
        merits=(Merit(name="Resources", points=7),),
        genesis=GenesisProvenance(
            profile_id=item_profile.profile_id,
            ruleset_id=item_profile.ruleset_id,
            source_type="character-architect",
            source_id="test",
            created_at=now,
        ),
        version=1,
        updated_at=now,
    )


def event(world_id: UUID) -> EventEnvelope:
    now = datetime(2026, 6, 2, tzinfo=UTC)
    return EventEnvelope(
        event_id=uuid4(),
        world_id=world_id,
        timeline_id=uuid4(),
        occurred_at=now,
        recorded_at=now,
        sequence=1,
        event_type="meaningful-experience",
        source_type="test",
        source_id="evidence",
        payload_version="1",
        payload={},
        interruption_class=InterruptionClass.RELEVANT,
    )


def setup(
    database: Database,
) -> tuple[
    StorytellingCreationProfile,
    CharacterSheet,
    EventEnvelope,
    CharacterProgressionService,
]:
    item_profile = profile()
    item_sheet = sheet(item_profile)
    item_event = event(item_profile.world_id)
    with SqlAlchemySimulationUnitOfWork(database.session_factory) as uow:
        uow.session.add(
            WorldClockModel(
                world_id=str(item_event.world_id),
                timeline_id=str(item_event.timeline_id),
                current_time=item_event.occurred_at,
                version=0,
            )
        )
        uow.repository.append_event(item_event)
    factory = lambda: SqlAlchemySimulationUnitOfWork(database.session_factory)
    CharacterGenesisService(factory).create(item_sheet, item_profile)
    return item_profile, item_sheet, item_event, CharacterProgressionService(factory)


def proposal(
    item_sheet: CharacterSheet,
    item_event: EventEnvelope,
    evidence_id: UUID,
    *changes: CharacterProgressionChange,
    version: int = 1,
) -> CharacterProgressionProposal:
    return CharacterProgressionProposal(
        proposal_id=uuid4(),
        request_id=uuid4(),
        world_id=item_sheet.world_id,
        character_id=item_sheet.character_id,
        ruleset_id=item_sheet.ruleset_id,
        expected_sheet_version=version,
        evidence_ids=(evidence_id,),
        changes=changes,
        proposed_by="character-architect",
        rationale="Explicitly supported by persisted event evidence.",
        proposed_at=item_event.recorded_at,
    )


def record_evidence(
    service: CharacterProgressionService,
    item_sheet: CharacterSheet,
    item_event: EventEnvelope,
) -> CharacterProgressionEvidence:
    evidence = CharacterProgressionEvidence(
        evidence_id=uuid4(),
        world_id=item_sheet.world_id,
        character_id=item_sheet.character_id,
        event_ids=(item_event.event_id,),
        summary="The character completed a difficult study.",
        recorded_at=item_event.recorded_at,
    )
    return service.record_evidence(evidence)


def test_arbitrary_proposal_without_persisted_evidence_is_rejected(
    database: Database,
) -> None:
    item_profile, item_sheet, item_event, service = setup(database)
    item = proposal(
        item_sheet,
        item_event,
        uuid4(),
        CharacterProgressionChange(
            kind=ProgressionChangeKind.SKILL,
            target="Lore",
            category="mental",
            operation=ProgressionChangeOperation.INCREASE,
        ),
    )

    with pytest.raises(CharacterProgressionError, match="evidence"):
        service.submit(item, item_profile)


def test_positive_negative_changes_and_idempotent_history(database: Database) -> None:
    item_profile, item_sheet, item_event, service = setup(database)
    evidence = record_evidence(service, item_sheet, item_event)
    item = proposal(
        item_sheet,
        item_event,
        evidence.evidence_id,
        CharacterProgressionChange(
            kind=ProgressionChangeKind.SKILL,
            target="Etiquette",
            category="social",
            operation=ProgressionChangeOperation.INCREASE,
        ),
        CharacterProgressionChange(
            kind=ProgressionChangeKind.SKILL,
            target="Stealth",
            category="physical",
            operation=ProgressionChangeOperation.DECREASE,
        ),
        CharacterProgressionChange(
            kind=ProgressionChangeKind.INJURY,
            target="injured-knee",
            operation=ProgressionChangeOperation.ADD,
            description="An injury established by the event.",
        ),
    )
    service.submit(item, item_profile)
    service.approve(item.proposal_id, item_profile, validated_by="world-rules")

    first = service.apply(item.proposal_id, item_profile)
    second = service.apply(item.proposal_id, item_profile)

    assert first == second
    with pytest.raises(CharacterProgressionError, match="mismatch"):
        service.apply(
            item.proposal_id,
            item_profile.model_copy(update={"ruleset_id": "other"}),
        )
    assert first.sheet_before.skills[-1].rating == 0
    assert first.sheet_after.skills[-1].rating == 1
    assert first.sheet_after.skills[3].rating == 4
    assert first.sheet_after.injuries[0].name == "injured-knee"
    with SqlAlchemySimulationUnitOfWork(database.session_factory) as uow:
        assert uow.repository.get_character_sheet(item_sheet.character_id) == first.sheet_after
        assert len(
            uow.repository.list_progression_applications(item_sheet.character_id)
        ) == 1


def test_stale_version_and_mismatched_ruleset_are_rejected(database: Database) -> None:
    item_profile, item_sheet, item_event, service = setup(database)
    evidence = record_evidence(service, item_sheet, item_event)
    item = proposal(
        item_sheet,
        item_event,
        evidence.evidence_id,
        CharacterProgressionChange(
            kind=ProgressionChangeKind.ATTRIBUTE,
            target="Resolve",
            category="alpha",
            operation=ProgressionChangeOperation.INCREASE,
        ),
        version=9,
    )
    with pytest.raises(StaleWorldStateError):
        service.submit(item, item_profile)

    other = item_profile.model_copy(update={"ruleset_id": "another"})
    valid = proposal(
        item_sheet,
        item_event,
        evidence.evidence_id,
        CharacterProgressionChange(
            kind=ProgressionChangeKind.TRAIT,
            target="adaptable",
            operation=ProgressionChangeOperation.ADD,
        ),
    )
    with pytest.raises(CharacterProgressionError, match="mismatch"):
        service.submit(valid, other)


def test_progression_does_not_rewrite_identity_or_personality(
    database: Database,
) -> None:
    item_profile, item_sheet, item_event, service = setup(database)
    evidence = record_evidence(service, item_sheet, item_event)
    now = datetime(2026, 6, 2, tzinfo=UTC)
    provenance = RecordProvenance(
        source_type="test",
        source_id="identity",
        created_at=now,
        updated_at=now,
        version=1,
    )
    identity = CharacterIdentity(
        identity_id=uuid4(),
        character_id=item_sheet.character_id,
        display_name="Unchanged",
        provenance=provenance,
    )
    personality = PersonalityProfile(
        profile_id=uuid4(),
        character_id=item_sheet.character_id,
        traits=("patient",),
        provenance=provenance,
    )
    with SqlAlchemySimulationUnitOfWork(database.session_factory) as uow:
        uow.repository.create_character_identity(identity)
        uow.repository.create_personality_profile(personality)
    item = proposal(
        item_sheet,
        item_event,
        evidence.evidence_id,
        CharacterProgressionChange(
            kind=ProgressionChangeKind.TRAIT,
            target="observant",
            operation=ProgressionChangeOperation.ADD,
        ),
    )
    service.submit(item, item_profile)
    service.approve(item.proposal_id, item_profile, validated_by="rules")
    service.apply(item.proposal_id, item_profile)

    with SqlAlchemySimulationUnitOfWork(database.session_factory) as uow:
        assert uow.repository.get_character_identity(item_sheet.character_id) == identity
        assert (
            uow.repository.get_personality_profile(item_sheet.character_id)
            == personality
        )
