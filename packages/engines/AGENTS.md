# Engines Package Instructions

This package owns deterministic simulation algorithms.

- Do not call LLMs or write directly to storage.
- Accept explicit domain inputs and return validated deterministic proposals/results.
- Ordering must not rewrite in-world occurrence time or invent causal dependencies.
- Add focused tests for ordering, boundary, and conflict behavior.
