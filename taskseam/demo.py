"""`taskseam demo`: a one-minute, agent-free walkthrough in a temporary project."""

import json
import sys
import tempfile
import time
from pathlib import Path

from .hooks import session_start
from .render import brief, short
from .store import Store
from .workspace import database_path, find_workspace, initialize


def run(pause=None, stream=None):
    stream = stream or sys.stdout
    color = hasattr(stream, "isatty") and stream.isatty()
    if pause is None:
        pause = 1.2 if color else 0.0

    def say(text):
        stream.write("\n" + ("\033[1m# " + text + "\033[0m" if color else "# " + text) + "\n")
        stream.flush()
        time.sleep(pause)

    def show(text):
        stream.write(text if text.endswith("\n") else text + "\n")
        stream.flush()

    with tempfile.TemporaryDirectory(prefix="taskseam-demo-") as directory:
        root = Path(directory)

        def create(path, title):
            store = Store(path)
            try:
                return store.create_task(title)
            finally:
                store.close()

        initialize(root, "Invoice exporter", create)
        workspace = find_workspace(root)
        task = workspace[1]["active_task"]
        store = Store(database_path(workspace))
        try:
            say("Monday, in Claude Code: you accept a decision, and the agent saves it")
            pdf = store.add_item(task, "decision", "Export invoices as PDF", "claude-code")
            store.add_item(task, "constraint", "Never send invoice data to third-party services", "user")
            store.add_item(task, "question", "Should exports include voided invoices?", "claude-code")
            store.handoff(task, "claude-code")
            context = store.context(task)
            show(brief(context["task"], context["items"], header=False, ids=False))

            say("Tuesday, in Codex: you change your mind. CSV replaces PDF, plus a new rule")
            csv = store.add_item(task, "decision", "Export invoices as CSV, not PDF", "codex", pdf)
            store.add_item(task, "constraint", "CSV must follow RFC 4180", "codex")
            show("saved. The PDF decision is superseded, not deleted")

            say("Any new chat, in any agent: the session-start hook loads current state")
            show("(no prompting, no pasted history. The old PDF decision is gone)")
            stdin = _Input(json.dumps({"cwd": str(root), "source": "startup"}))
            session_start(stdin, stream)

            say("Back in Claude Code: it receives only what changed since its last visit")
            delta = store.handoff(task, "claude-code")
            for item in delta["added"]:
                show("  + {}: {}".format(item["kind"], item["body"]))
            for item in delta["removed"]:
                show("  - {}: {}".format(item["kind"], item["body"]))

            say("Every item keeps its evidence")
            evidence = store.explain(csv)
            show("  {} `{}`  <- {} at {}".format(evidence["body"], short(csv), evidence["source"],
                                                 evidence["event_time"][:16].replace("T", " ")))
        finally:
            store.close()

    say("Try it in your own project")
    show("  taskseam setup     # connect Claude Code and Codex (CLI or editor extension)\n"
         "  cd your-project && taskseam init\n"
         "  taskseam doctor    # confirm everything is connected")
    return 0


class _Input:
    """Minimal stdin stand-in for the hook (not a TTY)."""

    def __init__(self, text):
        self.text = text

    def isatty(self):
        return False

    def read(self):
        return self.text
