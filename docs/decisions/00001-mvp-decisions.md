# AETHER STORYTELLING SYSTEM
# 000001 — Architectural Decisions

**Document ID:** AETHER-DEC-000001  
**Document Type:** Foundational Decision Record  
**Status:** APPROVED  
**Scope:** Project-wide  
**Language:** English  
**Version:** 1.0

---

# 1. Purpose

This document establishes the foundational architectural, operational, and development decisions of the Aether Storytelling System.

It consolidates previously approved architectural decisions and resolves the outstanding ambiguities identified during architecture review.

This document is a foundational reference for:

- System architecture.
- Domain design.
- Software development.
- Agent responsibilities.
- Runtime behavior.
- Persistence and simulation.
- Technical documentation.
- Future architectural decisions.

All implementation work must comply with the decisions established here.

If a future implementation requires changing an approved decision, the change must be explicitly reviewed and documented.

# 2. General Project Decisions

## 2.1. Project Language

**English is the mandatory language for the entire project.**

This requirement applies to:

- Source code.
- Variable and function names.
- Class and module names.
- Package names.
- Repository structure and documentation.
- Architecture specifications.
- Markdown files.
- Agent definitions and instructions.
- Prompts and templates.
- Tests and test descriptions.
- Technical comments.
- Logs and internal system messages.
- Development artifacts.

All new project content must be written in English.

Existing material incorporated into the repository must be translated or adapted to comply with this rule.

This requirement must also be included in the repository's permanent agent and contributor instructions.

## 2.2. Software Engineering Principles

All code must follow:

- Clean Code.
- Domain-Driven Design (DDD).
- SOLID principles.
- Separation of Concerns (SoC).

These are mandatory engineering principles, not optional recommendations.

Implementation requirements:

1. Domain logic must remain independent of infrastructure concerns whenever applicable.
2. Business rules must not be duplicated across unrelated components.
3. Modules must have clear responsibilities and explicit boundaries.
4. Dependencies must be explicit and appropriately directed.
5. Abstractions must represent meaningful domain or technical responsibilities.
6. Avoid unnecessary coupling between packages.
7. Avoid premature complexity and abstractions without a demonstrated purpose.
8. Maintainability and testability must be considered throughout implementation.

### Testing requirement

Every coded feature or modification must be tested after implementation.

The test strategy must include appropriate levels of:

- Unit tests.
- Integration tests.
- Contract tests.
- Regression tests.
- End-to-end tests, where applicable.

Existing tests must continue passing after changes.

A feature is not considered complete merely because its implementation compiles or appears to work.

Its expected behavior and potential regressions must be verified.

## 2.3. Monorepo Architecture

Aether must be developed as a monorepo.

The repository must be organized into independently identifiable packages or bounded contexts, with explicit responsibilities and dependencies.

### Package-level agent selection

The development environment must support selecting or assigning different coding agents locally for individual packages.

This means:

- Packages must have clearly defined boundaries.
- Each package must have its own development context.
- Package-specific instructions must be supported.
- Package-level testing must be possible.
- Agents must be able to work on individual packages without requiring the entire repository context.
- Cross-package contracts must be explicit.

The architecture must not assume that every package will always be developed by the same agent or model.

The monorepo must preserve system-wide architectural consistency while allowing independent package-level development.

## 2.4. Validated Architectural Documents

The following existing architecture documents are considered validated and approved for use:

- Document 03.
- Document 04.
- Documents 06 through 10.

These documents are accepted as architectural references and must be considered during implementation.

Their established decisions must not be silently reinterpreted, simplified, or discarded.

Any identified conflict with a newer approved decision must be documented and resolved explicitly.

# 3. Foundational Operational Profile

## 3.1. Local-First Architecture

**Local-first execution is mandatory in the current development stage.**

All essential Aether functionality must operate locally without requiring external APIs, cloud services, or remote inference providers.

The initial architecture must support:

- Local language model inference.
- Local persistence.
- Local simulation.
- Local agent execution.
- Local asset management.
- Local image generation.
- Local application interfaces.

### Future external provider support

The architecture must allow users to optionally provide their own API keys and use external model providers in the future.

However:

- External providers are not required for current functionality.
- Essential system behavior must not depend on them.
- External inference must be optional.
- Model selection and agent logic must remain independent of provider implementations.

The initial local model strategy and operational profile are approved in:

`00002-model-decisions.md`

That document establishes the approved operational profile. Concrete model selections and quantitative resource policies still require benchmarking and dedicated specifications.

