from collections.abc import Callable
from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID, uuid5

from aether.contracts import (
    OrganizationDecisionContext,
    OrganizationDecisionProposal,
    OrganizationDecisionProposalStatus,
    OrganizationDecisionResult,
    OrganizationDecisionType,
    OrganizationPlanStep,
    OrganizationPlanStepScheduleResult,
    RecordProvenance,
    ResourceAvailability,
    ResourceEffectOutcome,
    ResourceOwnerKind,
    ResourceReservation,
    ScheduledEvent,
    organization_context_hash,
)
from aether.domain import (
    OrganizationAuthorityError,
    OrganizationDecisionConflictError,
    OrganizationDecisionPort,
    OrganizationDecisionValidationError,
    PlanStepSchedulingRejectedError,
    validate_organization_authority,
)
from aether.domain.ports import SimulationUnitOfWorkFactory
from aether.engines import DeterministicOrganizationDecisionEngine


class OrganizationDecisionService:
    def __init__(
        self,
        unit_of_work_factory: SimulationUnitOfWorkFactory,
        *,
        decision_port: OrganizationDecisionPort | None = None,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self._unit_of_work_factory = unit_of_work_factory
        self._decision_port = decision_port or DeterministicOrganizationDecisionEngine()
        self._clock = clock or (lambda: datetime.now(UTC))

    def propose(
        self, context: OrganizationDecisionContext
    ) -> OrganizationDecisionResult:
        context_hash = organization_context_hash(context)
        with self._unit_of_work_factory() as unit_of_work:
            existing = unit_of_work.repository.get_organization_decision_by_request(
                context.request_id
            )
            if existing is not None:
                if existing.context_hash != context_hash:
                    raise OrganizationDecisionConflictError(
                        "Organization decision request ID belongs to another context"
                    )
                return OrganizationDecisionResult(
                    proposal=existing, idempotent_replay=True
                )

        draft = self._decision_port.propose(context)
        rejection_reason = self._validate_proposal(context, draft)
        proposal = draft.model_copy(
            update={
                "status": (
                    OrganizationDecisionProposalStatus.REJECTED
                    if rejection_reason
                    else OrganizationDecisionProposalStatus.VALIDATED
                ),
                "rejection_reason": rejection_reason,
                "context_hash": context_hash,
            }
        )
        with self._unit_of_work_factory() as unit_of_work:
            unit_of_work.repository.create_organization_decision(
                proposal, context=context
            )
            unit_of_work.commit()
        return OrganizationDecisionResult(proposal=proposal)

    def schedule_validated_step(
        self,
        proposal_id: UUID,
        *,
        world_id: UUID,
        timeline_id: UUID,
        scheduled_at: datetime,
    ) -> OrganizationPlanStepScheduleResult:
        if scheduled_at.tzinfo is None or scheduled_at.utcoffset() is None:
            raise ValueError("Scheduled organization step time needs a UTC offset")
        with self._unit_of_work_factory() as unit_of_work:
            proposal = unit_of_work.repository.get_organization_decision(proposal_id)
            context = unit_of_work.repository.get_organization_decision_context(
                proposal_id
            )
            if proposal is None or context is None:
                raise OrganizationDecisionValidationError(
                    "Organization decision proposal was not found"
                )
            if proposal.status != OrganizationDecisionProposalStatus.VALIDATED:
                raise OrganizationDecisionValidationError(
                    "Organization decision proposal is not valid"
                )
            if proposal.application_result is not None:
                if (
                    proposal.application_result.get("world_id") != str(world_id)
                    or proposal.application_result.get("timeline_id")
                    != str(timeline_id)
                ):
                    raise OrganizationDecisionConflictError(
                        "Organization decision is scheduled in another timeline"
                    )
                return OrganizationPlanStepScheduleResult(
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
                proposal.decision_type
                != OrganizationDecisionType.EXECUTE_PLAN_STEP
                or proposal.target_plan_step_id is None
            ):
                raise OrganizationDecisionValidationError(
                    "Decision does not authorize an organization plan step"
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
            stored_step = unit_of_work.repository.get_organization_plan_step(
                proposal.target_plan_step_id
            )
            if step is None or stored_step is None or stored_step != step:
                raise OrganizationDecisionValidationError(
                    "Organization plan step no longer matches the decision context"
                )
            responsible_id = proposal.responsible_character_id
            if responsible_id is None:
                raise OrganizationAuthorityError(
                    "An executable organization step requires a responsible member"
                )
            self._validate_authority(
                unit_of_work.repository,
                proposal.organization_id,
                responsible_id,
                step,
            )
            missing = self._missing_prerequisites(context, step)
            if missing:
                raise PlanStepSchedulingRejectedError(
                    "Organization plan step prerequisites unavailable: "
                    + ", ".join(missing)
                )
            clock = unit_of_work.repository.get_clock(world_id, timeline_id)
            if clock is None:
                raise OrganizationDecisionValidationError(
                    "World clock was not found"
                )
            if clock.current_time != context.as_of:
                raise OrganizationDecisionValidationError(
                    "World time changed after the organization decision"
                )
            if scheduled_at <= clock.current_time:
                raise OrganizationDecisionValidationError(
                    "Organization step must be scheduled after current world time"
                )

            event_id = uuid5(
                UUID("7b4f3d7e-9dbd-43c9-9e4e-0c9a0f5d31a8"),
                str(proposal.proposal_id),
            )
            if unit_of_work.repository.get_scheduled_event(event_id) is not None:
                raise OrganizationDecisionConflictError(
                    "Organization scheduled event ID is already in use"
                )
            event = ScheduledEvent(
                event_id=event_id,
                world_id=world_id,
                timeline_id=timeline_id,
                scheduled_at=scheduled_at,
                event_type="organization-plan-step",
                source_type="organization-decision",
                source_id=str(proposal.proposal_id),
                payload_version="1",
                payload={
                    "organization_id": str(proposal.organization_id),
                    "responsible_character_id": str(responsible_id),
                    "plan_step_id": str(step.step_id),
                    "decision_proposal_id": str(proposal.proposal_id),
                },
            )
            for reservation in self._resource_reservations(
                event_id, proposal.organization_id, step
            ):
                unit_of_work.repository.reserve_resource(reservation)
            unit_of_work.repository.schedule_event(event)
            unit_of_work.repository.mark_organization_plan_step_scheduled(
                step.step_id
            )
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
            unit_of_work.repository.save_organization_decision_application(applied)
            unit_of_work.commit()
            return OrganizationPlanStepScheduleResult(
                proposal_id=proposal.proposal_id,
                plan_step_id=step.step_id,
                scheduled_event_id=event_id,
            )

    def persisted_resource_availability(
        self, organization_id: UUID, resource_codes: tuple[str, ...]
    ) -> tuple[ResourceAvailability, ...]:
        with self._unit_of_work_factory() as unit_of_work:
            return tuple(
                ResourceAvailability(
                    name=code,
                    available=(
                        unit_of_work.repository.get_available_resource_quantity(
                            ResourceOwnerKind.ORGANIZATION,
                            organization_id,
                            code,
                        )
                        > 0
                    ),
                )
                for code in resource_codes
            )

    @staticmethod
    def _validate_proposal(
        context: OrganizationDecisionContext,
        proposal: OrganizationDecisionProposal,
    ) -> str | None:
        if proposal.request_id != context.request_id:
            return "Proposal request ID does not match the supplied context"
        if proposal.organization_id != context.organization_id:
            return "Proposal organization ID does not match the supplied context"
        if context.identity.organization_id != context.organization_id:
            return "Organization identity belongs to another actor"
        owner_ids = (
            {context.governance.organization_id}
            | {item.organization_id for item in context.memberships}
            | {item.organization_id for item in context.authority_grants}
            | {item.organization_id for item in context.motives}
            | {item.organization_id for item in context.goals}
            | {item.plan.organization_id for item in context.plans}
        )
        if owner_ids != {context.organization_id}:
            return "Supplied context contains records for another organization"
        goal_ids = {goal.goal_id for goal in context.goals}
        for plan_context in context.plans:
            if plan_context.plan.goal_id not in goal_ids:
                return "Organization plan goal is absent from supplied context"
            if any(
                step.plan_id != plan_context.plan.plan_id
                for step in plan_context.steps
            ):
                return "Organization plan contains a step owned by another plan"
        if proposal.target_plan_step_id is None:
            if proposal.decision_type == OrganizationDecisionType.EXECUTE_PLAN_STEP:
                return "An executable organization decision requires a target step"
            return None
        step = next(
            (
                candidate
                for plan in context.plans
                for candidate in plan.steps
                if candidate.step_id == proposal.target_plan_step_id
            ),
            None,
        )
        if step is None:
            return "Target organization step is absent from supplied context"
        if proposal.responsible_character_id != step.responsible_character_id:
            return "Proposal responsible member does not match the target step"
        if proposal.required_resources != step.required_resources:
            return "Proposal resources do not match the target organization step"
        return None

    @staticmethod
    def _validate_authority(
        repository,
        organization_id: UUID,
        character_id: UUID,
        step: OrganizationPlanStep,
    ) -> None:
        membership = repository.get_organization_membership(
            organization_id, character_id
        )
        grants = repository.list_organization_authority_grants(
            organization_id, character_id
        )
        validate_organization_authority(membership, grants, step)

    @staticmethod
    def _missing_prerequisites(
        context: OrganizationDecisionContext,
        step: OrganizationPlanStep,
    ) -> tuple[str, ...]:
        capabilities = {
            item.name for item in context.capabilities if item.available
        }
        resources = {item.name for item in context.resources if item.available}
        facts = {
            item.fact_key for item in (*context.facts, *context.circumstances)
        }
        return tuple(
            sorted(
                {
                    *(f"capability:{name}" for name in step.required_capabilities
                      if name not in capabilities),
                    *(f"resource:{name}" for name in step.required_resources
                      if name not in resources),
                    *(f"knowledge:{name}" for name in step.required_knowledge_fact_keys
                      if name not in facts),
                }
            )
        )

    @staticmethod
    def _resource_reservations(
        scheduled_event_id: UUID,
        organization_id: UUID,
        step: OrganizationPlanStep,
    ) -> tuple[ResourceReservation, ...]:
        by_outcome: dict[ResourceEffectOutcome, dict[str, Decimal]] = {}
        for effect in step.resource_effects:
            if effect.delta >= 0:
                continue
            values = by_outcome.setdefault(effect.on_outcome, {})
            values[effect.resource_code] = (
                values.get(effect.resource_code, Decimal(0)) - effect.delta
            )
        maximum: dict[str, Decimal] = {}
        for values in by_outcome.values():
            for code, quantity in values.items():
                maximum[code] = max(maximum.get(code, Decimal(0)), quantity)
        return tuple(
            ResourceReservation(
                reservation_id=uuid5(
                    UUID("dce0d2c6-4cbe-4ee4-8bb2-6e7e0f3c8a52"),
                    f"{scheduled_event_id}:{code}",
                ),
                scheduled_event_id=scheduled_event_id,
                owner_kind=ResourceOwnerKind.ORGANIZATION,
                owner_id=organization_id,
                resource_code=code,
                quantity=quantity,
            )
            for code, quantity in sorted(maximum.items())
        )
