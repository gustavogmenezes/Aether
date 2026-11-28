from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import uuid4

import pytest
from sqlalchemy import select

from aether.application import CulturalSystemsService, TemporalAdvanceService
from aether.contracts import (
    AccessRequirements,
    AdvanceTimeCommand,
    CommunicationMedium,
    CurriculumEntry,
    EducationEnrollment,
    EducationProgram,
    IndividualBeliefRecord,
    InformationNature,
    InformationTransmission,
    KnowledgeArtifact,
    KnowledgeLifecycleState,
    Language,
    LearningOpportunity,
    MetaphysicalTruth,
    RecordProvenance,
    ReligionTradition,
    ScheduledEvent,
    Technology,
    TransmissionStatus,
)
from aether.domain import WorldClockState
from aether.infrastructure import Database, SqlAlchemySimulationUnitOfWork
from aether.infrastructure.models import (
    AssessmentOutcomeModel,
    CharacterKnowledgeModel,
    EducationEnrollmentModel,
    EventLedgerModel,
    IndividualBeliefRecordModel,
    InformationTransmissionModel,
    KnowledgeLifecycleRecordModel,
    MetaphysicalTruthModel,
    RitualCompletionModel,
)


def provenance(now: datetime, source: str = "test") -> RecordProvenance:
    return RecordProvenance(
        source_type="test",
        source_id=source,
        created_at=now,
        updated_at=now,
        version=1,
    )


def database_at(tmp_path: Path, name: str):
    database = Database.from_path(tmp_path / name)
    database.create_schema()
    now = datetime(2026, 5, 1, tzinfo=UTC)
    world_id, timeline_id = uuid4(), uuid4()
    with SqlAlchemySimulationUnitOfWork(database.session_factory) as uow:
        uow.repository.create_clock(
            WorldClockState(world_id, timeline_id, now, version=0)
        )
    return database, now, world_id, timeline_id


def service(database: Database) -> TemporalAdvanceService:
    return TemporalAdvanceService(
        lambda: SqlAlchemySimulationUnitOfWork(database.session_factory)
    )


def test_knowledge_does_not_teleport_and_authorized_transmission_is_idempotent(
    tmp_path: Path,
) -> None:
    database, now, world_id, timeline_id = database_at(tmp_path, "knowledge.db")
    actor_id = uuid4()
    location_id = uuid4()
    language_id = uuid4()
    artifact = KnowledgeArtifact(
        artifact_id=uuid4(),
        world_id=world_id,
        name="Tidal Memory",
        category="scientific",
        state=KnowledgeLifecycleState.EXISTS,
        requirements=AccessRequirements(
            location_ids=(location_id,),
            language_requirements=(language_id,),
            secrecy_permissions=("archive-reader",),
        ),
        provenance=provenance(now),
    )
    cultural = CulturalSystemsService(
        lambda: SqlAlchemySimulationUnitOfWork(database.session_factory)
    )
    cultural.register_knowledge_artifact(artifact)
    transmission_event = ScheduledEvent(
        event_id=uuid4(),
        world_id=world_id,
        timeline_id=timeline_id,
        scheduled_at=now + timedelta(hours=1),
        event_type="knowledge-transmission",
        source_type="education",
        source_id="archive-lesson",
        payload_version="1",
        payload={
            "artifact_id": str(artifact.artifact_id),
            "actor_id": str(actor_id),
            "target_state": "transmitted",
            "cause": "explicit teaching session",
            "location_id": str(location_id),
            "language_id": str(language_id),
            "access_context": {
                "actor_id": str(actor_id),
                "location_id": str(location_id),
                "language_capabilities": [str(language_id)],
                "secrecy_permissions": ["archive-reader"],
            },
        },
    )
    cultural.schedule_authorized_cultural_event(transmission_event)

    with SqlAlchemySimulationUnitOfWork(database.session_factory) as uow:
        before = uow.repository.get_knowledge_artifact(artifact.artifact_id)
        assert before is not None
        assert before.state == KnowledgeLifecycleState.EXISTS
        assert uow.session.scalars(select(CharacterKnowledgeModel)).all() == []

    command = AdvanceTimeCommand(
        simulation_run_id=uuid4(),
        world_id=world_id,
        timeline_id=timeline_id,
        duration=timedelta(hours=1),
    )
    first = service(database).advance_time(command)
    replay = service(database).advance_time(command)

    assert replay.idempotent_replay
    assert replay.processed_event_ids == first.processed_event_ids
    with SqlAlchemySimulationUnitOfWork(database.session_factory) as uow:
        stored = uow.repository.get_knowledge_artifact(artifact.artifact_id)
        assert stored is not None and stored.state == KnowledgeLifecycleState.TRANSMITTED
        assert len(uow.session.scalars(select(KnowledgeLifecycleRecordModel)).all()) == 1
        assert len(uow.session.scalars(select(EventLedgerModel)).all()) == 1
        assert uow.session.scalars(select(CharacterKnowledgeModel)).all() == []


