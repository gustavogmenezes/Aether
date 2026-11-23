from collections.abc import Iterator
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import pytest
from sqlalchemy import func, select

from aether.contracts import (
    CharacterIdentity,
    Goal,
    PersonalityProfile,
    Plan,
    PlanStatus,
    PlanStep,
    PsychologicalState,
    RecordProvenance,
    Relationship,
    RelationshipDimension,
)
from aether.infrastructure import Database, SqlAlchemySimulationUnitOfWork
from aether.infrastructure.models import GoalModel, PlanModel, PlanStepModel


@pytest.fixture
def database(tmp_path: Path) -> Iterator[Database]:
    database = Database.from_path(tmp_path / "characters.db")
    database.create_schema()
    yield database
    database.dispose()


def provenance(now: datetime) -> RecordProvenance:
    return RecordProvenance(
        source_type="test",
        source_id="repository-test",
        created_at=now,
        updated_at=now,
        version=1,
    )


def test_directional_relationships_are_independent(database: Database) -> None:
    now = datetime(2026, 1, 1, tzinfo=UTC)
    first = uuid4()
    second = uuid4()
    records = (
        Relationship(
            relationship_id=uuid4(),
            source_character_id=first,
            target_character_id=second,
            dimensions=(RelationshipDimension(name="trust", disposition="high"),),
            provenance=provenance(now),
        ),
        Relationship(
            relationship_id=uuid4(),
            source_character_id=second,
            target_character_id=first,
            dimensions=(RelationshipDimension(name="trust", disposition="low"),),
            hidden=True,
            provenance=provenance(now),
        ),
    )
    with SqlAlchemySimulationUnitOfWork(database.session_factory) as unit_of_work:
        unit_of_work.repository.create_relationship(records[0])
        unit_of_work.repository.create_relationship(records[1])

    with SqlAlchemySimulationUnitOfWork(database.session_factory) as unit_of_work:
        from_first = unit_of_work.repository.list_relationships(first)
        from_second = unit_of_work.repository.list_relationships(second)

    assert from_first == (records[0],)
    assert from_second == (records[1],)
    assert from_first[0].dimensions[0].disposition == "high"
    assert from_second[0].dimensions[0].disposition == "low"


def test_personality_and_psychological_state_remain_separate(
    database: Database,
) -> None:
    now = datetime(2026, 1, 1, tzinfo=UTC)
    character_id = uuid4()
    identity = CharacterIdentity(
        identity_id=uuid4(),
        character_id=character_id,
        display_name="Mira",
        provenance=provenance(now),
    )
    personality = PersonalityProfile(
        profile_id=uuid4(),
        character_id=character_id,
        traits=("patient",),
        values=("keep promises",),
        provenance=provenance(now),
    )
    state = PsychologicalState(
        state_id=uuid4(),
        character_id=character_id,
        observed_at=now,
        emotions=("angry",),
        behavioral_modes=("guarded",),
        provenance=provenance(now),
    )
    with SqlAlchemySimulationUnitOfWork(database.session_factory) as unit_of_work:
        unit_of_work.repository.create_character_identity(identity)
        unit_of_work.repository.create_personality_profile(personality)
        unit_of_work.repository.create_psychological_state(state)

    with SqlAlchemySimulationUnitOfWork(database.session_factory) as unit_of_work:
        stored_identity = unit_of_work.repository.get_character_identity(character_id)
        stored_personality = unit_of_work.repository.get_personality_profile(
            character_id
        )
        stored_state = unit_of_work.repository.get_psychological_state(
            character_id,
            as_of=now,
        )

    assert stored_identity == identity
    assert stored_personality == personality
    assert stored_state == state
    assert personality.profile_id != identity.identity_id != state.state_id


def test_goal_plan_and_steps_round_trip(database: Database) -> None:
    now = datetime(2026, 1, 1, tzinfo=UTC)
    character_id = uuid4()
    goal = Goal(
        goal_id=uuid4(),
        character_id=character_id,
        desired_outcome="Restore the bridge.",
        provenance=provenance(now),
    )
    plan = Plan(
        plan_id=uuid4(),
        character_id=character_id,
        goal_id=goal.goal_id,
        name="Gather builders",
        status=PlanStatus.ACTIVE,
        provenance=provenance(now),
    )
    step = PlanStep(
        step_id=uuid4(),
        plan_id=plan.plan_id,
        sequence=0,
        action_intent="Visit the guild",
        required_resources=("guild-seal",),
        provenance=provenance(now),
    )
    with SqlAlchemySimulationUnitOfWork(database.session_factory) as unit_of_work:
        unit_of_work.repository.create_goal(goal)
        unit_of_work.repository.create_plan(plan)
        unit_of_work.repository.create_plan_step(step)

    with SqlAlchemySimulationUnitOfWork(database.session_factory) as unit_of_work:
        stored_goal = unit_of_work.repository.get_goal(goal.goal_id)
        stored_plan = unit_of_work.repository.get_plan(plan.plan_id)
        stored_step = unit_of_work.repository.get_plan_step(step.step_id)
    with database.session_factory() as session:
        assert session.scalar(select(func.count(GoalModel.goal_id))) == 1
        assert session.scalar(select(func.count(PlanModel.plan_id))) == 1
        assert session.scalar(select(func.count(PlanStepModel.step_id))) == 1

    assert stored_goal == goal
    assert stored_plan == plan
    assert stored_step == step
