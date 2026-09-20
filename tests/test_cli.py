import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


class CliTests(unittest.TestCase):
    def test_handoff_flow(self):
        with tempfile.TemporaryDirectory() as directory:
            db = Path(directory) / "state.db"

            def run(*args):
                command = [sys.executable, "-m", "taskseam", "--db", str(db), *args]
                result = subprocess.run(command, capture_output=True, text=True, check=True)
                return json.loads(result.stdout)

            task = run("task", "create", "Prototype")["id"]
            first = run("item", task, "decision", "Use Markdown", "--source", "chatgpt")["item_id"]
            base = run("checkpoint", task)["checkpoint_id"]
            second = run("item", task, "decision", "Use SQLite", "--source", "claude",
                         "--supersedes", first)["item_id"]
            head = run("checkpoint", task)["checkpoint_id"]

            delta = run("delta", base, head)
            self.assertEqual(delta["added"][0]["id"], second)
            self.assertEqual(delta["removed"][0]["id"], first)
            self.assertEqual(run("context", task)["items"][0]["body"], "Use SQLite")
            self.assertEqual(run("explain", second)["source"], "claude")


if __name__ == "__main__":
    unittest.main()
