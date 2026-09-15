# Framework Loop

English | [简体中文](README.zh-CN.md)

Framework Loop is a Reviewer–Executor automation system driven by repository-backed governance.
Its only active mainline is **1PCloop**: two isolated Codex identities on one Mac automatically
compile tasks, implement changes, perform independent review, route repairs, stop at Human Gates,
and advance auditable state.

> **Project status**
>
> - [`1PCloop/`](1PCloop/) is the only active implementation and maintenance mainline.
> - [`2PCloop/`](2PCloop/) is an inactive historical design archive. It is not being implemented
>   and has no active Runtime.

## What problem it solves

Long-running coding-agent work often mixes goals, progress, evidence, and approval authority into
conversation history. 1PCloop separates them into a stable contract, authoritative current state,
and real artifacts. A task can survive across sessions, and “implementation completed” is no
longer accepted as the same Agent's unsupported self-assessment.

```text
                         Human Owner
                              |
                     Static / Runtime
                              |
                              v
                    deterministic orchestrator
                              |
                 +------------+------------+
                 |                         |
                 v                         v
             Reviewer                  Executor
       independent inspection      implementation, tests,
           and verdict                  and commit
                 |                         |
                 +----------- Git / evidence
                              |
                  ACCEPT / REJECT / HUMAN_GATE
```

The system routes Reviewer → Executor → Reviewer automatically. On ACCEPT, the orchestrator may
advance Runtime only within authority granted in advance by the Human. On REJECT, a repair
instruction returns to the Executor. Subjective decisions, authority changes, and questions that
evidence cannot resolve stop automatically at a Human Gate with a visible terminal notice and
persisted state.

## Implemented foundations and extensible architecture

1PCloop already implements the single-Reviewer/single-Executor form of four core capabilities.
Future work extends the same governance foundation to local models, other Agents, visual tools,
and replaceable workers without redesigning the system from scratch.

```text
                  Human Owner
                       |
          Static / Runtime / Git / Evidence       implemented
                       |
                       v
        Authoritative Context Construction         implemented
                       |
                       v
            persistent/resumable Reviewer          implemented
                       |
                       v
              fresh bounded Executor               implemented
                       |
                 artifact / evidence
                       |
                       v
               Reviewer final gate                 implemented

      local / cloud / vision / GUI worker adapters extensible
```

### Cost–quality decoupling

The implemented foundation gives Reviewer and Executor separate profiles and sessions, allows
different model and reasoning configurations, assigns expensive implementation work to the
Executor, and lets only an evidence-backed Reviewer verdict advance Runtime. Execution cost and
final acceptance authority are therefore no longer tied to one Agent.

An extensible deployment can assign high-token, tool-heavy implementation to a local or cheaper
Executor while reserving task compilation, evidence inspection, and the final verdict for a
stronger cloud Reviewer. One example is a local Qwen 35B A3B MoE Q8 Executor paired with a
GPT-5.6 Sol Reviewer. Codex CLI already supports Ollama and LM Studio; 1PCloop still needs explicit
per-role provider configuration and end-to-end evidence for a mixed local/cloud deployment.

This setup does not claim that the local model's first attempt matches the stronger cloud model.
A weaker Executor may require more repairs and more time. The advantage is that only results that
pass the Reviewer evidence gate are accepted, making it possible to reduce cloud cost without
lowering the final acceptance threshold by the same amount.

The current Executor already uses a fresh ephemeral session and does not depend on its previous
conversation. With a local model, the CLI session can still exit after every turn while the
Ollama/LM Studio service and model weights remain resident. Existing runs also show high cache
hits on stable prompt prefixes. Prompt caching and a smaller context window are separate
optimizations: bounded instructions may permit less input or a smaller configured window when
quality remains comparable, but that must be validated on real workloads.

### Contract-backed context

This is already implemented, and it is more than external memory:

```text
Static       = long-lived objectives, constraints, and authority
Runtime      = current valid state, the one Active Step, and Human decisions
Git/Evidence = locatable facts that support state and verdicts
```

Agents, models, and sessions can be replaced without losing the task with a conversation. A new
Reviewer can reconstruct authoritative state from hash-bound governance. A fresh Executor can
start from a bounded instruction. A Human can revisit any commit, artifact, or hash. A superseded
conclusion does not regain authority merely because it still appears in history.

Future provider adapters only need to honor the same contract, identity, freshness, and evidence
boundary; they do not need to invent a new project-memory system for every Agent product.

### Capability reuse

1PCloop already reuses Codex CLI's shell, file, Git, and tool capabilities, then adds roles,
authority, evidence validation, Runtime transitions, and Human Gates around them. The
orchestrator does not reimplement coding tools.

