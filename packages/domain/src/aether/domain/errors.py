class AetherDomainError(Exception):
    pass


class InvalidTemporalAdvanceError(AetherDomainError):
    pass


class TimelineMismatchError(AetherDomainError):
    pass


class StaleWorldStateError(AetherDomainError):
    pass


class CausalOrderingError(AetherDomainError):
    pass


class DuplicateSimulationRunError(AetherDomainError):
    pass


class SimulationRunInProgressError(AetherDomainError):
    pass


class ActionValidationError(AetherDomainError):
    pass


class PresentationDeliveryError(AetherDomainError):
    pass


class NpcDecisionConflictError(AetherDomainError):
    pass


class NpcDecisionValidationError(AetherDomainError):
    pass


class PlanStepSchedulingRejectedError(AetherDomainError):
    pass


class CanonizationValidationError(AetherDomainError):
    pass


class ResourceInvariantError(AetherDomainError):
    pass


class OrganizationDecisionConflictError(AetherDomainError):
    pass


class OrganizationDecisionValidationError(AetherDomainError):
    pass


class OrganizationAuthorityError(AetherDomainError):
    pass


class CharacterGenesisError(AetherDomainError):
    pass


class CharacterProgressionError(AetherDomainError):
    pass


class SimulationTierTransitionError(AetherDomainError):
    pass
