# Infrastructure Package Instructions

This package owns SQLite, SQLAlchemy, Alembic, filesystem, and future adapter integrations.

- Never define domain invariants here; implement the ports and persist validated state.
- Keep common event-envelope fields queryable; version event-specific payloads.
- Use short transactions and preserve rollback behavior.
- Schema changes require an Alembic migration and integration tests.
