from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from uuid import UUID

from .errors import InvalidTemporalAdvanceError


class ScheduledEventStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    FAILED = "failed"


@dataclass(frozen=True, slots=True)
class WorldClockState:
    world_id: UUID
    timeline_id: UUID
    current_time: datetime
    version: int

    def advance_to(self, target_time: datetime) -> "WorldClockState":
        if target_time.tzinfo is None or target_time.utcoffset() is None:
            raise InvalidTemporalAdvanceError("Target time must include a UTC offset")
        if target_time < self.current_time:
            raise InvalidTemporalAdvanceError("World time cannot move backwards")
        return WorldClockState(
            world_id=self.world_id,
            timeline_id=self.timeline_id,
            current_time=target_time,
            version=self.version + 1,
        )
