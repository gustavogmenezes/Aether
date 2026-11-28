from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from .character import RecordProvenance
from .geography import ActorReference


class PublicChannelKind(str, Enum):
    ORAL = "oral"
    PUBLICATION = "publication"
    BROADCAST = "broadcast"
    DIGITAL = "digital"
    INSTITUTIONAL = "institutional"
    SUPERNATURAL = "supernatural"


class PublicChannel(BaseModel):
    model_config = ConfigDict(frozen=True)

    channel_id: UUID
    world_id: UUID
    name: str
    kind: PublicChannelKind
    reach: tuple[str, ...] = ()
    speed: str
    reliability: str
    cost: str
    control: tuple[str, ...] = ()
    interception: tuple[str, ...] = ()
    provenance: RecordProvenance


class PublicInformation(BaseModel):
    model_config = ConfigDict(frozen=True)

    publication_id: UUID
    world_id: UUID
    channel_id: UUID
    publisher_actor: ActorReference | None = None
    title: str
    statement: str
    declared_truth_status: str
    manipulation_tags: tuple[str, ...] = ()
    censorship_tags: tuple[str, ...] = ()
    diegetic_language_id: UUID | None = None
    published_at: datetime
    provenance: RecordProvenance


class CollectiveReception(BaseModel):
    model_config = ConfigDict(frozen=True)

    reception_id: UUID
    publication_id: UUID
    population_id: UUID
    received_at: datetime
    reaction_summary: str
    opinion_dimensions: dict[str, str] = Field(default_factory=dict)
    accepted: bool | None = None
    confidence_semantics: tuple[str, ...] = ()
    provenance: RecordProvenance


class PublicationPayload(BaseModel):
    model_config = ConfigDict(frozen=True)

    publication: PublicInformation
    receptions: tuple[CollectiveReception, ...] = ()


class CreativeWorkKind(str, Enum):
    MUSIC = "music"
    LITERATURE = "literature"
    VISUAL_ART = "visual-art"
    PERFORMANCE = "performance"
    ARCHITECTURE = "architecture"
    CRAFT = "craft"
    GAME = "game"
    OTHER = "other"


class CreativeWork(BaseModel):
    model_config = ConfigDict(frozen=True)

    work_id: UUID
    world_id: UUID
    kind: CreativeWorkKind
    title: str
    creator_actor: ActorReference | None = None
    context: str | None = None
    style: tuple[str, ...] = ()
    traditions: tuple[str, ...] = ()
    materials: tuple[str, ...] = ()
    technique: tuple[str, ...] = ()
    intent: tuple[str, ...] = ()
    audience_tags: tuple[str, ...] = ()
    influence_tags: tuple[str, ...] = ()
    censorship_tags: tuple[str, ...] = ()
    provenance: RecordProvenance


class LeisureRoutine(BaseModel):
    model_config = ConfigDict(frozen=True)

    routine_id: UUID
    actor: ActorReference
    activity: str
    schedule: tuple[str, ...] = ()
    location_ids: tuple[UUID, ...] = ()
    preference_notes: tuple[str, ...] = ()
    mechanical_reward_tags: tuple[str, ...] = ()
    provenance: RecordProvenance


class VisualIdentity(BaseModel):
    model_config = ConfigDict(frozen=True)

    identity_id: UUID
    subject: ActorReference
    canonical_traits: dict[str, str] = Field(default_factory=dict)
    current_state: dict[str, str] = Field(default_factory=dict)
    direction: tuple[str, ...] = ()
    provenance: RecordProvenance


class SonicIdentity(BaseModel):
    model_config = ConfigDict(frozen=True)

    identity_id: UUID
    subject: ActorReference
    canonical_traits: dict[str, str] = Field(default_factory=dict)
    current_state: dict[str, str] = Field(default_factory=dict)
    soundscape_tags: tuple[str, ...] = ()
    provenance: RecordProvenance


class GeneratedAssetKind(str, Enum):
    IMAGE = "image"
    AUDIO = "audio"


class GeneratedAsset(BaseModel):
    model_config = ConfigDict(frozen=True)

    asset_id: UUID
    subject: ActorReference
    kind: GeneratedAssetKind
    canonical_identity_id: UUID
    filesystem_reference: str
    generated_at: datetime
    prompt_version: str
    model_version: str
    diegetic: bool
    provenance: RecordProvenance

    @field_validator("filesystem_reference", "prompt_version", "model_version")
    @classmethod
    def metadata_must_not_be_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Generated asset metadata cannot be blank")
        return value
