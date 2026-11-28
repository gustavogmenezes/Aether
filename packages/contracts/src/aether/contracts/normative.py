from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .character import RecordProvenance
from .knowledge import EpistemicStatus


class NormativeSystemKind(str, Enum):
    FORMAL = "formal"
    CUSTOMARY = "custom"
    RELIGIOUS = "religious"
    INSTITUTIONAL = "institutional"
    TREATY = "treaty"
    PRIVATE = "private"
    SUPERNATURAL = "supernatural"


class SemanticMetadata(BaseModel):
    model_config = ConfigDict(frozen=True)

    code: str
    description: str | None = None
    evidence_notes: tuple[str, ...] = ()


class Jurisdiction(BaseModel):
    model_config = ConfigDict(frozen=True)

    location_ids: tuple[UUID, ...] = ()
    include_descendants: bool = True
    territory_claim_ids: tuple[UUID, ...] = ()
    scope_notes: tuple[str, ...] = ()


class NormativeRule(BaseModel):
    model_config = ConfigDict(frozen=True)

    rule_id: UUID
    system_id: UUID
    name: str
    statement: str
    rights: tuple[str, ...] = ()
    duties: tuple[str, ...] = ()
    offense_references: tuple[str, ...] = ()
    sanction_references: tuple[str, ...] = ()
    provenance: RecordProvenance


class NormativeAuthority(BaseModel):
    model_config = ConfigDict(frozen=True)

    organization_id: UUID
    permission_code: str
    description: str | None = None


class NormativeSystem(BaseModel):
    model_config = ConfigDict(frozen=True)

    system_id: UUID
    world_id: UUID
    name: str
    kind: NormativeSystemKind
    jurisdiction: Jurisdiction = Field(default_factory=Jurisdiction)
    authorities: tuple[NormativeAuthority, ...] = ()
    enforceability: SemanticMetadata
    legitimacy: SemanticMetadata
    legal_validity: SemanticMetadata
    acceptance: SemanticMetadata | None = None
    oversight: tuple[str, ...] = ()
    corruption_notes: tuple[str, ...] = ()
    status: str = "active"
    provenance: RecordProvenance


class Offense(BaseModel):
    model_config = ConfigDict(frozen=True)

    offense_id: UUID
    system_id: UUID
    rule_id: UUID
    code: str
    description: str
    severity_semantics: tuple[str, ...] = ()
    provenance: RecordProvenance


class CaseStatus(str, Enum):
    OPEN = "open"
    INVESTIGATING = "investigating"
    PROCEEDING = "proceeding"
    DECIDED = "decided"
    APPEALED = "appealed"
    ENFORCED = "enforced"
    CLOSED = "closed"


class LegalCase(BaseModel):
    model_config = ConfigDict(frozen=True)

    case_id: UUID
    world_id: UUID
    system_id: UUID
    offense_ids: tuple[UUID, ...] = ()
    subject_actor_ids: tuple[UUID, ...] = ()
    complainant_actor_ids: tuple[UUID, ...] = ()
    location_id: UUID
    status: CaseStatus = CaseStatus.OPEN
    opened_at: datetime
    closed_at: datetime | None = None
    provenance: RecordProvenance


class InvestigationStatus(str, Enum):
    PLANNED = "planned"
    ACTIVE = "active"
    COMPLETED = "completed"
    ABANDONED = "abandoned"


class Investigation(BaseModel):
    model_config = ConfigDict(frozen=True)

    investigation_id: UUID
    case_id: UUID
    responsible_organization_id: UUID
    status: InvestigationStatus = InvestigationStatus.PLANNED
    evidence_ids: tuple[UUID, ...] = ()
    findings_summary: str | None = None
    completed_at: datetime | None = None
    provenance: RecordProvenance


class EvidenceVisibility(str, Enum):
    RESTRICTED = "restricted"
    PARTIES = "parties"
    PUBLIC = "public"


class EvidenceRecord(BaseModel):
    model_config = ConfigDict(frozen=True)

    evidence_id: UUID
    investigation_id: UUID
    case_id: UUID
    description: str
    evidence_type: str
    visibility: EvidenceVisibility = EvidenceVisibility.RESTRICTED
    permitted_character_ids: tuple[UUID, ...] = ()
    acquired_at: datetime
    reliability_semantics: tuple[str, ...] = ()
    provenance: RecordProvenance


class ProceedingStatus(str, Enum):
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in-progress"
    ADJOURNED = "adjourned"
    DECIDED = "decided"
    APPEALED = "appealed"
    CLOSED = "closed"


