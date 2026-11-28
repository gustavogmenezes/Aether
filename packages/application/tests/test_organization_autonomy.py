from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from uuid import UUID, uuid4

import pytest
from sqlalchemy import func, select

from aether.application import OrganizationDecisionService, TemporalAdvanceService
from aether.contracts import (
    AdvanceTimeCommand,
    DecisionCircumstance,
    GoalStatus,
    OrganizationAuthorityGrant,
    OrganizationDecisionContext,
    OrganizationDecisionProposal,
    OrganizationDecisionType,
    OrganizationGoal,
    OrganizationGovernance,
    OrganizationIdentity,
    OrganizationMembership,
    OrganizationMotive,
    OrganizationPlan,
    OrganizationPlanContext,
    OrganizationPlanStep,
    OrganizationRole,
    PlanStatus,
    PlanStepStatus,
    RecordProvenance,
    ResourceAvailability,
    ResourceBalance,
    ResourceEffect,
    ResourceEffectOutcome,
    ResourceKind,
    ResourceOwnerKind,
)
from aether.domain import OrganizationAuthorityError, WorldClockState
from aether.infrastructure import Database, SqlAlchemySimulationUnitOfWork
from aether.infrastructure.models import (
    EventLedgerModel,
    ResourceTransactionModel,
    ScheduledEventModel,
)


def provenance(now: datetime) -> RecordProvenance:
    return RecordProvenance(
        source_type="test",
        source_id="organization-test",
        created_at=now,
        updated_at=now,
        version=1,
    )


def organization_context(now: datetime, *, with_resource_authority: bool = True):
    organization_id = uuid4()
    steward_id = uuid4()
    advisor_id = uuid4()
    role = OrganizationRole(
        role_code="quartermaster",
        description="May commit declared stores to approved operations.",
        permission_codes=(
            "consume-resource:timber",
            "produce-resource:shelter",
        ),
    )
    identity = OrganizationIdentity(
        identity_id=uuid4(),
        organization_id=organization_id,
        display_name="The North Quay Cooperative",
        purpose="Maintain harbor supply",
        history="Founded before the present harbor administration.",
        internal_conflicts=("trade faction favors expansion", "craft faction favors caution"),
        provenance=provenance(now),
    )
    governance = OrganizationGovernance(
        governance_id=uuid4(),
        organization_id=organization_id,
        system="council-with-delegated-quartermaster",
        decision_rules=("formal resource commitments require a role grant",),
        role_definitions=(role,),
        provenance=provenance(now),
    )
    steward = OrganizationMembership(
        membership_id=uuid4(),
        organization_id=organization_id,
        character_id=steward_id,
        formal_roles=("quartermaster",),
        provenance=provenance(now),
    )
    advisor = OrganizationMembership(
        membership_id=uuid4(),
        organization_id=organization_id,
        character_id=advisor_id,
        informal_roles=("respected-founder",),
        effective_influence=("shapes council debate without signing commitments",),
        provenance=provenance(now),
    )
    grant = OrganizationAuthorityGrant(
        grant_id=uuid4(),
        organization_id=organization_id,
        character_id=steward_id,
        role_code="quartermaster",
        permission_codes=(
            ("consume-resource:timber", "produce-resource:shelter")
            if with_resource_authority
            else ()
        ),
        formal=True,
        basis="Council charter delegates store commitments",
        provenance=provenance(now),
    )
    informal_grant = OrganizationAuthorityGrant(
        grant_id=uuid4(),
        organization_id=organization_id,
        character_id=advisor_id,
        role_code="respected-founder",
        permission_codes=("consume-resource:timber",),
        formal=False,
        basis="Personal influence only; not formal resource authority",
        provenance=provenance(now),
    )
    motive = OrganizationMotive(
        motive_id=uuid4(),
        organization_id=organization_id,
        description="Preserve the cooperative through shared infrastructure",
        internal_supporters=("craft faction",),
        internal_opposition=("trade faction questions the cost",),
        provenance=provenance(now),
    )
    goal = OrganizationGoal(
        goal_id=uuid4(),
        organization_id=organization_id,
        motive_id=motive.motive_id,
        desired_outcome="Establish a permanent repair shelter",
        status=GoalStatus.ACTIVE,
        provenance=provenance(now),
    )
    plan = OrganizationPlan(
        plan_id=uuid4(),
        organization_id=organization_id,
        goal_id=goal.goal_id,
        name="Build the shared shelter",
        status=PlanStatus.ACTIVE,
        provenance=provenance(now),
    )
    step = OrganizationPlanStep(
        step_id=uuid4(),
        plan_id=plan.plan_id,
        sequence=0,
        action_intent="Assemble the cooperative repair shelter",
        required_resources=("timber",),
        required_knowledge_fact_keys=("council-approved-site",),
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
        responsible_character_id=steward_id,
        provenance=provenance(now),
    )
    context = OrganizationDecisionContext(
        request_id=uuid4(),
        organization_id=organization_id,
        as_of=now,
        identity=identity,
        governance=governance,
        memberships=(steward, advisor),
        authority_grants=(grant, informal_grant),
        facts=(
            DecisionCircumstance(
                fact_key="council-approved-site",
                statement="The council approved the north yard site.",
                observed_at=now,
            ),
        ),
        resources=(ResourceAvailability(name="timber", available=True),),
        motives=(motive,),
        goals=(goal,),
        plans=(OrganizationPlanContext(plan=plan, steps=(step,)),),
    )
    return context, identity, governance, (steward, advisor), (
        grant,
        informal_grant,
    ), motive, goal, plan, step


