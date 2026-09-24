# TaskSeam

**Switch AI. Keep working.**

TaskSeam keeps the accepted state of a project available when work moves between Codex, Claude Code, VS Code agents, ChatGPT, and Claude.

[Website](https://taskseam.github.io/taskseam/) · [Editor setup](docs/EDITOR_SETUP.md) · [Quick start](docs/QUICKSTART.md) · [Demo](docs/DEMO.md) · [Privacy](PRIVACY.md)

> **Public alpha:** The local CLI, MCP server, agent plugin, project state, provenance, and per-agent continuation are working. The browser extension is a developer preview. PyPI and extension-store distribution are being prepared.

## Quick start

Install TaskSeam:

```bash
pipx install git+https://github.com/TaskSeam/taskseam.git
```

Connect the supported agents installed on your computer:

```bash
taskseam setup
```

Enable TaskSeam in a project:

```bash
cd your-project
taskseam init
```

Now open the project in **Codex for VS Code/Cursor**, **Claude Code for VS Code**, or their terminal interface and start a new chat. TaskSeam supplies the project's accepted decisions, active constraints, unresolved questions, and changes the agent has not seen. Durable changes use the agent's normal tool-approval screen.

Start with this prompt:

> Continue this project. What accepted decisions, constraints, and open questions should I know?

There are no routine TaskSeam commands after initialization.

## What changes for the user?

Without TaskSeam:

1. Explain the project again.
2. Paste an earlier conversation.
3. Correct an outdated summary.
4. Repeat when switching tools.

With TaskSeam:

1. Start an agent in the project.
2. Continue the work.
3. Approve durable project changes when prompted.

TaskSeam stores project state locally under `.taskseam/`, which it adds to `.gitignore`.

## Supported surfaces

| Surface | Current experience |
|---|---|
| Codex in VS Code/Cursor and CLI | Working alpha through shared MCP configuration |
| Claude Code in VS Code and terminal | Working alpha through user scoped MCP configuration |
| VS Code with GitHub Copilot | Working alpha through the portable agent plugin |
| ChatGPT and Claude websites | Developer-preview browser extension with explicit review |
| Claude Desktop general chat | Planned desktop extension with project selection |

See the [editor setup guide](docs/EDITOR_SETUP.md) for the exact UI steps and the [integration guide](docs/INTEGRATIONS.md) for technical details.

## Why this is different from shared memory

Shared memory retrieves potentially relevant facts. Session summaries describe what happened in one conversation. TaskSeam maintains the current state of a project, preserves what changed, and tracks what each agent has already received.

```text
Claude discussion ─┐
ChatGPT decision ──┼─> current project state ─> unseen changes ─> Codex
Code and Git ──────┘            │                       │
                            provenance              per agent
```

The goal is a small, explainable continuation rather than a transcript dump.

## Privacy model

- Project state stays on the user's computer by default.
- Agent writes use the host's approval flow.
- Browser capture starts only after an explicit user action.
- Browser results remain editable before saving.
- TaskSeam does not operate an analytics, advertising, or hosted synchronization service.

Read [PRIVACY.md](PRIVACY.md) and [SECURITY.md](SECURITY.md) for the current alpha boundaries.

## Try the complete flow

The [five-minute demo](docs/DEMO.md) starts with a clean directory, accepts a project decision in one agent, continues in another, and verifies that the first agent later receives only what changed.

## Project status

The public roadmap is in [ROADMAP.md](ROADMAP.md). Current priorities are:

1. Validate clean installation across supported operating systems.
2. Publish the Python package to PyPI.
3. Package and submit the browser extension.
4. Improve automatic task matching and correction.
5. Publish repeatable continuity evaluations.

## Development

```bash
git clone https://github.com/TaskSeam/taskseam.git
cd taskseam
python3 -m venv .venv
.venv/bin/python -m pip install -e .
.venv/bin/python -m unittest discover -s tests -v
```

TaskSeam is licensed under Apache-2.0. Contributions are welcome through focused issues and pull requests. Read [CONTRIBUTING.md](CONTRIBUTING.md) before making broad architecture changes.