class LegalProceeding(BaseModel):
    model_config = ConfigDict(frozen=True)

    proceeding_id: UUID
    case_id: UUID
    kind: str
    status: ProceedingStatus = ProceedingStatus.SCHEDULED
    location_id: UUID
    decision_summary: str | None = None
    sanction_ids: tuple[UUID, ...] = ()
    provenance: RecordProvenance


class SanctionStatus(str, Enum):
    PROPOSED = "proposed"
    ORDERED = "ordered"
    ENFORCED = "enforced"
    STAYED = "stayed"
    APPEALED = "appealed"
    VACATED = "vacated"


class Sanction(BaseModel):
    model_config = ConfigDict(frozen=True)

    sanction_id: UUID
    case_id: UUID
    proceeding_id: UUID
    kind: str
    terms: tuple[str, ...] = ()
    target_actor_ids: tuple[UUID, ...] = ()
    status: SanctionStatus = SanctionStatus.PROPOSED
    authority_organization_id: UUID
    provenance: RecordProvenance


class Appeal(BaseModel):
    model_config = ConfigDict(frozen=True)

    appeal_id: UUID
    case_id: UUID
    proceeding_id: UUID
    sanction_id: UUID | None = None
    filed_by_actor_id: UUID
    status: str = "filed"
    grounds: tuple[str, ...] = ()
    filed_at: datetime
    provenance: RecordProvenance


