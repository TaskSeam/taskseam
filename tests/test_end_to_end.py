import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


class EndToEndTests(unittest.TestCase):
    def test_agent_continuity_through_real_mcp_process(self):
        project_root = str(Path(__file__).resolve().parents[1])
        env = dict(os.environ)
        env.pop("TASKSEAM_DB", None)
        env["PYTHONPATH"] = project_root + os.pathsep + env.get("PYTHONPATH", "")

        with tempfile.TemporaryDirectory() as directory:
            subprocess.run([sys.executable, "-m", "taskseam", "init"], cwd=directory,
                           env=env, check=True, capture_output=True, text=True)
            process = subprocess.Popen(
                [sys.executable, "-m", "taskseam", "mcp"], cwd=directory, env=env,
                stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                text=True,
            )
            try:
                def call(request_id, name, arguments):
                    request = {"jsonrpc": "2.0", "id": request_id, "method": "tools/call",
                               "params": {"name": name, "arguments": arguments}}
                    process.stdin.write(json.dumps(request) + "\n")
                    process.stdin.flush()
                    response = json.loads(process.stdout.readline())
                    self.assertNotIn("error", response)
                    result = response["result"]
                    self.assertFalse(result.get("isError", False), result)
                    return json.loads(result["content"][0]["text"])

                process.stdin.write(json.dumps({"jsonrpc": "2.0", "id": 1,
                                                "method": "initialize"}) + "\n")
                process.stdin.flush()
                initialized = json.loads(process.stdout.readline())
                self.assertIn("explicitly accepts", initialized["result"]["instructions"])

                call(2, "taskseam_record", {
                    "kind": "decision", "body": "Use SQLite", "source": "user"})
                first = call(3, "taskseam_continue", {"target": "codex"})
                self.assertEqual([item["body"] for item in first["added"]], ["Use SQLite"])
                repeated = call(4, "taskseam_continue", {"target": "codex"})
                self.assertFalse(repeated["changed"])

                call(5, "taskseam_record", {
                    "kind": "constraint", "body": "Exports must be deterministic",
                    "source": "claude-code"})
                update = call(6, "taskseam_continue", {"target": "codex"})
                self.assertEqual([item["body"] for item in update["added"]],
                                 ["Exports must be deterministic"])
                self.assertEqual(update["removed"], [])
            finally:
                process.stdin.close()
                process.wait(timeout=5)
                stderr = process.stderr.read()
                process.stdout.close()
                process.stderr.close()
                if process.returncode != 0:
                    self.fail(stderr)


if __name__ == "__main__":
    unittest.main()
