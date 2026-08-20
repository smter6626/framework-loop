# Miniloop Runtime

## Task Status

`ACTIVE`

当前 task：实现并验证最小可运行的本地 Reviewer–Executor 自动闭环。

本 Runtime 记录当前 authoritative execution state。稳定目标、硬约束和最终验收标准见：

`miniloop/docs/miniloop_static.md`

---

## Completed

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

Meaning:

Miniloop 已具备初始稳定合同和当前执行状态，可以开始实现实际自动循环。

---

## Active Step

### Step 1 — Build and demonstrate the first end-to-end Miniloop

Status: `ACTIVE`

### Objective

实现一个最小但真实可运行的本地 orchestrator，使同一个本地 Qwen 模型可以在 Reviewer 与 Executor 两个隔离 session 之间串行切换，并完成一次由 repository-backed state 驱动的自动闭环。

目标链路：

```text
Reviewer reads Static + Runtime
    -> Reviewer compiles bounded execution instruction
    -> orchestrator routes instruction to Executor
    -> Executor performs a real bounded task
    -> Executor self-checks and reports evidence locator
    -> orchestrator routes report to Reviewer
    -> Reviewer directly checks evidence
    -> ACCEPT or REJECT
    -> if REJECT: repair instruction -> Executor -> Reviewer
    -> if ACCEPT: Runtime transition
```

### Required Functional Scope

本 Step 至少需要解决或验证：

1. **Context switching**
   - Reviewer / Executor 使用同一个本地 Qwen model ID；
   - 两个角色使用独立 system instruction；
   - 两个角色使用独立 conversation state；
   - 角色切换不通过加载两个相同模型副本实现。

2. **Message routing**
   - Reviewer -> Executor 的结构化 instruction；
   - Executor -> Reviewer 的结构化 implementation / evidence report；
   - orchestrator 自动触发目标角色下一次 inference；
   - 不需要 Human 手工复制粘贴。

3. **Bounded context construction**
   - Reviewer 可以读取 Static + Runtime；
   - Executor 只获得执行当前 Active Step 所需的信息，而不是 Reviewer 的完整 conversation history。

4. **Real Executor action**
   - Executor 必须执行至少一个真实、可验证的 bounded task；
   - 产生 repository diff、test artifact、log 或其他可直接检查的 evidence；
   - Executor 运行 self-check 并返回 evidence locator。

5. **Independent review**
   - Reviewer 不能仅依据 Executor 自述验收；
   - Reviewer 必须直接读取或重新检查实际 evidence；
   - Reviewer 输出结构化 `ACCEPT` 或 `REJECT`。

6. **Repair path**
   - 至少一个受控 scenario 必须走通 `REJECT -> REPAIR -> new evidence -> re-review`。

7. **Runtime progression**
   - 只有 Reviewer 在 evidence 足够时可以触发当前 Step 的最终 acceptance；
   - Executor 不能自行完成最终 acceptance；
   - acceptance transition 必须记录 evidence locator。

### Permitted Changes

允许为完成当前 Active Step：

- 在 `miniloop/` 下创建或修改 orchestrator source code；
- 创建 Reviewer / Executor system instruction 或配置；
- 创建 structured message schema；
- 创建本地 tool wrapper；
- 创建 bounded demo / fixture / test；
- 创建 run logs、test outputs 或其他 evidence artifact；
- 创建必要的 README / run instruction；
- 在 evidence 支持 Reviewer verdict 后更新本 Runtime。

### Restricted Changes

当前 Active Step 不授权 Executor：

- 修改 `miniloop/docs/miniloop_static.md`；
- 自行修改 `miniloop/docs/miniloop_runtime.md`；
- 重新定义 Miniloop Acceptance Criteria；
- 扩大 scope 到 Web UI、多 Executor、分布式部署或 production-grade agent platform；
- 为解决当前 Step 而引入必须依赖的云端 LLM API。

### Required Evidence

当前 Step 最终验收至少应能定位以下 evidence：

- orchestrator source code；
- Reviewer / Executor context separation 的实现位置；
- 使用同一 model ID 的实现或运行 evidence；
- structured inter-agent message routing 的实现位置；
- 一个完整 end-to-end run log；
- Executor 实际执行产生的 artifact / diff / test result；
- Reviewer 直接检查 evidence 的记录；
- 至少一个 `REJECT -> REPAIR -> re-review` 的运行记录；
- 最终 `ACCEPT` 所依据的 evidence locator；
- 可重复运行 demo 的命令或说明。

### Acceptance Criteria

当前 Step 的 acceptance 由 `miniloop_static.md` 中的全部 Miniloop Acceptance Criteria 决定。

Reviewer 不得因为局部功能已经跑通而提前将整个 Step 标记为 `COMPLETED`。

---

## Current Blockers

None confirmed.

当前尚未形成 implementation-level evidence，因此不得预先声称 context switching、message routing、tool permission、independent review 或 Runtime transition 已经实现。

---

## Explicitly Deferred for This Task

当前 Miniloop 不处理：

- conversation history 超过约 60K tokens 后的 context management；
- Human Decision Gate；
- 无限 repair / clarification loop 的自动检测与终止。

这些属于已知但 deferred 的问题，不应阻塞当前 Active Step。

---

## State Transition

### Previous state

Repository existed but contained no implementation or governance state.

### Evidence

Initial repository documents created:

- `issue_solution.md`
- `miniloop/docs/miniloop_static.md`
- `miniloop/docs/miniloop_runtime.md`

### Current state

`ACTIVE — Step 1: Build and demonstrate the first end-to-end Miniloop`

### Meaning

治理合同已经建立，但自动 Reviewer–Executor loop 尚未有 implementation evidence。下一步应围绕当前唯一 Active Step 开始实现，而不是继续扩展未来架构范围。

---

## Superseded / Invalidated Decisions

None.

---

## Next Direction

先实现能够真实运行的最小路径：

```text
one local Qwen model
+ two isolated logical sessions
+ local orchestrator
+ automatic message routing
+ one bounded Executor task
+ evidence-backed Reviewer verdict
```

具体代码结构、message schema、tool interface 和 demo fixture 尚未由 evidence 决定，当前保持开放，不在 Runtime 中提前冻结。
