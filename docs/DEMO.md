# End-to-end TaskSeam demo

## One minute, no setup

```bash
pipx install taskseam
taskseam demo
```

`taskseam demo` runs in a temporary directory and touches no agent settings. It shows the whole loop. A decision is made in one agent and replaced in another. A new chat then starts with only current state, a returning agent receives only what changed, and every item keeps its evidence. Record it with any screen recorder, or `asciinema rec -c "taskseam demo"`.

## With real agents

This demonstration proves that one agent can save accepted task state and another can receive only what changed. After setup, the user works through normal conversation rather than maintaining state with CLI commands.

## Prepare a clean project

```bash
taskseam setup
mkdir taskseam-demo
cd taskseam-demo
git init
taskseam init
```

These are one-time setup commands. Open this directory in the Codex or Claude Code editor interface, then start a new agent chat. The optional plugin setup for GitHub Copilot is described in the [editor setup guide](EDITOR_SETUP.md).

## Accept a decision in the first agent

Ask Claude Code or Codex:

> For this local-first application, compare Markdown and SQLite storage. Recommend one approach, but do not treat it as accepted yet.

After reviewing its recommendation, respond:

> I accept SQLite as the authoritative local store. Save that accepted decision for this TaskSeam task.

The agent should propose saving the accepted decision through its normal tool approval screen. Approve it.

## Continue in another agent

Start a different supported agent in the same directory and ask:

> Continue the current project. Summarize its accepted state and where it came from.

The second agent should retrieve the accepted SQLite decision without receiving the full earlier conversation.

Tell the second agent:

> Markdown exports must be deterministic so Git diffs remain stable. I accept this as an active constraint. Save it to TaskSeam.

Approve the proposed TaskSeam write.

## Return to the first agent

Start a new session with the first agent. With the session-start hook installed by `taskseam setup`, you do not need to ask anything special. The session already contains the SQLite decision and the new deterministic-export constraint. To see only what changed, ask:

> Continue this TaskSeam task. Tell me only what changed since you last received it.

The response should contain the newly added deterministic-export constraint.

## Correct state

Tell either agent that a stored item no longer applies, for example:

> We are dropping the deterministic export requirement. Retire it in TaskSeam.

The agent proposes `taskseam_retire` with your reason. After approval, `taskseam show` no longer lists it, and other agents receive it as removed.

If anything does not appear, run `taskseam doctor` in the project folder.

The demo works for any project. The storage topic is example data rather than application logic.

Browser capture is a separate developer preview documented in [`browser-extension/README.md`](../browser-extension/README.md).
