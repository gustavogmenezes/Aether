# Operational Model Benchmark Specification

**Status:** Proposed for benchmark execution and approval

This specification supplies the evidence protocol for DEC-001, DEC-002, and
DEC-003. It does not select a model, runtime, loading policy, or concurrency
limit.

## 1. Reference environment

Record at every run:

- GPU, driver, total/free VRAM.
- RAM and swap.
- Operating system.
- Runtime and runtime version.
- Model name, model version, quantization/format, and context window.
- GPU-layer or offload configuration.
- Runtime and benchmark Git/system versions.

The current reference machine is an NVIDIA RTX 3060 with 12 GB VRAM and 16 GB
RAM. This is a benchmark target, not an architectural dependency.

## 2. Capabilities to evaluate

Every candidate must be tested independently for:

1. Structured Game Master action proposals.
2. NPC decision proposals using isolated, epistemically filtered context.
3. Narrator focalization over confirmed facts.
4. Canonization impact classification.
5. Short deterministic follow-up/recovery context.
6. Long-context retrieval and instruction retention.

A model may be selected per capability. One model is not presumed sufficient
for every agent role.

## 3. Correctness gates

A run is valid only when it:

- Produces parseable JSON where JSON is required.
- Includes every required key.
- Does not invent a mechanical result absent from supplied confirmed facts.
- Does not mention forbidden hidden-fact markers.
- Does not treat Player Knowledge as Character Knowledge.
- Keeps IDs and enum values from the input contract.
- Recovers or reports failure explicitly instead of producing a success-shaped
  fallback.

Correctness is mandatory. A faster or cheaper model does not pass by sacrificing
an invariant.

## 4. Performance measurements

Collect:

- Cold-load duration.
- First-token duration.
- Total generation duration.
- Prompt-evaluation and generation tokens where exposed.
- Generation tokens/second.
- Peak and median VRAM use.
- Peak and median system RAM use when available.
- Failure/retry counts.
- Out-of-memory events.
- Output-schema validity rate.
- Capability-specific correctness rate.

Run at least five warm repetitions and three cold-load repetitions per
candidate/configuration. Report distributions, not only averages.

## 5. Concurrency

Test independently:

- One foreground interaction.
- One foreground interaction plus one low-priority background inference.
- Model/image workload handoff.
- Load/unload during an active request.
- Recovery after runtime failure or cancellation.

DEC-003 limits must be selected from the highest stable configuration that
preserves correctness and leaves a measured safety reserve. The policy must
include denial/queue behavior; oversubscription is not resolved by risking
silent truncation or OOM.

## 6. Candidate selection

A candidate can be approved only after:

1. All mandatory correctness gates pass.
2. Hardware evidence is retained in machine-readable JSON.
3. A smaller qualifying model is compared where available.
4. Loading/offloading consequences are measured.
5. The selected model version and quantization are pinned.
6. The model-to-capability mapping is documented in an ADR.

## 7. Deferred choices

This benchmark does not preselect:

- Ollama, llama.cpp, another runtime, or a remote fallback.
- A model family or parameter count.
- A quantization format.
- Simultaneous language/image generation.
- A concurrency limit.
- Context truncation behavior.
- Fine-tuning or LoRA.
