from datetime import datetime
from decimal import Decimal
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator, field_validator

from .character import RecordProvenance


class CulturalAffiliationTargetType(str, Enum):
    CULTURE = "culture"
    SOCIAL_GROUP = "social-group"


class CulturalAffiliationDisposition(str, Enum):
    ADHERES = "adheres"
    QUESTIONS = "questions"
    REJECTS = "rejects"
    ASSIMILATES = "assimilates"
    HYBRIDIZES = "hybridizes"
    TRANSFORMS = "transforms"


class CulturalAffiliationVisibility(str, Enum):
    SELF = "self"
    PUBLIC = "public"
    RESTRICTED = "restricted"


class CulturalChangeCause(str, Enum):
    MIGRATION = "migration"
    TRADE = "trade"
    WAR = "war"
    COLONIZATION = "colonization"
    CONVERSION = "conversion"
    REVOLUTION = "revolution"
    TECHNOLOGY = "technology"


class InterculturalRelationship(BaseModel):
    model_config = ConfigDict(frozen=True)

    other_culture_id: UUID
    semantics: str
    history_event_ids: tuple[UUID, ...] = ()

    @field_validator("semantics")
    @classmethod
    def require_semantics(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Intercultural relationship semantics cannot be blank")
        return value


class CultureDefinition(BaseModel):
    model_config = ConfigDict(frozen=True)

    culture_id: UUID
    world_id: UUID
    name: str
    description: str | None = None
    values: tuple[str, ...] = ()
    customs: tuple[str, ...] = ()
    traditions: tuple[str, ...] = ()
    norms: tuple[str, ...] = ()
    belief_references: tuple[str, ...] = ()
    religion_tradition_ids: tuple[UUID, ...] = ()
    language_ids: tuple[UUID, ...] = ()
    art_work_ids: tuple[UUID, ...] = ()
    symbol_ids: tuple[UUID, ...] = ()
    intercultural_relationships: tuple[InterculturalRelationship, ...] = ()
    history_event_ids: tuple[UUID, ...] = ()
    provenance: RecordProvenance


class SocialGroup(BaseModel):
    """A semantic social category, without an implied universal hierarchy."""

    model_config = ConfigDict(frozen=True)

    group_id: UUID
    world_id: UUID
    name: str
    semantic_category: str
    description: str | None = None
    culture_ids: tuple[UUID, ...] = ()
    provenance: RecordProvenance

    @field_validator("semantic_category")
    @classmethod
    def require_semantic_category(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Social group semantic category cannot be blank")
        return value


class IndividualCulturalAffiliation(BaseModel):
    model_config = ConfigDict(frozen=True)

    affiliation_id: UUID
    character_id: UUID
    target_type: CulturalAffiliationTargetType
    target_id: UUID
    disposition: CulturalAffiliationDisposition
    visibility: CulturalAffiliationVisibility
    visible_to_character_ids: tuple[UUID, ...] = ()
    confidence: Decimal = Field(ge=Decimal("0"), le=Decimal("1"))
    notes: str | None = None
    effective_from: datetime
    effective_until: datetime | None = None
    provenance: RecordProvenance

    @field_validator("effective_from", "effective_until")
    @classmethod
    def require_timezone(
        cls, value: datetime | None
    ) -> datetime | None:
        if value is not None and (value.tzinfo is None or value.utcoffset() is None):
            raise ValueError("Affiliation timestamps must include a UTC offset")
        return value

    @model_validator(mode="after")
    def validate_visibility_and_interval(self) -> "IndividualCulturalAffiliation":
        if (
            self.effective_until is not None
            and self.effective_until < self.effective_from
        ):
            raise ValueError("Affiliation cannot end before it begins")
        if self.visibility is CulturalAffiliationVisibility.RESTRICTED:
            if not self.visible_to_character_ids:
                raise ValueError("Restricted affiliation requires visible characters")
        return self


class CulturalChangeRecord(BaseModel):
    model_config = ConfigDict(frozen=True)

    record_id: UUID
    world_id: UUID
    target_type: CulturalAffiliationTargetType
    target_id: UUID
    source_event_id: UUID
    occurred_at: datetime
    cause_tags: tuple[CulturalChangeCause, ...]
    old_state_reference: UUID | None
    new_state_reference: UUID
    summary: str
    provenance: RecordProvenance

    @field_validator("occurred_at")
    @classmethod
    def require_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("Cultural change time must include a UTC offset")
        return value

    @field_validator("summary")
    @classmethod
    def require_summary(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Cultural change summary cannot be blank")
        return value

    @field_validator("cause_tags")
    @classmethod
    def require_cause_tag(
        cls, value: tuple[CulturalChangeCause, ...]
    ) -> tuple[CulturalChangeCause, ...]:
        if not value:
            raise ValueError("Cultural change requires at least one cause tag")
        return value

    @model_validator(mode="after")
    def state_reference_changes(self) -> "CulturalChangeRecord":
        if self.old_state_reference == self.new_state_reference:
            raise ValueError("Cultural change old and new state references must differ")
        return self


class CharacterCulturalContext(BaseModel):
    model_config = ConfigDict(frozen=True)

    character_id: UUID
    observer_character_id: UUID
    as_of: datetime
    affiliations: tuple[IndividualCulturalAffiliation, ...] = ()
    cultures: tuple[CultureDefinition, ...] = ()
    social_groups: tuple[SocialGroup, ...] = ()

    @field_validator("as_of")
    @classmethod
    def require_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("Cultural context time must include a UTC offset")
        return value


class KnowledgeLifecycleState(str, Enum):
    EXISTS = "exists"
    DISCOVERED = "discovered"
    DOCUMENTED = "documented"
    TRANSMITTED = "transmitted"
    MASTERED = "mastered"
    APPLIED = "applied"


class ResourceRequirement(BaseModel):
    model_config = ConfigDict(frozen=True)

    resource_code: str
    quantity: Decimal = Field(gt=0)


class PrerequisiteRequirement(BaseModel):
    model_config = ConfigDict(frozen=True)

    entity_id: UUID
    required_state: KnowledgeLifecycleState


class AccessRequirements(BaseModel):
    model_config = ConfigDict(frozen=True)

    location_ids: tuple[UUID, ...] = ()
    resource_requirements: tuple[ResourceRequirement, ...] = ()
    infrastructure_ids: tuple[UUID, ...] = ()
    language_requirements: tuple[UUID, ...] = ()
    secrecy_permissions: tuple[str, ...] = ()
    education_admission_conditions: tuple[str, ...] = ()
    prerequisite_requirements: tuple[PrerequisiteRequirement, ...] = ()
    capability_conditions: tuple[str, ...] = ()


class KnowledgeArtifact(BaseModel):
    model_config = ConfigDict(frozen=True)

    artifact_id: UUID
    world_id: UUID
    name: str
    category: str
    description: str | None = None
    state: KnowledgeLifecycleState = KnowledgeLifecycleState.EXISTS
    requirements: AccessRequirements = Field(default_factory=AccessRequirements)
    documentation_references: tuple[str, ...] = ()
    provenance: RecordProvenance


class Technology(BaseModel):
    model_config = ConfigDict(frozen=True)

    technology_id: UUID
    world_id: UUID
    name: str
    description: str | None = None
    state: KnowledgeLifecycleState = KnowledgeLifecycleState.EXISTS
    theory_references: tuple[UUID, ...] = ()
    material_references: tuple[str, ...] = ()
    manufacture_conditions: tuple[str, ...] = ()
    labor_conditions: tuple[str, ...] = ()
    funding_conditions: tuple[str, ...] = ()
    political_conditions: tuple[str, ...] = ()
    requirements: AccessRequirements = Field(default_factory=AccessRequirements)
    provenance: RecordProvenance


class KnowledgeLifecycleRecord(BaseModel):
    model_config = ConfigDict(frozen=True)

    record_id: UUID
    entity_type: str
    entity_id: UUID
    actor_id: UUID | None
    state: KnowledgeLifecycleState
    occurred_at: datetime
    cause: str
    location_id: UUID | None = None
    source_event_id: UUID
    language_id: UUID | None = None
    provenance: RecordProvenance

    @field_validator("occurred_at")
    @classmethod
    def require_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("Lifecycle occurrence time must include a UTC offset")
        return value


class LanguageProficiencyDimension(str, Enum):
    COMPREHENSION = "comprehension"
    SPEAKING = "speaking"
    READING = "reading"
    WRITING = "writing"


class Language(BaseModel):
    model_config = ConfigDict(frozen=True)

    language_id: UUID
    world_id: UUID
    name: str
    origin: str | None = None
    family: str | None = None
    status: str = "living"
    artificial_or_supernatural: bool = False
    regional_variants: tuple[str, ...] = ()
    social_variants: tuple[str, ...] = ()
    provenance: RecordProvenance


class Dialect(BaseModel):
    model_config = ConfigDict(frozen=True)

    dialect_id: UUID
    language_id: UUID
    name: str
    region: str | None = None
    social_group: str | None = None
    historical_relation: str | None = None
    provenance: RecordProvenance


class WritingSystem(BaseModel):
    model_config = ConfigDict(frozen=True)

    writing_system_id: UUID
    world_id: UUID
    name: str
    language_ids: tuple[UUID, ...] = ()
    script_characteristics: tuple[str, ...] = ()
    status: str = "living"
    provenance: RecordProvenance


class CharacterLanguageProficiency(BaseModel):
    model_config = ConfigDict(frozen=True)

    proficiency_id: UUID
    character_id: UUID
    language_id: UUID
    dialect_id: UUID | None = None
    comprehension: str
    speaking: str
    reading: str
    writing: str
    semantic_notes: tuple[str, ...] = ()
    acquired_at: datetime
    provenance: RecordProvenance


class TranslationMetadata(BaseModel):
    model_config = ConfigDict(frozen=True)

    source_language_id: UUID | None = None
    target_language_id: UUID | None = None
    source_dialect_id: UUID | None = None
    target_dialect_id: UUID | None = None
    writing_system_id: UUID | None = None
    presentation_language: str | None = None
    translation_semantics: tuple[str, ...] = ()
    imperfect: bool = False


class CurriculumEntry(BaseModel):
    model_config = ConfigDict(frozen=True)

    entry_id: UUID
    subject_reference: str
    knowledge_artifact_ids: tuple[UUID, ...] = ()
    method: str
    sequence: int = Field(ge=0)


class EducationProgram(BaseModel):
    model_config = ConfigDict(frozen=True)

    program_id: UUID
    world_id: UUID
    organization_id: UUID | None = None
    name: str
    formality: str
    curriculum: tuple[CurriculumEntry, ...] = ()
    teacher_character_ids: tuple[UUID, ...] = ()
    methods: tuple[str, ...] = ()
    location_ids: tuple[UUID, ...] = ()
    infrastructure_ids: tuple[UUID, ...] = ()
    resource_requirements: tuple[ResourceRequirement, ...] = ()
    language_ids: tuple[UUID, ...] = ()
    admission_requirements: tuple[str, ...] = ()
    provenance: RecordProvenance


class EnrollmentStatus(str, Enum):
    ADMITTED = "admitted"
    PARTICIPATING = "participating"
    COMPLETED = "completed"
    WITHDRAWN = "withdrawn"
    REJECTED = "rejected"


class EducationEnrollment(BaseModel):
    model_config = ConfigDict(frozen=True)

    enrollment_id: UUID
    program_id: UUID
    character_id: UUID
    status: EnrollmentStatus = EnrollmentStatus.ADMITTED
    enrolled_at: datetime
    provenance: RecordProvenance


class LearningOpportunity(BaseModel):
    model_config = ConfigDict(frozen=True)

    opportunity_id: UUID
    program_id: UUID | None
    participant_character_id: UUID
    curriculum_entry_id: UUID | None = None
    kind: str
    began_at: datetime
    ended_at: datetime
    teacher_character_id: UUID | None = None
    location_id: UUID | None = None
    source_event_id: UUID | None = None
    participation_recorded: bool = True
    provenance: RecordProvenance

    @model_validator(mode="after")
    def ordering_is_valid(self) -> "LearningOpportunity":
        if self.ended_at < self.began_at:
            raise ValueError("Learning opportunity cannot end before it begins")
        return self


class AssessmentOutcome(BaseModel):
    model_config = ConfigDict(frozen=True)

    outcome_id: UUID
    enrollment_id: UUID
    opportunity_id: UUID | None
    character_id: UUID
    assessed_at: datetime
    assessor_character_id: UUID | None = None
    stated_outcome: str
    evidence_references: tuple[str, ...] = ()
    mastery_asserted: bool = False
    completion_asserted: bool = False
    source_event_id: UUID
    provenance: RecordProvenance

    @model_validator(mode="after")
    def outcome_has_a_statement(self) -> "AssessmentOutcome":
        if not self.stated_outcome.strip():
            raise ValueError("Assessment outcome requires an explicit statement")
        return self


class ReligionTradition(BaseModel):
    model_config = ConfigDict(frozen=True)

    tradition_id: UUID
    world_id: UUID
    name: str
    parent_tradition_id: UUID | None = None
    cosmology_references: tuple[str, ...] = ()
    doctrine_references: tuple[str, ...] = ()
    entity_or_principle_references: tuple[str, ...] = ()
    ritual_references: tuple[str, ...] = ()
    text_references: tuple[str, ...] = ()
    value_references: tuple[str, ...] = ()
    internal_interpretations: tuple[str, ...] = ()
    organization_id: UUID | None = None
    provenance: RecordProvenance


class IndividualBeliefRecord(BaseModel):
    model_config = ConfigDict(frozen=True)

    belief_id: UUID
    character_id: UUID
    tradition_id: UUID | None = None
    propositions: tuple[str, ...] = ()
    doubt_or_ambiguity: tuple[str, ...] = ()
    practice_commitment: str
    epistemic_status: str = "belief"
    acquired_at: datetime
    source_event_id: UUID | None = None
    provenance: RecordProvenance


class RitualCompletion(BaseModel):
    model_config = ConfigDict(frozen=True)

    completion_id: UUID
    tradition_id: UUID
    organization_id: UUID | None
    actor_id: UUID
    ritual_reference: str
    location_id: UUID
    completed_at: datetime
    source_event_id: UUID
    participants: tuple[UUID, ...] = ()
    outcome_record: str
    provenance: RecordProvenance


class MetaphysicalTruth(BaseModel):
    model_config = ConfigDict(frozen=True)

    truth_id: UUID
    world_id: UUID
    statement: str
    scope: str
    disclosure_class: str = "world-objective-only"
    provenance: RecordProvenance

    @model_validator(mode="after")
    def objective_truth_is_world_scoped(self) -> "MetaphysicalTruth":
        if self.disclosure_class != "world-objective-only":
            raise ValueError("Metaphysical truth cannot be exposed to character context")
        return self


class ActorAccessContext(BaseModel):
    model_config = ConfigDict(frozen=True)

    actor_id: UUID
    location_id: UUID | None
    available_resources: dict[str, Decimal] = Field(default_factory=dict)
    available_infrastructure_ids: tuple[UUID, ...] = ()
    language_capabilities: tuple[UUID, ...] = ()
    secrecy_permissions: tuple[str, ...] = ()
    education_qualifications: tuple[str, ...] = ()
    satisfied_prerequisite_states: dict[str, KnowledgeLifecycleState] = Field(
        default_factory=dict
    )
    satisfied_capabilities: tuple[str, ...] = ()


class AccessFailure(BaseModel):
    model_config = ConfigDict(frozen=True)

    code: str
    requirement: str
    message: str


class AccessDecision(BaseModel):
    model_config = ConfigDict(frozen=True)

    allowed: bool
    failures: tuple[AccessFailure, ...] = ()


class KnowledgeTransmissionPayload(BaseModel):
    model_config = ConfigDict(frozen=True)

    artifact_id: UUID
    actor_id: UUID
    target_state: KnowledgeLifecycleState = KnowledgeLifecycleState.TRANSMITTED
    cause: str
    location_id: UUID | None = None
    language_id: UUID | None = None
    access_context: ActorAccessContext


class TechnologyUsePayload(BaseModel):
    model_config = ConfigDict(frozen=True)

    technology_id: UUID
    actor_id: UUID
    target_state: KnowledgeLifecycleState = KnowledgeLifecycleState.APPLIED
    cause: str
    location_id: UUID | None = None
    access_context: ActorAccessContext


class LearningAssessmentPayload(BaseModel):
    model_config = ConfigDict(frozen=True)

    enrollment_id: UUID
    opportunity_id: UUID | None = None
    actor_id: UUID
    assessor_character_id: UUID | None = None
    stated_outcome: str
    evidence_references: tuple[str, ...] = ()
    mastery_asserted: bool = False
    completion_asserted: bool = False
    access_context: ActorAccessContext


class ReligiousRitualPayload(BaseModel):
    model_config = ConfigDict(frozen=True)

    tradition_id: UUID
    actor_id: UUID
    ritual_reference: str
    location_id: UUID
    participants: tuple[UUID, ...] = ()
    outcome_record: str
    access_requirements: AccessRequirements = Field(default_factory=AccessRequirements)
    access_context: ActorAccessContext
