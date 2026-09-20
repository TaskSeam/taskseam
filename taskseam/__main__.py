"""Command-line entry point: python -m taskseam."""

import argparse
import json
import os
import sys
from pathlib import Path

from .store import Store


def parser():
    p = argparse.ArgumentParser(prog="taskseam", description="Local task checkpoints and context deltas")
    p.add_argument("--db", default=os.environ.get("TASKSEAM_DB", str(Path.home() / ".local/share/taskseam/taskseam.db")),
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
    checkpoint.add_argument("task_id")
    delta = commands.add_parser("delta", help="Compare two checkpoints")
    delta.add_argument("base")
    delta.add_argument("head")
    context = commands.add_parser("context", help="Show current task state")
    context.add_argument("task_id")
    explain = commands.add_parser("explain", help="Show an item's source event")
    explain.add_argument("item_id")
    return p


def main(argv=None):
    args = parser().parse_args(argv)
    try:
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
            elif args.command == "checkpoint":
                result = {"checkpoint_id": store.checkpoint(args.task_id)}
            elif args.command == "delta":
                result = store.delta(args.base, args.head)
            elif args.command == "context":
                result = {"task": store.task(args.task_id), "items": store.current_items(args.task_id)}
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
