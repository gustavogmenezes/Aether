# ADR 0012 — Public Culture and Multimodal Identity

## Context

Validations 24, 25, 28, 29, and 30 require public information, collective reception, creative expression, everyday leisure, visual identity, and sonic identity without conflating publication, reception, objective truth, or generated assets.

## Decision

Public channels persist reach, speed, reliability, cost, control, and interception semantics. Publication remains separate from aggregate reception. A publication records what was publicly stated; reception records when and how a population received or interpreted it. Neither automatically changes Character Knowledge.

`public-publication` events occur only during an authorized temporal interval. The event payload supplies the publication and explicitly authored aggregate reception records. The pure resolver validates world and chronology, and the temporal transaction persists the publication, reception records, and Event Ledger event together.

Creative works persist creator, context, style, tradition, material, technique, intent, audience, influence, and censorship metadata without requiring historical relevance or numerical artistic quality.

Leisure routines record actor, schedule, locations, preferences, and optional reward tags. They do not automatically generate mechanical benefits.

Visual and sonic identities distinguish canonical traits from current state. Generated image or audio assets reference canonical identities and filesystem objects; generated representations never replace canonical identity data. Diegetic and extradiegetic sound remains explicit.

## Consequences

- Objective truth, public statement, aggregate opinion, and individual Character Knowledge remain separate.
- Censorship, propaganda, and manipulation are tags and explicit outcomes rather than inferred truth.
- Aggregate reception can be recorded without materializing every recipient.
- Image/audio generation may be integrated later without changing identity authority.
- Publication, generated assets, creative works, and routine semantics do not automatically canonize structural world changes.

## Deferred

No collective-opinion prediction formula, art-quality metric, censorship propagation algorithm, automatic canonization threshold, image model, audio model, or adaptive-soundtrack policy is selected here.

## Traceability

Implements validations 24, 25, 28, 29, and 30 with ADRs 0001, 0002, 0003, 0008, and 0011.
