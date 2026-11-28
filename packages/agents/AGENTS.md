# Agents Package Instructions

This package adapts contextual Aether agent roles to provider capability ports.

- Never write directly to persistence or resolve mechanical rules.
- Depend on inference provider protocols, not concrete runtimes.
- Return structured proposals with invocation metadata.
- Reject malformed provider output explicitly.
- Do not assume one model is assigned to every capability.
