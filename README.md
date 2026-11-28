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
Public information, creative expression, leisure, and visual/sonic identity are
recorded in `docs/architecture/adr/0012-public-culture-and-multimodal-identity.md`.
Canonical detail proposals and non-destructive revision/invalidation history are
recorded in `docs/architecture/adr/0013-canonical-detail-governance.md`.
Resource-ledger consequences are recorded in
`docs/architecture/adr/0006-resource-ledger-and-plan-consequences.md`.
Organizations are first-class autonomous actors with distinct membership,
governance, formal authority, effective influence, internal goals, and shared
resource permission validation. Their plan steps produce off-screen
consequences only while an authorized temporal interval is processed. These
contracts fulfill validation 12 and are recorded in
`docs/architecture/adr/0007-organizations-as-autonomous-actors.md`.

The Phase 4 geography and mobility slice provides hierarchical semantic
locations, separate formal/effective ownership and control claims,
infrastructure nodes/facilities, and explicit-distance/duration/cost route
segments. Journeys reserve configured resources and schedule arrival without
advancing the clock; a later authorized temporal operation processes arrival,
position, resources, and Event Ledger state atomically. Off-screen travel is
not automatically disclosed as Character or Player Knowledge. Validations 13
and 26 are recorded in
`docs/architecture/adr/0008-geography-territory-infrastructure-and-mobility.md`.

The Phase 5 biology, ecology, demography, and health slice provides configurable
species/natures, ordered lifecycle stages, aggregate decimal-count populations
and cohorts, habitats, ecological processes, and condition-based character
health. Health keeps biological integrity, consciousness, action ability, and
fighting ability separate from psychological state and combat outcomes.
Explicitly configured `population-change`, `ecological-process`, and
`health-condition-change` events apply only during authorized temporal
operations, with atomic ledger updates and no invented rates or formulas.
Validations 15, 20, and 21 are recorded in
`docs/architecture/adr/0009-ecology-demography-and-health.md`.

The next Phase 5 slice implements explicit knowledge and technology lifecycle
states, conditions, and immutable lifecycle evidence; languages, dialects,
writing systems, semantic character proficiency, and optional transmission
language metadata; education programs, participation, and explicit assessment
records; and traditions, individual belief, ritual completion, and isolated
world metaphysical truth. `knowledge-transmission`,
`technology-use-completion`, `learning-assessment`, and `religious-ritual`
events execute only during authorized temporal operations. This slice
implements validations 16-19 without adding automatic mastery, universal
learning or linguistics models, religious truth, discovery algorithms, or
quantitative quality formulas. See
`docs/architecture/adr/0010-knowledge-language-education-and-belief.md`.

The normative and strategic Phase 5 slice adds persisted normative systems,
rules, rights/duties, jurisdiction, cases, filtered evidence, proceedings,
sanctions and appeals; directional organization relations and treaty
lifecycle; explicit semantic strategic conflict factors and non-linear stages;
and security threats, incidents, intelligence operations and non-combat
resolutions. Formal organization authority and actor location are rechecked
when explicitly supplied legal, treaty, escalation, investigation, or security
events are processed during an authorized temporal interval. See
`docs/architecture/adr/0011-normative-diplomacy-strategy-and-security.md`.

The Phase 3 Character Genesis and Progression slice is recorded in
`docs/architecture/adr/0014-character-genesis-and-progression.md`. It provides
world-supplied category names, deterministic validation of the approved
Storytelling 5/4/3, 11/7/4, three-specialization, seven-Merit distribution, and
event-evidenced explicit positive or negative progression. Progression is
version checked, idempotent, and preserves immutable before/after history
without selecting a universal XP formula or rewriting identity, personality,
or psychological state.

The adaptive-resolution slice is recorded in
`docs/architecture/adr/0015-simulation-tiers-and-materialization.md`. It
provides explicit, version-checked Tier 1/2/3 transitions, caller-supplied
population materialization, aggregate-member accounting, duplicate prevention,
and non-destructive consolidation. It intentionally does not select the
quantitative promotion or demotion thresholds left open by DEC-006.

The culture and collective-identity slice is recorded in
`docs/architecture/adr/0016-culture-society-and-collective-identity.md`.
It persists historical culture definitions, semantic social groups separate
from organizations, heterogeneous individual affiliations, visibility-filtered
character context, and immutable event-tied cultural change history. It
implements validation 14 without automatic cultural change, behavioral
determinism, sociology formulas, or a universal class hierarchy.

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

## Local model benchmark

DEC-001/002/003 are intentionally unresolved until a local candidate is
benchmarked on the reference hardware. Start Ollama or a local
OpenAI-compatible server, provide an installed model, and run:

```bash
python -m tools.model_benchmark \
  --runtime ollama \
  --base-url http://127.0.0.1:11434 \
  --model MODEL_NAME \
  --output benchmark-results/result.json
```

The benchmark records correctness gates, hidden-fact leakage, latency, and
VRAM use. No model, lifecycle policy, or concurrency limit is selected by the
harness.

## Documentation integrity

This package was reconstructed from available project decisions and records. Where the original wording or exact historical numbering could not be recovered in full, this is stated in the record itself. Do not turn editorial reconstructions into new product decisions without project-owner approval.
