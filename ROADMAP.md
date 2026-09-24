# TaskSeam Roadmap

TaskSeam aims to provide versioned task state across AI tools. This roadmap defines the behavior required to distinguish that product from a generic memory store or transcript handoff.

## North-star acceptance scenario

1. A user discusses a feature in ChatGPT and considers storing state in Markdown.
2. In Claude, the user accepts SQLite instead and leaves one permissions question unresolved.
3. The user opens Codex in the associated repository.
4. TaskSeam associates both conversations and the repository with one task.
5. Codex receives a bounded delta containing:
   - SQLite as the current accepted decision;
   - Markdown as a superseded decision;
   - the unresolved permissions question;
   - relevant artifact references;
   - evidence and confidence for every included item.
6. Unrelated or private conversation state is excluded.
7. The user can inspect and correct the association or extracted state.

TaskSeam is ready for a broader alpha when this scenario works repeatedly on an evaluation set, not only in a prepared demo.

## Milestone 1: Versioned state foundation

- [x] Local SQLite store
- [x] Typed decisions, questions, and constraints
- [x] Explicit supersession
- [x] Explicit question resolution into an accepted decision
- [x] Checkpoints and deltas
- [x] Source-event provenance
- [x] Localhost API
- [x] Read-only MCP delivery
- [ ] Schema migrations with compatibility tests
- [ ] Export and deletion commands

## Milestone 2: Evidence ingestion

- [ ] Normalized episode and message schema
- [ ] Import one ChatGPT conversation
- [ ] Import one Claude conversation
- [ ] Associate repository and Git metadata
- [ ] Preserve source references without executing captured instructions
- [ ] Capture controls and private-session behavior

## Milestone 3: Task-state reconstruction

- [ ] Task-link confidence using repository, file, entity, semantic, and time signals
- [ ] Proposal, accepted decision, rejected decision, constraint, question, and completion classification
- [ ] Supersession and question-resolution detection
- [ ] Ambiguity preservation instead of silent conflict resolution
- [ ] Human corrections that override inferred state
- [ ] Extraction version and evidence recorded for every derived item

## Milestone 4: Per-tool continuity

- [ ] Record the checkpoint last delivered to each tool
- [ ] Generate a bounded delta from that checkpoint
- [ ] Filter by target, purpose, permissions, and token budget
- [ ] Deliver the result through MCP
- [ ] Preview and approve sensitive handoffs

## Milestone 5: Evaluation and public alpha

- [ ] Publish representative cross-tool scenarios
- [ ] Compare against full transcript, latest-session summary, and shared-memory retrieval
- [ ] Measure current-state, supersession, provenance, irrelevant-context, and leakage accuracy
- [ ] Demonstrate the north-star scenario end to end
- [ ] Publish limitations and failure cases

## Explicit boundaries

TaskSeam is not intended to become a general personal-memory database, model host, autonomous computer-use agent, or employee-monitoring system. Integrations with memory systems are welcome when they act as evidence sources or downstream stores.
