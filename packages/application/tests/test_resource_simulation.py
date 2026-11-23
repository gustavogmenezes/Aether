from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from uuid import UUID, uuid4

import pytest
from sqlalchemy import func, select

from aether.application import TemporalAdvanceService
from aether.application import NpcDecisionService
from aether.contracts import (
    AdvanceTimeCommand,
    Goal,
    GoalStatus,
    Plan,
    PlanStatus,
    PlanStep,
    PlanStepStatus,
    RecordProvenance,
    ResourceBalance,
    ResourceEffect,
    ResourceEffectOutcome,
    ResourceKind,
    ResourceOwnerKind,
    ResourceReservation,
    ScheduledEvent,
)
from aether.domain import ResourceInvariantError, WorldClockState
from aether.infrastructure import Database, SqlAlchemySimulationUnitOfWork
from aether.infrastructure.models import (
    EventLedgerModel,
    ResourceTransactionModel,
)


def setup_resource_step(
    tmp_path: Path,
) -> tuple[Database, UUID, UUID, UUID, UUID, UUID, datetime]:
    database = Database.from_path(tmp_path / "resources.db")
    database.create_schema()
    now = datetime(2026, 1, 1, 12, tzinfo=UTC)
    world_id = uuid4()
    timeline_id = uuid4()
    character_id = uuid4()
    provenance = RecordProvenance(
        source_type="test",
        source_id="resource-test",
        created_at=now,
        updated_at=now,
        version=1,
    )
    goal = Goal(
        goal_id=uuid4(),
        character_id=character_id,
        desired_outcome="Establish a field camp",
        status=GoalStatus.ACTIVE,
        provenance=provenance,
    )
    plan = Plan(
        plan_id=uuid4(),
        character_id=character_id,
        goal_id=goal.goal_id,
        name="Build the camp",
        status=PlanStatus.ACTIVE,
        provenance=provenance,
    )
    step = PlanStep(
        step_id=uuid4(),
        plan_id=plan.plan_id,
        sequence=0,
        action_intent="Build a shelter",
        status=PlanStepStatus.SCHEDULED,
        resource_effects=(
            ResourceEffect(
                resource_code="timber",
                delta=Decimal("-2"),
                on_outcome=ResourceEffectOutcome.COMPLETED,
            ),
            ResourceEffect(
                resource_code="shelter",
                delta=Decimal("1"),
                on_outcome=ResourceEffectOutcome.COMPLETED,
            ),
        ),
        provenance=provenance,
    )
    event = ScheduledEvent(
        event_id=uuid4(),
        world_id=world_id,
        timeline_id=timeline_id,
        scheduled_at=now + timedelta(minutes=10),
        event_type="npc-plan-step",
        source_type="npc-decision",
        source_id="resource-test",
        payload_version="1",
        payload={
            "character_id": str(character_id),
            "plan_step_id": str(step.step_id),
        },
    )
    with SqlAlchemySimulationUnitOfWork(database.session_factory) as uow:
        uow.repository.create_clock(
            WorldClockState(world_id, timeline_id, now, version=0)
        )
        for code, quantity in (("timber", Decimal("5")), ("shelter", Decimal("0"))):
            uow.repository.create_resource_balance(
                ResourceBalance(
                    balance_id=uuid4(),
                    owner_kind=ResourceOwnerKind.CHARACTER,
                    owner_id=character_id,
                    resource_code=code,
                    resource_kind=ResourceKind.MATERIAL,
                    quantity=quantity,
                    reserved=Decimal("0"),
                    version=0,
                )
            )
        uow.repository.create_goal(goal)
        uow.repository.create_plan(plan)
        uow.repository.create_plan_step(step)
        uow.repository.reserve_resource(
            ResourceReservation(
                reservation_id=uuid4(),
                scheduled_event_id=event.event_id,
                owner_kind=ResourceOwnerKind.CHARACTER,
                owner_id=character_id,
                resource_code="timber",
                quantity=Decimal("2"),
            )
        )
        uow.repository.schedule_event(event)
    return (
        database,
        world_id,
        timeline_id,
        character_id,
        step.step_id,
        event.event_id,
        now,
    )