## 3.2. Operational Profile

Aether is a local-first, single-user, event-driven narrative simulation engine.

Its architecture combines:

- Transactional persistent state.
- Deterministic simulation.
- Specialized artificial intelligence capabilities.
- Explicit computational resource limits.
- Causal and temporal consistency.
- Recoverable execution.
- Configurable fictional world rules.

The engine remains the authority over the simulated world.

LLMs interpret, propose, reason, and generate content. The engine validates, applies, and persists changes.

## 3.3. Hardware Independence

The initial development environment serves as a performance reference, not as a permanent architectural limitation.

The system must support future hardware improvements and alternative execution environments without requiring fundamental changes to its domain architecture.

---

# 4. Approved Architectural Decisions

## 4.1. Temporal Advancement and World Autonomy

**Decision: World autonomy and temporal advancement authorization are separate concerns.**

The world may have independent actors, goals, plans, scheduled events, and causal processes.

However, world autonomy does not authorize the simulation clock to advance independently.

The world advances only through an explicitly authorized operation.

The following temporal operations must be supported:

| Operation | Responsibility |
|---|---|
| `AdvanceTime` | Advances the world by a specified duration |
| `AdvanceUntil` | Advances until a specified event, condition, or temporal limit |
| `PauseSimulation` | Stops temporal advancement |

### Player modes

- **Player Character:** Actions consume world time according to their resolved duration.
- **Narrative Protagonist:** The Game Master interprets intentions and proposes action duration; the engine validates and applies it.
- **Observer:** The user explicitly authorizes temporal advancement through observation controls or equivalent commands.

NPC autonomy and world simulation continue during authorized intervals, regardless of the player's narrative focus.

The simulation must never advance time simply because an NPC has an active plan or a scheduled event exists.

## 4.2. Universal Rules Framework and World-Specific Rulesets

**Decision: Aether provides a universal mechanical framework, while each universe defines or selects its own Ruleset.**

The Universal Rules Framework provides common mechanisms for:

- Attributes and capabilities.
- Skills and specializations.
- Tests and difficulties.
- Modifiers.
- Resources.
- Conditions.
- Character progression.
- Combat resolution.
- Consequences.

It does not impose one universal mechanical formula on every universe.

### Storytelling Ruleset

The approved Storytelling-inspired mechanics constitute the first reference Ruleset.

They are not mandatory rules for every future universe.

The first world may adopt this Ruleset as its default mechanical implementation.

Other universes may implement different mechanics while respecting the Universal Rules Framework contracts.

### Mechanical authority

LLMs must never invent or independently modify mechanical formulas.

Mechanical calculations and rule resolution belong to the active Ruleset and its deterministic execution mechanisms.

Previously approved NPC creation and progression rules remain valid for the initial Storytelling implementation.

## 4.3. Canonization of Inferred Details

**Decision: Canonization uses four levels of impact and a centralized validation mechanism.**

Generated or inferred details are not automatically canonical.

The Canonization Engine determines whether a detail may become part of the persistent world.

### Canonization levels

| Level | Classification | Policy |
|---|---|---|
| 0 | Ephemeral detail | Exists only during response construction |
| 1 | Contextual detail | May be automatically canonized |
| 2 | Persistent local fact | Requires automatic consistency validation |
| 3 | Structural change | Requires explicit approval |

Examples:

- Level 0: Temporary lighting description.
- Level 1: Minor decoration in an established tavern.
- Level 2: A recurring merchant with persistent identity and history.
- Level 3: Creation of a city, faction, religion, or major historical event.

### Authority

- The Narrator may suggest details.
- The Context Builder may identify opportunities for contextual expansion.
- The Canonization Engine classifies and validates proposed content.
- The deterministic engine records approved canonization.
- The user approves changes classified as structural.

### Canonical records

Every persistent canonical detail must preserve:

- Origin.
- Responsible agent or author.
- Creation timestamp.
- Source event or justification.
- Canonization level.
- Related entity references.
- Modification history.

Canonized details must not be silently deleted when contradicted.

Corrections, revisions, and invalidations must preserve historical traceability.

### Impact classification

Impact must be evaluated according to potential consequences, not merely the apparent size of a narrative detail.

A seemingly minor detail may have structural consequences.

For example, a door is a contextual detail until it provides access to a secret location or changes the political balance of a fortress.

## 4.4. Entity Materialization and Simulation Tiers

**Decision: Promotion and demotion between simulation tiers must preserve entity continuity and use explicit materialization and consolidation mechanisms.**

