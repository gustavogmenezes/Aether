from uuid import UUID, uuid5

from aether.contracts import (
    NpcDecisionContext,
    NpcDecisionProposal,
    NpcDecisionType,
    PlanStatus,
    PlanStepStatus,
    RecordProvenance,
    GoalStatus,
)


class DeterministicNpcDecisionEngine:
    """Proposes decisions without reading or mutating external state."""

    def propose(self, context: NpcDecisionContext) -> NpcDecisionProposal:
        active_plans = [
            plan_context
            for plan_context in sorted(
                context.plans,
                key=lambda item: (item.plan.provenance.created_at, str(item.plan.plan_id)),
            )
            if plan_context.plan.character_id == context.character_id
            and plan_context.plan.status == PlanStatus.ACTIVE
        ]
        active_plan_goal_ids = {
            plan_context.plan.goal_id for plan_context in active_plans
        }
        active_goals = sorted(
            (
                goal
                for goal in context.goals
                if goal.character_id == context.character_id
                and goal.status == GoalStatus.ACTIVE
                and goal.goal_id in active_plan_goal_ids
            ),
            key=lambda goal: (goal.provenance.created_at, str(goal.goal_id)),
        )
        target = None
        for goal in active_goals:
            for plan_context in active_plans:
                if plan_context.plan.goal_id != goal.goal_id:
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
                    break
            if target is not None:
                break

        if target is None:
            return self._proposal(
                context,
                reaction="The character observes the supplied circumstances.",
                decision_type=NpcDecisionType.DEFER,
                target_step_id=None,
                rationale=(
                    "No pending step belongs to an active goal and active plan in "
                    "the supplied character context."
                ),
                required_resources=(),
                validation_requirements=("reassess-active-goals",),
                confidence=1.0,
            )

        available_capabilities = {
            item.name for item in context.capabilities if item.available
        }
        available_resources = {item.name for item in context.resources if item.available}
        known_fact_keys = {item.fact_key for item in context.knowledge}
        requirements = tuple(
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
        circumstances = (
            ", ".join(item.fact_key for item in context.circumstances)
            or "no supplied circumstance details"
        )
        rationale = (
            f"The pending step '{target.action_intent}' advances an active goal; "
            f"context circumstances: {circumstances}."
        )
        if requirements:
            return self._proposal(
                context,
                reaction="The character defers the step until missing prerequisites exist.",
                decision_type=NpcDecisionType.DEFER,
                target_step_id=target.step_id,
                rationale=rationale,
                required_resources=target.required_resources,
                validation_requirements=requirements,
                confidence=1.0,
            )

        return self._proposal(
            context,
            reaction="The character is prepared to perform the selected plan step.",
            decision_type=NpcDecisionType.EXECUTE_PLAN_STEP,
            target_step_id=target.step_id,
            rationale=rationale,
            required_resources=target.required_resources,
            validation_requirements=("resource-availability", "knowledge-context"),
            confidence=1.0,
        )

    @staticmethod
    def _proposal(
        context: NpcDecisionContext,
        *,
        reaction: str,
        decision_type: NpcDecisionType,
        target_step_id: UUID | None,
        rationale: str,
        required_resources: tuple[str, ...],
        validation_requirements: tuple[str, ...],
        confidence: float,
    ) -> NpcDecisionProposal:
        namespace = UUID("be8f6fb8-9c90-48c5-9016-a6f5f6c3c58d")
        return NpcDecisionProposal(
            proposal_id=uuid5(namespace, str(context.request_id)),
            request_id=context.request_id,
            character_id=context.character_id,
            reaction=reaction,
            decision_type=decision_type,
            target_plan_step_id=target_step_id,
            rationale=rationale,
            required_resources=required_resources,
            confidence=confidence,
            validation_requirements=validation_requirements,
            context_hash="",
            provenance=RecordProvenance(
                source_type="deterministic-engine",
                source_id="npc-decision",
                created_at=context.as_of,
                updated_at=context.as_of,
                version=1,
            ),
        )
