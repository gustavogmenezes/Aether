from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class EpistemicStatus(str, Enum):
    KNOWN = "known"
    PARTIALLY_KNOWN = "partially-known"
    BELIEF = "belief"
    RUMOR = "rumor"
    SUSPICION = "suspicion"
    FALSE_INFORMATION = "false-information"
    INTENTIONAL_LIE = "intentional-lie"
    UNKNOWN = "unknown"


class CommunicationMedium(str, Enum):
    IN_PERSON = "in-person"
    PHYSICAL = "physical"
    SOCIAL = "social"
    INSTITUTIONAL = "institutional"
    TECHNOLOGICAL = "technological"
    SUPERNATURAL = "supernatural"


class InformationNature(str, Enum):
    FACT = "fact"
    HONEST_ERROR = "honest-error"
    MISINTERPRETATION = "misinterpretation"
    UNVERIFIED_RUMOR = "unverified-rumor"
    DELIBERATE_LIE = "deliberate-lie"
    PROPAGANDA = "propaganda"
    FABRICATION = "fabrication"


class TransmissionStatus(str, Enum):
    SENT = "sent"
    DELIVERED = "delivered"
    INTERPRETED = "interpreted"
    FAILED = "failed"
    CANCELLED = "cancelled"


class CharacterKnowledgeRecord(BaseModel):
    model_config = ConfigDict(frozen=True)

    knowledge_id: UUID
    character_id: UUID
    fact_key: str
    statement: str
    source_event_id: UUID | None
    acquisition_event_id: UUID | None
    acquired_at: datetime
    confidence: float = Field(ge=0, le=1)
    epistemic_status: EpistemicStatus
    temporal_scope: str | None = None
    visible_in_character_context: bool = True

    @field_validator("fact_key", "statement")
    @classmethod
    def require_non_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Knowledge fields cannot be blank")
        return value

    @field_validator("acquired_at")
    @classmethod
    def require_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("Knowledge acquisition time must include a UTC offset")
        return value


class InformationTransmission(BaseModel):
    model_config = ConfigDict(frozen=True)

    transmission_id: UUID
    source_event_id: UUID | None = None
    sender_character_id: UUID | None = None
    recipient_character_id: UUID
    fact_key: str
    statement: str
    medium: CommunicationMedium
    nature: InformationNature
    sent_at: datetime
    arrival_at: datetime
    status: TransmissionStatus = TransmissionStatus.SENT
    perceived_reliability: float = Field(ge=0, le=1)
    alterations: tuple[str, ...] = ()
    sender_intent: str | None = None
    reach: str | None = None
    source_language_id: UUID | None = None
    target_language_id: UUID | None = None
    source_dialect_id: UUID | None = None
    target_dialect_id: UUID | None = None
    writing_system_id: UUID | None = None
    presentation_language: str | None = None
    translation_semantics: tuple[str, ...] = ()
    imperfect_translation: bool = False

    @field_validator("fact_key", "statement")
    @classmethod
    def require_non_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Transmission fields cannot be blank")
        return value

    @field_validator("sent_at", "arrival_at")
    @classmethod
    def require_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("Transmission times must include a UTC offset")
        return value


class PerceptionEvidence(BaseModel):
    model_config = ConfigDict(frozen=True)

    event_id: UUID
    observer_character_id: UUID
    fact_key: str
    statement: str
    observed_at: datetime
    base_confidence: float = Field(ge=0, le=1)
    perceptible: bool
    attention_modifier: float = Field(default=1, ge=0, le=1)

    @field_validator("observed_at")
    @classmethod
    def require_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("Observation time must include a UTC offset")
        return value


class KnowledgeContextEntry(BaseModel):
    model_config = ConfigDict(frozen=True)

    fact_key: str
    statement: str
    confidence: float
    epistemic_status: EpistemicStatus
    acquired_at: datetime
