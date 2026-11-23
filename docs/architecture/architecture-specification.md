# Architecture Specification
**Aether Storytelling System — v1.0 (consolidation)**

## 1. Product vision

Aether is a local-first engine for creating and running storytelling/RPG experiences in persistent worlds. It combines literary narrative, causal world simulation, autonomous NPCs, configurable RPG rules, and contextual image generation. The standard experience combines immersive prose, rich dialogue, free-form player input, and optional guidance.

Aether is not a linear story waiting for the player. It is a world with its own history and dynamics, whose reality may be discovered and transformed by the protagonist.

## 2. Fundamental principles

1. **Autonomous world:** the world, NPCs, organizations, economy, ecology, and conflicts have independent dynamics.
2. **Player as lens:** the player’s presence and actions determine narrative resolution and detail focus, not the world’s existence or autonomous capacity. A time-consuming action may authorize an interval; it does not imply direct control of the global simulation.
3. **Causality:** events arise from conditions, actions, plans, resources, and previous events.
4. **Individual epistemology:** characters know only what they have accessed through valid means.
5. **LLM subordinate to rules:** the LLM interprets, proposes, and narrates; the domain and engines validate and apply invariants.
6. **Literary narrative:** immersive, focalized, paced prose without automatic prolixity.
7. **Local-first:** essential functionality runs locally without mandatory external APIs.
8. **Modularity:** worlds, rules, agents, engines, and adapters must be replaceable.
9. **Auditability:** relevant changes arise from traceable events.
10. **Adaptive abstraction:** resolution varies by relevance, scale, and narrative focus while continuity is preserved.
11. **Authorized temporal advancement:** autonomy, plans, and schedules do not by themselves move the simulation clock.

## 3. Experience modes

- **Player Character:** the player directly controls the protagonist’s actions, speech, and decisions.
- **Narrative Protagonist:** the player defines intent; the LLM may elaborate intermediate actions, but consequential decisions require approval (controlled autonomy).
- **Observer:** the player follows the world without direct protagonist control.

Mode neither changes the world’s general autonomy nor grants the player omniscience.

The Player Character and Narrative Protagonist modes authorize advancement through resolved actions that consume time. The Observer mode uses explicit `AdvanceTime`, `AdvanceUntil`, or equivalent observer controls. Merely opening the application, maintaining a plan, or scheduling an event is not authorization.

## 4. Narrative perspective

- Narrator style: **literary**.
- Normal focalization: restricted to the protagonist’s perceptible experience.
- The narrator may describe atmosphere, sensations, perceptible inferences, and nuance.
- It does not present private/off-screen scenes as direct protagonist knowledge or secret NPC thoughts as accessible facts.
- The player remains free to attempt actions using metaknowledge; the system resolves them according to actual protagonist capabilities, evidence, and knowledge without fabricating retroactive knowledge.
- Narrative State preserves scene and presentation continuity; it is not an action-blocking mechanism.

## 5. NPC autonomy

Autonomy is **contextual**. NPCs may form goals, plan, decide, act off-screen, lie, conceal, fail, revise plans, and develop relationships. Every action must be compatible with personality, capabilities, knowledge, resources, state, relationships, and circumstances.

The system does not instantiate a persistent LLM per NPC. A reusable decision agent receives isolated, filtered context for each character.

### 5.1 Adaptive resolution
- Tier 1: central NPCs, deep individual simulation.
- Tier 2: secondary NPCs, abstract individual simulation.
- Tier 3: populations and background characters, collective/statistical simulation.
- Materialization and promotion expand an aggregate into compatible individual representation without duplicating members or inventing contradictory history.
- Dynamic promotion/demotion or consolidation changes simulation resolution by narrative relevance while preserving identity, state, memory, relationships, active plans, and history.

## 6. Logical layers

- **Presentation:** local web interface and API.
- **Application:** use cases, orchestration, and simulation coordination.
- **Domain:** entities, invariants, events, value objects, and policies.
- **Engines:** time, events, NPCs, progression, relationships, resources, combat, economy, etc.
- **Agents:** Game Master, NPC Decision Agent, World Architect, Character Architect, and Narrator.
- **Infrastructure:** SQLite, filesystem, embeddings, indexes, local inference, and image generation.

