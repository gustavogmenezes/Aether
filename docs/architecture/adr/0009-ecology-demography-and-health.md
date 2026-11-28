# ADR 0009 — Ecology, Demography, and Health

## Context

Validations 15, 20, and 21 require configurable biology, ecological processes,
background populations, species-specific life cycles, and a health model that
does not collapse medical state into psychology or combat outcomes. The
approved operational model also requires deterministic, local, transactional,
recoverable state changes without a universal biological, medical, or combat
formula.

## Decision

Species/nature definitions are world-scoped authored configuration containing
anatomy, physiology, reproduction, nutrition, habitat, senses, adaptations,
resource links, and ordered lifecycle stages. Biological, artificial,
extraterrestrial, and supernatural organisms use the same representation.

Populations are aggregate by default. Decimal-count cohorts are keyed by a
species lifecycle stage and retain explicit birth, mortality, and migration
distribution quantities. Habitats and ecological process state are
location-bound. Resource codes may be linked for future authored economy or
ecology integration, but no economy formula is applied here.

Health is a character-owned state distinct from psychological state. It keeps
physical/biological integrity, consciousness, ability to act, and ability to
fight as independent dimensions. Disease, infection, injury, disability, aging,
recovery, and rehabilitation are explicit condition records. Combat outcomes and
psychology are neither inferred from nor written into this state; a later
configured consequence must state the intended medical dimensions and
conditions.

Natural scheduled effects are limited to explicitly configured signed changes:

- `population-change`
- `ecological-process`
- `health-condition-change`

Each payload names its target and cause. Population effects validate species,
lifecycle stage, cohort, location, and a nonnegative resulting count.
Demographic and health consequences do not derive from a universal rate or
formula. Scheduled events are processed only inside an authorized `AdvanceTime`
or `AdvanceUntil` transaction through the deterministic scheduled resolver
boundary. The resulting aggregate, ecological state, health state, scheduled
status, clock, simulation run, and Event Ledger entry commit atomically or roll
back together. Simulation-run replay and optimistic versions preserve
idempotency and prevent duplicate effects.

Ecological and demographic ledger events remain objective World State. This
slice does not generate Character Knowledge or Player Knowledge for off-screen
changes.

## Consequences

- Every rate, reproduction mechanism, life stage, medical consequence, and
  ecological measure remains world-authored configuration.
- Background populations can evolve without materializing individuals.
- A configured actor may be conscious but unable to fight, unconscious without
  a represented severe injury, or injured and conscious without an implied
  combat formula.
- Population, ecological, and health changes are not resource-ledger changes
  merely because a resource link exists.
- SQLite remains authoritative; all new records use versioned provenance.

## Traceability

Implements validations 15, 20, and 21 and cross-system contracts C1-C5, C7-C14,
and C16. It follows approved decisions 00001 and 00002 and extends the
scheduled-world transaction established by ADR 0005. Alembic revision `0009`
persists the representation.

## Review criteria

Revisit for canonical species configuration loading, cohort materialization
and consolidation, collective health summaries, world-specific medicine rules,
and authored formulas in a ruleset or dedicated ADR. No universal reproductive,
mortality, disease, recovery, aging, ecology, economy, or combat formula is
selected by this decision.
