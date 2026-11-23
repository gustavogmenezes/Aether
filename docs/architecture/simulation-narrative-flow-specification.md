# Simulation & Narrative Flow Specification
**Aether Storytelling System — v1.0 (consolidation)**

## 1. Principle

World simulation and narrative presentation are separate responsibilities. World time advances only through an explicitly authorized operation; narrative then presents the relevant experience with resolution proportional to context. Autonomy and the presence of a plan or scheduled event do not independently authorize clock advancement.

## 2. Integrated cycle

1. Player Input.
2. The Game Master interprets intent and produces a structured Action Proposal.
3. Initial validation: capabilities, knowledge, state, resources, permissions, and rules.
4. Duration estimate.
5. Preparation of an explicitly authorized temporal interval.
6. Chronological processing of actions, scheduled events, consequences, and NPC autonomy.
7. Invariant and consistency validation.
8. Atomic commit.
9. The Narrative Context Builder queries confirmed state.
10. The Narrator produces a literary response.
11. Session/presentation state update.

The Narrator does not decide mechanical outcomes and must not narrate an unconfirmed event as having occurred.

## 3. Action types

- Instantaneous: pick up an object, open a simple door.
- Interval: travel, training, rest.
- Interruptible: conversation, investigation, preparation.
- Scheduled: an event set for a future time/condition.

An action may combine categories. Long actions may be interrupted by events; the system determines continuation, cancellation, or alteration according to rules and context.

## 4. Hybrid duration

The LLM interprets intent and may suggest duration. The Engine validates and applies duration using known deterministic rules. The LLM estimates ambiguous or uncatalogued actions. Duration must not be accepted without contextual validation.

## 5. World advancement

- The world does not advance while the application is closed.
- The application being open is not sufficient to advance time.
- Player actions advance time when their validated duration authorizes an interval; Narrative Protagonist duration proposals still require engine validation.
- Observer mode advances through `AdvanceTime`, `AdvanceUntil`, or equivalent explicit observer controls.
- `PauseSimulation` or its equivalent freezes temporal advancement until a later authorization.
- Causal, scheduled, and emergent events are processed during the interval in chronological order.
- An active NPC plan or scheduled event alone never advances the clock.
- Do not resolve everything only at the final instant.
- NPCs and organizations may act while the protagonist performs an interval action.
- The world may produce consequences outside the protagonist’s presence; they become known only through valid means.

## 6. Events and scheduler

The Event Ledger records events that actually occurred. The Event Scheduler maintains intentions/future events. The World Calendar is a temporal index over the ledger. Every event uses the 00001 common envelope (`event_id`, `world_id`, `timeline_id`, `occurred_at`, `recorded_at`, `sequence`, `event_type`, `source_type`, `source_id`, `caused_by`, `priority`, `payload_version`, `payload`).

The engine orders by occurrence time, causal dependency, operational priority, and deterministic sequence. Independent events may share a logical processing window; changes competing for the same state or unique resource serialize deterministically. Critical, relevant, and ordinary interruption classes apply as defined in `../decisions/00001-mvp-decisions.md`; priority affects processing, not fictional chronology. The concrete scheduler and conflict algorithm remain DEC-012.

Safeguards:
- maximum events per cycle;
- maximum causal depth;
- duplicate prevention;
- LLM-call budget;
- pause and recovery when limits are exceeded, without silently discarding events.

## 7. Transactions and recovery

Do not keep a SQLite transaction open during LLM calls.

Flow:
- create `simulation_run_id`;
- capture the reference version/state;
- prepare proposals outside the transaction;
- validate against current state;
- calculate changes;
- open a short transaction;
- persist changes, events, and clock atomically;
- commit;
- produce narrative from confirmed state.

Simulation Run, LLM Invocation, and Agent Proposal are separate persistent records related by `simulation_run_id`. Preserve actual model responses, proposal validation, and recovery state. Reuse completed invocations only when context and relevant versions remain valid, and never repeat committed effects when narrative generation fails. The physical schema and recovery state machine remain DEC-013.

Failure before commit preserves the previous state. Failure after commit must allow presentation to resume without repeating effects. Operations must be idempotent.

## 8. Ordering

Order by occurrence time, causal dependencies, operational priority, and deterministic engine-assigned sequence. Simultaneous events are allowed. Do not impose fictional causal order where no dependency exists, and do not let processing priority rewrite chronology.

## 9. Player lens / Narrative Resolution

The player is a resolution lens, not the world’s engine.

The protagonist’s proximity, actions, and interests determine which elements receive more detail and presentation:
- global/strategic world;
- region;
- locality;
- immediate experience.

These layers are different resolutions of the same reality, not separate worlds.

The lens:
- retrieves established details;
- infers compatible details;
- develops still-abstract elements;
- canonizes local details according to authorship policies;
- never suspends autonomous simulation during an authorized interval;
- never advances the clock merely because an element is developed or a plan exists.

A patrol may fulfill its objective while the protagonist studies elsewhere. Destruction of a pyre, for example, must occur if conditions and schedule permit, even when the player abandons the mission.

## 10. Narrative presentation

Quality is not measured by word count. The LLM should seek experiential density: atmosphere, relevant sensory detail, natural dialogue, distinct characters, curiosity, and pacing. Avoid both simplistic responses and purposelessly verbose descriptions. A transition may be brief; a significant scene deserves development.

## 11. Focalization and knowledge

Narrative is normally restricted to what the protagonist can perceive/know. Do not expose secret/off-screen thoughts as protagonist knowledge. Do not fabricate retroactive knowledge. The player may attempt actions using metaknowledge; resolution considers actual capabilities and evidence.

Narrative completion has a presentation lifecycle: the Narrator proposes presentation, the system confirms what was actually delivered, and only then extracts relevant information into persistent Player Knowledge or continuity state. Generated but undelivered content is not a player discovery. Narrative State is persistent presentation context, not world truth; Player Knowledge does not determine protagonist knowledge.
