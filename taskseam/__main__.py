"""Command-line entry point: python -m taskseam."""

import argparse
import json
import os
import sys
from pathlib import Path

from .store import Store
from .workspace import active_task, browser_token, database_path, find_workspace, initialize


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
    setup = commands.add_parser("setup", help="Auto-detect and configure supported AI tools")
    setup.add_argument("tool", nargs="?", choices=("codex", "claude-code"),
                       help="Configure one tool; omit to configure every detected tool")
    setup.add_argument("--dry-run", action="store_true")
    setup.add_argument("--no-hooks", action="store_true",
                       help="Skip the session-start hook that loads project state automatically")
    commands.add_parser("prompt", help="Print the prompt for creating an import packet")
    import_command = commands.add_parser("import", help="Preview or apply a TaskSeam state packet")
    import_command.add_argument("path", nargs="?", help="JSON file; omit to read standard input")
    import_command.add_argument("--source", required=True)
    import_command.add_argument("--apply", action="store_true", help="Write the reviewed packet")
    resolve = commands.add_parser("resolve", help="Resolve a question into an accepted decision")
    resolve.add_argument("question_id")
    resolve.add_argument("decision")
    resolve.add_argument("--source", default="manual")
    resolve.add_argument("--supersedes", help="Existing decision replaced by the resolution")
    supersede = commands.add_parser("supersede", help="Correctly link an old item to its replacement")
    supersede.add_argument("old_item_id")
    supersede.add_argument("--with", dest="new_item_id", required=True)
    handoff = commands.add_parser("handoff", help="Deliver changes since a target's last handoff")
    handoff.add_argument("--to", required=True, dest="target")
    handoff.add_argument("--task-id", help="Defaults to the active workspace task")
    handoff.add_argument("--full", action="store_true",
                         help="Also include current state for a fresh chat or lost context")
    show = commands.add_parser("show", help="Print the active task's state in readable form")
    show.add_argument("task_id", nargs="?", help="Defaults to the active workspace task")
    drop = commands.add_parser("drop", help="Retire an item that no longer applies")
    drop.add_argument("item_id", help="Item ID or unique prefix")
    drop.add_argument("--reason", required=True)
    drop.add_argument("--source", default="manual")
    export = commands.add_parser("export", help="Write deterministic JSON or Markdown state")
    export.add_argument("--format", choices=("json", "markdown"), default="json")
    export.add_argument("--history", action="store_true",
                        help="Include superseded, resolved, and retired items (JSON only)")
    destination = export.add_mutually_exclusive_group()
    destination.add_argument("--output", "-o", help="Write to a file instead of standard output")
    destination.add_argument("--agents-md", nargs="?", const="AGENTS.md", metavar="PATH",
                             help="Maintain a TaskSeam block inside AGENTS.md (or PATH)")
    export.add_argument("--task-id", help="Defaults to the active workspace task")
    demo = commands.add_parser("demo", help="One-minute walkthrough in a temporary project")
    demo.add_argument("--pause", type=float, default=None, help="Seconds between steps")
    doctor = commands.add_parser("doctor", help="Check agent connections and this project's state")
    doctor.add_argument("--json", action="store_true", help="Print machine-readable results")
    doctor.add_argument("--skip-mcp", action="store_true",
                        help="Do not ask agent CLIs whether the MCP server is registered")
    hook = commands.add_parser("hook", help="Agent session hooks")
    hook_sub = hook.add_subparsers(dest="action", required=True)
    hook_sub.add_parser("session-start", help="Print state for a SessionStart hook (reads hook JSON)")
    hook_install = hook_sub.add_parser("install", help="Install the SessionStart hook")
    hook_install.add_argument("tool", nargs="?", choices=("codex", "claude-code"))
    hook_install.add_argument("--dry-run", action="store_true")
    return p


def _task_or_active(task_id, workspace):
    task_id = task_id or (active_task(workspace) if workspace else None)
    if not task_id:
        raise ValueError("Provide a task ID or run this command in a TaskSeam workspace")
    return task_id


