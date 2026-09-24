"""Minimal MCP stdio server exposing TaskSeam's local state."""

import json
import sys

from . import __version__
from .store import Store


TOOLS = [
    {"name": "taskseam_list_tasks", "description": "List local TaskSeam tasks",
     "inputSchema": {"type": "object", "properties": {}}},
    {"name": "taskseam_context", "description": "Get the current state of a task",
     "inputSchema": {"type": "object", "properties": {"task_id": {"type": "string"}},
                     "required": ["task_id"]}},
    {"name": "taskseam_delta", "description": "Get changes between two checkpoints",
     "inputSchema": {"type": "object", "properties": {
         "base": {"type": "string"}, "head": {"type": "string"}},
         "required": ["base", "head"]}},
    {"name": "taskseam_explain", "description": "Show the source evidence for a state item",
     "inputSchema": {"type": "object", "properties": {"item_id": {"type": "string"}},
                     "required": ["item_id"]}},
]


def _result(request_id, value):
    return {"jsonrpc": "2.0", "id": request_id, "result": value}


def _error(request_id, code, message):
    return {"jsonrpc": "2.0", "id": request_id, "error": {"code": code, "message": message}}


def handle(store, request):
    request_id, method = request.get("id"), request.get("method")
    if method == "initialize":
        return _result(request_id, {
            "protocolVersion": "2025-06-18",
            "capabilities": {"tools": {"listChanged": False}},
            "serverInfo": {"name": "taskseam", "version": __version__},
        })
    if method == "ping":
        return _result(request_id, {})
    if method == "tools/list":
        return _result(request_id, {"tools": TOOLS})
    if method == "notifications/initialized":
        return None
    if method != "tools/call":
        return _error(request_id, -32601, "Method not found")
    params = request.get("params") or {}
    name, args = params.get("name"), params.get("arguments") or {}
    try:
        if name == "taskseam_list_tasks":
            value = store.tasks()
        elif name == "taskseam_context":
            value = store.context(args["task_id"])
        elif name == "taskseam_delta":
            value = store.delta(args["base"], args["head"])
        elif name == "taskseam_explain":
            value = store.explain(args["item_id"])
        else:
            return _error(request_id, -32602, "Unknown tool: " + str(name))
        return _result(request_id, {"content": [{"type": "text", "text": json.dumps(value, indent=2)}]})
    except (KeyError, ValueError) as exc:
        return _result(request_id, {"content": [{"type": "text", "text": str(exc)}], "isError": True})


def run(db_path, input_stream=None, output_stream=None):
    input_stream = input_stream or sys.stdin
    output_stream = output_stream or sys.stdout
    store = Store(db_path)
    try:
        for line in input_stream:
            try:
                response = handle(store, json.loads(line))
            except (json.JSONDecodeError, TypeError) as exc:
                response = _error(None, -32700, "Parse error: " + str(exc))
            if response is not None:
                output_stream.write(json.dumps(response, separators=(",", ":")) + "\n")
                output_stream.flush()
    finally:
        store.close()
