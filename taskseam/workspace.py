"""Repository-local TaskSeam workspace configuration."""

import json
from pathlib import Path


CONFIG_VERSION = 1


def find_workspace(start=None):
    current = Path(start or Path.cwd()).resolve()
    for directory in (current, *current.parents):
        config_path = directory / ".taskseam" / "config.json"
        if config_path.is_file():
            data = json.loads(config_path.read_text(encoding="utf-8"))
            if data.get("version") != CONFIG_VERSION:
                raise ValueError("Unsupported workspace configuration version")
            return directory, data
    return None


def initialize(directory, title, create_task):
    root = Path(directory).resolve()
    state_dir = root / ".taskseam"
    config_path = state_dir / "config.json"
    if config_path.exists():
        raise ValueError("TaskSeam is already initialized in " + str(root))
    state_dir.mkdir(parents=True, exist_ok=True)
    task_id = create_task(state_dir / "state.db", title)
    config = {
        "version": CONFIG_VERSION,
        "project": root.name,
        "active_task": task_id,
        "database": "state.db",
    }
    config_path.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")
    _ensure_ignored(root)
    return root, config


def database_path(workspace):
    root, config = workspace
    return root / ".taskseam" / config.get("database", "state.db")


def active_task(workspace):
    task_id = workspace[1].get("active_task")
    if not task_id:
        raise ValueError("Workspace has no active task")
    return task_id


def _ensure_ignored(root):
    ignore = root / ".gitignore"
    text = ignore.read_text(encoding="utf-8") if ignore.exists() else ""
    entries = {line.strip() for line in text.splitlines()}
    if ".taskseam/" not in entries and "/.taskseam/" not in entries:
        if text and not text.endswith("\n"):
            text += "\n"
        text += ".taskseam/\n"
        ignore.write_text(text, encoding="utf-8")
