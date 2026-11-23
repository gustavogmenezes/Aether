from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import pytest

from aether.contracts import ScheduledEvent
from aether.domain import CausalOrderingError
from aether.engines import EventOrderingEngine


def scheduled(
    *,
    event_id: UUID | None = None,
    at: datetime,
    priority: int = 0,
    caused_by: tuple[UUID, ...] = (),
) -> ScheduledEvent:
    return ScheduledEvent(
        event_id=event_id or uuid4(),
        world_id=uuid4(),
        timeline_id=uuid4(),
        scheduled_at=at,
        event_type="test",
        source_type="test",
        source_id="source",
        caused_by=caused_by,
        priority=priority,
        payload_version="1",
        payload={},
    )


def test_orders_by_time_priority_and_deterministic_id() -> None:
    at = datetime(2026, 1, 1, tzinfo=UTC)
    low = scheduled(event_id=UUID(int=1), at=at, priority=1)
    high = scheduled(event_id=UUID(int=2), at=at, priority=10)
    later = scheduled(event_id=UUID(int=3), at=at + timedelta(seconds=1))

    ordered = EventOrderingEngine().order((later, low, high))

    assert [event.event_id for event in ordered] == [
        high.event_id,
        low.event_id,
        later.event_id,
    ]


def test_causal_dependency_overrides_priority() -> None:
    at = datetime(2026, 1, 1, tzinfo=UTC)
    cause = scheduled(event_id=UUID(int=1), at=at, priority=0)
    effect = scheduled(
        event_id=UUID(int=2),
        at=at,
        priority=100,
        caused_by=(cause.event_id,),
    )

    ordered = EventOrderingEngine().order((effect, cause))

    assert ordered == (cause, effect)


def test_rejects_causal_cycle() -> None:
    at = datetime(2026, 1, 1, tzinfo=UTC)
    first_id = UUID(int=1)
    second_id = UUID(int=2)
    first = scheduled(event_id=first_id, at=at, caused_by=(second_id,))
    second = scheduled(event_id=second_id, at=at, caused_by=(first_id,))

    with pytest.raises(CausalOrderingError):
        EventOrderingEngine().order((first, second))
