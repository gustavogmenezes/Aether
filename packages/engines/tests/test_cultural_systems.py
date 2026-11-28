from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid4

from aether.contracts import (
    AccessRequirements,
    ActorAccessContext,
    CommunicationMedium,
    InformationNature,
    InformationTransmission,
    LanguageProficiencyDimension,
    ResourceRequirement,
)
from aether.engines import ActorAccessEngine, LanguageCommunicationEngine


def test_actor_access_has_explicit_location_resource_language_and_admission_failures(
) -> None:
    requirements = AccessRequirements(
        location_ids=(uuid4(),),
        resource_requirements=(
            ResourceRequirement(resource_code="vellum", quantity=Decimal("2")),
        ),
        infrastructure_ids=(uuid4(),),
        language_requirements=(uuid4(),),
        secrecy_permissions=("restricted-archive",),
        education_admission_conditions=("guild-sponsor",),
    )
    context = ActorAccessContext(
        actor_id=uuid4(),
        location_id=uuid4(),
        available_resources={"vellum": Decimal("1")},
    )

    decision = ActorAccessEngine().decide(requirements, context)

    assert not decision.allowed
    assert {failure.code for failure in decision.failures} == {
        "location-denied",
        "resource-unavailable",
        "infrastructure-unavailable",
        "language-barrier",
        "secrecy-denied",
        "education-admission-denied",
    }


def test_language_barrier_prevents_communication_without_translatable_proficiency(
) -> None:
    now = datetime(2026, 1, 1, tzinfo=UTC)
    language_id = uuid4()
    transmission = InformationTransmission(
        transmission_id=uuid4(),
        recipient_character_id=uuid4(),
        fact_key="water.sealed",
        statement="The cistern is sealed.",
        medium=CommunicationMedium.IN_PERSON,
        nature=InformationNature.FACT,
        sent_at=now,
        arrival_at=now,
        perceived_reliability=1,
        source_language_id=language_id,
    )

    assert not LanguageCommunicationEngine().can_interpret(transmission, None)
    assert (
        LanguageProficiencyDimension.COMPREHENSION.value == "comprehension"
    )

