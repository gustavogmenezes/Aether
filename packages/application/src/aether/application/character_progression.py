from datetime import UTC, datetime
from uuid import uuid4

from pydantic import ValidationError

from aether.contracts import (
    CharacterProgressionApplication,
    CharacterProgressionEvidence,
    CharacterProgressionProposal,
    CharacterProgressionValidation,
    CharacterSheet,
    ProgressionValidationStatus,
    StorytellingCreationProfile,
)
from aether.domain import (
    CharacterGenesisError,
    CharacterProgressionError,
    StaleWorldStateError,
)
from aether.domain.ports import SimulationUnitOfWorkFactory
from aether.engines import (
    CharacterGenesisEngine,
    CharacterGenesisValidationError,
    CharacterProgressionValidationError,
)


class CharacterGenesisService:
    def __init__(
        self,
        unit_of_work_factory: SimulationUnitOfWorkFactory,
        genesis_engine: CharacterGenesisEngine | None = None,
    ) -> None:
        self._unit_of_work_factory = unit_of_work_factory
        self._genesis_engine = genesis_engine or CharacterGenesisEngine()

    def create(
        self,
        sheet: CharacterSheet,
        profile: StorytellingCreationProfile,
    ) -> CharacterSheet:
        try:
            self._genesis_engine.validate_sheet(sheet, profile)
        except CharacterGenesisValidationError as error:
            raise CharacterGenesisError(str(error)) from error
        with self._unit_of_work_factory() as unit_of_work:
            existing = unit_of_work.repository.get_character_sheet(sheet.character_id)
            if existing is not None:
                if existing != sheet:
                    raise CharacterGenesisError(
                        "Character already has a different genesis sheet"
                    )
                return existing
            unit_of_work.repository.create_character_sheet(sheet)
            unit_of_work.commit()
        return sheet


