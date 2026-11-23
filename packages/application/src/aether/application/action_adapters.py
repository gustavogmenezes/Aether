import hashlib
import re
from datetime import UTC, datetime
from uuid import uuid4

from aether.contracts import (
    ActionKind,
    ActionProposal,
    ActionValidationResult,
    GameMasterContext,
    GameMasterResult,
    NarrativeContext,
    NarrativeDelivery,
    NarrativeDraft,
    PlayerInput,
)


class DeterministicGameMaster:
    _WAIT_PATTERN = re.compile(
        r"^\s*(?:wait|rest)(?:\s+for)?\s+(\d+)\s+"
        r"(second|seconds|minute|minutes|hour|hours)\s*$",
        re.IGNORECASE,
    )
    _MULTIPLIERS = {
        "second": 1,
        "seconds": 1,
        "minute": 60,
        "minutes": 60,
        "hour": 3600,
        "hours": 3600,
    }

    def interpret(self, context: GameMasterContext) -> GameMasterResult:
        now = datetime.now(UTC)
        match = self._WAIT_PATTERN.fullmatch(context.player_input.text)
        if match is None:
            raise ValueError(
                "Deterministic Game Master supports 'wait for <n> "
                "seconds|minutes|hours' only"
            )
        amount = int(match.group(1))
        duration = amount * self._MULTIPLIERS[match.group(2).lower()]
        invocation_id = uuid4()
        proposal = ActionProposal(
            proposal_id=uuid4(),
            invocation_id=invocation_id,
            action_kind=ActionKind.INTERVAL,
            intent=f"wait for {amount} {match.group(2).lower()}",
            duration_seconds=duration,
            targets=(),
        )
        canonical_context = (
            f"{context.player_input.model_dump_json()}|{context.current_world_time.isoformat()}"
        )
        context_hash = hashlib.sha256(canonical_context.encode()).hexdigest()
        return GameMasterResult(
            invocation_id=invocation_id,
            proposal=proposal,
            model="deterministic-command-parser",
            model_version="1",
            prompt_version="command-wait-v1",
            context_hash=context_hash,
            inference_parameters={},
            raw_response_reference=f"inline:{proposal.model_dump_json()}",
            created_at=now,
            completed_at=now,
        )


class DeterministicActionValidator:
    def validate(
        self,
        player_input: PlayerInput,
        proposal: ActionProposal,
    ) -> ActionValidationResult:
        if proposal.action_kind == ActionKind.INTERVAL and proposal.duration_seconds <= 0:
            return ActionValidationResult(
                accepted=False,
                duration_seconds=0,
                rejection_reason="Interval actions must consume positive world time",
            )
        if proposal.requires_player_approval:
            return ActionValidationResult(
                accepted=False,
                duration_seconds=proposal.duration_seconds,
                rejection_reason="Player approval is required before this action can run",
                requires_player_approval=True,
            )
        return ActionValidationResult(
            accepted=True,
            duration_seconds=proposal.duration_seconds,
            confirmed_facts=(
                f"intent:{proposal.intent}",
                f"duration-seconds:{proposal.duration_seconds}",
            ),
        )


class TemplateNarrator:
    def narrate(self, context: NarrativeContext) -> NarrativeDraft:
        result = context.confirmed_action
        content = (
            f"{result.intent.capitalize()}. World time moves from "
            f"{result.initial_time} to {result.final_time}, and the action completes "
            "without the narrator inventing an additional mechanical outcome."
        )
        return NarrativeDraft(
            presentation_id=uuid4(),
            simulation_run_id=result.simulation_run_id,
            content=content,
            claims_supported_by_facts=context.confirmed_facts,
        )


class DirectPresentationDelivery:
    def deliver(self, draft: NarrativeDraft) -> NarrativeDelivery:
        return NarrativeDelivery(
            delivered_content=draft.content,
            delivered_claim_ids=draft.claims_supported_by_facts,
        )
