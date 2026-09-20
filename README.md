# TaskSeam

**Switch AI. Keep working.**

TaskSeam is a project for carrying the state of your work between AI tools. When a task moves from ChatGPT to Claude to Codex, the next assistant should understand the current goal, accepted decisions, open questions, and relevant files without asking you to reconstruct the story.

The project is in **early development**. A local CLI can record task state and produce checkpoint deltas today. Automatic capture and integrations with AI tools have not been built yet. The first goal is to prove one useful, trustworthy handoff.

## The problem

A real task rarely fits in one conversation. You might explore an idea in ChatGPT, change the design in Claude, and implement it in Codex. Each tool sees only part of the work. Copying a transcript is tedious, and a summary can miss the decision that changed yesterday.

TaskSeam aims to keep track of the *task* across those conversations and give each assistant the context it needs to continue.

## What a handoff could look like

Suppose you discuss a feature in ChatGPT, then decide in Claude to use SQLite instead of a Markdown state file. When you open Codex in the repository, TaskSeam should be able to show:

```text
Task: Build the local capture prototype

Current decision: Use SQLite for local storage.
Changed since the last handoff: The Markdown state file was superseded.
Open question: How should browser capture permissions work?
Relevant artifact: docs/event-schema.md

Each item links back to the conversation or file that supports it.
```

The CLI can record and compare these state changes when you enter them manually. Automatic detection and delivery to Codex are still planned.

## Try the local prototype

Requires Python 3.9 or newer. From the repository root:

```bash
python3 -m taskseam --db .taskseam/state.db task create "Build capture prototype"
```

The command prints a task ID. Use that ID in the commands below; each `item` command also prints an item ID.

```bash
python3 -m taskseam --db .taskseam/state.db item TASK_ID decision "Use Markdown" --source chatgpt
python3 -m taskseam --db .taskseam/state.db checkpoint TASK_ID
python3 -m taskseam --db .taskseam/state.db item TASK_ID decision "Use SQLite" --source claude --supersedes FIRST_ITEM_ID
python3 -m taskseam --db .taskseam/state.db item TASK_ID question "How should browser capture permissions work?" --source claude
python3 -m taskseam --db .taskseam/state.db checkpoint TASK_ID
python3 -m taskseam --db .taskseam/state.db delta FIRST_CHECKPOINT_ID SECOND_CHECKPOINT_ID
python3 -m taskseam --db .taskseam/state.db context TASK_ID
python3 -m taskseam --db .taskseam/state.db explain SQLITE_ITEM_ID
```

Output is JSON. The database stays on your machine, and `.taskseam/` is ignored by Git. Source names are labels you enter manually; the prototype does not verify or capture those sources. You can also install the CLI locally with `python3 -m pip install -e .` and run `taskseam` instead of `python3 -m taskseam`.

Run the tests with `python3 -m unittest discover -s tests -v`.

## How TaskSeam is intended to work

1. **Capture with permission.** Collect activity from sources you explicitly enable.
2. **Connect related work.** Recognize when conversations and coding sessions belong to the same task, and show uncertainty when the match is unclear.
3. **Track current state.** Distinguish proposals from accepted decisions, preserve open questions, and record when a decision is superseded.
4. **Prepare a handoff.** Give the next tool a small update focused on what changed, with relevant artifacts and source evidence.
5. **Let you correct it.** Make wrong task matches and incorrect state easy to inspect and fix.

The intended design is local-first: work state stays on your machine by default, with visible capture controls and user control over what reaches another assistant.

## First milestone

The initial proof of concept will focus on **ChatGPT → Claude → Codex** for one project. Success means Codex receives the latest accepted decision, knows what it replaced, retains unresolved questions, and can show where each item came from. It should avoid including unrelated or private context.

This narrow handoff comes before support for more providers, sync, or team features.

## Why build in the open?

People should be able to inspect a tool that handles their conversations and work history. Open development also makes it possible to build adapters for different AI tools and evaluate handoff quality in the open.

TaskSeam is starting small. If this problem matches your workflow, follow the repository or open an issue with a concrete handoff that you wish worked better.
