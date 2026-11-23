from typing import Protocol
from uuid import UUID

from aether.contracts import (
    ActionProposal,
    ActionValidationResult,
    GameMasterContext,
    GameMasterResult,
    NarrativeContext,
    NarrativeDelivery,
    NarrativeDraft,
    PlayerInput,
    PresentationRecord,
)


class GameMasterPort(Protocol):
    def interpret(self, context: GameMasterContext) -> GameMasterResult: ...


class ActionValidationPort(Protocol):
    def validate(
        self,
        player_input: PlayerInput,
        proposal: ActionProposal,
    ) -> ActionValidationResult: ...


class NarratorPort(Protocol):
    def narrate(self, context: NarrativeContext) -> NarrativeDraft: ...


class PresentationDeliveryPort(Protocol):
    def deliver(self, draft: NarrativeDraft) -> NarrativeDelivery: ...


class PresentationRepository(Protocol):
    def create_presentation(self, presentation: PresentationRecord) -> None: ...

    def get_presentation(self, presentation_id: UUID) -> PresentationRecord | None: ...

    def get_presentation_by_run(
        self,
        simulation_run_id: UUID,
    ) -> PresentationRecord | None: ...

    def save_presentation(self, presentation: PresentationRecord) -> None: ...
