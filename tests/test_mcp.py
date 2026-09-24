import json
import tempfile
import unittest
from pathlib import Path

from taskseam.mcp import TOOLS, handle
from taskseam.store import Store


class McpTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.store = Store(Path(self.tmp.name) / "state.db")

    def tearDown(self):
        self.store.close()
        self.tmp.cleanup()

    def test_initialize_and_tools(self):
        initialized = handle(self.store, {"jsonrpc": "2.0", "id": 1, "method": "initialize"})
        self.assertEqual(initialized["result"]["serverInfo"]["name"], "taskseam")
        listed = handle(self.store, {"jsonrpc": "2.0", "id": 2, "method": "tools/list"})
        self.assertEqual(listed["result"]["tools"], TOOLS)

    def test_context_tool(self):
        task = self.store.create_task("MCP task")
        self.store.add_item(task, "decision", "Keep data local", "manual")
        response = handle(self.store, {"jsonrpc": "2.0", "id": 3, "method": "tools/call",
                                      "params": {"name": "taskseam_context",
                                                 "arguments": {"task_id": task}}})
        value = json.loads(response["result"]["content"][0]["text"])
        self.assertEqual(value["items"][0]["body"], "Keep data local")

    def test_continue_uses_active_task_and_tracks_delivery(self):
        task = self.store.create_task("Active task")
        self.store.add_item(task, "decision", "Keep data local", "manual")
        request = {"jsonrpc": "2.0", "id": 4, "method": "tools/call", "params": {
            "name": "taskseam_continue", "arguments": {"target": "codex"}
        }}
        first = handle(self.store, request, active_task_id=task)
        first_value = json.loads(first["result"]["content"][0]["text"])
        self.assertTrue(first_value["changed"])
        second = handle(self.store, request, active_task_id=task)
        second_value = json.loads(second["result"]["content"][0]["text"])
        self.assertFalse(second_value["changed"])


if __name__ == "__main__":
    unittest.main()
