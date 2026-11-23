# Domain & Data Model Specification
**Aether Storytelling System — v1.1 (temporal consolidation)**

## 1. Reality model

The domain distinguishes:
- **World State:** objective world facts, including hidden facts, physical conditions, entity states, and events.
- **Character Knowledge:** each character’s knowledge, beliefs, suspicions, interpretations, and memories.
- **Player Knowledge:** persistent information actually presented to and discovered by the player; it supports continuity and consultation and is not a mechanical barrier to actions or a proxy for Character Knowledge.
- **Narrative State:** persistent scene state, location, present characters, perspective, tone, dialogue continuity, and presentation, without authority as world truth.
- **Canonical Content:** approved authored definitions of worlds, characters, rules, places, and lore.
- **Derived Context:** summaries, embeddings, graphs, and material retrieved for agents; rebuildable and never final authority.

No character automatically accesses World State. Exceptions require explicit powers/rules in the world.

## 2. Principal entities

### 2.1 World
Identity, configuration, rules, calendar, geography, species, cultures, institutions, history, cosmology, and simulation policies.

### 2.2 Timeline and Branch
- Timeline represents a historical/causal sequence.
- A Branch derives from a timeline at a divergence point.
- Events before the divergence are inherited; later events belong to the branch.
- Original history is preserved internally even when fictional reality presents an altered version.
- Each world may define a Fixed, Branching, Mutable, or Paradox-Based Timeline.
- Diegetic time travel is not the same as restoring a checkpoint.

### 2.3 Checkpoint
A persisted snapshot of relevant world/session/character/inventory/relationship/event state. It identifies timeline, Event Ledger position, schema version, relevant system versions, and an integrity hash or equivalent verification. Snapshots support recovery, comparison, and loading but do not replace the Event Ledger. Rollback creates a branch and preserves original history; it is not automatically fictional time travel.

### 2.4 Character
Identity, nature/species, biography, attributes, skills, specializations, qualities, flaws, personality, beliefs, goals, plans, capabilities, relationships, knowledge, memory, physical/mental condition, and visual/sonic identity.

### 2.5 Organization
A first-class entity with identity, purpose, history, hierarchy, authority, governance, rules, resources, territory, goals, interests, relationships, and capacity to act. It may outlive founders, split, merge, change purpose, or disappear.

### 2.6 Location / Region / Territory
Configurable hierarchical geography: world/planet, continents/regions, countries/kingdoms, provinces, cities, neighborhoods, properties, and points of interest. Distinguish location, ownership, and effective control.

### 2.7 Resource
Categories:
- Material: money, food, weapons, tools.
- Social/human: allies, contacts, influence, authority.
- Structural: territory, property, organizations.
- Personal: energy, health, disposition, capabilities.

### 2.8 Event
A record of something that actually occurred. Every event must support the common envelope:
`event_id`, `world_id`, `timeline_id`, `occurred_at`, `recorded_at`, `sequence`, `event_type`, `source_type`, `source_id`, `caused_by`, `priority`, `payload_version`, and `payload`.

Common indexed fields may be normalized further where frequent queries or relationships require it; event-specific data uses a versioned payload. Historical payloads require readable adapters or migrations.

`occurred_at` represents when the event occurred in-world; `recorded_at` represents when the system recorded/imported it. Simultaneous events are permitted. The engine orders by occurrence time, causal dependency, operational priority, then deterministic sequence; sequence is engine-assigned and operational priority must not rewrite fictional chronology.

### 2.9 Scheduled Event
A planned future event that has not occurred. It lives in the Event Scheduler. It enters the Event Ledger as occurred only after actual execution. Plan failure must be recorded as failure, not as the intended event.

## 3. History before the player

The timeline must begin before the protagonist’s entry. Every world needs preexisting history: canonical events and social, political, economic, and natural processes before the first session. The player may change the past when world rules permit, without internally erasing original history.

## 4. Knowledge and memory

Each knowledge record must represent source, acquisition event, timestamp, confidence, epistemic status, temporal scope, and visibility. Possible states include known, partially known, belief, rumor, suspicion, false information, intentional lie, and unknown.

Separate:
- objective fact;
- transmitted information;
- recipient knowledge/interpretation.

Knowledge changes only when information reaches and is interpreted by the character. Player Knowledge instead follows presentation, not simulated acquisition by the protagonist: content is generated, recorded as confirmed only if actually delivered, then relevant information is extracted into Player Knowledge and/or other continuity domains.

## 5. Characters and creation

