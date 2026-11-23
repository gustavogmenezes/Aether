# ADR 0002 — Action and Presentation Flow

## Context

Phase 2 must connect free-form player intent to a structured Action Proposal, deterministic validation, an authorized temporal operation, and literary presentation without selecting a concrete LLM runtime.

The approved architecture requires Game Master and Narrator authority boundaries, separate LLM Invocation and Agent Proposal records, and the presentation-confirmation-extraction lifecycle.

## Problem

An executable action flow is required before an external or local model adapter is benchmarked. The flow must preserve idempotency and must not allow generated text to invent mechanical outcomes or player discoveries.

## Considered alternatives

- Let the temporal engine accept unstructured player text.
- Allow the Game Master to mutate world state directly.
- Make the Narrator the source of action duration and results.
- Use persistent records only for successful delivery.

## Decision

Define replaceable Game Master, Action Validation, Narrator, and Presentation Delivery ports.

The application orchestrates:

1. Interpretation outside a database transaction.
2. Deterministic proposal validation.
3. Preparation of a persistent Simulation Run.
4. Separate persistence of LLM Invocation and Agent Proposal records.
5. Authorized temporal execution.
6. Narrative generation only from confirmed action facts.
7. Persistence of generated presentation.
8. Delivery confirmation.
9. Extraction of delivered facts into Player Knowledge and Narrative State.

The deterministic command parser and template narrator are baseline local adapters for the current slice. They do not establish the future LLM/model choice. The parser accepts only explicitly supported structured wait commands and fails other inputs rather than guessing.

Narrator claim identifiers must be a subset of validated fact identifiers. Delivery must confirm only generated claims. Hidden events processed during an interval are not included in narrative context unless a future filtered Context Builder establishes perception through an approved knowledge path.

## Consequences

- World simulation may be committed before presentation succeeds without replaying effects on retry.
- Generated but undelivered text does not become Player Knowledge.
- Narration can be tested independently from model providers.
- More expressive interpretation and literary quality remain adapter concerns subject to model benchmarks and evaluation.

## Review criteria

Revisit if action duration needs a shared domain Ruleset, if presentation requires a delivery queue, if partial content delivery must be represented, or when a concrete model adapter is selected through an ADR.
