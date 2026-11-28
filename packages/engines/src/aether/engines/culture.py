from uuid import UUID, uuid4

from aether.contracts import (
    AccessDecision,
    AccessFailure,
    AccessRequirements,
    ActorAccessContext,
    AssessmentOutcome,
    CharacterLanguageProficiency,
    CommunicationMedium,
    EducationEnrollment,
    EducationProgram,
    InformationTransmission,
    KnowledgeArtifact,
    KnowledgeLifecycleRecord,
    KnowledgeLifecycleState,
    KnowledgeTransmissionPayload,
    LearningAssessmentPayload,
    LearningOpportunity,
    ReligiousRitualPayload,
    ReligionTradition,
    RitualCompletion,
    ScheduledEvent,
    ScheduledEventOutcome,
    ScheduledEventResolution,
    Technology,
    TechnologyUsePayload,
)


class ActorAccessEngine:
    def decide(
        self,
        requirements: AccessRequirements,
        context: ActorAccessContext,
    ) -> AccessDecision:
        failures: list[AccessFailure] = []
        if requirements.location_ids and context.location_id not in requirements.location_ids:
            failures.append(
                AccessFailure(
                    code="location-denied",
                    requirement=",".join(map(str, requirements.location_ids)),
                    message="Actor is not at an authorized location",
                )
            )
        for required in requirements.resource_requirements:
            available = context.available_resources.get(required.resource_code, 0)
            if available < required.quantity:
                failures.append(
                    AccessFailure(
                        code="resource-unavailable",
                        requirement=(
                            f"{required.resource_code}:{required.quantity}"
                        ),
                        message="Required resource is unavailable",
                    )
                )
        for infrastructure_id in requirements.infrastructure_ids:
            if infrastructure_id not in context.available_infrastructure_ids:
                failures.append(
                    AccessFailure(
                        code="infrastructure-unavailable",
                        requirement=str(infrastructure_id),
                        message="Required infrastructure is unavailable",
                    )
                )
        for language_id in requirements.language_requirements:
            if language_id not in context.language_capabilities:
                failures.append(
                    AccessFailure(
                        code="language-barrier",
                        requirement=str(language_id),
                        message="Actor lacks an explicit language capability",
                    )
                )
        for permission in requirements.secrecy_permissions:
            if permission not in context.secrecy_permissions:
                failures.append(
                    AccessFailure(
                        code="secrecy-denied",
                        requirement=permission,
                        message="Actor lacks the required secrecy permission",
                    )
                )
        for condition in requirements.education_admission_conditions:
            if condition not in context.education_qualifications:
                failures.append(
                    AccessFailure(
                        code="education-admission-denied",
                        requirement=condition,
                        message="Education admission condition is not satisfied",
                    )
                )
        for prerequisite in requirements.prerequisite_requirements:
            actual = context.satisfied_prerequisite_states.get(str(prerequisite.entity_id))
            if actual != prerequisite.required_state:
                failures.append(
                    AccessFailure(
                        code="prerequisite-unsatisfied",
                        requirement=(
                            f"{prerequisite.entity_id}:{prerequisite.required_state.value}"
                        ),
                        message="Required knowledge or technology state is not established",
                    )
                )
        for capability in requirements.capability_conditions:
            if capability not in context.satisfied_capabilities:
                failures.append(
                    AccessFailure(
                        code="capability-unsatisfied",
                        requirement=capability,
                        message="Required capability condition is not satisfied",
                    )
                )
        return AccessDecision(allowed=not failures, failures=tuple(failures))

    def require(
        self,
        requirements: AccessRequirements,
        context: ActorAccessContext,
    ) -> None:
        decision = self.decide(requirements, context)
        if not decision.allowed:
            codes = ",".join(failure.code for failure in decision.failures)
            raise PermissionError(f"Actor access denied: {codes}")