### 6.1 Agent roles
- **Game Master:** interprets input and proposes a structured action; it does not apply arbitrary state.
- **NPC Decision Agent:** proposes contextual NPC decisions using only that NPC’s knowledge.
- **World Architect:** helps create the world, history, rules, geography, factions, and policies; important canonical changes require approval.
- **Character Architect:** creates identity, psychology, behavior, goals, initial knowledge, and relationships.
- **Narrator:** presents confirmed results in literary prose; it does not decide mechanical outcomes.

### 6.2 Development structure and agent contexts

The repository is a monorepo of independently identifiable packages or bounded contexts. Each package has an explicit responsibility, dependency boundary, development context, instructions, and test command. Development agents may receive package-scoped context, but cross-package contracts remain repository-wide constraints. This package model does not imply that every listed domain must become an installable package.

## 7. Domain engines

Aether should maintain integrated, specialized engines, including:
- World Clock, Event Scheduler, and Simulation Processor.
- Timeline Manager, Branch Manager, Temporal Event Resolver, and Causality Tracker.
- Character Genesis and Character Progression.
- Personality, Relationship, Goal & Motivation.
- Perception & Cognition and Information & Communication.
- Resource & Economy.
- Organization & Power.
- Geography & Territory, Ecology & Biology, Demography.
- Technology & Knowledge, Religion & Belief, Language & Education.
- Health, Combat Resolution, Justice, Conflict & Diplomacy.
- Media & Public Opinion, Arts, Leisure, Transportation, Security & Crime.
- Visual Identity, Sound Identity, and Narrative Resolution.
- Canonization and entity materialization/consolidation as cross-domain mechanisms.
- Persisted Simulation Run, LLM Invocation, and Agent Proposal records.

The Combat Resolution Engine determines tactical outcomes; the Health System determines resulting physical and medical conditions, and the Character Progression Engine evaluates longer-term consequences. This list maps approved domains; it does not require each item to be an independent installable package.

## 8. Reference technical architecture

The initial proposal, subject to ADRs and technical validation:
- Backend: Python + FastAPI + Pydantic.
- Transactional persistence: SQLite + SQLAlchemy.
- Frontend: React + TypeScript, local web interface.
- LLM inference: llama.cpp with local GGUF models.
- Embeddings: replaceable local model.
- Image generation: ComfyUI in a local workflow.
- Authored data: YAML and Markdown.
- Assets: local filesystem.
- Tests: pytest and integration tests.

These are preferred technologies, not approved vendor coupling. Significant adoption, replacement, or runtime/model selection requires an ADR after technical validation. Do not initially introduce Docker/Kubernetes, Redis, PostgreSQL, or cloud services as mandatory dependencies without justification and approval.

## 9. Hardware and resources

Known target configuration: Omarchy/Arch Linux, NVIDIA RTX 3060 12 GB. It is a benchmark reference, not a permanent architectural dependency. Concrete model selection, loading/unloading, and RAM/VRAM concurrency policy remain to be benchmarked and specified (DEC-001 through DEC-003); implementation must not assume those details.

## 10. Artificial intelligence strategy

Begin with versioned prompts, templates, retrieval, structured context, validation, and evaluation. Fine-tuning/LoRA is not an initial requirement; consider it only when suitable training data and evidence of benefit exist.

## 11. Implementation principles

- Do not couple the domain to frameworks, models, or vendors.
- Do not delegate deterministic invariants to the LLM.
- Do not allow generated text to become the mechanical source of truth.
- Preserve provenance, logs, and recovery.
- Use English throughout.
- Test at package boundaries as well as through affected cross-package integration and recovery paths.
- Build a small, testable vertical slice first, after documentation and contracts.

For the approved distinctions added by 00001, especially canonization, tier continuity, event ordering, recovery records, and knowledge presentation, see `../decisions/00001-mvp-decisions.md`. The architecture documents summarize how those decisions integrate; they do not replace the decision record.
