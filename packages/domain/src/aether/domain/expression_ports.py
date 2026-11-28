from typing import Protocol

from aether.contracts import ScheduledEvent, ScheduledEventResolution


class PublicExpressionResolverPort(Protocol):
    def resolve_publication(
        self,
        event: ScheduledEvent,
    ) -> ScheduledEventResolution: ...