The same pattern can extend to vision, browsers, MCP, plugins, and Computer Use. Codex CLI
supports local Ollama/LM Studio providers and image input; Codex/ChatGPT Computer Use can operate
GUIs through a desktop plugin and operating-system permissions. See the official
[Codex CLI command reference](https://learn.chatgpt.com/docs/developer-commands?surface=cli) and
[Computer Use documentation](https://learn.chatgpt.com/docs/computer-use). These visual and GUI
paths are not yet integrated into the current 1PCloop runner.

Moving from Codex today to Claude, another cloud Agent, or a local vision model tomorrow does not
require rewriting Static, Runtime, or the evidence contract. The provider-specific surface can
be limited to invocation, structured output, tool capabilities, timeout/cancellation, and
identity adapters. Governance migration can be inexpensive, though every new adapter still
requires compatibility and safety validation.

GUI operations can affect state outside the repository. Computer Use and similar capabilities
must remain subject to application permissions, action/screenshot evidence, approval for
sensitive operations, and Human Gates. A backend-provided tool cannot bypass 1PCloop's authority
boundary.

### Authoritative context-compiled workers

A narrow version is already implemented. A fresh Reviewer bootstrap receives complete,
hash-bound framework/workload Static and Runtime. Every Executor turn uses a fresh session and
receives only its role constraints, the current bounded instruction, target identity, and
necessary evidence context. It leaves Git/artifact evidence rather than conversation state for
the next turn.

```text
Tier 0  role, authority, Active Step, permitted and prohibited actions
Tier 1  complete bytes and hashes for task-relevant Static and Runtime
Tier 2  commit, artifact, test, and evidence manifests
Tier 3  repository files, historical evidence, and logs read on demand
```

The extensible form lets the Reviewer/orchestrator select a fresh worker by provider, model, and
tool capability: local coding, cloud coding, testing, vision, or GUI work. Each worker is born
with mechanically compiled, sufficient authoritative context. A REJECT can lead to a different
Executor without losing the contract, current state, or review history.

The current implementation has one fixed, sequential Executor. A future worker pool should first
retain the single-writer model: only one mutation worker may operate on one target at a time.
Parallel writers require additional worktree/branch isolation, commit attribution, merge rules,
and Runtime consistency; that capability cannot be inferred from the current system.

### Capability boundary

| Capability | Implemented | Extension or validation still required |
| --- | --- | --- |
| Role/model separation | Independent Reviewer/Executor profiles and sessions with different model configurations | Formal mixed local/cloud provider configuration and evidence |
| Contract-backed context | Static/Runtime/Git/evidence, hashes, freshness, and fresh reconstruction | A general provider-adapter contract |
| Fresh worker | Fresh bounded Executor with no dependency on old Executor history | Multiple replaceable workers selected by capability |
| Tool reuse | Codex CLI shell, files, Git, and current tool calls | Governed image, vision, browser, MCP, plugin, and Computer Use integration |
| Final authority | One Reviewer independently inspects evidence and forms the verdict | A replaceable Reviewer backend that retains one final authority |
| Mutation concurrency | Single writer | Parallel mutation has not been designed or validated |

For runnable behavior and commands, see [`1PCloop/README.md`](1PCloop/README.md). Items in the
extension column are not current deliverables, but they build on the implemented governance core.

## Core concepts

### Static: the stable contract

Static records what remains valid across sessions: the final objective, hard constraints,
authority boundaries, prohibited actions, and acceptance criteria. It does not track current
progress, and an ordinary Executor cannot modify it.

### Runtime: authoritative current state

Runtime records accepted results, the one Active Step, current blockers, pending items, Human
decisions, and evidence locators. It answers “what is valid now and what happens next” instead of
copying chat history or the Git log.

### Git, artifacts, and evidence

An Executor report is only an index. Before issuing a final verdict, the Reviewer must directly
inspect the commit, diff, test output, file hash, or other real evidence that supports the claim.

### External context

Long-lived context resides in Static, Runtime, Git, and artifacts rather than one Codex
conversation. The Reviewer receives complete hash-bound governance; the Executor receives only
the bounded instruction needed for the current step. Old conversations can be discarded while
the task remains reconstructable from repository state.

## Why use two roles

The Executor focuses on implementation; the Reviewer focuses on objectives, diffs, tests, and
evidence. They have separate identities, session histories, and role instructions, reducing the
influence of the implementation context on the review decision.

Operational guidance:

- Reviewer model capability and reasoning effort should normally be at least as strong as the
  Executor's.
- High-risk or complex work can use a stronger Reviewer.
- Reviewer and Executor may use the same or different model families; roles do not depend on a
  model name.
- A stronger Reviewer does not replace tests, hashes, Git identity, or Human Gates.

This design improves review independence and traceability. It does not guarantee that a model is
always correct, and it is not a model-voting system.

## Basic workflow

1. Create task-local Static and Runtime documents.
2. Prepare a clean target Git repository on the intended branch.
3. Run preflight to bind the target, governance, profiles, and evidence destination.
4. Start the loop; the orchestrator invokes Reviewer and Executor automatically.
5. Observe progress, a Human Gate, or the final result in the terminal.
6. Recover or audit the result through Runtime, checkpoint, tracked summary, and Git commits.

Installation, exact commands, file formats, recovery behavior, and safety boundaries are in
[`1PCloop/README.md`](1PCloop/README.md).

## Implemented capabilities

- Explicit role binding for two Codex identities
- Automatic Reviewer → Executor → Reviewer routing
- Complete governance injection and freshness checks
- Bounded Executor context
- Real repository mutation, tests, and ordinary Git commits
- Runtime-enforced structured verdicts
- Independent evidence validation
- Capability-gated Runtime transition after ACCEPT
- Bounded repair routing after REJECT
- Automatic stop and visible notice at Human Gates
- Checkpoints, crash/restart reconciliation, and idempotent recovery
- Git-ignored raw evidence, tracked summaries, and framework evidence commit/push
- Limited same-thread correction for Reviewer verdicts
- Independent display of logical outcome, Runtime transition, and evidence publication

## Current boundaries

1PCloop currently targets local use by one Human contributor, one active loop, and one target
writer. It is not an operating-system security sandbox and does not provide multiple writers,
parallel Executors, repository locking, or distributed consistency. The orchestrator never
pushes or merges the target repository. Unexplained state fails closed or enters a Human Gate
instead of being reset, force-pushed, or repaired by guesswork.

## Repository layout

```text
1PCloop/                 active single-machine implementation, docs, tests, and evidence
2PCloop/                 inactive two-machine design archive
```

`2PCloop` preserves an early two-machine design for possible future reference after explicit
Human reactivation. Current issues, commits, and feature requests should target `1PCloop`; the
archive does not define current behavior or direction.
