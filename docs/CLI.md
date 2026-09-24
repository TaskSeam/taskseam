# TaskSeam CLI reference

These commands are for inspection, scripting, correction, and tools that cannot use TaskSeam's MCP write tools. Normal users initialize a project once and work through their agent.

## Inspect a workspace

```bash
taskseam status
taskseam context
```

## Record state manually

```bash
taskseam record decision "Use SQLite" --source user
taskseam record constraint "Exports must be deterministic" --source user
taskseam record question "Which export format should we use?" --source user
```

Use `--supersedes ITEM_ID` when a new item replaces an earlier decision or constraint.

## Resolve and correct state

```bash
taskseam resolve QUESTION_ID "Use Markdown exports" --source user
taskseam supersede OLD_ITEM_ID --with NEW_ITEM_ID
```

## Import from a client without MCP writes

Ask the client to answer the prompt printed by:

```bash
taskseam prompt
```

Save its JSON response as `packet.json`, preview it, and apply only after review:

```bash
taskseam import packet.json --source your-tool
taskseam import packet.json --source your-tool --apply
```

## Checkpoints and delivery

```bash
taskseam checkpoint
taskseam delta BASE_CHECKPOINT HEAD_CHECKPOINT
taskseam handoff --to TARGET
```

Each target maintains an independent delivery checkpoint. A repeated handoff returns only changes since that target's previous delivery.

Run `taskseam --help` or `taskseam COMMAND --help` for the complete command and option list.
