from uuid import uuid4

from aether.contracts import (
    CharacterKnowledgeRecord,
    EpistemicStatus,
    InformationNature,
    InformationTransmission,
    PerceptionEvidence,
    TransmissionStatus,
)


class PerceptionAndInterpretationEngine:
    def perceive(
        self,
        evidence: PerceptionEvidence,
    ) -> CharacterKnowledgeRecord | None:
        if not evidence.perceptible:
            return None
        confidence = evidence.base_confidence * evidence.attention_modifier
        status = (
            EpistemicStatus.KNOWN
            if confidence >= 0.75
            else EpistemicStatus.PARTIALLY_KNOWN
        )
        return CharacterKnowledgeRecord(
            knowledge_id=uuid4(),
            character_id=evidence.observer_character_id,
            fact_key=evidence.fact_key,
            statement=evidence.statement,
            source_event_id=evidence.event_id,
            acquisition_event_id=evidence.event_id,
            acquired_at=evidence.observed_at,
            confidence=confidence,
            epistemic_status=status,
            temporal_scope="acquired-through-perception",
            visible_in_character_context=True,
        )

    def interpret(
        self,
        transmission: InformationTransmission,
    ) -> CharacterKnowledgeRecord:
        if transmission.status not in {
            TransmissionStatus.SENT,
            TransmissionStatus.DELIVERED,
        }:
            raise ValueError("Only sent or delivered transmissions can be interpreted")
        nature_status = {
            InformationNature.FACT: EpistemicStatus.KNOWN,
            InformationNature.HONEST_ERROR: EpistemicStatus.BELIEF,
            InformationNature.MISINTERPRETATION: EpistemicStatus.BELIEF,
            InformationNature.UNVERIFIED_RUMOR: EpistemicStatus.RUMOR,
            InformationNature.DELIBERATE_LIE: EpistemicStatus.INTENTIONAL_LIE,
            InformationNature.PROPAGANDA: EpistemicStatus.SUSPICION,
            InformationNature.FABRICATION: EpistemicStatus.FALSE_INFORMATION,
        }[transmission.nature]
        return CharacterKnowledgeRecord(
            knowledge_id=uuid4(),
            character_id=transmission.recipient_character_id,
            fact_key=transmission.fact_key,
            statement=transmission.statement,
            source_event_id=transmission.source_event_id,
            acquisition_event_id=None,
            acquired_at=transmission.arrival_at,
            confidence=transmission.perceived_reliability,
            epistemic_status=nature_status,
            temporal_scope="acquired-through-communication",
            visible_in_character_context=True,
        )
