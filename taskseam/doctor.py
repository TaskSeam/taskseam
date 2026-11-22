"""`taskseam doctor`: explain exactly what is connected and how to fix what is not."""

import json
import shlex
import subprocess
import sys
from pathlib import Path

from . import __version__
from .hooks import HOOK_MARKER, claude_settings_path, codex_hooks_path
from .setup import find_agent
from .store import SCHEMA_VERSION, Store
from .workspace import active_task, database_path, find_workspace

AGENTS = (("Claude Code", "claude-code", "claude", claude_settings_path),
          ("Codex", "codex", "codex", codex_hooks_path))


def _check(status, name, detail, fix=None):
    return {"status": status, "check": name, "detail": detail, "fix": fix}


def _mcp_registration(executable, tool):
    try:
        result = subprocess.run([executable, "mcp", "get", "taskseam"], capture_output=True,
                                text=True, timeout=30)
    except (OSError, subprocess.TimeoutExpired) as exc:
        return _check("warn", "MCP server", "could not ask {}: {}".format(tool, exc))
    if result.returncode != 0:
        return _check("fail", "MCP server", "taskseam is not registered",
                      "taskseam setup " + tool)
    output = result.stdout + result.stderr
    if "taskseam" in output and sys.executable not in output and "-m taskseam" in output:
        return _check("warn", "MCP server",
                      "registered with a different Python than this TaskSeam ({})".format(sys.executable),
                      "taskseam setup " + tool)
    return _check("ok", "MCP server", "registered")


def _hook(path, tool):
    if not path.exists():
        return _check("fail", "Session-start hook", "not installed ({} missing)".format(path),
                      "taskseam hook install " + tool)
    try:
        data = json.loads(path.read_text(encoding="utf-8") or "{}")
    except (OSError, ValueError) as exc:
        return _check("fail", "Session-start hook", "cannot read {}: {}".format(path, exc))
    groups = ((data.get("hooks") or {}).get("SessionStart") or []) if isinstance(data, dict) else []
    for group in groups:
        for handler in (group.get("hooks") or []) if isinstance(group, dict) else []:
            command = str(handler.get("command", "")) if isinstance(handler, dict) else ""
            if HOOK_MARKER not in command:
                continue
            try:
                python = shlex.split(command)[0]
            except (ValueError, IndexError):
                python = ""
            if python and not Path(python).exists():
                return _check("fail", "Session-start hook",
                              "points to a Python that no longer exists: " + python,
                              "taskseam hook install " + tool)
            detail = "installed in " + str(path)
            if tool == "codex":
                detail += "; Codex runs it after you trust it once in /hooks"
            return _check("ok", "Session-start hook", detail)
    return _check("fail", "Session-start hook", "not installed in " + str(path),
                  "taskseam hook install " + tool)


def _nearby_workspaces(cwd, limit=3):
    found = []
    try:
        for config in sorted(cwd.glob("*/.taskseam/config.json")) + sorted(cwd.glob("*/*/.taskseam/config.json")):
            found.append(str(config.parent.parent))
            if len(found) >= limit:
                break
    except OSError:
        pass
    return found


def _project(cwd):
    checks = []
    try:
        workspace = find_workspace(cwd)
    except ValueError as exc:
        return [_check("fail", "Project", str(exc))]
    if not workspace:
        nearby = _nearby_workspaces(cwd)
        if nearby:
            return [_check("fail", "Project",
                           "{} is not inside a TaskSeam project, but these folders are: {}. Agents "
                           "only see state when the editor opens the project folder itself.".format(
                               cwd, ", ".join(nearby)),
                           "open one of those folders in your editor, or cd into it")]
        return [_check("fail", "Project", "{} is not inside a TaskSeam project".format(cwd),
                       "cd your-project && taskseam init")]
    root = workspace[0]
    checks.append(_check("ok", "Project", str(root)))
    try:
        store = Store(database_path(workspace))
        try:
            version = store.db.execute("PRAGMA user_version").fetchone()[0]
            context = store.context(active_task(workspace))
        finally:
            store.close()
    except (ValueError, OSError) as exc:
        checks.append(_check("fail", "Project state", str(exc)))
        return checks
    counts = {}
    for item in context["items"]:
        counts[item["kind"]] = counts.get(item["kind"], 0) + 1
    summary = ", ".join("{} {}{}".format(counts.get(kind, 0), kind, "" if counts.get(kind, 0) == 1 else "s")
                        for kind in ("decision", "constraint", "question"))
    checks.append(_check("ok", "Project state",
                         "task '{}' (schema v{}): {}".format(context["task"]["title"], version, summary)))
    if version != SCHEMA_VERSION:
        checks.append(_check("warn", "Project state", "schema v{} differs from v{}".format(
            version, SCHEMA_VERSION)))
    if not context["items"]:
        checks.append(_check("warn", "Project state",
                             "nothing recorded yet; agents save state when you accept a decision",
                             'taskseam record decision "..." --source user'))
    ignore = root / ".gitignore"
    lines = ignore.read_text(encoding="utf-8").splitlines() if ignore.exists() else []
    if not {".taskseam/", "/.taskseam/", ".taskseam"} & {line.strip() for line in lines}:
        checks.append(_check("warn", "Privacy", ".taskseam/ is not in .gitignore, so state could be committed",
                             "echo '.taskseam/' >> .gitignore"))
    return checks


def diagnose(cwd=None, probe_mcp=True):
    cwd = Path(cwd or Path.cwd()).resolve()
    sections = [("TaskSeam", [_check("ok", "Installed", "{} ({})".format(__version__, sys.executable))])]
    any_agent = False
    for label, tool, executable, locate in AGENTS:
        found, how = find_agent(executable)
        if not found:
            sections.append((label, [_check("info", "Installed", "not found on PATH or in an editor extension")]))
            continue
        any_agent = True
        checks = [_check("ok", "Installed", "{} ({})".format(found, how))]
        if probe_mcp:
            checks.append(_mcp_registration(found, tool))
        checks.append(_hook(locate(), tool))
        sections.append((label, checks))
    if not any_agent:
        sections[0][1].append(_check("fail", "Agents", "neither Claude Code nor Codex was found",
                                     "install Claude Code or Codex, then run taskseam setup"))
    sections.append(("This folder", _project(cwd)))
    return sections


SYMBOLS = {"ok": ("✓", "ok"), "warn": ("!", "!!"), "fail": ("✗", "XX"), "info": ("-", "--")}


def render(sections, stream=None):
    stream = stream or sys.stdout
    encoding = getattr(stream, "encoding", None) or "utf-8"
    try:
        "✓✗".encode(encoding)
        index = 0
    except (UnicodeEncodeError, LookupError):
        index = 1
    lines = []
    for title, checks in sections:
        lines.append(title)
        for check in checks:
            lines.append("  {} {}: {}".format(SYMBOLS[check["status"]][index], check["check"], check["detail"]))
            if check["fix"] and check["status"] in ("fail", "warn"):
                lines.append("      fix: " + check["fix"])
        lines.append("")
    problems = sum(1 for _, checks in sections for check in checks if check["status"] == "fail")
    lines.append("Everything needed is in place." if not problems else
                 "{} problem{} found.".format(problems, "" if problems == 1 else "s"))
    stream.write("\n".join(lines) + "\n")
    return 1 if problems else 0
