from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import uuid4

from sqlalchemy import select

from aether.application import CulturalSystemsService
from aether.contracts import (
    CulturalAffiliationDisposition,
    CulturalAffiliationTargetType,
    CulturalAffiliationVisibility,
    CulturalChangeCause,
    CulturalChangeRecord,
    CultureDefinition,
    EventEnvelope,
    IndividualCulturalAffiliation,
    OrganizationIdentity,
    RecordProvenance,
    SocialGroup,
)
from aether.infrastructure import Database, SqlAlchemySimulationUnitOfWork
from aether.infrastructure.models import (
    CulturalChangeRecordModel,
    OrganizationIdentityModel,
    SocialGroupModel,
)


def provenance(now: datetime) -> RecordProvenance:
    return RecordProvenance(
        source_type="test",
        source_id="collective-identity",
        created_at=now,
        updated_at=now,
        version=1,
    )


def culture_service(database: Database) -> CulturalSystemsService:
    return CulturalSystemsService(
        lambda: SqlAlchemySimulationUnitOfWork(database.session_factory)
    )


def database_at(tmp_path: Path) -> tuple[Database, datetime]:
    database = Database.from_path(tmp_path / "culture.db")
    database.create_schema()
    return database, datetime(2026, 7, 1, tzinfo=UTC)


def test_culture_and_social_group_are_distinct_from_organization(
    tmp_path: Path,
) -> None:
    database, now = database_at(tmp_path)
    service = culture_service(database)
    world_id = uuid4()
    culture = CultureDefinition(
        culture_id=uuid4(),
        world_id=world_id,
        name="Tidefolk",
        values=("reciprocity",),
        customs=("harbor welcome",),
        traditions=("night lanterns",),
        norms=("shared anchorage",),
        belief_references=("salt remembers",),
        religion_tradition_ids=(uuid4(),),
        language_ids=(uuid4(),),
        art_work_ids=(uuid4(),),
        symbol_ids=(uuid4(),),
        history_event_ids=(uuid4(),),
        provenance=provenance(now),
    )
    group = SocialGroup(
        group_id=uuid4(),
        world_id=world_id,
        name="Harbor Artisans",
        semantic_category="profession",
        culture_ids=(culture.culture_id,),
        provenance=provenance(now),
    )
    service.register_culture(culture)
    service.register_social_group(group)

    assert CultureDefinition.model_fields.keys() != OrganizationIdentity.model_fields.keys()
    with database.session_factory() as session:
        assert session.scalar(select(SocialGroupModel)) is not None
        assert session.scalars(select(OrganizationIdentityModel)).all() == []


def test_heterogeneous_simultaneous_affiliations_keep_disposition_and_confidence(
    tmp_path: Path,
) -> None:
    database, now = database_at(tmp_path)
    service = culture_service(database)
    assert {disposition.value for disposition in CulturalAffiliationDisposition} == {
        "adheres",
        "questions",
        "rejects",
        "assimilates",
        "hybridizes",
        "transforms",
    }
    world_id, character_id = uuid4(), uuid4()
    cultures = tuple(
        CultureDefinition(
            culture_id=uuid4(),
            world_id=world_id,
            name=name,
            provenance=provenance(now),
        )
        for name in ("River", "Mountain")
    )
    group = SocialGroup(
        group_id=uuid4(),
        world_id=world_id,
        name="Copper Guild",
        semantic_category="community",
        provenance=provenance(now),
    )
    for culture in cultures:
        service.register_culture(culture)
    service.register_social_group(group)
    affiliations = (
        IndividualCulturalAffiliation(
            affiliation_id=uuid4(),
            character_id=character_id,
            target_type=CulturalAffiliationTargetType.CULTURE,
            target_id=cultures[0].culture_id,
            disposition=CulturalAffiliationDisposition.ADHERES,
            visibility=CulturalAffiliationVisibility.PUBLIC,
            confidence="0.9",
            effective_from=now,
            provenance=provenance(now),
        ),
        IndividualCulturalAffiliation(
            affiliation_id=uuid4(),
            character_id=character_id,
            target_type=CulturalAffiliationTargetType.CULTURE,
            target_id=cultures[1].culture_id,
            disposition=CulturalAffiliationDisposition.HYBRIDIZES,
            visibility=CulturalAffiliationVisibility.PUBLIC,
            confidence="0.6",
            effective_from=now,
            provenance=provenance(now),
        ),
        IndividualCulturalAffiliation(
            affiliation_id=uuid4(),
            character_id=character_id,
            target_type=CulturalAffiliationTargetType.SOCIAL_GROUP,
            target_id=group.group_id,
            disposition=CulturalAffiliationDisposition.QUESTIONS,
            visibility=CulturalAffiliationVisibility.PUBLIC,
            confidence="0.3",
            effective_from=now,
            provenance=provenance(now),
        ),
    )
    for affiliation in affiliations:
        service.record_individual_cultural_affiliation(affiliation)

    context = service.character_cultural_context(
        character_id, uuid4(), now
    )

    assert {item.disposition for item in context.affiliations} == {
        CulturalAffiliationDisposition.ADHERES,
        CulturalAffiliationDisposition.HYBRIDIZES,
        CulturalAffiliationDisposition.QUESTIONS,
    }
    assert len(context.affiliations) == 3
    assert len(context.cultures) == 2
    assert context.social_groups == (group,)


