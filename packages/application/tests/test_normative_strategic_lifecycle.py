from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import uuid4

import pytest
from sqlalchemy import select

from aether.application import TemporalAdvanceService
from aether.contracts import (
    ActorPosition,
    ActorReference,
    ActorType,
    AdvanceUntilEventCommand,
    EvidenceRecord,
    EvidenceVisibility,
    Investigation,
    Jurisdiction,
    LegalCase,
    MembershipStatus,
    NormativeAuthority,
    NormativeSystem,
    NormativeSystemKind,
    OrganizationAuthorityGrant,
    OrganizationMembership,
    RecordProvenance,
    ScheduledEvent,
    SemanticMetadata,
)
from aether.domain import WorldClockState
from aether.infrastructure import Database, SqlAlchemySimulationUnitOfWork
from aether.infrastructure.models import (
    CharacterKnowledgeModel,
    EventLedgerModel,
    EvidenceRecordModel,
    InvestigationModel,
)


def provenance(now):
    return RecordProvenance(
        source_type="test",
        source_id="authority",
        created_at=now,
        updated_at=now,
        version=1,
    )


def setup_case(tmp_path: Path, name: str, authorized: bool = True):
    database = Database.from_path(tmp_path / name)
    database.create_schema()
    now = datetime(2026, 8, 1, tzinfo=UTC)
    world_id, timeline_id = uuid4(), uuid4()
    system_id, case_id, investigation_id = uuid4(), uuid4(), uuid4()
    org_id, actor_id, location_id = uuid4(), uuid4(), uuid4()
    recipient_id, outsider_id = uuid4(), uuid4()
    evidence_id = uuid4()
    system = NormativeSystem(
        system_id=system_id,
        world_id=world_id,
        name="Municipal Charter",
        kind=NormativeSystemKind.FORMAL,
        jurisdiction=Jurisdiction(location_ids=(location_id,)),
        authorities=(
            NormativeAuthority(
                organization_id=org_id,
                permission_code="investigate",
            ),
        ),
        enforceability=SemanticMetadata(code="strong"),
        legitimacy=SemanticMetadata(code="accepted"),
        legal_validity=SemanticMetadata(code="valid"),
        provenance=provenance(now),
    )
    case = LegalCase(
        case_id=case_id,
        world_id=world_id,
        system_id=system_id,
        location_id=location_id,
        opened_at=now,
        provenance=provenance(now),
    )
    investigation = Investigation(
        investigation_id=investigation_id,
        case_id=case_id,
        responsible_organization_id=org_id,
        provenance=provenance(now),
    )
    evidence = EvidenceRecord(
        evidence_id=evidence_id,
        investigation_id=investigation_id,
        case_id=case_id,
        description="Restricted ledger entry",
        evidence_type="document",
        visibility=EvidenceVisibility.RESTRICTED,
        permitted_character_ids=(recipient_id,),
        acquired_at=now + timedelta(minutes=30),
        provenance=provenance(now),
    )
    event = ScheduledEvent(
        event_id=uuid4(),
        world_id=world_id,
        timeline_id=timeline_id,
        scheduled_at=now + timedelta(hours=1),
        event_type="investigation-completion",
        source_type="justice",
        source_id=str(investigation_id),
        payload_version="1",
        payload={
            "investigation_id": str(investigation_id),
            "evidence": [evidence.model_dump(mode="json")],
            "findings_summary": "Restricted facts established for the case.",
            "authority": {
                "actor_id": str(actor_id),
                "organization_id": str(org_id),
                "permission_code": "investigate",
                "location_id": str(location_id),
            },
            "knowledge_disclosures": [
                {
                    "character_id": str(recipient_id),
                    "fact_key": f"case:{case_id}:finding",
                    "statement": "A finding was explicitly disclosed to this character.",
                    "confidence": 0.9,
                    "epistemic_status": "belief",
                }
            ],
        },
    )
    with SqlAlchemySimulationUnitOfWork(database.session_factory) as uow:
        uow.repository.create_clock(
            WorldClockState(world_id, timeline_id, now, version=0)
        )
        uow.repository.create_normative_system(system)
        uow.repository.create_legal_case(case)
        uow.repository.create_investigation(investigation)
        uow.repository.create_organization_membership(
            OrganizationMembership(
                membership_id=uuid4(),
                organization_id=org_id,
                character_id=actor_id,
                formal_roles=("investigator",),
                status=(
                    MembershipStatus.ACTIVE
                    if authorized
                    else MembershipStatus.SUSPENDED
                ),
                provenance=provenance(now),
            )
        )
        uow.repository.create_organization_authority_grant(
            OrganizationAuthorityGrant(
                grant_id=uuid4(),
                organization_id=org_id,
                character_id=actor_id,
                role_code="investigator",
                permission_codes=("investigate",),
                formal=True,
                basis="charter",
                provenance=provenance(now),
            )
        )
        uow.repository.save_actor_position(
            ActorPosition(
                actor=ActorReference(actor_type=ActorType.CHARACTER, actor_id=actor_id),
                location_id=location_id,
                version=0,
            )
        )
        uow.repository.schedule_event(event)
    return {
        "database": database,
        "world_id": world_id,
        "timeline_id": timeline_id,
        "event": event,
        "investigation_id": investigation_id,
        "recipient_id": recipient_id,
        "outsider_id": outsider_id,
        "now": now,
    }


