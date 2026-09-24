import unittest
from unittest import mock

from taskseam.setup import codex_command, setup_codex


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


if __name__ == "__main__":
    unittest.main()
