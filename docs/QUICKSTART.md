# TaskSeam onboarding

This guide sets up local task continuity for Codex or Claude Code.

## 1. Install

Until the first PyPI release:

```bash
pipx install git+https://github.com/TaskSeam/taskseam.git
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

Start Codex or Claude Code inside the project. The TaskSeam agent plugin can retrieve unseen task state and propose saving an explicitly accepted decision, constraint, or unresolved question through the host's tool approval screen.

You do not need to run `taskseam record`, manage checkpoints, or copy IDs during normal use. Those commands are advanced controls and fallbacks. Speak to the agent normally; when a conclusion becomes durable, approve or reject the TaskSeam write proposed by the agent.

Useful inspection command:

```bash
taskseam context
```

## Expected privacy behavior

- State stays in the project's local `.taskseam/` directory.
- TaskSeam does not upload the database.
- Agent write tools use the host's approval flow.
- Web conversation capture requires a deliberate extension action and review.

Continue with the [demo](DEMO.md) or choose another tool in the [integration guide](INTEGRATIONS.md).
