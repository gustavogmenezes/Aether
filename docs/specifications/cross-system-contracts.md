# Cross-System Contracts

This document gathers rules that every subsystem must honor.

## C1. World autonomy
The world, its actors, organizations, natural processes, economy, and conflicts have independent dynamics. The protagonist is neither the clock nor the universal trigger of events.

## C2. Time and pause
The world does not advance while the application is closed and does not advance merely because it is open. Time advances only through an explicitly authorized operation: a validated action that consumes time, `AdvanceTime`, `AdvanceUntil`, or an equivalent observer control. Plans and scheduled events alone do not authorize movement. `PauseSimulation` or an equivalent pause freezes the clock. Intermediate events are processed chronologically during authorized intervals.

## C3. Causality
Every relevant consequence must have a traceable cause. Planned events are not occurred events. Plan failures are also recordable outcomes.

## C4. Epistemology
World State, Character Knowledge, Player Knowledge, and Narrative State are separate persistent domains. No character automatically knows objective truth. Character knowledge has a source, medium, time, and reliability. Player Knowledge is confirmed delivered information and must not be treated as protagonist knowledge. Narrative State is presentation continuity, not world truth.

## C5. LLM/Engine authority
The LLM proposes, interprets, contextualizes, and narrates. Engines/the domain validate rules, invariants, resources, time, state, and persistence. The LLM cannot bypass validation.

## C6. Narrative
Literary Narrator with focalization restricted to the protagonist. Narrative presents only confirmed results. Player metaknowledge is neither erased nor retroactively converted into character knowledge.

## C7. Adaptive resolution
The player acts as a lens that increases resolution. Detail neither changes reality nor interrupts autonomy during an authorized interval. Abstract elements may be developed without contradicting canon. Four-level canonization applies before persistent details become canonical. Materialization and tier changes preserve aggregate totals, identity, state, relationships, plans, and history.

## C8. Identity and continuity
Canonical characteristics, current state, and generated representation are distinct. Images/audio do not replace canonical data.

## C9. Transactions
Simulations are idempotent, recoverable, and atomically persisted. Persist separate Simulation Run, LLM Invocation, and Agent Proposal records linked by `simulation_run_id`. Do not keep transactions open during inference, repeat committed effects, or assume model replay is deterministic.

## C10. Abstraction
Individual, abstract, or collective simulation depends on relevance. Promotion/demotion preserves identity, state, and history.

## C11. Configurable world
Biology, magic, technology, religion, justice, economy, time, languages, and other laws vary by world. Aether provides universal representations and interfaces, not a single fictional ontology.

## C12. Contract integrity
Technical difficulty does not authorize relaxing an approved contract. Record the conflict and request a decision.

## C13. Event ordering
All events use the approved common envelope and versioned payload. Order by occurrence time, causal dependency, operational priority, then engine-assigned deterministic sequence. Independent events may execute in one logical window; conflicting state/resource changes must serialize. Scheduler changes retain history, and only occurred events enter the Event Ledger.

## C14. Combat and health
Combat Resolution determines tactical conflict outcomes. Health determines resulting physical and medical conditions. Progression evaluates longer-term consequences. No subsystem may duplicate or bypass that authority.

## C15. Presentation persistence
Narrative follows presentation, confirmation, then extraction. Only content actually delivered may enter Player Knowledge; generated but undelivered content cannot become a player discovery.

## C16. Development boundaries
English is mandatory. The monorepo contains bounded packages with package-level instructions, tests, and agent contexts plus explicit cross-package contracts. Preferred technologies require technical validation and ADRs; concrete model and resource policies require benchmarks/specifications.

See `../decisions/00001-mvp-decisions.md` for the approved expansion of these contracts. Quantitative and algorithmic details remain listed in `decision-status-and-open-items.md`, not implementation assumptions.
