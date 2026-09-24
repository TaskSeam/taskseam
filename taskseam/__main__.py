"""Command-line entry point: python -m taskseam."""

import argparse
import json
import os
import sys
from pathlib import Path

from .store import Store
from .workspace import active_task, database_path, find_workspace, initialize


def default_db():
    workspace = find_workspace()
    if workspace:
        return str(database_path(workspace))
    return str(Path.home() / ".local/share/taskseam/taskseam.db")


def parser():
    p = argparse.ArgumentParser(prog="taskseam", description="Local task checkpoints and context deltas")
    p.add_argument("--db", default=None,
                   help="SQLite database path (or set TASKSEAM_DB)")
    commands = p.add_subparsers(dest="command", required=True)
    task = commands.add_parser("task", help="Create, list, or inspect tasks")
    task_sub = task.add_subparsers(dest="action", required=True)
    task_sub.add_parser("list")
    create = task_sub.add_parser("create")
    create.add_argument("title")
    show = task_sub.add_parser("show")
    show.add_argument("task_id")

    event = commands.add_parser("event", help="Record a source event")
    event.add_argument("task_id")
    event.add_argument("body")
    event.add_argument("--source", default="manual")

    item = commands.add_parser("item", help="Record a decision, question, or constraint")
    item.add_argument("task_id")
    item.add_argument("kind", choices=("decision", "question", "constraint"))
    item.add_argument("body")
    item.add_argument("--source", default="manual")
    item.add_argument("--supersedes", help="ID of an earlier item in the same task")

    checkpoint = commands.add_parser("checkpoint", help="Save current task state")
    checkpoint.add_argument("task_id", nargs="?", help="Defaults to the active workspace task")
    delta = commands.add_parser("delta", help="Compare two checkpoints")
    delta.add_argument("base")
    delta.add_argument("head")
    context = commands.add_parser("context", help="Show current task state")
    context.add_argument("task_id", nargs="?", help="Defaults to the active workspace task")
    explain = commands.add_parser("explain", help="Show an item's source event")
    explain.add_argument("item_id")
    serve = commands.add_parser("serve", help="Run the localhost JSON API")
    serve.add_argument("--host", default="127.0.0.1")
    serve.add_argument("--port", default=8765, type=int)
    commands.add_parser("mcp", help="Run the MCP server over standard input/output")
    commands.add_parser("version", help="Print the installed version")
    init = commands.add_parser("init", help="Initialize TaskSeam in the current directory")
    init.add_argument("title", nargs="?", help="Title of the first task")
    commands.add_parser("status", help="Show the current workspace and active task")
    record = commands.add_parser("record", help="Record state on the active workspace task")
    record.add_argument("kind", choices=("decision", "question", "constraint"))
    record.add_argument("body")
    record.add_argument("--source", default="manual")
    record.add_argument("--supersedes")
    setup = commands.add_parser("setup", help="Configure an AI tool to use TaskSeam")
    setup.add_argument("tool", choices=("codex",))
    setup.add_argument("--dry-run", action="store_true")
    return p


def main(argv=None):
    args = parser().parse_args(argv)
    try:
        if args.command == "init":
            title = args.title or "Continue work in " + Path.cwd().name

            def create_task(path, task_title):
                store = Store(path)
                try:
                    return store.create_task(task_title)
                finally:
                    store.close()

            root, config = initialize(Path.cwd(), title, create_task)
            print(json.dumps({"workspace": str(root), "project": config["project"],
                              "active_task": config["active_task"]}, indent=2))
            return 0
        workspace = find_workspace()
        args.db = args.db or os.environ.get("TASKSEAM_DB") or default_db()
        if args.command == "status":
            if not workspace:
                raise ValueError("No TaskSeam workspace found; run 'taskseam init'")
            store = Store(args.db)
            try:
                result = {"workspace": str(workspace[0]), "database": args.db,
                          "active_task": store.context(active_task(workspace))}
                print(json.dumps(result, indent=2))
                return 0
            finally:
                store.close()
        if args.command == "setup":
            from .setup import setup_codex
            if not workspace:
                raise ValueError("No TaskSeam workspace found; run 'taskseam init'")
            result = setup_codex(sys.executable, args.dry_run)
            print(json.dumps(result, indent=2))
            return 0
        if args.command == "serve":
            from .api import serve
            serve(args.db, args.host, args.port)
            return 0
        if args.command == "mcp":
            from .mcp import run
            run(args.db)
            return 0
        if args.command == "version":
            from . import __version__
            print(__version__)
            return 0
        store = Store(args.db)
        try:
            if args.command == "task":
                if args.action == "create":
                    result = {"id": store.create_task(args.title), "title": args.title}
                elif args.action == "list":
                    result = store.tasks()
                else:
                    result = {"task": store.task(args.task_id), "items": store.current_items(args.task_id)}
            elif args.command == "event":
                result = {"event_id": store.add_event(args.task_id, args.source, args.body)}
            elif args.command == "item":
                result = {"item_id": store.add_item(args.task_id, args.kind, args.body,
                                                     args.source, args.supersedes)}
            elif args.command == "record":
                if not workspace:
                    raise ValueError("No TaskSeam workspace found; run 'taskseam init'")
                result = {"item_id": store.add_item(active_task(workspace), args.kind, args.body,
                                                     args.source, args.supersedes)}
            elif args.command == "checkpoint":
                task_id = args.task_id or (active_task(workspace) if workspace else None)
                if not task_id:
                    raise ValueError("Provide a task ID or run this command in a TaskSeam workspace")
                result = {"checkpoint_id": store.checkpoint(task_id)}
            elif args.command == "delta":
                result = store.delta(args.base, args.head)
            elif args.command == "context":
                task_id = args.task_id or (active_task(workspace) if workspace else None)
                if not task_id:
                    raise ValueError("Provide a task ID or run this command in a TaskSeam workspace")
                result = store.context(task_id)
            else:
                result = store.explain(args.item_id)
            print(json.dumps(result, indent=2))
            return 0
        finally:
            store.close()
    except (ValueError, OSError) as exc:
        print("taskseam: " + str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
