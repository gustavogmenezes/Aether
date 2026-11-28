# ADR 0007 — Organizations as Autonomous Actors

## Context

Validation 12 requires organizations to remain first-class actors with their own
purpose, continuity, governance, goals, plans, resources, and internal
disagreement. Existing Phase 3 plan decisions and Phase 3.5 resource ledger
support characterize individual characters and organization-owned balances, but
organization decisions require a distinct actor model and authority boundary.

## Problem

Organizations cannot be treated as characters or as homogeneous collective
minds. Their plans may be carried out through members while their resources are
shared. Formal authority, effective influence, informal roles, and personal
memberships must remain distinguishable, and neither influence nor an informal
role may silently authorize a resource commitment.

## Decision

Persist organization identity, purpose, history, status, interests,
relationships, territory references, and recorded internal conflicts separately
from characters. Persist governance rules and named role definitions, active and
inactive memberships, formal and informal roles, semantic effective influence,
and explicit authority grants. Authority grants carry semantic permission codes;
no universal numeric authority scale is introduced.

Organization motives, goals, plans, and plan steps reuse the established
conceptual lifecycle and statuses but use organization identifiers in distinct
contracts and records. An organization is therefore not represented as a
character with a different label.

Resource permissions are explicit, world/configuration-defined codes. The
organization scheduler checks current persisted membership, a formal active role
grant, and permissions required by the step. Quantity-bearing effects also
require `consume-resource:<resource-code>` or
`produce-resource:<resource-code>`. Informal influence and non-formal grants may
inform a decision context but never substitute for formal resource authority.

`OrganizationDecisionPort` accepts a frozen `OrganizationDecisionContext`
assembled by the caller. The context contains only supplied identity,
governance, memberships, authority grants, filtered facts, capabilities,
resources, motives, goals, plans, and circumstances. It has no repository or
World State access. The replaceable deterministic implementation proposes but
does not persist or schedule anything.

The organization decision service validates the proposal outside the port,
rechecks persisted authority and prerequisites, reserves organization-owned
resources, marks the organization plan step scheduled, persists the proposal
application, and appends `organization-plan-step` to the scheduler in one short
transaction. This operation does not advance time.

During an authorized `AdvanceTime` or `AdvanceUntilEvent`, a pure deterministic
scheduled-event resolver accepts the referenced organization step. The temporal
service validates that the organization owns the plan, applies the completed or
failed transition, applies the outcome's organization-owned resource effects and
reservation releases, records the occurred event, and advances the clock
atomically. No organization or plan independently advances time.

Simulation Run replay, deterministic scheduler identifiers, reservation state,
unique resource transactions, Event Ledger records, and organization plan state
jointly prevent repeated effects. Resolver or transaction failure rolls back all
world consequences while the failed Simulation Run remains recoverable.

## Consequences

- Organizations can act off-screen during authorized temporal intervals.
- Membership, authority, influence, and internal disagreement remain visible as
  separate concepts.
- Organization resource commitments use shared persisted balances without
  transferring authority to every member.
- No universal authority, price, economy, or quantity policy is selected.
- The scheduler and temporal authorization remain shared infrastructure while
  character and organization ownership stay explicit.

## Traceability

This decision implements Validation 12 and cross-system contracts C1-C5, C8-C9,
C13, and C16. It extends ADR 0004's filtered decision pattern, ADR 0005's
authorized scheduled consequences, and ADR 0006's organization-capable resource
owner abstraction.

## Review criteria

Revisit for multi-owner transfers, delegation chains, organization merge/split
mechanics, collective knowledge, aggregate memberships, recurring commitments,
and world-specific governance models.
