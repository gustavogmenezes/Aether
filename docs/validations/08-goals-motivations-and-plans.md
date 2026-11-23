# Validation 08 — Goals, motivations, and plans

**Status:** APPROVED — reconstruction



> Traceability note: the approved content is preserved in project summaries/decisions, but the full original wording of this validation was not recovered. This file is a faithful reconstruction of the available content; confirm the exact title/order during the documentation audit before declaring textual equivalence.


## Decisions and contracts

- Motives explain why a character wants something; goals are desired outcomes; plans describe how to achieve them.
- Goals may be hierarchical (long, medium, and short term), coexist, compete, or conflict.
- Plans are mutable, revisable, abandonable, and may fail.
- Goals and plans persist while the protagonist is elsewhere.
- The Scheduler tracks future steps; the Event Ledger records only events that actually occurred.


## Implementation rule
Implementations must preserve these decisions and their cross-system contracts. Technical difficulties must be recorded as conflicts/proposals, never resolved through silent relaxation.
