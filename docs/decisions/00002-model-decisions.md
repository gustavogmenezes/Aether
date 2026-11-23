# MODEL DECISIONS
# Reference Operational Profile

**Identifier:** AETHER-ARCH-OPR-001  
**Type:** Architectural specification  
**Status:** APPROVED  
**Scope:** Foundational operational contract of the engine

---

## 1. Purpose

Establish the fundamental operating conditions under which the Aether Storytelling System will be designed and executed.

This document defines the principles that will guide decisions related to:

- Infrastructure and local execution.
- Language model management.
- Concurrency and computational resource allocation.
- Data persistence and integrity.
- Content canonization.
- NPC abstraction and promotion.
- Processing and simulation limits.
- Temporal consistency.
- Asset management.
- Narrative-quality evaluation.

The purpose is to establish a common architectural foundation and avoid isolated or contradictory technical decisions across subsystems.

## 2. Foundational Operational Contract

Aether will be a local-first, single-user, event-driven narrative simulation engine, with persistent transactional state, deterministic execution as authority, and artificial intelligence as a specialized computational capability subject to explicit resource and execution limits.

This contract establishes five fundamental commitments.

### 2.1. Local-first

Aether’s essential functionality must operate locally, without dependence on external services or remote APIs.

External integrations may exist as optional features, but they may not be requirements for the system’s fundamental operation.

### 2.2. Resource-bounded

No operation may consume computational resources or processing time indefinitely.

Inference, simulation cycles, causal processing, content generation, and concurrent operations must have explicit limits.

### 2.3. Deterministic Core

The simulation engine will control the world’s official state.

Language models may interpret situations, propose decisions, generate content, and suggest changes, but they will not have unrestricted authority to modify persistent state directly.

Changes must pass through the engine’s validation and application mechanisms.

### 2.4. Event-driven

World evolution will be driven by events, actions, consequences, and temporal processing.

The engine must preserve the causal order of events and allow multiple event chains to execute within a simulation cycle.

### 2.5. Reproducible and Recoverable

Decisions, events, state changes, and content versions must be traceable.

Interrupted operations must have recovery mechanisms, preventing duplicated effects, loss of integrity, or inconsistency across subsystems.

Exact reproduction of an execution will not be assumed when inference is nondeterministic. In such cases, the results actually used, their relevant contexts, and their versions must be preserved.

---

## 3. Reference Hardware Profile

Initial development will use the following environment as a performance reference:

| Component | Reference |
|---|---|
| Operating system | Omarchy / Arch Linux |
| GPU | NVIDIA RTX 3060 |
| VRAM | 12 GB |
| Inference | Local |
| Model format | GGUF, where compatible |
| Inference runtime | llama.cpp |
| Image generation | ComfyUI |
| Execution architecture | Local-first |

This profile represents the minimum reference environment for initial performance and feasibility tests.

**The architecture must not be coupled to this hardware.**

Aether must support more powerful equipment, different GPUs, greater memory availability, and alternative runtimes without requiring fundamental changes to its architectural contracts.

---

## 4. Architectural Consequences

The operational contract establishes the following guidelines for the principal technical domains.

### 4.1. Infrastructure and persistence

- SQLite will be the initial transactional authority for the system’s dynamic state.
- The physical database schema must be versioned.
- Structural changes must use explicit migrations.
- Assets will be stored in the local filesystem.
- Derived vector data and graphs must be rebuildable from their authoritative sources.
- Persistence must preserve referential integrity and consistency across operations.
- Write transactions must not remain open during LLM calls.
- Processes must use execution identifiers to enable recovery and duplicate prevention.

The physical definition of tables, indexes, relationships, and migration strategies will be derived from these guidelines.

### 4.2. Model management

The system must have a central model manager responsible for:

- Identifying available models.
- Loading and unloading.
- Memory control.
- Capability-based selection.
- Version management.
- Performance monitoring.
- Failure handling.
- Integration with the Model Router.

Agents must request capabilities rather than depend directly on specific model implementations.

Model loading must be centrally controlled to avoid unnecessary VRAM contention.

Final selection of local models will be performed through benchmarks on the reference hardware.

### 4.3. Concurrency and computational resources

Aether must have a central resource-management mechanism.

That mechanism must consider:

- Available RAM.
- Available VRAM.
- Loaded models.
- Inferences in progress.
- Image generation.
- Auxiliary operations.
- Task priority.
- Concurrency limits.

The execution policy must prevent multiple heavy operations from compromising system stability.

### 4.4. Canonization

The system must have mechanisms for transforming generated content into canonical content.

Low-impact details may be canonized automatically when they satisfy previously defined criteria.

Relevant-impact changes must undergo stricter validation.

Canonization must preserve:

- Compatibility with the world’s current state.
- Chronological consistency.
- Geographical consistency.
- Causal coherence.
- Universe-specific rules.
- Change history.

The definition of impact levels and quantitative approval criteria will be established in a dedicated specification.

### 4.5. NPC abstraction and promotion

The system will continue to use three simulation levels:

- Tier 1: high-relevance NPCs with deep individual simulation.
- Tier 2: secondary NPCs with abstract individual simulation.
- Tier 3: populations and background characters with collective or statistical simulation.

Promotion and demotion must occur dynamically.

Classification must consider factors such as:

- Narrative relevance.
- Proximity to the player.
- Participation in important events.
- Relationships with relevant characters.
- Potential causal impact.
- Recent activity.
- Need for individual decisions.

