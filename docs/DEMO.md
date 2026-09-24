# End-to-end TaskSeam demo

This demonstration proves that one agent can save accepted task state and another can receive only what changed. After setup, the user works through normal conversation rather than maintaining state with CLI commands.

## Prepare a clean project

```bash
mkdir taskseam-demo
cd taskseam-demo
git init
taskseam init "Choose storage for a local-first application"
taskseam setup
```

These are one-time setup commands. Install the TaskSeam agent plugin as described in the [integration guide](INTEGRATIONS.md), then start a new agent session in this directory.

## Accept a decision in the first agent

Ask Claude Code or Codex:

> For this local-first application, compare Markdown and SQLite storage. Recommend one approach, but do not treat it as accepted yet.

After reviewing its recommendation, respond:

> I accept SQLite as the authoritative local store. Save that accepted decision for this TaskSeam task.

The agent should propose a `taskseam_record` write through its normal tool approval screen. Approve it.

## Continue in another agent

Start a different supported agent in the same directory and ask:

> Continue this TaskSeam task. Summarize its accepted state with source evidence.

The second agent should retrieve the accepted SQLite decision without receiving the full earlier conversation.

Tell the second agent:

> Markdown exports must be deterministic so Git diffs remain stable. I accept this as an active constraint. Save it to TaskSeam.

Approve the proposed TaskSeam write.

## Return to the first agent

Start a new session with the first agent and ask:

> Continue this TaskSeam task. Tell me only what changed since you last received it.

The response should contain the newly added deterministic-export constraint.

## Inspect the local state

This optional command lets you inspect what the agents saved:

```bash
taskseam context
```

This output should show the accepted decision and constraint with their sources. The demo works for any task title and state; the storage topic is example data rather than application logic.

If an agent does not support MCP writes, use the CLI commands documented under **Manual and advanced state commands** in the main README.

## Optional browser capture

The browser extension is currently a developer preview:

1. Clone the TaskSeam repository.
2. Run `taskseam serve` in this demo project and keep it running.
3. Load the repository's `browser-extension` directory from `chrome://extensions` using **Load unpacked**.
4. Send the output of `taskseam prompt` to ChatGPT or Claude.
5. Open TaskSeam Capture, pair it using the displayed token, review the detected packet, and save it.

The extension does not capture a page until the user selects **Read latest AI response**.
