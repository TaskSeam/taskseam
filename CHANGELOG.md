# Changelog

All notable changes to TaskSeam will be documented here.

## 0.2.0 - 2026-11-21

Upgrade with `pipx upgrade taskseam` (or `python3 -m pip install -U taskseam`), then rerun
`taskseam setup` to install the session-start hook. Databases upgrade to schema version 4
automatically; once upgraded, they cannot be opened by 0.1.x.

- Add optional full current-state recovery to MCP continuation and CLI handoff
  for fresh chats and lost context, preserving normal per-target deltas.
- Add recovery regression coverage and an evidence-linked next-step research memo.
- Load project state automatically: `taskseam setup` installs a read-only SessionStart hook
  for Claude Code and Codex (`--no-hooks` to skip; `taskseam hook install` to manage it).
- Add `taskseam show`, a readable view of the state agents receive.
- Add `taskseam drop` and the `taskseam_retire` MCP tool. They remove an item that no longer
  applies, recording the reason as an event. The database schema moves to version 4.
- Add deterministic `taskseam export` (JSON with optional history, or Markdown) and
  `--agents-md`, which maintains a marked block in AGENTS.md for agents without MCP.
- Accept unique item ID prefixes in the CLI and MCP tools.
- MCP: negotiate protocol revisions 2025-11-25, 2025-06-18, and 2025-03-26; return
  `structuredContent`; add a `continue` prompt and a current-state resource.
- Briefs with a size budget report omitted item counts instead of truncating silently.

## 0.1.1 - 2026-09-24

- Use the public PyPI installation command throughout the onboarding experience.
- Align package authorship, project descriptions, and search metadata.
- Add editor-first setup guidance for Codex and Claude Code.

## 0.1.0 - 2026-09-23

- Add local SQLite task, event, state item, checkpoint, and delta storage.
- Add provenance lookup for decisions, constraints, and questions.
- Add the `taskseam` command-line interface.
- Add a localhost-only JSON API for local integrations.
- Add an MCP server for task context, evidence, continuation, and approved state updates.
- Add repository initialization, workspace discovery, active-task recording, and status commands.
- Add one-command Codex MCP configuration for initialized workspaces.
- Add review-first conversation state packets with shared source evidence.
- Add question resolution as an evidence-backed state transition.
- Add human correction of supersession relationships between existing state items.
- Add per-target delivery checkpoints and automatic continuation deltas.
- Add automatic Codex and Claude Code setup detection.
- Add a portable agent plugin for Codex, VS Code, and compatible hosts.
- Add approved MCP writes for accepted decisions, constraints, and question resolutions.
- Add an authenticated localhost bridge and reviewed ChatGPT/Claude browser capture preview.
- Add public onboarding, integration, demo, privacy, and landing-page documentation.