All NPCs obey the world’s mechanical creation rules, even when simulated abstractly. Initial reference inspired by Storytelling/Chronicles:
- Attributes: 5/4/3 distribution, with one starting point in each attribute.
- Skills: 11/7/4 distribution.
- Three initial specialization levels under the approved rule.
- 7 Merit points.
- Narrative qualities and flaws are separate from mechanical Merits.
- Skill 0: −3 penalty to mental tests and −1 to physical/social tests under the approved rule.
- Mechanical, conceptual, and biographical templates are guides, not scripts.
- Contextual 1–5 scale: 1 novice, 2 ordinary, 3 good, 4 excellent, 5 an exceptional reference in the world.

Biographical genesis must adapt developmental stages to the entity’s nature: origin/nature, childhood or equivalent, education, adolescence or equivalent, maturity, and later experiences. Do not assume every entity is human.

## 6. Progression

There is no mandatory universal level or XP. Growth results from meaningful experience, difficulty, effective participation, learning, practice, reflection, adaptation, aptitude, and limitations. Progression may be negative: injury, trauma, aging, decline, or loss. The LLM proposes; the Character Progression Engine validates and applies according to world rules. Evidence history is preserved in the Event Ledger, separate from the current character sheet.

## 7. Relationships, personality, and goals

- Personality, identity, values/beliefs, behavior, and emotional state are distinct dimensions.
- Profound changes are possible when supported by a causal trajectory.
- Relationships are directional and multidimensional; trust, respect, affection, fear, admiration, resentment, loyalty, attraction, etc. need not be symmetric.
- Motives = why a character wants; goals = desired outcomes; plans = how the character intends to achieve them.
- Hierarchical goals may coexist and conflict. Plans are revisable, abandonable, and may fail.

## 8. Knowledge and transmission

Information does not teleport between characters. Every transmission depends on source, content, sender, recipient/audience, medium, sending/receipt, reach, perceived reliability, alterations, and intent when known. Media may be in-person, physical, social, institutional, technological, or supernatural.

## 9. World domains

The universal model supports, with world-specific rules:
- regional/political economy;
- institutions and dimensions of power;
- geography, territory, and infrastructure;
- culture and society;
- ecology and biology;
- technology and scientific knowledge;
- religion, spirituality, and metaphysics;
- language and linguistic evolution;
- education and knowledge transmission;
- health, medicine, and conditions of existence;
- demography and life cycles;
- justice and normative systems;
- conflict, diplomacy, and international relations;
- media, public information, and collective opinion;
- arts and creative expression;
- entertainment, leisure, and everyday life;
- transportation and mobility;
- security, intelligence, and crime;
- visual identity and sonic identity.

## 10. Canonization and simulation continuity

Persistent details use the four-level canonization policy from approved 00001: ephemeral detail (Level 0), contextual detail (Level 1), persistent local fact (Level 2), and structural change (Level 3). Persistent records preserve origin, responsible author/agent, timestamps, justification, canonization level, entity references, and revision history. Structural changes require explicit approval.

Tier promotion must materialize compatible individuals from an aggregate without duplicated members or contradictory history. Demotion/consolidation reduces simulation resolution without deleting identity, state, relevant history, relationships, plans, or event participation. Quantitative transition criteria remain open under DEC-006; the continuity rules do not.

## 11. Execution and recovery records

Persist separate, related records for:

- **Simulation Run:** `simulation_run_id`, initial state/snapshot reference, status, processed events, validated/final results, and recovery information.
- **LLM Invocation:** `invocation_id`, `simulation_run_id`, requesting agent/capability, model and model/prompt versions, context hash, parameters, preserved response or reference, status, token use, and timestamps.
- **Agent Proposal:** `proposal_id`, `simulation_run_id`, `invocation_id`, proposal type/payload, validation result, rejection reason if any, and application result.

Completed model outputs may be reused only when their context and relevant versions remain valid; committed effects must never be repeated. Exact persistence fields and the state machine remain DEC-013.

## 12. Combat and health

Combat Resolution is a deterministic subsystem for tactical conflict; Health owns physical and medical character conditions. Combat may produce consequences for Health, and progression may assess longer-term trauma or injury effects. Detailed combat mechanics remain DEC-011.

## 13. Persistence

- SQLite: transactional authority for dynamic state, events, sessions, relationships, schedules, and snapshots.
- YAML: canonical definitions/editable configuration.
- Markdown: lore, biographies, authored text, and documentation.
- Filesystem: images, audio, and other assets.
- Vector and graph indexes: derived and rebuildable.

The Event Ledger is the authority for historical events that occurred. The World Calendar is a chronological index over events, not a full copy of payloads. The Event Scheduler stores the planned future.

See `../decisions/00001-mvp-decisions.md` sections 4.3–4.9 for the binding decisions; unresolved quantitative or physical details remain assigned to DEC-004 through DEC-013 in `../specifications/decision-status-and-open-items.md`.
