from uuid import UUID, uuid5

from aether.contracts import (
    GoalStatus,
    OrganizationDecisionContext,
    OrganizationDecisionProposal,
    OrganizationDecisionType,
    PlanStatus,
    PlanStepStatus,
    RecordProvenance,
)


class DeterministicOrganizationDecisionEngine:
    """Proposes organization decisions using only supplied filtered facts."""

    def propose(
        self,
        context: OrganizationDecisionContext,
    ) -> OrganizationDecisionProposal:
        active_plans = sorted(
            (
                plan_context
                for plan_context in context.plans
                if plan_context.plan.organization_id == context.organization_id
                and plan_context.plan.status == PlanStatus.ACTIVE
            ),
            key=lambda item: (
                item.plan.provenance.created_at,
                str(item.plan.plan_id),
            ),
        )
        active_goal_ids = {
            goal.goal_id
            for goal in context.goals
            if goal.organization_id == context.organization_id
            and goal.status == GoalStatus.ACTIVE
        }
        target = None
        target_plan = None
        for plan_context in active_plans:
            if plan_context.plan.goal_id not in active_goal_ids:
                continue
            target = next(
                (
                    step
                    for step in sorted(
                        plan_context.steps,
                        key=lambda item: (item.sequence, str(item.step_id)),
                    )
                    if step.status == PlanStepStatus.PENDING
                ),
                None,
            )
            if target is not None:
                target_plan = plan_context.plan
                break

        if target is None or target_plan is None:
            return self._proposal(
                context,
                responsible_character_id=None,
                decision_type=OrganizationDecisionType.DEFER,
                target_step_id=None,
                rationale=(
                    "No pending step belongs to an active organization goal and plan "
                    "in the supplied context."
                ),
                required_resources=(),
            )

        available_capabilities = {
            item.name for item in context.capabilities if item.available
        }
        available_resources = {
            item.name for item in context.resources if item.available
        }
        known_fact_keys = {
            item.fact_key for item in (*context.facts, *context.circumstances)
        }
        missing = tuple(
            sorted(
                {
                    *(f"capability:{name}" for name in target.required_capabilities
                      if name not in available_capabilities),
                    *(f"resource:{name}" for name in target.required_resources
                      if name not in available_resources),
                    *(f"knowledge:{name}" for name in target.required_knowledge_fact_keys
                      if name not in known_fact_keys),
                }
            )
        )
        if missing:
            return self._proposal(
                context,
                responsible_character_id=target.responsible_character_id,
                decision_type=OrganizationDecisionType.DEFER,
                target_step_id=target.step_id,
                rationale=(
                    f"The organization defers '{target.action_intent}' because "
                    f"prerequisites are unavailable: {', '.join(missing)}."
                ),
                required_resources=target.required_resources,
                requirements=missing,
            )
        return self._proposal(
            context,
            responsible_character_id=target.responsible_character_id,
            decision_type=OrganizationDecisionType.EXECUTE_PLAN_STEP,
            target_step_id=target.step_id,
            rationale=(
                f"Plan '{target_plan.name}' advances an active goal; supplied "
                "institutional facts and circumstances were considered."
            ),
            required_resources=target.required_resources,
            requirements=(
                "membership-authority",
                "resource-availability",
                "filtered-knowledge-context",
            ),
        )

    @staticmethod
    def _proposal(
        context: OrganizationDecisionContext,
        *,
        responsible_character_id: UUID | None,
        decision_type: OrganizationDecisionType,
        target_step_id: UUID | None,
        rationale: str,
        required_resources: tuple[str, ...],
        requirements: tuple[str, ...] = (),
    ) -> OrganizationDecisionProposal:
        return OrganizationDecisionProposal(
            proposal_id=uuid5(
                UUID("2f0cc2e1-bf66-4f5f-9977-4f4d7a24efb1"),
                str(context.request_id),
            ),
            request_id=context.request_id,
            organization_id=context.organization_id,
            responsible_character_id=responsible_character_id,
            reaction=(
                "The organization is prepared to act through an authorized member."
                if decision_type == OrganizationDecisionType.EXECUTE_PLAN_STEP
                else "The organization defers the proposed action."
            ),
            decision_type=decision_type,
            target_plan_step_id=target_step_id,
            rationale=rationale,
            required_resources=required_resources,
            confidence=1.0,
            validation_requirements=requirements,
            context_hash="",
            provenance=RecordProvenance(
                source_type="deterministic-engine",
                source_id="organization-decision",
                created_at=context.as_of,
                updated_at=context.as_of,
                version=1,
            ),
        )