def test_language_barrier_records_explicit_transmission_failure(tmp_path: Path) -> None:
    database, now, world_id, timeline_id = database_at(tmp_path, "language.db")
    language = Language(
        language_id=uuid4(),
        world_id=world_id,
        name="Keth",
        family="Valley",
        provenance=provenance(now),
    )
    recipient_id = uuid4()
    transmission = InformationTransmission(
        transmission_id=uuid4(),
        recipient_character_id=recipient_id,
        fact_key="warning",
        statement="The bridge is unsafe.",
        medium=CommunicationMedium.IN_PERSON,
        nature=InformationNature.FACT,
        sent_at=now,
        arrival_at=now + timedelta(minutes=5),
        perceived_reliability=1,
        source_language_id=language.language_id,
    )
    with SqlAlchemySimulationUnitOfWork(database.session_factory) as uow:
        uow.repository.create_language(language)
        uow.repository.create_transmission(transmission)

    service(database).advance_time(
        AdvanceTimeCommand(
            simulation_run_id=uuid4(),
            world_id=world_id,
            timeline_id=timeline_id,
            duration=timedelta(minutes=5),
        )
    )

    with database.session_factory() as session:
        stored = session.get(
            InformationTransmissionModel, str(transmission.transmission_id)
        )
        assert stored is not None and stored.status == TransmissionStatus.FAILED.value
        assert session.scalars(select(CharacterKnowledgeModel)).all() == []


def test_education_opportunity_does_not_grant_mastery(tmp_path: Path) -> None:
    database, now, world_id, timeline_id = database_at(tmp_path, "education.db")
    character_id = uuid4()
    program = EducationProgram(
        program_id=uuid4(),
        world_id=world_id,
        name="Foundry Apprenticeship",
        formality="formal",
        curriculum=(
            CurriculumEntry(
                entry_id=uuid4(),
                subject_reference="metalworking",
                method="practice",
                sequence=0,
            ),
        ),
        provenance=provenance(now),
    )
    enrollment = EducationEnrollment(
        enrollment_id=uuid4(),
        program_id=program.program_id,
        character_id=character_id,
        enrolled_at=now,
        provenance=provenance(now),
    )
    opportunity = LearningOpportunity(
        opportunity_id=uuid4(),
        program_id=program.program_id,
        participant_character_id=character_id,
        kind="practice-session",
        began_at=now,
        ended_at=now + timedelta(hours=1),
        provenance=provenance(now),
    )
    with SqlAlchemySimulationUnitOfWork(database.session_factory) as uow:
        uow.repository.create_education_program(program)
        uow.repository.create_education_enrollment(enrollment)
        uow.repository.create_learning_opportunity(opportunity)
        uow.repository.schedule_event(
            ScheduledEvent(
                event_id=uuid4(),
                world_id=world_id,
                timeline_id=timeline_id,
                scheduled_at=opportunity.ended_at,
                event_type="learning-assessment",
                source_type="education",
                source_id="foundry",
                payload_version="1",
                payload={
                    "enrollment_id": str(enrollment.enrollment_id),
                    "opportunity_id": str(opportunity.opportunity_id),
                    "actor_id": str(character_id),
                    "stated_outcome": "Observed basic safe handling only",
                    "mastery_asserted": False,
                    "completion_asserted": False,
                    "access_context": {
                        "actor_id": str(character_id),
                        "location_id": None,
                    },
                },
            )
        )

    service(database).advance_time(
        AdvanceTimeCommand(
            simulation_run_id=uuid4(),
            world_id=world_id,
            timeline_id=timeline_id,
            duration=timedelta(hours=1),
        )
    )

    with database.session_factory() as session:
        outcomes = session.scalars(select(AssessmentOutcomeModel)).all()
        enrollments = session.scalars(select(EducationEnrollmentModel)).all()
        assert len(outcomes) == 1
        assert outcomes[0].payload["mastery_asserted"] is False
        assert enrollments[0].status == "admitted"
        assert session.scalars(select(KnowledgeLifecycleRecordModel)).all() == []


