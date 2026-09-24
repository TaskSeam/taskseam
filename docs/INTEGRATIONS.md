# TaskSeam integration guide

Choose the AI surface you use. Every integration writes to the same local TaskSeam state model.

## Codex CLI or Codex IDE extension

```bash
taskseam setup codex
```

Codex CLI and the Codex IDE extension share their MCP configuration. The optional TaskSeam agent plugin also supplies continuity behavior:

```bash
codex plugin marketplace add TaskSeam/taskseam
codex plugin add taskseam@taskseam
```

Start a new Codex session after installing the plugin.

## Claude Code

```bash
taskseam setup claude-code
```

Start a new Claude Code session inside an initialized TaskSeam project.

## Visual Studio Code with GitHub Copilot

1. Confirm `taskseam version` works in the integrated terminal.
2. Enable the `chat.plugins.enabled` setting.
3. Run **Chat: Install Plugin From Source** from the Command Palette.
4. Enter `https://github.com/TaskSeam/taskseam`.
5. Start a new Copilot Agent mode chat in a project initialized with `taskseam init`.

## ChatGPT or Claude website

The browser extension is an unpacked developer preview and has not been published to the Chrome Web Store. Its development setup is documented separately in [`browser-extension/README.md`](../browser-extension/README.md) so the normal onboarding remains focused on supported agent integrations.

Other AI clients require local MCP support or a dedicated TaskSeam adapter. They are not presented as supported until their complete flow has been tested.
