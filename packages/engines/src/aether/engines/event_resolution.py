from dataclasses import dataclass
from datetime import datetime
from heapq import heappop, heappush
from uuid import UUID

from aether.contracts import EventEnvelope, ScheduledEvent
from aether.domain import CausalOrderingError


@dataclass(frozen=True, slots=True)
class _QueueKey:
    occurred_at: datetime
    priority_descending: int
    event_id: str
    event: ScheduledEvent

    def __lt__(self, other: "_QueueKey") -> bool:
        return (
            self.occurred_at,
            self.priority_descending,
            self.event_id,
        ) < (
            other.occurred_at,
            other.priority_descending,
            other.event_id,
        )


class EventOrderingEngine:
    def order(self, events: tuple[ScheduledEvent, ...]) -> tuple[ScheduledEvent, ...]:
        by_id = {event.event_id: event for event in events}
        if len(by_id) != len(events):
            raise CausalOrderingError("Scheduled event IDs must be unique within a cycle")

        dependencies = {
            event.event_id: tuple(
                cause_id for cause_id in event.caused_by if cause_id in by_id
            )
            for event in events
        }
        remaining_dependencies = {
            event_id: len(causes) for event_id, causes in dependencies.items()
        }
        dependants: dict[UUID, list[UUID]] = {event_id: [] for event_id in by_id}
        for event_id, causes in dependencies.items():
            for cause_id in causes:
                cause = by_id[cause_id]
                if by_id[event_id].scheduled_at < cause.scheduled_at:
                    raise CausalOrderingError(
                        "A scheduled event cannot occur before a scheduled cause"
                    )
                dependants[cause_id].append(event_id)

        ready: list[_QueueKey] = []
        for event in events:
            if remaining_dependencies[event.event_id] == 0:
                heappush(ready, self._queue_key(event))

        ordered: list[ScheduledEvent] = []
        while ready:
            key = heappop(ready)
            event = key.event
            ordered.append(event)
            for dependant_id in dependants[event.event_id]:
                remaining_dependencies[dependant_id] -= 1
                if remaining_dependencies[dependant_id] == 0:
                    heappush(ready, self._queue_key(by_id[dependant_id]))

        if len(ordered) != len(events):
            raise CausalOrderingError("Scheduled events contain a causal cycle")
        return tuple(ordered)

    def materialize(
        self,
        ordered_events: tuple[ScheduledEvent, ...],
        *,
        recorded_at: datetime,
        first_sequence: int,
    ) -> tuple[EventEnvelope, ...]:
        return tuple(
            EventEnvelope(
                event_id=event.event_id,
                world_id=event.world_id,
                timeline_id=event.timeline_id,
                occurred_at=event.scheduled_at,
                recorded_at=recorded_at,
                sequence=first_sequence + index,
                event_type=event.event_type,
                source_type=event.source_type,
                source_id=event.source_id,
                caused_by=event.caused_by,
                priority=event.priority,
                payload_version=event.payload_version,
                payload=event.payload,
                interruption_class=event.interruption_class,
            )
            for index, event in enumerate(ordered_events)
        )

    @staticmethod
    def _queue_key(event: ScheduledEvent) -> _QueueKey:
        return _QueueKey(
            occurred_at=event.scheduled_at,
            priority_descending=-event.priority,
            event_id=str(event.event_id),
            event=event,
        )
