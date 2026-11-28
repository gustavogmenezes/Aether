from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class SkillCategoryKind(str, Enum):
    MENTAL = "mental"
    PHYSICAL = "physical"
    SOCIAL = "social"


class AttributeRating(BaseModel):
    model_config = ConfigDict(frozen=True)

    category: str
    name: str
    rating: int = Field(ge=1, le=5)


class SkillRating(BaseModel):
    model_config = ConfigDict(frozen=True)

    category: str
    name: str
    rating: int = Field(ge=0, le=5)


class Specialization(BaseModel):
    model_config = ConfigDict(frozen=True)

    skill: str
    name: str
    level: int = Field(ge=1)


class Merit(BaseModel):
    model_config = ConfigDict(frozen=True)

    name: str
    points: int = Field(ge=1)


class NarrativeFeature(BaseModel):
    model_config = ConfigDict(frozen=True)

    name: str
    description: str | None = None


class StorytellingCreationProfile(BaseModel):
    model_config = ConfigDict(frozen=True)

    profile_id: UUID
    world_id: UUID
    ruleset_id: str
    attribute_categories: tuple[str, ...]
    skill_categories: tuple[str, ...]
    skill_category_kinds: dict[str, SkillCategoryKind]
    attribute_priority_budgets: tuple[int, ...] = (5, 4, 3)
    skill_priority_budgets: tuple[int, ...] = (11, 7, 4)
    base_attribute_rating: int = 1
    initial_specialization_levels: int = 3
    merit_points: int = 7
    untrained_mental_penalty: int = -3
    untrained_physical_social_penalty: int = -1

    @model_validator(mode="after")
    def validate_storytelling_reference(self) -> "StorytellingCreationProfile":
        if self.attribute_priority_budgets != (5, 4, 3):
            raise ValueError("Storytelling attributes require 5/4/3 budgets")
        if self.skill_priority_budgets != (11, 7, 4):
            raise ValueError("Storytelling skills require 11/7/4 budgets")
        if (
            self.base_attribute_rating != 1
            or self.initial_specialization_levels != 3
            or self.merit_points != 7
        ):
            raise ValueError("Storytelling base, specialization, and Merit budgets do not match")
        if (
            self.untrained_mental_penalty != -3
            or self.untrained_physical_social_penalty != -1
        ):
            raise ValueError("Storytelling untrained skill penalties do not match")
        if len(self.attribute_categories) != 3 or len(set(self.attribute_categories)) != 3:
            raise ValueError("The world must supply exactly three attribute categories")
        if len(self.skill_categories) != 3 or len(set(self.skill_categories)) != 3:
            raise ValueError("The world must supply exactly three skill categories")
        if any(not value.strip() for value in (*self.attribute_categories, *self.skill_categories)):
            raise ValueError("Category names cannot be blank")
        if set(self.skill_category_kinds) != set(self.skill_categories):
            raise ValueError("Every supplied skill category requires an explicit penalty kind")
        return self


class GenesisProvenance(BaseModel):
    model_config = ConfigDict(frozen=True)

    profile_id: UUID
    ruleset_id: str
    source_type: str
    source_id: str
    biographical_stage: str | None = None
    template_ids: tuple[str, ...] = ()
    origin_event_ids: tuple[UUID, ...] = ()
    created_at: datetime

    @field_validator("ruleset_id", "source_type", "source_id")
    @classmethod
    def require_non_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Genesis provenance fields cannot be blank")
        return value

    @field_validator("created_at")
    @classmethod
    def require_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("Genesis timestamps must include a UTC offset")
        return value


