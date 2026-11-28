import hashlib
import json
from datetime import UTC, datetime
from uuid import uuid4

from pydantic import ValidationError

from aether.contracts import (
    ActionKind,
    ActionProposal,
    GameMasterContext,
    GameMasterResult,
    InferenceMessage,
    InferenceProviderKind,
    InferenceRequest,
)
from aether.domain import InferenceProviderPort


class OllamaGameMaster:
    def __init__(
        self,
        provider: InferenceProviderPort,
        model: str,
        prompt_version: str = "game-master-v1",
    ) -> None:
        self._provider = provider
        self._model = model
        self._prompt_version = prompt_version

    def interpret(self, context: GameMasterContext) -> GameMasterResult:
        request_id = uuid4()
        invocation_id = uuid4()
        context_json = context.model_dump_json()
        result = self._provider.generate(
            InferenceRequest(
                request_id=request_id,
                capability="action-interpretation",
                model=self._model,
                messages=(
                    InferenceMessage(
                        role="system",
                        content=(
                            "You interpret a player intention into an Action Proposal. "
                            "Return only JSON with intent, action_kind, "
                            "duration_seconds, targets, "
                            "requires_player_approval, and unverified_details. "
                            "Never invent a mechanical result."
                        ),
                    ),
                    InferenceMessage(role="user", content=context_json),
                ),
                response_schema={
                    "type": "object",
                    "properties": {
                        "intent": {"type": "string"},
                        "action_kind": {
                            "type": "string",
                            "enum": [kind.value for kind in ActionKind],
                        },
                        "duration_seconds": {"type": "integer", "minimum": 0},
                        "targets": {"type": "array", "items": {"type": "string"}},
                        "requires_player_approval": {"type": "boolean"},
                        "unverified_details": {
                            "type": "array",
                            "items": {"type": "string"},
                        },
                    },
                    "required": [
                        "intent",
                        "action_kind",
                        "duration_seconds",
                    ],
                },
            )
        )
        if result.provider not in {
            InferenceProviderKind.OLLAMA,
            InferenceProviderKind.OPENAI_COMPATIBLE,
        }:
            raise ValueError("Unsupported inference provider for Game Master")
        try:
            content = json.loads(result.content)
            proposal = ActionProposal.model_validate(
                {
                    "proposal_id": uuid4(),
                    "invocation_id": invocation_id,
                    **content,
                }
            )
        except (json.JSONDecodeError, ValidationError) as error:
            raise ValueError("Game Master provider output is not a valid proposal") from error
        completed_at = datetime.now(UTC)
        return GameMasterResult(
            invocation_id=invocation_id,
            proposal=proposal,
            requesting_agent="GameMaster",
            requested_capability="action-interpretation",
            model=result.model,
            model_version=result.provider.value,
            prompt_version=self._prompt_version,
            context_hash=hashlib.sha256(context_json.encode()).hexdigest(),
            inference_parameters={"temperature": 0},
            raw_response_reference=f"inline:{result.content}",
            created_at=completed_at,
            completed_at=completed_at,
        )
