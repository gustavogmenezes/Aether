# ADR 0006 — Resource Ledger and Plan Consequences

## Context

Validation 11 requires material, social/human, structural, and personal resources to constrain NPC and organization plans. Worldwide autonomous simulation already resolves scheduled plan steps during authorized temporal intervals.

## Problem

NPC plan execution must consume and produce persisted resources without relying on universal prices, economy formulas, or unvalidated semantic availability.

## Decision

Add a resource ledger with:

- Resource balances owned by characters or organizations.
- Decimal quantities and reserved quantities.
- Resource categories for material, social, structural, and personal resources.
- Immutable resource transactions linked to scheduled events, occurred events, and simulation runs.
- Explicit reservations for scheduled consumption.

Plan steps retain semantic resource requirement names for compatibility and may additionally declare quantity-bearing resource effects. Each effect specifies a resource code, signed decimal delta, and the outcome on which it applies: completed or failed.

When a plan step is scheduled:

1. The maximum possible consumption for each resource code across possible outcomes is reserved.
2. The Event Scheduler entry, plan-step state, and reservations commit in one short transaction.
3. The process does not advance world time.

When the event occurs:

1. The selected completed/failed outcome determines the applied effects.
2. Consumption uses its reservation.
3. Production increases the owner balance.
4. Unused reservations are released.
5. Immutable resource transactions, plan state, event outcome, and clock update commit together.

Negative balances and stale resource-result quantities are domain errors. A replay uses the completed Simulation Run and cannot repeat transactions because scheduled-event/resource-code uniqueness and idempotency records are preserved.

## Consequences

- Resource constraints influence actual scheduled consequences rather than existing only in narrative text.
- Resource effects remain world-configurable; no universal price or economy model is introduced.
- Organizations use the same owner abstraction as characters.
- Caller-supplied semantic resource availability can still be used for low-detail plans, while quantity-bearing effects require persisted balances.
- Failures remain capable of consuming resources when explicitly configured.
- More complex transfers, trading, reserves by aggregate populations, and economic price formation remain later specifications.

## Review criteria

Revisit for organization-specific authority, multi-owner transfers, spoilage, composite inventories, loans, recurring costs, or high-volume statistical resource models.
