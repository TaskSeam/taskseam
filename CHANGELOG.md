# Changelog

All notable changes to TaskSeam will be documented here.

## 0.1.0 - 2026-09-23

- Add local SQLite task, event, state item, checkpoint, and delta storage.
- Add provenance lookup for decisions, constraints, and questions.
- Add the `taskseam` command-line interface.
- Add a localhost-only JSON API for local integrations.
- Add a read-only MCP server for listing tasks, reading context and deltas, and explaining evidence.
- Add repository initialization, workspace discovery, active-task recording, and status commands.
- Add one-command Codex MCP configuration for initialized workspaces.
- Add review-first conversation state packets with shared source evidence.
- Add question resolution as an evidence-backed state transition.
- Add human correction of supersession relationships between existing state items.
- Add per-target delivery checkpoints and automatic continuation deltas.
