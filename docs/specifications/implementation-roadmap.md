# Implementation Roadmap — proposed technical sequence

This roadmap organizes dependencies; it is not authorization to begin implementation without user review.

## Phase 0 — Foundation
- Establish the approved English-only monorepo with independently identifiable bounded packages, explicit dependency direction, package instructions, and package-level agent contexts.
- Define root and package-level configuration, logging, test commands, quality gates, and contract tests across package boundaries.
- Domain models and stable IDs.
- SQLite persistence and migrations.
- Prompt and schema versioning.
- Record significant technology choices through ADRs; treat the reference stack as replaceable preferred technology, not approved vendor coupling.
- Apply the approved 00002 operational profile while benchmarking concrete models and resource strategies for DEC-001 through DEC-003.

## Phase 1 — Transactional core
- Package the World, Session, Character, and Location boundaries behind explicit cross-package contracts.
- Event Ledger, Event Scheduler, World Clock, and `AdvanceTime`/`AdvanceUntil`/pause authorization.
- Persist separate Simulation Run, LLM Invocation, and Agent Proposal records.
- Common event envelope, causal and deterministic ordering, controlled concurrency, atomic commit, and recovery.
- Chronology, causality, idempotency, concurrency, and failure tests at package and integration levels.

## Phase 2 — Action and narrative
- Player Input, Game Master, Action Proposal.
- Hybrid duration and action categories.
- Context Builder and literary Narrator.
- Focalization and knowledge filtering.
- Presentation-confirmation-extraction lifecycle for persistent Player Knowledge and Narrative State.

## Phase 3 — Characters
- Character Genesis and Storytelling character sheet.
- Character Progression.
- Personality, Relationship, Goals & Motivation.
- Perception & Cognition.
- Information & Communication.
- Materialization, promotion/demotion, and consolidation continuity across simulation tiers.

## Phase 4 — Autonomous world
- NPC Decision Agent and simulation tiers.
- Organizations, resources, economy, and geography.
- Causal, scheduled, and emergent events.
- Adaptive resolution / player as lens.
- Four-level canonization and provenance.

## Phase 5 — Social and natural domains
- Ecology, demography, technology, religion, language, education.
- Dedicated Combat Resolution with Health responsible for physical/medical conditions.
- Justice, diplomacy, security.
- Media, arts, leisure, transportation.

## Phase 6 — Multimodal experience
- Visual identity and contextual image generation.
- Sonic identity and optional audio.
- Local web interface and world-authoring tools.

## Phase 7 — Evaluation
- Narrative and causal consistency tests.
- Long scenarios and branching.
- Narrative-quality evaluation.
- RAM/VRAM profiling and model concurrency benchmarks.
- Package-level regression suites plus cross-package recovery and contract suites.

## Open-specification gate

Do not infer DEC-001 through DEC-013 values or algorithms. Implement the approved direction from 00001 and 00002, plus only the approved portions of dedicated specifications and ADRs. Concrete model selection and quantitative resource policy remain benchmark-dependent.

See `decision-status-and-open-items.md` for the 13-item register and `../decisions/00001-mvp-decisions.md` for the binding decisions.