class LanguageCommunicationEngine:
    def can_interpret(
        self,
        transmission: InformationTransmission,
        proficiency: CharacterLanguageProficiency | None,
    ) -> bool:
        language_id = (
            transmission.target_language_id or transmission.source_language_id
        )
        if language_id is None:
            return True
        if proficiency is None or proficiency.language_id != language_id:
            return False
        if not self._present(proficiency.comprehension):
            return False
        if transmission.medium in {
            CommunicationMedium.PHYSICAL,
            CommunicationMedium.TECHNOLOGICAL,
        } and transmission.writing_system_id is not None:
            return self._present(proficiency.reading)
        return True

    @staticmethod
    def _present(value: str) -> bool:
        return value.strip().lower() not in {"", "none", "absent", "unknown"}


class CulturalScheduledEventResolver:
    def __init__(self, access_engine: ActorAccessEngine | None = None) -> None:
        self._access = access_engine or ActorAccessEngine()

    def resolve_knowledge_transmission(
        self,
        event: ScheduledEvent,
        artifact: KnowledgeArtifact,
    ) -> ScheduledEventResolution:
        if event.event_type != "knowledge-transmission":
            raise ValueError("Knowledge transmission resolver received another type")
        payload = KnowledgeTransmissionPayload.model_validate(event.payload)
        if artifact.world_id != event.world_id:
            raise ValueError("Knowledge artifact belongs to another world")
        if payload.artifact_id != artifact.artifact_id:
            raise ValueError("Knowledge transmission targets another artifact")
        if payload.target_state != KnowledgeLifecycleState.TRANSMITTED:
            raise ValueError("Knowledge transmission must use the transmitted state")
        self._require_actor(payload.actor_id, payload.access_context)
        self._require_location(payload.location_id, payload.access_context)
        self._access.require(artifact.requirements, payload.access_context)
        updated = self._advance_artifact(
            artifact, KnowledgeLifecycleState.TRANSMITTED, event
        )
        record = self._lifecycle(
            "knowledge-artifact",
            artifact.artifact_id,
            payload.actor_id,
            KnowledgeLifecycleState.TRANSMITTED,
            payload.cause,
            payload.location_id,
            payload.language_id,
            event,
            artifact,
        )
        return ScheduledEventResolution(
            scheduled_event_id=event.event_id,
            outcome=ScheduledEventOutcome.COMPLETED,
            payload={
                **event.payload,
                "resolution": "transmitted",
                "record_id": str(record.record_id),
            },
            knowledge_artifact=updated,
            lifecycle_records=(record,),
            reason="Explicit knowledge transmission completed",
        )

    def resolve_technology_use(
        self,
        event: ScheduledEvent,
        technology: Technology,
    ) -> ScheduledEventResolution:
        if event.event_type != "technology-use-completion":
            raise ValueError("Technology use resolver received another type")
        payload = TechnologyUsePayload.model_validate(event.payload)
        if technology.world_id != event.world_id:
            raise ValueError("Technology belongs to another world")
        if payload.technology_id != technology.technology_id:
            raise ValueError("Technology completion targets another technology")
        if payload.target_state != KnowledgeLifecycleState.APPLIED:
            raise ValueError("Technology use completion must use the applied state")
        self._require_actor(payload.actor_id, payload.access_context)
        self._require_location(payload.location_id, payload.access_context)
        explicit_conditions = tuple(
            technology.manufacture_conditions
            + technology.labor_conditions
            + technology.funding_conditions
            + technology.political_conditions
            + technology.material_references
        )
        requirements = technology.requirements.model_copy(
            update={
                "capability_conditions": tuple(
                    dict.fromkeys(
                        technology.requirements.capability_conditions
                        + explicit_conditions
                    )
                )
            }
        )
        self._access.require(requirements, payload.access_context)
        updated = technology.model_copy(
            update={
                "state": KnowledgeLifecycleState.APPLIED,
                "provenance": technology.provenance.model_copy(
                    update={
                        "origin_event_id": event.event_id,
                        "updated_at": event.scheduled_at,
                        "version": technology.provenance.version + 1,
                    }
                ),
            }
        )
        record = KnowledgeLifecycleRecord(
            record_id=uuid4(),
            entity_type="technology",
            entity_id=technology.technology_id,
            actor_id=payload.actor_id,
            state=KnowledgeLifecycleState.APPLIED,
            occurred_at=event.scheduled_at,
            cause=payload.cause,
            location_id=payload.location_id,
            source_event_id=event.event_id,
            provenance=technology.provenance.model_copy(
                update={
                    "source_type": "scheduled-event",
                    "source_id": str(event.event_id),
                    "origin_event_id": event.event_id,
                    "updated_at": event.scheduled_at,
                    "version": technology.provenance.version + 1,
                }
            ),
        )
        return ScheduledEventResolution(
            scheduled_event_id=event.event_id,
            outcome=ScheduledEventOutcome.COMPLETED,
            payload={
                **event.payload,
                "resolution": "applied",
                "record_id": str(record.record_id),
            },
            technology=updated,
            lifecycle_records=(record,),
            reason="Explicit technology use completed",
        )

    def resolve_learning_assessment(
        self,
        event: ScheduledEvent,
        enrollment: EducationEnrollment,
        program: EducationProgram,
        opportunity: LearningOpportunity | None,
    ) -> ScheduledEventResolution:
        if event.event_type != "learning-assessment":
            raise ValueError("Learning assessment resolver received another type")
        payload = LearningAssessmentPayload.model_validate(event.payload)
        if payload.enrollment_id != enrollment.enrollment_id:
            raise ValueError("Assessment targets another enrollment")
        if enrollment.program_id != program.program_id:
            raise ValueError("Enrollment does not belong to its education program")
        if program.world_id != event.world_id:
            raise ValueError("Education program belongs to another world")
        if payload.actor_id != enrollment.character_id:
            raise ValueError("Enrollment and assessment actor do not match")
        if opportunity is not None and (
            opportunity.opportunity_id != payload.opportunity_id
            or opportunity.participant_character_id != payload.actor_id
            or opportunity.program_id != program.program_id
        ):
            raise ValueError("Assessment opportunity does not match participation")
        self._require_actor(payload.actor_id, payload.access_context)
        requirements = AccessRequirements(
            location_ids=program.location_ids,
            resource_requirements=program.resource_requirements,
            infrastructure_ids=program.infrastructure_ids,
            language_requirements=program.language_ids,
            education_admission_conditions=program.admission_requirements,
        )
        self._access.require(requirements, payload.access_context)
        outcome = AssessmentOutcome(
            outcome_id=uuid4(),
            enrollment_id=enrollment.enrollment_id,
            opportunity_id=opportunity.opportunity_id if opportunity else None,
            character_id=enrollment.character_id,
            assessed_at=event.scheduled_at,
            assessor_character_id=payload.assessor_character_id,
            stated_outcome=payload.stated_outcome,
            evidence_references=payload.evidence_references,
            mastery_asserted=payload.mastery_asserted,
            completion_asserted=payload.completion_asserted,
            source_event_id=event.event_id,
            provenance=program.provenance.model_copy(
                update={
                    "source_type": "learning-assessment",
                    "source_id": str(event.event_id),
                    "origin_event_id": event.event_id,
                    "updated_at": event.scheduled_at,
                    "version": program.provenance.version + 1,
                }
            ),
        )
        return ScheduledEventResolution(
            scheduled_event_id=event.event_id,
            outcome=ScheduledEventOutcome.COMPLETED,
            payload={
                **event.payload,
                "resolution": "assessed",
                "outcome_id": str(outcome.outcome_id),
            },
            learning_opportunities=(opportunity,) if opportunity is not None else (),
            assessment_outcomes=(outcome,),
            reason="Explicit learning assessment completed",
        )

    def resolve_religious_ritual(
        self,
        event: ScheduledEvent,
        tradition: ReligionTradition,
    ) -> ScheduledEventResolution:
        if event.event_type != "religious-ritual":
            raise ValueError("Religious ritual resolver received another type")
        payload = ReligiousRitualPayload.model_validate(event.payload)
        if tradition.world_id != event.world_id:
            raise ValueError("Religious tradition belongs to another world")
        if payload.tradition_id != tradition.tradition_id:
            raise ValueError("Religious ritual targets another tradition")
        self._require_actor(payload.actor_id, payload.access_context)
        self._require_location(payload.location_id, payload.access_context)
        requirements = payload.access_requirements.model_copy(
            update={
                "location_ids": tuple(payload.access_requirements.location_ids)
                or (payload.location_id,)
            }
        )
        self._access.require(requirements, payload.access_context)
        completion = RitualCompletion(
            completion_id=uuid4(),
            tradition_id=tradition.tradition_id,
            organization_id=tradition.organization_id,
            actor_id=payload.actor_id,
            ritual_reference=payload.ritual_reference,
            location_id=payload.location_id,
            completed_at=event.scheduled_at,
            source_event_id=event.event_id,
            participants=payload.participants,
            outcome_record=payload.outcome_record,
            provenance=tradition.provenance.model_copy(
                update={
                    "source_type": "religious-ritual",
                    "source_id": str(event.event_id),
                    "origin_event_id": event.event_id,
                    "updated_at": event.scheduled_at,
                    "version": tradition.provenance.version + 1,
                }
            ),
        )
        return ScheduledEventResolution(
            scheduled_event_id=event.event_id,
            outcome=ScheduledEventOutcome.COMPLETED,
            payload={
                **event.payload,
                "resolution": "completed",
                "completion_id": str(completion.completion_id),
            },
            ritual_completions=(completion,),
            reason="Explicit religious ritual completed",
        )

    @staticmethod
    def _require_actor(actor_id: UUID, context: ActorAccessContext) -> None:
        if actor_id != context.actor_id:
            raise PermissionError("Actor access context belongs to another actor")

    @staticmethod
    def _require_location(
        location_id: UUID | None, context: ActorAccessContext
    ) -> None:
        if location_id is not None and location_id != context.location_id:
            raise PermissionError("Actor access location does not match the event")

    @staticmethod
    def _advance_artifact(
        artifact: KnowledgeArtifact,
        state: KnowledgeLifecycleState,
        event: ScheduledEvent,
    ) -> KnowledgeArtifact:
        return artifact.model_copy(
            update={
                "state": state,
                "provenance": artifact.provenance.model_copy(
                    update={
                        "origin_event_id": event.event_id,
                        "updated_at": event.scheduled_at,
                        "version": artifact.provenance.version + 1,
                    }
                ),
            }
        )

    @staticmethod
    def _lifecycle(
        entity_type: str,
        entity_id: UUID,
        actor_id: UUID,
        state: KnowledgeLifecycleState,
        cause: str,
        location_id: UUID | None,
        language_id: UUID | None,
        event: ScheduledEvent,
        source,
    ) -> KnowledgeLifecycleRecord:
        return KnowledgeLifecycleRecord(
            record_id=uuid4(),
            entity_type=entity_type,
            entity_id=entity_id,
            actor_id=actor_id,
            state=state,
            occurred_at=event.scheduled_at,
            cause=cause,
            location_id=location_id,
            source_event_id=event.event_id,
            language_id=language_id,
            provenance=source.provenance.model_copy(
                update={
                    "source_type": "scheduled-event",
                    "source_id": str(event.event_id),
                    "origin_event_id": event.event_id,
                    "updated_at": event.scheduled_at,
                    "version": source.provenance.version + 1,
                }
            ),
        )