def _print_setup_summary(result, dry_run, tool=None):
    names = {"claude-code": "Claude Code", "codex": "Codex"}
    connected = [{"tool": tool, **result}] if tool else result.get("configured", [])
    lines = []
    for entry in connected:
        if entry.get("tool"):
            how = entry.get("found_via", "")
            lines.append("  {} {}{}".format("would connect" if dry_run else "connected", names[entry["tool"]],
                                            " (" + how + ")" if how and how != "PATH" else ""))
    for entry in result.get("skipped", []):
        lines.append("  skipped {}: {}".format(names.get(entry["tool"], entry["tool"]), entry["reason"]))
    for entry in (result.get("session_hooks") or {}).get("hooks", []):
        if entry["tool"] == "codex" and entry["status"] != "unchanged":
            lines.append("  Codex: open /hooks once and trust the TaskSeam hook")
    if lines:
        print("\nTaskSeam setup" + (" (dry run, nothing written)" if dry_run else "") + ":\n" +
              "\n".join(lines) + "\nNext: cd your-project && taskseam init, then `taskseam doctor`.",
              file=sys.stderr)


def _agents_md_block(task, items):
    from .render import brief
    body = brief(task, items, header=False)
    body = "\n".join("#" + line if line.startswith("## ") else line for line in body.splitlines())
    return "## Project state (TaskSeam: {})\n\n{}\n".format(task["title"], body)


