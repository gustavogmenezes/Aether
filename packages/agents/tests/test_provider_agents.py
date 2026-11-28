import json
from datetime import UTC, datetime
from uuid import uuid4

import pytest

from aether.agents import OllamaGameMaster, OllamaNarrator
from aether.contracts import (
    ConfirmedActionResult,
    ExperienceMode,
    GameMasterContext,
    InferenceProviderKind,
    InferenceRequest,
    InferenceResult,
    NarrativeContext,
    PlayerInput,
)


class FakeProvider:
    def __init__(self, content: str) -> None:
        self.content = content
        self.requests: list[InferenceRequest] = []

    def generate(self, request: InferenceRequest) -> InferenceResult:
        self.requests.append(request)
        return InferenceResult(
            request_id=request.request_id,
            provider=InferenceProviderKind.OLLAMA,
            model=request.model,
            content=self.content,
            prompt_tokens=12,
            output_tokens=8,
            duration_seconds=0.5,
        )

    def list_models(self) -> tuple[str, ...]:
        return ("chosen-model",)

    def health(self) -> bool:
        return True


def context() -> GameMasterContext:
    now = datetime(2026, 12, 1, tzinfo=UTC)
    return GameMasterContext(
        player_input=PlayerInput(
            input_id=uuid4(),
            simulation_run_id=uuid4(),
            world_id=uuid4(),
            timeline_id=uuid4(),
            protagonist_character_id=uuid4(),
            mode=ExperienceMode.PLAYER_CHARACTER,
            text="wait for five minutes",
        ),
        current_world_time=now,
    )


def test_game_master_maps_structured_provider_output_to_proposal() -> None:
    provider = FakeProvider(
        json.dumps(
            {
                "intent": "wait for five minutes",
                "action_kind": "interval",
                "duration_seconds": 300,
                "targets": [],
                "requires_player_approval": False,
                "unverified_details": [],
            }
        )
    )
    result = OllamaGameMaster(provider, "chosen-model").interpret(context())

    assert result.proposal.duration_seconds == 300
    assert result.model == "chosen-model"
    assert provider.requests[0].response_schema is not None


def test_game_master_rejects_malformed_provider_output() -> None:
    provider = FakeProvider('{"intent": "wait"}')

    with pytest.raises(ValueError, match="valid proposal"):
        OllamaGameMaster(provider, "chosen-model").interpret(context())


def test_narrator_returns_only_confirmed_claim_contract() -> None:
    fact = "world-time:2026-12-01T00:05:00+00:00"
    provider = FakeProvider(
        json.dumps(
            {
                "content": "Five minutes pass in stillness.",
                "claims_supported_by_facts": [fact],
            }
        )
    )
    now = datetime(2026, 12, 1, tzinfo=UTC)
    narrative_context = NarrativeContext(
        confirmed_action=ConfirmedActionResult(
            simulation_run_id=uuid4(),
            protagonist_character_id=uuid4(),
            intent="wait for five minutes",
            initial_time=now.isoformat(),
            final_time=now.isoformat(),
            confirmed_facts=(fact,),
        ),
        confirmed_facts=(fact,),
    )

    draft = OllamaNarrator(provider, "chosen-model").narrate(narrative_context)

    assert draft.claims_supported_by_facts == (fact,)
    assert draft.content
