# TaskSeam integration guide

Choose the AI surface you use. Every integration writes to the same local TaskSeam state model.

## Codex IDE extension or CLI

```bash
taskseam setup codex
```

Codex CLI and the Codex IDE extension for VS Code or Cursor share their MCP configuration. After setup, restart the editor, open an initialized project, and start a new Codex chat. The optional TaskSeam agent plugin also supplies continuity behavior:

```bash
codex plugin marketplace add TaskSeam/taskseam
codex plugin add taskseam@taskseam
```

Start a new Codex session after installing the plugin.

## Claude Code extension or terminal

```bash
taskseam setup claude-code
```

Restart VS Code after setup. Open an initialized TaskSeam project and start a new chat from the Claude Code panel, or run Claude Code in that project's terminal.

## Visual Studio Code with GitHub Copilot

1. Confirm `taskseam version` works in the integrated terminal.
2. Enable the `chat.plugins.enabled` setting.
3. Run **Chat: Install Plugin From Source** from the Command Palette.
4. Enter `https://github.com/TaskSeam/taskseam`.
5. Start a new Copilot Agent mode chat in a project initialized with `taskseam init`.

## ChatGPT or Claude website

The browser extension is an unpacked developer preview and has not been published to the Chrome Web Store. Its development setup is documented separately in [`browser-extension/README.md`](../browser-extension/README.md) so the normal onboarding remains focused on supported agent integrations.

Other AI clients require local MCP support or a dedicated TaskSeam adapter. They are not presented as supported until their complete flow has been tested.

## Claude Desktop general chat

Claude Desktop uses a separate desktop-extension system and does not automatically inherit Claude Code's project working directory. TaskSeam does not currently present it as supported. A packaged desktop extension with an explicit project selector is planned.

See the [editor setup guide](EDITOR_SETUP.md) for the complete interface matrix.

## Load state automatically at session start

`taskseam setup` also installs a read-only SessionStart hook for Claude Code
(`~/.claude/settings.json`) and Codex (`~/.codex/hooks.json`, or `$CODEX_HOME`).
Both hosts add the hook's output to the model's context. Every new, resumed,
cleared, or compacted session therefore starts with the project's accepted
decisions, active constraints, and open questions, even if the model never
calls a TaskSeam tool.

- The hook prints nothing outside an initialized project and never blocks a session.
- It does not advance any agent's delivery position, so `taskseam_continue` deltas are unaffected.
- Output stays under 6,000 characters, below both hosts' limits. Items that do not fit are
  counted explicitly rather than silently dropped.
- Codex runs a new hook only after you review and trust it with `/hooks`.
- Existing settings are preserved. A one-time `*.taskseam-backup` copy is written beside the file.

Install or refresh only the hook with `taskseam hook install [claude-code|codex]`,
preview the change with `--dry-run`, or skip it during setup with `taskseam setup --no-hooks`.

## MCP prompt and resource

Besides its tools, the MCP server exposes:

- a `continue` prompt. Claude Code shows it as `/mcp__taskseam__continue`, which loads state on demand;
- a `taskseam://active/brief` Markdown resource with the current state.

The server negotiates MCP protocol revisions 2025-11-25, 2025-06-18, and 2025-03-26,
and tool results include `structuredContent` alongside the JSON text.

## Agents without MCP: AGENTS.md

Agents that read `AGENTS.md` but cannot reach TaskSeam (Cursor rules, Gemini CLI,
Jules, Windsurf, and others) can receive a generated copy of the current state:

```bash
taskseam export --agents-md          # or --agents-md docs/AGENTS.md
```

TaskSeam maintains only the block between `<!-- taskseam:start -->` and
`<!-- taskseam:end -->`. The rest of the file is left untouched, and rerunning the
command replaces the block. `AGENTS.md` is usually committed, so review the block
before pushing. Your state then leaves the private `.taskseam/` directory.

Other exports are deterministic:

```bash
taskseam export                      # current state as JSON (schema "taskseam_export": 1)
taskseam export --history            # include superseded, resolved, and retired items
taskseam export --format markdown -o STATE.md
```

## Recover state in a fresh chat

In a fresh chat or after losing prior context, call `taskseam_continue` with
`{"target": "codex", "full": true}` (use the receiving agent's stable target name).
In an initialized workspace the task is inferred; otherwise supply `task_id`.
The CLI equivalent is:

```bash
taskseam handoff --to codex --full
```

`current` contains all current items, while `added` and `removed` remain the
changes since that target's previous delivery. `changed: false` means no new
changes, not an empty task. Ordinary continuation omits `current` to keep
responses small. Recovery does not reset other agents' delivery positions.
This option requires TaskSeam 0.2.0 or later.
