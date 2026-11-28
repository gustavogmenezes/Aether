# ADR 0014 — Character Genesis and Event-Evidenced Progression

## Context

Approved validations 04, 05, and 06 require mechanically complete character
genesis, Storytelling reference distribution rules, and progression that may
change positively or negatively. They also require experience and causally
related events to support changes without conflating progression with identity,
personality, or psychological state. The approved Storytelling reference does
not define category names or a universal XP formula.

## Problem

Character creation must validate only deterministic point distributions while
leaving names and world content to a supplied ruleset. Progression proposals
must remain explainable and idempotent, but the system must not invent an
experience formula or permit an unevidenced or arbitrary rewrite.

## Considered alternatives

- Hard-code human Storytelling categories and character content.
- Store progression only as the current sheet, discarding causal history.
- Derive changes from XP, levels, or an automatic universal formula.
- Allow an LLM or proposer to write a character sheet directly.

## Decision

Introduce frozen contracts for categorized attributes and skills,
specializations, Merits, narrative qualities/flaws, injuries, traits, genesis
provenance, and the current `CharacterSheet`. A world supplies category names
and the category-to-mental/physical/social classification in a
`StorytellingCreationProfile`. The deterministic Genesis Engine validates the
approved 5/4/3 attribute extras (after one point in each attribute), 11/7/4
skills, three specialization levels, seven Merit points, and documented
untrained penalties. It does not create character or world content.

Progression evidence must reference persisted Event Ledger events and one
character/world. A proposal contains explicit, named positive or negative
changes and an expected sheet version. Submission rejects absent evidence,
unknown event links, mismatched world/ruleset, stale versions, missing targets,
and changes that violate rating bounds. No universal XP, level, cost, or
calculation is introduced.

Validation and application history are separate immutable JSON-backed records.
Approval is recorded before application. Application checks the approval,
current version, and supplied profile; creates one immutable snapshot record
containing the sheet before/after and evidence; and atomically replaces the
current sheet. A proposal ID can be applied once, and replay returns its
existing application.

Progression addresses only mechanical sheet fields, narrative features,
injuries, and traits. It has no repository operation for rewriting
`CharacterIdentity`, `PersonalityProfile`, or `PsychologicalState`. Those
records require their own evidenced workflows.

Migration 0014 creates:

- `character_sheets`;
- `character_progression_evidence`;
- `character_progression_proposals`;
- immutable `character_progression_validations`;
- immutable `character_progression_applications`.

## Consequences

- Category names are a world responsibility rather than an engine assumption.
- Mechanical point allocation is deterministic and independently testable.
- Every applied progression is traceable to persisted events and evidence.
- Negative change, including injury and capability decline, is explicit.
- Optimistic versions and immutable applications prevent stale or duplicate
  writes.
- World-specific formulas and progression costs remain outside this ADR.

## Traceability

This decision implements approved validations 04, 05, and 06 and preserves
cross-system contracts C3-C5, C8-C12, C14, and C16.
