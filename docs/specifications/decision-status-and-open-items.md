# Decision Status & Open Items

This register distinguishes approved contracts from preferred technical directions and unresolved specifications. Approved validation wording and traceability notes remain authoritative in `../validations/README.md`.

## Approved decisions

All 31 validations are approved; Validation 31 is approved conceptually. Reconstruction labels preserve the provenance facts from the validation registry and do not change approval status.

| No. | Validation | Status |
|---:|---|---|
| 01 | Action, simulation, and presentation cycle | APPROVED |
| 02 | Separation of state, knowledge, and disclosure | APPROVED |
| 03 | Contextual autonomy of NPCs | APPROVED — reconstruction |
| 04 | Character creation, identity, and genesis | APPROVED — reconstruction |
| 05 | Character progression and evolution | APPROVED |
| 06 | Personality and psychological transformation | APPROVED — reconstruction |
| 07 | Relationship system | APPROVED — reconstruction |
| 08 | Goals, motivations, and plans | APPROVED — reconstruction |
| 09 | Perception and cognition | APPROVED — reconstruction |
| 10 | Information and communication | APPROVED — reconstruction |
| 11 | Resources, economy, and needs | APPROVED |
| 12 | Institutions, organizations, and power | APPROVED |
| 13 | Geography, territory, and infrastructure | APPROVED |
| 14 | Culture, society, and collective identity | APPROVED |
| 15 | Ecology, biology, and natural systems | APPROVED |
| 16 | Technology, knowledge, and scientific evolution | APPROVED |
| 17 | Religion, spirituality, and belief systems | APPROVED |
| 18 | Language, communication, and linguistic evolution | APPROVED |
| 19 | Education, training, and knowledge transmission | APPROVED |
| 20 | Health, medicine, and conditions of existence | APPROVED |
| 21 | Reproduction, demography, and life cycles | APPROVED |
| 22 | Justice, laws, and normative systems | APPROVED |
| 23 | Conflicts, diplomacy, and international relations | APPROVED |
| 24 | Media, public information, and collective opinion | APPROVED |
| 25 | Arts and creative expression | APPROVED |
| 26 | Transportation and mobility | APPROVED |
| 27 | Security, intelligence, and crime | APPROVED |
| 28 | Entertainment, leisure, and everyday life | APPROVED |
| 29 | Customization, identity, and appearance | APPROVED |
| 30 | Sounds, music, and sonic identity | APPROVED |
| 31 | Orchestration, abstraction, and narrative resolution — player as lens | APPROVED CONCEPTUALLY |

`../decisions/00001-mvp-decisions.md` (AETHER-DEC-000001) is **APPROVED** as the foundational resolution. It preserves the approved validation contracts and adds project-wide direction for the development model, temporal authorization, canonization, simulation continuity, event persistence and ordering, recoverable model use, combat separation, knowledge presentation, and technology evaluation.

`../decisions/00002-model-decisions.md` (AETHER-ARCH-OPR-001) is **APPROVED** as the project-wide Reference Operational Profile. It approves the local-first, single-user, event-driven, resource-bounded, deterministic-authority, reproducible, and recoverable operating principles. It does not select concrete models or authorize completion of unresolved quantitative policies without the required benchmarks, specifications, or ADRs.

## Approved development decisions

- English is mandatory throughout source, documentation, tests, prompts, artifacts, identifiers, and developer/user-facing project content.
- Aether is a monorepo organized into independently identifiable packages or bounded contexts with explicit responsibilities, dependencies, package-specific contexts, package-level tests, and support for package-level agent assignment.
- Essential execution remains local-first, without a mandatory external dependency.
- Clean Code, DDD, SOLID, and separation of concerns apply to implementation, with tests after coded changes.

## Preferred reference stack

Python/FastAPI/Pydantic, SQLite/SQLAlchemy/Alembic, React/TypeScript, llama.cpp/GGUF, replaceable local embeddings, and ComfyUI are the initial **preferred reference stack**. They are subject to technical validation and significant adoption or replacement must be recorded in ADRs. This status does not approve permanent vendor/runtime coupling or preselect the concrete models.

Fine-tuning/LoRA is not an initial premise. Graphify is a code-graph development tool, not the runtime narrative Knowledge Graph. Vector indexes and the narrative graph remain derived and rebuildable.

## Remaining technical specifications

00001 resolves the architectural direction for each subject below, but deliberately leaves quantitative, algorithmic, or physical-detail specification open. None may be completed by implementation assumption.

| ID | Resolved direction | Unresolved specification required |
|---|---|---|
| DEC-001 | Agents request capabilities; essential inference is local; model/provider coupling is avoided. | Concrete local-model selection and evidence from reference-hardware benchmarks. |
| DEC-002 | Models are replaceable capability providers and model use is subject to the approved explicit-resource bounds. | Whether/how loading, unloading, pinning, and failure handling are centralized, plus the exact lifecycle policy. |
| DEC-003 | Resource use is explicitly bounded and model concurrency must be managed. | RAM/VRAM budgets, scheduling, priorities, and quantitative concurrency limits. |
| DEC-004 | SQLite is the initial transactional authority; schemas are versioned and normalized where queryability requires it. | Physical tables, indexes, constraints, relationships, and migrations. |
| DEC-005 | Canonization uses four impact levels with centralized classification, consistency validation, and structural approval. | Quantitative impact thresholds and detailed classification/approval algorithms. |
| DEC-006 | Materialization, promotion, demotion, and consolidation preserve entity existence, identity, totals, and continuity. | Quantitative tier metrics, thresholds, cadence, and transition policies. |
| DEC-007 | Operations are bounded and must pause/resume safely without discarding events. | Event, causal-depth, LLM-call, token, retry, and time-budget values and enforcement algorithms. |
| DEC-008 | A universal temporal mechanism preserves history while worlds configure temporal metaphysics and conflict policy. | Per-world paradox/conflict policies and deterministic resolution detail. |
| DEC-009 | Canonical descriptions and generated assets remain distinct; lifecycle and provenance are traceable. | Retention, versioning, archiving, deduplication, and removal policies. |
| DEC-010 | Narrative quality is evaluated for continuity, coherence, epistemology, causality, and literary behavior. | Metrics, reproducible scenarios, benchmarks, thresholds, and regression evaluation. |
| DEC-011 | Combat is resolved by a dedicated Combat Resolution Engine, with Health handling physical/medical conditions. | Detailed tactical formulas, action economy, initiative, damage, and world-specific mechanics. |
| DEC-012 | Events use the approved envelope and deterministic ordering; conflicting state changes serialize safely. | Concrete scheduler, concurrency, interruption, tie-breaking, and conflict-resolution algorithms. |
| DEC-013 | Simulation Run, LLM Invocation, and Agent Proposal records support atomic, idempotent recovery. | Physical persistence mapping and the detailed recovery state machine. |

The approved architectural direction remains binding while these specifications are open.
