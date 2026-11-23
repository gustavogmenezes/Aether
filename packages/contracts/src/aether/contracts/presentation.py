from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from .action import ConfirmedActionResult


class PresentationStatus(str, Enum):
    GENERATED = "generated"
    CONFIRMED = "confirmed"
    DELIVERY_FAILED = "delivery-failed"


class NarrativeDraft(BaseModel):
    model_config = ConfigDict(frozen=True)

    presentation_id: UUID
    simulation_run_id: UUID
    content: str
    claims_supported_by_facts: tuple[str, ...]

    @field_validator("content")
    @classmethod
    def content_must_not_be_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Narrative content cannot be blank")
        return value


class NarrativeDelivery(BaseModel):
    model_config = ConfigDict(frozen=True)

    delivered_content: str
    delivered_claim_ids: tuple[str, ...]


class PresentationRecord(BaseModel):
    model_config = ConfigDict(frozen=True)

    presentation_id: UUID
    simulation_run_id: UUID
    protagonist_character_id: UUID
    narrative_time: datetime
    status: PresentationStatus
    generated_content: str
    delivered_content: str | None = None
    confirmed_fact_ids: tuple[str, ...] = ()
    created_at: datetime
    delivered_at: datetime | None = None


class PlayerKnowledgeRecord(BaseModel):
    model_config = ConfigDict(frozen=True)

    knowledge_id: UUID
    simulation_run_id: UUID
    player_id: str
    fact_key: str
    description: str
    source_presentation_id: UUID
    acquired_at: datetime


class NarrativeStateRecord(BaseModel):
    model_config = ConfigDict(frozen=True)

    state_id: UUID
    simulation_run_id: UUID
    protagonist_character_id: UUID
    scene_summary: str
    narrative_time: datetime
    created_at: datetime


class NarrativeContext(BaseModel):
    model_config = ConfigDict(frozen=True)

    confirmed_action: ConfirmedActionResult
    confirmed_facts: tuple[str, ...] = Field(min_length=0)
    character_knowledge: tuple[str, ...] = ()
