import json
from uuid import uuid4

from pydantic import ValidationError

from aether.contracts import (
    InferenceMessage,
    InferenceRequest,
    NarrativeContext,
    NarrativeDraft,
)
from aether.domain import InferenceProviderPort


class OllamaNarrator:
    def __init__(
        self,
        provider: InferenceProviderPort,
        model: str,
    ) -> None:
        self._provider = provider
        self._model = model

    def narrate(self, context: NarrativeContext) -> NarrativeDraft:
        result = self._provider.generate(
            InferenceRequest(
                request_id=uuid4(),
                capability="literary-narration",
                model=self._model,
                messages=(
                    InferenceMessage(
                        role="system",
                        content=(
                            "Write literary narrative restricted to confirmed facts "
                            "and the supplied character knowledge. Return only JSON "
                            "with content and claims_supported_by_facts. Do not "
                            "invent mechanical outcomes or off-screen knowledge."
                        ),
                    ),
                    InferenceMessage(
                        role="user",
                        content=context.model_dump_json(),
                    ),
                ),
                response_schema={
                    "type": "object",
                    "properties": {
                        "content": {"type": "string"},
                        "claims_supported_by_facts": {
                            "type": "array",
                            "items": {"type": "string"},
                        },
                    },
                    "required": ["content", "claims_supported_by_facts"],
                },
            )
        )
        try:
            content = json.loads(result.content)
            return NarrativeDraft(
                presentation_id=uuid4(),
                simulation_run_id=context.confirmed_action.simulation_run_id,
                content=content["content"],
                claims_supported_by_facts=tuple(
                    content["claims_supported_by_facts"]
                ),
            )
        except (json.JSONDecodeError, KeyError, TypeError, ValidationError) as error:
            raise ValueError("Narrator provider output is not a valid draft") from error
