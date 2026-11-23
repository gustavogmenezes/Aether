# Contracts Package Instructions

This package contains durable value contracts, schemas, identifiers, and status enums shared across bounded contexts.

- Keep contracts free of SQLAlchemy, Alembic, model-provider, and presentation dependencies.
- Preserve approved field names and event-envelope semantics.
- Add schema tests when changing public contract behavior.
- Any breaking change requires a documented ADR or explicit contract-version decision.
