from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import UUID, uuid4

import pytest
from sqlalchemy import func, select

from aether.application import NpcDecisionService
from aether.contracts import (
    CapabilityAvailability,
    CharacterIdentity,
    Goal,
    GoalStatus,
    KnowledgeContextEntry,
    EpistemicStatus,
    NpcDecisionContext,
    NpcDecisionProposal,
    NpcDecisionProposalStatus,
    NpcDecisionType,
    NpcPlanContext,
    PersonalityProfile,
    Plan,
    PlanStatus,
    PlanStep,
    RecordProvenance,
    ResourceAvailability,
)
from aether.domain import (
    PlanStepSchedulingRejectedError,
    WorldClockState,
)
from aether.infrastructure import Database, SqlAlchemySimulationUnitOfWork
from aether.infrastructure.models import (
    NpcDecisionProposalModel,
    ScheduledEventModel,
)


def provenance(now: datetime) -> RecordProvenance:
    return RecordProvenance(
        source_type="test",
        source_id="npc-decision-test",
        created_at=now,
        updated_at=now,
        version=1,
    )


def decision_context(
    now: datetime,
    *,
    resource_available: bool = True,
) -> tuple[NpcDecisionContext, PlanStep, Goal, Plan]:
    character_id = uuid4()
    goal_id = uuid4()
    plan_id = uuid4()
    goal = Goal(
        goal_id=goal_id,
        character_id=character_id,
        desired_outcome="Warn the harbor wardens.",
        status=GoalStatus.ACTIVE,
        provenance=provenance(now),
    )
    plan = Plan(
        plan_id=plan_id,
        character_id=character_id,
        goal_id=goal_id,
        name="Reach the watch post",
        status=PlanStatus.ACTIVE,
        provenance=provenance(now),
    )
    step = PlanStep(
        step_id=uuid4(),
        plan_id=plan_id,
        sequence=0,
        action_intent="Travel to the watch post",
        required_capabilities=("navigation",),
        required_resources=("street-map",),
        required_knowledge_fact_keys=("watch-post-location",),
        provenance=provenance(now),
    )
    identity = CharacterIdentity(
        identity_id=uuid4(),
        character_id=character_id,
        display_name="Sera",
        provenance=provenance(now),
    )
    return (
        NpcDecisionContext(
            request_id=uuid4(),
            character_id=character_id,
            as_of=now,
            identity=identity,
            personality=PersonalityProfile(
                profile_id=uuid4(),
                character_id=character_id,
                traits=("dutiful",),
                provenance=provenance(now),
            ),
            knowledge=(
                KnowledgeContextEntry(
                    fact_key="watch-post-location",
                    statement="The watch post is above the north quay.",
                    confidence=1,
                    epistemic_status=EpistemicStatus.KNOWN,
                    acquired_at=now,
                ),
                KnowledgeContextEntry(
                    fact_key="visible-storm",
                    statement="A storm is approaching.",
                    confidence=0.9,
                    epistemic_status=EpistemicStatus.BELIEF,
                    acquired_at=now,
                ),
            ),
            capabilities=(CapabilityAvailability(name="navigation", available=True),),
            resources=(
                ResourceAvailability(
                    name="street-map",
                    available=resource_available,
                ),
            ),
            goals=(goal,),
            plans=(NpcPlanContext(plan=plan, steps=(step,)),),
        ),
        step,
        goal,
        plan,
    )


def database_for(tmp_path: Path, now: datetime) -> tuple[
    Database, UUID, UUID
]:
    database = Database.from_path(tmp_path / "npc-decision.db")
    database.create_schema()
    world_id = uuid4()
    timeline_id = uuid4()
    with SqlAlchemySimulationUnitOfWork(database.session_factory) as unit_of_work:
        unit_of_work.repository.create_clock(
            WorldClockState(world_id, timeline_id, now, version=0)
        )
    return database, world_id, timeline_id


