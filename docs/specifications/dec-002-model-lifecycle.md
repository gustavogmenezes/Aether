# DEC-002 — Model Lifecycle

**Status:** DRAFT — benchmark required

## Context

The Model Manager must identify, load, unload, version, monitor, and recover
local capability providers without coupling agents to a specific implementation.

## Decision needed

Define and approve:

- Load trigger and target-ready state.
- Idle/unload timeout policy.
- Pinning/priority behavior.
- Version compatibility checks.
- Cancellation behavior.
- Retry and failure classification.
- Restart/resume ownership.
- Model/image GPU handoff.
- Whether loaded models may coexist on the reference hardware.

## Required evidence

Measure cold and warm load time, unload/reclaim time, request cancellation
behavior, failure recovery, and peak memory during transitions.

No lifecycle value is approved in this draft.
