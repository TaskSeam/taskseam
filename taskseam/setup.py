"""Configuration helpers for supported AI tools."""

import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

# Editor extensions bundle their own agent CLI. Users who only install the
# VS Code/Cursor extension have no `claude` or `codex` on PATH.
EDITOR_EXTENSION_DIRS = (".vscode/extensions", ".vscode-insiders/extensions",
                         ".cursor/extensions", ".windsurf/extensions")
BUNDLED = {
    "claude": ("anthropic.claude-code-*", ("resources/native-binary/claude",
                                           "resources/native-binary/claude.exe")),
    "codex": ("openai.chatgpt-*", ("bin/*/codex", "bin/*/codex.exe")),
}


def _version_key(path):
    match = re.search(r"-(\d+(?:\.\d+)*)", path.name)
    return tuple(int(part) for part in match.group(1).split(".")) if match else ()


def find_agent(name, home=None):
    """Return (executable, how_found) for an agent CLI, or (None, None)."""
    on_path = shutil.which(name)
    if on_path:
        return on_path, "PATH"
    pattern, binaries = BUNDLED[name]
    home = Path(home or Path.home())
    candidates = []
    for base in EDITOR_EXTENSION_DIRS:
        for extension in (home / base).glob(pattern):
            for binary in binaries:
                candidates.extend((extension, found) for found in extension.glob(binary)
                                  if found.is_file() and os.access(str(found), os.X_OK))
    if not candidates:
        return None, None
    extension, found = max(candidates, key=lambda pair: _version_key(pair[0]))
    return str(found), "editor extension " + extension.name


def codex_command(python_executable=None):
    codex = find_agent("codex")[0]
    if not codex:
        raise ValueError("Codex was not found on PATH or in a VS Code/Cursor extension")
    python = python_executable or sys.executable
    return [codex, "mcp", "add", "taskseam", "--", python, "-m", "taskseam", "mcp"]


def claude_command(python_executable=None):
    claude = find_agent("claude")[0]
    if not claude:
        raise ValueError("Claude Code was not found on PATH or in a VS Code/Cursor extension")
    python = python_executable or sys.executable
    return [claude, "mcp", "add", "--scope", "user", "taskseam", "--",
            python, "-m", "taskseam", "mcp"]


def setup_codex(python_executable=None, dry_run=False):
    command = codex_command(python_executable)
    if dry_run:
        return {"configured": False, "command": command}

    existing = subprocess.run([command[0], "mcp", "get", "taskseam"],
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if existing.returncode == 0:
        removed = subprocess.run([command[0], "mcp", "remove", "taskseam"],
                                 capture_output=True, text=True)
        if removed.returncode != 0:
            raise ValueError(removed.stderr.strip() or "Could not update the existing TaskSeam MCP server")
    added = subprocess.run(command, capture_output=True, text=True)
    if added.returncode != 0:
        raise ValueError(added.stderr.strip() or "Could not configure TaskSeam in Codex")
    return {"configured": True, "server": "taskseam", "command": command,
            "message": added.stdout.strip()}


def setup_claude(python_executable=None, dry_run=False):
    command = claude_command(python_executable)
    if dry_run:
        return {"configured": False, "command": command}

    existing = subprocess.run([command[0], "mcp", "get", "taskseam"],
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if existing.returncode == 0:
        removed = subprocess.run([command[0], "mcp", "remove", "--scope", "user", "taskseam"],
                                 capture_output=True, text=True)
        if removed.returncode != 0:
            raise ValueError(removed.stderr.strip() or
                             "Could not update the existing TaskSeam MCP server")
    added = subprocess.run(command, capture_output=True, text=True)
    if added.returncode != 0:
        raise ValueError(added.stderr.strip() or "Could not configure TaskSeam in Claude Code")
    return {"configured": True, "server": "taskseam", "command": command,
            "message": added.stdout.strip()}


def setup_detected(python_executable=None, dry_run=False):
    """Configure every supported local agent found on PATH."""
    installers = (("codex", setup_codex), ("claude-code", setup_claude))
    detected = []
    skipped = []
    for name, installer in installers:
        executable = "claude" if name == "claude-code" else name
        found, how = find_agent(executable)
        if not found:
            skipped.append({"tool": name,
                            "reason": "not found on PATH or in a VS Code/Cursor extension"})
            continue
        result = installer(python_executable, dry_run)
        detected.append({"tool": name, "found_via": how, **result})
    return {"configured": detected, "skipped": skipped,
            "web_assistants": "ChatGPT and Claude web support is available as a developer-preview browser extension"}
