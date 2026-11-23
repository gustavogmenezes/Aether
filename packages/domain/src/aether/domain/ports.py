from datetime import datetime
from types import TracebackType
from typing import Protocol, Self
from uuid import UUID
from decimal import Decimal

from aether.contracts import (
    AgentProposalRecord,
    CharacterIdentity,
    CharacterKnowledgeRecord,
    EventEnvelope,
    Goal,
    InformationTransmission,
    KnowledgeContextEntry,
    LlmInvocationRecord,
    Motive,
    NpcDecisionContext,
    NpcDecisionProposal,
    NarrativeStateRecord,
    PersonalityProfile,
    Plan,
    PlanStep,
    PlayerKnowledgeRecord,
    PresentationRecord,
    PsychologicalState,
    Relationship,
    ResourceBalance,
    ResourceOwnerKind,
    ResourceReservation,
    ResourceTransaction,
    ScheduledEvent,
    SimulationRunRecord,
    SimulationRunStatus,
)

from .simulation import ScheduledEventStatus, WorldClockState


class SimulationRepository(Protocol):
    def get_clock(self, world_id: UUID, timeline_id: UUID) -> WorldClockState | None: ...

    def save_clock(
        self,
        clock: WorldClockState,
        expected_version: int,
    ) -> None: ...

    def get_run(self, simulation_run_id: UUID) -> SimulationRunRecord | None: ...

    def create_run(self, run: SimulationRunRecord) -> None: ...

    def update_run(
        self,
        simulation_run_id: UUID,
        *,
        status: SimulationRunStatus,
        final_time: datetime | None = None,
        processed_event_ids: tuple[UUID, ...] | None = None,
        error: str | None = None,
    ) -> SimulationRunRecord: ...

    def get_scheduled_event(self, event_id: UUID) -> ScheduledEvent | None: ...

    def schedule_event(self, event: ScheduledEvent) -> None: ...

    def get_scheduled_event_status(
        self,
        event_id: UUID,
    ) -> ScheduledEventStatus | None: ...

    def list_due_scheduled_events(
        self,
        world_id: UUID,
        timeline_id: UUID,
        after: datetime,
        through: datetime,
    ) -> tuple[ScheduledEvent, ...]: ...

    def mark_scheduled_event_completed(self, event_id: UUID) -> None: ...

    def mark_scheduled_event_failed(self, event_id: UUID, error: str) -> None: ...

    def get_latest_event_sequence(self, world_id: UUID, timeline_id: UUID) -> int: ...

    def append_event(self, event: EventEnvelope) -> None: ...

    def create_invocation(self, invocation: LlmInvocationRecord) -> None: ...

    def get_invocation(self, invocation_id: UUID) -> LlmInvocationRecord | None: ...

    def create_proposal(self, proposal: AgentProposalRecord) -> None: ...

    def get_proposal(self, proposal_id: UUID) -> AgentProposalRecord | None: ...

    def get_proposals_by_run(
        self,
        simulation_run_id: UUID,
    ) -> tuple[AgentProposalRecord, ...]: ...

    def create_presentation(self, presentation: PresentationRecord) -> None: ...

    def get_presentation(self, presentation_id: UUID) -> PresentationRecord | None: ...

    def get_presentation_by_run(
        self,
        simulation_run_id: UUID,
    ) -> PresentationRecord | None: ...

    def save_presentation(self, presentation: PresentationRecord) -> None: ...

    def create_player_knowledge(self, knowledge: PlayerKnowledgeRecord) -> None: ...

    def create_narrative_state(self, state: NarrativeStateRecord) -> None: ...

    def create_character_knowledge(
        self,
        knowledge: CharacterKnowledgeRecord,
    ) -> None: ...

    def list_character_knowledge(
        self,
        character_id: UUID,
        *,
        as_of: datetime,
    ) -> tuple[KnowledgeContextEntry, ...]: ...

    def create_transmission(
        self,
        transmission: InformationTransmission,
    ) -> None: ...

    def list_due_transmissions(
        self,
        through: datetime,
        *,
        after: datetime,
    ) -> tuple[InformationTransmission, ...]: ...

    def mark_transmission_interpreted(self, transmission_id: UUID) -> None: ...

    def create_character_identity(self, identity: CharacterIdentity) -> None: ...

    def get_character_identity(
        self,
        character_id: UUID,
    ) -> CharacterIdentity | None: ...

    def create_personality_profile(self, profile: PersonalityProfile) -> None: ...

    def get_personality_profile(
        self,
        character_id: UUID,
    ) -> PersonalityProfile | None: ...

    def create_psychological_state(self, state: PsychologicalState) -> None: ...

    def get_psychological_state(
        self,
        character_id: UUID,
        *,
        as_of: datetime,
    ) -> PsychologicalState | None: ...

    def create_relationship(self, relationship: Relationship) -> None: ...

    def list_relationships(
        self,
        character_id: UUID,
    ) -> tuple[Relationship, ...]: ...

    def create_motive(self, motive: Motive) -> None: ...

    def get_motive(self, motive_id: UUID) -> Motive | None: ...

    def create_goal(self, goal: Goal) -> None: ...

    def get_goal(self, goal_id: UUID) -> Goal | None: ...

    def create_plan(self, plan: Plan) -> None: ...

    def get_plan(self, plan_id: UUID) -> Plan | None: ...

    def create_plan_step(self, step: PlanStep) -> None: ...

    def get_plan_step(self, step_id: UUID) -> PlanStep | None: ...

    def mark_plan_step_scheduled(self, step_id: UUID) -> None: ...

    def mark_plan_step_completed(self, step_id: UUID) -> None: ...

    def mark_plan_step_failed(self, step_id: UUID, reason: str) -> None: ...

    def create_resource_balance(self, balance: ResourceBalance) -> None: ...

    def get_resource_balance(
        self,
        owner_kind: ResourceOwnerKind,
        owner_id: UUID,
        resource_code: str,
    ) -> ResourceBalance | None: ...

    def reserve_resource(
        self,
        reservation: ResourceReservation,
    ) -> None: ...

    def apply_resource_transaction(
        self,
        transaction: ResourceTransaction,
    ) -> None: ...

    def release_resource_reservation(
        self,
        reservation_id: UUID,
        *,
        cancelled: bool,
    ) -> None: ...

    def list_resource_reservations(
        self,
        scheduled_event_id: UUID,
    ) -> tuple[ResourceReservation, ...]: ...

    def list_resource_transactions(
        self,
        scheduled_event_id: UUID,
    ) -> tuple[ResourceTransaction, ...]: ...

    def get_available_resource_quantity(
        self,
        owner_kind: ResourceOwnerKind,
        owner_id: UUID,
        resource_code: str,
    ) -> Decimal: ...

    def create_npc_decision(
        self,
        proposal: NpcDecisionProposal,
        *,
        context: NpcDecisionContext,
    ) -> None: ...

    def get_npc_decision(
        self,
        proposal_id: UUID,
    ) -> NpcDecisionProposal | None: ...

    def get_npc_decision_by_request(
        self,
        request_id: UUID,
    ) -> NpcDecisionProposal | None: ...

    def get_npc_decision_context(
        self,
        proposal_id: UUID,
    ) -> NpcDecisionContext | None: ...

    def save_npc_decision_application(
        self,
        proposal: NpcDecisionProposal,
    ) -> None: ...


class SimulationUnitOfWork(Protocol):
    repository: SimulationRepository

    def __enter__(self) -> Self: ...

    def __exit__(
        self,
        exception_type: type[BaseException] | None,
        exception: BaseException | None,
        traceback: TracebackType | None,
    ) -> bool | None: ...

    def commit(self) -> None: ...


class SimulationUnitOfWorkFactory(Protocol):
    def __call__(self) -> SimulationUnitOfWork: ...
