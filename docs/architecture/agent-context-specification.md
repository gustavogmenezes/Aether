# Agent & Context Specification
**Aether Storytelling System — v1.1 (consolidation)**

## 1. Approved decisions

- NPC autonomy: **Contextual**.
- Narrative Protagonist: **Controlled**.
- Narrator: **Literary**.
- Normal focalization: the protagonist’s perceptible experience.

## 2. Agents

### Game Master
Interprets free-form input, identifies intent, requests necessary context, and produces a structured Action Proposal. It neither directly changes world state nor determines mechanical consequences alone.

### NPC Decision Agent
A reusable agent that decides for one NPC in isolated context. It receives relevant identity, personality, capabilities, state, memory, knowledge, relationships, motives, goals, plans, resources, and circumstances. It receives no objective knowledge that the NPC lacks.

### World Architect
Helps build the world, history, rules, geography, institutions, cultures, cosmology, and policies. It works through guided interviews and collaborative authorship. Suggestions remain draft/proposed until approval when they concern relevant canonical content.

### Character Architect
Creates identity, nature, biography, psychology, behavior, attributes, skills, qualities/flaws, goals, initial knowledge, relationships, and visual/sonic description.

### Narrator
Receives validated/persisted state and presentation context. It converts facts and available perceptions into literary prose. It neither invents mechanical outcomes nor grants improper access to secrets.

Agent packages and runtime contexts may be independently developed and tested in the monorepo, but model/provider implementations remain behind capability contracts. Agents receive package-specific instructions and no wider context than required by their role and dependencies.

## 3. Context Builder

The Context Builder retrieves only the context required for the task:
- current state and version;
- location and time;
- present characters;
- relevant recent events;
- causality and schedule;
- agent/character knowledge;
- resources and capabilities;
- world rules;
- relevant memory and summaries;
- narrative tone and continuity.

Context is filtered by role and epistemology. Avoid dumping the entire database or all lore into each prompt.

## 4. NPC autonomy

Contextual autonomy means NPCs may act off-screen, but not arbitrarily. Every decision must remain plausible given personality, experience, knowledge, capabilities, resources, relationships, needs, goals, plans, and circumstances. Plans may fail and be revised.

Do not instantiate a persistent model per NPC. Use a shared decision agent with character-specific context.

## 5. Narrative Protagonist control

In Narrative Protagonist mode, the player declares intentions and the LLM may elaborate intermediate means/interactions. Consequential decisions—irreversible risks, commitments, goal changes, use of important resources, violence, decisive relationships—require player approval. This mode does not authorize the LLM to take control of the protagonist.

## 6. Literary Narrator

Prose may include atmosphere, pacing, emotional nuance, and sensory detail. Focalization prevents the narrator from turning hidden facts into protagonist knowledge. Presentation in English does not imply that characters speak English diegetically; diegetic language and presentation language are distinct.

## 7. Filtered knowledge

Each character may:
- be unaware of facts;
- know partially;
- believe false information;
- interpret incorrectly;
- suspect;
- lie deliberately;
- conceal information.

NPC context never automatically receives the complete World State. Knowledge requires perception, communication, investigation, deduction, or a power explicitly defined in the world.

## 8. Approval and canonization

Suggested states for authored content are: draft, proposed, approved, published, deprecated. Canonization additionally classifies impact:

- Level 0: ephemeral response construction.
- Level 1: contextual detail that may be automatically canonized.
- Level 2: persistent local fact requiring automatic consistency validation.
- Level 3: structural change requiring explicit approval.

Impact follows potential consequences, not superficial size. The Canonization Engine classifies and validates; agents only propose. Canonical records preserve origin, responsible author/agent, time, justification/event, level, entity references, and modification history. Unresolved quantitative thresholds remain DEC-005.

## 9. Proposal and presentation persistence

Each LLM Invocation and interpreted Agent Proposal is persisted separately and associated with its Simulation Run. Validation status, rejection, and application result are not inferred from generated prose.

Narrator output follows presentation-confirmation-extraction: the content is generated, the portion actually delivered is confirmed, and relevant delivered information is routed to persistent Player Knowledge or Narrative State. Undelivered text is not a discovery. This summary does not conflate Player Knowledge with the protagonist’s Character Knowledge.

See `../decisions/00001-mvp-decisions.md` sections 4.3, 4.7, and 4.9 for the approved contracts.
