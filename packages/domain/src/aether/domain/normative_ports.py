from typing import Protocol

from aether.contracts import (
    IntelligenceOperation,
    Investigation,
    LegalCase,
    LegalProceeding,
    NormativeSystem,
    ScheduledEvent,
    ScheduledEventResolution,
    SecurityIncident,
    SecurityThreat,
    StrategicConflict,
    Treaty,
)


class NormativeStrategicResolverPort(Protocol):
    def resolve_legal_proceeding(
        self,
        event: ScheduledEvent,
        system: NormativeSystem,
        case: LegalCase,
        proceeding: LegalProceeding,
    ) -> ScheduledEventResolution: ...

    def resolve_investigation(
        self,
        event: ScheduledEvent,
        system: NormativeSystem,
        case: LegalCase,
        investigation: Investigation,
    ) -> ScheduledEventResolution: ...

    def resolve_treaty(
        self,
        event: ScheduledEvent,
        treaty: Treaty,
    ) -> ScheduledEventResolution: ...

    def resolve_strategic_escalation(
        self,
        event: ScheduledEvent,
        conflict: StrategicConflict,
    ) -> ScheduledEventResolution: ...

    def resolve_security(
        self,
        event: ScheduledEvent,
        threat: SecurityThreat,
        operation: IntelligenceOperation | None,
        incident: SecurityIncident | None,
    ) -> ScheduledEventResolution: ...
