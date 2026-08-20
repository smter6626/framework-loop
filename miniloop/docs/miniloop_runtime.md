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

### Locked Python Router v0 Decisions

以下内容已经由 Human Owner 在当前 Active Step 内确认，后续实现默认据此进行，除非出现新的 evidence 或 Human 明确修改。

#### 1. Single model, two isolated logical sessions

- Reviewer 与 Executor 使用同一个 Ollama model ID / 同一份本地 Qwen weights；
- Python 分别维护 Reviewer 与 Executor 的 conversation state；
- 两个 session 使用不同的 role / system instruction；
- 切换角色时切换的是输入 history / logical session，不是重新加载另一份模型权重；
- 当前 Miniloop 使用串行 inference，不要求 Reviewer 与 Executor 并行生成。

概念结构：

```text
reviewer_messages ----\
                       -> same local Qwen model
executor_messages ----/
```

#### 2. Verbatim peer-message routing

Reviewer / Executor 之间传递自然语言原文。Python 不对 payload 做 reasoning / instruction / evidence / verdict 等语义拆分。

Python 只负责它自身可以确定的 transport metadata，例如：

```text
sender
receiver
turn
run_id / session identity
payload = <raw LLM output>
```

发送方的完整 conversation history 不复制给接收方；只把本轮需要交给 peer 的原始输出作为 peer message 放入目标 session。

简化语义：

```text
LLM 理解 LLM。
Python 路由 LLM。
```

#### 3. Agent role instruction must state peer identity

Reviewer / Executor 的 agent / system instruction 应明确：

- 当前角色正在与另一个 LLM Agent 通信，而不是与 Human 对话；
- peer message 可能由 orchestrator 原样转发；
- 当前角色应自行理解自然语言中的 instruction、review reasoning、evidence locator、limitation 等语义；
- 不要求 peer 依赖固定 JSON / XML / marker 才能理解消息。

#### 4. Inference completion signal uses Ollama request lifecycle

Miniloop v0 不通过自然语言判断一个 Agent “是否说完”，也不需要通过 `ollama ps` 或每 10 秒轮询模型 busy 状态来判断。

采用 Ollama blocking chat request（例如 `stream = false`）作为 deterministic completion signal：

```text
Python calls Reviewer
    -> Ollama request remains in progress
    -> full response returns
    -> Reviewer turn is complete

Python routes raw output
    -> calls Executor
    -> full response returns
    -> Executor turn is complete
```

因此：

- request 未返回 = 当前 inference 尚未完成；
- request 正常返回 = 当前 inference 已完成，可以进入下一 deterministic routing action。

该信号只表示“本轮 inference 完成”，不表示语义上的 task ACCEPT / REJECT / completion。

#### 5. Persistent receiver control file

Miniloop v0 使用一个本地持久化 receiver control file 表示**下一自动控制权属于谁**。

当前允许的核心 receiver 值为：

```text
executor
human
```

语义：

```text
receiver = executor
-> Reviewer 允许自动循环继续
-> Reviewer raw output 路由给 Executor

receiver = human
-> Python 停止自动循环
-> 控制权交回 Human
```

Python 不通过读取 Reviewer 自然语言来猜测是否应继续或停机，而是读取这个 deterministic control state。

Python 应在：

- 程序启动时；
- 每次 Reviewer inference 完成后；

读取 receiver。

如果读取到 `human`，不得继续触发 Executor。

#### 6. Reviewer owns receiver transition authority

当前设计中，Reviewer 是 acceptance / orchestration authority，因此 receiver transition 默认由 Reviewer 决定。

Executor 不负责直接把 receiver 改为 `human` 或决定最终停机。Executor 遇到 blocker、limitation 或无法继续的问题时，应通过自然语言原文汇报给 Reviewer；Reviewer 再判断：

```text
继续自动执行 -> receiver = executor
需要 Human / 最终停止 -> receiver = human
```

实现上不应给 Reviewer 一个无限制的任意文件写入接口来修改 receiver；更稳妥的方向是提供窄 capability，例如：

```text
set_receiver("executor")
set_receiver("human")
```

由 Python 校验允许值并写入 receiver control file。

这属于 runtime-enforced control mechanism，不属于 prompt-only structured output parsing。

#### 7. `human` is a generic handoff / stop state

`receiver = human` 只回答：

> 下一控制权属于 Human，而不是 Executor。

它不要求 Python 理解“为什么”。

因此同一个控制状态可以覆盖：

- Reviewer 判断需要 Human 参与；
- 当前自动循环最终完成，需要把控制权交回 Human；
- 其他 Reviewer 判断不应继续自动触发 Executor 的情况。

具体原因仍应由 Runtime / Reviewer natural-language report 表达，而不是编码进 receiver 文件。

注意：Miniloop 当前仍不要求实现完整的 Human Decision Gate 恢复工作流；这里只锁定一个可用于停机 / handoff 的 deterministic primitive。

#### 8. Local repository operation is primary; GitHub remote is not required for loop routing

Miniloop 的 Reviewer / Executor 主要操作本机 clone / working tree。Agent 的 filesystem、git、test 等能力应面向本地 repository。

