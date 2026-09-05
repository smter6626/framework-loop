# Miniloop Runtime

## Task Status

`ACTIVE`

当前 task：实现并验证最小可运行的单机 Reviewer–Executor 自动闭环。

本 Runtime 记录当前 authoritative execution state。稳定目标、硬约束和最终验收标准见：

`1PCloop/docs/miniloop_static.md`

---

## Done

### Step 0 — Initialize governance documents

Status: `COMPLETED`

Result:

- 已创建 Miniloop Static；
- 已创建 Miniloop Runtime；
- 已创建根目录 `issue_solution.md`，用于保存非权威的预研 Issue / Solution working notes。

Evidence locator:

- `issue_solution.md`
- `miniloop/docs/miniloop_static.md`
- `miniloop/docs/miniloop_runtime.md`

Commit Notes:

- Step: `Step 0`
- Initial governance creation commits:
  - `d135a3f39ee5a99107eedf120dd72c8b9a8d236d` — initial `issue_solution.md`
  - `6a8f612b8c2418efca171d008d0bc9a4569ac42c` — initial `miniloop_static.md`
  - `a614bb0fbdd96055afcb90d8be25d0a369ef7987` — initial `miniloop_runtime.md`

Meaning:

Miniloop 已具备初始稳定合同和当前执行状态，可以开始实现实际自动循环。

### Runtime historical-record invariant

从当前设计锁定后，`Done` 中已经完成的历史记录视为不可追溯改写的 provenance：

- 已进入 `Done` 的完成记录不得直接删除或重写；
- `Commit Notes` 属于对应 Done record 的一部分，同样不可回写修改；
- 新增到 `Done` 的记录及其 `Commit Notes` 必须注明对应 Step 和 commit；
- 如果后续 evidence 证明历史记录、判断或 Commit Notes 存在错误，不回写旧记录，而是在 `Other Notes` 中追加 correction / invalidation / supersession 说明。

Python Runtime updater 只需要执行这种机械 invariant，不需要理解历史内容的自然语言语义。

---

## Other Notes

### 2026-09-05 — Repository path correction / supersession

Status: `ACTIVE CORRECTION`

Step: `Step 1`

Related commits:

- `ae49a2034dc992df0d7bf54b49305920d9ae8af6` — active `miniloop/` path reorganized as `1PCloop/`, and `issue_solution.md` moved under `1PCloop/docs/`;
- `9c6664b0f6b933207d16c36146c7510d84289366` — historical `codex/miniloop-skeleton-v0` implementation merged into `main` and preserved as a historical snapshot;
- `f4bdfae40e8453036b500d6a6a0fccbbdde09ab3` — active Static updated for the verified dual-Codex execution environment.

Correction:

The immutable Step 0 record above preserves the paths that were true when Step 0 was created. The current active locations are:

```text
1PCloop/docs/miniloop_static.md
1PCloop/docs/miniloop_runtime.md
1PCloop/docs/issue_solution.md
```

Historical implementation snapshot:

```text
1PCloop/history/miniloop-skeleton-v0/
```

The historical snapshot is read-only provenance and is not the active implementation path.

### 2026-09-05 — Execution-environment supersession

Status: `SUPERSEDES OLD ACTIVE-STEP ASSUMPTIONS`

Step: `Step 1`

Related commit:

- `f4bdfae40e8453036b500d6a6a0fccbbdde09ab3`

The previous Active Step assumed Ollama + one local Qwen model + two logical sessions + Linux sandbox as the immediate execution path. That is no longer the active implementation target.

The current verified execution environment is one M4 Max host with two independent ChatGPT/Codex identities:

```text
Reviewer = dym   = /Users/smterpro/.codex-B
Executor = cheng = /Users/smterpro/.codex-A
```

The active automation path is explicit per-process `CODEX_HOME` + `codex exec` / programmatic CLI invocation. Model names and reasoning effort are runtime configuration, not architecture invariants.

The old Ollama/Qwen implementation remains useful as historical implementation evidence only.

---

## Active Step

### Step 1 — Build the live dual-Codex 1PC Reviewer–Executor loop

Status: `ACTIVE`

### Current Objective

Implement the first real automatic loop on the verified dual-Codex environment.

Immediate target:

```text
dym / Reviewer
    -> bounded natural-language instruction
    -> deterministic Python transport
    -> cheng / Executor
    -> raw execution response
    -> deterministic Python transport
    -> dym / Reviewer
    -> review / repair / handoff decision
```

The immediate goal is not to complete all historical Miniloop acceptance criteria at once. The next milestone is a minimal text-only Reviewer→Executor→Reviewer loop with no Human copy/paste between turns.

### Verified Prerequisites

#### A. Independent profile homes — VERIFIED

```text
cheng -> /Users/smterpro/.codex-A

dym   -> /Users/smterpro/.codex-B
```

Verified properties:

- separate authentication state;
- separate session/history/profile-local state;
- both identities can access the same repository when normal filesystem permission allows it;
- `~/.codex` is only a convenience symlink and is not authoritative for account identity.

