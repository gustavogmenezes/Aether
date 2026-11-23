from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from aether.domain import InvalidTemporalAdvanceError, WorldClockState


def test_clock_advances_with_new_version() -> None:
    initial = datetime(2026, 1, 1, tzinfo=UTC)
    clock = WorldClockState(uuid4(), uuid4(), initial, version=4)

    advanced = clock.advance_to(initial + timedelta(minutes=5))

    assert advanced.current_time == initial + timedelta(minutes=5)
    assert advanced.version == 5


def test_clock_rejects_backwards_movement() -> None:
    initial = datetime(2026, 1, 1, tzinfo=UTC)
    clock = WorldClockState(uuid4(), uuid4(), initial, version=0)

    with pytest.raises(InvalidTemporalAdvanceError):
        clock.advance_to(initial - timedelta(seconds=1))
