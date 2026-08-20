# Miniloop Static

## Objective

在本地 Apple Silicon Mac 上实现并验证一个最小可运行的 Reviewer–Executor 自动闭环（Miniloop）。

该闭环应使用同一个本地 Qwen 模型实例，通过两个上下文隔离的逻辑 session 分别承担 Reviewer 与 Executor，并由本地 orchestrator 完成角色切换、结构化消息传递、工具调用和循环控制。

Miniloop 的目标不是实现完整生产级 Agent 平台，而是验证以下核心链路能够真实运行：

```text
Reviewer reads Static + Runtime
    -> Reviewer sends bounded instruction
    -> Executor performs work
    -> Executor self-checks and reports evidence locator
    -> Reviewer independently checks evidence
    -> ACCEPT or REJECT
    -> on REJECT: repair instruction -> Executor -> Reviewer
    -> on ACCEPT: Runtime transition
```

---

## Hard Constraints

### 1. Local execution

- LLM inference 应在当前本地机器上运行，不依赖云端 LLM API 才能完成 Miniloop。
- 当前机器为 Apple M4 Max、48 GB Unified Memory、macOS。
- 当前本地 runtime 为 Ollama。

### 2. Single model weights, isolated logical sessions

- Reviewer 与 Executor 应复用同一个本地 Qwen model instance / model weights。
- 不应通过同时常驻两个相同大型模型副本来实现角色隔离。
- Reviewer 与 Executor 必须使用不同的 system instruction 和不同的 conversation state。
- Reviewer 的完整 conversation history 不得自动进入 Executor context。
- Executor 的完整 conversation history 不得自动进入 Reviewer context。

### 3. Orchestrator-mediated communication

Reviewer 与 Executor 之间的通信必须经过本地 orchestrator 显式路由。

“主动发送消息”在本任务中的含义是：

```text
LLM inference
    -> structured message / tool call
    -> orchestrator
    -> target session inference
```

不得假设 LLM 自身拥有独立后台线程或能够在没有 orchestrator 触发的情况下自行唤醒另一角色。

### 4. Repository-backed authoritative state

- Static 与 Runtime 是 Miniloop 的权威治理状态。
- Conversation history 不是 authoritative project state。
- Git、source code、test output、run log 和 generated artifact 可以作为共享 evidence surface。
- Executor 的自然语言总结本身不能替代其所指向的实际 evidence。

### 5. Role separation

#### Reviewer

Reviewer 负责：

- 读取 Static 和 Runtime；
- 检查当前状态一致性；
- 编译当前唯一 Active Step；
- 向 Executor 发送 bounded instruction；
- 独立访问并检查实际 evidence；
- 形成 `ACCEPT` 或 `REJECT` verdict；
- `REJECT` 时产生 repair instruction；
- evidence 足够时推进 Runtime。

Reviewer 默认不承担当前 Active Step 的主要 implementation work。

#### Executor

Executor 负责：

- 接收当前 Active Step 所需的 bounded context；
- 执行被授权的 implementation / repository mutation；
- 调用允许的本地工具；
- 运行 self-check；
- 暴露实际 evidence locator；
- 向 Reviewer 汇报 implementation result、limitation 和 evidence locator。

Executor 不得：

- 修改本 Static；
- 自行推进 Runtime；
- 给自己的工作做最终 `ACCEPT`；
- 自行扩大 Active Step scope。

### 6. Single authoritative Active Step

正常执行时，Miniloop Runtime 最多只能有一个 authoritative Active Step。

Repair 仍属于当前 Active Step 的继续执行，不应在未验收当前 Step 时自行激活新的权威 Step。

### 7. Evidence-backed acceptance

Reviewer 最终 `ACCEPT` 必须基于 Reviewer 可以直接定位并检查的 evidence，而不是仅基于 Executor 的 `PASS` 或自然语言报告。

Runtime transition 必须能够指出支持该 transition 的 evidence locator。

---

## Stable Background

当前开发环境已经存在：

- Ollama；
- 一个可正常运行的 Qwen3.5 35B-class 本地模型；
- 约 64K 的当前默认 context configuration；
- M4 Max 48 GB Unified Memory 环境下本地推理已跑通。

