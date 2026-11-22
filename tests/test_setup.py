import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from taskseam.setup import (claude_command, codex_command, find_agent, setup_claude,
                            setup_codex, setup_detected)


class SetupTests(unittest.TestCase):
    @mock.patch("taskseam.setup.shutil.which")
    def test_codex_command_uses_python_module(self, which):
        which.return_value = "/tools/codex"
        self.assertEqual(codex_command("/venv/bin/python"),
                         ["/tools/codex", "mcp", "add", "taskseam", "--",
                          "/venv/bin/python", "-m", "taskseam", "mcp"])

    @mock.patch("taskseam.setup.subprocess.run")
    @mock.patch("taskseam.setup.shutil.which", return_value="/tools/codex")
    def test_setup_replaces_existing_entry(self, _which, run):
        run.side_effect = [
            mock.Mock(returncode=0),
            mock.Mock(returncode=0, stdout="removed", stderr=""),
            mock.Mock(returncode=0, stdout="added", stderr=""),
        ]
        result = setup_codex("/venv/bin/python")
        self.assertTrue(result["configured"])
        self.assertEqual(run.call_args_list[1].args[0], ["/tools/codex", "mcp", "remove", "taskseam"])
        self.assertEqual(run.call_args_list[2].args[0][-4:], ["/venv/bin/python", "-m", "taskseam", "mcp"])

    @mock.patch("taskseam.setup.shutil.which", return_value="/tools/codex")
    def test_dry_run_does_not_mutate(self, _which):
        result = setup_codex("/venv/bin/python", dry_run=True)
        self.assertFalse(result["configured"])

    @mock.patch("taskseam.setup.shutil.which", return_value="/tools/claude")
    def test_claude_command_uses_user_scope(self, _which):
        self.assertEqual(claude_command("/venv/bin/python"),
                         ["/tools/claude", "mcp", "add", "--scope", "user",
                          "taskseam", "--", "/venv/bin/python", "-m", "taskseam", "mcp"])

    @mock.patch("taskseam.setup.subprocess.run")
    @mock.patch("taskseam.setup.shutil.which", return_value="/tools/claude")
    def test_setup_claude_adds_server(self, _which, run):
        run.side_effect = [mock.Mock(returncode=1),
                           mock.Mock(returncode=0, stdout="added", stderr="")]
        result = setup_claude("/venv/bin/python")
        self.assertTrue(result["configured"])

    @mock.patch("taskseam.setup.setup_claude")
    @mock.patch("taskseam.setup.setup_codex")
    @mock.patch("taskseam.setup.find_agent")
    def test_auto_setup_configures_only_detected_tools(self, find, codex, claude):
        find.side_effect = lambda name: ("/tools/codex", "PATH") if name == "codex" else (None, None)
        codex.return_value = {"configured": True}
        result = setup_detected("/venv/bin/python")
        self.assertEqual(result["configured"],
                         [{"tool": "codex", "found_via": "PATH", "configured": True}])
        self.assertEqual(result["skipped"][0]["tool"], "claude-code")
        claude.assert_not_called()


class FindAgentTests(unittest.TestCase):
    def make_binary(self, path):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("#!/bin/sh\n")
        os.chmod(str(path), 0o755)

    @mock.patch("taskseam.setup.shutil.which", return_value=None)
    def test_finds_newest_bundled_editor_binary(self, _which):
        with tempfile.TemporaryDirectory() as home:
            ext = Path(home) / ".vscode" / "extensions"
            self.make_binary(ext / "anthropic.claude-code-2.1.9-darwin-arm64" /
                             "resources" / "native-binary" / "claude")
            newest = (Path(home) / ".cursor" / "extensions" /
                      "anthropic.claude-code-2.1.10-darwin-arm64" / "resources" / "native-binary" / "claude")
            self.make_binary(newest)
            self.make_binary(ext / "openai.chatgpt-26.1117.4-darwin-arm64" / "bin" / "macos-aarch64" / "codex")
            found, how = find_agent("claude", home)
            self.assertEqual(found, str(newest))
            self.assertIn("2.1.10", how)
            self.assertTrue(find_agent("codex", home)[0].endswith("codex"))

    @mock.patch("taskseam.setup.shutil.which", return_value="/usr/local/bin/claude")
    def test_path_wins_and_missing_returns_none(self, _which):
        self.assertEqual(find_agent("claude"), ("/usr/local/bin/claude", "PATH"))
        with mock.patch("taskseam.setup.shutil.which", return_value=None), \
                tempfile.TemporaryDirectory() as home:
            self.assertEqual(find_agent("codex", home), (None, None))


if __name__ == "__main__":
    unittest.main()
