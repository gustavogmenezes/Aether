from datetime import datetime
from decimal import Decimal
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class ResourceKind(str, Enum):
    MATERIAL = "material"
    SOCIAL = "social"
    STRUCTURAL = "structural"
    PERSONAL = "personal"


class ResourceOwnerKind(str, Enum):
    CHARACTER = "character"
    ORGANIZATION = "organization"


class ResourceEffectOutcome(str, Enum):
    COMPLETED = "completed"
    FAILED = "failed"


class ResourceEffect(BaseModel):
    model_config = ConfigDict(frozen=True)

    resource_code: str
    delta: Decimal
    on_outcome: ResourceEffectOutcome

    @field_validator("resource_code")
    @classmethod
    def resource_code_must_not_be_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Resource code cannot be blank")
        return value

    @field_validator("delta")
    @classmethod
    def delta_must_not_be_zero(cls, value: Decimal) -> Decimal:
        if value == 0:
            raise ValueError("Resource delta cannot be zero")
        return value


class ResourceBalance(BaseModel):
    model_config = ConfigDict(frozen=True)

    balance_id: UUID
    owner_kind: ResourceOwnerKind
    owner_id: UUID
    resource_code: str
    resource_kind: ResourceKind
    quantity: Decimal = Field(ge=0)
    reserved: Decimal = Field(ge=0)
    version: int = Field(ge=0)

    @model_validator(mode="after")
    def reserved_cannot_exceed_quantity(self) -> "ResourceBalance":
        if self.reserved > self.quantity:
            raise ValueError("Reserved resources cannot exceed total quantity")
        return self


class ResourceReservation(BaseModel):
    model_config = ConfigDict(frozen=True)

    reservation_id: UUID
    scheduled_event_id: UUID
    owner_kind: ResourceOwnerKind
    owner_id: UUID
    resource_code: str
    quantity: Decimal = Field(gt=0)
    applied: bool = False
    cancelled: bool = False


class ResourceTransaction(BaseModel):
    model_config = ConfigDict(frozen=True)

    transaction_id: UUID
    owner_kind: ResourceOwnerKind
    owner_id: UUID
    resource_code: str
    delta: Decimal
    resulting_quantity: Decimal = Field(ge=0)
    scheduled_event_id: UUID | None = None
    event_id: UUID | None = None
    simulation_run_id: UUID | None = None
    occurred_at: datetime

    @field_validator("occurred_at")
    @classmethod
    def require_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("Resource transaction time must include a UTC offset")
        return value
