from typing import Protocol

from aether.contracts import (
    OrganizationDecisionContext,
    OrganizationDecisionProposal,
)


class OrganizationDecisionPort(Protocol):
    def propose(
        self,
        context: OrganizationDecisionContext,
    ) -> OrganizationDecisionProposal: ...
