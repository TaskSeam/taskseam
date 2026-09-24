# Use TaskSeam in your editor

TaskSeam works inside supported editor agents. You do not need to operate TaskSeam from a separate terminal after setup.

## One-time setup

Install TaskSeam and connect the agents already installed on your computer:

```bash
pipx install taskseam
taskseam setup
```

Run this once in every project that should have its own TaskSeam state:

```bash
cd your-project
taskseam init
```

Then restart the editor or begin a new agent chat.

## Codex in VS Code or Cursor

1. Open the initialized project in VS Code or Cursor.
2. Open the Codex panel and start a new local chat.
3. Ask: **“Continue this project. What accepted decisions, constraints, and open questions should I know?”**
4. Work normally. When you explicitly accept a durable conclusion, Codex can ask permission to save it through TaskSeam.

Codex CLI and the Codex IDE extension share MCP configuration, so `taskseam setup` configures both. See the [official OpenAI MCP documentation](https://developers.openai.com/learn/docs-mcp).

## Claude Code in VS Code

1. Open the initialized project in VS Code.
2. Open the Claude Code panel and start a new chat.
3. Ask: **“Continue this project using its TaskSeam state.”**
4. Work normally and approve TaskSeam updates when Claude proposes saving an accepted conclusion.

`taskseam setup` registers TaskSeam in Claude Code's user scoped MCP configuration, which makes it available across initialized projects on that computer.

## GitHub Copilot Agent mode

1. Confirm `taskseam version` works in the VS Code terminal.
2. Enable the `chat.plugins.enabled` VS Code setting.
3. Run **Chat: Install Plugin From Source** from the Command Palette.
4. Enter `https://github.com/TaskSeam/taskseam`.
5. Open an initialized project, start an Agent mode chat, and ask it to continue the project using TaskSeam.

## Current UI coverage

| Interface | Status | How it connects |
|---|---|---|
| Codex IDE extension for VS Code/Cursor | Supported alpha | Shared Codex MCP configuration |
| Claude Code extension for VS Code | Supported alpha | Claude Code user scoped MCP configuration |
| GitHub Copilot Agent mode | Supported alpha | Portable TaskSeam agent plugin |
| Codex CLI and Claude Code terminal | Supported alpha | Local MCP configuration |
| ChatGPT and Claude websites | Developer preview | Reviewed browser extension capture |
| Claude Desktop general chat | Planned | Requires a packaged desktop extension and project selector |

TaskSeam is project scoped. Open the editor agent inside the initialized project so it can discover that project's `.taskseam` state.