class OrganizationRelationStatus(str, Enum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    SEVERED = "severed"


class OrganizationRelation(BaseModel):
    model_config = ConfigDict(frozen=True)

    relation_id: UUID
    world_id: UUID
    source_organization_id: UUID
    target_organization_id: UUID
    dimensions: dict[str, tuple[str, ...]] = Field(default_factory=dict)
    status: OrganizationRelationStatus = OrganizationRelationStatus.ACTIVE
    provenance: RecordProvenance

    @model_validator(mode="after")
    def relation_is_directional(self) -> "OrganizationRelation":
        if self.source_organization_id == self.target_organization_id:
            raise ValueError("Organization relation requires different parties")
        return self


class TreatyStatus(str, Enum):
    PROPOSED = "proposed"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    TERMINATED = "terminated"
    FULFILLED = "fulfilled"
    VIOLATED = "violated"


class Treaty(BaseModel):
    model_config = ConfigDict(frozen=True)

    treaty_id: UUID
    world_id: UUID
    name: str
    kind: str
    party_organization_ids: tuple[UUID, ...] = Field(min_length=2)
    obligations: tuple[str, ...] = ()
    concessions: tuple[str, ...] = ()
    reparations: tuple[str, ...] = ()
    information_sharing: tuple[str, ...] = ()
    sanction_terms: tuple[str, ...] = ()
    ceasefire_terms: tuple[str, ...] = ()
    status: TreatyStatus = TreatyStatus.PROPOSED
    effective_at: datetime | None = None
    expires_at: datetime | None = None
    provenance: RecordProvenance


class DiplomaticActionStatus(str, Enum):
    PROPOSED = "proposed"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    EXPIRED = "expired"
    WITHDRAWN = "withdrawn"


class DiplomaticAction(BaseModel):
    model_config = ConfigDict(frozen=True)

    action_id: UUID
    world_id: UUID
    source_organization_id: UUID
    target_organization_id: UUID
    kind: str
    terms: tuple[str, ...] = ()
    status: DiplomaticActionStatus = DiplomaticActionStatus.PROPOSED
    related_treaty_id: UUID | None = None
    provenance: RecordProvenance


class StrategicFactor(BaseModel):
    model_config = ConfigDict(frozen=True)

    category: str
    subject_id: UUID | None = None
    value: str
    recorded_at: datetime
    source: str


class StrategicConflict(BaseModel):
    model_config = ConfigDict(frozen=True)

    conflict_id: UUID
    world_id: UUID
    name: str
    party_organization_ids: tuple[UUID, ...] = Field(min_length=2)
    objectives: tuple[str, ...] = ()
    escalation_stage: str = "declared"
    stage_metadata: dict[str, str] = Field(default_factory=dict)
    factors: tuple[StrategicFactor, ...] = ()
    status: str = "active"
    provenance: RecordProvenance


class SecurityDomain(str, Enum):
    INDIVIDUAL = "individual"
    PROPERTY = "property"
    COMMUNITY = "community"
    INSTITUTIONAL = "institutional"
    TERRITORIAL = "territorial"
    NATIONAL = "national"
    INFORMATIONAL = "informational"


class SecurityThreatStatus(str, Enum):
    IDENTIFIED = "identified"
    MONITORED = "monitored"
    ACTIVE = "active"
    RESOLVED = "resolved"
    UNFOUNDED = "unfounded"
    ESCAPED = "escaped"


class SecurityThreat(BaseModel):
    model_config = ConfigDict(frozen=True)

    threat_id: UUID
    world_id: UUID
    domain: SecurityDomain
    description: str
    location_ids: tuple[UUID, ...] = ()
    motive_context: tuple[str, ...] = ()
    resource_context: tuple[str, ...] = ()
    opportunity_context: tuple[str, ...] = ()
    risk_context: tuple[str, ...] = ()
    status: SecurityThreatStatus = SecurityThreatStatus.IDENTIFIED
    provenance: RecordProvenance


class SecurityIncident(BaseModel):
    model_config = ConfigDict(frozen=True)

    incident_id: UUID
    threat_id: UUID
    occurred_at: datetime
    location_id: UUID
    description: str
    status: str = "reported"
    provenance: RecordProvenance


class IntelligenceOperationStatus(str, Enum):
    PROPOSED = "proposed"
    ACTIVE = "active"
    COMPLETED = "completed"
    COMPROMISED = "compromised"
    ABORTED = "aborted"


class IntelligenceOperation(BaseModel):
    model_config = ConfigDict(frozen=True)

    operation_id: UUID
    world_id: UUID
    organization_id: UUID
    kind: str
    threat_ids: tuple[UUID, ...] = ()
    location_id: UUID
    secrecy: tuple[str, ...] = ()
    status: IntelligenceOperationStatus = IntelligenceOperationStatus.PROPOSED
    provenance: RecordProvenance


class SecurityResolutionOutcome(str, Enum):
    ARREST = "arrest"
    EXPOSURE = "exposure"
    DISMANTLE = "dismantle"
    ESCAPE = "escape"
    NEGOTIATION = "negotiation"
    UNRESOLVED = "unresolved"


class SecurityResolution(BaseModel):
    model_config = ConfigDict(frozen=True)

    resolution_id: UUID
    operation_id: UUID | None
    threat_id: UUID
    outcome: SecurityResolutionOutcome
    status: str
    summary: str
    resolved_at: datetime
    source_event_id: UUID
    provenance: RecordProvenance


class AuthorityContext(BaseModel):
    model_config = ConfigDict(frozen=True)

    actor_id: UUID
    organization_id: UUID
    permission_code: str
    location_id: UUID


class ExplicitKnowledgeDisclosure(BaseModel):
    model_config = ConfigDict(frozen=True)

    character_id: UUID
    fact_key: str
    statement: str
    confidence: float = Field(ge=0, le=1)
    epistemic_status: EpistemicStatus = EpistemicStatus.BELIEF


class LegalProceedingTransitionPayload(BaseModel):
    model_config = ConfigDict(frozen=True)

    case_id: UUID
    proceeding_id: UUID
    target_status: ProceedingStatus
    case_status: CaseStatus
    decision_summary: str | None = None
    sanctions: tuple[Sanction, ...] = ()
    authority: AuthorityContext
    knowledge_disclosures: tuple[ExplicitKnowledgeDisclosure, ...] = ()


class InvestigationCompletionPayload(BaseModel):
    model_config = ConfigDict(frozen=True)

    investigation_id: UUID
    evidence: tuple[EvidenceRecord, ...] = ()
    findings_summary: str
    authority: AuthorityContext
    knowledge_disclosures: tuple[ExplicitKnowledgeDisclosure, ...] = ()


class TreatyChangePayload(BaseModel):
    model_config = ConfigDict(frozen=True)

    treaty_id: UUID
    target_status: TreatyStatus
    notes: tuple[str, ...] = ()
    authority: AuthorityContext


class StrategicEscalationPayload(BaseModel):
    model_config = ConfigDict(frozen=True)

    conflict_id: UUID
    target_stage: str
    stage_metadata: dict[str, str] = Field(default_factory=dict)
    added_factors: tuple[StrategicFactor, ...] = ()
    authority: AuthorityContext


class SecurityResolutionPayload(BaseModel):
    model_config = ConfigDict(frozen=True)

    threat_id: UUID
    operation_id: UUID | None = None
    incident_id: UUID | None = None
    outcome: SecurityResolutionOutcome
    resulting_threat_status: SecurityThreatStatus
    resulting_operation_status: IntelligenceOperationStatus | None = None
    summary: str
    authority: AuthorityContext
    knowledge_disclosures: tuple[ExplicitKnowledgeDisclosure, ...] = ()
