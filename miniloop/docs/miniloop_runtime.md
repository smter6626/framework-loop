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
    -> orchestrator routes Reviewer output to Executor
    -> Executor performs a real bounded task
    -> Executor self-checks and reports evidence locator
    -> orchestrator routes Executor output to Reviewer
    -> Reviewer directly checks evidence
    -> ACCEPT or REJECT
    -> if REJECT: repair instruction -> Executor -> Reviewer
    -> if ACCEPT: Runtime transition
```

### Current Design Direction

Human Owner 已确认以下两项底层原则，并已同步进入 Static：

1. **不指望 Python 理解自然语言。** Python orchestrator 负责 deterministic transport / control，不负责从 Agent 自由文本中拆解 reasoning、instruction、evidence、verdict 等语义层。
2. **不指望 LLM 稳定输出 prompt-only 结构化内容。** Miniloop 不依赖 LLM 稳定生成 JSON / XML / marker 后再由 Python 解析才能运行。

当前 Agent-to-Agent 通信方向为：

```text
Deterministic envelope owned by Python
+
Verbatim natural-language payload produced by LLM
```

Reviewer / Executor 的 role instruction 应明确：当前角色正在与另一个 LLM Agent 通信，而不是与 Human 对话。目标 LLM 负责理解 peer message 的自然语言语义。

Python 可以确定并保存 sender、receiver、turn、session 等 transport metadata，但不得据此之外继续解析 LLM payload 的内部语义。

### Required Functional Scope

本 Step 至少需要解决或验证：

1. **Context switching**
   - Reviewer / Executor 使用同一个本地 Qwen model ID；
   - 两个角色使用独立 system instruction；
   - 两个角色使用独立 conversation state；
   - 角色切换不通过加载两个相同模型副本实现。

2. **Message routing**
   - Reviewer 的自然语言输出可以由 orchestrator 原样路由给 Executor；
   - Executor 的自然语言输出可以由 orchestrator 原样路由给 Reviewer；
   - Python 只添加自身确定的 deterministic transport metadata；
   - Python 不解析 Agent payload 的 reasoning / instruction / evidence / verdict 语义；
   - Agent-to-Agent transport 不依赖 prompt-only JSON parsing；
   - orchestrator 自动触发目标角色下一次 inference；
   - 不需要 Human 手工复制粘贴。

3. **Bounded context construction**
   - Reviewer 可以读取 Static + Runtime；
   - Executor 只获得执行当前 Active Step 所需的信息，而不是 Reviewer 的完整 conversation history；
   - peer message 可以原样进入目标 Agent context，但发送方完整 history 不随消息一起复制。

4. **Real Executor action**
   - Executor 必须执行至少一个真实、可验证的 bounded task；
   - 产生 repository diff、test artifact、log 或其他可直接检查的 evidence；
   - Executor 运行 self-check 并向 Reviewer说明可定位的 evidence。

5. **Independent review**
   - Reviewer 不能仅依据 Executor 自述验收；
   - Reviewer 必须直接读取或重新检查实际 evidence；
   - Reviewer 必须形成 `ACCEPT` 或 `REJECT` verdict；
   - Python 不得通过解析 Reviewer 自由文本中的 `ACCEPT` / `REJECT` 字样来推断 authoritative control state。

6. **Repair path**
   - 至少一个受控 scenario 必须走通 `REJECT -> REPAIR -> new evidence -> re-review`。

7. **Runtime progression**
   - 只有 Reviewer 在 evidence 足够时可以触发当前 Step 的最终 acceptance；
   - Executor 不能自行完成最终 acceptance；
   - acceptance transition 必须记录 evidence locator；
   - authoritative transition 所需的 control-plane mechanism 尚未在本 Runtime 中提前冻结，但不得依赖 Python 理解 Reviewer 自由文本。

### Permitted Changes

允许为完成当前 Active Step：

- 在 `miniloop/` 下创建或修改 orchestrator source code；
- 创建 Reviewer / Executor system instruction 或 agent configuration；
- 创建 deterministic transport envelope / routing logic；
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
- deterministic envelope + verbatim natural-language payload routing 的实现位置；
- 能证明 Python 未依赖自由文本语义拆分进行 Agent-to-Agent transport 的实现或测试；
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

Python routing 的精确字段、session storage 方式、下一角色触发方式和 control-plane mechanism 仍需要在当前 Active Step 内敲定后再实现；这些属于当前设计工作，不构成已确认 blocker。

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

`ACTIVE — Step 1`，但早期 Runtime 仍包含“structured instruction / structured report / structured verdict / structured message schema”等实现预设。

### Evidence

Human Owner 明确确认两项设计原则，并已同步到：

- `issue_solution.md`
- `miniloop/docs/miniloop_static.md`

原则为：

- 不指望 Python 理解自然语言；
- 不指望 LLM 稳定输出 prompt-only 结构化内容。

### Current state

`ACTIVE — Step 1: Build and demonstrate the first end-to-end Miniloop`

当前实现方向已收敛为：

```text
Python deterministic transport/control metadata
+
verbatim opaque natural-language Agent payload
```

### Meaning

Active Step 没有改变，也尚未产生实现 acceptance evidence；本次 Runtime 更新仅消除旧 structured-message 假设与当前 Static 之间的冲突，并记录当前已经确认的 implementation direction。

---

## Superseded / Invalidated Decisions

### Prompt-only structured Agent messages as required transport protocol

Status: `SUPERSEDED`

Previous assumption:

Reviewer / Executor 需要稳定生成结构化 instruction / report / verdict，再由 Python 解析完成消息路由。

Current decision:

Agent-to-Agent semantic payload 默认使用自然语言原文；Python 只负责 deterministic envelope 和 transport / control，不承担自由文本语义拆分。

---

## Next Direction

当前下一步是敲定 **Python Router v0** 的精确职责边界，包括：

- Python 必须保存哪些 deterministic state；
- Reviewer / Executor session 如何分别保存；
- peer payload 如何原样封装和投递；
- 一次 inference 完成后如何确定并触发下一个 role；
- 哪些内容明确禁止由 Python 通过自由文本语义解析获得。

敲定后再进入 Codex implementation。
