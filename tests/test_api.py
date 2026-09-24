import json
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path

from taskseam.api import make_handler


class ApiTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Path(self.tmp.name) / "state.db"
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(self.db))
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.url = "http://127.0.0.1:{}".format(self.server.server_port)

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()
        self.tmp.cleanup()

    def request(self, path, body=None):
        data = None if body is None else json.dumps(body).encode()
        req = urllib.request.Request(self.url + path, data=data,
                                     headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req) as response:
            return response.status, json.load(response)

    def authorized_request(self, path, token, body=None):
        data = None if body is None else json.dumps(body).encode()
        req = urllib.request.Request(self.url + path, data=data, headers={
            "Content-Type": "application/json", "Authorization": "Bearer " + token})
        with urllib.request.urlopen(req) as response:
            return response.status, json.load(response)

    def test_health_and_task_flow(self):
        status, health = self.request("/health")
        self.assertEqual(status, 200)
        self.assertEqual(health["storage"], "local")
        _, task = self.request("/v1/tasks", {"title": "API task"})
        _, item = self.request("/v1/tasks/{}/items".format(task["id"]), {
            "kind": "decision", "body": "Use SQLite", "source": "test"
        })
        _, context = self.request("/v1/tasks/{}/context".format(task["id"]))
        self.assertEqual(context["items"][0]["id"], item["item_id"])

    def test_rejects_invalid_payload(self):
        with self.assertRaises(urllib.error.HTTPError) as caught:
            self.request("/v1/tasks", {})
        self.assertEqual(caught.exception.code, 400)

    def test_authenticated_browser_import_uses_active_task(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()
        from taskseam.store import Store
        store = Store(self.db)
        task = store.create_task("Browser task")
        store.close()
        self.server = ThreadingHTTPServer(
            ("127.0.0.1", 0), make_handler(self.db, "secret", task))
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.url = "http://127.0.0.1:{}".format(self.server.server_port)

        with self.assertRaises(urllib.error.HTTPError) as caught:
            self.request("/v1/active")
        self.assertEqual(caught.exception.code, 401)
        status, imported = self.authorized_request("/v1/active/import", "secret", {
            "source": "chatgpt-web", "evidence": "accepted response",
            "items": [{"kind": "decision", "body": "Use SQLite"}]
        })
        self.assertEqual(status, 201)
        self.assertEqual(len(imported["item_ids"]), 1)
        _, context = self.authorized_request("/v1/active", "secret")
        self.assertEqual(context["items"][0]["source"], "chatgpt-web")


if __name__ == "__main__":
    unittest.main()
