from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from aether.contracts import (
    AgentProposalRecord,
    CharacterKnowledgeRecord,
    EventEnvelope,
    InterruptionClass,
    LlmInvocationRecord,
    NarrativeStateRecord,
    PlayerKnowledgeRecord,
    PresentationRecord,
    PresentationStatus,
    InformationTransmission,
    KnowledgeContextEntry,
    EpistemicStatus,
    CommunicationMedium,
    InformationNature,
    TransmissionStatus,
    ScheduledEvent,
    SimulationRunRecord,
    SimulationRunStatus,
    CharacterIdentity,
    PersonalityProfile,
    PsychologicalState,
    RecordProvenance,
    Relationship,
    RelationshipDimension,
    Motive,
    Goal,
    Plan,
    PlanStep,
    NpcDecisionContext,
    NpcDecisionProposal,
    CharacterRecordStatus,
    GoalStatus,
    PlanStatus,
    PlanStepStatus,
    NpcDecisionProposalStatus,
    NpcDecisionType,
    ResourceBalance,
    ResourceKind,
    ResourceOwnerKind,
    ResourceReservation,
    ResourceTransaction,
    ResourceEffect,
)
from aether.domain import (
    DuplicateSimulationRunError,
    ResourceInvariantError,
    StaleWorldStateError,
)
from aether.domain.simulation import ScheduledEventStatus, WorldClockState

from .models import (
    AgentProposalModel,
    CharacterKnowledgeModel,
    EventLedgerModel,
    LlmInvocationModel,
    NarrativePresentationModel,
    NarrativeStateModel,
    PlayerKnowledgeModel,
    ScheduledEventModel,
    SimulationRunModel,
    WorldClockModel,
    InformationTransmissionModel,
    CharacterIdentityModel,
    PersonalityProfileModel,
    PsychologicalStateModel,
    RelationshipModel,
    MotiveModel,
    GoalModel,
    PlanModel,
    PlanStepModel,
    NpcDecisionProposalModel,
    ResourceBalanceModel,
    ResourceReservationModel,
    ResourceTransactionModel,
)


class SqlAlchemySimulationRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def create_clock(self, clock: WorldClockState) -> None:
        self._session.add(
            WorldClockModel(
                world_id=str(clock.world_id),
                timeline_id=str(clock.timeline_id),
                current_time=clock.current_time,
                version=clock.version,
            )
        )

    def schedule_event(self, event: ScheduledEvent) -> None:
        self._session.add(
            ScheduledEventModel(
                event_id=str(event.event_id),
                world_id=str(event.world_id),
                timeline_id=str(event.timeline_id),
                scheduled_at=event.scheduled_at,
                event_type=event.event_type,
                source_type=event.source_type,
                source_id=event.source_id,
                caused_by=[str(value) for value in event.caused_by],
                priority=event.priority,
                payload_version=event.payload_version,
                payload=event.payload,
                interruption_class=event.interruption_class.value,
                status=ScheduledEventStatus.PENDING.value,
            )
        )

    def get_clock(self, world_id: UUID, timeline_id: UUID) -> WorldClockState | None:
        model = self._session.scalar(
            select(WorldClockModel).where(
                WorldClockModel.world_id == str(world_id),
                WorldClockModel.timeline_id == str(timeline_id),
            )
        )
        if model is None:
            return None
        return WorldClockState(
            world_id=UUID(model.world_id),
            timeline_id=UUID(model.timeline_id),
            current_time=model.current_time,
            version=model.version,
        )

    def save_clock(self, clock: WorldClockState, expected_version: int) -> None:
        model = self._session.scalar(
            select(WorldClockModel).where(
                WorldClockModel.world_id == str(clock.world_id),
                WorldClockModel.timeline_id == str(clock.timeline_id),
                WorldClockModel.version == expected_version,
            )
        )
        if model is None:
            raise StaleWorldStateError("World clock changed during simulation")
        model.current_time = clock.current_time
        model.version = clock.version

    def get_run(self, simulation_run_id: UUID) -> SimulationRunRecord | None:
        model = self._session.get(SimulationRunModel, str(simulation_run_id))
        return self._run_contract(model) if model is not None else None

    def create_run(self, run: SimulationRunRecord) -> None:
        self._session.add(
            SimulationRunModel(
                simulation_run_id=str(run.simulation_run_id),
                operation=run.operation,
                world_id=str(run.world_id),
                timeline_id=str(run.timeline_id),
                status=run.status.value,
                initial_time=run.initial_time,
                target_time=run.target_time,
                final_time=run.final_time,
                processed_event_ids=[
                    str(event_id) for event_id in run.processed_event_ids
                ],
                error=run.error,
                created_at=run.created_at,
                updated_at=run.updated_at,
            )
        )
        try:
            self._session.flush()
        except IntegrityError as error:
            raise DuplicateSimulationRunError(
                f"Simulation run {run.simulation_run_id} already exists"
            ) from error

    def update_run(
        self,
        simulation_run_id: UUID,
        *,
        status: SimulationRunStatus,
        final_time: datetime | None = None,
        processed_event_ids: tuple[UUID, ...] | None = None,
        error: str | None = None,
    ) -> SimulationRunRecord:
        model = self._session.get(SimulationRunModel, str(simulation_run_id))
        if model is None:
            raise KeyError(f"Unknown simulation run {simulation_run_id}")
        now = datetime.now(UTC)
        model.status = status.value
        model.updated_at = now
        if final_time is not None:
            model.final_time = final_time
        if processed_event_ids is not None:
            model.processed_event_ids = [
                str(event_id) for event_id in processed_event_ids
            ]
        if error is not None:
            model.error = error
        self._session.flush()
        return self._run_contract(model)

    def get_scheduled_event(self, event_id: UUID) -> ScheduledEvent | None:
        model = self._session.scalar(
            select(ScheduledEventModel).where(
                ScheduledEventModel.event_id == str(event_id)
            )
        )
        return self._scheduled_contract(model) if model is not None else None

    def get_scheduled_event_status(
        self,
        event_id: UUID,
    ) -> ScheduledEventStatus | None:
        model = self._session.get(ScheduledEventModel, str(event_id))
        if model is None:
            return None
        return ScheduledEventStatus(model.status)

    def list_due_scheduled_events(
        self,
        world_id: UUID,
        timeline_id: UUID,
        after: datetime,
        through: datetime,
    ) -> tuple[ScheduledEvent, ...]:
        models = self._session.scalars(
            select(ScheduledEventModel)
            .where(
                ScheduledEventModel.world_id == str(world_id),
                ScheduledEventModel.timeline_id == str(timeline_id),
                ScheduledEventModel.status == ScheduledEventStatus.PENDING.value,
                ScheduledEventModel.scheduled_at > after,
                ScheduledEventModel.scheduled_at <= through,
            )
            .order_by(ScheduledEventModel.scheduled_at, ScheduledEventModel.event_id)
        ).all()
        return tuple(self._scheduled_contract(model) for model in models)

    def mark_scheduled_event_completed(self, event_id: UUID) -> None:
        self._set_scheduled_status(event_id, ScheduledEventStatus.COMPLETED)

    def mark_scheduled_event_failed(self, event_id: UUID, error: str) -> None:
        model = self._scheduled_model(event_id)
        model.status = ScheduledEventStatus.FAILED.value
        model.failure_reason = error

    def get_latest_event_sequence(self, world_id: UUID, timeline_id: UUID) -> int:
        value = self._session.scalar(
            select(func.max(EventLedgerModel.sequence)).where(
                EventLedgerModel.world_id == str(world_id),
                EventLedgerModel.timeline_id == str(timeline_id),
            )
        )
        return int(value or 0)

    def append_event(self, event: EventEnvelope) -> None:
        self._session.add(
            EventLedgerModel(
                event_id=str(event.event_id),
                world_id=str(event.world_id),
                timeline_id=str(event.timeline_id),
                occurred_at=event.occurred_at,
                recorded_at=event.recorded_at,
                sequence=event.sequence,
                event_type=event.event_type,
                source_type=event.source_type,
                source_id=event.source_id,
                caused_by=[str(value) for value in event.caused_by],
                priority=event.priority,
                payload_version=event.payload_version,
                payload=event.payload,
                interruption_class=event.interruption_class.value,
            )
        )

    def create_invocation(self, invocation: LlmInvocationRecord) -> None:
        self._session.add(
            LlmInvocationModel(
                invocation_id=str(invocation.invocation_id),
                simulation_run_id=str(invocation.simulation_run_id),
                requesting_agent=invocation.requesting_agent,
                requested_capability=invocation.requested_capability,
                model=invocation.model,
                model_version=invocation.model_version,
                prompt_version=invocation.prompt_version,
                context_hash=invocation.context_hash,
                inference_parameters=invocation.inference_parameters,
                response_reference=invocation.response_reference,
                status=invocation.status,
                input_tokens=invocation.input_tokens,
                output_tokens=invocation.output_tokens,
                created_at=invocation.created_at,
                completed_at=invocation.completed_at,
            )
        )

    def get_invocation(self, invocation_id: UUID) -> LlmInvocationRecord | None:
        model = self._session.get(LlmInvocationModel, str(invocation_id))
        if model is None:
            return None
        return LlmInvocationRecord(
            invocation_id=UUID(model.invocation_id),
            simulation_run_id=UUID(model.simulation_run_id),
            requesting_agent=model.requesting_agent,
            requested_capability=model.requested_capability,
            model=model.model,
            model_version=model.model_version,
            prompt_version=model.prompt_version,
            context_hash=model.context_hash,
            inference_parameters=model.inference_parameters,
            response_reference=model.response_reference,
            status=model.status,
            input_tokens=model.input_tokens,
            output_tokens=model.output_tokens,
            created_at=model.created_at,
            completed_at=model.completed_at,
        )

    def create_proposal(self, proposal: AgentProposalRecord) -> None:
        self._session.add(
            AgentProposalModel(
                proposal_id=str(proposal.proposal_id),
                simulation_run_id=str(proposal.simulation_run_id),
                invocation_id=str(proposal.invocation_id),
                proposal_type=proposal.proposal_type,
                payload=proposal.payload,
                validation_status=proposal.validation_status,
                rejection_reason=proposal.rejection_reason,
                application_result=proposal.application_result,
                created_at=proposal.created_at,
            )
        )

    def get_proposal(self, proposal_id: UUID) -> AgentProposalRecord | None:
        model = self._session.get(AgentProposalModel, str(proposal_id))
        if model is None:
            return None
        return AgentProposalRecord(
            proposal_id=UUID(model.proposal_id),
            simulation_run_id=UUID(model.simulation_run_id),
            invocation_id=UUID(model.invocation_id),
            proposal_type=model.proposal_type,
            payload=model.payload,
            validation_status=model.validation_status,
            rejection_reason=model.rejection_reason,
            application_result=model.application_result,
            created_at=model.created_at,
        )

    def get_proposals_by_run(
        self,
        simulation_run_id: UUID,
    ) -> tuple[AgentProposalRecord, ...]:
        models = self._session.scalars(
            select(AgentProposalModel).where(
                AgentProposalModel.simulation_run_id == str(simulation_run_id)
            )
        ).all()
        return tuple(
            AgentProposalRecord(
                proposal_id=UUID(model.proposal_id),
                simulation_run_id=UUID(model.simulation_run_id),
                invocation_id=UUID(model.invocation_id),
                proposal_type=model.proposal_type,
                payload=model.payload,
                validation_status=model.validation_status,
                rejection_reason=model.rejection_reason,
                application_result=model.application_result,
                created_at=model.created_at,
            )
            for model in models
        )

    def create_presentation(self, presentation: PresentationRecord) -> None:
        self._session.add(self._presentation_model(presentation))

    def get_presentation(self, presentation_id: UUID) -> PresentationRecord | None:
        model = self._session.get(NarrativePresentationModel, str(presentation_id))
        return self._presentation_contract(model) if model is not None else None

    def get_presentation_by_run(
        self,
        simulation_run_id: UUID,
    ) -> PresentationRecord | None:
        model = self._session.scalar(
            select(NarrativePresentationModel).where(
                NarrativePresentationModel.simulation_run_id
                == str(simulation_run_id)
            )
        )
        return self._presentation_contract(model) if model is not None else None

    def save_presentation(self, presentation: PresentationRecord) -> None:
        model = self._session.get(
            NarrativePresentationModel,
            str(presentation.presentation_id),
        )
        if model is None:
            self.create_presentation(presentation)
            return
        model.status = presentation.status.value
        model.generated_content = presentation.generated_content
        model.delivered_content = presentation.delivered_content
        model.confirmed_fact_ids = list(presentation.confirmed_fact_ids)
        model.delivered_at = presentation.delivered_at

    def create_player_knowledge(self, knowledge: PlayerKnowledgeRecord) -> None:
        self._session.add(
            PlayerKnowledgeModel(
                knowledge_id=str(knowledge.knowledge_id),
                simulation_run_id=str(knowledge.simulation_run_id),
                player_id=knowledge.player_id,
                fact_key=knowledge.fact_key,
                description=knowledge.description,
                source_presentation_id=str(knowledge.source_presentation_id),
                acquired_at=knowledge.acquired_at,
            )
        )

    def create_narrative_state(self, state: NarrativeStateRecord) -> None:
        self._session.add(
            NarrativeStateModel(
                state_id=str(state.state_id),
                simulation_run_id=str(state.simulation_run_id),
                protagonist_character_id=str(state.protagonist_character_id),
                scene_summary=state.scene_summary,
                narrative_time=state.narrative_time,
                created_at=state.created_at,
            )
        )

    def create_character_knowledge(
        self,
        knowledge: CharacterKnowledgeRecord,
    ) -> None:
        self._session.add(
            CharacterKnowledgeModel(
                knowledge_id=str(knowledge.knowledge_id),
                character_id=str(knowledge.character_id),
                fact_key=knowledge.fact_key,
                statement=knowledge.statement,
                source_event_id=(
                    str(knowledge.source_event_id)
                    if knowledge.source_event_id is not None
                    else None
                ),
                acquisition_event_id=(
                    str(knowledge.acquisition_event_id)
                    if knowledge.acquisition_event_id is not None
                    else None
                ),
                acquired_at=knowledge.acquired_at,
                confidence=knowledge.confidence,
                epistemic_status=knowledge.epistemic_status.value,
                temporal_scope=knowledge.temporal_scope,
                visible_in_character_context=knowledge.visible_in_character_context,
            )
        )

    def list_character_knowledge(
        self,
        character_id: UUID,
        *,
        as_of: datetime,
    ) -> tuple[KnowledgeContextEntry, ...]:
        models = self._session.scalars(
            select(CharacterKnowledgeModel)
            .where(
                CharacterKnowledgeModel.character_id == str(character_id),
                CharacterKnowledgeModel.visible_in_character_context.is_(True),
                CharacterKnowledgeModel.acquired_at <= as_of,
            )
            .order_by(
                CharacterKnowledgeModel.acquired_at,
                CharacterKnowledgeModel.knowledge_id,
            )
        ).all()
        return tuple(
            KnowledgeContextEntry(
                fact_key=model.fact_key,
                statement=model.statement,
                confidence=model.confidence,
                epistemic_status=EpistemicStatus(model.epistemic_status),
                acquired_at=model.acquired_at,
            )
            for model in models
        )

    def create_transmission(
        self,
        transmission: InformationTransmission,
    ) -> None:
        self._session.add(
            InformationTransmissionModel(
                transmission_id=str(transmission.transmission_id),
                source_event_id=(
                    str(transmission.source_event_id)
                    if transmission.source_event_id is not None
                    else None
                ),
                sender_character_id=(
                    str(transmission.sender_character_id)
                    if transmission.sender_character_id is not None
                    else None
                ),
                recipient_character_id=str(transmission.recipient_character_id),
                fact_key=transmission.fact_key,
                statement=transmission.statement,
                medium=transmission.medium.value,
                nature=transmission.nature.value,
                sent_at=transmission.sent_at,
                arrival_at=transmission.arrival_at,
                status=transmission.status.value,
                perceived_reliability=transmission.perceived_reliability,
                alterations=list(transmission.alterations),
                sender_intent=transmission.sender_intent,
                reach=transmission.reach,
            )
        )

    def list_due_transmissions(
        self,
        through: datetime,
        *,
        after: datetime,
    ) -> tuple[InformationTransmission, ...]:
        models = self._session.scalars(
            select(InformationTransmissionModel)
            .where(
                InformationTransmissionModel.status == TransmissionStatus.SENT.value,
                InformationTransmissionModel.arrival_at > after,
                InformationTransmissionModel.arrival_at <= through,
            )
            .order_by(
                InformationTransmissionModel.arrival_at,
                InformationTransmissionModel.transmission_id,
            )
        ).all()
        return tuple(self._transmission_contract(model) for model in models)

    def mark_transmission_interpreted(self, transmission_id: UUID) -> None:
        model = self._session.get(
            InformationTransmissionModel,
            str(transmission_id),
        )
        if model is None:
            raise KeyError(f"Unknown information transmission {transmission_id}")
        model.status = TransmissionStatus.INTERPRETED.value

    def create_character_identity(self, identity: CharacterIdentity) -> None:
        self._session.add(
            CharacterIdentityModel(
                identity_id=str(identity.identity_id),
                character_id=str(identity.character_id),
                display_name=identity.display_name,
                nature=identity.nature,
                biography=identity.biography,
                defining_attributes=identity.defining_attributes,
                status=identity.status.value,
                **self._provenance_values(identity.provenance),
            )
        )

    def get_character_identity(
        self,
        character_id: UUID,
    ) -> CharacterIdentity | None:
        model = self._session.scalar(
            select(CharacterIdentityModel).where(
                CharacterIdentityModel.character_id == str(character_id)
            )
        )
        if model is None:
            return None
        return CharacterIdentity(
            identity_id=UUID(model.identity_id),
            character_id=UUID(model.character_id),
            display_name=model.display_name,
            nature=model.nature,
            biography=model.biography,
            defining_attributes=model.defining_attributes,
            status=CharacterRecordStatus(model.status),
            provenance=self._provenance_contract(model),
        )

    def create_personality_profile(self, profile: PersonalityProfile) -> None:
        self._session.add(
            PersonalityProfileModel(
                profile_id=str(profile.profile_id),
                character_id=str(profile.character_id),
                traits=list(profile.traits),
                values=list(profile.values),
                behavioral_tendencies=list(profile.behavioral_tendencies),
                status=profile.status.value,
                **self._provenance_values(profile.provenance),
            )
        )

    def get_personality_profile(
        self,
        character_id: UUID,
    ) -> PersonalityProfile | None:
        model = self._session.scalar(
            select(PersonalityProfileModel)
            .where(
                PersonalityProfileModel.character_id == str(character_id),
                PersonalityProfileModel.status == CharacterRecordStatus.ACTIVE.value,
            )
            .order_by(
                PersonalityProfileModel.version.desc(),
                PersonalityProfileModel.updated_at.desc(),
            )
        )
        if model is None:
            return None
        return PersonalityProfile(
            profile_id=UUID(model.profile_id),
            character_id=UUID(model.character_id),
            traits=tuple(model.traits),
            values=tuple(model.values),
            behavioral_tendencies=tuple(model.behavioral_tendencies),
            status=CharacterRecordStatus(model.status),
            provenance=self._provenance_contract(model),
        )

    def create_psychological_state(self, state: PsychologicalState) -> None:
        self._session.add(
            PsychologicalStateModel(
                state_id=str(state.state_id),
                character_id=str(state.character_id),
                observed_at=state.observed_at,
                emotions=list(state.emotions),
                behavioral_modes=list(state.behavioral_modes),
                description=state.description,
                cause_event_ids=[str(value) for value in state.cause_event_ids],
                status=state.status.value,
                **self._provenance_values(state.provenance),
            )
        )

    def get_psychological_state(
        self,
        character_id: UUID,
        *,
        as_of: datetime,
    ) -> PsychologicalState | None:
        model = self._session.scalar(
            select(PsychologicalStateModel)
            .where(
                PsychologicalStateModel.character_id == str(character_id),
                PsychologicalStateModel.status == CharacterRecordStatus.ACTIVE.value,
                PsychologicalStateModel.observed_at <= as_of,
            )
            .order_by(
                PsychologicalStateModel.observed_at.desc(),
                PsychologicalStateModel.version.desc(),
            )
        )
        if model is None:
            return None
        return PsychologicalState(
            state_id=UUID(model.state_id),
            character_id=UUID(model.character_id),
            observed_at=model.observed_at,
            emotions=tuple(model.emotions),
            behavioral_modes=tuple(model.behavioral_modes),
            description=model.description,
            cause_event_ids=tuple(UUID(value) for value in model.cause_event_ids),
            status=CharacterRecordStatus(model.status),
            provenance=self._provenance_contract(model),
        )

    def create_relationship(self, relationship: Relationship) -> None:
        self._session.add(
            RelationshipModel(
                relationship_id=str(relationship.relationship_id),
                source_character_id=str(relationship.source_character_id),
                target_character_id=str(relationship.target_character_id),
                dimensions=[item.model_dump() for item in relationship.dimensions],
                hidden=relationship.hidden,
                status=relationship.status.value,
                **self._provenance_values(relationship.provenance),
            )
        )

    def list_relationships(
        self,
        character_id: UUID,
    ) -> tuple[Relationship, ...]:
        models = self._session.scalars(
            select(RelationshipModel)
            .where(
                RelationshipModel.source_character_id == str(character_id),
                RelationshipModel.status == CharacterRecordStatus.ACTIVE.value,
            )
            .order_by(
                RelationshipModel.target_character_id,
                RelationshipModel.relationship_id,
            )
        ).all()
        return tuple(self._relationship_contract(model) for model in models)

    def create_motive(self, motive: Motive) -> None:
        self._session.add(
            MotiveModel(
                motive_id=str(motive.motive_id),
                character_id=str(motive.character_id),
                description=motive.description,
                status=motive.status.value,
                **self._provenance_values(motive.provenance),
            )
        )

    def get_motive(self, motive_id: UUID) -> Motive | None:
        model = self._session.get(MotiveModel, str(motive_id))
        if model is None:
            return None
        return Motive(
            motive_id=UUID(model.motive_id),
            character_id=UUID(model.character_id),
            description=model.description,
            status=CharacterRecordStatus(model.status),
            provenance=self._provenance_contract(model),
        )

    def create_goal(self, goal: Goal) -> None:
        self._session.add(
            GoalModel(
                goal_id=str(goal.goal_id),
                character_id=str(goal.character_id),
                motive_id=str(goal.motive_id) if goal.motive_id else None,
                parent_goal_id=(
                    str(goal.parent_goal_id) if goal.parent_goal_id else None
                ),
                desired_outcome=goal.desired_outcome,
                status=goal.status.value,
                **self._provenance_values(goal.provenance),
            )
        )

    def get_goal(self, goal_id: UUID) -> Goal | None:
        model = self._session.get(GoalModel, str(goal_id))
        if model is None:
            return None
        return Goal(
            goal_id=UUID(model.goal_id),
            character_id=UUID(model.character_id),
            motive_id=UUID(model.motive_id) if model.motive_id else None,
            parent_goal_id=(
                UUID(model.parent_goal_id) if model.parent_goal_id else None
            ),
            desired_outcome=model.desired_outcome,
            status=GoalStatus(model.status),
            provenance=self._provenance_contract(model),
        )

    def create_plan(self, plan: Plan) -> None:
        self._session.add(
            PlanModel(
                plan_id=str(plan.plan_id),
                character_id=str(plan.character_id),
                goal_id=str(plan.goal_id),
                name=plan.name,
                status=plan.status.value,
                **self._provenance_values(plan.provenance),
            )
        )

    def get_plan(self, plan_id: UUID) -> Plan | None:
        model = self._session.get(PlanModel, str(plan_id))
        if model is None:
            return None
        return Plan(
            plan_id=UUID(model.plan_id),
            character_id=UUID(model.character_id),
            goal_id=UUID(model.goal_id),
            name=model.name,
            status=PlanStatus(model.status),
            provenance=self._provenance_contract(model),
        )

    def create_plan_step(self, step: PlanStep) -> None:
        self._session.add(
            PlanStepModel(
                step_id=str(step.step_id),
                plan_id=str(step.plan_id),
                sequence=step.sequence,
                action_intent=step.action_intent,
                required_capabilities=list(step.required_capabilities),
                required_resources=list(step.required_resources),
                required_knowledge_fact_keys=list(step.required_knowledge_fact_keys),
                resource_effects=[
                    effect.model_dump(mode="json") for effect in step.resource_effects
                ],
                status=step.status.value,
                resolution_reason=step.resolution_reason,
                **self._provenance_values(step.provenance),
            )
        )

    def get_plan_step(self, step_id: UUID) -> PlanStep | None:
        model = self._session.get(PlanStepModel, str(step_id))
        return self._plan_step_contract(model) if model is not None else None

    def mark_plan_step_scheduled(self, step_id: UUID) -> None:
        model = self._session.get(PlanStepModel, str(step_id))
        if model is None:
            raise KeyError(f"Unknown plan step {step_id}")
        if model.status != PlanStepStatus.PENDING.value:
            raise ValueError("Only pending plan steps can be scheduled")
        model.status = PlanStepStatus.SCHEDULED.value

    def mark_plan_step_completed(self, step_id: UUID) -> None:
        model = self._session.get(PlanStepModel, str(step_id))
        if model is None:
            raise KeyError(f"Unknown plan step {step_id}")
        if model.status != PlanStepStatus.SCHEDULED.value:
            raise ValueError("Only scheduled plan steps can be completed")
        model.status = PlanStepStatus.COMPLETED.value

    def mark_plan_step_failed(self, step_id: UUID, reason: str) -> None:
        model = self._session.get(PlanStepModel, str(step_id))
        if model is None:
            raise KeyError(f"Unknown plan step {step_id}")
        if model.status != PlanStepStatus.SCHEDULED.value:
            raise ValueError("Only scheduled plan steps can fail")
        model.status = PlanStepStatus.FAILED.value
        model.resolution_reason = reason

    def create_resource_balance(self, balance: ResourceBalance) -> None:
        self._session.add(
            ResourceBalanceModel(
                balance_id=str(balance.balance_id),
                owner_kind=balance.owner_kind.value,
                owner_id=str(balance.owner_id),
                resource_code=balance.resource_code,
                resource_kind=balance.resource_kind.value,
                quantity=balance.quantity,
                reserved=balance.reserved,
                version=balance.version,
            )
        )

    def get_resource_balance(
        self,
        owner_kind: ResourceOwnerKind,
        owner_id: UUID,
        resource_code: str,
    ) -> ResourceBalance | None:
        model = self._resource_balance_model(owner_kind, owner_id, resource_code)
        return self._resource_balance_contract(model) if model else None

    def get_available_resource_quantity(
        self,
        owner_kind: ResourceOwnerKind,
        owner_id: UUID,
        resource_code: str,
    ) -> Decimal:
        model = self._resource_balance_model(owner_kind, owner_id, resource_code)
        if model is None:
            return Decimal(0)
        return Decimal(model.quantity) - Decimal(model.reserved)

    def reserve_resource(self, reservation: ResourceReservation) -> None:
        model = self._require_resource_balance(
            reservation.owner_kind,
            reservation.owner_id,
            reservation.resource_code,
        )
        available = Decimal(model.quantity) - Decimal(model.reserved)
        if available < reservation.quantity:
            raise ResourceInvariantError(
                f"Insufficient available resource {reservation.resource_code}"
            )
        model.reserved += reservation.quantity
        model.version += 1
        self._session.add(
            ResourceReservationModel(
                reservation_id=str(reservation.reservation_id),
                scheduled_event_id=str(reservation.scheduled_event_id),
                owner_kind=reservation.owner_kind.value,
                owner_id=str(reservation.owner_id),
                resource_code=reservation.resource_code,
                quantity=reservation.quantity,
                applied=False,
                cancelled=False,
            )
        )

    def apply_resource_transaction(
        self,
        transaction: ResourceTransaction,
    ) -> None:
        existing = None
        if transaction.scheduled_event_id is not None:
            existing = self._session.scalar(
                select(ResourceTransactionModel).where(
                    ResourceTransactionModel.scheduled_event_id
                    == str(transaction.scheduled_event_id),
                    ResourceTransactionModel.resource_code
                    == transaction.resource_code,
                )
            )
        if existing is not None:
            return
        model = self._require_resource_balance(
            transaction.owner_kind,
            transaction.owner_id,
            transaction.resource_code,
        )
        result = Decimal(model.quantity) + transaction.delta
        if result < 0:
            raise ResourceInvariantError(
                f"Resource transaction makes {transaction.resource_code} negative"
            )
        if transaction.resulting_quantity != result:
            raise ResourceInvariantError(
                "Resource transaction resulting quantity is stale"
            )
        reservation = None
        if transaction.scheduled_event_id is not None and transaction.delta < 0:
            reservation = self._session.scalar(
                select(ResourceReservationModel).where(
                    ResourceReservationModel.scheduled_event_id
                    == str(transaction.scheduled_event_id),
                    ResourceReservationModel.owner_kind
                    == transaction.owner_kind.value,
                    ResourceReservationModel.owner_id
                    == str(transaction.owner_id),
                    ResourceReservationModel.resource_code
                    == transaction.resource_code,
                    ResourceReservationModel.applied.is_(False),
                    ResourceReservationModel.cancelled.is_(False),
                )
            )
            if reservation is None or Decimal(reservation.quantity) < -transaction.delta:
                raise ResourceInvariantError(
                    "Negative resource transaction requires sufficient reservation"
                )
        if reservation is not None:
            model.reserved -= reservation.quantity
            reservation.applied = True
        model.quantity = result
        model.version += 1
        self._session.add(
            ResourceTransactionModel(
                transaction_id=str(transaction.transaction_id),
                owner_kind=transaction.owner_kind.value,
                owner_id=str(transaction.owner_id),
                resource_code=transaction.resource_code,
                delta=transaction.delta,
                resulting_quantity=result,
                scheduled_event_id=(
                    str(transaction.scheduled_event_id)
                    if transaction.scheduled_event_id is not None
                    else None
                ),
                event_id=(
                    str(transaction.event_id)
                    if transaction.event_id is not None
                    else None
                ),
                simulation_run_id=(
                    str(transaction.simulation_run_id)
                    if transaction.simulation_run_id is not None
                    else None
                ),
                occurred_at=transaction.occurred_at,
            )
        )

    def release_resource_reservation(
        self,
        reservation_id: UUID,
        *,
        cancelled: bool,
    ) -> None:
        reservation = self._session.get(
            ResourceReservationModel,
            str(reservation_id),
        )
        if reservation is None:
            raise KeyError(f"Unknown resource reservation {reservation_id}")
        if reservation.applied or reservation.cancelled:
            return
        balance = self._require_resource_balance(
            ResourceOwnerKind(reservation.owner_kind),
            UUID(reservation.owner_id),
            reservation.resource_code,
        )
        balance.reserved -= reservation.quantity
        balance.version += 1
        reservation.cancelled = cancelled
        reservation.applied = not cancelled

    def list_resource_reservations(
        self,
        scheduled_event_id: UUID,
    ) -> tuple[ResourceReservation, ...]:
        models = self._session.scalars(
            select(ResourceReservationModel).where(
                ResourceReservationModel.scheduled_event_id
                == str(scheduled_event_id)
            )
        ).all()
        return tuple(self._resource_reservation_contract(model) for model in models)

    def list_resource_transactions(
        self,
        scheduled_event_id: UUID,
    ) -> tuple[ResourceTransaction, ...]:
        models = self._session.scalars(
            select(ResourceTransactionModel)
            .where(
                ResourceTransactionModel.scheduled_event_id
                == str(scheduled_event_id)
            )
            .order_by(ResourceTransactionModel.resource_code)
        ).all()
        return tuple(self._resource_transaction_contract(model) for model in models)

    def _resource_balance_model(
        self,
        owner_kind: ResourceOwnerKind,
        owner_id: UUID,
        resource_code: str,
    ) -> ResourceBalanceModel | None:
        return self._session.scalar(
            select(ResourceBalanceModel).where(
                ResourceBalanceModel.owner_kind == owner_kind.value,
                ResourceBalanceModel.owner_id == str(owner_id),
                ResourceBalanceModel.resource_code == resource_code,
            )
        )

    def _require_resource_balance(
        self,
        owner_kind: ResourceOwnerKind,
        owner_id: UUID,
        resource_code: str,
    ) -> ResourceBalanceModel:
        model = self._resource_balance_model(owner_kind, owner_id, resource_code)
        if model is None:
            raise ValueError(f"Resource balance {resource_code} was not found")
        return model

    @staticmethod
    def _resource_balance_contract(model: ResourceBalanceModel) -> ResourceBalance:
        return ResourceBalance(
            balance_id=UUID(model.balance_id),
            owner_kind=ResourceOwnerKind(model.owner_kind),
            owner_id=UUID(model.owner_id),
            resource_code=model.resource_code,
            resource_kind=ResourceKind(model.resource_kind),
            quantity=Decimal(model.quantity),
            reserved=Decimal(model.reserved),
            version=model.version,
        )

    @staticmethod
    def _resource_reservation_contract(
        model: ResourceReservationModel,
    ) -> ResourceReservation:
        return ResourceReservation(
            reservation_id=UUID(model.reservation_id),
            scheduled_event_id=UUID(model.scheduled_event_id),
            owner_kind=ResourceOwnerKind(model.owner_kind),
            owner_id=UUID(model.owner_id),
            resource_code=model.resource_code,
            quantity=Decimal(model.quantity),
            applied=model.applied,
            cancelled=model.cancelled,
        )

    @staticmethod
    def _resource_transaction_contract(
        model: ResourceTransactionModel,
    ) -> ResourceTransaction:
        return ResourceTransaction(
            transaction_id=UUID(model.transaction_id),
            owner_kind=ResourceOwnerKind(model.owner_kind),
            owner_id=UUID(model.owner_id),
            resource_code=model.resource_code,
            delta=Decimal(model.delta),
            resulting_quantity=Decimal(model.resulting_quantity),
            scheduled_event_id=(
                UUID(model.scheduled_event_id)
                if model.scheduled_event_id is not None
                else None
            ),
            event_id=UUID(model.event_id) if model.event_id is not None else None,
            simulation_run_id=(
                UUID(model.simulation_run_id)
                if model.simulation_run_id is not None
                else None
            ),
            occurred_at=model.occurred_at,
        )

    def create_npc_decision(
        self,
        proposal: NpcDecisionProposal,
        *,
        context: NpcDecisionContext,
    ) -> None:
        self._session.add(
            NpcDecisionProposalModel(
                proposal_id=str(proposal.proposal_id),
                request_id=str(proposal.request_id),
                character_id=str(proposal.character_id),
                reaction=proposal.reaction,
                decision_type=proposal.decision_type.value,
                target_plan_step_id=(
                    str(proposal.target_plan_step_id)
                    if proposal.target_plan_step_id
                    else None
                ),
                rationale=proposal.rationale,
                required_resources=list(proposal.required_resources),
                confidence=proposal.confidence,
                validation_requirements=list(proposal.validation_requirements),
                status=proposal.status.value,
                rejection_reason=proposal.rejection_reason,
                context_hash=proposal.context_hash,
                context=context.model_dump(mode="json"),
                application_result=proposal.application_result,
                **self._provenance_values(proposal.provenance),
            )
        )

    def get_npc_decision(
        self,
        proposal_id: UUID,
    ) -> NpcDecisionProposal | None:
        model = self._session.get(NpcDecisionProposalModel, str(proposal_id))
        return self._npc_decision_contract(model) if model is not None else None

    def get_npc_decision_by_request(
        self,
        request_id: UUID,
    ) -> NpcDecisionProposal | None:
        model = self._session.scalar(
            select(NpcDecisionProposalModel).where(
                NpcDecisionProposalModel.request_id == str(request_id)
            )
        )
        return self._npc_decision_contract(model) if model is not None else None

    def get_npc_decision_context(
        self,
        proposal_id: UUID,
    ) -> NpcDecisionContext | None:
        model = self._session.get(NpcDecisionProposalModel, str(proposal_id))
        return NpcDecisionContext.model_validate(model.context) if model else None

    def save_npc_decision_application(
        self,
        proposal: NpcDecisionProposal,
    ) -> None:
        model = self._session.get(NpcDecisionProposalModel, str(proposal.proposal_id))
        if model is None:
            raise KeyError(f"Unknown NPC decision proposal {proposal.proposal_id}")
        model.status = proposal.status.value
        model.rejection_reason = proposal.rejection_reason
        model.application_result = proposal.application_result
        model.version = proposal.provenance.version
        model.updated_at = proposal.provenance.updated_at

    def _scheduled_model(self, event_id: UUID) -> ScheduledEventModel:
        model = self._session.get(ScheduledEventModel, str(event_id))
        if model is None:
            raise KeyError(f"Unknown scheduled event {event_id}")
        return model

    @staticmethod
    def _provenance_values(provenance: RecordProvenance) -> dict[str, object]:
        return {
            "source_type": provenance.source_type,
            "source_id": provenance.source_id,
            "origin_event_id": (
                str(provenance.origin_event_id)
                if provenance.origin_event_id
                else None
            ),
            "version": provenance.version,
            "created_at": provenance.created_at,
            "updated_at": provenance.updated_at,
        }

    @staticmethod
    def _provenance_contract(model: object) -> RecordProvenance:
        return RecordProvenance(
            source_type=model.source_type,  # type: ignore[attr-defined]
            source_id=model.source_id,  # type: ignore[attr-defined]
            origin_event_id=(
                UUID(model.origin_event_id)  # type: ignore[attr-defined]
                if model.origin_event_id  # type: ignore[attr-defined]
                else None
            ),
            version=model.version,  # type: ignore[attr-defined]
            created_at=model.created_at,  # type: ignore[attr-defined]
            updated_at=model.updated_at,  # type: ignore[attr-defined]
        )

    @staticmethod
    def _relationship_contract(model: RelationshipModel) -> Relationship:
        return Relationship(
            relationship_id=UUID(model.relationship_id),
            source_character_id=UUID(model.source_character_id),
            target_character_id=UUID(model.target_character_id),
            dimensions=tuple(
                RelationshipDimension.model_validate(item)
                for item in model.dimensions
            ),
            hidden=model.hidden,
            status=CharacterRecordStatus(model.status),
            provenance=SqlAlchemySimulationRepository._provenance_contract(model),
        )

    @staticmethod
    def _plan_step_contract(model: PlanStepModel) -> PlanStep:
        return PlanStep(
            step_id=UUID(model.step_id),
            plan_id=UUID(model.plan_id),
            sequence=model.sequence,
            action_intent=model.action_intent,
            required_capabilities=tuple(model.required_capabilities),
            required_resources=tuple(model.required_resources),
            required_knowledge_fact_keys=tuple(model.required_knowledge_fact_keys),
            resource_effects=tuple(
                ResourceEffect.model_validate(effect)
                for effect in model.resource_effects
            ),
            resolution_reason=model.resolution_reason,
            status=PlanStepStatus(model.status),
            provenance=SqlAlchemySimulationRepository._provenance_contract(model),
        )

    @staticmethod
    def _npc_decision_contract(
        model: NpcDecisionProposalModel,
    ) -> NpcDecisionProposal:
        return NpcDecisionProposal(
            proposal_id=UUID(model.proposal_id),
            request_id=UUID(model.request_id),
            character_id=UUID(model.character_id),
            reaction=model.reaction,
            decision_type=NpcDecisionType(model.decision_type),
            target_plan_step_id=(
                UUID(model.target_plan_step_id)
                if model.target_plan_step_id
                else None
            ),
            rationale=model.rationale,
            required_resources=tuple(model.required_resources),
            confidence=model.confidence,
            validation_requirements=tuple(model.validation_requirements),
            status=NpcDecisionProposalStatus(model.status),
            rejection_reason=model.rejection_reason,
            context_hash=model.context_hash,
            application_result=model.application_result,
            provenance=SqlAlchemySimulationRepository._provenance_contract(model),
        )

    @staticmethod
    def _presentation_model(
        presentation: PresentationRecord,
    ) -> NarrativePresentationModel:
        return NarrativePresentationModel(
            presentation_id=str(presentation.presentation_id),
            simulation_run_id=str(presentation.simulation_run_id),
            protagonist_character_id=str(presentation.protagonist_character_id),
            narrative_time=presentation.narrative_time,
            status=presentation.status.value,
            generated_content=presentation.generated_content,
            delivered_content=presentation.delivered_content,
            confirmed_fact_ids=list(presentation.confirmed_fact_ids),
            created_at=presentation.created_at,
            delivered_at=presentation.delivered_at,
        )

    @staticmethod
    def _presentation_contract(
        model: NarrativePresentationModel,
    ) -> PresentationRecord:
        return PresentationRecord(
            presentation_id=UUID(model.presentation_id),
            simulation_run_id=UUID(model.simulation_run_id),
            protagonist_character_id=UUID(model.protagonist_character_id),
            narrative_time=model.narrative_time,
            status=PresentationStatus(model.status),
            generated_content=model.generated_content,
            delivered_content=model.delivered_content,
            confirmed_fact_ids=tuple(model.confirmed_fact_ids),
            created_at=model.created_at,
            delivered_at=model.delivered_at,
        )

    @staticmethod
    def _transmission_contract(
        model: InformationTransmissionModel,
    ) -> InformationTransmission:
        return InformationTransmission(
            transmission_id=UUID(model.transmission_id),
            source_event_id=(
                UUID(model.source_event_id)
                if model.source_event_id is not None
                else None
            ),
            sender_character_id=(
                UUID(model.sender_character_id)
                if model.sender_character_id is not None
                else None
            ),
            recipient_character_id=UUID(model.recipient_character_id),
            fact_key=model.fact_key,
            statement=model.statement,
            medium=CommunicationMedium(model.medium),
            nature=InformationNature(model.nature),
            sent_at=model.sent_at,
            arrival_at=model.arrival_at,
            status=TransmissionStatus(model.status),
            perceived_reliability=model.perceived_reliability,
            alterations=tuple(model.alterations),
            sender_intent=model.sender_intent,
            reach=model.reach,
        )

    def _set_scheduled_status(
        self,
        event_id: UUID,
        status: ScheduledEventStatus,
    ) -> None:
        self._scheduled_model(event_id).status = status.value

    @staticmethod
    def _scheduled_contract(model: ScheduledEventModel) -> ScheduledEvent:
        return ScheduledEvent(
            event_id=UUID(model.event_id),
            world_id=UUID(model.world_id),
            timeline_id=UUID(model.timeline_id),
            scheduled_at=model.scheduled_at,
            event_type=model.event_type,
            source_type=model.source_type,
            source_id=model.source_id,
            caused_by=tuple(UUID(value) for value in model.caused_by),
            priority=model.priority,
            payload_version=model.payload_version,
            payload=model.payload,
            interruption_class=InterruptionClass(model.interruption_class),
        )

    @staticmethod
    def _run_contract(model: SimulationRunModel) -> SimulationRunRecord:
        return SimulationRunRecord(
            simulation_run_id=UUID(model.simulation_run_id),
            operation=model.operation,
            world_id=UUID(model.world_id),
            timeline_id=UUID(model.timeline_id),
            status=SimulationRunStatus(model.status),
            initial_time=model.initial_time,
            target_time=model.target_time,
            final_time=model.final_time,
            processed_event_ids=tuple(
                UUID(event_id) for event_id in model.processed_event_ids
            ),
            error=model.error,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