def persist_context(
    tmp_path: Path,
    now: datetime,
    *,
    authority: bool = True,
) -> tuple[Database, UUID, UUID, OrganizationDecisionContext, OrganizationPlanStep]:
    database = Database.from_path(tmp_path / "organizations.db")
    database.create_schema()
    (
        context,
        identity,
        governance,
        memberships,
        grants,
        motive,
        goal,
        plan,
        step,
    ) = organization_context(now, with_resource_authority=authority)
    world_id = uuid4()
    timeline_id = uuid4()
    with SqlAlchemySimulationUnitOfWork(database.session_factory) as uow:
        uow.repository.create_clock(
            WorldClockState(world_id, timeline_id, now, version=0)
        )
        uow.repository.create_organization_identity(identity)
        uow.repository.create_organization_governance(governance)
        for membership in memberships:
            uow.repository.create_organization_membership(membership)
        for grant_item in grants:
            uow.repository.create_organization_authority_grant(grant_item)
        uow.repository.create_organization_motive(motive)
        uow.repository.create_organization_goal(goal)
        uow.repository.create_organization_plan(plan)
        uow.repository.create_organization_plan_step(step)
        for code, quantity in (("timber", Decimal("5")), ("shelter", Decimal("0"))):
            uow.repository.create_resource_balance(
                ResourceBalance(
                    balance_id=uuid4(),
                    owner_kind=ResourceOwnerKind.ORGANIZATION,
                    owner_id=context.organization_id,
                    resource_code=code,
                    resource_kind=ResourceKind.MATERIAL,
                    quantity=quantity,
                    reserved=Decimal("0"),
                    version=0,
                )
            )
    return database, world_id, timeline_id, context, step


def test_membership_preserves_formal_authority_and_informal_influence(
    tmp_path: Path,
) -> None:
    now = datetime(2026, 1, 1, tzinfo=UTC)
    database, _, _, context, _ = persist_context(tmp_path, now)

    with SqlAlchemySimulationUnitOfWork(database.session_factory) as uow:
        stored = uow.repository.list_organization_memberships(
            context.organization_id
        )
    advisor = next(item for item in stored if not item.formal_roles)
    steward = next(item for item in stored if item.formal_roles)

    assert steward.formal_roles == ("quartermaster",)
    assert advisor.informal_roles == ("respected-founder",)
    assert advisor.effective_influence == (
        "shapes council debate without signing commitments",
    )
    assert advisor.character_id != steward.character_id
    database.dispose()


def test_unauthorized_member_cannot_consume_organization_resources(
    tmp_path: Path,
) -> None:
    now = datetime(2026, 1, 1, tzinfo=UTC)
    database, world_id, timeline_id, context, _ = persist_context(
        tmp_path, now, authority=False
    )
    service = OrganizationDecisionService(
        lambda: SqlAlchemySimulationUnitOfWork(database.session_factory)
    )
    proposal = service.propose(context).proposal

    with pytest.raises(OrganizationAuthorityError, match="consume-resource:timber"):
        service.schedule_validated_step(
            proposal.proposal_id,
            world_id=world_id,
            timeline_id=timeline_id,
            scheduled_at=now + timedelta(minutes=10),
        )
    with database.session_factory() as session:
        assert session.scalar(select(func.count(ScheduledEventModel.event_id))) == 0
    database.dispose()


def test_organization_port_receives_only_supplied_filtered_context(
    tmp_path: Path,
) -> None:
    now = datetime(2026, 1, 1, tzinfo=UTC)
    database, _, _, context, step = persist_context(tmp_path, now)

    class CapturingPort:
        def __init__(self) -> None:
            self.context: OrganizationDecisionContext | None = None

        def propose(
            self, context: OrganizationDecisionContext
        ) -> OrganizationDecisionProposal:
            self.context = context
            return OrganizationDecisionProposal(
                proposal_id=uuid4(),
                request_id=context.request_id,
                organization_id=context.organization_id,
                responsible_character_id=step.responsible_character_id,
                reaction="Defer.",
                decision_type=OrganizationDecisionType.DEFER,
                target_plan_step_id=None,
                rationale="Only supplied facts are visible.",
                confidence=1,
                context_hash="",
                provenance=provenance(now),
            )

    port = CapturingPort()
    result = OrganizationDecisionService(
        lambda: SqlAlchemySimulationUnitOfWork(database.session_factory),
        decision_port=port,
    ).propose(context)

    assert port.context is not None
    assert port.context == context
    assert [fact.fact_key for fact in port.context.facts] == [
        "council-approved-site"
    ]
    assert result.proposal.organization_id == context.organization_id
    database.dispose()


