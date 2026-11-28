# ADR 0008 — Geography, Territory, Infrastructure, and Mobility

## Context

Validations 13 and 26 require configurable geography, distinguishable
territorial claims and effective control, explicit infrastructure capabilities,
and durable travel whose completion is driven by the World Clock. Physical
distance must not be converted into travel time or cost by an assumed universal
formula.

## Decision

Locations form a configurable world-scoped hierarchy. The shared location
representation stores semantic terrain, climate, hydrology, flora/fauna,
resources, population density, barriers, strategic points, and risks. Regions
and points of interest specialize that representation without replacing its
parent relationship.

Formal or effective territorial claims record owner and controller actor
references independently. Actor kinds are explicitly `character` or
`organization`; control status may be controlled, contested, occupied, or
shared. A formal ownership claim therefore does not imply effective control.

Infrastructure is persisted as location-bound network nodes and facilities.
Transport routes contain selected location segments. Every segment carries
world-supplied physical distance and unit, base duration, explicit cost,
capacity, availability, consumption, safety, risk, and transport mode. A pure
engine rejects unknown, foreign, duplicated, or disconnected segment choices.
It sums the selected explicit values and derives no speed, price, or economic
formula.

Starting a journey validates route continuity and participant positions, persists
participant and resource-owner references, creates an in-transit journey,
sets transit positions, reserves configured resource consumption/cost, and
schedules `travel-arrival`. This operation never advances the World Clock.
Participants use generic actor references plus semantic participation types,
including organization fleets, without inventing aggregate membership or
quantities.

During an explicitly authorized `AdvanceTime` or `AdvanceUntilEvent`, a due
arrival is resolved in the existing atomic temporal transaction. The journey
becomes arrived, participant positions move to the destination, configured
resources are consumed through the resource ledger, reservations are finalized,
and the occurred outcome enters the Event Ledger. Resolver, state, position, or
ledger failures roll back all arrival effects while retaining the prior
reservation. Simulation Run identifiers prevent replayed resource or arrival
effects.

Travel ledger events are objective World State. They are not automatically
inserted into Character Knowledge or Player Knowledge, so off-screen travel is
not disclosed by this slice.

## Consequences

- Geography is hierarchical and world-configured rather than tied to a single
  fictional cosmology.
- Ownership and control may disagree and may be represented formally and
  effectively at the same time.
- Distance, duration, cost, capacity, risk, and consumption remain explicit
  authored facts.
- Arrival uses the established scheduler, transaction, recovery, and ledger
  authority.
- Resource-bearing travel uses the same reservation and immutable transaction
  semantics as plan steps.
- No universal speed, carrying capacity, cost, upkeep, or fleet-size formula is
  selected.

## Traceability

Implements Validations 13 and 26 and cross-system contracts C1-C6, C8-C11,
C13-C16. It extends ADR 0005's scheduled world consequences and ADR 0006's
resource reservations. Alembic revision `0008` persists the approved
representation.

## Review criteria

Revisit for route maintenance, dynamic unavailability, transit-time
interruption, intermediate events, transfer and fare policies, aggregate
fleet quantities, topology indexes, and world-specific movement rules.
