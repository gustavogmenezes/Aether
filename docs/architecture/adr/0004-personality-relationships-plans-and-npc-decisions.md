# ADR 0004 — Personality, Relationships, Plans, and NPC Decision Proposals

## Context

Phase 3 follows Character Knowledge and Communication. Approved validations 03,
06, 07, 08, and 09 require contextual NPC autonomy, psychological dimensions that
remain distinct, directional relationships, persistent goals and plans, and
epistemically filtered decisions.

## Problem

NPC decisions must use only a character-specific context while remaining
deterministic and non-mutating during proposal. The proposal must be separately
validated and persisted, and a plan step may enter the scheduler only when its
supplied prerequisites are present.

## Considered alternatives

- Give the NPC decision component direct repository or World State access.
- Store personality, current emotion, and identity as one mutable record.
- Collapse relationships to one symmetric affinity score.
- Materialize an intended plan step directly in the Event Ledger.
- Treat a deterministic proposal as an LLM invocation.

## Decision

Persist identity, personality, and psychological/emotional state as distinct
versioned records with provenance. Personality contains semantic traits, values,
and tendencies without a universal numeric scale. Psychological state records
current emotions and behavioral modes independently from identity and personality.

Relationships are unique by source and target character. Dimensions are named,
semantic, and optional; no inverse relationship is inferred.

Motives explain desire, goals describe desired outcomes and optional hierarchy,
plans identify an approach to a goal, and plan steps hold explicit capability,
resource, and knowledge prerequisites. Each persisted record has explicit status
and provenance.

The NPC Decision port accepts one frozen `NpcDecisionContext`. The context is
assembled by the caller and may contain only supplied identity, personality,
psychological state, filtered knowledge, capabilities, resources, motives, goals,
plans, outgoing relationships, and circumstances. It exposes no repository or
World State interface.

The deterministic engine returns a proposal with reaction, decision type, target
step, rationale, required resources, confidence, and validation requirements. It
does not mutate state or schedule events.

`NpcDecisionService` validates and persists the proposal outside the decision
port call. Reusing a request ID with the same canonical context replays the
stored proposal; another context is rejected. Scheduling a validated step opens
a short transaction, rechecks explicit prerequisites and current plan-step state,
marks the step scheduled, and appends one pending scheduled event atomically.
Scheduling never advances the clock.

Deterministic proposals have their own persistent decision record. They are not
misrepresented as LLM Invocation records because no model invocation occurs.
Future model-backed adapters remain behind the same port and, when used, must
also persist approved invocation/proposal records under ADR 0001/00001 recovery
contracts.

## Consequences

- Different characters can hold contradictory directional relationships.
- Current emotional or behavioral state can change without rewriting identity
  or personality.
- Decision behavior remains explainable and reproducible for the supplied
  context.
- An agent cannot acquire objective facts merely by reading storage.
- Missing capability, resource, or knowledge prerequisites reject scheduling
  without partially creating an event.
- Plans remain persistent intentions. Only authorized temporal processing may
  turn their scheduled intentions into occurred events.

## Traceability

This decision implements approved validations 03, 06, 07, 08, and 09 and
cross-system contracts C1-C5, C8-C9, C13, and C16. It does not select an LLM
runtime, resource policy, universal personality scale, or quantitative
relationship model.