A population or aggregate is not necessarily a collection of fully instantiated individual characters.

Promotion must not invent arbitrary personal histories or duplicate population members.

### Entity Materialization

When an aggregate requires individual representation, the system must:

1. Identify the source aggregate.
2. Determine which individuals need materialization.
3. Retrieve existing identities when available.
4. Create compatible individual identities when necessary.
5. Derive individual characteristics from the aggregate's established properties.
6. Associate relevant historical events.
7. Preserve collective totals and properties.
8. Record the relationship between materialized individuals and their source aggregate.

Example:

A garrison of forty soldiers exists as a Tier 3 population.

When the player begins interacting with one specific soldier, the system materializes that individual with characteristics consistent with the garrison.

The soldier must not receive an invented personal history that contradicts established events.

### Aggregate continuity

Materialized individuals must be accounted for separately from the remaining aggregate to prevent duplication.

### Demotion

Demotion changes simulation resolution, not character existence.

The system must preserve:

- Identity.
- Current state.
- Relevant individual history.
- Important relationships.
- Active goals and plans.
- Significant event participation.

Characters may receive less frequent individual simulation without losing their identities or continuity.

### Simulation tiers

- Tier 1: Deep individual simulation.
- Tier 2: Abstract individual simulation.
- Tier 3: Collective or statistical simulation.

Promotion and demotion criteria will be defined through quantitative operational policies.

## 4.5. Event Ordering and Concurrency

**Decision: Event execution uses deterministic ordering and controlled concurrency.**

Event ordering must consider:

1. In-world occurrence time.
2. Causal dependencies.
3. Operational priority.
4. Deterministic sequence as a final tie-breaker.

The engine, not the LLM, assigns event sequence identifiers.

### Event envelope

Every event must support a common envelope containing:

- `event_id`
- `world_id`
- `timeline_id`
- `occurred_at`
- `recorded_at`
- `sequence`
- `event_type`
- `source_type`
- `source_id`
- `caused_by`
- `priority`
- `payload_version`
- `payload`

### Simultaneous events

Events may occur at the same in-world timestamp.

Independent events may be processed within the same logical processing window.

Events competing for the same resources or modifying conflicting state must be serialized according to deterministic rules.

Concurrency must never allow logically impossible outcomes, such as two characters acquiring the same unique item.

### Interruptions

The engine must support three operational interruption classes:

| Priority | Behavior |
|---|---|
| Critical | Interrupts immediately when required by the event's consequences |
| Relevant | Interrupts at the next safe action boundary |
| Ordinary | Waits until the action completes or reaches its next evaluation point |

Examples:

- An ambush may interrupt travel.
- An urgent message may interrupt a conversation.
- An unrelated background event does not automatically interrupt every player activity.

Operational processing priority must not rewrite fictional chronology.

### Scheduler modifications

Future scheduled events may be rescheduled, cancelled, or replaced.

Scheduler modifications must preserve their history.

Only events that actually occur may be recorded as completed events in the Event Ledger.

## 4.6. Physical Event Data Model

**Decision: Event persistence uses a normalized common envelope with versioned event-specific payloads.**

The Event Ledger is the authoritative historical record.

The physical data model must avoid both:

- A single oversized table containing every possible event-specific field.
- An entirely opaque JSON-based event store without queryable common structures.

### Event Ledger

The main event record contains common indexed fields and a versioned payload.

Event-specific structures may be normalized when they require frequent queries or relationships.

Examples include:

- Event participants.
- Event location.
- Affected entities.
- Causal relationships.
- Asset references.

### Payload versioning

Every payload must identify its schema version.

Historical events must remain readable after structural changes.

The system must provide adapters or migrations for older payload versions.

### Snapshots

Snapshots represent the world state at a particular point in a timeline.

They are used for:

- Recovery.
- Faster state loading.
- Checkpoints.
- State comparison.
- Simulation resumption.

Snapshots do not replace the Event Ledger.

Every snapshot must identify:

- Timeline.
- Event Ledger position.
- Schema version.
- Relevant system versions.
- Integrity hash or equivalent verification mechanism.

### Authority

The Event Ledger is the authoritative historical source.

Snapshots and derived indexes are supporting mechanisms.

## 4.7. LLM Invocation and Simulation Recovery

**Decision: Simulation execution, LLM invocations, and agent proposals must have separate persistent records associated through a common `simulation_run_id`.**

The system must not assume that LLM inference is transactional or deterministic.

Three principal records are required:

