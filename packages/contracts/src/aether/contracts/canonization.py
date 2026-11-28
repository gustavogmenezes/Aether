from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator


class CanonizationLevel(int, Enum):
    EPHEMERAL = 0
    CONTEXTUAL = 1
    PERSISTENT_LOCAL = 2
    STRUCTURAL = 3


class CanonicalRecordStatus(str, Enum):
    DRAFT = "draft"
    PROPOSED = "proposed"
    APPROVED = "approved"
    PUBLISHED = "published"
    DEPRECATED = "deprecated"
    INVALIDATED = "invalidated"


class CanonicalProposal(BaseModel):
    model_config = ConfigDict(frozen=True)

    proposal_id: UUID
    world_id: UUID
    entity_type: str
    entity_id: UUID | None
    level: CanonizationLevel
    statement: str
    origin_type: str
    origin_id: str
    source_event_id: UUID | None = None
    justification: str
    related_entity_ids: tuple[UUID, ...] = ()
    proposed_by: str
    proposed_at: datetime
    consistency_notes: tuple[str, ...] = ()
    status: CanonicalRecordStatus = CanonicalRecordStatus.PROPOSED


class CanonicalRecord(BaseModel):
    model_config = ConfigDict(frozen=True)

    record_id: UUID
    proposal_id: UUID
    world_id: UUID
    entity_type: str
    entity_id: UUID | None
    level: CanonizationLevel
    statement: str
    status: CanonicalRecordStatus
    approved_by: str | None = None
    approved_at: datetime | None = None
    revision: int = Field(ge=1)
    supersedes_record_id: UUID | None = None
    invalidated_at: datetime | None = None
    invalidation_reason: str | None = None
    provenance: dict[str, object]

    @model_validator(mode="after")
    def approved_records_require_author(self) -> "CanonicalRecord":
        if self.status == CanonicalRecordStatus.APPROVED and not self.approved_by:
            raise ValueError("Approved canonical records require an approving identity")
        if self.status == CanonicalRecordStatus.INVALIDATED and not self.invalidation_reason:
            raise ValueError("Invalidated canonical records require a reason")
        return self
