"""Minimal MCP stdio server exposing TaskSeam's local state."""

import json
import sys

from . import __version__
from .store import Store


SERVER_INSTRUCTIONS = """Use TaskSeam for continuity when an active workspace task is available.
At the start of relevant project work, call taskseam_continue once with a stable lowercase target
for this agent. Use the returned state as evidence and do not invent missing context. During normal
work, call taskseam_record only for a decision the user explicitly accepts, an active constraint,
or a material unresolved question. Never store brainstorming, unaccepted recommendations, secrets,
or unrelated personal context. Use taskseam_resolve when the user explicitly answers a stored
question. Keep durable items concise and self-contained, preserve supersession links, and use the
host's normal approval flow for writes. Do not ask the user to run TaskSeam CLI record commands when
an MCP write tool can complete the operation."""


TOOLS = [
    {"name": "taskseam_list_tasks", "description": "List local TaskSeam tasks",
     "inputSchema": {"type": "object", "properties": {}},
     "annotations": {"readOnlyHint": True}},
    {"name": "taskseam_context", "description": "Get the current state of a task",
     "inputSchema": {"type": "object", "properties": {"task_id": {"type": "string"}},
                     "required": ["task_id"]}, "annotations": {"readOnlyHint": True}},
    {"name": "taskseam_delta", "description": "Get changes between two checkpoints",
     "inputSchema": {"type": "object", "properties": {
         "base": {"type": "string"}, "head": {"type": "string"}},
         "required": ["base", "head"]}, "annotations": {"readOnlyHint": True}},
    {"name": "taskseam_explain", "description": "Show the source evidence for a state item",
     "inputSchema": {"type": "object", "properties": {"item_id": {"type": "string"}},
                     "required": ["item_id"]}, "annotations": {"readOnlyHint": True}},
    {"name": "taskseam_continue",
     "description": "Return changes since a target last received this task, then mark them delivered",
     "inputSchema": {"type": "object", "properties": {
         "task_id": {"type": "string", "description": "Omit for the active workspace task"},
         "target": {"type": "string", "description": "Receiving tool, such as codex"}},
         "required": ["target"]}},
    {"name": "taskseam_record",
     "description": "Record one user-accepted decision, active constraint, or unresolved question",
     "inputSchema": {"type": "object", "properties": {
         "task_id": {"type": "string", "description": "Omit for the active workspace task"},
         "kind": {"type": "string", "enum": ["decision", "constraint", "question"]},
         "body": {"type": "string"},
         "source": {"type": "string", "description": "Originating agent or user"},
         "supersedes": {"type": "string", "description": "Earlier item replaced by this item"}},
         "required": ["kind", "body", "source"]},
     "annotations": {"readOnlyHint": False}},
    {"name": "taskseam_resolve",
     "description": "Resolve an open question with an explicitly accepted decision",
     "inputSchema": {"type": "object", "properties": {
         "task_id": {"type": "string", "description": "Omit for the active workspace task"},
         "question_id": {"type": "string"},
         "decision": {"type": "string"},
         "source": {"type": "string", "description": "Originating agent or user"},
         "supersedes": {"type": "string", "description": "Earlier decision replaced by this resolution"}},
         "required": ["question_id", "decision", "source"]},
     "annotations": {"readOnlyHint": False}},
]


def _result(request_id, value):
    return {"jsonrpc": "2.0", "id": request_id, "result": value}


def _error(request_id, code, message):
    return {"jsonrpc": "2.0", "id": request_id, "error": {"code": code, "message": message}}


def handle(store, request, active_task_id=None):
    request_id, method = request.get("id"), request.get("method")
    if method == "initialize":
        return _result(request_id, {
            "protocolVersion": "2025-06-18",
            "capabilities": {"tools": {"listChanged": False}},
            "serverInfo": {"name": "taskseam", "version": __version__},
            "instructions": SERVER_INSTRUCTIONS,
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
        elif name == "taskseam_continue":
            task_id = args.get("task_id") or active_task_id
            if not task_id:
                raise ValueError("task_id is required outside an initialized workspace")
            value = store.handoff(task_id, args["target"])
        elif name == "taskseam_record":
            task_id = args.get("task_id") or active_task_id
            if not task_id:
                raise ValueError("task_id is required outside an initialized workspace")
            item_id = store.add_item(task_id, args["kind"], args["body"], args["source"],
                                     args.get("supersedes"))
            value = {"item_id": item_id, "recorded": True}
        elif name == "taskseam_resolve":
            task_id = args.get("task_id") or active_task_id
            if not task_id:
                raise ValueError("task_id is required outside an initialized workspace")
            item_id = store.resolve_question(task_id, args["question_id"], args["decision"],
                                             args["source"], args.get("supersedes"))
            value = {"item_id": item_id, "resolved_question": args["question_id"]}
        else:
            return _error(request_id, -32602, "Unknown tool: " + str(name))
        return _result(request_id, {"content": [{"type": "text", "text": json.dumps(value, indent=2)}]})
    except (KeyError, ValueError) as exc:
        return _result(request_id, {"content": [{"type": "text", "text": str(exc)}], "isError": True})


def run(db_path, input_stream=None, output_stream=None, task_id=None):
    input_stream = input_stream or sys.stdin
    output_stream = output_stream or sys.stdout
    store = Store(db_path)
    try:
        for line in input_stream:
            try:
                response = handle(store, json.loads(line), task_id)
            except (json.JSONDecodeError, TypeError) as exc:
                response = _error(None, -32700, "Parse error: " + str(exc))
            if response is not None:
                output_stream.write(json.dumps(response, separators=(",", ":")) + "\n")
                output_stream.flush()
    finally:
        store.close()
