# ADR 0001 — Initial Transactional Core Technology

## Context

Phase 0/1 requires a testable local transactional core before model selection or presentation work. The approved reference stack selects Python, Pydantic, SQLite, SQLAlchemy, and Alembic while leaving vendor coupling and domain-framework coupling prohibited.

## Problem

The repository needs bounded package contexts, executable contracts, persistence, migrations, and tests without prematurely selecting an LLM runtime or external service.

## Considered alternatives

- A single Python package with framework-specific persistence mixed into domain modules.
- One independently distributed package per bounded context with a workspace manager.
- Namespace-style bounded contexts in one repository with package-specific instructions and tests.

## Decision

Use a Python 3.11+ monorepo with five bounded import packages:

- `aether.contracts`: shared durable value contracts.
- `aether.domain`: entities, invariants, and ports.
- `aether.engines`: deterministic simulation behavior.
- `aether.application`: temporal operation use cases.
- `aether.infrastructure`: SQLAlchemy, SQLite, and Alembic adapters.

Python dependencies and test discovery are centralized at the repository root for the first slice. Package-specific instructions and tests remain colocated with each bounded context. Dependencies point inward from infrastructure/application toward contracts/domain.

Use Pydantic 2 for executable public contracts, SQLAlchemy 2 for persistence, Alembic for migrations, and pytest for backend tests. The stack remains replaceable behind ports.

## Consequences

- Domain imports do not depend on SQLAlchemy, Alembic, or presentation concerns.
- The first implementation can validate atomicity, idempotency, ordering, and recovery without an LLM.
- Independent publication of packages is deferred until a package publication boundary has demonstrated value.
- Concrete package index, lockfile, and model runtime choices remain outside this ADR.

## Review criteria

Revisit if package boundaries become impossible to test or install independently, if infrastructure details leak into domain/application, or if root-level dependency management blocks parallel package work.
