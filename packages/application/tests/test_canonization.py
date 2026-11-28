from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import pytest

from aether.application import CanonizationService
from aether.contracts import (
    CanonicalProposal,
    CanonicalRecordStatus,
    CanonizationLevel,
)
from aether.domain import CanonizationValidationError
from aether.infrastructure import Database, SqlAlchemySimulationUnitOfWork


def proposal(level: CanonizationLevel, **updates) -> CanonicalProposal:
    values = {
        "proposal_id": uuid4(),
        "world_id": uuid4(),
        "entity_type": "location",
        "entity_id": uuid4(),
        "level": level,
        "statement": "The archive has a hidden side entrance.",
        "origin_type": "narrator",
        "origin_id": "narrator-v1",
        "justification": "A compatible local detail was developed in scene.",
        "proposed_by": "world-architect",
        "proposed_at": datetime(2026, 10, 1, tzinfo=UTC),
        "consistency_notes": ("location is established",),
    }
    values.update(updates)
    return CanonicalProposal(**values)


def service(tmp_path: Path, name: str):
    database = Database.from_path(tmp_path / name)
    database.create_schema()
    return database, CanonizationService(
        lambda: SqlAlchemySimulationUnitOfWork(database.session_factory)
    )


def test_structural_detail_requires_distinct_approval(tmp_path: Path) -> None:
    database, canonization = service(tmp_path, "structural.db")
    item = proposal(CanonizationLevel.STRUCTURAL)
    canonization.submit(item)

    with pytest.raises(CanonizationValidationError, match="distinct"):
        canonization.approve(item.proposal_id, approved_by=item.proposed_by)

    approved = canonization.approve(item.proposal_id, approved_by="project-owner")
    assert approved.status == CanonicalRecordStatus.APPROVED
    assert approved.level == CanonizationLevel.STRUCTURAL
    database.dispose()


def test_persistent_local_fact_requires_consistency_validation(tmp_path: Path) -> None:
    database, canonization = service(tmp_path, "consistency.db")
    item = proposal(CanonizationLevel.PERSISTENT_LOCAL, consistency_notes=())

    with pytest.raises(CanonizationValidationError, match="consistency"):
        canonization.submit(item)
    database.dispose()


def test_revision_and_invalidation_preserve_history(tmp_path: Path) -> None:
    database, canonization = service(tmp_path, "history.db")
    item = proposal(CanonizationLevel.CONTEXTUAL)
    canonization.submit(item)
    approved = canonization.approve(item.proposal_id, approved_by="project-owner")

    invalidated = canonization.invalidate(
        approved.record_id,
        reason="Contradicted by a later verified event.",
    )

    assert invalidated.status == CanonicalRecordStatus.INVALIDATED
    assert invalidated.supersedes_record_id == approved.record_id
    with SqlAlchemySimulationUnitOfWork(database.session_factory) as uow:
        history = uow.repository.list_canonical_records(
            world_id=item.world_id,
            entity_type=item.entity_type,
            entity_id=item.entity_id,
        )
    assert [record.status for record in history] == [
        CanonicalRecordStatus.APPROVED,
        CanonicalRecordStatus.INVALIDATED,
    ]
    database.dispose()
