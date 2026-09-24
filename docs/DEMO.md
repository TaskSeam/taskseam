# End-to-end TaskSeam demo

This demonstration proves that one tool can add task state and another tool can receive only what changed.

## Prepare a clean project

```bash
mkdir taskseam-demo
cd taskseam-demo
git init
taskseam init "Choose storage for a local-first application"
taskseam setup
```

## Record an initial decision

```bash
taskseam record decision \
  "Use SQLite as the authoritative local store" \
  --source user
```

Start Codex or Claude Code in this directory and ask:

> Continue this TaskSeam task and summarize its accepted state with source evidence.

The agent should retrieve the SQLite decision through TaskSeam.

## Add a change from another source

In another terminal:

```bash
taskseam record constraint \
  "Exports must be deterministic so Git diffs remain stable" \
  --source user
```

Start a new session with the first agent and ask:

> Continue this TaskSeam task. Tell me only what changed since you last received it.

The response should contain only the newly added deterministic-export constraint.

## Verify the stored state

```bash
taskseam context
```

This output should show the accepted decision and constraint with their sources. The demo works for any task title and state; the storage topic is example data rather than application logic.

## Optional browser capture

The browser extension is currently a developer preview:

1. Clone the TaskSeam repository.
2. Run `taskseam serve` in this demo project and keep it running.
3. Load the repository's `browser-extension` directory from `chrome://extensions` using **Load unpacked**.
4. Send the output of `taskseam prompt` to ChatGPT or Claude.
5. Open TaskSeam Capture, pair it using the displayed token, review the detected packet, and save it.

The extension does not capture a page until the user selects **Read latest AI response**.
