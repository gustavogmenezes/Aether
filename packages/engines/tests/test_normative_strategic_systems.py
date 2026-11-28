from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from aether.contracts import (
    AuthorityContext,
    Investigation,
    InvestigationCompletionPayload,
    LegalProceeding,
    LegalProceedingTransitionPayload,
    LegalCase,
    Jurisdiction,
    NormativeSystem,
    NormativeSystemKind,
    OrganizationRelation,
    RecordProvenance,
    ScheduledEvent,
    Sanction,
    SemanticMetadata,
    StrategicConflict,
    StrategicEscalationPayload,
    ProceedingStatus,
    SanctionStatus,
    CaseStatus,
    NormativeAuthority,
)
from aether.engines import NormativeStrategicResolver


def provenance(now):
    return RecordProvenance(
        source_type="test",
        source_id="normative",
        created_at=now,
        updated_at=now,
        version=1,
    )


def event(now, world_id, event_type, payload):
    return ScheduledEvent(
        event_id=uuid4(),
        world_id=world_id,
        timeline_id=uuid4(),
        scheduled_at=now + timedelta(hours=1),
        event_type=event_type,
        source_type="test",
        source_id="explicit",
        payload_version="1",
        payload=payload,
    )


def test_authority_and_legitimacy_are_independent_semantic_metadata() -> None:
    now = datetime(2026, 7, 1, tzinfo=UTC)
    system = NormativeSystem(
        system_id=uuid4(),
        world_id=uuid4(),
        name="River Compact",
        kind=NormativeSystemKind.CUSTOMARY,
        enforceability=SemanticMetadata(code="weak"),
        legitimacy=SemanticMetadata(code="high"),
        legal_validity=SemanticMetadata(code="disputed"),
        provenance=provenance(now),
    )

    assert system.enforceability.code == "weak"
    assert system.legitimacy.code == "high"
    assert system.legal_validity.code == "disputed"


def test_organization_relations_are_directional() -> None:
    now = datetime(2026, 7, 1, tzinfo=UTC)
    a, b, world = uuid4(), uuid4(), uuid4()
    forward = OrganizationRelation(
        relation_id=uuid4(),
        world_id=world,
        source_organization_id=a,
        target_organization_id=b,
        dimensions={"trust": ("low",), "dependence": ("high",)},
        provenance=provenance(now),
    )
    reverse = OrganizationRelation(
        relation_id=uuid4(),
        world_id=world,
        source_organization_id=b,
        target_organization_id=a,
        dimensions={"trust": ("guarded",), "dependence": ("none",)},
        provenance=provenance(now),
    )

    assert forward.dimensions != reverse.dimensions
    with pytest.raises(ValueError):
        OrganizationRelation(
            relation_id=uuid4(),
            world_id=world,
            source_organization_id=a,
            target_organization_id=a,
            provenance=provenance(now),
        )


def test_strategic_escalation_has_no_required_linear_stage() -> None:
    now = datetime(2026, 7, 1, tzinfo=UTC)
    world, org = uuid4(), uuid4()
    conflict = StrategicConflict(
        conflict_id=uuid4(),
        world_id=world,
        name="Harbor Dispute",
        party_organization_ids=(org, uuid4()),
        escalation_stage="diplomatic",
        provenance=provenance(now),
    )
    payload = StrategicEscalationPayload(
        conflict_id=conflict.conflict_id,
        target_stage="occupation",
        stage_metadata={"basis": "explicit authorized transition"},
        authority=AuthorityContext(
            actor_id=uuid4(),
            organization_id=org,
            permission_code="strategic-resolution",
            location_id=uuid4(),
        ),
    )
    resolution = NormativeStrategicResolver().resolve_strategic_escalation(
        event(now, world, "strategic-escalation", payload.model_dump(mode="json")),
        conflict,
    )

    assert resolution.strategic_conflict is not None
    assert resolution.strategic_conflict.escalation_stage == "occupation"
    assert conflict.escalation_stage == "diplomatic"


def test_investigation_rejects_undeclared_normative_authority() -> None:
    now = datetime(2026, 7, 1, tzinfo=UTC)
    world, org, location = uuid4(), uuid4(), uuid4()
    system = NormativeSystem(
        system_id=uuid4(),
        world_id=world,
        name="Civic Code",
        kind=NormativeSystemKind.FORMAL,
        authorities=(),
        enforceability=SemanticMetadata(code="operational"),
        legitimacy=SemanticMetadata(code="contested"),
        legal_validity=SemanticMetadata(code="valid"),
        provenance=provenance(now),
    )
    case = LegalCase(
        case_id=uuid4(),
        world_id=world,
        system_id=system.system_id,
        location_id=location,
        opened_at=now,
        provenance=provenance(now),
    )
    investigation = Investigation(
        investigation_id=uuid4(),
        case_id=case.case_id,
        responsible_organization_id=org,
        provenance=provenance(now),
    )
    payload = InvestigationCompletionPayload(
        investigation_id=investigation.investigation_id,
        findings_summary="No explicit finding is necessary for this denial.",
        authority=AuthorityContext(
            actor_id=uuid4(),
            organization_id=org,
            permission_code="investigate",
            location_id=location,
        ),
    )

    with pytest.raises(PermissionError):
        NormativeStrategicResolver().resolve_investigation(
            event(
                now,
                world,
                "investigation-completion",
                payload.model_dump(mode="json"),
            ),
            system,
            case,
            investigation,
        )


def test_sanction_rejects_an_authority_other_than_the_enforcing_actor() -> None:
    now = datetime(2026, 7, 1, tzinfo=UTC)
    world, org, location = uuid4(), uuid4(), uuid4()
    system = NormativeSystem(
        system_id=uuid4(),
        world_id=world,
        name="Civic Code",
        kind=NormativeSystemKind.FORMAL,
        jurisdiction=Jurisdiction(location_ids=(location,)),
        authorities=(
            NormativeAuthority(
                organization_id=org,
                permission_code="sentence",
            ),
        ),
        enforceability=SemanticMetadata(code="operational"),
        legitimacy=SemanticMetadata(code="contested"),
        legal_validity=SemanticMetadata(code="valid"),
        provenance=provenance(now),
    )
    case = LegalCase(
        case_id=uuid4(),
        world_id=world,
        system_id=system.system_id,
        location_id=location,
        opened_at=now,
        provenance=provenance(now),
    )
    proceeding = LegalProceeding(
        proceeding_id=uuid4(),
        case_id=case.case_id,
        kind="trial",
        location_id=location,
        provenance=provenance(now),
    )
    sanction = Sanction(
        sanction_id=uuid4(),
        case_id=case.case_id,
        proceeding_id=proceeding.proceeding_id,
        kind="detention",
        status=SanctionStatus.ORDERED,
        authority_organization_id=uuid4(),
        provenance=provenance(now),
    )
    payload = LegalProceedingTransitionPayload(
        case_id=case.case_id,
        proceeding_id=proceeding.proceeding_id,
        target_status=ProceedingStatus.DECIDED,
        case_status=CaseStatus.DECIDED,
        sanctions=(sanction,),
        authority=AuthorityContext(
            actor_id=uuid4(),
            organization_id=org,
            permission_code="sentence",
            location_id=location,
        ),
    )

    with pytest.raises(PermissionError):
        NormativeStrategicResolver().resolve_legal_proceeding(
            event(
                now,
                world,
                "legal-proceeding-transition",
                payload.model_dump(mode="json"),
            ),
            system,
            case,
            proceeding,
        )
