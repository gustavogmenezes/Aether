from enum import Enum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ExperienceMode(str, Enum):
    PLAYER_CHARACTER = "player-character"
    NARRATIVE_PROTAGONIST = "narrative-protagonist"
    OBSERVER = "observer"


class ActionKind(str, Enum):
    INSTANTANEOUS = "instantaneous"
    INTERVAL = "interval"
    INTERRUPTIBLE = "interruptible"
    SCHEDULED = "scheduled"


class PlayerInput(BaseModel):
    model_config = ConfigDict(frozen=True)

    input_id: UUID
    simulation_run_id: UUID
    world_id: UUID
    timeline_id: UUID
    protagonist_character_id: UUID
    player_id: str = "local-player"
    mode: ExperienceMode
    text: str

    @field_validator("text")
    @classmethod
    def text_must_not_be_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Player input cannot be blank")
        return value


class ActionProposal(BaseModel):
    model_config = ConfigDict(frozen=True)

    proposal_id: UUID
    invocation_id: UUID
    action_kind: ActionKind
    intent: str
    duration_seconds: int = Field(ge=0)
    targets: tuple[str, ...] = ()
    requires_player_approval: bool = False
    unverified_details: tuple[str, ...] = ()

    @field_validator("intent")
    @classmethod
    def intent_must_not_be_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Action intent cannot be blank")
        return value


class ActionValidationResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    accepted: bool
    duration_seconds: int = Field(ge=0)
    rejection_reason: str | None = None
    confirmed_facts: tuple[str, ...] = ()
    requires_player_approval: bool = False


class ConfirmedActionResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    simulation_run_id: UUID
    protagonist_character_id: UUID
    intent: str
    initial_time: str
    final_time: str
    confirmed_facts: tuple[str, ...]


class ActionFlowResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    simulation_run_id: UUID
    presentation_id: UUID
    content: str
    idempotent_replay: bool = False
