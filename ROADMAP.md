# TaskSeam Roadmap

TaskSeam aims to provide versioned task state across AI tools. This roadmap defines the behavior required to distinguish that product from a generic memory store or transcript handoff.

## Proposed next priorities

The [October 2026 ecosystem review](docs/NEXT_STEPS_RESEARCH.md) recommends:

1. Reliable fresh-chat recovery (released in 0.2.0 with session-start hooks), followed by retry-safe delivery.
2. Reproducible evaluations against transcripts, summaries, maintained Markdown, and memory retrieval.
3. Deterministic exports, auditable corrections, and concurrent-write protection.
4. Budgeted delivery with explicit omissions, then demand-led integrations.

These are recommendations; the research memo separates implemented behavior from future work.

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
- [x] MCP delivery with approved state updates
- [ ] Schema migrations with compatibility tests
  - Version-one migration has a regression test; broader compatibility coverage remains.
- [ ] Export and deletion commands
  - Deterministic JSON/Markdown export and item retirement shipped in 0.2.0; whole-task deletion remains.

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

- [x] Record the checkpoint last delivered to each tool
- [x] Generate a delta from that checkpoint
- [ ] Filter by target, purpose, permissions, and token budget
- [x] Deliver the result through MCP
- [x] Optional full current-state recovery for fresh chats
- [x] Session-start hooks that inject current state in Claude Code and Codex
- [ ] Acknowledge exact snapshots after successful delivery, with retry and concurrency tests
- [ ] Preview and approve sensitive handoffs
- [ ] Package a Claude Desktop extension with explicit project selection

## Milestone 5: Evaluation and public alpha

- [ ] Publish representative cross-tool scenarios
- [ ] Compare against full transcript, latest-session summary, and shared-memory retrieval
- [ ] Measure current-state, supersession, provenance, irrelevant-context, and leakage accuracy
- [ ] Demonstrate the north-star scenario end to end
- [ ] Publish limitations and failure cases

## Explicit boundaries

TaskSeam is not intended to become a general personal-memory database, model host, autonomous computer-use agent, or employee-monitoring system. Integrations with memory systems are welcome when they act as evidence sources or downstream stores.
