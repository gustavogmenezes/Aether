from datetime import datetime, timedelta
from uuid import UUID

from pydantic import BaseModel, ConfigDict, field_validator, model_validator


class AdvanceTimeCommand(BaseModel):
    model_config = ConfigDict(frozen=True)

    simulation_run_id: UUID
    world_id: UUID
    timeline_id: UUID
    duration: timedelta

    @field_validator("duration")
    @classmethod
    def duration_must_be_positive(cls, value: timedelta) -> timedelta:
        if value.total_seconds() <= 0:
            raise ValueError("AdvanceTime duration must be positive")
        return value


class AdvanceUntilEventCommand(BaseModel):
    model_config = ConfigDict(frozen=True)

    simulation_run_id: UUID
    world_id: UUID
    timeline_id: UUID
    scheduled_event_id: UUID


class TemporalAdvanceResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    simulation_run_id: UUID
    initial_time: datetime
    final_time: datetime
    processed_event_ids: tuple[UUID, ...]
    idempotent_replay: bool = False

    @model_validator(mode="after")
    def validate_interval(self) -> "TemporalAdvanceResult":
        if self.final_time < self.initial_time:
            raise ValueError("Final time cannot precede initial time")
        return self
