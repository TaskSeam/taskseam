import tempfile
import unittest
from pathlib import Path

from taskseam.store import Store


class StoreTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.store = Store(Path(self.tmp.name) / "state.db")
        self.task = self.store.create_task("Build capture prototype")

    def tearDown(self):
        self.store.close()
        self.tmp.cleanup()

    def test_checkpoint_delta_and_provenance(self):
        first = self.store.add_item(self.task, "decision", "Use Markdown", "chatgpt")
        base = self.store.checkpoint(self.task)
        second = self.store.add_item(self.task, "decision", "Use SQLite", "claude", supersedes=first)
        question = self.store.add_item(self.task, "question", "How should permissions work?", "claude")
        head = self.store.checkpoint(self.task)

        delta = self.store.delta(base, head)
        self.assertEqual({row["id"] for row in delta["added"]}, {second, question})
        self.assertEqual([row["id"] for row in delta["removed"]], [first])
        self.assertEqual({row["id"] for row in self.store.current_items(self.task)}, {second, question})
        self.assertEqual(self.store.explain(second)["source"], "claude")
        self.assertEqual(self.store.explain(second)["evidence"], "Use SQLite")

    def test_invalid_supersession_does_not_write_event(self):
        first = self.store.add_item(self.task, "decision", "Use Markdown", "chatgpt")
        other = self.store.create_task("Other task")
        with self.assertRaises(ValueError):
            self.store.add_item(other, "decision", "Use SQLite", "claude", supersedes=first)
        with self.assertRaises(ValueError):
            self.store.add_item(self.task, "question", "Open?", "claude", supersedes=first)
        self.assertEqual(len(self.store.items(other)), 0)

    def test_cross_task_delta_rejected(self):
        other = self.store.create_task("Other task")
        with self.assertRaises(ValueError):
            self.store.delta(self.store.checkpoint(self.task), self.store.checkpoint(other))

    def test_resolving_question_creates_decision_and_delta(self):
        question = self.store.add_item(self.task, "question", "Readable raw data?", "claude")
        base = self.store.checkpoint(self.task)
        decision = self.store.resolve_question(
            self.task, question, "Keep SQLite canonical and export Markdown", "codex"
        )
        head = self.store.checkpoint(self.task)
        current = self.store.current_items(self.task)
        self.assertEqual([item["id"] for item in current], [decision])
        self.assertEqual(current[0]["resolves"], question)
        delta = self.store.delta(base, head)
        self.assertEqual([item["id"] for item in delta["added"]], [decision])
        self.assertEqual([item["id"] for item in delta["removed"]], [question])

    def test_question_cannot_be_resolved_twice(self):
        question = self.store.add_item(self.task, "question", "Readable raw data?", "claude")
        self.store.resolve_question(self.task, question, "Export Markdown", "codex")
        with self.assertRaises(ValueError):
            self.store.resolve_question(self.task, question, "Export JSON", "manual")

    def test_resolution_can_supersede_existing_decision(self):
        old = self.store.add_item(self.task, "decision", "Use SQLite", "claude")
        question = self.store.add_item(self.task, "question", "Readable state?", "claude")
        new = self.store.resolve_question(
            self.task, question, "Use SQLite with Markdown export", "user", supersedes=old
        )
        self.assertEqual([item["id"] for item in self.store.current_items(self.task)], [new])

    def test_existing_items_can_be_linked_as_supersession_correction(self):
        old = self.store.add_item(self.task, "decision", "Use SQLite", "claude")
        new = self.store.add_item(self.task, "decision", "Use SQLite with Markdown export", "user")
        self.store.set_supersession(self.task, old, new)
        self.assertEqual([item["id"] for item in self.store.current_items(self.task)], [new])
        with self.assertRaises(ValueError):
            self.store.set_supersession(self.task, new, old)

    def test_version_one_database_migrates(self):
        path = Path(self.tmp.name) / "legacy.db"
        legacy = Store(path)
        legacy.db.execute("DROP TABLE resolutions")
        legacy.db.execute("DROP TABLE deliveries")
        legacy.db.execute("PRAGMA user_version = 1")
        legacy.db.commit()
        legacy.close()
        migrated = Store(path)
        try:
            self.assertEqual(migrated.db.execute("PRAGMA user_version").fetchone()[0], 4)
            self.assertIsNotNone(migrated.db.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='resolutions'"
            ).fetchone())
            self.assertIsNotNone(migrated.db.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='deliveries'"
            ).fetchone())
        finally:
            migrated.close()

    def test_full_handoff_recovers_state_without_repeating_delta(self):
        old = self.store.add_item(self.task, "decision", "Use Markdown", "user")
        question = self.store.add_item(self.task, "question", "Offline?", "user")
        initial = self.store.handoff(self.task, "codex")
        self.store.handoff(self.task, "claude")
        new = self.store.add_item(self.task, "decision", "Use SQLite", "user", old)
        answer = self.store.resolve_question(self.task, question, "Require offline", "user")
        recovered = self.store.handoff(self.task, " CODEX ", full=True)
        self.assertEqual({i["id"] for i in recovered["current"]}, {new, answer})
        self.assertEqual({i["id"] for i in recovered["removed"]}, {old, question})
        self.assertEqual(recovered["base"], initial["head"])
        checkpoints = len(self.store.checkpoints(self.task))
        repeated = self.store.handoff(self.task, "codex", full=True)
        self.assertFalse(repeated["changed"])
        self.assertEqual(repeated["current"], recovered["current"])
        self.assertEqual(len(self.store.checkpoints(self.task)), checkpoints)
        self.assertNotIn("current", self.store.handoff(self.task, "codex"))
        other = self.store.handoff(self.task, "claude")
        self.assertEqual({i["id"] for i in other["added"]}, {new, answer})

    def test_full_handoff_empty_and_invalid_requests(self):
        empty = self.store.handoff(self.task, "codex", full=True)
        self.assertEqual(empty["current"], [])
        self.assertFalse(empty["changed"])
        with self.assertRaisesRegex(ValueError, "boolean"):
            self.store.handoff(self.task, "claude", full="false")
        self.assertIsNone(self.store.handoff(self.task, "claude")["base"])

    def test_full_handoff_excludes_other_tasks(self):
        other = self.store.create_task("Private unrelated task")
        self.store.add_item(other, "constraint", "Unrelated material", "user")
        item = self.store.add_item(self.task, "constraint", "Local only", "user")
        result = self.store.handoff(self.task, "codex", full=True)
        self.assertEqual([i["id"] for i in result["current"]], [item])
        self.assertEqual(result["current"][0]["source"], "user")

    def test_handoff_tracks_each_target_checkpoint(self):
        first = self.store.add_item(self.task, "decision", "Use SQLite", "claude")
        initial = self.store.handoff(self.task, "codex")
        self.assertIsNone(initial["base"])
        self.assertEqual([item["id"] for item in initial["added"]], [first])
        self.assertTrue(initial["changed"])

        unchanged = self.store.handoff(self.task, "codex")
        self.assertFalse(unchanged["changed"])
        self.assertEqual(unchanged["base"], unchanged["head"])

        second = self.store.add_item(self.task, "constraint", "Stay local", "claude")
        update = self.store.handoff(self.task, "codex")
        self.assertEqual([item["id"] for item in update["added"]], [second])
        self.assertEqual(update["base"], initial["head"])

        other_target = self.store.handoff(self.task, "claude")
        self.assertEqual({item["id"] for item in other_target["added"]}, {first, second})


if __name__ == "__main__":
    unittest.main()
