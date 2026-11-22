# TaskSeam: next steps from ecosystem research

Reviewed October 20, 2026. Recommendations are proposals, not accepted product decisions. This review does not independently reproduce competitors' benchmarks or establish customer demand.

## Recommendation

Prioritize reliable continuation across fresh sessions, then prove its value with reproducible evaluations. TaskSeam's strongest product hypothesis is a small, inspectable record of accepted decisions, active constraints, unresolved questions, and what changed between independent tools.

“Agents have memory” is already a crowded category. Local storage, MCP support, and multiple client integrations alone are insufficient differentiation. The opportunity is whether users can trust the state carried across a switch, correct it easily, and spend less time repeating themselves.

## External signals and practical responses

| Signal and primary evidence | Implication | Recommended response |
|---|---|---|
| GitHub describes repository-scoped memory shared across coding agent, CLI, and review, with citation verification. [GitHub engineering, January 15, 2026](https://github.blog/ai-and-ml/github-copilot/building-an-agentic-memory-system-for-github-copilot/) | Built-in memory is a serious alternative. Provenance also exists elsewhere. | Demonstrate accepted-state correctness across independent hosts; add artifact freshness checks rather than claiming provenance alone is unique. |
| Anthropic describes continuity failures between context windows and uses progress artifacts and incremental verification. [Long-running harnesses, November 26, 2025](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents) | A tool identity is not a session identity. Delivery yesterday does not imply knowledge in today's chat. | Recover current state on a fresh chat, retain deltas for continuation, and test context loss explicitly. |
| Anthropic treats context as finite; Agent Skills specifies progressive loading. [Context engineering](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents), [Skills specification](https://agentskills.io/specification) | History injection is costly, but blindly shrinking state can hide constraints. | Keep concise state and on-demand evidence; introduce budgeted pagination with explicit omissions and delivery accounting. |
| Agent HQ describes coordination across multiple agent providers through a common development platform. [GitHub announcement](https://github.blog/news-insights/company-news/welcome-home-agents/) | Switching may increasingly occur within platforms as well as between them. | Integrate with existing workflows; test independent-host handoffs as a distinct use case. This announcement establishes direction, not current availability of every announced integration. |
| Letta provides persistent, shared, optionally read-only memory blocks and documents concurrent overwrite behavior. [Letta memory blocks](https://docs.letta.com/v1-sdk/memory/memory-blocks) | Structured state and cross-agent sharing are established capabilities. | Evaluate explicit supersession, correction history, and recipient state. Address concurrent writes before team sync. |
| Mem0 documents graph-based entity and relationship retrieval. [Mem0 graph memory](https://docs.mem0.ai/platform/features/graph-memory) | Retrieval can supply useful evidence, but relevance is not user acceptance. | Consider memory adapters as evidence inputs; require review before promoting retrieved claims into accepted state. |
| Agentmemory advertises local memory, MCP integrations, and reproducible retrieval evaluations. [Project repository](https://github.com/rohitg00/agentmemory) | Open-source alternatives overlap with the local, multi-tool positioning. | Compare identical continuation scenarios. Its author-reported results cannot establish a TaskSeam performance advantage. |
| MCP's Tasks extension describes durable execution and deferred result retrieval. [Draft specification](https://tasks.extensions.modelcontextprotocol.io/specification/draft/tasks) | Protocol execution tasks and TaskSeam's accepted work state solve different problems. | Keep ordinary tools for local reads/writes. Consider asynchronous support only for long-running imports; do not conflate task identifiers or imply extension support. |

## Repository findings

The store implements explicit supersession, question resolution, source-event lookup, checkpoints, per-target deltas, and a version-one migration test. MCP exposes continuation and writes. Browser ingestion is a reviewed packet workflow, not reliable arbitrary conversation reconstruction.

Documentation needed narrower claims:

- The roadmap left MCP delivery unchecked although it exists.
- Migration exists, but broad legacy-version and corrupted-database coverage remains.
- The article called history append-only, although `set_supersession` updates an existing relationship.
- Approval is host behavior and agent guidance; MCP annotations do not independently enforce acceptance.
- Source and evidence are recorded assertions, not authenticated proof of human acceptance.

The checkout has a demo database but no active workspace configuration. The connected tool could not supply active task state; demo content was not treated as accepted project guidance.

## Implemented improvement

Previously, a new chat using an already-used target could receive an empty delta and no current state. Optional `full=true` in MCP continuation and `handoff --full` in the CLI now return a `current` array alongside the normal delta.

Use full recovery in a fresh chat or after losing prior context. Within an ongoing session, leave it off. `changed` still describes changes since the previous delivery; it can be false while `current` contains state. Recovery excludes superseded decisions and resolved questions, preserves source references, and leaves other targets' positions alone.

This is explicit recovery, not automatic session detection or acknowledged delivery. The cursor still advances before the caller confirms receipt. A host that never requests full recovery can still begin with insufficient context.

## Proposed sequence and acceptance gates

### 1. Continuation reliability

Release recovery after normal review. Next, design preview/acknowledgment so a dropped response does not consume unseen changes. An acknowledgment must identify the exact delivered snapshot and must not move a newer cursor backward.

Acceptance gate: restart, retry, lost response, out-of-order acknowledgment, two recipients, and an empty task have defined results. Preserve older clients' default behavior.

Improve workspace diagnostics too: distinguish an uninitialized repository from a host launched in the wrong directory. Offer explicit task selection rather than guessing from similar conversation text.

### 2. Reproducible continuation evaluations

Publish synthetic scenarios with explicit gold state:

1. Replace a decision twice while preserving provenance.
2. Resolve one question while another remains open.
3. Resume two recipients from different checkpoints.
4. Start a fresh chat with an unchanged recipient cursor.
5. Include an unrelated task with matching vocabulary.
6. Include malicious instructions in source evidence.
7. Correct an incorrectly linked supersession.
8. Interrupt delivery and retry.

Separate deterministic store correctness from model behavior. Compare full transcript, maintained Markdown state, latest-session summary, shared-memory retrieval, and TaskSeam with identical inputs and model settings. Maintained Markdown matters: it is a cheap, credible alternative.

Report current-decision precision/recall, unresolved-question recall, stale-item inclusion, provenance correctness, cross-task leakage, output tokens using a named tokenizer, latency, and user corrections. Repeat model runs and disclose failures. The regression tests added here are not a model benchmark and do not prove token savings.

### 3. Inspectable, correctable state

Add deterministic JSON/Markdown exports with a schema version and source references. Distinguish current-state exports from full history; omit raw evidence by default when sharing. Specify deletion separately from supersession.

Record lineage corrections as events before promising immutable history. Add expected-version checks or serialization for competing writes. Recheck applicability when branch/worktree or referenced artifacts change; do not automatically expire accepted decisions merely because they are old.

Acceptance gate: identical state produces identical exports, corrections remain explainable, and two writers cannot silently replace the same current item.

### 4. Bounded delivery and integrations

Define a byte/item budget before claiming a universal token budget. Return omitted counts and a continuation handle; never advance a recipient past omitted items. Preserve removal information so recipients can discard stale state.

Prioritize adapters from observed demand. Test two independent coding hosts first. Browser capture should retain review and correction. Team/cloud sync should wait for permission, identity, conflict, and deletion semantics.

## Validate the product before expanding scope

Recruit a small opt-in pilot of developers already switching between at least two agents. Observe several switches per developer, including fresh chats and changed decisions. Measure time to resume, repeated explanation, incorrect carried state, correction effort, and voluntary reuse.

Proceed when developers repeatedly choose TaskSeam over maintained notes and resume correctly. If they rarely switch, or maintaining accepted state costs more effort than it saves, revise the hypothesis before adding connectors.

Defer autonomous extraction, vector-search infrastructure, hosted accounts, and a general orchestrator until evidence supports them. Each would substantially expand the current small local product.

## Launch implications

Keep the article's publication-after-review boundary. Modern memory systems can update state, share structured blocks, and validate evidence. Present TaskSeam's combination and workflow as its focus without claiming other systems cannot represent authority.

The strongest next launch asset would be a reproducible recording: accept a decision in one host, replace it in another, open a fresh chat in the first, and recover correct current state with evidence. Pair it with measured limitations and a reproducible evaluation report.
