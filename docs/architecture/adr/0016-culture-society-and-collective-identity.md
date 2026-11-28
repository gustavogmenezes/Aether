# ADR 0016 — Culture, Society, and Collective Identity

## Context

Approved validation 14 requires historical and heterogeneous representations
of culture and society. A culture is not an organization, an individual's
affiliation is not a deterministic behavior rule, and the architecture must
not impose a universal class or hierarchy system.

## Decision

Persist `CultureDefinition` as values, customs, traditions, norms, belief
references, religion-tradition references, language references, art/symbol
references, intercultural relationships, and Event Ledger history references.
Religion, language, and art references remain UUID references to their owning
domain records; culture persistence does not duplicate those entities.

Persist `SocialGroup` separately from `Organization`. Its `semantic_category`
is world-defined text (for example community, class, caste, profession, or
minority) and has no assigned rank, superiority relation, or universal social
hierarchy. Organization membership and authority remain represented only by
the organization contracts.

`IndividualCulturalAffiliation` links a character to either one culture or one
social group. Multiple simultaneous links are permitted. Each records an
explicit disposition (`adheres`, `questions`, `rejects`, `assimilates`,
`hybridizes`, or `transforms`), visibility, observer allow-list, decimal
confidence, temporal validity, notes, and provenance. A context method assembles
only effective affiliations visible to the observer and their referenced
definitions. It does not derive personality, goals, choices, actions, or
statistical tendencies.

`CulturalChangeRecord` is an immutable history record for a culture or social
group. It requires an occurred Event Ledger reference, at least one approved
cause tag (migration, trade, war, colonization, conversion, revolution, or
technology), old/new canonical state references, occurrence time, summary, and
provenance. Reusing a record ID with identical content is an idempotent replay;
reusing it with different content is rejected. Existing records are never
rewritten when a later state is recorded.

Migration 0016 creates the four authoritative tables for definitions, social
groups, affiliations, and change history.

## Consequences

- Cultural and social identity can be heterogeneous, uncertain, private, and
  simultaneous without becoming organization membership.
- Historical transformations remain queryable without flattening old state
  into the current definition.
- The representation introduces no automatic cultural change, sociology
  formulas, behavioral prediction, conversion rates, or universal class
  system.
- Visibility filtering is a context boundary; it does not grant knowledge of
  objective state or disclose hidden affiliations.

## Traceability

This decision implements validation 14 and cross-system contracts C3, C4, C5,
C9, C11, C12, and C16. It preserves the approved domain boundaries and
operational persistence rules from decisions 00001 and 00002.
