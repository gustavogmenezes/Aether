from datetime import UTC, datetime
from uuid import UUID, uuid4

from aether.contracts import (
    CanonicalProposal,
    CanonicalRecord,
    CanonicalRecordStatus,
    CanonizationLevel,
)
from aether.domain import CanonizationValidationError
from aether.domain.ports import SimulationUnitOfWorkFactory


class CanonizationService:
    def __init__(self, unit_of_work_factory: SimulationUnitOfWorkFactory) -> None:
        self._unit_of_work_factory = unit_of_work_factory

    def submit(self, proposal: CanonicalProposal) -> CanonicalProposal:
        if proposal.level == CanonizationLevel.EPHEMERAL:
            raise CanonizationValidationError(
                "Ephemeral details are not persisted as canonical proposals"
            )
        if (
            proposal.level == CanonizationLevel.PERSISTENT_LOCAL
            and not proposal.consistency_notes
        ):
            raise CanonizationValidationError(
                "Persistent local facts require consistency validation notes"
            )
        with self._unit_of_work_factory() as unit_of_work:
            existing = unit_of_work.repository.get_canonical_proposal(
                proposal.proposal_id
            )
            if existing is not None:
                if existing != proposal:
                    raise CanonizationValidationError(
                        "Proposal ID already represents another canonical claim"
                    )
                return existing
            unit_of_work.repository.create_canonical_proposal(proposal)
            unit_of_work.commit()
        return proposal

    def approve(
        self,
        proposal_id: UUID,
        *,
        approved_by: str,
        approved_at: datetime | None = None,
    ) -> CanonicalRecord:
        approved_at = approved_at or datetime.now(UTC)
        with self._unit_of_work_factory() as unit_of_work:
            proposal = unit_of_work.repository.get_canonical_proposal(proposal_id)
            if proposal is None:
                raise CanonizationValidationError("Canonical proposal was not found")
            records = unit_of_work.repository.list_canonical_records(
                world_id=proposal.world_id,
                entity_type=proposal.entity_type,
                entity_id=proposal.entity_id,
            )
            if any(record.proposal_id == proposal_id for record in records):
                return next(
                    record for record in records if record.proposal_id == proposal_id
                )
            if not approved_by.strip():
                raise CanonizationValidationError("Approving identity is required")
            if (
                proposal.level == CanonizationLevel.STRUCTURAL
                and approved_by == proposal.proposed_by
            ):
                raise CanonizationValidationError(
                    "Structural approval requires an approving identity distinct from proposer"
                )
            superseded = max(records, key=lambda item: item.revision, default=None)
            record = CanonicalRecord(
                record_id=uuid4(),
                proposal_id=proposal.proposal_id,
                world_id=proposal.world_id,
                entity_type=proposal.entity_type,
                entity_id=proposal.entity_id,
                level=proposal.level,
                statement=proposal.statement,
                status=CanonicalRecordStatus.APPROVED,
                approved_by=approved_by,
                approved_at=approved_at,
                revision=(superseded.revision + 1) if superseded else 1,
                supersedes_record_id=(
                    superseded.record_id if superseded is not None else None
                ),
                provenance={
                    "origin_type": proposal.origin_type,
                    "origin_id": proposal.origin_id,
                    "source_event_id": (
                        str(proposal.source_event_id)
                        if proposal.source_event_id is not None
                        else None
                    ),
                    "justification": proposal.justification,
                    "related_entity_ids": [
                        str(value) for value in proposal.related_entity_ids
                    ],
                    "consistency_notes": list(proposal.consistency_notes),
                    "proposed_by": proposal.proposed_by,
                    "proposed_at": proposal.proposed_at.isoformat(),
                },
            )
            unit_of_work.repository.create_canonical_record(record)
            unit_of_work.commit()
            return record

    def invalidate(
        self,
        record_id: UUID,
        *,
        reason: str,
        invalidated_at: datetime | None = None,
    ) -> CanonicalRecord:
        if not reason.strip():
            raise CanonizationValidationError("Invalidation reason cannot be blank")
        with self._unit_of_work_factory() as unit_of_work:
            current = unit_of_work.repository.get_canonical_record(record_id)
            if current is None:
                raise CanonizationValidationError("Canonical record was not found")
            if current.status == CanonicalRecordStatus.INVALIDATED:
                return current
            invalidated = current.model_copy(
                update={
                    "record_id": uuid4(),
                    "status": CanonicalRecordStatus.INVALIDATED,
                    "invalidated_at": invalidated_at or datetime.now(UTC),
                    "invalidation_reason": reason,
                    "revision": current.revision + 1,
                    "supersedes_record_id": current.record_id,
                }
            )
            unit_of_work.repository.create_canonical_record(invalidated)
            unit_of_work.commit()
            return invalidated