def service(database):
    return TemporalAdvanceService(
        lambda: SqlAlchemySimulationUnitOfWork(database.session_factory)
    )


def test_investigation_completion_filters_evidence_and_is_idempotent_with_advance_until(
    tmp_path: Path,
) -> None:
    data = setup_case(tmp_path, "filtered.db")
    command = AdvanceUntilEventCommand(
        simulation_run_id=uuid4(),
        world_id=data["world_id"],
        timeline_id=data["timeline_id"],
        scheduled_event_id=data["event"].event_id,
    )

    first = service(data["database"]).advance_until_event(command)
    replay = service(data["database"]).advance_until_event(command)

    assert replay.idempotent_replay
    assert replay.processed_event_ids == first.processed_event_ids
    with SqlAlchemySimulationUnitOfWork(data["database"].session_factory) as uow:
        investigation = uow.repository.get_investigation(data["investigation_id"])
        assert investigation is not None
        assert investigation.status.value == "completed"
        recipient_knowledge = uow.repository.list_character_knowledge(
            data["recipient_id"], as_of=data["now"] + timedelta(hours=1)
        )
        outsider_knowledge = uow.repository.list_character_knowledge(
            data["outsider_id"], as_of=data["now"] + timedelta(hours=1)
        )
        recipient_evidence = uow.repository.list_visible_evidence(
            data["recipient_id"], as_of=data["now"] + timedelta(hours=1)
        )
        outsider_evidence = uow.repository.list_visible_evidence(
            data["outsider_id"], as_of=data["now"] + timedelta(hours=1)
        )
        assert len(recipient_knowledge) == 1
        assert outsider_knowledge == ()
        assert len(recipient_evidence) == 1
        assert outsider_evidence == ()
    with data["database"].session_factory() as session:
        assert len(session.scalars(select(EventLedgerModel)).all()) == 1
        assert len(session.scalars(select(EvidenceRecordModel)).all()) == 1
        assert len(session.scalars(select(CharacterKnowledgeModel)).all()) == 1


def test_unauthorized_enforcement_rolls_back_the_whole_interval(tmp_path: Path) -> None:
    data = setup_case(tmp_path, "unauthorized.db", authorized=False)

    with pytest.raises(PermissionError):
        service(data["database"]).advance_until_event(
            AdvanceUntilEventCommand(
                simulation_run_id=uuid4(),
                world_id=data["world_id"],
                timeline_id=data["timeline_id"],
                scheduled_event_id=data["event"].event_id,
            )
        )

    with data["database"].session_factory() as session:
        assert session.scalars(select(EventLedgerModel)).all() == []
        assert session.scalars(select(EvidenceRecordModel)).all() == []
        stored = session.get(
            InvestigationModel, data["event"].payload["investigation_id"]
        )
        assert stored is not None and stored.status == "planned"
    with SqlAlchemySimulationUnitOfWork(data["database"].session_factory) as uow:
        clock = uow.repository.get_clock(data["world_id"], data["timeline_id"])
        assert clock is not None and clock.current_time == data["now"]
