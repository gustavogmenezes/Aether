# ADR 0005 — Worldwide Autonomous Simulation

## Context

Approved contracts require NPC goals and plans to continue during authorized temporal intervals regardless of protagonist focus. A scheduled event is an intention and enters the Event Ledger only when its occurrence is processed.

## Problem

The temporal engine must resolve scheduled NPC plan steps without granting agents direct World State access or advancing time merely because a plan exists.

## Decision

Add a replaceable `ScheduledEventResolverPort`. The resolver is deterministic and pure: it receives one scheduled event and an explicitly supplied plan step, then returns completion, failure, or unchanged outcome plus the authoritative ledger payload.

For NPC plan-step events, the application layer:

1. Loads the referenced plan step and owning plan.
2. Validates event, character, plan, and step ownership.
3. Validates that the step is still scheduled.
4. Calls the resolver outside repository ownership rules.
5. Applies completed or failed plan-step state.
6. Persists the resolved outcome in the event payload.
7. Marks the scheduled intention completed and advances the clock atomically.

Unknown scheduled event types pass through unchanged and remain available for specialized resolvers in later domains.

The resolver never reads a repository, invokes an LLM, or advances world time. The temporal service processes only events due inside an explicitly authorized `AdvanceTime` or `AdvanceUntilEvent` interval.

Plan failure remains an occurred attempt in the Event Ledger. The scheduled intention is completed because it was processed, while the referenced plan step is marked failed with an auditable reason.

## Consequences

- NPC plans produce off-screen consequences during authorized intervals.
- World autonomy is decoupled from narrative focalization and disclosure.
- Event, plan-state, and clock changes commit together.
- Resolver errors roll back all consequences and preserve a failed Simulation Run record.
- Replaying a completed Simulation Run does not repeat plan outcomes.
- Specialized organizational, economic, ecological, and conflict resolvers can be added behind the same handler boundary.

## Review criteria

Revisit when consequence graphs create multiple follow-up events, when interruption policies require partial intervals, or when a world-specific Ruleset needs nondeterministic or model-proposed resolution.
