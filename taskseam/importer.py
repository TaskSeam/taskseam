"""Validated, review-first imports of structured task state."""

import json


PACKET_PROMPT = """Return a TaskSeam state packet for our current work.
Include only conclusions I explicitly accepted and questions that remain unresolved.
Do not turn suggestions or hypothetical options into decisions.
Return JSON only, using this exact shape:
{
  "version": 1,
  "items": [
    {"kind": "decision", "body": "one current accepted decision"},
    {"kind": "constraint", "body": "one active constraint"},
    {"kind": "question", "body": "one unresolved question"}
  ]
}
Omit categories that have no supported items. Keep each body concise and self-contained."""


def parse_packet(text):
    try:
        packet = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError("Import must be valid JSON: " + str(exc)) from exc
    if not isinstance(packet, dict) or packet.get("version") != 1:
        raise ValueError("Import packet version must be 1")
    items = packet.get("items")
    if not isinstance(items, list) or not items:
        raise ValueError("Import packet must contain at least one item")
    normalized = []
    for item in items:
        if not isinstance(item, dict):
            raise ValueError("Each imported item must be an object")
        kind, body = item.get("kind"), item.get("body")
        if kind not in ("decision", "question", "constraint"):
            raise ValueError("Invalid imported item kind: " + str(kind))
        if not isinstance(body, str) or not body.strip():
            raise ValueError("Each imported item requires a non-empty body")
        normalized.append({"kind": kind, "body": body.strip()})
    return {"version": 1, "items": normalized}
