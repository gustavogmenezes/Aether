from datetime import datetime
from uuid import UUID

from aether.contracts import (
    CharacterCulturalContext,
    CulturalAffiliationTargetType,
    CulturalAffiliationVisibility,
    CulturalChangeRecord,
    CultureDefinition,
    CharacterLanguageProficiency,
    Dialect,
    EducationEnrollment,
    EducationProgram,
    IndividualBeliefRecord,
    KnowledgeArtifact,
    Language,
    LearningOpportunity,
    MetaphysicalTruth,
    ReligionTradition,
    ScheduledEvent,
    Technology,
    WritingSystem,
    IndividualCulturalAffiliation,
    SocialGroup,
)
from aether.domain.ports import SimulationUnitOfWorkFactory


class CulturalSystemsService:
    """Persists authored cultural definitions and immutable participation records."""

    def __init__(self, unit_of_work_factory: SimulationUnitOfWorkFactory) -> None:
        self._unit_of_work_factory = unit_of_work_factory

    def register_knowledge_artifact(self, artifact: KnowledgeArtifact) -> None:
        with self._unit_of_work_factory() as unit_of_work:
            unit_of_work.repository.create_knowledge_artifact(artifact)

    def register_culture(self, culture: CultureDefinition) -> None:
        with self._unit_of_work_factory() as unit_of_work:
            unit_of_work.repository.create_culture_definition(culture)

    def register_social_group(self, group: SocialGroup) -> None:
        with self._unit_of_work_factory() as unit_of_work:
            for culture_id in group.culture_ids:
                culture = unit_of_work.repository.get_culture_definition(culture_id)
                if culture is None:
                    raise KeyError(f"Social group references unknown culture {culture_id}")
                if culture.world_id != group.world_id:
                    raise ValueError(
                        "Social group culture references belong to another world"
                    )
            unit_of_work.repository.create_social_group(group)

    def record_individual_cultural_affiliation(
        self, affiliation: IndividualCulturalAffiliation
    ) -> None:
        with self._unit_of_work_factory() as unit_of_work:
            self._require_affiliation_target(unit_of_work.repository, affiliation)
            unit_of_work.repository.create_individual_cultural_affiliation(
                affiliation
            )

    def character_cultural_context(
        self,
        character_id: UUID,
        observer_character_id: UUID,
        as_of: datetime,
    ) -> CharacterCulturalContext:
        """Assemble visible affiliations without deriving character behavior."""
        with self._unit_of_work_factory() as unit_of_work:
            visible = tuple(
                affiliation
                for affiliation in (
                    unit_of_work.repository.list_individual_cultural_affiliations(
                        character_id
                    )
                )
                if affiliation.effective_from <= as_of
                and (
                    affiliation.effective_until is None
                    or affiliation.effective_until >= as_of
                )
                and (
                    observer_character_id == character_id
                    or affiliation.visibility
                    is CulturalAffiliationVisibility.PUBLIC
                    or (
                        affiliation.visibility
                        is CulturalAffiliationVisibility.RESTRICTED
                        and observer_character_id
                        in affiliation.visible_to_character_ids
                    )
                )
            )
            culture_ids = dict.fromkeys(
                affiliation.target_id
                for affiliation in visible
                if affiliation.target_type
                is CulturalAffiliationTargetType.CULTURE
            )
            group_ids = dict.fromkeys(
                affiliation.target_id
                for affiliation in visible
                if affiliation.target_type
                is CulturalAffiliationTargetType.SOCIAL_GROUP
            )
            cultures = tuple(
                culture
                for culture_id in culture_ids
                if (
                    culture
                    := unit_of_work.repository.get_culture_definition(culture_id)
                )
                is not None
            )
            groups = tuple(
                group
                for group_id in group_ids
                if (group := unit_of_work.repository.get_social_group(group_id))
                is not None
            )
        return CharacterCulturalContext(
            character_id=character_id,
            observer_character_id=observer_character_id,
            as_of=as_of,
            affiliations=visible,
            cultures=cultures,
            social_groups=groups,
        )

    def record_cultural_change(
        self, record: CulturalChangeRecord
    ) -> CulturalChangeRecord:
        with self._unit_of_work_factory() as unit_of_work:
            existing = unit_of_work.repository.get_cultural_change_record(
                record.record_id
            )
            if existing is not None:
                if existing != record:
                    raise ValueError(
                        "Cultural change record ID was already used with "
                        "different content"
                    )
                return existing

            event = unit_of_work.repository.get_event(record.source_event_id)
            if event is None:
                raise KeyError(f"Unknown source event {record.source_event_id}")
            if event.world_id != record.world_id:
                raise ValueError("Cultural change event belongs to another world")
            if event.occurred_at != record.occurred_at:
                raise ValueError(
                    "Cultural change occurrence must match its source event"
                )
            target = (
                unit_of_work.repository.get_culture_definition(record.target_id)
                if record.target_type is CulturalAffiliationTargetType.CULTURE
                else unit_of_work.repository.get_social_group(record.target_id)
            )
            if target is None:
                raise KeyError(f"Unknown cultural target {record.target_id}")
            if target.world_id != record.world_id:
                raise ValueError("Cultural change target belongs to another world")
            unit_of_work.repository.create_cultural_change_record(record)
            return record

    def list_cultural_change_history(
        self,
        target_type: CulturalAffiliationTargetType,
        target_id: UUID,
    ) -> tuple[CulturalChangeRecord, ...]:
        with self._unit_of_work_factory() as unit_of_work:
            return unit_of_work.repository.list_cultural_change_records(
                target_type, target_id
            )

    @staticmethod
    def _require_affiliation_target(repository, affiliation) -> None:
        target = (
            repository.get_culture_definition(affiliation.target_id)
            if affiliation.target_type is CulturalAffiliationTargetType.CULTURE
            else repository.get_social_group(affiliation.target_id)
        )
        if target is None:
            raise KeyError(f"Unknown cultural affiliation target {affiliation.target_id}")

    def register_technology(self, technology: Technology) -> None:
        with self._unit_of_work_factory() as unit_of_work:
            unit_of_work.repository.create_technology(technology)

    def register_language(self, language: Language) -> None:
        with self._unit_of_work_factory() as unit_of_work:
            unit_of_work.repository.create_language(language)

    def register_dialect(self, dialect: Dialect) -> None:
        with self._unit_of_work_factory() as unit_of_work:
            unit_of_work.repository.create_dialect(dialect)

    def register_writing_system(self, writing_system: WritingSystem) -> None:
        with self._unit_of_work_factory() as unit_of_work:
            unit_of_work.repository.create_writing_system(writing_system)

    def record_language_proficiency(
        self, proficiency: CharacterLanguageProficiency
    ) -> None:
        with self._unit_of_work_factory() as unit_of_work:
            unit_of_work.repository.create_character_language_proficiency(
                proficiency
            )

    def register_education_program(self, program: EducationProgram) -> None:
        with self._unit_of_work_factory() as unit_of_work:
            unit_of_work.repository.create_education_program(program)

    def record_enrollment(self, enrollment: EducationEnrollment) -> None:
        with self._unit_of_work_factory() as unit_of_work:
            unit_of_work.repository.create_education_enrollment(enrollment)

    def record_learning_opportunity(
        self, opportunity: LearningOpportunity
    ) -> None:
        with self._unit_of_work_factory() as unit_of_work:
            unit_of_work.repository.create_learning_opportunity(opportunity)

    def register_tradition(self, tradition: ReligionTradition) -> None:
        with self._unit_of_work_factory() as unit_of_work:
            unit_of_work.repository.create_religion_tradition(tradition)

    def record_individual_belief(self, belief: IndividualBeliefRecord) -> None:
        with self._unit_of_work_factory() as unit_of_work:
            unit_of_work.repository.create_individual_belief(belief)

    def register_world_metaphysical_truth(self, truth: MetaphysicalTruth) -> None:
        with self._unit_of_work_factory() as unit_of_work:
            unit_of_work.repository.create_metaphysical_truth(truth)

    def schedule_authorized_cultural_event(self, event: ScheduledEvent) -> None:
        if event.event_type not in {
            "knowledge-transmission",
            "technology-use-completion",
            "learning-assessment",
            "religious-ritual",
        }:
            raise ValueError("Unsupported cultural scheduled event type")
        with self._unit_of_work_factory() as unit_of_work:
            unit_of_work.repository.schedule_event(event)
