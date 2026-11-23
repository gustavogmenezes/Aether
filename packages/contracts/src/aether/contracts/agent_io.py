from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from .action import ActionProposal, PlayerInput


class GameMasterContext(BaseModel):
    model_config = ConfigDict(frozen=True)

    player_input: PlayerInput
    current_world_time: datetime


class GameMasterResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    invocation_id: UUID
    proposal: ActionProposal
    requesting_agent: str = "GameMaster"
    requested_capability: str = "action-interpretation"
    model: str
    model_version: str
    prompt_version: str
    context_hash: str
    inference_parameters: dict[str, object]
    raw_response_reference: str
    created_at: datetime
    completed_at: datetime
