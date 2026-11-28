from enum import Enum
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from .ecology import EcologicalProcess, Population
from .health import HealthState
from .culture import (
    AssessmentOutcome,
    KnowledgeArtifact,
    KnowledgeLifecycleRecord,
    LearningOpportunity,
    RitualCompletion,
    Technology,
)
from .knowledge import CharacterKnowledgeRecord
from .normative import (
    EvidenceRecord,
    IntelligenceOperation,
    Investigation,
    LegalCase,
    LegalProceeding,
    Sanction,
    SecurityResolution,
    SecurityThreat,
    StrategicConflict,
    Treaty,
)
from .expression import (
    CollectiveReception,
    PublicInformation,
)


class ScheduledEventOutcome(str, Enum):
    COMPLETED = "completed"
    FAILED = "failed"
    UNCHANGED = "unchanged"


class ScheduledEventResolution(BaseModel):
    model_config = ConfigDict(frozen=True)

    scheduled_event_id: UUID
    outcome: ScheduledEventOutcome
    payload: dict[str, object]
    plan_step_id: UUID | None = None
    journey_id: UUID | None = None
    reason: str | None = None
    population: Population | None = None
    ecological_process: EcologicalProcess | None = None
    health_state: HealthState | None = None
    knowledge_artifact: KnowledgeArtifact | None = None
    technology: Technology | None = None
    lifecycle_records: tuple[KnowledgeLifecycleRecord, ...] = ()
    learning_opportunities: tuple[LearningOpportunity, ...] = ()
    assessment_outcomes: tuple[AssessmentOutcome, ...] = ()
    ritual_completions: tuple[RitualCompletion, ...] = ()
    legal_case: LegalCase | None = None
    legal_proceeding: LegalProceeding | None = None
    sanctions: tuple[Sanction, ...] = ()
    investigation: Investigation | None = None
    evidence_records: tuple[EvidenceRecord, ...] = ()
    treaty: Treaty | None = None
    strategic_conflict: StrategicConflict | None = None
    security_threat: SecurityThreat | None = None
    intelligence_operation: IntelligenceOperation | None = None
    security_resolutions: tuple[SecurityResolution, ...] = ()
    character_knowledge: tuple[CharacterKnowledgeRecord, ...] = ()
    publication: PublicInformation | None = None
    collective_receptions: tuple[CollectiveReception, ...] = ()
