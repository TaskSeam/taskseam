"""A small localhost-only JSON API for TaskSeam clients."""

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

from . import __version__
from .store import Store


def _json(handler, status, payload):
    body = json.dumps(payload).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json")
    handler.send_header("Content-Length", str(len(body)))
    handler.send_header("Cache-Control", "no-store")
    origin = handler.headers.get("Origin", "")
    if origin.startswith("chrome-extension://") or origin.startswith("moz-extension://"):
        handler.send_header("Access-Control-Allow-Origin", origin)
        handler.send_header("Vary", "Origin")
    handler.end_headers()
    handler.wfile.write(body)


def make_handler(db_path, token=None, active_task_id=None):
    class Handler(BaseHTTPRequestHandler):
        server_version = "TaskSeam/" + __version__

        def log_message(self, fmt, *args):
            return

        def _body(self):
            try:
                length = int(self.headers.get("Content-Length", "0"))
                if length > 1_000_000:
                    raise ValueError("Request body is too large")
                return json.loads(self.rfile.read(length) or b"{}")
            except (ValueError, json.JSONDecodeError) as exc:
                raise ValueError("Invalid JSON body") from exc

        def _run(self, action):
            store = Store(db_path)
            try:
                return action(store)
            finally:
                store.close()

        def _authorized(self):
            if token is None:
                return True
            return self.headers.get("Authorization") == "Bearer " + token

        def _require_auth(self):
            if self._authorized():
                return True
            _json(self, 401, {"error": "Invalid or missing TaskSeam pairing token"})
            return False

        def do_OPTIONS(self):
            origin = self.headers.get("Origin", "")
            if not (origin.startswith("chrome-extension://") or
                    origin.startswith("moz-extension://")):
                return _json(self, 403, {"error": "Extension origin required"})
            self.send_response(204)
            self.send_header("Access-Control-Allow-Origin", origin)
            self.send_header("Access-Control-Allow-Headers", "Authorization, Content-Type")
            self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
            self.send_header("Access-Control-Max-Age", "600")
            self.end_headers()

        def do_GET(self):
            parts = [part for part in urlparse(self.path).path.split("/") if part]
            try:
                if parts == ["health"]:
                    result = {"status": "ok", "version": __version__, "storage": "local"}
                elif parts == ["v1", "active"]:
                    if not self._require_auth():
                        return
                    if not active_task_id:
                        raise ValueError("No active workspace task")
                    result = self._run(lambda store: store.context(active_task_id))
                elif parts == ["v1", "tasks"]:
                    if not self._require_auth():
                        return
                    result = self._run(lambda store: store.tasks())
                elif len(parts) == 4 and parts[:2] == ["v1", "tasks"] and parts[3] == "context":
                    if not self._require_auth():
                        return
                    result = self._run(lambda store: store.context(parts[2]))
                elif len(parts) == 3 and parts[:2] == ["v1", "items"]:
                    if not self._require_auth():
                        return
                    result = self._run(lambda store: store.explain(parts[2]))
                else:
                    return _json(self, 404, {"error": "Not found"})
                _json(self, 200, result)
            except ValueError as exc:
                _json(self, 404, {"error": str(exc)})

        def do_POST(self):
            parts = [part for part in urlparse(self.path).path.split("/") if part]
            try:
                if not self._require_auth():
                    return
                body = self._body()
                if parts == ["v1", "tasks"]:
                    title = _required(body, "title")
                    result = self._run(lambda store: {"id": store.create_task(title), "title": title})
                elif len(parts) == 4 and parts[:2] == ["v1", "tasks"] and parts[3] == "items":
                    result = self._run(lambda store: {"item_id": store.add_item(
                        parts[2], _required(body, "kind"), _required(body, "body"),
                        body.get("source", "api"), body.get("supersedes")
                    )})
                elif len(parts) == 4 and parts[:2] == ["v1", "tasks"] and parts[3] == "checkpoint":
                    result = self._run(lambda store: {"checkpoint_id": store.checkpoint(parts[2])})
                elif parts == ["v1", "delta"]:
                    result = self._run(lambda store: store.delta(
                        _required(body, "base"), _required(body, "head")
                    ))
                elif parts == ["v1", "active", "import"]:
                    if not active_task_id:
                        raise ValueError("No active workspace task")
                    items = body.get("items")
                    if not isinstance(items, list) or not items:
                        raise ValueError("Missing or empty field: items")
                    normalized = []
                    for item in items:
                        if not isinstance(item, dict):
                            raise ValueError("Each item must be an object")
                        kind = _required(item, "kind")
                        if kind not in ("decision", "constraint", "question"):
                            raise ValueError("Unsupported item kind: " + kind)
                        normalized.append({"kind": kind, "body": _required(item, "body")})
                    source = body.get("source", "browser-extension")
                    evidence = body.get("evidence", json.dumps({"items": normalized}))
                    result = self._run(lambda store: store.import_items(
                        active_task_id, source, evidence, normalized))
                else:
                    return _json(self, 404, {"error": "Not found"})
                _json(self, 201, result)
            except ValueError as exc:
                _json(self, 400, {"error": str(exc)})

    return Handler


def _required(body, key):
    value = body.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError("Missing or empty field: " + key)
    return value.strip()


def serve(db_path, host="127.0.0.1", port=8765, token=None, active_task_id=None):
    if host not in ("127.0.0.1", "localhost", "::1"):
        raise ValueError("TaskSeam only binds to a localhost address")
    server = ThreadingHTTPServer((host, port), make_handler(db_path, token, active_task_id))
    print("TaskSeam listening on http://{}:{}".format(host, server.server_port), flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
