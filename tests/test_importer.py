import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from taskseam.importer import parse_packet
from taskseam.store import Store


class ImporterTests(unittest.TestCase):
    def test_parse_packet_normalizes_items(self):
        packet = parse_packet(json.dumps({"version": 1, "items": [
            {"kind": "decision", "body": "  Use SQLite  "},
            {"kind": "question", "body": "Which export format?"},
        ]}))
        self.assertEqual(packet["items"][0]["body"], "Use SQLite")

    def test_invalid_packet_is_rejected(self):
        with self.assertRaises(ValueError):
            parse_packet('{"version": 1, "items": [{"kind": "idea", "body": "Maybe"}]}')

    def test_preview_then_apply_preserves_shared_evidence(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            project_root = str(Path(__file__).resolve().parents[1])
            env = dict(os.environ, PYTHONPATH=project_root)
            env.pop("TASKSEAM_DB", None)

            def run(*args, input_text=None):
                return subprocess.run([sys.executable, "-m", "taskseam", *args], cwd=root,
                                      env=env, input=input_text, capture_output=True,
                                      text=True, check=True)

            run("init", "Imported task")
            raw = json.dumps({"version": 1, "items": [
                {"kind": "decision", "body": "Use SQLite"},
                {"kind": "question", "body": "Which export format?"},
            ]})
            preview = json.loads(run("import", "--source", "claude-web", input_text=raw).stdout)
            self.assertFalse(preview["applied"])
            self.assertEqual(json.loads(run("context").stdout)["items"], [])

            applied = json.loads(run("import", "--source", "claude-web", "--apply",
                                     input_text=raw).stdout)
            self.assertTrue(applied["applied"])
            self.assertEqual(len(applied["item_ids"]), 2)
            store = Store(root / ".taskseam" / "state.db")
            try:
                evidence = {store.explain(item_id)["evidence"] for item_id in applied["item_ids"]}
                self.assertEqual(evidence, {raw})
            finally:
                store.close()


if __name__ == "__main__":
    unittest.main()
