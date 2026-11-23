# Application Package Instructions

This package owns use-case orchestration and transaction boundaries.

- Depend on domain ports, not concrete infrastructure classes.
- Do not keep a transaction open while an LLM or external adapter is executing.
- Simulation operations must be idempotent and recoverable.
- Tests must cover commit, idempotent replay, and failure recovery.
