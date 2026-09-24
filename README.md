# TaskSeam

**Switch AI. Keep working.**

[Website](https://taskseam.github.io/taskseam/) · [Five-minute demo](docs/DEMO.md) · [Integrations](docs/INTEGRATIONS.md) · [Privacy](PRIVACY.md)

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

> **Alpha status:** `0.1.0` provides the local CLI, SQLite state model, checkpoints, deltas, authenticated localhost API, MCP delivery, an agent plugin, and reviewed browser capture. Automatic task matching, extraction from arbitrary conversations, polished correction UX, and store distribution are still under development.

## Try TaskSeam in five minutes

The shortest working path uses Codex or Claude Code. These are one-time setup commands, plus one initialization command for each project that should participate:

```bash
pipx install git+https://github.com/TaskSeam/taskseam.git
taskseam setup
cd your-project
taskseam init "Describe the work you want to continue"
```

Start a new agent session in that project. TaskSeam can deliver current task state, remember only conclusions you explicitly accept, and send that agent only later changes on its next visit.

After these setup commands, work through normal conversation. You should not need to run `taskseam record`, create checkpoints, copy item IDs, or request handoffs manually. Those commands remain available for inspection, scripting, correction, and clients that do not support MCP writes. TaskSeam's MCP server tells compatible agents to retrieve unseen state and propose recording only decisions you explicitly accept, active constraints, and unresolved questions through the host's approval flow.

For a guided proof using two AI tools, follow the [end-to-end demo](docs/DEMO.md). For setup by tool, see the [integration guide](docs/INTEGRATIONS.md).

### What is available today?

| Surface | Current experience | Distribution status |
|---|---|---|
| Codex CLI and IDE extension | MCP plus installable TaskSeam agent plugin | Working alpha |
| Claude Code | MCP configured by `taskseam setup` | Working alpha |
| VS Code with Copilot Agent mode | Portable TaskSeam agent plugin | Working alpha; install from source |
| ChatGPT and Claude websites | Reviewed capture extension plus local bridge | Developer preview; unpacked extension |

The browser extension is not in the Chrome Web Store yet. PyPI publishing is also pending, so the current install command uses GitHub. These limitations are stated here so visitors can distinguish the working alpha from the intended one-click public experience.

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

The alpha records and compares these changes through CLI commands, agent-approved MCP writes, or reviewed browser packets. MCP then delivers stored context or only unseen changes to another AI tool.

## Install

TaskSeam requires Python 3.9 or newer. After the first PyPI release, installation will be:

```bash
python3 -m pip install taskseam
```

Because TaskSeam is a command-line application, [`pipx`](https://pipx.pypa.io/) is also a good option when you want it isolated from your other Python packages: `pipx install taskseam`.

For the current alpha, install directly from GitHub:

```bash
pipx install git+https://github.com/TaskSeam/taskseam.git
```

For local development:

```bash
git clone https://github.com/TaskSeam/taskseam.git
cd taskseam
python3 -m pip install -e .
```

After installation, use the [onboarding guide](docs/QUICKSTART.md) for the shortest setup.

## Manual and advanced state commands

Initialize TaskSeam in a repository if you have not already followed the quick start:

```bash
cd my-project
taskseam init "Build capture prototype"
taskseam setup
taskseam prompt
```

This creates private repository-local storage, an active task, and a `.taskseam/` Git ignore rule. Normal commands discover the workspace from the current directory or any directory beneath it.

```bash
taskseam record decision "Use SQLite" --source claude
taskseam record question "How should browser capture permissions work?" --source claude
taskseam checkpoint
taskseam context
taskseam status
taskseam handoff --to codex
```

Use `--supersedes ITEM_ID` with `taskseam record` when a new item replaces an earlier item. The advanced `task`, `item`, `delta`, and `explain` commands accept explicit IDs for scripting and multi-task workflows.

Resolve an open question into an accepted decision while preserving its history:

```bash
taskseam resolve QUESTION_ID \
  "Keep SQLite canonical and export deterministic Markdown" \
  --source codex \
  --supersedes EARLIER_DECISION_ID
```

If two existing items were imported without their relationship, correct it with `taskseam supersede OLD_ITEM_ID --with NEW_ITEM_ID`.

`taskseam handoff --to codex` returns the current state on first delivery and only the checkpoint delta on later deliveries. Each target has an independent delivery checkpoint. The equivalent `taskseam_continue` MCP tool performs the same operation and marks the returned changes as delivered.

Output is JSON. CLI source names are labels entered by the caller. Browser imports retain the reviewed assistant response as local evidence.

## Import reviewed state from a conversation

Run `taskseam prompt` and send its output at the end of a ChatGPT or Claude conversation. Save the returned JSON as `taskseam-packet.json`, then preview it:

```bash
taskseam import taskseam-packet.json --source claude-web
```

Nothing is stored during preview. After checking that proposals were not presented as accepted decisions and that sensitive context is absent, apply the packet:

```bash
taskseam import taskseam-packet.json --source claude-web --apply
```

All imported items link to the original packet as evidence. This reviewed import is an interim bridge for web assistants; automatic permissioned capture and extraction remain roadmap work.

Outside an initialized workspace, TaskSeam stores data at `~/.local/share/taskseam/taskseam.db`. Set `TASKSEAM_DB` or use `--db` to choose another path explicitly.

## Connect agents with one setup command

TaskSeam exposes MCP tools for listing tasks, reading current context, comparing checkpoints, explaining evidence, and delivering the changes an agent has not seen yet.

Run this once from any directory to auto-detect and configure supported local agents:

```bash
taskseam setup
```

Today this configures Codex and Claude Code when their CLIs are installed. Use `taskseam setup codex` or `taskseam setup claude-code` to configure only one. The stdio MCP server discovers the active workspace when an agent launches it, so the same user-level configuration works across initialized repositories. Codex CLI and its IDE extension share MCP configuration, as described in the [official OpenAI MCP setup documentation](https://developers.openai.com/learn/docs-mcp). Claude Code supports the same local stdio MCP pattern through its [official MCP integration](https://docs.anthropic.com/en/docs/claude-code/mcp).

## Install the agent plugin

The repository includes a portable TaskSeam agent plugin under `plugins/taskseam`. It bundles the MCP connection and instructions that tell an agent to retrieve unseen state, preserve provenance, and record only conclusions the user explicitly accepts.

For local Codex testing, add this repository as a plugin marketplace, open `/plugins`, and install TaskSeam:

```bash
codex plugin marketplace add TaskSeam/taskseam
```

Start a new agent session after installation. The Python package must also be installed so the plugin can run the local `taskseam mcp` command. MCP write tools use the host's approval UI before recording durable state.

### Visual Studio Code

TaskSeam supports both common agent paths in VS Code:

- **Codex extension:** run `taskseam setup` once. Codex CLI and the Codex IDE extension share MCP configuration.
- **GitHub Copilot Agent mode:** TaskSeam's portable Agent Plugin supplies both the continuity skill and MCP server.

To install the plugin for Copilot:

1. Confirm `taskseam version` works in VS Code's integrated terminal.
2. Enable the `chat.plugins.enabled` VS Code setting.
3. Run **Chat: Install Plugin From Source** from the Command Palette.
4. Enter `https://github.com/TaskSeam/taskseam` and approve the repository trust prompt.
5. Start a new Agent mode chat inside a repository initialized with `taskseam init`.

You can inspect or disable it from the **Agent Plugins - Installed** section of the Extensions view. VS Code documents portable plugin installation and controls in its [Agent plugins guide](https://code.visualstudio.com/docs/agent-customization/agent-plugins).

Claude.ai and ChatGPT web sessions cannot start a local stdio process. The alpha browser extension under `browser-extension/` connects them to TaskSeam through an authenticated localhost bridge.

### ChatGPT and Claude browser capture

Run the bridge from the initialized project whose active task should receive the capture:

```bash
taskseam serve
```

TaskSeam prints a workspace-specific pairing token. For local testing, open `chrome://extensions`, enable Developer mode, choose **Load unpacked**, and select the repository's `browser-extension` directory. Open the extension on `chatgpt.com` or `claude.ai`, enter the token once, and select **Read latest AI response**.

The latest assistant response must contain the JSON produced from `taskseam prompt`. The extension shows every detected item for editing or removal before anything is saved. It does not capture pages in the background. Chrome Web Store packaging and more resilient site adapters remain release work.

Advanced users can still register a fixed database manually:

```bash
codex mcp add taskseam --env TASKSEAM_DB=/absolute/path/to/taskseam.db -- taskseam mcp
```

## Local integration API

Run the API for the browser extension or another local client:

```bash
taskseam serve
curl http://127.0.0.1:8765/health
```

The API only accepts localhost bind addresses and browser writes require the workspace pairing token. Do not expose it through a public interface, tunnel, or proxy.

Available endpoints:

- `GET /health`
- `GET /v1/active`
- `POST /v1/active/import`
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