class CharacterSheet(BaseModel):
    model_config = ConfigDict(frozen=True)

    sheet_id: UUID
    world_id: UUID
    character_id: UUID
    ruleset_id: str
    attributes: tuple[AttributeRating, ...] = ()
    skills: tuple[SkillRating, ...] = ()
    specializations: tuple[Specialization, ...] = ()
    merits: tuple[Merit, ...] = ()
    narrative_qualities: tuple[NarrativeFeature, ...] = ()
    narrative_flaws: tuple[NarrativeFeature, ...] = ()
    injuries: tuple[NarrativeFeature, ...] = ()
    traits: tuple[NarrativeFeature, ...] = ()
    genesis: GenesisProvenance
    version: int = Field(ge=1)
    updated_at: datetime

    @field_validator("ruleset_id")
    @classmethod
    def require_ruleset(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("ruleset_id cannot be blank")
        return value

    @model_validator(mode="after")
    def validate_ruleset_provenance(self) -> "CharacterSheet":
        if self.genesis.ruleset_id != self.ruleset_id:
            raise ValueError("Character sheet ruleset and genesis provenance differ")
        return self

    @field_validator("updated_at")
    @classmethod
    def require_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("Character sheet timestamps must include a UTC offset")
        return value


class ProgressionChangeKind(str, Enum):
    ATTRIBUTE = "attribute"
    SKILL = "skill"
    SPECIALIZATION = "specialization"
    MERIT = "merit"
    NARRATIVE_QUALITY = "narrative_quality"
    NARRATIVE_FLAW = "narrative_flaw"
    INJURY = "injury"
    TRAIT = "trait"


class ProgressionChangeOperation(str, Enum):
    INCREASE = "increase"
    DECREASE = "decrease"
    ADD = "add"
    REMOVE = "remove"


class CharacterProgressionChange(BaseModel):
    model_config = ConfigDict(frozen=True)

    kind: ProgressionChangeKind
    target: str
    category: str | None = None
    operation: ProgressionChangeOperation
    amount: int = Field(default=1, ge=1)
    description: str | None = None

    @model_validator(mode="after")
    def validate_operation(self) -> "CharacterProgressionChange":
        if self.kind in {
            ProgressionChangeKind.ATTRIBUTE,
            ProgressionChangeKind.SKILL,
            ProgressionChangeKind.SPECIALIZATION,
            ProgressionChangeKind.MERIT,
        }:
            if self.operation not in {
                ProgressionChangeOperation.INCREASE,
                ProgressionChangeOperation.DECREASE,
            }:
                raise ValueError("Rating changes require increase or decrease")
        elif self.operation not in {
            ProgressionChangeOperation.ADD,
            ProgressionChangeOperation.REMOVE,
        }:
            raise ValueError("Narrative, injury, and trait changes require add or remove")
        if self.kind in {
            ProgressionChangeKind.ATTRIBUTE,
            ProgressionChangeKind.SKILL,
        } and not self.category:
            raise ValueError("Attribute and skill changes require an explicit category")
        if not self.target.strip():
            raise ValueError("Progression change target cannot be blank")
        return self


class CharacterProgressionEvidence(BaseModel):
    model_config = ConfigDict(frozen=True)

    evidence_id: UUID
    world_id: UUID
    character_id: UUID
    event_ids: tuple[UUID, ...]
    summary: str
    recorded_at: datetime

    @model_validator(mode="after")
    def validate_evidence(self) -> "CharacterProgressionEvidence":
        if not self.event_ids:
            raise ValueError("Progression evidence must link at least one event")
        if not self.summary.strip():
            raise ValueError("Progression evidence summary cannot be blank")
        return self

    @field_validator("recorded_at")
    @classmethod
    def require_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("Progression evidence timestamps must include a UTC offset")
        return value


class CharacterProgressionProposal(BaseModel):
    model_config = ConfigDict(frozen=True)

    proposal_id: UUID
    request_id: UUID
    world_id: UUID
    character_id: UUID
    ruleset_id: str
    expected_sheet_version: int = Field(ge=1)
    evidence_ids: tuple[UUID, ...]
    changes: tuple[CharacterProgressionChange, ...]
    proposed_by: str
    rationale: str
    proposed_at: datetime

    @model_validator(mode="after")
    def validate_proposal(self) -> "CharacterProgressionProposal":
        if not self.evidence_ids:
            raise ValueError("A progression proposal requires evidence")
        if not self.changes:
            raise ValueError("A progression proposal requires explicit changes")
        if (
            not self.ruleset_id.strip()
            or not self.proposed_by.strip()
            or not self.rationale.strip()
        ):
            raise ValueError("Ruleset, proposer, and rationale cannot be blank")
        return self

    @field_validator("proposed_at")
    @classmethod
    def require_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("Proposal timestamps must include a UTC offset")
        return value


class ProgressionValidationStatus(str, Enum):
    APPROVED = "approved"
    REJECTED = "rejected"


class CharacterProgressionValidation(BaseModel):
    model_config = ConfigDict(frozen=True)

    validation_id: UUID
    proposal_id: UUID
    status: ProgressionValidationStatus
    validated_by: str
    notes: str
    validated_at: datetime

    @model_validator(mode="after")
    def validate_record(self) -> "CharacterProgressionValidation":
        if not self.validated_by.strip() or not self.notes.strip():
            raise ValueError("Progression validation identity and notes cannot be blank")
        return self

    @field_validator("validated_at")
    @classmethod
    def require_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("Validation timestamps must include a UTC offset")
        return value


class CharacterProgressionApplication(BaseModel):
    model_config = ConfigDict(frozen=True)

    application_id: UUID
    proposal_id: UUID
    character_id: UUID
    prior_sheet_id: UUID
    prior_version: int
    resulting_sheet_version: int
    sheet_before: CharacterSheet
    sheet_after: CharacterSheet
    applied_at: datetime
    applied_changes: tuple[CharacterProgressionChange, ...]
    evidence_ids: tuple[UUID, ...]

    @field_validator("applied_at")
    @classmethod
    def require_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("Application timestamps must include a UTC offset")
        return value
