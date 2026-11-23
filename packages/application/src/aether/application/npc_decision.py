from collections.abc import Callable
from datetime import UTC, datetime
from hashlib import sha256
from uuid import UUID, uuid5
from decimal import Decimal

from aether.contracts import (
    NpcDecisionContext,
    NpcDecisionProposal,
    NpcDecisionProposalStatus,
    NpcDecisionResult,
    NpcDecisionType,
    PlanStep,
    PlanStepScheduleResult,
    RecordProvenance,
    ScheduledEvent,
    ResourceOwnerKind,
    ResourceReservation,
    ResourceAvailability,
)
from aether.domain import (
    NpcDecisionConflictError,
    NpcDecisionPort,
    NpcDecisionValidationError,
    PlanStepSchedulingRejectedError,
)
from aether.domain.ports import SimulationUnitOfWorkFactory
from aether.engines import DeterministicNpcDecisionEngine


class NpcDecisionService:
    def __init__(
        self,
        unit_of_work_factory: SimulationUnitOfWorkFactory,
        *,
        decision_port: NpcDecisionPort | None = None,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self._unit_of_work_factory = unit_of_work_factory
        self._decision_port = decision_port or DeterministicNpcDecisionEngine()
        self._clock = clock or (lambda: datetime.now(UTC))

    def propose(self, context: NpcDecisionContext) -> NpcDecisionResult:
        context_hash = self._context_hash(context)
        with self._unit_of_work_factory() as unit_of_work:
            existing = unit_of_work.repository.get_npc_decision_by_request(
                context.request_id
            )
            if existing is not None:
                if existing.context_hash != context_hash:
                    raise NpcDecisionConflictError(
                        "Decision request ID is already associated with another context"
                    )
                return NpcDecisionResult(
                    proposal=existing,
                    idempotent_replay=True,
                )

        draft = self._decision_port.propose(context)
        rejection_reason = self._validate_proposal(context, draft)
        proposal = draft.model_copy(
            update={
                "status": (
                    NpcDecisionProposalStatus.REJECTED
                    if rejection_reason
                    else NpcDecisionProposalStatus.VALIDATED
                ),
                "rejection_reason": rejection_reason,
                "context_hash": context_hash,
            }
        )
        with self._unit_of_work_factory() as unit_of_work:
            unit_of_work.repository.create_npc_decision(proposal, context=context)
            unit_of_work.commit()
        return NpcDecisionResult(proposal=proposal)

    def schedule_validated_step(
        self,
        proposal_id: UUID,
        *,
        world_id: UUID,
        timeline_id: UUID,
        scheduled_at: datetime,
    ) -> PlanStepScheduleResult:
        if scheduled_at.tzinfo is None or scheduled_at.utcoffset() is None:
            raise ValueError("Scheduled plan-step time must include a UTC offset")
        with self._unit_of_work_factory() as unit_of_work:
            proposal = unit_of_work.repository.get_npc_decision(proposal_id)
            context = unit_of_work.repository.get_npc_decision_context(proposal_id)
            if proposal is None or context is None:
                raise NpcDecisionValidationError("NPC decision proposal was not found")
            if proposal.status != NpcDecisionProposalStatus.VALIDATED:
                raise NpcDecisionValidationError("NPC decision proposal is not valid")
            if proposal.application_result is not None:
                if (
                    proposal.application_result.get("world_id") != str(world_id)
                    or proposal.application_result.get("timeline_id")
                    != str(timeline_id)
                ):
                    raise NpcDecisionConflictError(
                        "Decision is already scheduled in another world or timeline"
                    )
                return PlanStepScheduleResult(
                    proposal_id=proposal.proposal_id,
                    plan_step_id=UUID(
                        proposal.application_result["plan_step_id"]
                    ),
                    scheduled_event_id=UUID(
                        proposal.application_result["scheduled_event_id"]
                    ),
                    idempotent_replay=True,
                )
            if (
                proposal.decision_type != NpcDecisionType.EXECUTE_PLAN_STEP
                or proposal.target_plan_step_id is None
            ):
                raise NpcDecisionValidationError(
                    "Decision does not authorize a plan-step schedule"
                )
            step = next(
                (
                    candidate
                    for plan in context.plans
                    for candidate in plan.steps
                    if candidate.step_id == proposal.target_plan_step_id
                ),
                None,
            )
            stored_step = unit_of_work.repository.get_plan_step(
                proposal.target_plan_step_id
            )
            if step is None or stored_step is None or stored_step != step:
                raise NpcDecisionValidationError(
                    "Target plan step no longer matches the validated context"
                )
            clock = unit_of_work.repository.get_clock(world_id, timeline_id)
            if clock is None:
                raise NpcDecisionValidationError("World clock was not found")
            if clock.current_time != context.as_of:
                raise NpcDecisionValidationError(
                    "World time changed after the decision proposal"
                )
            if scheduled_at <= clock.current_time:
                raise NpcDecisionValidationError(
                    "Plan-step schedule must be later than the current world time"
                )
            missing = self._missing_prerequisites(context, step)
            if missing:
                raise PlanStepSchedulingRejectedError(
                    "Plan step prerequisites are unavailable: " + ", ".join(missing)
                )
            event_id = uuid5(
                UUID("40b37ed8-f32a-4a85-b8f3-91c9c6dc9a8d"),
                str(proposal.proposal_id),
            )
            existing_event = unit_of_work.repository.get_scheduled_event(event_id)
            if existing_event is not None:
                raise NpcDecisionConflictError(
                    "Scheduled event ID is already used by another operation"
                )
            event = ScheduledEvent(
                event_id=event_id,
                world_id=world_id,
                timeline_id=timeline_id,
                scheduled_at=scheduled_at,
                event_type="npc-plan-step",
                source_type="npc-decision",
                source_id=str(proposal.proposal_id),
                payload_version="1",
                payload={
                    "character_id": str(proposal.character_id),
                    "plan_step_id": str(step.step_id),
                    "decision_proposal_id": str(proposal.proposal_id),
                },
            )
            reservations = self._resource_reservations(
                event.event_id,
                proposal.character_id,
                step,
            )
            for reservation in reservations:
                unit_of_work.repository.reserve_resource(reservation)
            unit_of_work.repository.schedule_event(event)
            unit_of_work.repository.mark_plan_step_scheduled(step.step_id)
            applied = proposal.model_copy(
                update={
                    "application_result": {
                        "scheduled_event_id": str(event_id),
                        "plan_step_id": str(step.step_id),
                        "world_id": str(world_id),
                        "timeline_id": str(timeline_id),
                    },
                    "provenance": RecordProvenance(
                        source_type=proposal.provenance.source_type,
                        source_id=proposal.provenance.source_id,
                        origin_event_id=proposal.provenance.origin_event_id,
                        created_at=proposal.provenance.created_at,
                        updated_at=self._clock(),
                        version=proposal.provenance.version + 1,
                    ),
                }
            )
            unit_of_work.repository.save_npc_decision_application(applied)
            unit_of_work.commit()
            return PlanStepScheduleResult(
                proposal_id=proposal.proposal_id,
                plan_step_id=step.step_id,
                scheduled_event_id=event_id,
            )

    def persisted_resource_availability(
        self,
        character_id: UUID,
        resource_codes: tuple[str, ...],
    ) -> tuple[ResourceAvailability, ...]:
        with self._unit_of_work_factory() as unit_of_work:
            return tuple(
                ResourceAvailability(
                    name=code,
                    available=(
                        unit_of_work.repository.get_available_resource_quantity(
                            ResourceOwnerKind.CHARACTER,
                            character_id,
                            code,
                        )
                        > 0
                    ),
                )
                for code in resource_codes
            )

    @staticmethod
    def _validate_proposal(
        context: NpcDecisionContext,
        proposal: NpcDecisionProposal,
    ) -> str | None:
        if proposal.request_id != context.request_id:
            return "Proposal request ID does not match the supplied context"
        if proposal.character_id != context.character_id:
            return "Proposal character ID does not match the supplied context"
        context_character_ids = (
            {context.identity.character_id}
            | ({context.personality.character_id} if context.personality else set())
            | (
                {context.psychological_state.character_id}
                if context.psychological_state
                else set()
            )
            | {item.character_id for item in context.motives}
            | {item.character_id for item in context.goals}
            | {item.plan.character_id for item in context.plans}
            | {item.source_character_id for item in context.relationships}
        )
        if context_character_ids != {context.character_id}:
            return "Supplied context contains records for another character"
        goal_ids = {goal.goal_id for goal in context.goals}
        motive_ids = {motive.motive_id for motive in context.motives}
        for goal in context.goals:
            if goal.motive_id is not None and goal.motive_id not in motive_ids:
                return "Goal motive is absent from supplied context"
            if goal.parent_goal_id is not None and goal.parent_goal_id not in goal_ids:
                return "Parent goal is absent from supplied context"
        for plan_context in context.plans:
            if plan_context.plan.goal_id not in goal_ids:
                return "Plan goal is absent from supplied context"
            if any(
                step.plan_id != plan_context.plan.plan_id
                for step in plan_context.steps
            ):
                return "Plan contains a step owned by another plan"
        if proposal.target_plan_step_id is not None:
            step_ids = {
                step.step_id
                for plan in context.plans
                for step in plan.steps
            }
            if proposal.target_plan_step_id not in step_ids:
                return "Target plan step is absent from supplied context"
            target_step = next(
                step
                for plan_context in context.plans
                for step in plan_context.steps
                if step.step_id == proposal.target_plan_step_id
            )
            if proposal.required_resources != target_step.required_resources:
                return "Proposal resource requirements do not match the target step"
        elif proposal.decision_type == NpcDecisionType.EXECUTE_PLAN_STEP:
            return "An executable decision requires a target plan step"
        return None

    @staticmethod
    def _missing_prerequisites(
        context: NpcDecisionContext,
        step: PlanStep,
    ) -> tuple[str, ...]:
        capabilities = {item.name for item in context.capabilities if item.available}
        resources = {item.name for item in context.resources if item.available}
        knowledge = {item.fact_key for item in context.knowledge}
        return tuple(
            sorted(
                {
                    *(
                        f"capability:{name}"
                        for name in step.required_capabilities
                        if name not in capabilities
                    ),
                    *(
                        f"resource:{name}"
                        for name in step.required_resources
                        if name not in resources
                    ),
                    *(
                        f"knowledge:{name}"
                        for name in step.required_knowledge_fact_keys
                        if name not in knowledge
                    ),
                }
            )
        )

    @staticmethod
    def _resource_reservations(
        scheduled_event_id: UUID,
        character_id: UUID,
        step: PlanStep,
    ) -> tuple[ResourceReservation, ...]:
        consumption_by_outcome: dict[object, dict[str, Decimal]] = {}
        for effect in step.resource_effects:
            if effect.delta >= 0:
                continue
            outcome = consumption_by_outcome.setdefault(effect.on_outcome, {})
            outcome[effect.resource_code] = (
                outcome.get(effect.resource_code, Decimal(0)) - effect.delta
            )
        maximum_by_code: dict[str, Decimal] = {}
        for outcome_effects in consumption_by_outcome.values():
            for code, quantity in outcome_effects.items():
                maximum_by_code[code] = max(
                    maximum_by_code.get(code, Decimal(0)),
                    quantity,
                )
        return tuple(
            ResourceReservation(
                reservation_id=uuid5(
                    UUID("9a0c9b98-e9bf-4b9a-88be-b25fca53f2cc"),
                    f"{scheduled_event_id}:{code}",
                ),
                scheduled_event_id=scheduled_event_id,
                owner_kind=ResourceOwnerKind.CHARACTER,
                owner_id=character_id,
                resource_code=code,
                quantity=quantity,
            )
            for code, quantity in sorted(maximum_by_code.items())
        )

    @staticmethod
    def _context_hash(context: NpcDecisionContext) -> str:
        return sha256(context.model_dump_json().encode("utf-8")).hexdigest()
