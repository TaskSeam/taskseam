import unittest
from unittest import mock

from taskseam.setup import (claude_command, codex_command, setup_claude,
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
    @mock.patch("taskseam.setup.shutil.which")
    def test_auto_setup_configures_only_detected_tools(self, which, codex, claude):
        which.side_effect = lambda name: "/tools/codex" if name == "codex" else None
        codex.return_value = {"configured": True}
        result = setup_detected("/venv/bin/python")
        self.assertEqual(result["configured"], [{"tool": "codex", "configured": True}])
        self.assertEqual(result["skipped"][0]["tool"], "claude-code")
        claude.assert_not_called()


if __name__ == "__main__":
    unittest.main()
