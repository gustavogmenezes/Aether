# Validation 01 — Action, simulation, and presentation cycle

**Status:** APPROVED



## Decisions and contracts

- The flow has three macro-phases: preparation, simulation, and presentation.
- Actions are classified as instantaneous, interval, interruptible, or scheduled.
- The Game Master proposes a structured action; the Engine validates and resolves it.
- Events are processed chronologically; NPCs may act during intervals.
- Use `simulation_run_id`, a short transaction, atomic commit, idempotency, and recovery.
- The Narrator receives only confirmed results.


## Implementation rule
Implementations must preserve these decisions and their cross-system contracts. Technical difficulties must be recorded as conflicts/proposals, never resolved through silent relaxation.
