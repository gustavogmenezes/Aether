from enum import Enum
from uuid import UUID

from pydantic import BaseModel, ConfigDict


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
    reason: str | None = None
