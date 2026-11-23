from typing import Protocol

from aether.contracts import NpcDecisionContext, NpcDecisionProposal


class NpcDecisionPort(Protocol):
    def propose(self, context: NpcDecisionContext) -> NpcDecisionProposal: ...
