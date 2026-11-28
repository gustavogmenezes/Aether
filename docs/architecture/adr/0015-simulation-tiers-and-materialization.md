# ADR 0015 — Explicit Simulation Tiers and Materialization

## Context

Approved decision 4.4, validation 31, and cross-system contracts C7 and C10
require continuity when an aggregate is materialized or an individual changes
simulation resolution. DEC-006 still leaves quantitative promotion and demotion
metrics open.

## Problem

Tier transitions must be explicit, durable, idempotent, and free of invented
identity or biography. Population materialization must not duplicate members or
lose aggregate/cohort continuity. Consolidation must not erase character
identity, state, history, relationships, goals, or plans.

## Decision

Introduce Tier 1, Tier 2, and Tier 3 state contracts with explicit resolution
reason and immutable provenance. Every transition carries a request ID, target,
expected versions, explicit reason, and a persisted result. Replay of an
identical request returns the persisted result; a conflicting payload for the
same request ID is rejected.

Materialization accepts caller-supplied character IDs, counts, character
identity, compatible traits, optional source constraints, cohort, and Event
Ledger history references. The deterministic engine checks the population,
world, version, cohort, lifecycle stage, species, location, available count,
and supplied identity. It never synthesizes identity, biography, or history.
One persistent individual-to-aggregate link is permitted per character.

The aggregate population and cohort `count` remain authoritative total
counts. A source accounting link records the materialized count, making
remaining aggregate count equal to total count minus materialized members.
Source links, individual links, Tier state, and request result are committed
atomically. Materialization does not modify population existence.

Promotion, demotion, and consolidation operate only on existing Tier state.
They version-check the state and replace only tier, resolution reason, and
provenance. No repository or service operation deletes or rewrites character
identity, current state, history links, relationships, goals, plans, or
participation records.

Migration 0015 creates:

- `simulation_tier_states`;
- `aggregate_population_source_links`;
- `materialized_individual_links`;
- `simulation_tier_transition_results`.

## Consequences

- Tier changes happen only after an explicit caller request.
- No thresholds, scores, proximity formulas, relevance policy, or automatic
  promotion/demotion criteria are selected under this ADR.
- Aggregate count and materialized-member accounting remain compatible and
  auditable.
- Existing identity is reused only when it exactly matches caller-supplied
  identity; different reuse attempts are rejected.
- Optimistic state and population versions reject stale requests.

## Traceability

This decision implements approved decision 00001 section 4.4 and validation
31. It preserves cross-system contracts C3, C4, C5, C7, C9, C10, C12, and C16.
DEC-006 remains unresolved by design.
