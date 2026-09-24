"""Configuration helpers for supported AI tools."""

import shutil
import subprocess
import sys


def codex_command(python_executable=None):
    codex = shutil.which("codex")
    if not codex:
        raise ValueError("Codex CLI was not found on PATH")
    python = python_executable or sys.executable
    return [codex, "mcp", "add", "taskseam", "--", python, "-m", "taskseam", "mcp"]


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
