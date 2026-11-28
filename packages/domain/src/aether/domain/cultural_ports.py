from typing import Protocol

from aether.contracts import (
    AccessDecision,
    AccessRequirements,
    ActorAccessContext,
    CharacterLanguageProficiency,
    EducationEnrollment,
    EducationProgram,
    InformationTransmission,
    KnowledgeArtifact,
    LearningOpportunity,
    ReligionTradition,
    ScheduledEvent,
    ScheduledEventResolution,
    Technology,
)


class ActorAccessPort(Protocol):
    def decide(
        self,
        requirements: AccessRequirements,
        context: ActorAccessContext,
    ) -> AccessDecision: ...

    def require(
        self,
        requirements: AccessRequirements,
        context: ActorAccessContext,
    ) -> None: ...


class LanguageCommunicationPort(Protocol):
    def can_interpret(
        self,
        transmission: InformationTransmission,
        proficiency: CharacterLanguageProficiency | None,
    ) -> bool: ...


class CulturalScheduledEventResolverPort(Protocol):
    def resolve_knowledge_transmission(
        self, event: ScheduledEvent, artifact: KnowledgeArtifact
    ) -> ScheduledEventResolution: ...

    def resolve_technology_use(
        self, event: ScheduledEvent, technology: Technology
    ) -> ScheduledEventResolution: ...

    def resolve_learning_assessment(
        self,
        event: ScheduledEvent,
        enrollment: EducationEnrollment,
        program: EducationProgram,
        opportunity: LearningOpportunity | None,
    ) -> ScheduledEventResolution: ...

    def resolve_religious_ritual(
        self, event: ScheduledEvent, tradition: ReligionTradition
    ) -> ScheduledEventResolution: ...
