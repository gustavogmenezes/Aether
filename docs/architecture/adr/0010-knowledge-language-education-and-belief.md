# ADR 0010 — Knowledge, Technology, Language, Education, and Belief

## Context

Validations 16 through 19 require causal technology and knowledge lifecycles,
diegetic language barriers, education without automatic mastery, and a strict
separation among personal belief, religious institutions, and world
metaphysics. The operational model remains local, deterministic, transactional,
epistemically filtered, and recoverable.

## Decision

Knowledge artifacts and technologies use an explicit lifecycle vocabulary:
`exists`, `discovered`, `documented`, `transmitted`, `mastered`, and `applied`.
Each entity persists authored prerequisite states, resource quantities,
infrastructure, locations, language and secrecy permissions, educational
admission conditions, and other capability conditions. Lifecycle changes are
immutable, event-linked records. No transition is inferred from elapsed time.

Languages, dialects, writing systems, and character proficiency are separate
records. Proficiency is semantic for comprehension, speaking, reading, and
writing rather than a universal numeric scale. Information Transmission gains
optional source/target language, dialect, writing-system, presentation
language, and translation-semantic metadata. Existing records without that
metadata retain their prior behavior. A due transmission with an explicit
language that the recipient cannot interpret is marked failed and does not
create Character Knowledge.

Education programs retain curricula, methods, teachers, resources,
infrastructure, languages, locations, and admission conditions. Enrollment,
learning opportunity, and assessment outcome records are separate. A learning
opportunity records participation only; completion and mastery exist only when
an assessment explicitly states them.

Religious traditions contain references for cosmology, doctrine, principles or
entities, rituals, texts, values, and interpretations and may refer to an
institutional organization. Individual Belief Records are separate from
Organization Membership. Objective Metaphysical Truth records are
world-scoped and carry the mandatory `world-objective-only` disclosure class.
No repository or character-context operation publishes them as Character
Knowledge.

Four event types express temporal cultural consequences:
`knowledge-transmission`, `technology-use-completion`,
`learning-assessment`, and `religious-ritual`. They are scheduled intentions
and execute only inside an authorized temporal interval. Pure resolver and
access ports validate the explicit actor context, then Event Ledger, entity
state, immutable records, scheduler status, and clock commit atomically.
Simulation-run replay prevents duplicate records.

## Consequences

- Actor access failures are explicit and cover location, resources,
  infrastructure, language, secrecy, education admission, prerequisites, and
  capability conditions.
- Knowledge transmission is not teleportation and never directly grants
  Character Knowledge to an absent or linguistically incapable recipient.
- Faith, institutional membership, ritual participation, and objective
  metaphysics cannot be substituted for one another.
- Every new technology condition, rate, curriculum, assessment, ritual, and
  language statement remains authored world configuration.

## Deferred decisions

This ADR intentionally selects no universal learning rate, linguistic-evolution
model, language-quality measure, religious truth, technology discovery
algorithm, progression formula, or quantitative teaching/religious-quality
metric. None may be introduced as an implementation default.

## Traceability

Implements validations 16, 17, 18, and 19 and cross-system contracts C1-C13,
C16. It follows approved decisions 00001 and 00002. Alembic revision `0010`
persists the representation while the four domain ports keep orchestration
independent of SQLAlchemy and external services.