Promotion must preserve the character’s historical and behavioral continuity.

Quantitative classification criteria will be defined later.

### 4.6. Processing limits

Every simulation cycle must have an operational budget.

That budget must consider:

- Maximum number of processed events.
- Maximum causal-chain depth.
- Maximum number of LLM calls.
- Input- and output-token limits.
- Maximum processing time.
- Number of retries and recoveries.

When a limit is reached, the engine must stop or suspend processing safely, preserve pending events, and permit later resumption.

The system must not silently discard events merely to satisfy computational limits.

### 4.7. Temporal consistency

The engine must provide universal temporal infrastructure while preserving:

- Original history.
- Timelines.
- Branches.
- Causal events.
- Checkpoints.
- Change history.
- Relationships between events and their consequences.

Each universe may define its own temporal metaphysics.

Aether must provide mechanisms to represent and execute different policies, including:

- Fixed Timeline.
- Branching Timeline.
- Mutable Timeline.
- Paradox-Based Timeline.

Resolution of paradoxes and temporal conflicts will be determined by each universe’s specific rules, while the engine preserves internal historical integrity.

### 4.8. Asset management

The system must have a central asset-management policy.

It must account for:

- Persistent asset identity.
- Versioning.
- Change history.
- Relationships with characters, environments, and objects.
- References between versions.
- Retention.
- Archiving.
- Recovery.
- Controlled removal of unused versions.

An entity’s canonical representation must remain separate from its generated visual representations.

A generated image must not automatically replace the canonical description of its object or character.

### 4.9. Narrative quality

Aether must have mechanisms for evaluating narrative quality.

Evaluation must consider, among other factors:

- Narrative continuity.
- Character coherence.
- Epistemological fidelity.
- Causal consistency.
- Compatibility with world state.
- Dialogue quality.
- Literary quality.
- Naturalness of interactions.
- Preservation of personality.
- Absence of undue contradictions.

The system must have reproducible test scenarios, automated evaluations where applicable, and narrative regression mechanisms.

Literary quality must not be indiscriminately sacrificed for speed or resource economy.

---

## 5. Separation of Authority and Artificial Intelligence

The operational contract establishes a fundamental distinction.

### Deterministic engine

Responsible for:

- Validating rules.
- Applying changes.
- Controlling state.
- Persisting events.
- Performing calculations.
- Preserving causality.
- Managing resources.
- Ensuring integrity.

### Language models

Responsible for:

- Interpreting intentions.
- Analyzing contexts.
- Developing decisions.
- Proposing consequences.
- Building characters.
- Interpreting situations.
- Generating narrative content.
- Suggesting evolution.

The engine remains the authority over the simulated world.

No agent may bypass validation mechanisms through an LLM-generated response.

---

## 6. Per-Universe Configuration

The operational contract is universal, but it must not impose identical fictional rules on all worlds.

Each universe may configure:

- Metaphysical rules.
- Temporal policies.
- Knowledge limits.
- Canonization rules.
- Progression criteria.
- Biological rules.
- Power systems.
- Death and survival conditions.
- Abstraction and simulation policies.

The engine will provide execution, validation, and persistence mechanisms.

The universe will define permitted fictional behavior.

This separation must be preserved across all subsystems.

---

## 7. Open Items Derived from the Contract

The approved Reference Operational Profile establishes the foundation for detailing the following specifications.

| Identifier | Open item | Expected outcome |
|---|---|---|
| OPR-01 | Concrete local model | Model selection by capability and benchmark |
| OPR-02 | Load and unload policy | Central model manager |
| OPR-03 | RAM/VRAM concurrency | Resource budgeting and scheduling |
| OPR-04 | Database and migrations | Physical schema and versioning |
| OPR-05 | Automatic canonization | Impact and approval criteria |
| OPR-06 | Tier promotion and demotion | Quantitative metrics and thresholds |
| OPR-07 | Per-cycle limits | Operational simulation budget |
| OPR-08 | Paradoxes and conflicts | Configurable temporal policy |
| OPR-09 | Asset retention and versioning | Asset lifecycle |
| OPR-10 | Narrative quality | Metrics, benchmarks, and regression tests |

These specifications must respect the operational contract established in this document.

---

## 8. Evolution Principle

The Reference Operational Profile must operate as a stable architectural contract, but not as a permanent limitation on technological evolution.

New models, runtimes, equipment, and processing strategies may be incorporated.

However, changes must preserve the fundamental principles of:

1. Engine authority over world state.
2. Local execution of essential functionality.
3. Explicit resource control.
4. Causal and temporal consistency.
5. Traceable and recoverable persistence.
6. Separation among agents, capabilities, and models.
7. Configurability of each universe’s rules.

Any change that compromises these principles must be treated as a formal architectural change.

---

## 9. Approved Architectural Decision

Aether will be developed under a Reference Operational Profile that is local-first, single-user, event-driven, and bounded by computational resources.

Its architecture will combine deterministic execution, transactional persistence, and specialized inference by language models.

The engine will retain authority over world state, while agents use artificial intelligence for interpretation, decision, and narrative production, always respecting validation and execution contracts.

Current hardware will serve as a performance reference without establishing permanent architectural dependence.

**Document status: APPROVED**

**Implementation rule:** The operational contract established here is binding. Its derived technical specifications, including concrete model selection, resource budgets, and quantitative policies, still require benchmarking, dedicated specifications, or ADRs.
