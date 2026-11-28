# DEC-003 — RAM/VRAM Concurrency

**Status:** DRAFT — benchmark required

## Context

The Aether resource manager must prevent language, image, and auxiliary
workloads from destabilizing local execution.

## Decision needed

Approve:

- VRAM safety reserve.
- Maximum active model instances and contexts.
- Language-inference concurrency.
- Foreground/background priority.
- Queue and denial policy.
- Context/token admission policy.
- Heavy image/model transition handoff.
- Cancellation, OOM, and timeout recovery.

## Required evidence

Use measured peak VRAM, host RAM, latency degradation, correctness, and OOM
behavior from the benchmark suite. Limits must be derived from sustained
operation with a safety reserve, not a successful single request.

No numeric budget or concurrency limit is approved in this draft.
