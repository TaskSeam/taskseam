---
name: task-continuity
description: Continue work in a TaskSeam initialized project. Use whenever starting or resuming project work, when the user refers to earlier decisions or another AI session, or when an explicitly accepted decision, active constraint, or unresolved question should persist for another agent.
---

# TaskSeam continuity

Use TaskSeam as the project task-state layer when its MCP tools are available.

## Start or resume work

1. Call `taskseam_continue` once with a stable lowercase target identifying this agent, such as `codex` or `claude-code`.
2. Treat returned current items and changes as task evidence. Do not invent missing context.
3. If there are no unseen changes, continue without making TaskSeam the focus of the response.
4. Call `taskseam_explain` when the origin or reasoning for an item matters.

## Save durable state

Use `taskseam_record` only when the conversation supports one of these items:

- `decision`: a conclusion the user explicitly accepted.
- `constraint`: a requirement that currently governs the task.
- `question`: a material question that remains unresolved.

Keep each body concise and self-contained. Set `source` to the originating agent or `user`. When a new item replaces an existing item, pass the earlier item ID as `supersedes`.

Do not record brainstorming, recommendations awaiting acceptance, implementation details already evident from code, casual discussion, secrets, or unrelated personal context. Never turn a suggestion or inference into a decision.

Use `taskseam_resolve` when the user explicitly answers a stored open question. Include `supersedes` when that answer also replaces an earlier decision.

## Interaction behavior

- Use the host's normal approval UI for write tools.
- Briefly say what durable state is being saved when approval is requested.
- Do not ask the user to run TaskSeam CLI commands when the MCP tool can perform the operation.
- Do not expose internal checkpoints or item IDs unless the user asks or they are needed to correct state.
- If no TaskSeam workspace is active, continue the user's work normally and mention initialization only when continuity would materially help.
