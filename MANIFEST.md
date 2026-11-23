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

Generated as a documentation handoff package. Review the traceability note for validations whose original prose was not fully available. The two decision records are approved; their unresolved derived technical specifications remain non-binding until separately specified and approved.
