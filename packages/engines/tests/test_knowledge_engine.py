from datetime import UTC, datetime
from uuid import uuid4

from aether.contracts import (
    CommunicationMedium,
    EpistemicStatus,
    InformationNature,
    InformationTransmission,
    PerceptionEvidence,
)
from aether.engines import PerceptionAndInterpretationEngine


def test_non_perceptible_event_creates_no_knowledge() -> None:
    result = PerceptionAndInterpretationEngine().perceive(
        PerceptionEvidence(
            event_id=uuid4(),
            observer_character_id=uuid4(),
            fact_key="hidden-patrol",
            statement="A patrol crossed the ridge.",
            observed_at=datetime(2026, 1, 1, tzinfo=UTC),
            base_confidence=1,
            perceptible=False,
        )
    )

    assert result is None


def test_low_confidence_perception_is_partial_knowledge() -> None:
    result = PerceptionAndInterpretationEngine().perceive(
        PerceptionEvidence(
            event_id=uuid4(),
            observer_character_id=uuid4(),
            fact_key="distant-signal",
            statement="A light moved in the valley.",
            observed_at=datetime(2026, 1, 1, tzinfo=UTC),
            base_confidence=0.8,
            attention_modifier=0.5,
            perceptible=True,
        )
    )

    assert result is not None
    assert result.epistemic_status == EpistemicStatus.PARTIALLY_KNOWN
    assert result.confidence == 0.4


def test_deliberate_lie_is_not_promoted_to_known_fact() -> None:
    recipient_id = uuid4()
    result = PerceptionAndInterpretationEngine().interpret(
        InformationTransmission(
            transmission_id=uuid4(),
            source_event_id=None,
            sender_character_id=uuid4(),
            recipient_character_id=recipient_id,
            fact_key="bridge-state",
            statement="The north bridge is safe.",
            medium=CommunicationMedium.IN_PERSON,
            nature=InformationNature.DELIBERATE_LIE,
            sent_at=datetime(2026, 1, 1, tzinfo=UTC),
            arrival_at=datetime(2026, 1, 1, 0, 5, tzinfo=UTC),
            perceived_reliability=0.9,
        )
    )

    assert result.character_id == recipient_id
    assert result.epistemic_status == EpistemicStatus.INTENTIONAL_LIE