def test_context_isolation_and_proposal_replay(tmp_path: Path) -> None:
    now = datetime(2026, 1, 1, tzinfo=UTC)
    context, _, _, _ = decision_context(now)
    database, _, _ = database_for(tmp_path, now)

    class CapturingPort:
        def __init__(self) -> None:
            self.context: NpcDecisionContext | None = None
            self.calls = 0

        def propose(self, supplied: NpcDecisionContext) -> NpcDecisionProposal:
            self.context = supplied
            self.calls += 1
            return NpcDecisionProposal(
                proposal_id=uuid4(),
                request_id=supplied.request_id,
                character_id=supplied.character_id,
                reaction="Wait for a clearer view.",
                decision_type=NpcDecisionType.DEFER,
                target_plan_step_id=None,
                rationale="The supplied circumstances require observation.",
                confidence=0.5,
                context_hash="",
                provenance=provenance(now),
            )

    port = CapturingPort()
    service = NpcDecisionService(
        lambda: SqlAlchemySimulationUnitOfWork(database.session_factory),
        decision_port=port,
    )

    first = service.propose(context)
    replay = service.propose(context)

    assert port.context == context
    assert {item.fact_key for item in port.context.knowledge} == {
        "watch-post-location",
        "visible-storm",
    }
    assert port.calls == 1
    assert not first.idempotent_replay
    assert replay.idempotent_replay
    assert replay.proposal == first.proposal
    assert replay.proposal.status == NpcDecisionProposalStatus.VALIDATED
    with database.session_factory() as session:
        assert session.scalar(
            select(func.count(NpcDecisionProposalModel.proposal_id))
        ) == 1
    database.dispose()


def test_successful_proposal_schedules_once_without_advancing_clock(
    tmp_path: Path,
) -> None:
    now = datetime(2026, 1, 1, tzinfo=UTC)
    context, step, goal, plan = decision_context(now)
    database, world_id, timeline_id = database_for(tmp_path, now)
    with SqlAlchemySimulationUnitOfWork(database.session_factory) as unit_of_work:
        unit_of_work.repository.create_goal(goal)
        unit_of_work.repository.create_plan(plan)
        unit_of_work.repository.create_plan_step(step)
    service = NpcDecisionService(
        lambda: SqlAlchemySimulationUnitOfWork(database.session_factory)
    )

    proposal = service.propose(context).proposal
    scheduled = service.schedule_validated_step(
        proposal.proposal_id,
        world_id=world_id,
        timeline_id=timeline_id,
        scheduled_at=now + timedelta(minutes=10),
    )
    replay = service.schedule_validated_step(
        proposal.proposal_id,
        world_id=world_id,
        timeline_id=timeline_id,
        scheduled_at=now + timedelta(hours=5),
    )

    assert proposal.decision_type == NpcDecisionType.EXECUTE_PLAN_STEP
    assert scheduled.scheduled_event_id == replay.scheduled_event_id
    assert replay.idempotent_replay
    with database.session_factory() as session:
        event = session.scalar(select(ScheduledEventModel))
        assert event is not None
        assert event.scheduled_at == now + timedelta(minutes=10)
        assert session.scalar(select(func.count(ScheduledEventModel.event_id))) == 1
    with SqlAlchemySimulationUnitOfWork(database.session_factory) as unit_of_work:
        clock = unit_of_work.repository.get_clock(world_id, timeline_id)
        stored_step = unit_of_work.repository.get_plan_step(step.step_id)
    assert clock is not None and clock.current_time == now
    assert stored_step is not None and stored_step.status.value == "scheduled"
    database.dispose()


def test_missing_resources_reject_scheduling_without_partial_write(
    tmp_path: Path,
) -> None:
    now = datetime(2026, 1, 1, tzinfo=UTC)
    context, step, goal, plan = decision_context(now, resource_available=False)
    database, world_id, timeline_id = database_for(tmp_path, now)
    with SqlAlchemySimulationUnitOfWork(database.session_factory) as unit_of_work:
        unit_of_work.repository.create_goal(goal)
        unit_of_work.repository.create_plan(plan)
        unit_of_work.repository.create_plan_step(step)

    class InsistingPort:
        def propose(self, supplied: NpcDecisionContext) -> NpcDecisionProposal:
            return NpcDecisionProposal(
                proposal_id=uuid4(),
                request_id=supplied.request_id,
                character_id=supplied.character_id,
                reaction="Proceed anyway.",
                decision_type=NpcDecisionType.EXECUTE_PLAN_STEP,
                target_plan_step_id=step.step_id,
                rationale="Test validator.",
                required_resources=step.required_resources,
                confidence=1,
                context_hash="",
                provenance=provenance(now),
            )

    service = NpcDecisionService(
        lambda: SqlAlchemySimulationUnitOfWork(database.session_factory),
        decision_port=InsistingPort(),
    )
    proposal = service.propose(context).proposal

    with pytest.raises(PlanStepSchedulingRejectedError, match="resource:street-map"):
        service.schedule_validated_step(
            proposal.proposal_id,
            world_id=world_id,
            timeline_id=timeline_id,
            scheduled_at=now + timedelta(minutes=10),
        )

    with database.session_factory() as session:
        assert session.scalar(select(func.count(ScheduledEventModel.event_id))) == 0
    with SqlAlchemySimulationUnitOfWork(database.session_factory) as unit_of_work:
        stored_step = unit_of_work.repository.get_plan_step(step.step_id)
    assert stored_step == step
    database.dispose()
