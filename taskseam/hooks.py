"""Session-start hooks that load TaskSeam state without relying on a tool call.

Claude Code and Codex both run SessionStart hooks and add their plain stdout to
the model's context. TaskSeam uses that to put current project state into every
new, cleared, compacted, or resumed session. The hook is read-only: it does not
advance any agent's delivery position, so ``taskseam_continue`` deltas still work.
"""

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

from .render import brief
from .store import Store
from .workspace import active_task, database_path, find_workspace

HOOK_MARKER = "taskseam hook session-start"
MATCHER = "startup|resume|clear|compact"
# Claude Code caps hook context at 10,000 characters; Codex defaults to about
# 2,500 tokens. Stay below both so the brief is never truncated by the host.
BUDGET = 6000
GUIDANCE = ("TaskSeam is connected for this project. When the user explicitly accepts a decision, "
            "sets a constraint, or leaves a material question open, save it with taskseam_record "
            "(or taskseam_resolve / taskseam_retire); call taskseam_continue for changes made by "
            "other agents during this session.")


def session_start(stdin=None, stdout=None):
    """Print the active task's brief; stay silent outside a TaskSeam workspace."""
    stdin = stdin or sys.stdin
    stdout = stdout or sys.stdout
    payload = {}
    try:
        if not stdin.isatty():
            raw = stdin.read()
            payload = json.loads(raw) if raw.strip() else {}
    except (ValueError, OSError):
        payload = {}
    cwd = payload.get("cwd") if isinstance(payload, dict) else None
    try:
        workspace = find_workspace(cwd or os.getcwd())
        if not workspace:
            return 0
        store = Store(database_path(workspace))
        try:
            context = store.context(active_task(workspace))
        finally:
            store.close()
    except Exception as exc:  # A hook must never block the user's session.
        print("taskseam hook: " + str(exc), file=sys.stderr)
        return 0
    stdout.write(brief(context["task"], context["items"], budget=BUDGET))
    stdout.write("\n" + GUIDANCE + "\n")
    stdout.flush()
    return 0


def hook_command(python_executable=None):
    python = python_executable or sys.executable
    args = [python, "-m", "taskseam", "hook", "session-start"]
    if os.name == "nt":
        return subprocess.list2cmdline(args)
    import shlex
    return " ".join(shlex.quote(arg) for arg in args)


def claude_settings_path():
    return Path.home() / ".claude" / "settings.json"


def codex_hooks_path():
    return Path(os.environ.get("CODEX_HOME") or Path.home() / ".codex") / "hooks.json"


def install(path, python_executable=None, dry_run=False):
    """Add or refresh the TaskSeam SessionStart hook in a hooks JSON file.

    Claude Code's settings.json and Codex's hooks.json share this structure.
    Unrelated settings and hooks are preserved; an existing TaskSeam entry is
    updated in place so reinstalling never duplicates it.
    """
    path = Path(path)
    command = hook_command(python_executable)
    original = path.read_text(encoding="utf-8") if path.exists() else ""
    try:
        data = json.loads(original) if original.strip() else {}
    except json.JSONDecodeError as exc:
        raise ValueError("Cannot update {}: invalid JSON ({})".format(path, exc)) from exc
    if not isinstance(data, dict):
        raise ValueError("Cannot update {}: expected a JSON object".format(path))
    hooks = data.setdefault("hooks", {})
    if not isinstance(hooks, dict):
        raise ValueError("Cannot update {}: 'hooks' must be an object".format(path))
    groups = hooks.setdefault("SessionStart", [])
    if not isinstance(groups, list):
        raise ValueError("Cannot update {}: 'hooks.SessionStart' must be a list".format(path))
    entry = {"type": "command", "command": command, "timeout": 10}
    status = "installed"
    for group in groups:
        for handler in (group.get("hooks") or []) if isinstance(group, dict) else []:
            if isinstance(handler, dict) and HOOK_MARKER in str(handler.get("command", "")):
                status = "unchanged" if handler.get("command") == command else "updated"
                handler["command"] = command
                break
        else:
            continue
        break
    else:
        groups.append({"matcher": MATCHER, "hooks": [entry]})
    result = {"path": str(path), "status": status, "command": command}
    if dry_run or status == "unchanged":
        result["written"] = False
        return result
    path.parent.mkdir(parents=True, exist_ok=True)
    if original:
        backup = path.with_name(path.name + ".taskseam-backup")
        if not backup.exists():
            backup.write_text(original, encoding="utf-8")
            result["backup"] = str(backup)
    temporary = path.with_name(path.name + ".taskseam-tmp")
    temporary.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    os.replace(str(temporary), str(path))
    result["written"] = True
    return result


def install_detected(python_executable=None, dry_run=False, tools=None):
    """Install the hook for each supported agent found on PATH."""
    targets = (("claude-code", "claude", claude_settings_path),
               ("codex", "codex", codex_hooks_path))
    installed, skipped = [], []
    for name, executable, locate in targets:
        if tools and name not in tools:
            continue
        if not shutil.which(executable):
            skipped.append({"tool": name, "reason": "not found on PATH"})
            continue
        result = install(locate(), python_executable, dry_run)
        if name == "codex":
            result["note"] = "Codex runs new hooks only after you review and trust them with /hooks"
        installed.append({"tool": name, **result})
    return {"hooks": installed, "skipped": skipped}
