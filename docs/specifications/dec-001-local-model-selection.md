# DEC-001 — Local Model Selection

**Status:** DRAFT — benchmark required

## Context

The approved architecture requires local essential inference, replaceable
capability providers, and engine authority. Concrete models must be selected by
benchmark evidence on the reference hardware.

## Decision needed

Approve capability-to-model mappings containing:

- Capability.
- Candidate model and pinned version.
- Quantization/format.
- Minimum context window.
- Runtime and backend configuration.
- Measured correctness, latency, memory, and failure evidence.
- Fallback/escalation policy.

## Constraints

- Selection is per capability, not necessarily one universal model.
- Essential operation must remain local.
- The domain remains provider-independent.
- A model that violates epistemic, causality, or schema contracts cannot pass on
  speed alone.

No selection is made in this draft because local model evidence is not yet
available.
