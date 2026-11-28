from datetime import datetime
from uuid import UUID

from aether.contracts import (
    CharacterKnowledgeRecord,
    InformationTransmission,
    PerceptionEvidence,
)
from aether.domain.ports import SimulationUnitOfWorkFactory
from aether.engines import PerceptionAndInterpretationEngine


class KnowledgeService:
    def __init__(
        self,
        unit_of_work_factory: SimulationUnitOfWorkFactory,
        *,
        interpretation_engine: PerceptionAndInterpretationEngine | None = None,
    ) -> None:
        self._unit_of_work_factory = unit_of_work_factory
        self._interpretation_engine = (
            interpretation_engine or PerceptionAndInterpretationEngine()
        )

    def perceive(self, evidence: PerceptionEvidence) -> CharacterKnowledgeRecord | None:
        knowledge = self._interpretation_engine.perceive(evidence)
        if knowledge is None:
            return None
        with self._unit_of_work_factory() as unit_of_work:
            unit_of_work.repository.create_character_knowledge(knowledge)
            unit_of_work.commit()
        return knowledge

    def send(self, transmission: InformationTransmission) -> None:
        if transmission.arrival_at < transmission.sent_at:
            raise ValueError("Information cannot arrive before it is sent")
        with self._unit_of_work_factory() as unit_of_work:
            unit_of_work.repository.create_transmission(transmission)
            unit_of_work.commit()

    def character_context(
        self,
        character_id: UUID,
        *,
        as_of: datetime,
    ) -> tuple[str, ...]:
        with self._unit_of_work_factory() as unit_of_work:
            entries = unit_of_work.repository.list_character_knowledge(
                character_id,
                as_of=as_of,
            )
        return tuple(
            (
                f"{entry.fact_key}:{entry.statement}"
                f"[{entry.epistemic_status.value};confidence={entry.confidence:.2f}]"
            )
            for entry in entries
        )
