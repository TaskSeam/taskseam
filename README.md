# TaskSeam

**Switch AI. Keep working.**

TaskSeam carries the state of your work between AI tools. When a task moves from ChatGPT to Claude to Codex, the next assistant should understand the current goal, accepted decisions, open questions, and relevant evidence without asking you to reconstruct the story.

TaskSeam `0.1.0` is an alpha release. Its local CLI, SQLite store, localhost API, and read-only MCP server work today. Browser capture and automatic state extraction have not been built yet.

## The problem

A real task rarely fits in one conversation. You might explore an idea in ChatGPT, change the design in Claude, and implement it in Codex. Each tool sees only part of the work. Copying a transcript is tedious, and a summary can miss the decision that changed yesterday.

TaskSeam keeps track of the *task* across those conversations and gives each assistant the context it needs to continue.

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

## How TaskSeam is intended to work

1. **Capture with permission.** Collect activity from sources you explicitly enable.
2. **Connect related work.** Recognize when sessions belong to the same task and show uncertainty when a match is unclear.
3. **Track current state.** Distinguish proposals from accepted decisions, preserve open questions, and record superseded decisions.
4. **Prepare a handoff.** Give the next tool a small update with relevant evidence.
5. **Let you correct it.** Make incorrect state and task matches easy to inspect and fix.

The design is local-first: work state stays on your machine by default, with visible capture controls and control over what reaches another assistant.

## Current milestone

The initial proof focuses on **ChatGPT → Claude → Codex** for one project. Success means Codex receives the latest accepted decision, knows what it replaced, retains unresolved questions, and can show where each item came from without receiving unrelated private context.

The remaining work for that proof is browser capture, state extraction, user corrections, and a complete setup flow.

## Development

Run the test suite:

```bash
python3 -m unittest discover -s tests -v
```

TaskSeam is licensed under Apache-2.0. Read [CONTRIBUTING.md](CONTRIBUTING.md) and [SECURITY.md](SECURITY.md) before contributing or reporting a vulnerability.

## Why build in the open?

People should be able to inspect a tool that handles their conversations and work history. Open development also makes it possible to build adapters for different AI tools and evaluate handoff quality in the open.

If this problem matches your workflow, follow the repository or open an issue with a concrete handoff you wish worked better.