def test_individual_faith_and_world_truth_remain_separate_from_membership(
    tmp_path: Path,
) -> None:
    database, now, world_id, _ = database_at(tmp_path, "belief.db")
    organization_id = uuid4()
    character_id = uuid4()
    tradition = ReligionTradition(
        tradition_id=uuid4(),
        world_id=world_id,
        name="Ember Tradition",
        organization_id=organization_id,
        doctrine_references=("cycle.md",),
        ritual_references=("dawn-vigil",),
        provenance=provenance(now),
    )
    belief = IndividualBeliefRecord(
        belief_id=uuid4(),
        character_id=character_id,
        tradition_id=None,
        propositions=("The ember remembers.",),
        practice_commitment="private observance",
        acquired_at=now,
        provenance=provenance(now),
    )
    truth = MetaphysicalTruth(
        truth_id=uuid4(),
        world_id=world_id,
        statement="The ember has no memory.",
        scope="world-cosmology",
        provenance=provenance(now),
    )
    with SqlAlchemySimulationUnitOfWork(database.session_factory) as uow:
        uow.repository.create_religion_tradition(tradition)
        uow.repository.create_individual_belief(belief)
        uow.repository.create_metaphysical_truth(truth)

    with SqlAlchemySimulationUnitOfWork(database.session_factory) as uow:
        character_context = uow.repository.list_character_knowledge(
            character_id, as_of=now
        )
        assert character_context == ()
    with database.session_factory() as session:
        stored_belief = session.scalar(select(IndividualBeliefRecordModel))
        assert stored_belief is not None
        assert stored_belief.tradition_id is None
        stored_truth = session.scalar(select(MetaphysicalTruthModel))
        assert stored_truth is not None
        assert stored_truth.disclosure_class == "world-objective-only"


