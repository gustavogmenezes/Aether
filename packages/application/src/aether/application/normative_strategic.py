from aether.contracts import (
    Appeal,
    DiplomaticAction,
    EvidenceRecord,
    IntelligenceOperation,
    Investigation,
    LegalCase,
    LegalProceeding,
    NormativeRule,
    NormativeSystem,
    Offense,
    OrganizationRelation,
    Sanction,
    ScheduledEvent,
    SecurityIncident,
    SecurityThreat,
    StrategicConflict,
    Treaty,
)
from aether.domain.ports import SimulationUnitOfWorkFactory


class NormativeStrategicService:
    """Persists authored institutional and strategic records and intentions."""

    _EVENT_TYPES = {
        "legal-proceeding-transition",
        "treaty-change",
        "strategic-escalation",
        "investigation-completion",
        "security-resolution",
    }

    def __init__(self, unit_of_work_factory: SimulationUnitOfWorkFactory) -> None:
        self._unit_of_work_factory = unit_of_work_factory

    def _create(self, method: str, entity) -> None:
        with self._unit_of_work_factory() as unit_of_work:
            getattr(unit_of_work.repository, method)(entity)

    def register_normative_system(self, system: NormativeSystem) -> None:
        self._create("create_normative_system", system)

    def register_normative_rule(self, rule: NormativeRule) -> None:
        self._create("create_normative_rule", rule)

    def register_offense(self, offense: Offense) -> None:
        self._create("create_offense", offense)

    def open_case(self, case: LegalCase) -> None:
        self._create("create_legal_case", case)

    def open_investigation(self, investigation: Investigation) -> None:
        self._create("create_investigation", investigation)

    def record_evidence(self, evidence: EvidenceRecord) -> None:
        self._create("create_evidence", evidence)

    def register_proceeding(self, proceeding: LegalProceeding) -> None:
        self._create("create_legal_proceeding", proceeding)

    def record_sanction(self, sanction: Sanction) -> None:
        self._create("create_sanction", sanction)

    def record_appeal(self, appeal: Appeal) -> None:
        self._create("create_appeal", appeal)

    def register_organization_relation(self, relation: OrganizationRelation) -> None:
        self._create("create_organization_relation", relation)

    def register_treaty(self, treaty: Treaty) -> None:
        self._create("create_treaty", treaty)

    def record_diplomatic_action(self, action: DiplomaticAction) -> None:
        self._create("create_diplomatic_action", action)

    def register_strategic_conflict(self, conflict: StrategicConflict) -> None:
        self._create("create_strategic_conflict", conflict)

    def register_security_threat(self, threat: SecurityThreat) -> None:
        self._create("create_security_threat", threat)

    def record_security_incident(self, incident: SecurityIncident) -> None:
        self._create("create_security_incident", incident)

    def register_intelligence_operation(self, operation: IntelligenceOperation) -> None:
        self._create("create_intelligence_operation", operation)

    def schedule_authorized_event(self, event: ScheduledEvent) -> None:
        if event.event_type not in self._EVENT_TYPES:
            raise ValueError("Unsupported normative or strategic scheduled event")
        with self._unit_of_work_factory() as unit_of_work:
            unit_of_work.repository.schedule_event(event)
