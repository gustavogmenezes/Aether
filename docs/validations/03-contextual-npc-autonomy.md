# Validation 03 — Contextual autonomy of NPCs

**Status:** APPROVED — reconstruction



> Traceability note: the approved content is preserved in project summaries/decisions, but the full original wording of this validation was not recovered. This file is a faithful reconstruction of the available content; confirm the exact title/order during the documentation audit before declaring textual equivalence.


## Decisions and contracts

- NPCs have contextual autonomy: goals, plans, decisions, off-screen actions, lies, omissions, failures, and plan revisions.
- Decisions are limited by personality, capabilities, knowledge, resources, relationships, and circumstances.
- There is no persistent LLM instance per NPC; a reusable agent receives isolated context.
- Simulation tiers: primary (deep individual), secondary (abstract individual), populations (collective/statistical).
- Promotion/demotion preserves state, memory, and history.


## Implementation rule
Implementations must preserve these decisions and their cross-system contracts. Technical difficulties must be recorded as conflicts/proposals, never resolved through silent relaxation.
