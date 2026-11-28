# ADR 0011 — Normative, Diplomatic, Strategic, and Security Foundations

## Context

Validations 22, 23, and 27 require persistent legal and security institutions
without universal law knowledge, linear war progression, universal crime
probabilities, or automatic tactical outcomes. Existing organization authority,
territorial, event-ledger, knowledge, and recovery systems already define the
boundaries needed by these foundations.

## Decision

Normative systems record their formal, customary, religious, institutional,
treaty, private, or supernatural character separately from rules, rights and
duties, jurisdiction, authority grants, territorial scope, legal validity,
enforceability, legitimacy, oversight, acceptance, and corruption semantics.
Cases, offenses, investigations, restricted evidence, proceedings, sanctions,
appeals, and enforcement states are distinct lifecycle records.

Organization relations are directional and multidimensional. Treaties,
sanctions, ceasefires, reparations, concessions, and information-sharing are
recorded with explicit parties and lifecycle state. No reverse relation or
counterparty obligation is inferred.

Strategic conflicts persist authored objectives and semantic factor records for
capability, logistics, resources, morale, command, terrain, infrastructure,
public support, allies, and demographic/economic effects. Escalation stage and
stage metadata are supplied explicitly. There is no stage ordering requirement
and no automatic progression.

Security threats, incidents, intelligence operations, and immutable resolution
records represent investigation and the explicit outcomes of arrest, exposure,
dismantling, escape, negotiation, or remaining unresolved. Threat motivation and
opportunity are recorded context, never a crime probability.

Five pure scheduled resolvers apply only during an explicitly authorized
temporal interval: `legal-proceeding-transition`, `treaty-change`,
`strategic-escalation`, `investigation-completion`, and
`security-resolution`. Before resolution, persisted active organization
membership, a formal permission grant, current actor location, normative-system
authority, and jurisdiction are rechecked. Version checks, one transaction,
simulation-run identity, scheduler status, and the common Event Ledger provide
idempotency and rollback.

Evidence bodies remain in access-filtered evidence records rather than
resolution payloads. Public event payloads contain identifiers and lifecycle
outcomes. Character Knowledge is created only from explicit per-character
disclosures supplied by an event; restricted evidence and investigation
findings otherwise never enter character context.

## Consequences

- Authority is operational permission, while validity, enforceability, and
  legitimacy remain independent authored semantics.
- Sanctions and enforcement cannot bypass existing formal organization grants
  or actor-location jurisdiction.
- Treaty and strategic changes are explicit recorded state, not simulation
  formulas.
- Investigation and intelligence completion do not reveal their contents to
  absent characters.
- Migration `0011` persists the records in versioned JSON payloads with
  queryable identity, world, party, status, and linkage columns.

## Deferred decisions

This ADR intentionally selects no tactical combat mechanics, universal crime or
enforcement probability, legal-evaluation engine, sanctions economic formula,
strategic optimization rule, mandatory escalation path, or tactical battle
model. Those concerns require separate approved specifications.

## Traceability

Implements validations 22, 23, and 27, cross-system contracts C1-C14 and C16,
and approved decisions 00001 and 00002.
