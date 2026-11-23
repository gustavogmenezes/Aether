# Aether Storytelling System

This repository contains the Aether Storytelling System architectural specification package, prepared to guide development assisted by GitHub Copilot.

## Package status

- 4 consolidated architectural documents.
- 31 validation records, one file per validation.
- `AGENTS.md` with mandatory rules for coding agents.
- Glossary, decision map, cross-system contracts, and implementation roadmap.
- Decision records in `docs/decisions/`: an approved foundational decision and an approved operational model.

**Reading rule:** explicitly approved decisions are contracts. Details identified as proposals, hypotheses, or open items must not be treated as approved decisions.

## Reading order

1. `AGENTS.md`
2. `docs/README.md`
3. `docs/architecture/architecture-specification.md`
4. `docs/architecture/domain-data-model-specification.md`
5. `docs/architecture/simulation-narrative-flow-specification.md`
6. `docs/architecture/agent-context-specification.md`
7. `docs/specifications/cross-system-contracts.md`
8. `docs/decisions/00001-mvp-decisions.md` — **APPROVED**
9. `docs/decisions/00002-model-decisions.md` — **APPROVED**
10. `docs/validations/README.md` and the individual records.

## Scope

Aether is a local-first storytelling/RPG system with persistent worlds, causal simulation, autonomous NPCs, literary narrative, and contextual image generation. The project must not depend on external APIs for essential functionality.

## Current implementation

The repository now contains the Phase 0/1 transactional-core slice:

- Bounded Python packages for contracts, domain, engines, application, and infrastructure.
- Pydantic contracts for events, scheduled intentions, temporal commands, and recoverable execution records.
- Deterministic event ordering with causal dependencies, operational priority, and stable tie-breaking.
- SQLite persistence through SQLAlchemy and Alembic.
- `AdvanceTime` and `AdvanceUntilEvent` services with atomic commit, optimistic state versions, idempotent replay, and failure recovery.
- A Phase 2 action flow with replaceable Game Master, Action Validation, Narrator, and Presentation Delivery ports.
- Deterministic wait-command interpretation and template narration for local development without selecting an LLM runtime.
- Persistent generated/confirmed presentation records and delivered Player Knowledge/Narrative State extraction.
- Separate persistent Character Knowledge and delayed Information Transmission.
- Perception and interpretation filters based on character, visibility, acquisition time, confidence, and epistemic status.
- Authorized temporal delivery of communications without granting characters direct World State access.
- Separate character identity, personality, and psychological/behavioral state records.
- Directional multidimensional relationships and persistent motives, hierarchical goals, plans, and plan steps.
- Isolated, deterministic NPC decision proposals with replaceable decision ports.
- Validated, idempotent plan-step scheduling without automatic clock advancement.
- Pure scheduled-event resolution for off-screen NPC plan steps during authorized temporal intervals.
- Atomic plan completion/failure consequences recorded in the Event Ledger and preserved through replay/recovery.
- Persistent material, social, structural, and personal resource balances.
- Plan-step resource consumption and production with reservations and immutable transactions.
- Failed or interrupted plan execution cannot partially change balances.

No model runtime, narrative generation, or unresolved quantitative model/resource policy is selected by this slice.

The Phase 3 NPC decision slice fulfills validations 03, 06, 07, 08, and 09 and
is recorded in `docs/architecture/adr/0004-personality-relationships-plans-and-npc-decisions.md`.
Worldwide scheduled-event consequences are recorded in
`docs/architecture/adr/0005-worldwide-autonomous-simulation.md`.
Resource-ledger consequences are recorded in
`docs/architecture/adr/0006-resource-ledger-and-plan-consequences.md`.

## Development

Install the project dependencies in the active Python 3.11+ environment:

```bash
python -m pip install -e ".[dev]"
```

Run the focused package suites:

```bash
python -m pytest packages
```

Apply the database migrations:

```bash
python -m alembic upgrade head
```

## Documentation integrity

This package was reconstructed from available project decisions and records. Where the original wording or exact historical numbering could not be recovered in full, this is stated in the record itself. Do not turn editorial reconstructions into new product decisions without project-owner approval.