def test_plan_consequence_consumes_and_produces_resources_atomically(
    tmp_path: Path,
) -> None:
    (
        database,
        world_id,
        timeline_id,
        character_id,
        _,
        event_id,
        _,
    ) = setup_resource_step(tmp_path)
    service = TemporalAdvanceService(
        lambda: SqlAlchemySimulationUnitOfWork(database.session_factory)
    )

    service.advance_time(
        AdvanceTimeCommand(
            simulation_run_id=uuid4(),
            world_id=world_id,
            timeline_id=timeline_id,
            duration=timedelta(minutes=10),
        )
    )

    with SqlAlchemySimulationUnitOfWork(database.session_factory) as uow:
        timber = uow.repository.get_resource_balance(
            ResourceOwnerKind.CHARACTER,
            character_id,
            "timber",
        )
        shelter = uow.repository.get_resource_balance(
            ResourceOwnerKind.CHARACTER,
            character_id,
            "shelter",
        )
        assert timber is not None
        assert shelter is not None
        assert timber.quantity == Decimal("3")
        assert timber.reserved == Decimal("0")
        assert shelter.quantity == Decimal("1")
        transactions = uow.repository.list_resource_transactions(event_id)
        assert [(item.resource_code, item.delta) for item in transactions] == [
            ("shelter", Decimal("1")),
            ("timber", Decimal("-2")),
        ]
        ledger = uow.session.scalars(select(EventLedgerModel)).one()
        assert ledger.payload["resource_changes"] == {
            "shelter": "1",
            "timber": "-2",
        }
    database.dispose()


def test_insufficient_resource_cannot_be_reserved(tmp_path: Path) -> None:
    database, _, _, character_id, _, event_id, _ = setup_resource_step(tmp_path)

    with pytest.raises(ResourceInvariantError, match="Insufficient"):
        with SqlAlchemySimulationUnitOfWork(database.session_factory) as uow:
            uow.repository.reserve_resource(
                ResourceReservation(
                    reservation_id=uuid4(),
                    scheduled_event_id=event_id,
                    owner_kind=ResourceOwnerKind.CHARACTER,
                    owner_id=character_id,
                    resource_code="timber",
                    quantity=Decimal("4"),
                )
            )

    database.dispose()


def test_resource_failure_rolls_back_consumption_and_preserves_reservation(
    tmp_path: Path,
) -> None:
    (
        database,
        world_id,
        timeline_id,
        character_id,
        step_id,
        event_id,
        now,
    ) = setup_resource_step(tmp_path)

    class BrokenResolver:
        def resolve(self, event, plan_step):
            raise RuntimeError("resource resolution interrupted")

    service = TemporalAdvanceService(
        lambda: SqlAlchemySimulationUnitOfWork(database.session_factory),
        scheduled_resolver=BrokenResolver(),
    )
    with pytest.raises(RuntimeError, match="resource resolution interrupted"):
        service.advance_time(
            AdvanceTimeCommand(
                simulation_run_id=uuid4(),
                world_id=world_id,
                timeline_id=timeline_id,
                duration=timedelta(minutes=10),
            )
        )

    with SqlAlchemySimulationUnitOfWork(database.session_factory) as uow:
        timber = uow.repository.get_resource_balance(
            ResourceOwnerKind.CHARACTER,
            character_id,
            "timber",
        )
        assert timber is not None
        assert timber.quantity == Decimal("5")
        assert timber.reserved == Decimal("2")
        reservations = uow.repository.list_resource_reservations(event_id)
        assert len(reservations) == 1
        assert not reservations[0].applied
        assert not reservations[0].cancelled
        assert uow.repository.get_plan_step(step_id).status == PlanStepStatus.SCHEDULED
        assert uow.session.scalar(
            select(func.count(ResourceTransactionModel.transaction_id))
        ) == 0
        assert uow.repository.get_clock(world_id, timeline_id).current_time == now
    database.dispose()


def test_npc_context_uses_persisted_resource_availability(
    tmp_path: Path,
) -> None:
    database, _, _, character_id, _, _, _ = setup_resource_step(tmp_path)
    service = NpcDecisionService(
        lambda: SqlAlchemySimulationUnitOfWork(database.session_factory)
    )

    availability = service.persisted_resource_availability(
        character_id,
        ("timber", "shelter", "missing-resource"),
    )

    assert [(item.name, item.available) for item in availability] == [
        ("timber", True),
        ("shelter", False),
        ("missing-resource", False),
    ]
    database.dispose()
