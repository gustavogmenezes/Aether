from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class InterruptionClass(str, Enum):
    CRITICAL = "critical"
    RELEVANT = "relevant"
    ORDINARY = "ordinary"


class EventEnvelope(BaseModel):
    model_config = ConfigDict(frozen=True)

    event_id: UUID
    world_id: UUID
    timeline_id: UUID
    occurred_at: datetime
    recorded_at: datetime
    sequence: int = Field(ge=1)
    event_type: str
    source_type: str
    source_id: str
    caused_by: tuple[UUID, ...] = ()
    priority: int = 0
    payload_version: str
    payload: dict[str, Any]
    interruption_class: InterruptionClass = InterruptionClass.ORDINARY

    @field_validator("occurred_at", "recorded_at")
    @classmethod
    def require_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("Event timestamps must include a UTC offset")
        return value

    @field_validator("event_type", "source_type", "source_id", "payload_version")
    @classmethod
    def require_non_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Event metadata cannot be blank")
        return value


class ScheduledEvent(BaseModel):
    model_config = ConfigDict(frozen=True)

    event_id: UUID
    world_id: UUID
    timeline_id: UUID
    scheduled_at: datetime
    event_type: str
    source_type: str
    source_id: str
    caused_by: tuple[UUID, ...] = ()
    priority: int = 0
    payload_version: str
    payload: dict[str, Any]
    interruption_class: InterruptionClass = InterruptionClass.ORDINARY

    @field_validator("scheduled_at")
    @classmethod
    def require_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("Scheduled time must include a UTC offset")
        return value

    @model_validator(mode="after")
    def validate_metadata(self) -> "ScheduledEvent":
        for field_name in ("event_type", "source_type", "source_id", "payload_version"):
            if not getattr(self, field_name).strip():
                raise ValueError(f"{field_name} cannot be blank")
        return self
