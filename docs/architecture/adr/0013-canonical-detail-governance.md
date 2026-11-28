# ADR 0013 — Canonical Detail Governance

## Context

Approved 00001 establishes four canonization impact levels. Quantitative impact classification remains DEC-005, but persistent governance can operate on an explicitly supplied level.

## Decision

Ephemeral details are not persisted as canonical proposals. Contextual, persistent local, and structural proposals preserve origin, author, event/justification, level, related entities, and timestamps.

Persistent local facts require explicit consistency-validation notes. Structural records require an approving identity distinct from the proposer. Every approval creates an immutable canonical record with revision and supersession links.

Invalidation preserves the earlier record and creates a later invalidated revision with a required reason. Nothing is silently deleted.

## Consequences

- Generated detail cannot become persistent canon merely by narration.
- Approval history remains auditable across corrections and contradictions.
- DEC-005 impact classification, automatic proposal thresholds, and consistency algorithms remain open.

## Traceability

Implements approved 00001 canonization decisions and cross-system contracts C7, C12.
