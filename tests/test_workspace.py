import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


class WorkspaceTests(unittest.TestCase):
    def run_cli(self, cwd, *args, check=True):
        env = dict(os.environ)
        env.pop("TASKSEAM_DB", None)
        project_root = str(Path(__file__).resolve().parents[1])
        env["PYTHONPATH"] = project_root + os.pathsep + env.get("PYTHONPATH", "")
        result = subprocess.run([sys.executable, "-m", "taskseam", *args], cwd=cwd,
                                env=env, capture_output=True, text=True, check=check)
        return result

    def test_init_record_checkpoint_and_nested_discovery(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            nested = root / "src"
            nested.mkdir()
            initialized = json.loads(self.run_cli(root, "init", "Workspace task").stdout)
            self.assertEqual(initialized["project"], root.name)
            self.assertIn(".taskseam/", (root / ".gitignore").read_text())

            item = json.loads(self.run_cli(nested, "record", "decision", "Use SQLite",
                                           "--source", "test").stdout)
            self.assertIn("item_id", item)
            checkpoint = json.loads(self.run_cli(nested, "checkpoint").stdout)
            self.assertIn("checkpoint_id", checkpoint)
            context = json.loads(self.run_cli(nested, "context").stdout)
            self.assertEqual(context["items"][0]["body"], "Use SQLite")
            status = json.loads(self.run_cli(nested, "status").stdout)
            self.assertEqual(status["active_task"]["task"]["id"], initialized["active_task"])

            question = json.loads(self.run_cli(
                nested, "record", "question", "Readable raw data?", "--source", "claude"
            ).stdout)["item_id"]
            resolved = json.loads(self.run_cli(
                nested, "resolve", question, "Export deterministic Markdown", "--source", "codex"
            ).stdout)
            self.assertEqual(resolved["resolved_question"], question)
            current = json.loads(self.run_cli(nested, "context").stdout)["items"]
            self.assertNotIn(question, {item["id"] for item in current})
            self.assertIn(question, {item["resolves"] for item in current})

    def test_duplicate_init_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            self.run_cli(directory, "init")
            result = self.run_cli(directory, "init", check=False)
            self.assertEqual(result.returncode, 1)
            self.assertIn("already initialized", result.stderr)


if __name__ == "__main__":
    unittest.main()