Current convenience symlink:

```text
/Users/smterpro/.codex -> /Users/smterpro/.codex-B
```

The orchestrator must therefore set `CODEX_HOME` explicitly for every role invocation.

#### B. Role binding — VERIFIED

Current default role binding:

```text
Reviewer = dym / .codex-B
Executor = cheng / .codex-A
```

Automatic role swapping is not part of the current scope. If account usage or another operational condition requires swapping roles, the Human Owner may do so manually.

#### C. CLI invocation — VERIFIED

Serial smoke tests succeeded from the repository working directory:

```text
CODEX_HOME="$HOME/.codex-A" codex exec 'Reply with exactly: CHENG_EXEC_OK'
-> CHENG_EXEC_OK

CODEX_HOME="$HOME/.codex-B" codex exec 'Reply with exactly: DYM_EXEC_OK'
-> DYM_EXEC_OK
```

Both created fresh Codex sessions and returned normal final responses.

#### D. Concurrent CLI processes — VERIFIED

Parallel smoke test succeeded:

```text
A exit=0
CHENG_PARALLEL_OK

B exit=0
DYM_PARALLEL_OK
```

Therefore two independent Codex CLI processes using `.codex-A` and `.codex-B` can coexist on the same physical Mac.

GUI simultaneous-launch limitations are not relevant to the automated 1PCloop control path.

#### E. Shared executable / isolated profiles — VERIFIED

Observed behavior:

- one profile triggered a Codex application/runtime update;
- the second profile subsequently launched without performing an independent update;
- profile authentication/history/config remain separate.

Interpretation for the active implementation:

```text
shared Codex executable/runtime installation
+
independent CODEX_HOME state
```

#### F. Current role capability behavior — OBSERVED

During the successful serial `codex exec` smoke tests:

```text
cheng / Executor:
  approval = never
  sandbox = workspace-write


dym / Reviewer:
  approval = never
  sandbox = read-only
```

This aligns with the intended role split, but the current 1PCloop does not depend on adding new filesystem-level isolation rules.

Role boundaries are initially enforced by role instructions and existing profile behavior. Stronger capability enforcement is deferred unless actual violations justify it.

#### G. Conversation continuity — NOT REQUIRED FOR INITIAL LOOP

The first active implementation may use fresh `codex exec` sessions for each turn.

Authoritative context remains external:

```text
Static
+ Runtime
+ repository / artifacts / evidence
+ current bounded peer instruction
```

The loop must not require a long-lived Codex conversation to preserve authoritative state.

### Locked Architecture for This Pass

#### Python / LLM semantic boundary

- Python performs deterministic transport/control.
- Reviewer / Executor peer payload is passed verbatim as natural language.
- Python may maintain role, sender, receiver, run id, turn id, process status, and other mechanical metadata.
- Python must not infer semantic acceptance by parsing arbitrary prose.
- Do not implement `if "ACCEPT" in output`-style authoritative transitions.
- Principle remains: `LLM understands LLM; Python routes LLM.`

#### Reviewer / Executor responsibility split

Reviewer:

- reads Static / Runtime / repository evidence;
- compiles bounded Executor instructions;
- independently evaluates implementation/evidence;
- owns review/repair/handoff semantics;
- normally does not perform primary implementation mutation.

Executor:

- performs bounded implementation work;
- modifies implementation/tests/artifacts as required by the task;
- runs execution-side checks;
- reports evidence;
- does not self-accept;
- does not modify Static / Runtime by default.

Current enforcement priority is prompt-level role instruction. Do not introduce extra profile/config friction unless actual evidence shows it is needed.

### Implementation Scope for the Next Pass

Implement only enough to prove the transport loop:

1. create a minimal Python orchestrator under the active `1PCloop/` implementation area;
2. explicitly invoke Reviewer with `CODEX_HOME=/Users/smterpro/.codex-B`;
3. capture Reviewer final response;
4. route that raw response to Executor with `CODEX_HOME=/Users/smterpro/.codex-A`;
5. capture Executor final response;
6. route Executor raw response back to Reviewer;
7. save deterministic run/turn logs or transcripts sufficient to inspect all three turns;
8. do not require GUI automation;
9. do not require session resume;
10. do not yet require code mutation, Runtime mutation, receiver tools, repair-limit logic, or Linux sandbox enforcement.

### Acceptance for This Immediate Milestone

The text-only routing milestone is satisfied only if evidence shows:

1. Reviewer is actually invoked through `.codex-B`;
2. Executor is actually invoked through `.codex-A`;
3. Reviewer output reaches Executor without Human copy/paste;
4. Executor output reaches Reviewer without Human copy/paste;
5. all Codex invocations terminate normally;
6. the complete three-turn transcript is inspectable;
7. Python does not semantically parse the peer natural-language payload.

Passing this milestone does not complete Step 1. It only proves the basic live transport loop.