class CharacterProgressionService:
    def __init__(
        self,
        unit_of_work_factory: SimulationUnitOfWorkFactory,
        genesis_engine: CharacterGenesisEngine | None = None,
    ) -> None:
        self._unit_of_work_factory = unit_of_work_factory
        self._genesis_engine = genesis_engine or CharacterGenesisEngine()

    def record_evidence(
        self, evidence: CharacterProgressionEvidence
    ) -> CharacterProgressionEvidence:
        with self._unit_of_work_factory() as unit_of_work:
            existing = unit_of_work.repository.get_progression_evidence(
                evidence.evidence_id
            )
            if existing is not None:
                if existing != evidence:
                    raise CharacterProgressionError(
                        "Evidence ID already represents different evidence"
                    )
                return existing
            for event_id in evidence.event_ids:
                event = unit_of_work.repository.get_event(event_id)
                if event is None:
                    raise CharacterProgressionError(
                        f"Progression evidence references unknown event {event_id}"
                    )
                if event.world_id != evidence.world_id:
                    raise CharacterProgressionError(
                        "Progression evidence event belongs to another world"
                    )
            unit_of_work.repository.create_progression_evidence(evidence)
            unit_of_work.commit()
        return evidence

    def submit(
        self,
        proposal: CharacterProgressionProposal,
        profile: StorytellingCreationProfile,
    ) -> CharacterProgressionProposal:
        with self._unit_of_work_factory() as unit_of_work:
            existing = unit_of_work.repository.get_progression_proposal_by_request(
                proposal.request_id
            )
            if existing is not None:
                if existing != proposal:
                    raise CharacterProgressionError(
                        "Request ID already represents another progression proposal"
                    )
                sheet = unit_of_work.repository.get_character_sheet(
                    existing.character_id
                )
                self._validate_context(
                    sheet, existing, profile, check_version=False
                )
                return existing
            sheet = unit_of_work.repository.get_character_sheet(proposal.character_id)
            self._validate_context(sheet, proposal, profile)
            assert sheet is not None
            evidence = []
            for evidence_id in proposal.evidence_ids:
                item = unit_of_work.repository.get_progression_evidence(evidence_id)
                if item is None:
                    raise CharacterProgressionError(
                        "Every progression proposal must reference persisted evidence"
                    )
                if (
                    item.character_id != proposal.character_id
                    or item.world_id != proposal.world_id
                ):
                    raise CharacterProgressionError(
                        "Progression evidence does not belong to the proposed character"
                    )
                evidence.append(item)
            if not evidence:
                raise CharacterProgressionError("Progression requires event evidence")
            try:
                self._genesis_engine.apply_changes(sheet, proposal.changes)
            except (CharacterProgressionValidationError, ValidationError) as error:
                raise CharacterProgressionError(str(error)) from error
            unit_of_work.repository.create_progression_proposal(proposal)
            unit_of_work.commit()
        return proposal

    def approve(
        self,
        proposal_id,
        profile: StorytellingCreationProfile,
        *,
        validated_by: str,
        notes: str = "Explicit changes validated against the supplied ruleset.",
        validated_at: datetime | None = None,
    ) -> CharacterProgressionValidation:
        with self._unit_of_work_factory() as unit_of_work:
            proposal = unit_of_work.repository.get_progression_proposal(proposal_id)
            if proposal is None:
                raise CharacterProgressionError("Progression proposal was not found")
            sheet = unit_of_work.repository.get_character_sheet(proposal.character_id)
            self._validate_context(sheet, proposal, profile)
            validations = unit_of_work.repository.list_progression_validations(
                proposal_id
            )
            if any(
                item.status == ProgressionValidationStatus.REJECTED
                for item in validations
            ):
                raise CharacterProgressionError(
                    "A rejected progression proposal cannot be approved"
                )
            if any(
                item.status == ProgressionValidationStatus.APPROVED
                for item in validations
            ):
                return next(
                    item
                    for item in validations
                    if item.status == ProgressionValidationStatus.APPROVED
                )
            if not validated_by.strip():
                raise CharacterProgressionError("Validation identity is required")
            validation = CharacterProgressionValidation(
                validation_id=uuid4(),
                proposal_id=proposal_id,
                status=ProgressionValidationStatus.APPROVED,
                validated_by=validated_by,
                notes=notes,
                validated_at=validated_at or datetime.now(UTC),
            )
            unit_of_work.repository.create_progression_validation(validation)
            unit_of_work.commit()
            return validation

    def reject(
        self,
        proposal_id,
        profile: StorytellingCreationProfile,
        *,
        validated_by: str,
        notes: str,
        validated_at: datetime | None = None,
    ) -> CharacterProgressionValidation:
        if not validated_by.strip() or not notes.strip():
            raise CharacterProgressionError(
                "Rejection requires a validating identity and reason"
            )
        with self._unit_of_work_factory() as unit_of_work:
            proposal = unit_of_work.repository.get_progression_proposal(proposal_id)
            if proposal is None:
                raise CharacterProgressionError("Progression proposal was not found")
            sheet = unit_of_work.repository.get_character_sheet(proposal.character_id)
            self._validate_context(sheet, proposal, profile)
            if unit_of_work.repository.get_progression_application(proposal_id):
                raise CharacterProgressionError(
                    "An applied progression proposal cannot be rejected"
                )
            validations = unit_of_work.repository.list_progression_validations(
                proposal_id
            )
            if validations:
                raise CharacterProgressionError(
                    "Progression proposal already has an immutable validation"
                )
            validation = CharacterProgressionValidation(
                validation_id=uuid4(),
                proposal_id=proposal_id,
                status=ProgressionValidationStatus.REJECTED,
                validated_by=validated_by,
                notes=notes,
                validated_at=validated_at or datetime.now(UTC),
            )
            unit_of_work.repository.create_progression_validation(validation)
            unit_of_work.commit()
            return validation

    def apply(
        self,
        proposal_id,
        profile: StorytellingCreationProfile,
        *,
        applied_at: datetime | None = None,
    ) -> CharacterProgressionApplication:
        with self._unit_of_work_factory() as unit_of_work:
            proposal = unit_of_work.repository.get_progression_proposal(proposal_id)
            if proposal is None:
                raise CharacterProgressionError("Progression proposal was not found")
            sheet = unit_of_work.repository.get_character_sheet(proposal.character_id)
            self._validate_context(
                sheet, proposal, profile, check_version=False
            )
            assert sheet is not None
            existing = unit_of_work.repository.get_progression_application(proposal_id)
            if existing is not None:
                return existing
            if sheet.version != proposal.expected_sheet_version:
                raise StaleWorldStateError(
                    "Character sheet version does not match progression proposal"
                )
            validations = unit_of_work.repository.list_progression_validations(
                proposal_id
            )
            if not validations or not any(
                item.status == ProgressionValidationStatus.APPROVED
                for item in validations
            ):
                raise CharacterProgressionError(
                    "Progression cannot be applied before approval"
                )
            if any(
                item.status == ProgressionValidationStatus.REJECTED
                for item in validations
            ):
                raise CharacterProgressionError(
                    "Progression proposal has an immutable rejection record"
                )
            try:
                changed = self._genesis_engine.apply_changes(sheet, proposal.changes)
            except (CharacterProgressionValidationError, ValidationError) as error:
                raise CharacterProgressionError(str(error)) from error
            resulting = changed.model_copy(
                update={
                    "version": sheet.version + 1,
                    "updated_at": applied_at or datetime.now(UTC),
                }
            )
            application = CharacterProgressionApplication(
                application_id=uuid4(),
                proposal_id=proposal.proposal_id,
                character_id=proposal.character_id,
                prior_sheet_id=sheet.sheet_id,
                prior_version=sheet.version,
                resulting_sheet_version=resulting.version,
                sheet_before=sheet,
                sheet_after=resulting,
                applied_at=resulting.updated_at,
                applied_changes=proposal.changes,
                evidence_ids=proposal.evidence_ids,
            )
            unit_of_work.repository.save_character_sheet(
                resulting, expected_version=proposal.expected_sheet_version
            )
            unit_of_work.repository.create_progression_application(application)
            unit_of_work.commit()
            return application

    @staticmethod
    def _validate_context(
        sheet: CharacterSheet | None,
        proposal: CharacterProgressionProposal,
        profile: StorytellingCreationProfile,
        *,
        check_version: bool = True,
    ) -> None:
        if sheet is None:
            raise CharacterProgressionError("Character sheet was not found")
        if (
            profile.ruleset_id != sheet.ruleset_id
            or proposal.ruleset_id != sheet.ruleset_id
            or profile.world_id != sheet.world_id
            or proposal.world_id != sheet.world_id
        ):
            raise CharacterProgressionError("Progression ruleset or world mismatch")
        if proposal.character_id != sheet.character_id:
            raise CharacterProgressionError("Progression character mismatch")
        if check_version and proposal.expected_sheet_version != sheet.version:
            raise StaleWorldStateError(
                "Character sheet version does not match progression proposal"
            )
