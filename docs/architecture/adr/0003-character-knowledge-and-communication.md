# ADR 0003 — Character Knowledge and Communication

## Context

Phase 3 requires a persistent epistemic domain before deeper character personality, goals, or NPC decision behavior. Approved validations distinguish objective World State, Character Knowledge, Player Knowledge, and Narrative State.

## Problem

The engine must represent perception and communication without allowing characters to read the objective ledger directly or treating information as instantaneously transmitted.

## Considered alternatives

- Copy World State into every character context.
- Store all knowledge as narrative text.
- Materialize transmitted claims immediately when a sender creates them.
- Let the Narrator infer what a character should know.

## Decision

Implement separate Character Knowledge and Information Transmission persistence.

Character Knowledge preserves:

- Character identity.
- Fact key and interpreted statement.
- Source and acquisition events.
- Acquisition time.
- Confidence.
- Epistemic status.
- Temporal scope.
- Character-context visibility.

Information Transmission preserves:

- Source and sender.
- One recipient per record.
- Content and medium.
- Information nature, including honest error, rumor, lie, propaganda, and fabrication.
- Send and arrival times.
- Perceived reliability, alterations, intent, reach, and status.

Perception first tests whether evidence is perceptible. Interpretation converts perception or a due transmission into Character Knowledge. A transmission remains only an intention until authorized world time reaches its arrival time; interpretation and its state transition then persist atomically with the temporal operation.

Character context retrieves only visible knowledge acquired by that character at or before the current narrative/world time. Player Knowledge remains a separate presentation-delivery domain.

## Consequences

- Objective event persistence does not imply character awareness.
- A lie can be retained as an intentional lie or other non-truth epistemic status without silently becoming objective fact.
- Delayed communication is naturally processed by `AdvanceTime` and equivalent temporal operations.
- Reactions, personality-driven interpretation, and richer perception capabilities remain future Phase 3 engines.

## Review criteria

Revisit when aggregate/public reception, perception capabilities, language barriers, distortion pipelines, or knowledge revision/supersession receive dedicated specifications.