def test_organization_schedule_executes_off_screen_and_replays_once(
    tmp_path: Path,
) -> None:
    now = datetime(2026, 1, 1, tzinfo=UTC)
    database, world_id, timeline_id, context, step = persist_context(tmp_path, now)
    decisions = OrganizationDecisionService(
        lambda: SqlAlchemySimulationUnitOfWork(database.session_factory)
    )
    proposal = decisions.propose(context).proposal
    scheduled = decisions.schedule_validated_step(
        proposal.proposal_id,
        world_id=world_id,
        timeline_id=timeline_id,
        scheduled_at=now + timedelta(minutes=10),
    )
    replay_schedule = decisions.schedule_validated_step(
        proposal.proposal_id,
        world_id=world_id,
        timeline_id=timeline_id,
        scheduled_at=now + timedelta(hours=2),
    )
    command = AdvanceTimeCommand(
        simulation_run_id=uuid4(),
        world_id=world_id,
        timeline_id=timeline_id,
        duration=timedelta(minutes=10),
    )
    temporal = TemporalAdvanceService(
        lambda: SqlAlchemySimulationUnitOfWork(database.session_factory)
    )

    first = temporal.advance_time(command)
    replay = temporal.advance_time(command)

    assert replay_schedule.idempotent_replay
    assert scheduled.scheduled_event_id == replay_schedule.scheduled_event_id
    assert first.processed_event_ids == (scheduled.scheduled_event_id,)
    assert replay.idempotent_replay
    with SqlAlchemySimulationUnitOfWork(database.session_factory) as uow:
        stored_step = uow.repository.get_organization_plan_step(step.step_id)
        timber = uow.repository.get_resource_balance(
            ResourceOwnerKind.ORGANIZATION, context.organization_id, "timber"
        )
        shelter = uow.repository.get_resource_balance(
            ResourceOwnerKind.ORGANIZATION, context.organization_id, "shelter"
        )
        assert stored_step is not None
        assert stored_step.status == PlanStepStatus.COMPLETED
        assert timber is not None and timber.quantity == Decimal("3")
        assert shelter is not None and shelter.quantity == Decimal("1")
        transactions = uow.repository.list_resource_transactions(
            scheduled.scheduled_event_id
        )
        assert len(transactions) == 2
        event = uow.session.scalars(select(EventLedgerModel)).one()
        assert event.payload["resource_changes"] == {
            "shelter": "1",
            "timber": "-2",
        }
    with database.session_factory() as session:
        assert session.scalar(select(func.count(EventLedgerModel.event_id))) == 1
        assert (
            session.scalar(select(func.count(ResourceTransactionModel.transaction_id)))
            == 2
        )
    database.dispose()


def test_organization_failure_rolls_back_step_ledger_and_shared_balances(
    tmp_path: Path,
) -> None:
    now = datetime(2026, 1, 1, tzinfo=UTC)
    database, world_id, timeline_id, context, step = persist_context(tmp_path, now)
    decisions = OrganizationDecisionService(
        lambda: SqlAlchemySimulationUnitOfWork(database.session_factory)
    )
    proposal = decisions.propose(context).proposal
    scheduled = decisions.schedule_validated_step(
        proposal.proposal_id,
        world_id=world_id,
        timeline_id=timeline_id,
        scheduled_at=now + timedelta(minutes=10),
    )

    class BrokenResolver:
        def resolve(self, event, plan_step):
            del event, plan_step
            raise RuntimeError("organization resolution interrupted")

    temporal = TemporalAdvanceService(
        lambda: SqlAlchemySimulationUnitOfWork(database.session_factory),
        scheduled_resolver=BrokenResolver(),
    )
    with pytest.raises(RuntimeError, match="organization resolution interrupted"):
        temporal.advance_time(
            AdvanceTimeCommand(
                simulation_run_id=uuid4(),
                world_id=world_id,
                timeline_id=timeline_id,
                duration=timedelta(minutes=10),
            )
        )

    with SqlAlchemySimulationUnitOfWork(database.session_factory) as uow:
        stored_step = uow.repository.get_organization_plan_step(step.step_id)
        assert stored_step is not None
        assert stored_step.status == PlanStepStatus.SCHEDULED
        timber = uow.repository.get_resource_balance(
            ResourceOwnerKind.ORGANIZATION, context.organization_id, "timber"
        )
        assert timber is not None
        assert timber.quantity == Decimal("5")
        assert timber.reserved == Decimal("2")
        clock = uow.repository.get_clock(world_id, timeline_id)
        assert clock is not None and clock.current_time == now
        assert (
            uow.repository.list_resource_transactions(scheduled.scheduled_event_id)
            == ()
        )
        assert tuple(uow.session.scalars(select(EventLedgerModel)).all()) == ()
    database.dispose()
