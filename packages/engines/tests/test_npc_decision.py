from datetime import UTC, datetime
from uuid import UUID, uuid4

from aether.contracts import (
    CapabilityAvailability,
    CharacterIdentity,
    Goal,
    GoalStatus,
    KnowledgeContextEntry,
    EpistemicStatus,
    NpcDecisionContext,
    NpcDecisionType,
    NpcPlanContext,
    PersonalityProfile,
    Plan,
    PlanStatus,
    PlanStep,
    RecordProvenance,
    ResourceAvailability,
)
from aether.engines import DeterministicNpcDecisionEngine


def provenance(now: datetime) -> RecordProvenance:
    return RecordProvenance(
        source_type="test",
        source_id="fixture",
        created_at=now,
        updated_at=now,
        version=1,
    )


def context(
    *,
    now: datetime,
    resource_available: bool = True,
) -> tuple[NpcDecisionContext, UUID]:
    character_id = uuid4()
    goal_id = uuid4()
    plan_id = uuid4()
    step_id = uuid4()
    identity = CharacterIdentity(
        identity_id=uuid4(),
        character_id=character_id,
        display_name="Ari",
        provenance=provenance(now),
    )
    personality = PersonalityProfile(
        profile_id=uuid4(),
        character_id=character_id,
        traits=("cautious",),
        provenance=provenance(now),
    )
    goal = Goal(
        goal_id=goal_id,
        character_id=character_id,
        desired_outcome="Secure passage through the gate.",
        status=GoalStatus.ACTIVE,
        provenance=provenance(now),
    )
    plan = Plan(
        plan_id=plan_id,
        character_id=character_id,
        goal_id=goal_id,
        name="Find a trustworthy guide",
        status=PlanStatus.ACTIVE,
        provenance=provenance(now),
    )
    step = PlanStep(
        step_id=step_id,
        plan_id=plan_id,
        sequence=0,
        action_intent="Contact the guide",
        required_capabilities=("persuasion",),
        required_resources=("travel-pass",),
        required_knowledge_fact_keys=("guide-location",),
        provenance=provenance(now),
    )
    return (
        NpcDecisionContext(
            request_id=uuid4(),
            character_id=character_id,
            as_of=now,
            identity=identity,
            personality=personality,
            knowledge=(
                KnowledgeContextEntry(
                    fact_key="guide-location",
                    statement="The guide waits near the east gate.",
                    confidence=0.8,
                    epistemic_status=EpistemicStatus.BELIEF,
                    acquired_at=now,
                ),
            ),
            capabilities=(
                CapabilityAvailability(name="persuasion", available=True),
            ),
            resources=(
                ResourceAvailability(
                    name="travel-pass",
                    available=resource_available,
                ),
            ),
            goals=(goal,),
            plans=(NpcPlanContext(plan=plan, steps=(step,)),),
        ),
        step_id,
    )


def test_deterministic_engine_selects_an_available_plan_step() -> None:
    supplied, step_id = context(now=datetime(2026, 1, 1, tzinfo=UTC))

    proposal = DeterministicNpcDecisionEngine().propose(supplied)

    assert proposal == DeterministicNpcDecisionEngine().propose(supplied)
    assert proposal.decision_type == NpcDecisionType.EXECUTE_PLAN_STEP
    assert proposal.target_plan_step_id == step_id
    assert proposal.required_resources == ("travel-pass",)
    assert proposal.confidence == 1.0


def test_deterministic_engine_exposes_missing_resource_requirement() -> None:
    supplied, step_id = context(
        now=datetime(2026, 1, 1, tzinfo=UTC),
        resource_available=False,
    )

    proposal = DeterministicNpcDecisionEngine().propose(supplied)

    assert proposal.decision_type == NpcDecisionType.DEFER
    assert proposal.target_plan_step_id == step_id
    assert proposal.validation_requirements == ("resource:travel-pass",)