def main(argv=None):
    args = parser().parse_args(argv)
    try:
        if args.command == "demo":
            from .demo import run as run_demo
            return run_demo(args.pause)
        if args.command == "doctor":
            from .doctor import diagnose, render
            sections = diagnose(probe_mcp=not args.skip_mcp)
            if args.json:
                print(json.dumps([{"section": title, "checks": checks} for title, checks in sections],
                                 indent=2))
                return 1 if any(c["status"] == "fail" for _, cs in sections for c in cs) else 0
            return render(sections)
        if args.command == "hook" and args.action == "session-start":
            from .hooks import session_start
            return session_start()
        if args.command == "init":
            title = args.title or Path.cwd().name

            def create_task(path, task_title):
                store = Store(path)
                try:
                    return store.create_task(task_title)
                finally:
                    store.close()

            root, config = initialize(Path.cwd(), title, create_task)
            print(json.dumps({"workspace": str(root), "project": config["project"],
                              "active_task": config["active_task"]}, indent=2))
            print("\nTaskSeam is ready in {}.\nNext: open this folder in Claude Code or Codex and "
                  "start a new chat.\nCheck the connection any time with: taskseam doctor".format(root),
                  file=sys.stderr)
            return 0
        if args.command == "prompt":
            from .importer import PACKET_PROMPT
            print(PACKET_PROMPT)
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
            from .setup import setup_claude, setup_codex, setup_detected
            if args.tool == "codex":
                result = setup_codex(sys.executable, args.dry_run)
            elif args.tool == "claude-code":
                result = setup_claude(sys.executable, args.dry_run)
            else:
                result = setup_detected(sys.executable, args.dry_run)
            if not args.no_hooks:
                from .hooks import install_detected
                tools = {"codex": ["codex"], "claude-code": ["claude-code"]}.get(args.tool)
                result["session_hooks"] = install_detected(sys.executable, args.dry_run, tools)
            print(json.dumps(result, indent=2))
            _print_setup_summary(result, args.dry_run, args.tool)
            return 0
        if args.command == "import":
            from .importer import parse_packet
            if not workspace:
                raise ValueError("No TaskSeam workspace found; run 'taskseam init'")
            raw = Path(args.path).read_text(encoding="utf-8") if args.path else sys.stdin.read()
            packet = parse_packet(raw)
            if not args.apply:
                print(json.dumps({"preview": packet["items"], "source": args.source,
                                  "applied": False,
                                  "next": "Review the items, then rerun with --apply"}, indent=2))
                return 0
            store = Store(args.db)
            try:
                imported = store.import_items(active_task(workspace), args.source, raw, packet["items"])
                result = {"applied": True, "source": args.source, **imported,
                          "items": packet["items"]}
                print(json.dumps(result, indent=2))
                return 0
            finally:
                store.close()
        if args.command == "serve":
            from .api import serve
            if not workspace:
                raise ValueError("No TaskSeam workspace found; run 'taskseam init'")
            task_id = active_task(workspace)
            token = browser_token(workspace)
            print("Browser pairing token: " + token, flush=True)
            serve(args.db, args.host, args.port, token, task_id)
            return 0
        if args.command == "mcp":
            from .mcp import run
            run(args.db, task_id=active_task(workspace) if workspace else None)
            return 0
        if args.command == "hook":
            from .hooks import install_detected
            tools = [args.tool] if args.tool else None
            print(json.dumps(install_detected(sys.executable, args.dry_run, tools), indent=2))
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
                supersedes = args.supersedes and store.resolve_item_id(args.supersedes, args.task_id)
                result = {"item_id": store.add_item(args.task_id, args.kind, args.body,
                                                     args.source, supersedes)}
            elif args.command in ("record", "resolve", "supersede", "drop"):
                if not workspace:
                    raise ValueError("No TaskSeam workspace found; run 'taskseam init'")
                task_id = active_task(workspace)

                def ref(value):
                    return store.resolve_item_id(value, task_id) if value else None

                if args.command == "record":
                    result = {"item_id": store.add_item(task_id, args.kind, args.body,
                                                         args.source, ref(args.supersedes))}
                elif args.command == "resolve":
                    question_id = ref(args.question_id)
                    result = {"item_id": store.resolve_question(task_id, question_id, args.decision,
                                                                 args.source, ref(args.supersedes)),
                              "resolved_question": question_id}
                elif args.command == "supersede":
                    old, new = ref(args.old_item_id), ref(args.new_item_id)
                    store.set_supersession(task_id, old, new)
                    result = {"superseded": old, "replacement": new}
                else:
                    result = store.retire_item(task_id, ref(args.item_id), args.reason, args.source)
            elif args.command == "show":
                from .render import brief
                context = store.context(_task_or_active(args.task_id, workspace))
                print(brief(context["task"], context["items"]), end="")
                return 0
            elif args.command == "export":
                from .render import brief, splice_agents_md
                task_id = _task_or_active(args.task_id, workspace)
                if args.history and args.format != "json":
                    raise ValueError("--history is only available with --format json")
                if args.agents_md:
                    context = store.context(task_id)
                    target = Path(args.agents_md)
                    existing = target.read_text(encoding="utf-8") if target.exists() else ""
                    target.write_text(splice_agents_md(
                        existing, _agents_md_block(context["task"], context["items"])), encoding="utf-8")
                    print("taskseam: updated {}. It is usually committed to Git; review the block "
                          "before sharing.".format(target), file=sys.stderr)
                    return 0
                if args.format == "json":
                    text = json.dumps(store.export(task_id, history=args.history), indent=2,
                                      sort_keys=True) + "\n"
                else:
                    snapshot = store.export(task_id)
                    text = brief(snapshot["task"], snapshot["items"])
                if args.output:
                    Path(args.output).write_text(text, encoding="utf-8")
                else:
                    sys.stdout.write(text)
                return 0
            elif args.command == "handoff":
                task_id = args.task_id or (active_task(workspace) if workspace else None)
                if not task_id:
                    raise ValueError("Provide a task ID or run this command in a TaskSeam workspace")
                result = store.handoff(task_id, args.target, full=args.full)
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
                result = store.explain(store.resolve_item_id(args.item_id))
            print(json.dumps(result, indent=2))
            return 0
        finally:
            store.close()
    except (ValueError, OSError) as exc:
        print("taskseam: " + str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
