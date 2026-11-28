from typing import Protocol

from aether.contracts import (
    PlanStep,
    OrganizationPlanStep,
    ScheduledEvent,
    ScheduledEventResolution,
)


class ScheduledEventResolverPort(Protocol):
    def resolve(
        self,
        event: ScheduledEvent,
        plan_step: PlanStep | OrganizationPlanStep | None,
    ) -> ScheduledEventResolution: ...