def test_character_cultural_context_filters_visibility_and_time(
    tmp_path: Path,
) -> None:
    database, now = database_at(tmp_path)
    service = culture_service(database)
    character_id, observer_id, trusted_id = uuid4(), uuid4(), uuid4()
    culture = CultureDefinition(
        culture_id=uuid4(),
        world_id=uuid4(),
        name="Masked Vale",
        provenance=provenance(now),
    )
    service.register_culture(culture)
    base = dict(
        character_id=character_id,
        target_type=CulturalAffiliationTargetType.CULTURE,
        target_id=culture.culture_id,
        disposition=CulturalAffiliationDisposition.REJECTS,
        effective_from=now,
        provenance=provenance(now),
    )
    private_affiliation = IndividualCulturalAffiliation(
        affiliation_id=uuid4(),
        visibility=CulturalAffiliationVisibility.SELF,
        confidence="1",
        **base,
    )
    public_affiliation = IndividualCulturalAffiliation(
        affiliation_id=uuid4(),
        visibility=CulturalAffiliationVisibility.PUBLIC,
        confidence="0.8",
        effective_from=now - timedelta(days=10),
        effective_until=now - timedelta(days=1),
        **{key: value for key, value in base.items() if key != "effective_from"},
    )
    restricted_affiliation = IndividualCulturalAffiliation(
        affiliation_id=uuid4(),
        visibility=CulturalAffiliationVisibility.RESTRICTED,
        visible_to_character_ids=(trusted_id,),
        confidence="0.7",
        **base,
    )
    for affiliation in (
        private_affiliation,
        public_affiliation,
        restricted_affiliation,
    ):
        service.record_individual_cultural_affiliation(affiliation)

    outsider = service.character_cultural_context(character_id, observer_id, now)
    trusted = service.character_cultural_context(character_id, trusted_id, now)
    subject = service.character_cultural_context(character_id, character_id, now)

    assert outsider.affiliations == ()
    assert trusted.affiliations == (restricted_affiliation,)
    assert set(subject.affiliations) == {
        private_affiliation,
        restricted_affiliation,
    }


def test_cultural_change_history_is_event_tied_and_idempotent(
    tmp_path: Path,
) -> None:
    database, now = database_at(tmp_path)
    service = culture_service(database)
    world_id, timeline_id = uuid4(), uuid4()
    culture = CultureDefinition(
        culture_id=uuid4(),
        world_id=world_id,
        name="Delta Common",
        provenance=provenance(now),
    )
    event = EventEnvelope(
        event_id=uuid4(),
        world_id=world_id,
        timeline_id=timeline_id,
        occurred_at=now,
        recorded_at=now,
        sequence=1,
        event_type="migration",
        source_type="history",
        source_id="delta-settlement",
        payload_version="1",
        payload={},
    )
    with SqlAlchemySimulationUnitOfWork(database.session_factory) as unit_of_work:
        unit_of_work.repository.create_culture_definition(culture)
        unit_of_work.repository.append_event(event)
    record = CulturalChangeRecord(
        record_id=uuid4(),
        world_id=world_id,
        target_type=CulturalAffiliationTargetType.CULTURE,
        target_id=culture.culture_id,
        source_event_id=event.event_id,
        occurred_at=now,
        cause_tags=(
            CulturalChangeCause.MIGRATION,
            CulturalChangeCause.TRADE,
        ),
        old_state_reference=uuid4(),
        new_state_reference=uuid4(),
        summary="Delta customs became a practiced bridge-trade vocabulary.",
        provenance=provenance(now),
    )

    assert service.record_cultural_change(record) == record
    assert service.record_cultural_change(record) == record
    assert service.list_cultural_change_history(
        CulturalAffiliationTargetType.CULTURE, culture.culture_id
    ) == (record,)
    with database.session_factory() as session:
        changes = session.scalars(select(CulturalChangeRecordModel)).all()
        assert len(changes) == 1
        assert changes[0].source_event_id == str(event.event_id)
        assert set(changes[0].cause_tags) == {"migration", "trade"}
