from datetime import UTC, datetime
from datetime import timedelta
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
    MembershipStatus,
    OrganizationAuthorityGrant,
    OrganizationDecisionContext,
    OrganizationDecisionProposal,
    OrganizationDecisionProposalStatus,
    OrganizationDecisionType,
    OrganizationGoal,
    OrganizationGovernance,
    OrganizationIdentity,
    OrganizationMembership,
    OrganizationMotive,
    OrganizationPlan,
    OrganizationPlanStep,
    OrganizationRole,
    OrganizationStatus,
    ActorPosition,
    ActorReference,
    ActorType,
    ClaimSemantics,
    ControlStatus,
    InfrastructureFacility,
    InfrastructureNode,
    Journey,
    JourneyStatus,
    ResourceCharge,
    Location,
    LocationType,
    TerritoryClaim,
    TransportMode,
    TransportRoute,
    TransportRouteSegment,
    EcologicalProcess,
    Habitat,
    HealthCondition,
    HealthState,
    LifecycleStage,
    OrganismKind,
    Population,
    PopulationCohort,
    Species,
    AssessmentOutcome,
    CharacterLanguageProficiency,
    Dialect,
    EducationEnrollment,
    EducationProgram,
    IndividualBeliefRecord,
    KnowledgeArtifact,
    KnowledgeLifecycleRecord,
    Language,
    LearningOpportunity,
    MetaphysicalTruth,
    ReligionTradition,
    RitualCompletion,
    Technology,
    WritingSystem,
    Appeal,
    DiplomaticAction,
    EvidenceRecord,
    IntelligenceOperation,
    Investigation,
    LegalCase,
    LegalProceeding,
    NormativeRule,
    NormativeSystem,
    Offense,
    OrganizationRelation,
    Sanction,
    SecurityIncident,
    SecurityResolution,
    SecurityThreat,
    StrategicConflict,
    Treaty,
    CollectiveReception,
    CreativeWork,
    GeneratedAsset,
    LeisureRoutine,
    PublicChannel,
    PublicInformation,
    SonicIdentity,
    VisualIdentity,
    CanonicalProposal,
    CanonicalRecord,
    CharacterProgressionApplication,
    CharacterProgressionEvidence,
    CharacterProgressionProposal,
    CharacterProgressionValidation,
    CharacterSheet,
    AggregatePopulationSourceLink,
    MaterializedIndividualLink,
    SimulationTierState,
    SimulationTierTransitionResult,
    CultureDefinition,
    SocialGroup,
    IndividualCulturalAffiliation,
    CulturalChangeRecord,
    CulturalAffiliationTargetType,
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
    OrganizationAuthorityGrantModel,
    OrganizationDecisionProposalModel,
    OrganizationGoalModel,
    OrganizationGovernanceModel,
    OrganizationIdentityModel,
    OrganizationMembershipModel,
    OrganizationMotiveModel,
    OrganizationPlanModel,
    OrganizationPlanStepModel,
    ActorPositionModel,
    InfrastructureFacilityModel,
    InfrastructureNodeModel,
    JourneyModel,
    LocationModel,
    TerritoryClaimModel,
    TransportRouteModel,
    TransportRouteSegmentModel,
    EcologicalProcessModel,
    HabitatModel,
    HealthStateModel,
    PopulationModel,
    SpeciesModel,
    AssessmentOutcomeModel,
    CharacterLanguageProficiencyModel,
    DialectModel,
    EducationEnrollmentModel,
    EducationProgramModel,
    IndividualBeliefRecordModel,
    KnowledgeArtifactModel,
    KnowledgeLifecycleRecordModel,
    LanguageModel,
    LearningOpportunityModel,
    MetaphysicalTruthModel,
    ReligionTraditionModel,
    RitualCompletionModel,
    TechnologyModel,
    WritingSystemModel,
    AppealModel,
    DiplomaticActionModel,
    EvidenceRecordModel,
    IntelligenceOperationModel,
    InvestigationModel,
    LegalCaseModel,
    LegalProceedingModel,
    NormativeRuleModel,
    NormativeSystemModel,
    OffenseModel,
    OrganizationRelationModel,
    SanctionModel,
    SecurityIncidentModel,
    SecurityResolutionModel,
    SecurityThreatModel,
    StrategicConflictModel,
    TreatyModel,
    CollectiveReceptionModel,
    CreativeWorkModel,
    GeneratedAssetModel,
    LeisureRoutineModel,
    PublicChannelModel,
    PublicInformationModel,
    SonicIdentityModel,
    VisualIdentityModel,
    CanonicalProposalModel,
    CanonicalRecordModel,
    CharacterProgressionApplicationModel,
    CharacterProgressionEvidenceModel,
    CharacterProgressionProposalModel,
    CharacterProgressionValidationModel,
    CharacterSheetModel,
    AggregatePopulationSourceLinkModel,
    MaterializedIndividualLinkModel,
    SimulationTierStateModel,
    SimulationTierTransitionResultModel,
    CultureDefinitionModel,
    SocialGroupModel,
    IndividualCulturalAffiliationModel,
    CulturalChangeRecordModel,
)


class SqlAlchemySimulationRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get_tier_transition_result(
        self, request_id: UUID
    ) -> SimulationTierTransitionResult | None:
        model = self._session.get(
            SimulationTierTransitionResultModel, str(request_id)
        )
        return (
            SimulationTierTransitionResult.model_validate(model.payload)
            if model
            else None
        )

    def save_tier_transition_result(
        self, result: SimulationTierTransitionResult
    ) -> None:
        self._session.add(
            SimulationTierTransitionResultModel(
                request_id=str(result.request.request_id),
                world_id=str(result.request.world_id),
                payload=result.model_dump(mode="json"),
            )
        )

    def get_simulation_tier_state(
        self, entity_id: UUID
    ) -> SimulationTierState | None:
        model = self._session.get(SimulationTierStateModel, str(entity_id))
        return SimulationTierState.model_validate(model.payload) if model else None

    def create_simulation_tier_state(self, state: SimulationTierState) -> None:
        self._session.add(
            SimulationTierStateModel(
                entity_id=str(state.entity_id),
                world_id=str(state.world_id),
                entity_type=state.entity_type,
                version=state.provenance.version,
                payload=state.model_dump(mode="json"),
            )
        )

    def save_simulation_tier_state(
        self, state: SimulationTierState, expected_version: int
    ) -> None:
        model = self._session.get(SimulationTierStateModel, str(state.entity_id))
        if model is None:
            raise KeyError(f"Unknown simulation tier state {state.entity_id}")
        self._check_expected_version(model, expected_version)
        model.version = state.provenance.version
        model.payload = state.model_dump(mode="json")

    def get_materialized_individual_link(
        self, character_id: UUID
    ) -> MaterializedIndividualLink | None:
        model = self._session.get(
            MaterializedIndividualLinkModel, str(character_id)
        )
        return MaterializedIndividualLink.model_validate(model.payload) if model else None

    def create_materialized_individual_link(
        self, link: MaterializedIndividualLink
    ) -> None:
        self._session.add(
            MaterializedIndividualLinkModel(
                character_id=str(link.character_id),
                population_id=str(link.population_id),
                cohort_id=str(link.cohort_id),
                payload=link.model_dump(mode="json"),
            )
        )

    def list_aggregate_population_source_links(
        self, population_id: UUID
    ) -> tuple[AggregatePopulationSourceLink, ...]:
        models = self._session.scalars(
            select(AggregatePopulationSourceLinkModel)
            .where(
                AggregatePopulationSourceLinkModel.population_id
                == str(population_id)
            )
            .order_by(AggregatePopulationSourceLinkModel.cohort_id)
        ).all()
        return tuple(
            AggregatePopulationSourceLink.model_validate(model.payload)
            for model in models
        )

    def save_aggregate_population_source_link(
        self, link: AggregatePopulationSourceLink, expected_version: int | None = None
    ) -> None:
        model = self._session.get(
            AggregatePopulationSourceLinkModel,
            (str(link.population_id), str(link.cohort_id)),
        )
        if model is None:
            self._session.add(
                AggregatePopulationSourceLinkModel(
                    population_id=str(link.population_id),
                    cohort_id=str(link.cohort_id),
                    version=link.provenance.version,
                    payload=link.model_dump(mode="json"),
                )
            )
            return
        self._check_expected_version(model, expected_version)
        model.version = link.provenance.version
        model.payload = link.model_dump(mode="json")

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
                source_language_id=(
                    str(transmission.source_language_id)
                    if transmission.source_language_id
                    else None
                ),
                target_language_id=(
                    str(transmission.target_language_id)
                    if transmission.target_language_id
                    else None
                ),
                source_dialect_id=(
                    str(transmission.source_dialect_id)
                    if transmission.source_dialect_id
                    else None
                ),
                target_dialect_id=(
                    str(transmission.target_dialect_id)
                    if transmission.target_dialect_id
                    else None
                ),
                writing_system_id=(
                    str(transmission.writing_system_id)
                    if transmission.writing_system_id
                    else None
                ),
                presentation_language=transmission.presentation_language,
                translation_semantics=list(transmission.translation_semantics),
                imperfect_translation=transmission.imperfect_translation,
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

    def mark_transmission_failed(self, transmission_id: UUID) -> None:
        model = self._session.get(
            InformationTransmissionModel,
            str(transmission_id),
        )
        if model is None:
            raise KeyError(f"Unknown information transmission {transmission_id}")
        model.status = TransmissionStatus.FAILED.value

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

    def create_organization_identity(self, identity: OrganizationIdentity) -> None:
        self._session.add(
            OrganizationIdentityModel(
                identity_id=str(identity.identity_id),
                organization_id=str(identity.organization_id),
                display_name=identity.display_name,
                purpose=identity.purpose,
                history=identity.history,
                interests=list(identity.interests),
                relationships=list(identity.relationships),
                territory_references=list(identity.territory_references),
                internal_conflicts=list(identity.internal_conflicts),
                status=identity.status.value,
                **self._provenance_values(identity.provenance),
            )
        )

    def get_organization_identity(
        self, organization_id: UUID
    ) -> OrganizationIdentity | None:
        model = self._session.scalar(
            select(OrganizationIdentityModel).where(
                OrganizationIdentityModel.organization_id == str(organization_id)
            )
        )
        if model is None:
            return None
        return OrganizationIdentity(
            identity_id=UUID(model.identity_id),
            organization_id=UUID(model.organization_id),
            display_name=model.display_name,
            purpose=model.purpose,
            history=model.history,
            interests=tuple(model.interests),
            relationships=tuple(model.relationships),
            territory_references=tuple(model.territory_references),
            internal_conflicts=tuple(model.internal_conflicts),
            status=OrganizationStatus(model.status),
            provenance=self._provenance_contract(model),
        )

    def create_organization_governance(
        self, governance: OrganizationGovernance
    ) -> None:
        self._session.add(
            OrganizationGovernanceModel(
                governance_id=str(governance.governance_id),
                organization_id=str(governance.organization_id),
                system=governance.system,
                decision_rules=list(governance.decision_rules),
                role_definitions=[
                    item.model_dump(mode="json") for item in governance.role_definitions
                ],
                status=governance.status.value,
                **self._provenance_values(governance.provenance),
            )
        )

    def get_organization_governance(
        self, organization_id: UUID
    ) -> OrganizationGovernance | None:
        model = self._session.scalar(
            select(OrganizationGovernanceModel).where(
                OrganizationGovernanceModel.organization_id == str(organization_id)
            )
        )
        if model is None:
            return None
        return OrganizationGovernance(
            governance_id=UUID(model.governance_id),
            organization_id=UUID(model.organization_id),
            system=model.system,
            decision_rules=tuple(model.decision_rules),
            role_definitions=tuple(
                OrganizationRole.model_validate(item) for item in model.role_definitions
            ),
            status=OrganizationStatus(model.status),
            provenance=self._provenance_contract(model),
        )

    def create_organization_membership(
        self, membership: OrganizationMembership
    ) -> None:
        self._session.add(
            OrganizationMembershipModel(
                membership_id=str(membership.membership_id),
                organization_id=str(membership.organization_id),
                character_id=str(membership.character_id),
                formal_roles=list(membership.formal_roles),
                informal_roles=list(membership.informal_roles),
                effective_influence=list(membership.effective_influence),
                status=membership.status.value,
                **self._provenance_values(membership.provenance),
            )
        )

    def get_organization_membership(
        self, organization_id: UUID, character_id: UUID
    ) -> OrganizationMembership | None:
        model = self._session.scalar(
            select(OrganizationMembershipModel).where(
                OrganizationMembershipModel.organization_id == str(organization_id),
                OrganizationMembershipModel.character_id == str(character_id),
            )
        )
        return self._organization_membership_contract(model) if model else None

    def list_organization_memberships(
        self, organization_id: UUID
    ) -> tuple[OrganizationMembership, ...]:
        models = self._session.scalars(
            select(OrganizationMembershipModel).where(
                OrganizationMembershipModel.organization_id == str(organization_id)
            )
        ).all()
        return tuple(self._organization_membership_contract(item) for item in models)

    def create_organization_authority_grant(
        self, grant: OrganizationAuthorityGrant
    ) -> None:
        self._session.add(
            OrganizationAuthorityGrantModel(
                grant_id=str(grant.grant_id),
                organization_id=str(grant.organization_id),
                character_id=str(grant.character_id),
                role_code=grant.role_code,
                permission_codes=list(grant.permission_codes),
                formal=grant.formal,
                basis=grant.basis,
                status=grant.status.value,
                **self._provenance_values(grant.provenance),
            )
        )

    def list_organization_authority_grants(
        self, organization_id: UUID, character_id: UUID
    ) -> tuple[OrganizationAuthorityGrant, ...]:
        models = self._session.scalars(
            select(OrganizationAuthorityGrantModel).where(
                OrganizationAuthorityGrantModel.organization_id
                == str(organization_id),
                OrganizationAuthorityGrantModel.character_id == str(character_id),
                OrganizationAuthorityGrantModel.status
                == OrganizationStatus.ACTIVE.value,
            )
        ).all()
        return tuple(
            OrganizationAuthorityGrant(
                grant_id=UUID(item.grant_id),
                organization_id=UUID(item.organization_id),
                character_id=UUID(item.character_id),
                role_code=item.role_code,
                permission_codes=tuple(item.permission_codes),
                formal=item.formal,
                basis=item.basis,
                status=OrganizationStatus(item.status),
                provenance=self._provenance_contract(item),
            )
            for item in models
        )

    def create_organization_motive(self, motive: OrganizationMotive) -> None:
        self._session.add(
            OrganizationMotiveModel(
                motive_id=str(motive.motive_id),
                organization_id=str(motive.organization_id),
                description=motive.description,
                internal_supporters=list(motive.internal_supporters),
                internal_opposition=list(motive.internal_opposition),
                status=motive.status.value,
                **self._provenance_values(motive.provenance),
            )
        )

    def get_organization_motive(
        self, motive_id: UUID
    ) -> OrganizationMotive | None:
        model = self._session.get(OrganizationMotiveModel, str(motive_id))
        if model is None:
            return None
        return OrganizationMotive(
            motive_id=UUID(model.motive_id),
            organization_id=UUID(model.organization_id),
            description=model.description,
            internal_supporters=tuple(model.internal_supporters),
            internal_opposition=tuple(model.internal_opposition),
            status=OrganizationStatus(model.status),
            provenance=self._provenance_contract(model),
        )

    def create_organization_goal(self, goal: OrganizationGoal) -> None:
        self._session.add(
            OrganizationGoalModel(
                goal_id=str(goal.goal_id),
                organization_id=str(goal.organization_id),
                motive_id=str(goal.motive_id) if goal.motive_id else None,
                parent_goal_id=(
                    str(goal.parent_goal_id) if goal.parent_goal_id else None
                ),
                desired_outcome=goal.desired_outcome,
                status=goal.status.value,
                **self._provenance_values(goal.provenance),
            )
        )

    def get_organization_goal(self, goal_id: UUID) -> OrganizationGoal | None:
        model = self._session.get(OrganizationGoalModel, str(goal_id))
        if model is None:
            return None
        return OrganizationGoal(
            goal_id=UUID(model.goal_id),
            organization_id=UUID(model.organization_id),
            motive_id=UUID(model.motive_id) if model.motive_id else None,
            parent_goal_id=(
                UUID(model.parent_goal_id) if model.parent_goal_id else None
            ),
            desired_outcome=model.desired_outcome,
            status=GoalStatus(model.status),
            provenance=self._provenance_contract(model),
        )

    def create_organization_plan(self, plan: OrganizationPlan) -> None:
        self._session.add(
            OrganizationPlanModel(
                plan_id=str(plan.plan_id),
                organization_id=str(plan.organization_id),
                goal_id=str(plan.goal_id),
                name=plan.name,
                status=plan.status.value,
                **self._provenance_values(plan.provenance),
            )
        )

    def get_organization_plan(self, plan_id: UUID) -> OrganizationPlan | None:
        model = self._session.get(OrganizationPlanModel, str(plan_id))
        if model is None:
            return None
        return OrganizationPlan(
            plan_id=UUID(model.plan_id),
            organization_id=UUID(model.organization_id),
            goal_id=UUID(model.goal_id),
            name=model.name,
            status=PlanStatus(model.status),
            provenance=self._provenance_contract(model),
        )

    def create_organization_plan_step(self, step: OrganizationPlanStep) -> None:
        self._session.add(
            OrganizationPlanStepModel(
                step_id=str(step.step_id),
                plan_id=str(step.plan_id),
                sequence=step.sequence,
                action_intent=step.action_intent,
                required_capabilities=list(step.required_capabilities),
                required_resources=list(step.required_resources),
                required_knowledge_fact_keys=list(
                    step.required_knowledge_fact_keys
                ),
                resource_effects=[
                    effect.model_dump(mode="json") for effect in step.resource_effects
                ],
                responsible_character_id=(
                    str(step.responsible_character_id)
                    if step.responsible_character_id
                    else None
                ),
                required_permission_codes=list(step.required_permission_codes),
                resolution_reason=step.resolution_reason,
                status=step.status.value,
                **self._provenance_values(step.provenance),
            )
        )

    def get_organization_plan_step(
        self, step_id: UUID
    ) -> OrganizationPlanStep | None:
        model = self._session.get(OrganizationPlanStepModel, str(step_id))
        return self._organization_plan_step_contract(model) if model else None

    def mark_organization_plan_step_scheduled(self, step_id: UUID) -> None:
        model = self._session.get(OrganizationPlanStepModel, str(step_id))
        if model is None:
            raise KeyError(f"Unknown organization plan step {step_id}")
        if model.status != PlanStepStatus.PENDING.value:
            raise ValueError("Only pending organization plan steps can be scheduled")
        model.status = PlanStepStatus.SCHEDULED.value

    def mark_organization_plan_step_completed(self, step_id: UUID) -> None:
        model = self._session.get(OrganizationPlanStepModel, str(step_id))
        if model is None:
            raise KeyError(f"Unknown organization plan step {step_id}")
        if model.status != PlanStepStatus.SCHEDULED.value:
            raise ValueError("Only scheduled organization plan steps can be completed")
        model.status = PlanStepStatus.COMPLETED.value

    def mark_organization_plan_step_failed(self, step_id: UUID, reason: str) -> None:
        model = self._session.get(OrganizationPlanStepModel, str(step_id))
        if model is None:
            raise KeyError(f"Unknown organization plan step {step_id}")
        if model.status != PlanStepStatus.SCHEDULED.value:
            raise ValueError("Only scheduled organization plan steps can fail")
        model.status = PlanStepStatus.FAILED.value
        model.resolution_reason = reason

    def create_organization_decision(
        self,
        proposal: OrganizationDecisionProposal,
        *,
        context: OrganizationDecisionContext,
    ) -> None:
        self._session.add(
            OrganizationDecisionProposalModel(
                proposal_id=str(proposal.proposal_id),
                request_id=str(proposal.request_id),
                organization_id=str(proposal.organization_id),
                responsible_character_id=(
                    str(proposal.responsible_character_id)
                    if proposal.responsible_character_id
                    else None
                ),
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

    def get_organization_decision(
        self, proposal_id: UUID
    ) -> OrganizationDecisionProposal | None:
        model = self._session.get(
            OrganizationDecisionProposalModel, str(proposal_id)
        )
        return self._organization_decision_contract(model) if model else None

    def get_organization_decision_by_request(
        self, request_id: UUID
    ) -> OrganizationDecisionProposal | None:
        model = self._session.scalar(
            select(OrganizationDecisionProposalModel).where(
                OrganizationDecisionProposalModel.request_id == str(request_id)
            )
        )
        return self._organization_decision_contract(model) if model else None

    def get_organization_decision_context(
        self, proposal_id: UUID
    ) -> OrganizationDecisionContext | None:
        model = self._session.get(
            OrganizationDecisionProposalModel, str(proposal_id)
        )
        return OrganizationDecisionContext.model_validate(model.context) if model else None

    def save_organization_decision_application(
        self, proposal: OrganizationDecisionProposal
    ) -> None:
        model = self._session.get(
            OrganizationDecisionProposalModel, str(proposal.proposal_id)
        )
        if model is None:
            raise KeyError(f"Unknown organization proposal {proposal.proposal_id}")
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
    def _organization_membership_contract(
        model: OrganizationMembershipModel,
    ) -> OrganizationMembership:
        return OrganizationMembership(
            membership_id=UUID(model.membership_id),
            organization_id=UUID(model.organization_id),
            character_id=UUID(model.character_id),
            formal_roles=tuple(model.formal_roles),
            informal_roles=tuple(model.informal_roles),
            effective_influence=tuple(model.effective_influence),
            status=MembershipStatus(model.status),
            provenance=SqlAlchemySimulationRepository._provenance_contract(model),
        )

    @staticmethod
    def _organization_plan_step_contract(
        model: OrganizationPlanStepModel,
    ) -> OrganizationPlanStep:
        return OrganizationPlanStep(
            step_id=UUID(model.step_id),
            plan_id=UUID(model.plan_id),
            sequence=model.sequence,
            action_intent=model.action_intent,
            required_capabilities=tuple(model.required_capabilities),
            required_resources=tuple(model.required_resources),
            required_knowledge_fact_keys=tuple(
                model.required_knowledge_fact_keys
            ),
            resource_effects=tuple(
                ResourceEffect.model_validate(item)
                for item in model.resource_effects
            ),
            responsible_character_id=(
                UUID(model.responsible_character_id)
                if model.responsible_character_id
                else None
            ),
            required_permission_codes=tuple(model.required_permission_codes),
            resolution_reason=model.resolution_reason,
            status=PlanStepStatus(model.status),
            provenance=SqlAlchemySimulationRepository._provenance_contract(model),
        )

    @staticmethod
    def _organization_decision_contract(
        model: OrganizationDecisionProposalModel,
    ) -> OrganizationDecisionProposal:
        return OrganizationDecisionProposal(
            proposal_id=UUID(model.proposal_id),
            request_id=UUID(model.request_id),
            organization_id=UUID(model.organization_id),
            responsible_character_id=(
                UUID(model.responsible_character_id)
                if model.responsible_character_id
                else None
            ),
            reaction=model.reaction,
            decision_type=OrganizationDecisionType(model.decision_type),
            target_plan_step_id=(
                UUID(model.target_plan_step_id)
                if model.target_plan_step_id
                else None
            ),
            rationale=model.rationale,
            required_resources=tuple(model.required_resources),
            confidence=model.confidence,
            validation_requirements=tuple(model.validation_requirements),
            status=OrganizationDecisionProposalStatus(model.status),
            rejection_reason=model.rejection_reason,
            context_hash=model.context_hash,
            application_result=model.application_result,
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
            source_language_id=(
                UUID(model.source_language_id) if model.source_language_id else None
            ),
            target_language_id=(
                UUID(model.target_language_id) if model.target_language_id else None
            ),
            source_dialect_id=(
                UUID(model.source_dialect_id) if model.source_dialect_id else None
            ),
            target_dialect_id=(
                UUID(model.target_dialect_id) if model.target_dialect_id else None
            ),
            writing_system_id=(
                UUID(model.writing_system_id) if model.writing_system_id else None
            ),
            presentation_language=model.presentation_language,
            translation_semantics=tuple(model.translation_semantics or ()),
            imperfect_translation=model.imperfect_translation,
        )

    def create_location(self, location: Location) -> None:
        self._session.add(
            LocationModel(
                location_id=str(location.location_id),
                world_id=str(location.world_id),
                name=location.name,
                location_type=location.location_type.value,
                parent_location_id=(
                    str(location.parent_location_id)
                    if location.parent_location_id is not None
                    else None
                ),
                terrain=list(location.terrain),
                climate=list(location.climate),
                hydrology=list(location.hydrology),
                flora_fauna=list(location.flora_fauna),
                natural_resources=list(location.natural_resources),
                population_density=location.population_density,
                strategic_tags=list(location.strategic_tags),
                risk_tags=list(location.risk_tags),
                barrier_tags=list(location.barrier_tags),
                **self._provenance_values(location.provenance),
            )
        )

    def get_location(self, location_id: UUID) -> Location | None:
        model = self._session.get(LocationModel, str(location_id))
        return self._location_contract(model) if model else None

    def list_locations(self, world_id: UUID) -> tuple[Location, ...]:
        models = self._session.scalars(
            select(LocationModel)
            .where(LocationModel.world_id == str(world_id))
            .order_by(LocationModel.location_id)
        ).all()
        return tuple(self._location_contract(model) for model in models)

    def list_child_locations(self, parent_location_id: UUID) -> tuple[Location, ...]:
        models = self._session.scalars(
            select(LocationModel)
            .where(LocationModel.parent_location_id == str(parent_location_id))
            .order_by(LocationModel.location_id)
        ).all()
        return tuple(self._location_contract(model) for model in models)

    def create_territory_claim(self, claim: TerritoryClaim) -> None:
        self._session.add(
            TerritoryClaimModel(
                claim_id=str(claim.claim_id),
                location_id=str(claim.location_id),
                semantics=claim.semantics.value,
                owner_actor_type=(
                    claim.owner.actor_type.value if claim.owner is not None else None
                ),
                owner_actor_id=(
                    str(claim.owner.actor_id) if claim.owner is not None else None
                ),
                controller_actor_type=(
                    claim.controller.actor_type.value
                    if claim.controller is not None
                    else None
                ),
                controller_actor_id=(
                    str(claim.controller.actor_id)
                    if claim.controller is not None
                    else None
                ),
                status=claim.status.value,
                basis=claim.basis,
                **self._provenance_values(claim.provenance),
            )
        )

    def list_territory_claims(
        self, location_id: UUID
    ) -> tuple[TerritoryClaim, ...]:
        models = self._session.scalars(
            select(TerritoryClaimModel).where(
                TerritoryClaimModel.location_id == str(location_id)
            )
        ).all()
        return tuple(self._territory_claim_contract(model) for model in models)

    def create_infrastructure_node(self, node: InfrastructureNode) -> None:
        self._session.add(
            InfrastructureNodeModel(
                node_id=str(node.node_id),
                world_id=str(node.world_id),
                location_id=str(node.location_id),
                name=node.name,
                node_type=node.node_type,
                availability=node.availability,
                capacity=node.capacity,
                safety_tags=list(node.safety_tags),
                risk_tags=list(node.risk_tags),
                **self._provenance_values(node.provenance),
            )
        )

    def create_infrastructure_facility(
        self, facility: InfrastructureFacility
    ) -> None:
        self._session.add(
            InfrastructureFacilityModel(
                facility_id=str(facility.facility_id),
                node_id=str(facility.node_id),
                location_id=str(facility.location_id),
                facility_type=facility.facility_type,
                name=facility.name,
                availability=facility.availability,
                capacity=facility.capacity,
                resource_consumption=list(facility.resource_consumption),
                safety_tags=list(facility.safety_tags),
                risk_tags=list(facility.risk_tags),
                **self._provenance_values(facility.provenance),
            )
        )

    def get_infrastructure_node(
        self, node_id: UUID
    ) -> InfrastructureNode | None:
        model = self._session.get(InfrastructureNodeModel, str(node_id))
        return self._infrastructure_node_contract(model) if model else None

    def list_infrastructure_nodes(
        self, location_id: UUID
    ) -> tuple[InfrastructureNode, ...]:
        models = self._session.scalars(
            select(InfrastructureNodeModel).where(
                InfrastructureNodeModel.location_id == str(location_id)
            )
        ).all()
        return tuple(self._infrastructure_node_contract(model) for model in models)

    def get_infrastructure_facility(
        self, facility_id: UUID
    ) -> InfrastructureFacility | None:
        model = self._session.get(InfrastructureFacilityModel, str(facility_id))
        return self._infrastructure_facility_contract(model) if model else None

    def list_infrastructure_facilities(
        self, node_id: UUID
    ) -> tuple[InfrastructureFacility, ...]:
        models = self._session.scalars(
            select(InfrastructureFacilityModel).where(
                InfrastructureFacilityModel.node_id == str(node_id)
            )
        ).all()
        return tuple(
            self._infrastructure_facility_contract(model) for model in models
        )

    def create_transport_route(self, route: TransportRoute) -> None:
        self._session.add(
            TransportRouteModel(
                route_id=str(route.route_id),
                world_id=str(route.world_id),
                name=route.name,
                start_location_id=str(route.start_location_id),
                end_location_id=str(route.end_location_id),
                modes=[mode.value for mode in route.modes],
                availability=route.availability,
                **self._provenance_values(route.provenance),
            )
        )

    def get_transport_route(self, route_id: UUID) -> TransportRoute | None:
        model = self._session.get(TransportRouteModel, str(route_id))
        return self._transport_route_contract(model) if model else None

    def create_transport_route_segment(
        self, segment: TransportRouteSegment
    ) -> None:
        self._session.add(
            TransportRouteSegmentModel(
                segment_id=str(segment.segment_id),
                route_id=str(segment.route_id),
                sequence=segment.sequence,
                start_location_id=str(segment.start_location_id),
                end_location_id=str(segment.end_location_id),
                physical_distance=segment.physical_distance,
                distance_unit=segment.distance_unit,
                base_duration_microseconds=(
                    segment.base_duration // timedelta(microseconds=1)
                ),
                mode=segment.mode.value,
                costs=[item.model_dump(mode="json") for item in segment.costs],
                capacity=segment.capacity,
                availability=segment.availability,
                resource_consumption=[
                    item.model_dump(mode="json")
                    for item in segment.resource_consumption
                ],
                safety_tags=list(segment.safety_tags),
                risk_tags=list(segment.risk_tags),
                **self._provenance_values(segment.provenance),
            )
        )

    def list_transport_route_segments(
        self, route_id: UUID
    ) -> tuple[TransportRouteSegment, ...]:
        models = self._session.scalars(
            select(TransportRouteSegmentModel)
            .where(TransportRouteSegmentModel.route_id == str(route_id))
            .order_by(TransportRouteSegmentModel.sequence)
        ).all()
        return tuple(self._route_segment_contract(model) for model in models)

    def create_journey(self, journey: Journey) -> None:
        self._session.add(
            JourneyModel(
                journey_id=str(journey.journey_id),
                world_id=str(journey.world_id),
                timeline_id=str(journey.timeline_id),
                participants=[
                    {
                        "actor_type": item.actor.actor_type.value,
                        "actor_id": str(item.actor.actor_id),
                        "participant_type": item.participant_type.value,
                    }
                    for item in journey.participants
                ],
                start_location_id=str(journey.start_location_id),
                end_location_id=str(journey.end_location_id),
                route_id=str(journey.route_id),
                segment_ids=[str(item) for item in journey.segment_ids],
                resource_owner=(
                    {
                        "actor_type": journey.resource_owner.actor_type.value,
                        "actor_id": str(journey.resource_owner.actor_id),
                    }
                    if journey.resource_owner is not None
                    else None
                ),
                costs=[item.model_dump(mode="json") for item in journey.costs],
                resource_consumption=[
                    item.model_dump(mode="json")
                    for item in journey.resource_consumption
                ],
                started_at=journey.started_at,
                expected_arrival_at=journey.expected_arrival_at,
                arrived_at=journey.arrived_at,
                status=journey.status.value,
                scheduled_event_id=str(journey.scheduled_event_id),
                **self._provenance_values(journey.provenance),
            )
        )

    def get_journey(self, journey_id: UUID) -> Journey | None:
        model = self._session.get(JourneyModel, str(journey_id))
        return self._journey_contract(model) if model else None

    def get_actor_position(self, actor: ActorReference) -> ActorPosition | None:
        model = self._session.get(
            ActorPositionModel,
            (actor.actor_type.value, str(actor.actor_id)),
        )
        return self._actor_position_contract(model) if model else None

    def save_actor_position(self, position: ActorPosition) -> None:
        model = self._session.get(
            ActorPositionModel,
            (position.actor.actor_type.value, str(position.actor.actor_id)),
        )
        if model is None:
            self._session.add(
                ActorPositionModel(
                    actor_type=position.actor.actor_type.value,
                    actor_id=str(position.actor.actor_id),
                    location_id=str(position.location_id),
                    journey_id=(
                        str(position.journey_id)
                        if position.journey_id is not None
                        else None
                    ),
                    version=position.version,
                )
            )
            return
        model.location_id = str(position.location_id)
        model.journey_id = (
            str(position.journey_id) if position.journey_id is not None else None
        )
        model.version = position.version

    def mark_journey_in_transit(self, journey_id: UUID) -> None:
        model = self._session.get(JourneyModel, str(journey_id))
        if model is None:
            raise KeyError(f"Unknown journey {journey_id}")
        if JourneyStatus(model.status) != JourneyStatus.SCHEDULED:
            raise ValueError("Only scheduled journeys can start")
        model.status = JourneyStatus.IN_TRANSIT.value

    def mark_journey_arrived(self, journey_id: UUID, arrived_at: datetime) -> None:
        model = self._session.get(JourneyModel, str(journey_id))
        if model is None:
            raise KeyError(f"Unknown journey {journey_id}")
        if JourneyStatus(model.status) != JourneyStatus.IN_TRANSIT:
            raise ValueError("Only in-transit journeys can arrive")
        model.status = JourneyStatus.ARRIVED.value
        model.arrived_at = arrived_at

    def create_species(self, species: Species) -> None:
        self._session.add(
            SpeciesModel(
                species_id=str(species.species_id),
                world_id=str(species.world_id),
                name=species.name,
                organism_kind=species.organism_kind.value,
                anatomy=species.anatomy,
                physiology=species.physiology,
                reproduction_model=species.reproduction_model,
                nutrition=species.nutrition,
                habitat=list(species.habitat),
                senses=list(species.senses),
                adaptations=list(species.adaptations),
                lifecycle_stages=[
                    stage.model_dump(mode="json") for stage in species.lifecycle_stages
                ],
                resource_links=list(species.resource_links),
                **self._provenance_values(species.provenance),
            )
        )

    def get_species(self, species_id: UUID) -> Species | None:
        model = self._session.get(SpeciesModel, str(species_id))
        return self._species_contract(model) if model else None

    def create_habitat(self, habitat: Habitat) -> None:
        self._session.add(
            HabitatModel(
                habitat_id=str(habitat.habitat_id),
                world_id=str(habitat.world_id),
                location_id=str(habitat.location_id),
                name=habitat.name,
                habitat_type=habitat.habitat_type,
                habitability=habitat.habitability,
                species_ids=[str(item) for item in habitat.species_ids],
                resources=list(habitat.resources),
                resource_links=list(habitat.resource_links),
                characteristics=habitat.characteristics,
                **self._provenance_values(habitat.provenance),
            )
        )

    def get_habitat(self, habitat_id: UUID) -> Habitat | None:
        model = self._session.get(HabitatModel, str(habitat_id))
        return self._habitat_contract(model) if model else None

    def list_habitats(self, location_id: UUID) -> tuple[Habitat, ...]:
        models = self._session.scalars(
            select(HabitatModel)
            .where(HabitatModel.location_id == str(location_id))
            .order_by(HabitatModel.habitat_id)
        ).all()
        return tuple(self._habitat_contract(model) for model in models)

    def create_population(self, population: Population) -> None:
        self._session.add(
            PopulationModel(
                population_id=str(population.population_id),
                world_id=str(population.world_id),
                species_id=str(population.species_id),
                location_id=str(population.location_id),
                name=population.name,
                cohorts=[
                    cohort.model_dump(mode="json") for cohort in population.cohorts
                ],
                aggregate_by_default=population.aggregate_by_default,
                resource_links=list(population.resource_links),
                **self._provenance_values(population.provenance),
            )
        )

    def get_population(self, population_id: UUID) -> Population | None:
        model = self._session.get(PopulationModel, str(population_id))
        return self._population_contract(model) if model else None

    def list_populations(
        self, world_id: UUID, *, location_id: UUID | None = None
    ) -> tuple[Population, ...]:
        statement = select(PopulationModel).where(
            PopulationModel.world_id == str(world_id)
        )
        if location_id is not None:
            statement = statement.where(
                PopulationModel.location_id == str(location_id)
            )
        models = self._session.scalars(
            statement.order_by(PopulationModel.population_id)
        ).all()
        return tuple(self._population_contract(model) for model in models)

    def save_population(
        self, population: Population, expected_version: int | None = None
    ) -> None:
        model = self._session.get(PopulationModel, str(population.population_id))
        if model is None:
            raise KeyError(f"Unknown population {population.population_id}")
        self._check_expected_version(model, expected_version)
        model.cohorts = [
            cohort.model_dump(mode="json") for cohort in population.cohorts
        ]
        model.aggregate_by_default = population.aggregate_by_default
        model.resource_links = list(population.resource_links)
        self._save_provenance(model, population.provenance)

    def create_ecological_process(self, process: EcologicalProcess) -> None:
        self._session.add(
            EcologicalProcessModel(
                process_id=str(process.process_id),
                world_id=str(process.world_id),
                location_id=str(process.location_id),
                process_type=process.process_type,
                measures={
                    key: str(value) for key, value in process.measures.items()
                },
                population_links=[str(item) for item in process.population_links],
                resource_links=list(process.resource_links),
                status=process.status,
                **self._provenance_values(process.provenance),
            )
        )

    def get_ecological_process(
        self, process_id: UUID
    ) -> EcologicalProcess | None:
        model = self._session.get(EcologicalProcessModel, str(process_id))
        return self._ecological_process_contract(model) if model else None

    def save_ecological_process(
        self, process: EcologicalProcess, expected_version: int | None = None
    ) -> None:
        model = self._session.get(EcologicalProcessModel, str(process.process_id))
        if model is None:
            raise KeyError(f"Unknown ecological process {process.process_id}")
        self._check_expected_version(model, expected_version)
        model.measures = {key: str(value) for key, value in process.measures.items()}
        model.population_links = [str(item) for item in process.population_links]
        model.resource_links = list(process.resource_links)
        model.status = process.status
        self._save_provenance(model, process.provenance)

    def create_health_state(self, state: HealthState) -> None:
        self._session.add(
            HealthStateModel(
                state_id=str(state.state_id),
                character_id=str(state.character_id),
                species_id=str(state.species_id) if state.species_id else None,
                physical_integrity=state.physical_integrity,
                consciousness=state.consciousness,
                ability_to_act=state.ability_to_act,
                ability_to_fight=state.ability_to_fight,
                conditions=[
                    condition.model_dump(mode="json") for condition in state.conditions
                ],
                **self._provenance_values(state.provenance),
            )
        )

    def get_health_state(self, character_id: UUID) -> HealthState | None:
        model = self._session.scalar(
            select(HealthStateModel).where(
                HealthStateModel.character_id == str(character_id)
            )
        )
        return self._health_state_contract(model) if model else None

    def save_health_state(
        self, state: HealthState, expected_version: int | None = None
    ) -> None:
        model = self._session.get(HealthStateModel, str(state.state_id))
        if model is None:
            raise KeyError(f"Unknown health state {state.state_id}")
        self._check_expected_version(model, expected_version)
        model.physical_integrity = state.physical_integrity
        model.consciousness = state.consciousness
        model.ability_to_act = state.ability_to_act
        model.ability_to_fight = state.ability_to_fight
        model.conditions = [
            condition.model_dump(mode="json") for condition in state.conditions
        ]
        self._save_provenance(model, state.provenance)

    def create_knowledge_artifact(self, artifact: KnowledgeArtifact) -> None:
        self._session.add(
            KnowledgeArtifactModel(
                artifact_id=str(artifact.artifact_id),
                world_id=str(artifact.world_id),
                state=artifact.state.value,
                payload=artifact.model_dump(mode="json"),
            )
        )

    def create_culture_definition(self, culture: CultureDefinition) -> None:
        self._session.add(
            CultureDefinitionModel(
                culture_id=str(culture.culture_id),
                world_id=str(culture.world_id),
                payload=culture.model_dump(mode="json"),
            )
        )

    def get_culture_definition(
        self, culture_id: UUID
    ) -> CultureDefinition | None:
        model = self._session.get(CultureDefinitionModel, str(culture_id))
        return CultureDefinition.model_validate(model.payload) if model else None

    def create_social_group(self, group: SocialGroup) -> None:
        self._session.add(
            SocialGroupModel(
                group_id=str(group.group_id),
                world_id=str(group.world_id),
                semantic_category=group.semantic_category,
                payload=group.model_dump(mode="json"),
            )
        )

    def get_social_group(self, group_id: UUID) -> SocialGroup | None:
        model = self._session.get(SocialGroupModel, str(group_id))
        return SocialGroup.model_validate(model.payload) if model else None

    def create_individual_cultural_affiliation(
        self, affiliation: IndividualCulturalAffiliation
    ) -> None:
        self._session.add(
            IndividualCulturalAffiliationModel(
                affiliation_id=str(affiliation.affiliation_id),
                character_id=str(affiliation.character_id),
                target_type=affiliation.target_type.value,
                target_id=str(affiliation.target_id),
                visibility=affiliation.visibility.value,
                effective_from=affiliation.effective_from,
                effective_until=affiliation.effective_until,
                payload=affiliation.model_dump(mode="json"),
            )
        )

    def list_individual_cultural_affiliations(
        self, character_id: UUID
    ) -> tuple[IndividualCulturalAffiliation, ...]:
        models = self._session.scalars(
            select(IndividualCulturalAffiliationModel)
            .where(
                IndividualCulturalAffiliationModel.character_id
                == str(character_id)
            )
            .order_by(
                IndividualCulturalAffiliationModel.effective_from,
                IndividualCulturalAffiliationModel.affiliation_id,
            )
        ).all()
        return tuple(
            IndividualCulturalAffiliation.model_validate(model.payload)
            for model in models
        )

    def create_cultural_change_record(self, record: CulturalChangeRecord) -> None:
        self._session.add(
            CulturalChangeRecordModel(
                record_id=str(record.record_id),
                world_id=str(record.world_id),
                target_type=record.target_type.value,
                target_id=str(record.target_id),
                source_event_id=str(record.source_event_id),
                occurred_at=record.occurred_at,
                cause_tags=[tag.value for tag in record.cause_tags],
                payload=record.model_dump(mode="json"),
            )
        )

    def get_cultural_change_record(
        self, record_id: UUID
    ) -> CulturalChangeRecord | None:
        model = self._session.get(CulturalChangeRecordModel, str(record_id))
        return CulturalChangeRecord.model_validate(model.payload) if model else None

    def list_cultural_change_records(
        self,
        target_type: CulturalAffiliationTargetType,
        target_id: UUID,
    ) -> tuple[CulturalChangeRecord, ...]:
        models = self._session.scalars(
            select(CulturalChangeRecordModel)
            .where(
                CulturalChangeRecordModel.target_type == target_type.value,
                CulturalChangeRecordModel.target_id == str(target_id),
            )
            .order_by(
                CulturalChangeRecordModel.occurred_at,
                CulturalChangeRecordModel.record_id,
            )
        ).all()
        return tuple(
            CulturalChangeRecord.model_validate(model.payload) for model in models
        )

    def get_knowledge_artifact(
        self, artifact_id: UUID
    ) -> KnowledgeArtifact | None:
        model = self._session.get(KnowledgeArtifactModel, str(artifact_id))
        return KnowledgeArtifact.model_validate(model.payload) if model else None

    def save_knowledge_artifact(
        self, artifact: KnowledgeArtifact, expected_version: int | None = None
    ) -> None:
        model = self._session.get(KnowledgeArtifactModel, str(artifact.artifact_id))
        if model is None:
            raise KeyError(f"Unknown knowledge artifact {artifact.artifact_id}")
        stored = KnowledgeArtifact.model_validate(model.payload)
        if expected_version is not None and stored.provenance.version != expected_version:
            raise StaleWorldStateError("Knowledge artifact changed during simulation")
        model.state = artifact.state.value
        model.payload = artifact.model_dump(mode="json")

    def create_technology(self, technology: Technology) -> None:
        self._session.add(
            TechnologyModel(
                technology_id=str(technology.technology_id),
                world_id=str(technology.world_id),
                state=technology.state.value,
                payload=technology.model_dump(mode="json"),
            )
        )

    def get_technology(self, technology_id: UUID) -> Technology | None:
        model = self._session.get(TechnologyModel, str(technology_id))
        return Technology.model_validate(model.payload) if model else None

    def save_technology(
        self, technology: Technology, expected_version: int | None = None
    ) -> None:
        model = self._session.get(TechnologyModel, str(technology.technology_id))
        if model is None:
            raise KeyError(f"Unknown technology {technology.technology_id}")
        stored = Technology.model_validate(model.payload)
        if expected_version is not None and stored.provenance.version != expected_version:
            raise StaleWorldStateError("Technology changed during simulation")
        model.state = technology.state.value
        model.payload = technology.model_dump(mode="json")

    def create_knowledge_lifecycle_record(
        self, record: KnowledgeLifecycleRecord
    ) -> None:
        self._session.add(
            KnowledgeLifecycleRecordModel(
                record_id=str(record.record_id),
                entity_id=str(record.entity_id),
                actor_id=str(record.actor_id) if record.actor_id else None,
                state=record.state.value,
                payload=record.model_dump(mode="json"),
            )
        )

    def create_language(self, language: Language) -> None:
        self._session.add(
            LanguageModel(
                language_id=str(language.language_id),
                world_id=str(language.world_id),
                payload=language.model_dump(mode="json"),
            )
        )

    def get_language(self, language_id: UUID) -> Language | None:
        model = self._session.get(LanguageModel, str(language_id))
        return Language.model_validate(model.payload) if model else None

    def create_dialect(self, dialect: Dialect) -> None:
        self._session.add(
            DialectModel(
                dialect_id=str(dialect.dialect_id),
                language_id=str(dialect.language_id),
                payload=dialect.model_dump(mode="json"),
            )
        )

    def create_writing_system(self, writing_system: WritingSystem) -> None:
        self._session.add(
            WritingSystemModel(
                writing_system_id=str(writing_system.writing_system_id),
                world_id=str(writing_system.world_id),
                payload=writing_system.model_dump(mode="json"),
            )
        )

    def create_character_language_proficiency(
        self, proficiency: CharacterLanguageProficiency
    ) -> None:
        self._session.add(
            CharacterLanguageProficiencyModel(
                proficiency_id=str(proficiency.proficiency_id),
                character_id=str(proficiency.character_id),
                language_id=str(proficiency.language_id),
                payload=proficiency.model_dump(mode="json"),
            )
        )

    def get_character_language_proficiency(
        self, character_id: UUID, language_id: UUID
    ) -> CharacterLanguageProficiency | None:
        model = self._session.scalar(
            select(CharacterLanguageProficiencyModel).where(
                CharacterLanguageProficiencyModel.character_id == str(character_id),
                CharacterLanguageProficiencyModel.language_id == str(language_id),
            )
        )
        return (
            CharacterLanguageProficiency.model_validate(model.payload)
            if model
            else None
        )

    def create_education_program(self, program: EducationProgram) -> None:
        self._session.add(
            EducationProgramModel(
                program_id=str(program.program_id),
                world_id=str(program.world_id),
                organization_id=(
                    str(program.organization_id) if program.organization_id else None
                ),
                payload=program.model_dump(mode="json"),
            )
        )

    def get_education_program(self, program_id: UUID) -> EducationProgram | None:
        model = self._session.get(EducationProgramModel, str(program_id))
        return EducationProgram.model_validate(model.payload) if model else None

    def create_education_enrollment(
        self, enrollment: EducationEnrollment
    ) -> None:
        self._session.add(
            EducationEnrollmentModel(
                enrollment_id=str(enrollment.enrollment_id),
                program_id=str(enrollment.program_id),
                character_id=str(enrollment.character_id),
                status=enrollment.status.value,
                payload=enrollment.model_dump(mode="json"),
            )
        )

    def get_education_enrollment(
        self, enrollment_id: UUID
    ) -> EducationEnrollment | None:
        model = self._session.get(EducationEnrollmentModel, str(enrollment_id))
        return EducationEnrollment.model_validate(model.payload) if model else None

    def create_learning_opportunity(
        self, opportunity: LearningOpportunity
    ) -> None:
        self._session.add(
            LearningOpportunityModel(
                opportunity_id=str(opportunity.opportunity_id),
                program_id=(
                    str(opportunity.program_id) if opportunity.program_id else None
                ),
                participant_character_id=str(opportunity.participant_character_id),
                payload=opportunity.model_dump(mode="json"),
            )
        )

    def get_learning_opportunity(
        self, opportunity_id: UUID
    ) -> LearningOpportunity | None:
        model = self._session.get(LearningOpportunityModel, str(opportunity_id))
        return LearningOpportunity.model_validate(model.payload) if model else None

    def create_assessment_outcome(self, outcome: AssessmentOutcome) -> None:
        self._session.add(
            AssessmentOutcomeModel(
                outcome_id=str(outcome.outcome_id),
                enrollment_id=str(outcome.enrollment_id),
                character_id=str(outcome.character_id),
                source_event_id=str(outcome.source_event_id),
                payload=outcome.model_dump(mode="json"),
            )
        )

    def create_religion_tradition(
        self, tradition: ReligionTradition
    ) -> None:
        self._session.add(
            ReligionTraditionModel(
                tradition_id=str(tradition.tradition_id),
                world_id=str(tradition.world_id),
                organization_id=(
                    str(tradition.organization_id)
                    if tradition.organization_id
                    else None
                ),
                payload=tradition.model_dump(mode="json"),
            )
        )

    def get_religion_tradition(
        self, tradition_id: UUID
    ) -> ReligionTradition | None:
        model = self._session.get(ReligionTraditionModel, str(tradition_id))
        return ReligionTradition.model_validate(model.payload) if model else None

    def create_individual_belief(self, belief: IndividualBeliefRecord) -> None:
        self._session.add(
            IndividualBeliefRecordModel(
                belief_id=str(belief.belief_id),
                character_id=str(belief.character_id),
                tradition_id=(
                    str(belief.tradition_id) if belief.tradition_id else None
                ),
                payload=belief.model_dump(mode="json"),
            )
        )

    def create_ritual_completion(self, completion: RitualCompletion) -> None:
        self._session.add(
            RitualCompletionModel(
                completion_id=str(completion.completion_id),
                tradition_id=str(completion.tradition_id),
                actor_id=str(completion.actor_id),
                source_event_id=str(completion.source_event_id),
                payload=completion.model_dump(mode="json"),
            )
        )

    def create_metaphysical_truth(self, truth: MetaphysicalTruth) -> None:
        self._session.add(
            MetaphysicalTruthModel(
                truth_id=str(truth.truth_id),
                world_id=str(truth.world_id),
                disclosure_class=truth.disclosure_class,
                payload=truth.model_dump(mode="json"),
            )
        )

    def create_normative_system(self, system: NormativeSystem) -> None:
        self._session.add(
            NormativeSystemModel(
                system_id=str(system.system_id),
                world_id=str(system.world_id),
                kind=system.kind.value,
                payload=system.model_dump(mode="json"),
            )
        )

    def get_normative_system(self, system_id: UUID) -> NormativeSystem | None:
        model = self._session.get(NormativeSystemModel, str(system_id))
        return NormativeSystem.model_validate(model.payload) if model else None

    def create_normative_rule(self, rule: NormativeRule) -> None:
        self._session.add(NormativeRuleModel(rule_id=str(rule.rule_id), system_id=str(rule.system_id), payload=rule.model_dump(mode="json")))

    def get_normative_rule(self, rule_id: UUID) -> NormativeRule | None:
        model = self._session.get(NormativeRuleModel, str(rule_id))
        return NormativeRule.model_validate(model.payload) if model else None

    def create_offense(self, offense: Offense) -> None:
        self._session.add(OffenseModel(offense_id=str(offense.offense_id), system_id=str(offense.system_id), rule_id=str(offense.rule_id), payload=offense.model_dump(mode="json")))

    def create_legal_case(self, case: LegalCase) -> None:
        self._session.add(LegalCaseModel(case_id=str(case.case_id), world_id=str(case.world_id), system_id=str(case.system_id), status=case.status.value, payload=case.model_dump(mode="json")))

    def get_legal_case(self, case_id: UUID) -> LegalCase | None:
        model = self._session.get(LegalCaseModel, str(case_id))
        return LegalCase.model_validate(model.payload) if model else None

    def save_legal_case(self, case: LegalCase, expected_version: int) -> None:
        model = self._session.get(LegalCaseModel, str(case.case_id))
        model = self._save_json_versioned(model, case, expected_version, "Legal case")
        model.status = case.status.value

    def create_investigation(self, investigation: Investigation) -> None:
        self._session.add(InvestigationModel(investigation_id=str(investigation.investigation_id), case_id=str(investigation.case_id), organization_id=str(investigation.responsible_organization_id), status=investigation.status.value, payload=investigation.model_dump(mode="json")))

    def get_investigation(self, investigation_id: UUID) -> Investigation | None:
        model = self._session.get(InvestigationModel, str(investigation_id))
        return Investigation.model_validate(model.payload) if model else None

    def save_investigation(self, investigation: Investigation, expected_version: int) -> None:
        model = self._session.get(InvestigationModel, str(investigation.investigation_id))
        model = self._save_json_versioned(model, investigation, expected_version, "Investigation")
        model.status = investigation.status.value

    def create_evidence(self, evidence: EvidenceRecord) -> None:
        self._session.add(EvidenceRecordModel(evidence_id=str(evidence.evidence_id), investigation_id=str(evidence.investigation_id), case_id=str(evidence.case_id), visibility=evidence.visibility.value, payload=evidence.model_dump(mode="json")))

    def list_visible_evidence(self, character_id: UUID, *, as_of: datetime) -> tuple[EvidenceRecord, ...]:
        models = self._session.scalars(select(EvidenceRecordModel).order_by(EvidenceRecordModel.evidence_id)).all()
        result: list[EvidenceRecord] = []
        for model in models:
            evidence = EvidenceRecord.model_validate(model.payload)
            if evidence.acquired_at <= as_of and (
                evidence.visibility.value == "public"
                or character_id in evidence.permitted_character_ids
            ):
                result.append(evidence)
        return tuple(result)

    def create_legal_proceeding(self, proceeding: LegalProceeding) -> None:
        self._session.add(LegalProceedingModel(proceeding_id=str(proceeding.proceeding_id), case_id=str(proceeding.case_id), status=proceeding.status.value, payload=proceeding.model_dump(mode="json")))

    def get_legal_proceeding(self, proceeding_id: UUID) -> LegalProceeding | None:
        model = self._session.get(LegalProceedingModel, str(proceeding_id))
        return LegalProceeding.model_validate(model.payload) if model else None

    def save_legal_proceeding(self, proceeding: LegalProceeding, expected_version: int) -> None:
        model = self._session.get(LegalProceedingModel, str(proceeding.proceeding_id))
        model = self._save_json_versioned(model, proceeding, expected_version, "Legal proceeding")
        model.status = proceeding.status.value

    def create_sanction(self, sanction: Sanction) -> None:
        self._session.add(SanctionModel(sanction_id=str(sanction.sanction_id), case_id=str(sanction.case_id), proceeding_id=str(sanction.proceeding_id), status=sanction.status.value, payload=sanction.model_dump(mode="json")))

    def create_appeal(self, appeal: Appeal) -> None:
        self._session.add(AppealModel(appeal_id=str(appeal.appeal_id), case_id=str(appeal.case_id), proceeding_id=str(appeal.proceeding_id), payload=appeal.model_dump(mode="json")))

    def create_organization_relation(self, relation: OrganizationRelation) -> None:
        self._session.add(OrganizationRelationModel(relation_id=str(relation.relation_id), world_id=str(relation.world_id), source_organization_id=str(relation.source_organization_id), target_organization_id=str(relation.target_organization_id), payload=relation.model_dump(mode="json")))

    def create_treaty(self, treaty: Treaty) -> None:
        self._session.add(TreatyModel(treaty_id=str(treaty.treaty_id), world_id=str(treaty.world_id), status=treaty.status.value, payload=treaty.model_dump(mode="json")))

    def get_treaty(self, treaty_id: UUID) -> Treaty | None:
        model = self._session.get(TreatyModel, str(treaty_id))
        return Treaty.model_validate(model.payload) if model else None

    def save_treaty(self, treaty: Treaty, expected_version: int) -> None:
        model = self._session.get(TreatyModel, str(treaty.treaty_id))
        model = self._save_json_versioned(model, treaty, expected_version, "Treaty")
        model.status = treaty.status.value

    def create_diplomatic_action(self, action: DiplomaticAction) -> None:
        self._session.add(DiplomaticActionModel(action_id=str(action.action_id), world_id=str(action.world_id), source_organization_id=str(action.source_organization_id), target_organization_id=str(action.target_organization_id), status=action.status.value, payload=action.model_dump(mode="json")))

    def create_strategic_conflict(self, conflict: StrategicConflict) -> None:
        self._session.add(StrategicConflictModel(conflict_id=str(conflict.conflict_id), world_id=str(conflict.world_id), escalation_stage=conflict.escalation_stage, status=conflict.status, payload=conflict.model_dump(mode="json")))

    def get_strategic_conflict(self, conflict_id: UUID) -> StrategicConflict | None:
        model = self._session.get(StrategicConflictModel, str(conflict_id))
        return StrategicConflict.model_validate(model.payload) if model else None

    def save_strategic_conflict(self, conflict: StrategicConflict, expected_version: int) -> None:
        model = self._session.get(StrategicConflictModel, str(conflict.conflict_id))
        model = self._save_json_versioned(model, conflict, expected_version, "Strategic conflict")
        model.escalation_stage = conflict.escalation_stage
        model.status = conflict.status

    def create_security_threat(self, threat: SecurityThreat) -> None:
        self._session.add(SecurityThreatModel(threat_id=str(threat.threat_id), world_id=str(threat.world_id), status=threat.status.value, payload=threat.model_dump(mode="json")))

    def get_security_threat(self, threat_id: UUID) -> SecurityThreat | None:
        model = self._session.get(SecurityThreatModel, str(threat_id))
        return SecurityThreat.model_validate(model.payload) if model else None

    def save_security_threat(self, threat: SecurityThreat, expected_version: int) -> None:
        model = self._session.get(SecurityThreatModel, str(threat.threat_id))
        model = self._save_json_versioned(model, threat, expected_version, "Security threat")
        model.status = threat.status.value

    def create_security_incident(self, incident: SecurityIncident) -> None:
        self._session.add(SecurityIncidentModel(incident_id=str(incident.incident_id), threat_id=str(incident.threat_id), payload=incident.model_dump(mode="json")))

    def get_security_incident(self, incident_id: UUID) -> SecurityIncident | None:
        model = self._session.get(SecurityIncidentModel, str(incident_id))
        return SecurityIncident.model_validate(model.payload) if model else None

    def create_intelligence_operation(self, operation: IntelligenceOperation) -> None:
        self._session.add(IntelligenceOperationModel(operation_id=str(operation.operation_id), world_id=str(operation.world_id), organization_id=str(operation.organization_id), status=operation.status.value, payload=operation.model_dump(mode="json")))

    def get_intelligence_operation(self, operation_id: UUID) -> IntelligenceOperation | None:
        model = self._session.get(IntelligenceOperationModel, str(operation_id))
        return IntelligenceOperation.model_validate(model.payload) if model else None

    def save_intelligence_operation(self, operation: IntelligenceOperation, expected_version: int) -> None:
        model = self._session.get(IntelligenceOperationModel, str(operation.operation_id))
        model = self._save_json_versioned(model, operation, expected_version, "Intelligence operation")
        model.status = operation.status.value

    def create_security_resolution(self, resolution: SecurityResolution) -> None:
        self._session.add(SecurityResolutionModel(resolution_id=str(resolution.resolution_id), threat_id=str(resolution.threat_id), source_event_id=str(resolution.source_event_id), payload=resolution.model_dump(mode="json")))

    @staticmethod
    def _save_json_versioned(model, entity, expected_version: int, label: str):
        if model is None:
            raise KeyError(f"Unknown {label.lower()}")
        if type(entity).model_validate(model.payload).provenance.version != expected_version:
            raise StaleWorldStateError(f"{label} changed during simulation")
        model.payload = entity.model_dump(mode="json")
        return model

    @staticmethod
    def _check_expected_version(model, expected_version: int | None) -> None:
        if expected_version is not None and model.version != expected_version:
            raise StaleWorldStateError("Natural system state changed during simulation")

    @staticmethod
    def _save_provenance(model, provenance: RecordProvenance) -> None:
        model.source_type = provenance.source_type
        model.source_id = provenance.source_id
        model.origin_event_id = (
            str(provenance.origin_event_id)
            if provenance.origin_event_id is not None
            else None
        )
        model.version = provenance.version
        model.created_at = provenance.created_at
        model.updated_at = provenance.updated_at

    def create_public_channel(self, channel: PublicChannel) -> None:
        self._session.add(
            PublicChannelModel(
                channel_id=str(channel.channel_id),
                world_id=str(channel.world_id),
                payload=channel.model_dump(mode="json"),
            )
        )

    def get_public_channel(self, channel_id: UUID) -> PublicChannel | None:
        model = self._session.get(PublicChannelModel, str(channel_id))
        return PublicChannel.model_validate(model.payload) if model else None

    def create_public_information(
        self,
        publication: PublicInformation,
    ) -> None:
        self._session.add(
            PublicInformationModel(
                publication_id=str(publication.publication_id),
                world_id=str(publication.world_id),
                channel_id=str(publication.channel_id),
                published_at=publication.published_at,
                payload=publication.model_dump(mode="json"),
            )
        )

    def create_collective_reception(
        self,
        reception: CollectiveReception,
    ) -> None:
        self._session.add(
            CollectiveReceptionModel(
                reception_id=str(reception.reception_id),
                publication_id=str(reception.publication_id),
                population_id=str(reception.population_id),
                received_at=reception.received_at,
                payload=reception.model_dump(mode="json"),
            )
        )

    def create_creative_work(self, work: CreativeWork) -> None:
        self._session.add(
            CreativeWorkModel(
                work_id=str(work.work_id),
                world_id=str(work.world_id),
                payload=work.model_dump(mode="json"),
            )
        )

    def create_leisure_routine(self, routine: LeisureRoutine) -> None:
        self._session.add(
            LeisureRoutineModel(
                routine_id=str(routine.routine_id),
                actor_type=routine.actor.actor_type.value,
                actor_id=str(routine.actor.actor_id),
                payload=routine.model_dump(mode="json"),
            )
        )

    def create_visual_identity(self, identity: VisualIdentity) -> None:
        self._session.add(
            VisualIdentityModel(
                identity_id=str(identity.identity_id),
                actor_type=identity.subject.actor_type.value,
                actor_id=str(identity.subject.actor_id),
                payload=identity.model_dump(mode="json"),
            )
        )

    def create_sonic_identity(self, identity: SonicIdentity) -> None:
        self._session.add(
            SonicIdentityModel(
                identity_id=str(identity.identity_id),
                actor_type=identity.subject.actor_type.value,
                actor_id=str(identity.subject.actor_id),
                payload=identity.model_dump(mode="json"),
            )
        )

    def create_generated_asset(self, asset: GeneratedAsset) -> None:
        self._session.add(
            GeneratedAssetModel(
                asset_id=str(asset.asset_id),
                actor_type=asset.subject.actor_type.value,
                actor_id=str(asset.subject.actor_id),
                kind=asset.kind.value,
                canonical_identity_id=str(asset.canonical_identity_id),
                filesystem_reference=asset.filesystem_reference,
                generated_at=asset.generated_at,
                payload=asset.model_dump(mode="json"),
            )
        )

    def create_canonical_proposal(
        self,
        proposal: CanonicalProposal,
    ) -> None:
        self._session.add(
            CanonicalProposalModel(
                proposal_id=str(proposal.proposal_id),
                world_id=str(proposal.world_id),
                entity_type=proposal.entity_type,
                entity_id=str(proposal.entity_id) if proposal.entity_id else None,
                status=proposal.status.value,
                payload=proposal.model_dump(mode="json"),
            )
        )

    def get_canonical_proposal(
        self,
        proposal_id: UUID,
    ) -> CanonicalProposal | None:
        model = self._session.get(CanonicalProposalModel, str(proposal_id))
        return CanonicalProposal.model_validate(model.payload) if model else None

    def create_canonical_record(self, record: CanonicalRecord) -> None:
        self._session.add(
            CanonicalRecordModel(
                record_id=str(record.record_id),
                proposal_id=str(record.proposal_id),
                world_id=str(record.world_id),
                entity_type=record.entity_type,
                entity_id=str(record.entity_id) if record.entity_id else None,
                level=int(record.level),
                revision=record.revision,
                status=record.status.value,
                supersedes_record_id=(
                    str(record.supersedes_record_id)
                    if record.supersedes_record_id
                    else None
                ),
                payload=record.model_dump(mode="json"),
            )
        )

    def get_canonical_record(self, record_id: UUID) -> CanonicalRecord | None:
        model = self._session.get(CanonicalRecordModel, str(record_id))
        return CanonicalRecord.model_validate(model.payload) if model else None

    def list_canonical_records(
        self,
        *,
        world_id: UUID,
        entity_type: str | None = None,
        entity_id: UUID | None = None,
    ) -> tuple[CanonicalRecord, ...]:
        statement = select(CanonicalRecordModel).where(
            CanonicalRecordModel.world_id == str(world_id)
        )
        if entity_type is not None:
            statement = statement.where(
                CanonicalRecordModel.entity_type == entity_type
            )
        if entity_id is not None:
            statement = statement.where(
                CanonicalRecordModel.entity_id == str(entity_id)
            )
        models = self._session.scalars(
            statement.order_by(CanonicalRecordModel.revision)
        ).all()
        return tuple(
            CanonicalRecord.model_validate(model.payload) for model in models
        )

    def get_event(self, event_id: UUID) -> EventEnvelope | None:
        model = self._session.get(EventLedgerModel, str(event_id))
        if model is None:
            return None
        return EventEnvelope(
            event_id=UUID(model.event_id),
            world_id=UUID(model.world_id),
            timeline_id=UUID(model.timeline_id),
            occurred_at=model.occurred_at,
            recorded_at=model.recorded_at,
            sequence=model.sequence,
            event_type=model.event_type,
            source_type=model.source_type,
            source_id=model.source_id,
            caused_by=tuple(UUID(value) for value in model.caused_by),
            priority=model.priority,
            payload_version=model.payload_version,
            payload=model.payload,
            interruption_class=InterruptionClass(model.interruption_class),
        )

    def create_character_sheet(self, sheet: CharacterSheet) -> None:
        self._session.add(
            CharacterSheetModel(
                character_id=str(sheet.character_id),
                world_id=str(sheet.world_id),
                ruleset_id=sheet.ruleset_id,
                version=sheet.version,
                payload=sheet.model_dump(mode="json"),
            )
        )

    def get_character_sheet(self, character_id: UUID) -> CharacterSheet | None:
        model = self._session.get(CharacterSheetModel, str(character_id))
        return CharacterSheet.model_validate(model.payload) if model else None

    def save_character_sheet(
        self, sheet: CharacterSheet, expected_version: int
    ) -> None:
        model = self._session.get(CharacterSheetModel, str(sheet.character_id))
        if model is None:
            raise KeyError(f"Unknown character sheet {sheet.character_id}")
        if model.version != expected_version:
            raise StaleWorldStateError("Character sheet changed during progression")
        model.world_id = str(sheet.world_id)
        model.ruleset_id = sheet.ruleset_id
        model.version = sheet.version
        model.payload = sheet.model_dump(mode="json")

    def create_progression_evidence(
        self, evidence: CharacterProgressionEvidence
    ) -> None:
        self._session.add(
            CharacterProgressionEvidenceModel(
                evidence_id=str(evidence.evidence_id),
                character_id=str(evidence.character_id),
                world_id=str(evidence.world_id),
                payload=evidence.model_dump(mode="json"),
            )
        )

    def get_progression_evidence(
        self, evidence_id: UUID
    ) -> CharacterProgressionEvidence | None:
        model = self._session.get(
            CharacterProgressionEvidenceModel, str(evidence_id)
        )
        return CharacterProgressionEvidence.model_validate(model.payload) if model else None

    def create_progression_proposal(
        self, proposal: CharacterProgressionProposal
    ) -> None:
        self._session.add(
            CharacterProgressionProposalModel(
                proposal_id=str(proposal.proposal_id),
                request_id=str(proposal.request_id),
                character_id=str(proposal.character_id),
                world_id=str(proposal.world_id),
                payload=proposal.model_dump(mode="json"),
            )
        )

    def get_progression_proposal(
        self, proposal_id: UUID
    ) -> CharacterProgressionProposal | None:
        model = self._session.get(
            CharacterProgressionProposalModel, str(proposal_id)
        )
        return CharacterProgressionProposal.model_validate(model.payload) if model else None

    def get_progression_proposal_by_request(
        self, request_id: UUID
    ) -> CharacterProgressionProposal | None:
        model = self._session.scalar(
            select(CharacterProgressionProposalModel).where(
                CharacterProgressionProposalModel.request_id == str(request_id)
            )
        )
        return CharacterProgressionProposal.model_validate(model.payload) if model else None

    def create_progression_validation(
        self, validation: CharacterProgressionValidation
    ) -> None:
        self._session.add(
            CharacterProgressionValidationModel(
                validation_id=str(validation.validation_id),
                proposal_id=str(validation.proposal_id),
                payload=validation.model_dump(mode="json"),
            )
        )

    def list_progression_validations(
        self, proposal_id: UUID
    ) -> tuple[CharacterProgressionValidation, ...]:
        models = self._session.scalars(
            select(CharacterProgressionValidationModel).where(
                CharacterProgressionValidationModel.proposal_id == str(proposal_id)
            )
        ).all()
        return tuple(
            CharacterProgressionValidation.model_validate(model.payload)
            for model in models
        )

    def create_progression_application(
        self, application: CharacterProgressionApplication
    ) -> None:
        self._session.add(
            CharacterProgressionApplicationModel(
                application_id=str(application.application_id),
                proposal_id=str(application.proposal_id),
                character_id=str(application.character_id),
                payload=application.model_dump(mode="json"),
            )
        )

    def get_progression_application(
        self, proposal_id: UUID
    ) -> CharacterProgressionApplication | None:
        model = self._session.scalar(
            select(CharacterProgressionApplicationModel).where(
                CharacterProgressionApplicationModel.proposal_id == str(proposal_id)
            )
        )
        return CharacterProgressionApplication.model_validate(model.payload) if model else None

    def list_progression_applications(
        self, character_id: UUID
    ) -> tuple[CharacterProgressionApplication, ...]:
        models = self._session.scalars(
            select(CharacterProgressionApplicationModel)
            .where(
                CharacterProgressionApplicationModel.character_id
                == str(character_id)
            )
            .order_by(CharacterProgressionApplicationModel.application_id)
        ).all()
        return tuple(
            CharacterProgressionApplication.model_validate(model.payload)
            for model in models
        )

    @staticmethod
    def _species_contract(model: SpeciesModel) -> Species:
        return Species(
            species_id=UUID(model.species_id),
            world_id=UUID(model.world_id),
            name=model.name,
            organism_kind=OrganismKind(model.organism_kind),
            anatomy=model.anatomy,
            physiology=model.physiology,
            reproduction_model=model.reproduction_model,
            nutrition=model.nutrition,
            habitat=tuple(model.habitat),
            senses=tuple(model.senses),
            adaptations=tuple(model.adaptations),
            lifecycle_stages=tuple(
                LifecycleStage.model_validate(item) for item in model.lifecycle_stages
            ),
            resource_links=tuple(model.resource_links),
            provenance=SqlAlchemySimulationRepository._provenance_contract(model),
        )

    @staticmethod
    def _habitat_contract(model: HabitatModel) -> Habitat:
        return Habitat(
            habitat_id=UUID(model.habitat_id),
            world_id=UUID(model.world_id),
            location_id=UUID(model.location_id),
            name=model.name,
            habitat_type=model.habitat_type,
            habitability=model.habitability,
            species_ids=tuple(UUID(item) for item in model.species_ids),
            resources=tuple(model.resources),
            resource_links=tuple(model.resource_links),
            characteristics=model.characteristics,
            provenance=SqlAlchemySimulationRepository._provenance_contract(model),
        )

    @staticmethod
    def _population_contract(model: PopulationModel) -> Population:
        return Population(
            population_id=UUID(model.population_id),
            world_id=UUID(model.world_id),
            species_id=UUID(model.species_id),
            location_id=UUID(model.location_id),
            name=model.name,
            cohorts=tuple(
                PopulationCohort.model_validate(item) for item in model.cohorts
            ),
            aggregate_by_default=model.aggregate_by_default,
            resource_links=tuple(model.resource_links),
            provenance=SqlAlchemySimulationRepository._provenance_contract(model),
        )

    @staticmethod
    def _ecological_process_contract(
        model: EcologicalProcessModel,
    ) -> EcologicalProcess:
        return EcologicalProcess(
            process_id=UUID(model.process_id),
            world_id=UUID(model.world_id),
            location_id=UUID(model.location_id),
            process_type=model.process_type,
            measures={
                key: Decimal(value) for key, value in model.measures.items()
            },
            population_links=tuple(UUID(item) for item in model.population_links),
            resource_links=tuple(model.resource_links),
            status=model.status,
            provenance=SqlAlchemySimulationRepository._provenance_contract(model),
        )

    @staticmethod
    def _health_state_contract(model: HealthStateModel) -> HealthState:
        return HealthState(
            state_id=UUID(model.state_id),
            character_id=UUID(model.character_id),
            species_id=UUID(model.species_id) if model.species_id else None,
            physical_integrity=model.physical_integrity,
            consciousness=model.consciousness,
            ability_to_act=model.ability_to_act,
            ability_to_fight=model.ability_to_fight,
            conditions=tuple(
                HealthCondition.model_validate(item) for item in model.conditions
            ),
            provenance=SqlAlchemySimulationRepository._provenance_contract(model),
        )

    @staticmethod
    def _location_contract(model: LocationModel) -> Location:
        return Location(
            location_id=UUID(model.location_id),
            world_id=UUID(model.world_id),
            name=model.name,
            location_type=LocationType(model.location_type),
            parent_location_id=(
                UUID(model.parent_location_id)
                if model.parent_location_id is not None
                else None
            ),
            terrain=tuple(model.terrain),
            climate=tuple(model.climate),
            hydrology=tuple(model.hydrology),
            flora_fauna=tuple(model.flora_fauna),
            natural_resources=tuple(model.natural_resources),
            population_density=model.population_density,
            strategic_tags=tuple(model.strategic_tags),
            risk_tags=tuple(model.risk_tags),
            barrier_tags=tuple(model.barrier_tags),
            provenance=SqlAlchemySimulationRepository._provenance_contract(model),
        )

    @staticmethod
    def _territory_claim_contract(model: TerritoryClaimModel) -> TerritoryClaim:
        return TerritoryClaim(
            claim_id=UUID(model.claim_id),
            location_id=UUID(model.location_id),
            semantics=ClaimSemantics(model.semantics),
            owner=(
                ActorReference(
                    actor_type=ActorType(model.owner_actor_type),
                    actor_id=UUID(model.owner_actor_id),
                )
                if model.owner_actor_type is not None
                else None
            ),
            controller=(
                ActorReference(
                    actor_type=ActorType(model.controller_actor_type),
                    actor_id=UUID(model.controller_actor_id),
                )
                if model.controller_actor_type is not None
                else None
            ),
            status=ControlStatus(model.status),
            basis=model.basis,
            provenance=SqlAlchemySimulationRepository._provenance_contract(model),
        )

    @staticmethod
    def _transport_route_contract(model: TransportRouteModel) -> TransportRoute:
        return TransportRoute(
            route_id=UUID(model.route_id),
            world_id=UUID(model.world_id),
            name=model.name,
            start_location_id=UUID(model.start_location_id),
            end_location_id=UUID(model.end_location_id),
            modes=tuple(TransportMode(value) for value in model.modes),
            availability=model.availability,
            provenance=SqlAlchemySimulationRepository._provenance_contract(model),
        )

    @staticmethod
    def _infrastructure_node_contract(
        model: InfrastructureNodeModel,
    ) -> InfrastructureNode:
        return InfrastructureNode(
            node_id=UUID(model.node_id),
            world_id=UUID(model.world_id),
            location_id=UUID(model.location_id),
            name=model.name,
            node_type=model.node_type,
            availability=model.availability,
            capacity=model.capacity,
            safety_tags=tuple(model.safety_tags),
            risk_tags=tuple(model.risk_tags),
            provenance=SqlAlchemySimulationRepository._provenance_contract(model),
        )

    @staticmethod
    def _infrastructure_facility_contract(
        model: InfrastructureFacilityModel,
    ) -> InfrastructureFacility:
        return InfrastructureFacility(
            facility_id=UUID(model.facility_id),
            node_id=UUID(model.node_id),
            location_id=UUID(model.location_id),
            facility_type=model.facility_type,
            name=model.name,
            availability=model.availability,
            capacity=model.capacity,
            resource_consumption=tuple(model.resource_consumption),
            safety_tags=tuple(model.safety_tags),
            risk_tags=tuple(model.risk_tags),
            provenance=SqlAlchemySimulationRepository._provenance_contract(model),
        )

    @staticmethod
    def _route_segment_contract(
        model: TransportRouteSegmentModel,
    ) -> TransportRouteSegment:
        return TransportRouteSegment(
            segment_id=UUID(model.segment_id),
            route_id=UUID(model.route_id),
            sequence=model.sequence,
            start_location_id=UUID(model.start_location_id),
            end_location_id=UUID(model.end_location_id),
            physical_distance=Decimal(model.physical_distance),
            distance_unit=model.distance_unit,
            base_duration=timedelta(
                microseconds=model.base_duration_microseconds
            ),
            mode=TransportMode(model.mode),
            costs=tuple(ResourceCharge.model_validate(item) for item in model.costs),
            capacity=model.capacity,
            availability=model.availability,
            resource_consumption=tuple(
                ResourceCharge.model_validate(item)
                for item in model.resource_consumption
            ),
            safety_tags=tuple(model.safety_tags),
            risk_tags=tuple(model.risk_tags),
            provenance=SqlAlchemySimulationRepository._provenance_contract(model),
        )

    @staticmethod
    def _actor_position_contract(model: ActorPositionModel) -> ActorPosition:
        return ActorPosition(
            actor=ActorReference(
                actor_type=ActorType(model.actor_type),
                actor_id=UUID(model.actor_id),
            ),
            location_id=UUID(model.location_id),
            journey_id=UUID(model.journey_id) if model.journey_id else None,
            version=model.version,
        )

    @staticmethod
    def _journey_contract(model: JourneyModel) -> Journey:
        from aether.contracts import TravelParticipant, TravelParticipantType

        return Journey(
            journey_id=UUID(model.journey_id),
            world_id=UUID(model.world_id),
            timeline_id=UUID(model.timeline_id),
            participants=tuple(
                TravelParticipant(
                    actor=ActorReference(
                        actor_type=ActorType(item["actor_type"]),
                        actor_id=UUID(item["actor_id"]),
                    ),
                    participant_type=TravelParticipantType(item["participant_type"]),
                )
                for item in model.participants
            ),
            start_location_id=UUID(model.start_location_id),
            end_location_id=UUID(model.end_location_id),
            route_id=UUID(model.route_id),
            segment_ids=tuple(UUID(item) for item in model.segment_ids),
            resource_owner=(
                ActorReference.model_validate(model.resource_owner)
                if model.resource_owner is not None
                else None
            ),
            costs=tuple(ResourceCharge.model_validate(item) for item in model.costs),
            resource_consumption=tuple(
                ResourceCharge.model_validate(item)
                for item in model.resource_consumption
            ),
            started_at=model.started_at,
            expected_arrival_at=model.expected_arrival_at,
            arrived_at=model.arrived_at,
            status=JourneyStatus(model.status),
            scheduled_event_id=UUID(model.scheduled_event_id),
            provenance=SqlAlchemySimulationRepository._provenance_contract(model),
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
