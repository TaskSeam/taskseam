"""Minimal MCP stdio server exposing TaskSeam's local state."""

import json
import sys

from . import __version__
from .render import brief
from .store import Store

# Handshake-based revisions this server implements. The newest is preferred;
# an older client receives the revision it requested.
PROTOCOL_VERSIONS = ("2025-11-25", "2025-06-18", "2025-03-26")
RESOURCE_URI = "taskseam://active/brief"


SERVER_INSTRUCTIONS = """Use TaskSeam for continuity when an active workspace task is available.
At the start of relevant project work, call taskseam_continue once with a stable lowercase target
for this agent. Set full=true in a fresh chat or after losing prior context; otherwise use the delta.
An unchanged delta does not mean the task has no current state.
Use the returned state as evidence and do not invent missing context. During normal
work, call taskseam_record only for a decision the user explicitly accepts, an active constraint,
or a material unresolved question. Never store brainstorming, unaccepted recommendations, secrets,
or unrelated personal context. Use taskseam_resolve when the user explicitly answers a stored
question. Use taskseam_retire when the user says a stored item no longer applies and nothing
replaces it. Item IDs accept unique prefixes of at least four characters. Keep durable items concise and self-contained, preserve supersession links, and use the
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
     "description": "Return changes since a target last received this task, then mark them delivered. Set full=true to also recover current state in a fresh chat.",
     "inputSchema": {"type": "object", "properties": {
         "task_id": {"type": "string", "description": "Omit for the active workspace task"},
         "target": {"type": "string", "description": "Receiving tool, such as codex"},
         "full": {"type": "boolean", "default": False,
                  "description": "Include current state even if this target has no unseen changes"}},
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
    {"name": "taskseam_retire",
     "description": "Remove a decision, constraint, or question the user says no longer applies, when nothing replaces it",
     "inputSchema": {"type": "object", "properties": {
         "task_id": {"type": "string", "description": "Omit for the active workspace task"},
         "item_id": {"type": "string", "description": "Item ID or unique prefix"},
         "reason": {"type": "string", "description": "Why the item no longer applies"},
         "source": {"type": "string", "description": "Originating agent or user"}},
         "required": ["item_id", "reason", "source"]},
     "annotations": {"readOnlyHint": False, "destructiveHint": False}},
]

PROMPTS = [
    {"name": "continue",
     "title": "Continue with TaskSeam",
     "description": "Load this project's accepted decisions, constraints, and open questions"},
]


def _result(request_id, value):
    return {"jsonrpc": "2.0", "id": request_id, "result": value}


def _error(request_id, code, message):
    return {"jsonrpc": "2.0", "id": request_id, "error": {"code": code, "message": message}}


def handle(store, request, active_task_id=None):
    request_id, method = request.get("id"), request.get("method")
    if method == "initialize":
        requested = (request.get("params") or {}).get("protocolVersion")
        return _result(request_id, {
            "protocolVersion": requested if requested in PROTOCOL_VERSIONS else PROTOCOL_VERSIONS[0],
            "capabilities": {"tools": {"listChanged": False}, "prompts": {"listChanged": False},
                             "resources": {"listChanged": False}},
            "serverInfo": {"name": "taskseam", "version": __version__},
            "instructions": SERVER_INSTRUCTIONS,
        })
    if method == "ping":
        return _result(request_id, {})
    if method == "tools/list":
        return _result(request_id, {"tools": TOOLS})
    if isinstance(method, str) and method.startswith("notifications/"):
        return None
    if method in ("prompts/list", "prompts/get", "resources/list", "resources/read"):
        return _prompt_or_resource(store, request_id, method, request.get("params") or {},
                                   active_task_id)
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
            value = store.explain(store.resolve_item_id(args["item_id"]))
        elif name == "taskseam_continue":
            task_id = args.get("task_id") or active_task_id
            if not task_id:
                raise ValueError("task_id is required outside an initialized workspace")
            value = store.handoff(task_id, args["target"], full=args.get("full", False))
        elif name == "taskseam_record":
            task_id = args.get("task_id") or active_task_id
            if not task_id:
                raise ValueError("task_id is required outside an initialized workspace")
            supersedes = args.get("supersedes")
            item_id = store.add_item(task_id, args["kind"], args["body"], args["source"],
                                     store.resolve_item_id(supersedes, task_id) if supersedes else None)
            value = {"item_id": item_id, "recorded": True}
        elif name == "taskseam_resolve":
            task_id = args.get("task_id") or active_task_id
            if not task_id:
                raise ValueError("task_id is required outside an initialized workspace")
            supersedes = args.get("supersedes")
            question_id = store.resolve_item_id(args["question_id"], task_id)
            item_id = store.resolve_question(task_id, question_id, args["decision"], args["source"],
                                             store.resolve_item_id(supersedes, task_id) if supersedes else None)
            value = {"item_id": item_id, "resolved_question": question_id}
        elif name == "taskseam_retire":
            task_id = args.get("task_id") or active_task_id
            if not task_id:
                raise ValueError("task_id is required outside an initialized workspace")
            value = store.retire_item(task_id, store.resolve_item_id(args["item_id"], task_id),
                                      args["reason"], args["source"])
        else:
            return _error(request_id, -32602, "Unknown tool: " + str(name))
        result = {"content": [{"type": "text", "text": json.dumps(value, indent=2)}]}
        result["structuredContent"] = value if isinstance(value, dict) else {"result": value}
        return _result(request_id, result)
    except (KeyError, ValueError) as exc:
        return _result(request_id, {"content": [{"type": "text", "text": str(exc)}], "isError": True})


def _prompt_or_resource(store, request_id, method, params, active_task_id):
    if method == "prompts/list":
        return _result(request_id, {"prompts": PROMPTS})
    if method == "resources/list":
        resources = []
        if active_task_id:
            resources.append({"uri": RESOURCE_URI, "name": "active-task-brief",
                              "title": "TaskSeam project state", "mimeType": "text/markdown",
                              "description": "Current decisions, constraints, and open questions"})
        return _result(request_id, {"resources": resources})
    if method == "prompts/get" and params.get("name") != "continue":
        return _error(request_id, -32602, "Unknown prompt: " + str(params.get("name")))
    if method == "resources/read" and params.get("uri") != RESOURCE_URI:
        return _error(request_id, -32002, "Resource not found: " + str(params.get("uri")))
    if not active_task_id:
        return _error(request_id, -32002, "No active TaskSeam workspace; run 'taskseam init'")
    try:
        context = store.context(active_task_id)
    except ValueError as exc:
        return _error(request_id, -32002, str(exc))
    text = brief(context["task"], context["items"])
    if method == "resources/read":
        return _result(request_id, {"contents": [
            {"uri": RESOURCE_URI, "mimeType": "text/markdown", "text": text}]})
    return _result(request_id, {
        "description": "TaskSeam state for " + context["task"]["title"],
        "messages": [{"role": "user", "content": {"type": "text", "text": (
            "Continue this project using its recorded TaskSeam state below. Summarize the accepted "
            "decisions, active constraints, and open questions that matter for the next step, then "
            "call taskseam_continue once so later changes from other agents arrive as a delta.\n\n"
            + text)}}],
    })


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
