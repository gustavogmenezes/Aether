from uuid import UUID

from aether.contracts import (
    PlanStep,
    PlanStepStatus,
    ScheduledEvent,
    ScheduledEventOutcome,
    ScheduledEventResolution,
)


class DeterministicScheduledEventResolver:
    def resolve(
        self,
        event: ScheduledEvent,
        plan_step: PlanStep | None,
    ) -> ScheduledEventResolution:
        if event.event_type != "npc-plan-step":
            return ScheduledEventResolution(
                scheduled_event_id=event.event_id,
                outcome=ScheduledEventOutcome.UNCHANGED,
                payload=dict(event.payload),
            )

        payload_step_id = event.payload.get("plan_step_id")
        character_id = event.payload.get("character_id")
        if not isinstance(payload_step_id, str) or not isinstance(character_id, str):
            raise ValueError("NPC plan-step event payload is incomplete")
        if plan_step is None:
            raise ValueError("NPC plan-step event references an unknown plan step")
        if UUID(payload_step_id) != plan_step.step_id:
            raise ValueError("NPC plan-step event and stored step do not match")
        if plan_step.status != PlanStepStatus.SCHEDULED:
            raise ValueError("Only scheduled NPC plan steps can be resolved")

        return ScheduledEventResolution(
            scheduled_event_id=event.event_id,
            outcome=ScheduledEventOutcome.COMPLETED,
            payload={
                **event.payload,
                "resolution": "completed",
                "action_intent": plan_step.action_intent,
            },
            plan_step_id=plan_step.step_id,
            reason="Deterministic plan-step execution completed",
        )