项目计划使用一个约 27B 的 Qwen dense model 作为 Miniloop 的主要候选模型，但具体 model tag、quantization 和运行参数可在不违反 Hard Constraints 的前提下根据实际 evidence 调整。

现有 `structured-llm-execution-framework` 的 Static / Runtime、Reviewer / Executor、Git / Artifact Evidence 和 independent review 语义是本任务的治理基础。

---

## Explicitly Out of Scope for Miniloop

本阶段**明确不要求解决**以下问题：

1. Reviewer 或 Executor conversation history 超过约 60K tokens 后如何压缩、重建或迁移；
2. Human Decision Gate 的实现；
3. Reviewer / Executor 无限 repair、clarification 或其他死循环的自动检测与终止；
4. 多个并行 Executor；
5. 多模型异构 Reviewer / Executor；
6. Web UI；
7. 分布式部署；
8. production-grade queue、database、observability 或 fault recovery；
9. 长期 memory database 或大规模向量数据库。

测试任务必须选择不依赖以上能力即可完成的 bounded scenario。

---

## Authority and Approval

- Human Owner 可以修改本 Static 或改变 Miniloop 的稳定合同。
- Reviewer 可以解释 Static、形成 verdict，并在 evidence 支持时更新 Runtime。
- Executor 无权修改本 Static。
- Executor 默认无权修改 Runtime。
- 若实现过程中发现必须改变 Hard Constraints 或 Acceptance Criteria 才能继续，该变化不能由 Executor 静默完成。

---

## Acceptance Criteria

Miniloop 只有在以下条件都有可定位 evidence 支持时，才可判定完成。

### A. Same-model context switching

必须证明：

- Reviewer 与 Executor 使用同一个本地 Qwen model ID / model weights；
- 两个角色拥有独立 system instruction；
- 两个角色拥有独立 conversation state；
- 可以按 `Reviewer -> Executor -> Reviewer` 顺序切换；
- 角色切换不依赖加载两个相同大型模型副本。

### B. Automatic inter-agent message routing

必须证明：

- Reviewer 可以通过结构化消息向 Executor 下达 execution instruction；
- Executor 可以通过结构化消息向 Reviewer 汇报 implementation result / evidence；
- 消息通过 orchestrator 自动路由；
- 完整往返不依赖 Human 手工复制粘贴。

### C. Bounded Executor context

必须证明 Executor 接收的是当前 Active Step 所需的 bounded execution context，而不是 Reviewer 的完整内部 conversation history。

### D. Real execution and evidence exposure

Executor 必须完成至少一个真实、可验证的 bounded implementation task，并：

- 对 repository 或明确的测试 artifact 产生实际结果；
- 运行 self-check；
- 暴露 Reviewer 可以直接访问的 evidence locator。

纯语言角色扮演不满足本项。

### E. Independent Reviewer verification

Reviewer 必须直接检查 acceptance 所需的实际 evidence，并独立形成 verdict。

不得把以下流程视为充分验收：

```text
Executor: PASS
Reviewer: ACCEPT
```

除非 Reviewer 另外直接检查了支持该 claim 的 evidence。

### F. REJECT -> REPAIR path

必须至少通过一个受控测试证明：

```text
Reviewer REJECT
    -> bounded repair instruction
    -> Executor repair
    -> new evidence
    -> Reviewer re-review
```

可以正常运行。

### G. ACCEPT -> Runtime transition

必须证明：

- Reviewer 可以在 evidence 足够时形成 `ACCEPT`；
- `ACCEPT` 后 Runtime 才发生对应 authoritative transition；
- transition 记录 evidence locator；
- Executor 不能自行完成最终 acceptance 或 Runtime progression。

### H. Reproducible end-to-end run

Repository 中必须保留足够的 source、configuration、test / demo command 和 run evidence，使 Human Owner 能重新运行至少一个完整 Miniloop demonstration，并观察到：

```text
Reviewer
-> Executor
-> Reviewer
-> optional repair
-> Reviewer ACCEPT
-> Runtime progression
```

---

## Completion Definition

当上述 Acceptance Criteria 全部满足并由 Reviewer 基于实际 evidence 验收后，Miniloop task 才能从 `ACTIVE` 迁移为 `COMPLETED`。

在此之前，即使单独的模型调用、消息发送或 Executor implementation 已经成功，也不等于整个 Miniloop 已完成。
