# Aether Documentation

## Architectural documents

| Document | Purpose |
|---|---|
| Architecture Specification | Product vision, principles, layers, technologies, and architectural limits |
| Domain & Data Model Specification | Domains, entities, states, events, timelines, and persistence |
| Simulation & Narrative Flow Specification | Action cycle, temporal advancement, simulation, commit, and presentation |
| Agent & Context Specification | Agent roles, autonomy, context, knowledge, and focalization |

## Cross-system specifications

`specifications/cross-system-contracts.md` gathers invariants that span multiple subsystems and prevents each engine from interpreting the same rules independently.

## Decision records

`decisions/00001-mvp-decisions.md` is the approved foundational decision record. `decisions/00002-model-decisions.md` is the approved operational model record. Both are part of the mandatory reading hierarchy; their derived technical specifications remain subject to dedicated analysis, benchmarking, and approval.

## Validations

Each validation is recorded individually. The status `APPROVED` indicates an approved decision. Traceability notes identify records reconstructed from preserved summaries and decisions rather than a complete original transcript.

## Conventions

- `MUST` / **MUST**: mandatory requirement.
- `SHOULD` / **SHOULD**: strong architectural recommendation, subject to justification.
- `MAY` / **MAY**: optional capability.
- `PENDING` / **PENDING**: not approved or not yet sufficiently defined.
