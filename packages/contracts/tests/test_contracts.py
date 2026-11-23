from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from pydantic import ValidationError

from aether.contracts import (
    ActionKind,
    ActionProposal,
    AdvanceTimeCommand,
    EventEnvelope,
    ExperienceMode,
    PlayerInput,
    ScheduledEvent,
)


def test_event_timestamps_require_timezone() -> None:
    with pytest.raises(ValidationError):
        EventEnvelope(
            event_id=uuid4(),
            world_id=uuid4(),
            timeline_id=uuid4(),
            occurred_at=datetime(2026, 1, 1),
            recorded_at=datetime(2026, 1, 1),
            sequence=1,
            event_type="test",
            source_type="test",
            source_id="source",
            payload_version="1",
            payload={},
        )


def test_advance_time_rejects_non_positive_duration() -> None:
    with pytest.raises(ValidationError):
        AdvanceTimeCommand(
            simulation_run_id=uuid4(),
            world_id=uuid4(),
            timeline_id=uuid4(),
            duration=timedelta(0),
        )


def test_scheduled_event_is_an_intention_not_an_occurred_event() -> None:
    scheduled = ScheduledEvent(
        event_id=uuid4(),
        world_id=uuid4(),
        timeline_id=uuid4(),
        scheduled_at=datetime(2026, 1, 1, tzinfo=UTC),
        event_type="patrol-arrives",
        source_type="schedule",
        source_id="patrol-1",
        payload_version="1",
        payload={},
    )

    assert not hasattr(scheduled, "occurred_at")


def test_action_proposal_preserves_duration_without_claiming_a_result() -> None:
    proposal = ActionProposal(
        proposal_id=uuid4(),
        invocation_id=uuid4(),
        action_kind=ActionKind.INTERVAL,
        intent="wait for five minutes",
        duration_seconds=300,
    )
    player_input = PlayerInput(
        input_id=uuid4(),
        simulation_run_id=uuid4(),
        world_id=uuid4(),
        timeline_id=uuid4(),
        protagonist_character_id=uuid4(),
        mode=ExperienceMode.PLAYER_CHARACTER,
        text="wait for 5 minutes",
    )

    assert proposal.action_kind == ActionKind.INTERVAL
    assert player_input.text == "wait for 5 minutes"
    assert not hasattr(proposal, "outcome")
