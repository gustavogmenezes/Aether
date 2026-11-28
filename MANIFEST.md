# Package Manifest

- `AGENTS.md`
- `README.md`
- `docs/README.md`
- 4 architecture specifications
- `docs/decisions/`
  - `docs/decisions/00001-mvp-decisions.md` — foundational decision record, **APPROVED**
  - `docs/decisions/00002-model-decisions.md` — operational model decision, **APPROVED**
- 31 validation records
- Cross-system contracts
- Glossary
- Implementation roadmap (proposed)
- Decision status / open items
- Python monorepo with package-level contexts for contracts, domain, engines, application, and infrastructure
- SQLite/Alembic transactional-core implementation and tests
- ADR 0001 for the initial transactional-core technology
- ADR 0002 for the action and presentation flow
- Phase 2 action contracts, deterministic adapters, presentation confirmation, and Player Knowledge extraction
- ADR 0003 for Character Knowledge and communication
- Character knowledge, perception, delayed transmission, and filtered-context implementation
- ADR 0004 for personality, directional relationships, goals, plans, and NPC decisions
- Separate identity/personality/psychological state contracts and persistence
- Directional relationships, motive/goal/plan/step persistence, deterministic NPC proposals, and validated plan-step scheduling
- ADR 0005 for worldwide autonomous scheduled-event resolution
- Authorized off-screen NPC plan-step consequences with atomic Event Ledger and plan-state updates
- ADR 0006 for resource balances, reservations, transactions, and plan consequences
- Material/social/structural/personal resource ledger integrated with scheduled plan execution
- ADR 0012 for public information, creative expression, leisure, and multimodal identity
- Public channels/publications/receptions, creative works, routines, visual/sonic identity, and non-canonical generated assets
- ADR 0013 for canonical detail approval, revision, and invalidation history
- ADR 0007 for organizations as autonomous actors
- Organization identity, governance, membership, formal authority, informal
  influence, organization goals/plans, filtered decisions, scheduled
  consequences, and shared resource permission checks
- Alembic migration 0007 for organization persistence
- ADR 0008 for geography, territory, infrastructure, and mobility
- Hierarchical semantic locations, separate ownership/effective control claims,
  infrastructure persistence, explicit route segments, journeys, positions,
  resource reservations, and authorized arrival resolution
- Alembic migration 0008 and geography/mobility contract, engine, application,
  persistence, recovery, temporal, and epistemology tests
- ADR 0009 for configurable ecology, species, population/cohort demography,
  and independent health dimensions
- Explicit natural scheduled consequences, decimal population cohorts, habitat
  and ecological process persistence, and health condition records
- Alembic migration 0009 and natural-system contract, engine, application,
  replay, rollback, temporal, and epistemology tests
- ADR 0010 for knowledge/technology lifecycle, language and translation
  metadata, education opportunity and assessment, and separate belief and
  metaphysical-truth representations
- Explicit actor access, language communication, and cultural scheduled-event
  ports and pure engines
- Alembic migration 0010 and knowledge, language, education, belief,
  idempotency, rollback, access, and temporal integration tests
- ADR 0011 for normative systems, legal proceedings, asymmetric diplomacy,
  strategic state, and security/intelligence resolution
- Persistent Phase 5 justice, treaty, strategic conflict, threat, incident,
  intelligence operation, filtered evidence, and explicit outcome contracts
- Alembic migration 0011 and authority, jurisdiction, knowledge-filtering,
  non-linear escalation, idempotency, rollback, and AdvanceUntil tests
- ADR 0014 for Character Genesis and event-evidenced progression
- World-configured Storytelling creation categories, deterministic point
  distribution validation, current character sheets, and genesis provenance
- Immutable progression evidence, proposals, approval/validation records, and
  version-checked before/after application history
- Alembic migration 0014 and genesis/progression contract, engine, repository,
  idempotency, stale-state, positive/negative, and personality-isolation tests
- ADR 0015 for explicit simulation tiers, population materialization, and
  consolidation continuity
- Tier-state, population/cohort accounting, materialized-individual provenance,
  and idempotent transition contracts, engine, application service, and
  persistence
- Alembic migration 0015 and count-continuity, duplicate-prevention, explicit
  transition, preservation, stale-version, and roundtrip tests
- ADR 0016 for culture, society, semantic social groups, individual cultural
  affiliation, filtered character context, and historical cultural change
- Culture definitions with UUID-only religion/language/art references kept
  separate from organization persistence
- Multiple simultaneous affiliation dispositions with visibility, confidence,
  provenance, and temporal filtering without behavioral determination
- Alembic migration 0016 and culture/organization-separation, heterogeneity,
  disposition, filtered-context, history, and idempotency tests
- Operational-model benchmark protocol for DEC-001/002/003
- Runtime-neutral local benchmark harness and candidate scenario suite
- ADR 0017 for Ollama now and optional external API providers later
- `InferenceProviderPort`, Ollama HTTP adapter, and structured Game Master/Narrator provider adapters

Generated as a documentation handoff package. Review the traceability note for validations whose original prose was not fully available. The two decision records are approved; their unresolved derived technical specifications remain non-binding until separately specified and approved.
