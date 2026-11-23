# AGENTS.md — Aether Storytelling System

## 1. Mission

You are working on the Aether Storytelling System, a local-first storytelling/RPG engine. The goal is to build a persistent, causal, autonomous fictional world experienced by the player through a literary narrative. The player may transform the world, but is not required for the world to exist or continue operating.

## 2. Documentation hierarchy

Before implementing any functionality:
1. Read `README.md` and this file.
2. Consult the four documents in `docs/architecture/`.
3. Consult the cross-system contracts in `docs/specifications/cross-system-contracts.md`.
4. Consult the approved foundational decision in `docs/decisions/00001-mvp-decisions.md`.
5. Consult the applicable validation in `docs/validations/`.
6. Consult the approved operational model in `docs/decisions/00002-model-decisions.md`.

In case of conflict:
- Do not silently choose an interpretation.
- Identify the conflict, the involved documents, and the impact.
- Propose a resolution and wait for human approval.
- Never change an approved contract merely for implementation convenience.

## 3. Non-negotiable rules

- The world has history, state, causality, goals, and dynamics independent of the protagonist.
- The world does not advance while the application is closed and must never advance merely because the application is open, an NPC has a plan, or a scheduled event exists.
- World time advances only through an explicitly authorized temporal operation: a time-consuming player action, `AdvanceTime`, `AdvanceUntil`, or an equivalent authorized observer control.
- `PauseSimulation` or an equivalent pause preserves the frozen clock until a later authorized operation.
- The player is a lens of narrative resolution, not the controller of the world simulation.
- The Narrator uses literary perspective and focalization restricted to the protagonist’s perceptible experience, except for explicit world rules.
- NPCs have contextual autonomy limited by identity, knowledge, resources, capabilities, goals, plans, and circumstances.
- No character automatically accesses the world’s objective state. Knowledge depends on perception, communication, investigation, deduction, or world-defined powers.
- The LLM proposes and interprets; deterministic engines validate, resolve, and persist mechanical rules whenever possible.
- The Narrator receives confirmed, persisted results; it does not invent mechanical consequences.
- Narrative expansion of abstract elements must respect canon, geography, chronology, epistemology, causality, and world rules.
- Generated content does not automatically become canon when a change is structural or relevant; apply the approval flow defined by the World Architect.
- Vector indexes and graphs are derived and rebuildable. SQLite is the transactional authority for dynamic state and events.
- Do not introduce a mandatory dependency on external services.

## 4. Architecture and separation of responsibilities

Preserve separation among:
- Domain: entities, value objects, invariants, and domain contracts.
- Application: use cases and orchestration.
- Engines: deterministic, specialized rule resolution.
- Agents: contextual reasoning with an LLM.
- Infrastructure: persistence, local inference, filesystem, embeddings, and integrations.
- Presentation: API and interface.

Do not put domain rules in UI components, prompts, or infrastructure adapters. Do not allow LLM agents to write directly to the database without validation by the domain/application.

## 5. LLM and local execution

- Essential execution must be local.
- Use local models through replaceable adapters.
- Do not couple the domain to a specific vendor or runtime.
- Select concrete models, loading policies, concurrency budgets, and resource algorithms only through benchmarking and approved specifications/ADRs.
- Account for the target configuration’s VRAM constraint (RTX 3060 12 GB); plan model loading/unloading and concurrency.
- Do not keep heavy language and image models on the GPU simultaneously without an explicit resource policy.
- Begin with prompts, templates, retrieval, and evaluation; fine-tuning/LoRA is a future possibility, not an initial premise.

## 6. Persistence and transactions

- SQLite is the initial transactional source of truth.
- YAML stores editable canonical definitions/configurations.
- Markdown stores lore, documentation, and authored content.
- Binary assets live in the filesystem with stable references in the database.
- Vector/graph indexes are derived and rebuildable.
- Do not hold a SQLite transaction open while waiting for an LLM response.
- Use identifiable execution (`simulation_run_id`), state/version validation, short atomic commits, idempotency, and recovery.
- Never partially apply a simulation.

## 7. Changes and tests

Every change must:
- Reference the specification/validation it fulfills.
- Preserve invariants and cross-system contracts.
- Include domain, integration, and recovery tests proportionate to its risk.
- Cover causality, idempotency, temporal ordering, filtered knowledge, and narrative consistency when applicable.
- Update documentation when a human decision changes an approved contract.

## 8. Agent behavior and language

- If a request is ambiguous, ask only what is necessary.
- If documentation is incomplete, state the gap.
- Never invent decisions, entities, technologies, or rules as though they were approved.
- Prefer small, traceable, reversible changes.
- English is mandatory across source code, names, identifiers, documentation, tests, prompts, comments, logs, user/developer-facing artifacts, and generated artifacts. Preserve existing externally visible or technical identifiers verbatim when they are approved contracts or compatibility requirements.
- Development is a monorepo of bounded packages with explicit cross-package contracts, package-level instructions/tests, and locally selectable package agent contexts.
- Keep conflicts surfaced instead of silently resolving them.
