from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class SimulationRunStatus(str, Enum):
    PREPARED = "prepared"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class SimulationRunRecord(BaseModel):
    model_config = ConfigDict(frozen=True)

    simulation_run_id: UUID
    operation: str
    world_id: UUID
    timeline_id: UUID
    status: SimulationRunStatus
    initial_time: datetime
    target_time: datetime
    final_time: datetime | None = None
    processed_event_ids: tuple[UUID, ...] = ()
    error: str | None = None
    created_at: datetime
    updated_at: datetime


class LlmInvocationRecord(BaseModel):
    model_config = ConfigDict(frozen=True)

    invocation_id: UUID
    simulation_run_id: UUID
    requesting_agent: str
    requested_capability: str
    model: str
    model_version: str
    prompt_version: str
    context_hash: str
    inference_parameters: dict[str, Any] = Field(default_factory=dict)
    response_reference: str
    status: str
    input_tokens: int | None = None
    output_tokens: int | None = None
    created_at: datetime
    completed_at: datetime | None = None


class AgentProposalRecord(BaseModel):
    model_config = ConfigDict(frozen=True)

    proposal_id: UUID
    simulation_run_id: UUID
    invocation_id: UUID
    proposal_type: str
    payload: dict[str, Any]
    validation_status: str
    rejection_reason: str | None = None
    application_result: dict[str, Any] | None = None
    created_at: datetime
