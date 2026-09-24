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