GitHub remote 不是 Reviewer–Executor transport layer；SSH 只在需要 `git pull` / `git push` 等远端同步时使用。

因此 Miniloop v0 不需要依赖 GitHub API 才能完成核心循环，也不要求自动 push 才能证明本地 Reviewer–Executor loop 成立。

具体允许哪些本地 file / shell / git tools 仍待敲定。

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
   - Python 不通过理解 Reviewer 自由文本决定是否继续调用 Executor；
   - Reviewer 可以通过受限 receiver control capability 将下一控制权设置为 `executor` 或 `human`。

### Permitted Changes

允许为完成当前 Active Step：

- 在 `miniloop/` 下创建或修改 orchestrator source code；
- 创建 Reviewer / Executor system instruction 或 agent configuration；
- 创建 deterministic transport envelope / routing logic；
- 创建 receiver control file 及其受限 setter；
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
- Ollama blocking request completion 驱动下一 inference 的实现位置或运行 evidence；
- receiver control file / setter 的实现位置及 allowed-value enforcement；
- `receiver = human` 时 Python 不继续触发 Executor 的测试或运行 evidence；
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

Python Router v0 的 session routing、verbatim peer-message transport、Ollama inference-completion signal、receiver-based handoff / stop mechanism 已形成当前设计决策。

仍需在当前 Active Step 内继续敲定的主要实现边界包括：

- Reviewer / Executor 实际拥有的本地 filesystem / shell / git / test tools；
- 各角色的 capability / permission surface；
- receiver control file 的具体路径与最小持久化格式；
- Runtime 最终 acceptance transition 的具体受限写入机制。

这些属于当前设计工作，不构成已确认 blocker。

---

## Explicitly Deferred for This Task

当前 Miniloop 不处理：

- conversation history 超过约 60K tokens 后的 context management；
- 完整 Human Decision Gate 的交互、决策输入和自动恢复协议；
- 无限 repair / clarification loop 的自动检测与终止。

`receiver = human` 作为 deterministic stop / handoff primitive 已纳入当前设计，但不等于本阶段必须完成完整 Human Gate workflow。

这些 deferred 问题不应阻塞当前 Active Step。

---

## State Transition

### Previous state

`ACTIVE — Step 1`，Agent-to-Agent semantic transport 已收敛为 deterministic envelope + opaque natural-language payload，但 inference completion 与 loop stop / Human handoff 的 control-plane 细节尚未确定。

### Evidence

Human Owner 在当前设计讨论中确认：

- Miniloop v0 使用同一模型、两个隔离 logical session；
- Reviewer / Executor 原始自然语言 output 由 Python 原样路由，Python 不做语义拆分；
- Ollama blocking request completion 作为单轮 inference 完成信号；
- 使用本地 persistent receiver control file 表示下一控制权；
- receiver 核心值为 `executor` / `human`；
- Reviewer 拥有 receiver transition authority；
- `receiver = human` 统一表示自动 loop 停止并把控制权交回 Human；
- 本地 repository / filesystem / git / tests 是 Miniloop 执行面，GitHub remote 不是 Agent transport layer。

### Current state

`ACTIVE — Step 1: Build and demonstrate the first end-to-end Miniloop`

Python Router v0 的核心路由与停机方向已基本锁定：

```text
same local Qwen weights
+
two isolated logical sessions
+
verbatim peer payload routing
+
blocking Ollama request completion
+
persistent receiver control file
```

### Meaning

Active Step 没有改变，也尚未产生 implementation acceptance evidence。本次 Runtime 更新用于持久化已经敲定的 Router v0 设计，避免后续 conversation reset 后重新推导或误用旧 structured-message 方案。

---

## Superseded / Invalidated Decisions

### Prompt-only structured Agent messages as required transport protocol

Status: `SUPERSEDED`

Previous assumption:

Reviewer / Executor 需要稳定生成结构化 instruction / report / verdict，再由 Python 解析完成消息路由。

Current decision:

Agent-to-Agent semantic payload 默认使用自然语言原文；Python 只负责 deterministic envelope 和 transport / control，不承担自由文本语义拆分。

### Polling Ollama process/load state as inference-completion signal

Status: `SUPERSEDED`

Previous considered direction:

Python 周期性检查类似 busy / idle 的“信号灯”，用轮询判断 Reviewer / Executor 是否完成一轮 inference。

Current decision:

Miniloop v0 使用 blocking Ollama chat request 的返回作为 deterministic completion signal；模型是否仍常驻内存与当前 inference 是否完成是不同状态，不通过模型 load state 判断。

---

## Next Direction

当前下一步不再重新讨论已锁定的 session / peer-message / completion / receiver 路由机制。

下一阶段设计讨论集中在 **local tool and capability surface**：

- Executor 为完成真实 bounded task 最少需要哪些本地工具；
- Reviewer 为独立检查 evidence 最少需要哪些本地工具；
- 哪些工具必须按角色隔离；
- 如何从程序级权限上阻止 Executor 修改 Static / Runtime 或进行越权操作。

这些边界敲定后，再进入 Codex implementation。
