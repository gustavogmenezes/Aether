from datetime import UTC, datetime
from uuid import uuid4

from aether.contracts import (
    PlanStep,
    PlanStepStatus,
    RecordProvenance,
    ScheduledEvent,
    ScheduledEventOutcome,
)
from aether.engines import DeterministicScheduledEventResolver


def test_npc_plan_step_resolves_to_completed_consequence() -> None:
    now = datetime(2026, 1, 1, tzinfo=UTC)
    step = PlanStep(
        step_id=uuid4(),
        plan_id=uuid4(),
        sequence=0,
        action_intent="Secure the watch post",
        status=PlanStepStatus.SCHEDULED,
        provenance=RecordProvenance(
            source_type="test",
            source_id="test",
            created_at=now,
            updated_at=now,
            version=1,
        ),
    )
    event = ScheduledEvent(
        event_id=uuid4(),
        world_id=uuid4(),
        timeline_id=uuid4(),
        scheduled_at=now,
        event_type="npc-plan-step",
        source_type="npc-decision",
        source_id="proposal",
        payload_version="1",
        payload={
            "character_id": str(uuid4()),
            "plan_step_id": str(step.step_id),
        },
    )

    resolution = DeterministicScheduledEventResolver().resolve(event, step)

    assert resolution.outcome == ScheduledEventOutcome.COMPLETED
    assert resolution.plan_step_id == step.step_id
    assert resolution.payload["resolution"] == "completed"
    assert resolution.payload["action_intent"] == "Secure the watch post"


def test_unrelated_scheduled_event_is_not_reinterpreted() -> None:
    event = ScheduledEvent(
        event_id=uuid4(),
        world_id=uuid4(),
        timeline_id=uuid4(),
        scheduled_at=datetime(2026, 1, 1, tzinfo=UTC),
        event_type="seasonal-weather",
        source_type="test",
        source_id="weather",
        payload_version="1",
        payload={"season": "winter"},
    )

    resolution = DeterministicScheduledEventResolver().resolve(event, None)

    assert resolution.outcome == ScheduledEventOutcome.UNCHANGED
    assert resolution.payload == event.payload
    assert resolution.plan_step_id is None