### Simulation Run

Represents a complete simulation execution.

It must preserve:

- `simulation_run_id`
- Initial state or snapshot reference.
- Execution status.
- Processed events.
- Validated results.
- Final state.
- Recovery information.

### LLM Invocation

Represents an individual model request.

It must preserve:

- `invocation_id`
- `simulation_run_id`
- Requesting agent.
- Requested capability.
- Model and model version.
- Prompt version.
- Context hash.
- Inference parameters.
- Raw response or persistent response reference.
- Invocation status.
- Token usage.
- Timestamps.

### Agent Proposal

Represents an interpreted result from an invocation.

It must preserve:

- `proposal_id`
- `simulation_run_id`
- `invocation_id`
- Proposal type.
- Structured payload.
- Validation status.
- Rejection reason, when applicable.
- Application result.

### Recovery behavior

- Completed responses must be reusable when their context and versions remain valid.
- Incomplete invocations may be retried.
- Committed effects must never be applied twice.
- Narrative generation failure after simulation commit must not repeat world simulation.
- Actual model responses used by the system must be preserved.

The system must never assume that repeating an LLM request produces the same response.

## 4.8. Combat Resolution

**Decision: Combat is implemented as a dedicated subsystem integrated with the Universal Rules Framework.**

The subsystem is named `Combat Resolution Engine`.

It is responsible for tactical conflict resolution.

The Health System remains responsible for physical and medical character conditions.

### Combat responsibilities

The Combat Resolution Engine must support:

1. Combat initiation and termination.
2. Participants and opposing sides.
3. Initiative and resolution order.
4. Offensive and defensive actions.
5. Reactions and interruptions.
6. Distance and positioning.
7. Environmental and situational modifiers.
8. Mechanical resolution.
9. Application of consequences.
10. Victory, defeat, surrender, and escape conditions.

### Separation of responsibilities

- Combat Resolution Engine: Determines mechanical combat outcomes.
- Health System: Determines resulting physical and medical conditions.
- Character Progression Engine: Evaluates long-term consequences such as trauma, injury-related limitations, and learning.
- Narrator: Presents the resulting events.

### World-specific rules

Each universe defines or selects its combat mechanics, including:

- Formulas.
- Power scales.
- Action categories.
- Damage types.
- Combat resources.
- Initiative rules.
- Victory conditions.
- Defeat consequences.

The initial Storytelling Ruleset may implement Storytelling-inspired combat mechanics.

The Universal Rules Framework must not require every universe to use the same combat model.

Detailed combat formulas and tactical rules require a dedicated specification.

## 4.9. Character Knowledge, Player Knowledge, and Narrative State

**Decision: Character Knowledge, Player Knowledge, and Narrative State are separate persistent domains with different responsibilities.**

### Character Knowledge

Belongs to an individual character.

It records information acquired through:

- Perception.
- Communication.
- Investigation.
- Deduction.
- World-specific supernatural or exceptional abilities.

Character Knowledge may be incomplete, inaccurate, outdated, or false.

### Player Knowledge

Belongs to the player's experience.

It records information actually presented and discovered during gameplay.

Examples include:

- Revealed facts.
- Known rumors.
- Encountered characters.
- Visited locations.
- Witnessed events.
- Discovered narrative information.
- Important revelations.

Player Knowledge supports continuity, consultation, and experience recovery.

It does not determine what the protagonist knows and must not restrict player actions.

### Narrative State

Represents the current presentation and scene-continuity context.

It may contain:

- Current scene.
- Narrative location.
- Present characters.
- Perspective.
- Tone.
- Pacing.
- Conversation subject.
- Dialogue continuity.
- Temporary presentation elements.

Narrative State is not an authoritative source of world truth.

### Presentation lifecycle

A narrative presentation follows three stages:

1. **Presentation:** The Narrator generates content.
2. **Confirmation:** The system records the content actually delivered to the player.
3. **Extraction:** Relevant information is routed to the appropriate knowledge or continuity domains.

Content generated but not successfully delivered must not be registered as a player discovery.

### Epistemic separation

The same fact may exist simultaneously in different forms:

- The World State contains the objective truth.
- Character Knowledge contains what the protagonist knows or believes.
- Player Knowledge contains what the player has discovered.
- Narrative State contains what is needed to maintain presentation continuity.

These domains must never be implicitly conflated.

## 4.10. Technology Stack and Architecture Decision Records

**Decision: The initial technology stack is a preferred reference implementation, subject to technical validation and explicit Architecture Decision Records (ADRs).**