def test_technology_use_and_ritual_are_authorized_records_not_automatic_belief(
    tmp_path: Path,
) -> None:
    database, now, world_id, timeline_id = database_at(tmp_path, "events.db")
    actor_id = uuid4()
    location_id = uuid4()
    technology = Technology(
        technology_id=uuid4(),
        world_id=world_id,
        name="Pressure Loom",
        manufacture_conditions=("calibrated loom",),
        provenance=provenance(now),
    )
    tradition = ReligionTradition(
        tradition_id=uuid4(),
        world_id=world_id,
        name="Dawn Circle",
        ritual_references=("threshold-vigil",),
        provenance=provenance(now),
    )
    due_at = now + timedelta(minutes=10)
    with SqlAlchemySimulationUnitOfWork(database.session_factory) as uow:
        uow.repository.create_technology(technology)
        uow.repository.create_religion_tradition(tradition)
        for event in (
            ScheduledEvent(
                event_id=uuid4(),
                world_id=world_id,
                timeline_id=timeline_id,
                scheduled_at=due_at,
                event_type="technology-use-completion",
                source_type="work",
                source_id="loom",
                payload_version="1",
                payload={
                    "technology_id": str(technology.technology_id),
                    "actor_id": str(actor_id),
                    "target_state": "applied",
                    "cause": "calibrated operation completed",
                    "location_id": str(location_id),
                    "access_context": {
                        "actor_id": str(actor_id),
                        "location_id": str(location_id),
                        "satisfied_capabilities": ["calibrated loom"],
                    },
                },
            ),
            ScheduledEvent(
                event_id=uuid4(),
                world_id=world_id,
                timeline_id=timeline_id,
                scheduled_at=due_at,
                event_type="religious-ritual",
                source_type="tradition",
                source_id="dawn-circle",
                payload_version="1",
                payload={
                    "tradition_id": str(tradition.tradition_id),
                    "actor_id": str(actor_id),
                    "ritual_reference": "threshold-vigil",
                    "location_id": str(location_id),
                    "outcome_record": "ritual performed",
                    "access_context": {
                        "actor_id": str(actor_id),
                        "location_id": str(location_id),
                    },
                },
            ),
        ):
            uow.repository.schedule_event(event)

    service(database).advance_time(
        AdvanceTimeCommand(
            simulation_run_id=uuid4(),
            world_id=world_id,
            timeline_id=timeline_id,
            duration=timedelta(minutes=10),
        )
    )

    with database.session_factory() as session:
        completions = session.scalars(select(RitualCompletionModel)).all()
        assert len(completions) == 1
        assert session.scalars(select(IndividualBeliefRecordModel)).all() == []
    with SqlAlchemySimulationUnitOfWork(database.session_factory) as uow:
        stored = uow.repository.get_technology(technology.technology_id)
        assert stored is not None and stored.state == KnowledgeLifecycleState.APPLIED


def test_cultural_event_access_failure_rolls_back_interval(tmp_path: Path) -> None:
    database, now, world_id, timeline_id = database_at(tmp_path, "rollback.db")
    artifact = KnowledgeArtifact(
        artifact_id=uuid4(),
        world_id=world_id,
        name="Restricted Formula",
        category="practical",
        requirements=AccessRequirements(secrecy_permissions=("formula-reader",)),
        provenance=provenance(now),
    )
    with SqlAlchemySimulationUnitOfWork(database.session_factory) as uow:
        uow.repository.create_knowledge_artifact(artifact)
        uow.repository.schedule_event(
            ScheduledEvent(
                event_id=uuid4(),
                world_id=world_id,
                timeline_id=timeline_id,
                scheduled_at=now + timedelta(minutes=1),
                event_type="knowledge-transmission",
                source_type="test",
                source_id="denied",
                payload_version="1",
                payload={
                    "artifact_id": str(artifact.artifact_id),
                    "actor_id": str(uuid4()),
                    "target_state": "transmitted",
                    "cause": "attempted disclosure",
                    "access_context": {
                        "actor_id": str(uuid4()),
                        "location_id": None,
                    },
                },
            )
        )

    with pytest.raises(PermissionError):
        service(database).advance_time(
            AdvanceTimeCommand(
                simulation_run_id=uuid4(),
                world_id=world_id,
                timeline_id=timeline_id,
                duration=timedelta(minutes=1),
            )
        )

    with SqlAlchemySimulationUnitOfWork(database.session_factory) as uow:
        stored = uow.repository.get_knowledge_artifact(artifact.artifact_id)
        clock = uow.repository.get_clock(world_id, timeline_id)
        assert stored is not None and stored.state == KnowledgeLifecycleState.EXISTS
        assert clock is not None and clock.current_time == now
        assert uow.session.scalars(select(EventLedgerModel)).all() == []
