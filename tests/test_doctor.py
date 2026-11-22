import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from taskseam import doctor, hooks

ROOT = Path(__file__).resolve().parents[1]


def statuses(sections):
    return {(title, check["check"]): check["status"] for title, checks in sections for check in checks}


class DoctorTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.claude = self.root / "home" / ".claude" / "settings.json"
        self.codex = self.root / "home" / ".codex" / "hooks.json"
        patches = [
            mock.patch("taskseam.doctor.AGENTS", (
                ("Claude Code", "claude-code", "claude", lambda: self.claude),
                ("Codex", "codex", "codex", lambda: self.codex))),
            mock.patch("taskseam.doctor.find_agent",
                       side_effect=lambda name: ("/bin/" + name, "PATH") if name == "claude" else (None, None)),
        ]
        for patch in patches:
            patch.start()
            self.addCleanup(patch.stop)

    def tearDown(self):
        self.tmp.cleanup()

    def init_project(self, name="project"):
        project = self.root / name
        project.mkdir()
        subprocess.run([sys.executable, "-m", "taskseam", "init"], cwd=project, check=True,
                       capture_output=True, env={**os.environ, "PYTHONPATH": str(ROOT)})
        return project

    def test_healthy_setup_reports_no_problems(self):
        hooks.install(self.claude, sys.executable)
        project = self.init_project()
        registered = mock.Mock(returncode=0, stdout=sys.executable + " -m taskseam mcp", stderr="")
        with mock.patch("taskseam.doctor.subprocess.run", return_value=registered):
            sections = doctor.diagnose(project)
        result = statuses(sections)
        self.assertEqual(result[("Claude Code", "MCP server")], "ok")
        self.assertEqual(result[("Claude Code", "Session-start hook")], "ok")
        self.assertEqual(result[("Codex", "Installed")], "info")
        self.assertEqual(result[("This folder", "Project")], "ok")
        out = io.StringIO()
        self.assertEqual(doctor.render(sections, out), 0)
        self.assertIn("Everything needed is in place", out.getvalue())

    @mock.patch("taskseam.doctor.subprocess.run")
    def test_missing_registration_hook_and_stale_python_have_fixes(self, run):
        run.return_value = mock.Mock(returncode=1, stdout="", stderr="not found")
        sections = doctor.diagnose(self.root)
        result = statuses(sections)
        self.assertEqual(result[("Claude Code", "MCP server")], "fail")
        self.assertEqual(result[("Claude Code", "Session-start hook")], "fail")
        hooks.install(self.claude, "/gone/python")
        stale = [c for t, cs in doctor.diagnose(self.root, probe_mcp=False) for c in cs
                 if c["check"] == "Session-start hook"][0]
        self.assertIn("no longer exists", stale["detail"])
        self.assertEqual(stale["fix"], "taskseam hook install claude-code")
        out = io.StringIO()
        self.assertEqual(doctor.render(sections, out), 1)
        self.assertIn("fix: taskseam setup claude-code", out.getvalue())

    def test_wrong_folder_points_to_nearby_projects(self):
        self.init_project("app")
        project = [c for t, cs in doctor.diagnose(self.root, probe_mcp=False) for c in cs
                   if c["check"] == "Project"][0]
        self.assertEqual(project["status"], "fail")
        self.assertIn(str(self.root / "app"), project["detail"])

    def test_privacy_warning_when_state_is_not_ignored(self):
        project = self.init_project()
        (project / ".gitignore").write_text("node_modules/\n")
        result = statuses(doctor.diagnose(project, probe_mcp=False))
        self.assertEqual(result[("This folder", "Privacy")], "warn")

    def test_ascii_fallback_for_limited_consoles(self):
        class Ascii(io.StringIO):
            encoding = "ascii"
        out = Ascii()
        doctor.render([("X", [doctor._check("fail", "Thing", "broken", "fix it")])], out)
        self.assertIn("XX Thing", out.getvalue())


class DemoTests(unittest.TestCase):
    def test_demo_tells_the_story_and_cleans_up(self):
        from taskseam.demo import run
        out = io.StringIO()
        with mock.patch("taskseam.demo.tempfile.TemporaryDirectory",
                        wraps=tempfile.TemporaryDirectory) as temporary:
            self.assertEqual(run(pause=0, stream=out), 0)
        text = out.getvalue()
        self.assertIn("+ decision: Export invoices as CSV, not PDF", text)
        self.assertIn("- decision: Export invoices as PDF", text)
        hook_part = text.split("session-start hook")[1].split("Back in Claude Code")[0]
        self.assertNotIn("Export invoices as PDF\n", hook_part)
        self.assertIn("RFC 4180", hook_part)
        created = temporary.call_args.kwargs.get("prefix")
        self.assertEqual(created, "taskseam-demo-")


if __name__ == "__main__":
    unittest.main()
