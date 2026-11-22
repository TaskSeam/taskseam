import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from taskseam import hooks
from taskseam.mcp import PROTOCOL_VERSIONS, handle
from taskseam.render import AGENTS_MD_END, AGENTS_MD_START, brief, splice_agents_md
from taskseam.store import Store

ROOT = Path(__file__).resolve().parents[1]


class RetireAndReferenceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.store = Store(Path(self.tmp.name) / "state.db")
        self.task = self.store.create_task("Retire")

    def tearDown(self):
        self.store.close()
        self.tmp.cleanup()

    def test_retired_item_leaves_state_and_appears_as_removed_in_delta(self):
        item = self.store.add_item(self.task, "constraint", "Must work offline", "user")
        self.store.handoff(self.task, "codex")
        result = self.store.retire_item(self.task, item, "Offline was cut", "user")
        self.assertEqual(result["retired"], item)
        self.assertEqual(self.store.current_items(self.task), [])
        delta = self.store.handoff(self.task, "codex")
        self.assertEqual([i["id"] for i in delta["removed"]], [item])
        self.assertIn("Offline was cut", self.store.events(self.task)[-1]["body"])

    def test_retire_rejects_non_current_items_and_empty_reasons(self):
        old = self.store.add_item(self.task, "decision", "Use Markdown", "user")
        self.store.add_item(self.task, "decision", "Use SQLite", "user", old)
        with self.assertRaisesRegex(ValueError, "Only current items"):
            self.store.retire_item(self.task, old, "stale", "user")
        current = self.store.current_items(self.task)[0]["id"]
        with self.assertRaisesRegex(ValueError, "reason"):
            self.store.retire_item(self.task, current, "  ", "user")
        self.store.retire_item(self.task, current, "Dropped storage work", "user")
        with self.assertRaises(ValueError):
            self.store.add_item(self.task, "decision", "Use JSON", "user", current)
        other = self.store.create_task("Other")
        foreign = self.store.add_item(other, "decision", "Elsewhere", "user")
        with self.assertRaisesRegex(ValueError, "active task"):
            self.store.retire_item(self.task, foreign, "wrong task", "user")

    def test_prefix_references_resolve_uniquely(self):
        item = self.store.add_item(self.task, "decision", "Use SQLite", "user")
        self.assertEqual(self.store.resolve_item_id(item[:5].upper(), self.task), item)
        self.assertEqual(self.store.resolve_item_id(item, self.task), item)
        with self.assertRaisesRegex(ValueError, "four"):
            self.store.resolve_item_id(item[:3])
        with self.assertRaisesRegex(ValueError, "Unknown"):
            self.store.resolve_item_id("%%%%")
        self.store.db.execute("UPDATE items SET id = 'abcd11111111' WHERE id = ?", (item,))
        self.store.add_item(self.task, "decision", "Second", "user")
        self.store.db.execute("UPDATE items SET id = 'abcd22222222' WHERE body = 'Second'")
        with self.assertRaisesRegex(ValueError, "Ambiguous"):
            self.store.resolve_item_id("abcd", self.task)

    def test_export_is_deterministic_and_history_is_opt_in(self):
        old = self.store.add_item(self.task, "decision", "Use Markdown", "user")
        self.store.add_item(self.task, "question", "Offline?", "user")
        self.store.add_item(self.task, "constraint", "Local only", "user")
        self.store.add_item(self.task, "decision", "Use SQLite", "user", old)
        first = self.store.export(self.task)
        self.assertEqual(first, self.store.export(self.task))
        self.assertEqual([i["kind"] for i in first["items"]], ["decision", "constraint", "question"])
        self.assertEqual(first["taskseam_export"], 1)
        self.assertNotIn("retired_at", first["items"][0])
        history = self.store.export(self.task, history=True)
        self.assertEqual(len(history["items"]), 4)


class RenderTests(unittest.TestCase):
    def items(self, count, kind="decision"):
        return [{"id": "{:012x}".format(n), "kind": kind, "body": "Decision number %d" % n,
                 "source": "user"} for n in range(count)]

    def test_budget_reports_omissions_instead_of_dropping_silently(self):
        task = {"title": "Big"}
        text = brief(task, self.items(200), budget=1500)
        self.assertLessEqual(len(text), 1600)
        self.assertIn("Omitted to fit the size budget", text)
        self.assertIn("decisions", text)
        self.assertNotIn("Omitted", brief(task, self.items(3), budget=1500))

    def test_empty_state_is_explicit(self):
        self.assertIn("No accepted decisions", brief({"title": "Empty"}, []))

    def test_agents_md_block_is_inserted_then_replaced(self):
        original = "# Agents\n\nRun make test.\n"
        once = splice_agents_md(original, "first\n")
        self.assertTrue(once.startswith(original.rstrip("\n")))
        twice = splice_agents_md(once + "\n## Footer\n", "second\n")
        self.assertIn("second", twice)
        self.assertNotIn("first", twice)
        self.assertEqual(twice.count(AGENTS_MD_START), 1)
        self.assertIn("## Footer", twice)
        with self.assertRaises(ValueError):
            splice_agents_md(original + AGENTS_MD_END, "x")


class HookTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_session_start_prints_state_for_hook_cwd(self):
        project = self.root / "project"
        project.mkdir()
        subprocess.run([sys.executable, "-m", "taskseam", "init", "Hooked"], cwd=project,
                       check=True, capture_output=True, env={**os.environ, "PYTHONPATH": str(ROOT)})
        config = json.loads((project / ".taskseam" / "config.json").read_text())
        store = Store(project / ".taskseam" / "state.db")
        store.add_item(config["active_task"], "decision", "Use SQLite", "claude")
        store.close()
        nested = project / "src"
        nested.mkdir()
        out = io.StringIO()
        code = hooks.session_start(io.StringIO(json.dumps({"cwd": str(nested)})), out)
        self.assertEqual(code, 0)
        self.assertIn("Use SQLite", out.getvalue())
        self.assertIn("taskseam_record", out.getvalue())

    def test_session_start_is_silent_outside_workspace_and_with_bad_input(self):
        for payload in (json.dumps({"cwd": str(self.root)}), "not json"):
            out = io.StringIO()
            previous = os.getcwd()
            os.chdir(self.root)
            try:
                self.assertEqual(hooks.session_start(io.StringIO(payload), out), 0)
            finally:
                os.chdir(previous)
            self.assertEqual(out.getvalue(), "")

    def test_install_preserves_settings_and_is_idempotent(self):
        path = self.root / "settings.json"
        path.write_text(json.dumps({"theme": "dark", "hooks": {"SessionStart": [
            {"matcher": "startup", "hooks": [{"type": "command", "command": "echo hi"}]}]}}))
        first = hooks.install(path, "/old/python")
        self.assertEqual(first["status"], "installed")
        self.assertTrue(Path(first["backup"]).exists())
        self.assertEqual(hooks.install(path, "/old/python")["status"], "unchanged")
        self.assertEqual(hooks.install(path, "/new/python")["status"], "updated")
        data = json.loads(path.read_text())
        self.assertEqual(data["theme"], "dark")
        commands = [h["command"] for g in data["hooks"]["SessionStart"] for h in g["hooks"]]
        self.assertEqual(len(commands), 2)
        self.assertIn("echo hi", commands)
        self.assertTrue(any(c.startswith("/new/python") for c in commands))

    def test_install_dry_run_and_invalid_json(self):
        path = self.root / "hooks.json"
        self.assertFalse(hooks.install(path, dry_run=True)["written"])
        self.assertFalse(path.exists())
        path.write_text("{broken")
        with self.assertRaisesRegex(ValueError, "invalid JSON"):
            hooks.install(path)
        self.assertEqual(path.read_text(), "{broken")


class McpUpgradeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.store = Store(Path(self.tmp.name) / "state.db")
        self.task = self.store.create_task("MCP")

    def tearDown(self):
        self.store.close()
        self.tmp.cleanup()

    def call(self, method, params=None, task=True):
        return handle(self.store, {"jsonrpc": "2.0", "id": 1, "method": method, "params": params or {}},
                      active_task_id=self.task if task else None)

    def test_protocol_negotiation(self):
        self.assertEqual(self.call("initialize", {"protocolVersion": "2025-06-18"})
                         ["result"]["protocolVersion"], "2025-06-18")
        self.assertEqual(self.call("initialize", {"protocolVersion": "1999-01-01"})
                         ["result"]["protocolVersion"], PROTOCOL_VERSIONS[0])
        capabilities = self.call("initialize")["result"]["capabilities"]
        self.assertIn("prompts", capabilities)
        self.assertIn("resources", capabilities)

    def test_retire_tool_accepts_prefix_and_returns_structured_content(self):
        item = self.store.add_item(self.task, "constraint", "Offline", "user")
        response = self.call("tools/call", {"name": "taskseam_retire", "arguments": {
            "item_id": item[:6], "reason": "Cut", "source": "user"}})
        self.assertEqual(response["result"]["structuredContent"]["retired"], item)
        self.assertEqual(self.store.current_items(self.task), [])
        listed = self.call("tools/call", {"name": "taskseam_list_tasks"})
        self.assertIsInstance(listed["result"]["structuredContent"]["result"], list)

    def test_continue_prompt_and_resource(self):
        self.store.add_item(self.task, "decision", "Use SQLite", "claude")
        self.assertEqual(self.call("prompts/list")["result"]["prompts"][0]["name"], "continue")
        prompt = self.call("prompts/get", {"name": "continue"})["result"]
        self.assertIn("Use SQLite", prompt["messages"][0]["content"]["text"])
        uri = self.call("resources/list")["result"]["resources"][0]["uri"]
        contents = self.call("resources/read", {"uri": uri})["result"]["contents"]
        self.assertIn("Use SQLite", contents[0]["text"])
        self.assertIn("error", self.call("prompts/get", {"name": "nope"}))
        self.assertIn("error", self.call("resources/read", {"uri": uri}, task=False))
        self.assertEqual(self.call("resources/list", task=False)["result"]["resources"], [])
        self.assertIsNone(self.call("notifications/cancelled"))


class CliFeatureTests(unittest.TestCase):
    def test_show_drop_and_agents_md_export(self):
        with tempfile.TemporaryDirectory() as directory:
            env = {**os.environ, "PYTHONPATH": str(ROOT)}

            def run(*args):
                return subprocess.run([sys.executable, "-m", "taskseam", *args], cwd=directory,
                                      env=env, capture_output=True, text=True, check=True).stdout

            run("init", "CLI")
            item = json.loads(run("record", "constraint", "Offline", "--source", "user"))["item_id"]
            run("record", "decision", "Use SQLite", "--source", "claude")
            self.assertIn("Offline", run("show"))
            run("drop", item[:5], "--reason", "Cut")
            shown = run("show")
            self.assertNotIn("Offline", shown)
            self.assertIn("Use SQLite `", shown)
            agents = Path(directory) / "AGENTS.md"
            agents.write_text("# Agents\n")
            run("export", "--agents-md")
            run("export", "--agents-md")
            text = agents.read_text()
            self.assertEqual(text.count(AGENTS_MD_START), 1)
            self.assertIn("Use SQLite", text)
            exported = json.loads(run("export"))
            self.assertEqual([i["body"] for i in exported["items"]], ["Use SQLite"])


if __name__ == "__main__":
    unittest.main()
