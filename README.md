# TaskSeam

**Switch AI. Keep working.**

TaskSeam is being built as a **local-first, versioned task-state layer** for work that crosses AI tools. Its goal is to reconstruct the current state of a task, record how that state changed, and give each assistant only the delta it has not seen—with source evidence for every item.

```text
ChatGPT discussion ─┐
Claude decision ────┼─> task identity ─> versioned state ─> per-tool delta ─> Codex
Git/code changes ───┘        │                 │                 │
                         confidence       provenance       permission scope
```

TaskSeam is built around four questions:

1. Which activity belongs to the task being continued?
2. What is currently accepted, open, completed, or superseded?
3. What changed since this particular tool last participated?
4. What evidence supports every item delivered?

> **Alpha status:** `0.1.0` provides the local CLI, SQLite state model, checkpoints, deltas, localhost API, and read-only MCP delivery. Task matching, automatic extraction, browser capture, and correction UX are still under development. The current release is the foundation, not the completed vision.

## The problem

A real task rarely fits in one conversation. You might explore an idea in ChatGPT, change the design in Claude, and implement it in Codex. Each tool sees only part of the work. Copying a transcript is tedious, and a summary can miss the decision that changed yesterday.

TaskSeam treats the *task* as the durable object. Conversations, agent sessions, commits, and files are evidence about that task.

## How this differs from shared memory

Shared memory and session-handoff projects already solve useful parts of cross-agent continuity. TaskSeam is pursuing a different output: the **current, versioned state of work and the change since a specific collaborator last saw it**.

| Approach | Primary output | Typical question |
|---|---|---|
| Shared memory | Retrieved facts or notes | “What might be relevant?” |
| Session handoff | A point-in-time summary or transcript | “What happened in that session?” |
| TaskSeam | Current task state plus a checkpoint delta and evidence | “What changed, what is authoritative now, and why?” |

The distinction only matters if TaskSeam can reliably identify tasks, separate proposals from decisions, preserve unresolved questions, represent supersession, exclude unrelated context, and explain its result. These are release criteria rather than marketing claims. See [ROADMAP.md](ROADMAP.md).

## What a handoff looks like

Suppose you discuss a feature in ChatGPT, then decide in Claude to use SQLite instead of a Markdown state file. TaskSeam can provide Codex with:

```text
Task: Build the local capture prototype

Current decision: Use SQLite for local storage.
Changed since the last handoff: The Markdown state file was superseded.
Open question: How should browser capture permissions work?

Each item links back to the event that supports it.
```

The alpha can record and compare these changes when you enter them manually, and MCP can deliver the stored context to an AI tool. Automatic capture and detection are planned.

## Install

TaskSeam requires Python 3.9 or newer. Install it from PyPI with:

```bash
python3 -m pip install taskseam
```

Because TaskSeam is a command-line application, [`pipx`](https://pipx.pypa.io/) is also a good option when you want it isolated from your other Python packages: `pipx install taskseam`.

Until the first PyPI release is available, install directly from GitHub:

```bash
pipx install git+https://github.com/TaskSeam/taskseam.git
```

For local development:

```bash
git clone https://github.com/TaskSeam/taskseam.git
cd taskseam
python3 -m pip install -e .
```

## Record task state

Create a task:

```bash
taskseam --db .taskseam/state.db task create "Build capture prototype"
```

The command prints a task ID. Use that ID below; each item and checkpoint command also prints an ID.

```bash
taskseam --db .taskseam/state.db item TASK_ID decision "Use Markdown" --source chatgpt
taskseam --db .taskseam/state.db checkpoint TASK_ID
taskseam --db .taskseam/state.db item TASK_ID decision "Use SQLite" --source claude --supersedes FIRST_ITEM_ID
taskseam --db .taskseam/state.db item TASK_ID question "How should browser capture permissions work?" --source claude
taskseam --db .taskseam/state.db checkpoint TASK_ID
taskseam --db .taskseam/state.db delta FIRST_CHECKPOINT_ID SECOND_CHECKPOINT_ID
taskseam --db .taskseam/state.db context TASK_ID
taskseam --db .taskseam/state.db explain SQLITE_ITEM_ID
```

Output is JSON. Source names are labels you enter manually; the alpha does not verify or capture those sources.

Without `--db`, TaskSeam stores data at `~/.local/share/taskseam/taskseam.db`. Set `TASKSEAM_DB` to choose another default path. A repository-local `.taskseam/` directory is ignored by this repository's Git configuration.

## Connect Codex with MCP

TaskSeam exposes read-only MCP tools for listing tasks, reading current context, comparing checkpoints, and explaining an item's source.

After installing TaskSeam:

```bash
codex mcp add taskseam -- taskseam mcp
codex mcp list
```

The Codex CLI and IDE extension share MCP configuration, as described in the [official OpenAI MCP setup documentation](https://developers.openai.com/learn/docs-mcp).

To use a specific database:

```bash
codex mcp add taskseam --env TASKSEAM_DB=/absolute/path/to/taskseam.db -- taskseam mcp
```

## Local integration API

Run the API for a future browser extension or another local client:

```bash
taskseam serve
curl http://127.0.0.1:8765/health
```

The API only accepts localhost bind addresses. It has no authentication and must not be exposed through a public interface, tunnel, or proxy.

Available endpoints:

- `GET /health`
- `GET|POST /v1/tasks`
- `GET /v1/tasks/{task_id}/context`
- `POST /v1/tasks/{task_id}/items`
- `POST /v1/tasks/{task_id}/checkpoint`
- `POST /v1/delta`
- `GET /v1/items/{item_id}`

## How TaskSeam works toward that goal

1. **Capture with permission.** Collect activity from sources you explicitly enable.
2. **Connect related work.** Recognize when sessions belong to the same task and show uncertainty when a match is unclear.
3. **Track current state.** Distinguish proposals from accepted decisions, preserve open questions, and record superseded decisions.
4. **Prepare a handoff.** Give the next tool a small update with relevant evidence.
5. **Let you correct it.** Make incorrect state and task matches easy to inspect and fix.

The design is local-first: work state stays on your machine by default, with visible capture controls and control over what reaches another assistant.

## Current milestone

The initial proof focuses on **ChatGPT → Claude → Codex** for one project. Success means Codex receives the latest accepted decision, knows what it replaced, retains unresolved questions, and can show where each item came from without receiving unrelated private context.

The public acceptance scenario and remaining milestones are tracked in [ROADMAP.md](ROADMAP.md).

## Development

Run the test suite:

```bash
python3 -m unittest discover -s tests -v
```

TaskSeam is licensed under Apache-2.0. Read [CONTRIBUTING.md](CONTRIBUTING.md) and [SECURITY.md](SECURITY.md) before contributing or reporting a vulnerability.

## Why build in the open?

People should be able to inspect a tool that handles their conversations and work history. Open development also makes it possible to build adapters for different AI tools and evaluate handoff quality in the open.

If this problem matches your workflow, follow the repository or open an issue with a concrete handoff you wish worked better.