---

## Pending Tasks

### P1 — Stale rollout path in legacy Codex-A state

Status: `NON-BLOCKING`

Observed during the first `.codex-A` fresh `codex exec` smoke test:

```text
state db returned stale rollout path for thread ...
/Users/smterpro/.codex/sessions/...
```

The same invocation then successfully created a fresh session, returned `CHENG_EXEC_OK`, and completed normally. Parallel A/B `codex exec` also completed with exit code 0.

Current interpretation:

- likely legacy absolute-path metadata from pre-profile migration/copied state;
- does not block fresh-session `codex exec`;
- do not repair now;
- revisit only if old-session resume/history enumeration becomes required or if the warning begins affecting fresh invocations.

### P2 — Profile-internal references to `/Users/smterpro/.codex`

Status: `DEFERRED / NON-BLOCKING`

Some profile-local plugin / node-repl configuration contains absolute references to `/Users/smterpro/.codex`, which currently resolves to `.codex-B`.

The initial 1PCloop transport milestone does not require browser/plugin/node-repl subsystems. Do not modify these configurations now.

Revisit only if a required 1PCloop capability demonstrably launches a child subsystem under the wrong profile.

---

## Current Blockers

None confirmed.

The following prerequisites are already verified and are not blockers:

- dual profile authentication;
- explicit `CODEX_HOME` account selection;
- serial `codex exec`;
- concurrent A/B `codex exec`;
- shared repository accessibility.

The current unimplemented item is the deterministic Reviewer→Executor→Reviewer transport itself.

---

## Explicitly Deferred for This Task

Do not implement during the immediate text-only routing milestone:

- automatic role swapping;
- GUI automation;
- new filesystem hard-isolation configuration;
- Linux VM/container sandbox enforcement;
- full Human Decision Gate interaction/resume protocol;
- automatic infinite repair-loop detection;
- production-grade crash recovery;
- multi-Executor or distributed deployment;
- Web UI;
- long-history context management;
- old Codex session migration/repair;
- browser/plugin/node-repl profile cleanup;
- performance comparison between different models/reasoning efforts.

These may be revisited after the live transport loop produces evidence that they are necessary.

---

## State Transition

### Previous state

`ACTIVE — Step 1: build the Miniloop framework skeleton using Ollama/Qwen and isolated logical sessions.`

That state produced useful historical implementation work, later preserved under:

```text
1PCloop/history/miniloop-skeleton-v0/
```

but it is no longer the active runtime target.

### Current state

`ACTIVE — Step 1: build the live single-machine dual-Codex Reviewer→Executor→Reviewer loop.`

### Transition Meaning

The project has moved from an Ollama/Qwen-centric prototype path to a verified dual-Codex Plus profile environment on one M4 Max.

The governance architecture remains the same at the level that matters:

- Static / Runtime are authoritative external state;
- Reviewer and Executor remain distinct roles;
- Python routes; LLMs interpret;
- Reviewer independently evaluates Executor work;
- Human Owner remains final authority.

Only the concrete inference/session substrate has changed.

The next implementation action is now fully operational rather than theoretical: automate the already-verified CLI identities into a three-turn Reviewer→Executor→Reviewer text loop.

---

## Superseded / Invalidated Decisions

### Prompt-only structured Agent messages as required transport protocol

Status: `SUPERSEDED`

Reviewer / Executor semantic payload uses natural-language text; Python does not own arbitrary free-text semantic parsing.

### Polling Ollama process/load state as inference-completion signal

Status: `SUPERSEDED`

The current active inference substrate is Codex CLI. Process/command completion is the immediate mechanical turn-completion signal; semantic task completion remains a Reviewer judgment.

### Same local model / same Qwen weights as a hard requirement

Status: `SUPERSEDED FOR ACTIVE 1PCLOOP`

Reviewer and Executor are bound to independent Codex identities. Their model selections may differ and may change over time. Model identity is not a role invariant.

### Linux sandbox as prerequisite for first live loop

Status: `DEFERRED`

The immediate goal is to prove the live Reviewer→Executor→Reviewer transport. Stronger sandbox/capability enforcement is added only when evidence requires it.

### GUI Codex application as automation surface

Status: `REJECTED / NOT REQUIRED`

The active control path uses explicit per-process `CODEX_HOME` and Codex CLI/programmatic invocation. GUI simultaneous-launch behavior does not constrain the automated loop.

---

## Next Steps

1. Implement the minimal text-only Python routing prototype.
2. Run one complete automated `dym Reviewer -> cheng Executor -> dym Reviewer` three-turn cycle.
3. Save exact prompts/responses/process results as evidence.
4. Verify that no Human copy/paste is required between turns.
5. Verify that Python transports peer text verbatim rather than interpreting it.
6. If the text-only milestone passes, move to a disposable code/artifact mutation task where Executor writes and Reviewer independently inspects.
7. Only after that evidence exists, decide which control-plane features from the historical Miniloop skeleton should be reused next.