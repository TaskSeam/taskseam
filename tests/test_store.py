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


if __name__ == "__main__":
    unittest.main()
