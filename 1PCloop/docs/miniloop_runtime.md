# Miniloop Runtime

## 任务状态

`ACTIVE`

本 Runtime 记录当前权威执行状态。稳定目标、硬约束和最终验收标准见：

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

### Step 1 prerequisite — Verify dual-Codex CLI profiles

Status: `COMPLETED`

Result:

- 已按 Static 中记录的当前角色绑定完成两个独立 Codex profile 的串行与并发 CLI smoke test；
- 串行 smoke test：

```text
CODEX_HOME="$HOME/.codex-A" codex exec 'Reply with exactly: CHENG_EXEC_OK'
-> CHENG_EXEC_OK

CODEX_HOME="$HOME/.codex-B" codex exec 'Reply with exactly: DYM_EXEC_OK'
-> DYM_EXEC_OK
```

- 并发 smoke test：

```text
A exit=0
CHENG_PARALLEL_OK

B exit=0
DYM_PARALLEL_OK
```

Evidence locator:

- `f4bdfae40e8453036b500d6a6a0fccbbdde09ab3` — 记录已验证的双 Codex execution environment；
- `e08df1137b651ac38f16af0154220ca2b8471bc0` — 记录串行、并发 smoke test 及其输出。

Commit Notes:

- Step: `Step 1 prerequisite`
- Environment contract commit: `f4bdfae40e8453036b500d6a6a0fccbbdde09ab3`
- Runtime evidence-record commit: `e08df1137b651ac38f16af0154220ca2b8471bc0`

Meaning:

双 profile 身份选择和 CLI 调用前置条件已经完成；当前尚未完成的是 Reviewer→Executor→Reviewer 的自动文本路由。

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

### 2026-09-05 — Ollama completion-signal supersession

Status: `SUPERSEDED`

Step: `Step 1`

Decision:

不再轮询 Ollama process/load state 作为 inference-completion signal。当前 active inference substrate 是 Codex CLI；process/command completion 是直接的机械回合完成信号，语义上的 task completion 仍由 Reviewer 判断。

---

## 当前活跃步骤

### Step 1 — 构建在线的双 Codex 1PC Reviewer–Executor 循环

状态：`ACTIVE`

### 当前目标

在已验证的双 Codex 环境上实现最小的纯文本 Reviewer→Executor→Reviewer 自动循环，回合之间不需要 Human 复制粘贴。

当前角色绑定、`CODEX_HOME` 和调用方式以 Static 的 [Current Execution Environment](miniloop_static.md#current-execution-environment) 为准；通信、上下文和角色边界以 Static 的 [Hard Constraints](miniloop_static.md#hard-constraints) 为准。

### 本里程碑交付范围

1. 在 active `1PCloop/` implementation area 下创建最小 Python orchestrator；
2. 按当前角色绑定依次调用 Reviewer、Executor、Reviewer，并原样路由两次 peer natural-language payload；
3. 捕获三次调用的 final response 与 process result；
4. 保存可检查的确定性 run/turn log 或 transcript。

### 本里程碑验收

- 适用 Static [Acceptance Criteria A](miniloop_static.md#a-deterministic-dual-profile-invocation)、[B](miniloop_static.md#b-automatic-inter-agent-message-routing) 和 [H](miniloop_static.md#h-no-semantic-parser-dependency)；
- evidence 必须包含完整三回合 transcript，并能确认全部 Codex invocation 正常终止；
- Python 只维护确定性 transport/control metadata，不对 peer natural-language payload 做语义解析；
- 通过本里程碑只证明基础 live transport loop，不代表完成整个 `Step 1`。

### 本里程碑边界

Static 的 [Explicitly Out of Scope for Current 1PCloop](miniloop_static.md#explicitly-out-of-scope-for-current-1pcloop) 全部适用。此外，本里程碑暂不要求：

- session resume；
- code / artifact mutation；
- Runtime mutation；
- receiver tools；
- repair-limit logic；
- automatic infinite repair-loop detection；
- 完整 Human Decision Gate interaction/resume protocol；
- Linux VM/container sandbox enforcement；
- Web UI。

通过本里程碑后，按 Static 的 [Immediate Implementation Order](miniloop_static.md#immediate-implementation-order) 进入 disposable mutation 和 independent review；只有在新 evidence 存在后，才决定 historical Miniloop skeleton 中哪些 control-plane feature 值得复用。

### 当前运行观察

最近一次串行 `codex exec` smoke test 记录了以下 profile behavior：

```text
cheng / Executor:
  approval = never
  sandbox = workspace-write


dym / Reviewer:
  approval = never
  sandbox = read-only
```

该记录与预期角色分工一致，但不是角色身份或 architecture invariant；权威角色边界仍以 Static 为准。

---

## 待办任务

### P1 — 旧 Codex-A 状态中的过期 rollout path

状态：`NON-BLOCKING`

在首次 `.codex-A` 新建 `codex exec` smoke test 中观察到：

```text
state db returned stale rollout path for thread ...
/Users/smterpro/.codex/sessions/...
```

同一次 invocation 随后成功创建了新的 session，返回 `CHENG_EXEC_OK` 并正常完成。

当前判断：

- 可能是 profile migration / copied state 之前遗留的 absolute-path metadata；
- 不会阻塞新 session 的 `codex exec`；
- 目前不修复；
- 仅在需要旧 session resume / history enumeration，或该 warning 开始影响新的 invocation 时重新评估。

### P2 — 指向 `/Users/smterpro/.codex` 的 profile-internal references

状态：`DEFERRED / NON-BLOCKING`

部分 profile-local plugin / node-repl configuration 包含指向 `/Users/smterpro/.codex` 的 absolute reference；该路径当前解析为 `.codex-B`。

初始 1PCloop transport milestone 不要求 browser / plugin / node-repl subsystems。当前不要修改这些 configuration。

仅在所需 1PCloop capability 可被证明会在错误 profile 下启动 child subsystem 时重新评估。

---

## 当前阻塞项

未确认任何阻塞项。