Initial reference stack:

| Layer | Preferred technology |
|---|---|
| Backend | Python |
| API | FastAPI |
| Validation and contracts | Pydantic |
| Persistence | SQLite |
| ORM | SQLAlchemy |
| Database migrations | Alembic |
| Frontend | React + TypeScript |
| Local inference | llama.cpp |
| Model format | GGUF, when compatible |
| Image generation | ComfyUI |
| Backend testing | pytest |
| Frontend testing | Appropriate TypeScript testing tools |

### Technology adoption criteria

Each technology must be evaluated against:

- Local execution compatibility.
- Maturity and stability.
- Maintainability.
- Performance on reference hardware.
- Compatibility with architectural contracts.
- Testability.
- Operational complexity.
- Dependency footprint.

### Architecture Decision Records

Significant technology decisions must be documented through ADRs.

Each ADR must contain:

- Context.
- Problem.
- Considered alternatives.
- Decision.
- Justification.
- Consequences.
- Review criteria.

Technologies may be replaced without changing the domain architecture, provided the implementation preserves established contracts.

---

# 5. Universal Architectural Guarantees

The following guarantees apply across all worlds, agents, and subsystems.

1. The engine remains authoritative over persistent world state.
2. LLMs cannot bypass deterministic validation.
3. Essential functionality must operate locally in the current development stage.
4. World time advances only through explicit authorization.
5. Historical events must remain traceable.
6. Simulation execution must be recoverable.
7. Event processing must preserve causal consistency.
8. Character knowledge must remain epistemically isolated.
9. Agent logic must remain independent of model implementations.
10. Simulation tiers change computational resolution, not entity existence.
11. Generated details must not become canonical without the appropriate canonization process.
12. Mechanical rules must be resolved by the active Ruleset.
13. Assets and canonical descriptions must remain distinct.
14. Resource consumption must have explicit operational limits.
15. All coded changes must be tested for expected behavior and regressions.

# 6. World-Specific Configuration

Universal engine contracts must not impose identical fictional rules on every universe.

Each world may define or configure:

- Metaphysical rules.
- Temporal policies.
- Paradox resolution.
- Mechanical Rulesets.
- Combat systems.
- Knowledge limitations.
- Canonization thresholds.
- Character progression.
- Biological systems.
- Death and survival conditions.
- Power systems.
- Simulation-specific policies.

The engine provides the mechanisms for representing, validating, and executing these rules.

The world defines its fictional behavior.

# 7. Remaining Technical Specifications

The decisions in this document establish architectural direction.

The following details still require dedicated technical specifications:

| ID | Subject | Expected deliverable |
|---|---|---|
| DEC-001 | Local model selection | Model selection and benchmark |
| DEC-002 | Model lifecycle | Loading and unloading policy |
| DEC-003 | Resource concurrency | RAM/VRAM budgets and scheduling |
| DEC-004 | Physical database schema | Tables, indexes, migrations |
| DEC-005 | Canonization thresholds | Quantitative impact criteria |
| DEC-006 | Simulation tier thresholds | Promotion and demotion metrics |
| DEC-007 | Simulation budgets | Cycle, causal-depth, and LLM-call limits |
| DEC-008 | Temporal conflict resolution | World-specific paradox policies |
| DEC-009 | Asset lifecycle | Retention and versioning |
| DEC-010 | Narrative quality | Metrics, benchmarks, regression tests |
| DEC-011 | Combat mechanics | Detailed tactical and mechanical rules |
| DEC-012 | Event concurrency | Concrete scheduling and conflict-resolution algorithms |
| DEC-013 | Recovery implementation | Physical persistence and recovery state machine |

These specifications must remain consistent with the decisions established in this document.

# 8. Change Management

Approved decisions must not be modified implicitly during implementation.

Any proposed change must:

1. Identify the affected decision.
2. Explain the motivation.
3. Describe the architectural consequences.
4. Identify affected packages and contracts.
5. Include alternatives when applicable.
6. Be explicitly approved.
7. Update the relevant decision record and dependent specifications.

Implementation agents may identify architectural improvements and propose changes, but must not silently redefine approved requirements.

# 9. Final Status

This document consolidates the foundational project decisions and resolves the ten previously identified architectural ambiguities.

It establishes the initial operational, development, simulation, persistence, and domain contracts of the Aether Storytelling System.

**Document status: APPROVED**

**Implementation rule:** All development agents must read and comply with this document before implementing or modifying project components.