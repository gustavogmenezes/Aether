from enum import Enum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class InferenceProviderKind(str, Enum):
    OLLAMA = "ollama"
    OPENAI_COMPATIBLE = "openai-compatible"


class InferenceMessage(BaseModel):
    model_config = ConfigDict(frozen=True)

    role: str
    content: str


class InferenceRequest(BaseModel):
    model_config = ConfigDict(frozen=True)

    request_id: UUID
    capability: str
    model: str
    messages: tuple[InferenceMessage, ...]
    temperature: float = Field(default=0, ge=0, le=2)
    max_output_tokens: int | None = Field(default=None, gt=0)
    response_schema: dict[str, object] | None = None


class InferenceResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    request_id: UUID
    provider: InferenceProviderKind
    model: str
    content: str
    prompt_tokens: int | None = None
    output_tokens: int | None = None
    duration_seconds: float
