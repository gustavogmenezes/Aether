from typing import Protocol

from aether.contracts import (
    PlanStep,
    ScheduledEvent,
    ScheduledEventResolution,
)


class ScheduledEventResolverPort(Protocol):
    def resolve(
        self,
        event: ScheduledEvent,
        plan_step: PlanStep | None,
    ) -> ScheduledEventResolution: ...
