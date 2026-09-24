# TaskSeam onboarding

This guide sets up local task continuity for Codex or Claude Code in VS Code, Cursor, or the terminal.

## 1. Install

```bash
pipx install taskseam
```

`pipx` keeps command-line applications isolated. Standard installation also works:

```bash
python3 -m pip install taskseam
```

Confirm the command is available:

```bash
taskseam version
```

## 2. Connect installed agents

Run once from any directory:

```bash
taskseam setup
```

TaskSeam detects Codex and Claude Code on `PATH` and configures the tools it finds. Missing tools are skipped.

## 3. Initialize a project

```bash
cd your-project
taskseam init
```

TaskSeam names the initial task after the project directory, creates `.taskseam/` with a local SQLite database, and adds that directory to `.gitignore`.

## 4. Work normally

Open the initialized project in the Codex or Claude Code editor interface and start a new chat. You can also start either agent from the project terminal.

Ask:

> Continue this project. What accepted decisions, constraints, and open questions should I know?

TaskSeam can retrieve unseen task state and propose saving an explicitly accepted decision, constraint, or unresolved question through the host's tool approval screen.

Speak to the agent normally. When a conclusion becomes durable, approve or reject the TaskSeam action proposed by the agent.

## Expected privacy behavior

- State stays in the project's local `.taskseam/` directory.
- TaskSeam does not upload the database.
- Agent write tools use the host's approval flow.
- Web conversation capture requires a deliberate extension action and review.

Continue with the [editor setup guide](EDITOR_SETUP.md), the [demo](DEMO.md), or the [integration guide](INTEGRATIONS.md).
