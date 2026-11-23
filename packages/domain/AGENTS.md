# Domain Package Instructions

This package owns domain entities, invariants, exceptions, and dependency ports.

- Do not import infrastructure, SQLAlchemy, Alembic, HTTP, or LLM-provider modules.
- Keep state transitions and optimistic-version rules testable without a database.
- Persisted event facts and scheduled intentions must remain separate.
