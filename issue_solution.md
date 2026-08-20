# Issue / Solution Working Notes

## Status and Purpose

本文档用于记录 `framework-loop` 开发过程中**当前已经识别出的工程 Issue，以及对应的预测性解决方案**。

这些内容属于预先考虑（preliminary design / working hypotheses），用于帮助拆解问题、降低实现前的不确定性，并不构成最终任务合同，也不应被死板地当成必须逐项完成的固定路线图。

后续实现过程中可以随时：

- 新增 Issue；
- 删除已证明不成立或不再相关的 Issue；
- 修改解决方案；
- 合并或拆分 Issue；
- 根据实际 evidence 改变优先级。

真正的任务目标、硬约束和验收标准应以对应 task 的 **Static** 为准；当前执行状态应以对应 task 的 **Runtime** 为准。本文件不是 Static，也不是 Runtime。

---

## Issue 1 — Reviewer / Executor 如何切换上下文而不加载双倍模型权重

### Problem

Reviewer 与 Executor 必须拥有隔离的 conversation state，但本机为 Apple M4 Max / 48 GB Unified Memory，不适合为两个角色各自常驻一份大型 Qwen 模型权重。

### Predicted Solution

只运行一个 Ollama model instance，并让 Reviewer / Executor 串行复用同一份模型权重。

Orchestrator 分别保存：

```text
reviewer_messages
executor_messages
```

每次 inference 根据当前角色选择对应 messages，并始终调用同一个 model ID。

因此切换的是**逻辑上下文（logical context）**，不是模型权重。

### Expected Verification

- Reviewer → Executor → Reviewer 可以连续切换；
- 两个角色使用不同 system prompt 和不同 conversation history；
- Reviewer history 不自动进入 Executor context，反之亦然；
- Ollama 不需要同时加载两份相同模型权重。

---

## Issue 2 — Reviewer 与 Executor 如何主动向对方发送消息

### Problem

需要支持：

```text
Reviewer -> Executor
EXECUTE
REPAIR
CLARIFICATION

Executor -> Reviewer
IMPLEMENTED
EVIDENCE_READY
BLOCKER
CLARIFICATION_REQUIRED
```

LLM 本身没有后台线程，因此不能把“主动通信”理解成两个模型进程自行唤醒对方。

### Predicted Solution

由本地 Python orchestrator 实现消息路由和 event loop。

基本机制：

```text
Current role inference
    -> structured message / tool call
    -> orchestrator parses message
    -> append bounded message to target role context
    -> trigger target role inference
```

角色之间只传递明确需要共享的信息，不复制发送方完整 conversation history。

### Expected Verification

无需 Human 手工复制粘贴，即可完成至少一次：

```text
Reviewer -> Executor -> Reviewer
```

消息往返。

---

## Issue 3 — 如何保证 Reviewer / Executor 的权限边界不是只靠 prompt

### Problem

仅在 system prompt 中写“Executor 不得修改 Static / Runtime”属于软约束，模型仍可能误操作。

### Predicted Solution

由 orchestrator 提供角色级 capability / tool permission。

初步方向：

| Capability | Reviewer | Executor |
| --- | --- | --- |
| Read Static | Yes | Yes / bounded |
| Read Runtime | Yes | Yes / bounded |
| Read repository evidence | Yes | Yes |
| Modify implementation files | Normally no | Yes, within Active Step |
| Run tests / commands | Yes | Yes |
| Modify Runtime | Yes, under transition rules | No |
| Modify Static | No by default | No |
| Final ACCEPT | Yes | No |

具体权限模型应根据 prototype 的实际需要调整。

---

## Issue 4 — Reviewer 如何独立验收，而不是相信 Executor 的自我汇报

### Problem

Executor 的 `PASS`、测试总结或自然语言汇报不能直接成为 acceptance evidence。

### Predicted Solution

Executor 汇报实际 evidence locator；Reviewer 通过自己的工具直接读取或重新检查：

- git diff / commit；
- test result；
- source code；
- generated artifact；
- 其他 acceptance criteria 所需 evidence。

Reviewer 独立形成 verdict，并独立判断 evidence 是否充分。

### Expected Verification

应能构造一个 Executor self-check 为 `PASS`、但实际不满足 acceptance criteria 的测试案例，并验证 Reviewer 可以独立 `REJECT`。

---

## Issue 5 — Reviewer verdict 如何变成 Runtime transition

### Problem

`ACCEPT` 不能只是聊天中的一句话；它需要在满足条件后改变 authoritative Runtime state。

### Predicted Solution

Reviewer 产生结构化 verdict，例如：

```text
ACCEPT
REJECT
```

orchestrator 在允许 Runtime transition 前验证：

- verdict 来自 Reviewer；
- 对应当前唯一 Active Step；
- acceptance 所需 evidence 可定位；
- transition 不违反 Static。

满足条件后才更新 Runtime。

---

## Issue 6 — Executor 应该收到多少 Reviewer context

### Problem

如果把 Reviewer 的全部 conversation history、Static、Runtime 和所有历史 evidence 原样复制给 Executor，会破坏角色隔离并增加无关上下文。

### Predicted Solution

Reviewer / orchestrator 从 authoritative state 编译一个 bounded execution package，例如：

```text
Active Step
Relevant Static constraints
Permitted mutation surface
Required evidence
Acceptance criteria
Reviewer instruction
```

Executor 只获得执行当前 Active Step 所需的信息，加上自己的必要 recent history。

---

## Issue 7 — 长时间运行后 conversation context 如何处理

### Problem

如果 Reviewer / Executor history 持续增长，系统可能重新退化为 conversation-backed state，并最终触及上下文窗口限制。

### Predicted Solution

长期 authoritative state 保存在 Static、Runtime、Git、Artifacts 和 Evidence 中；conversation history 仅作为短期工作缓存，需要时可以丢弃并从 repository-backed state 重建。

### Current Scope Note

**Miniloop 第一阶段暂不解决此 Issue。** 当前 prototype 可以假设 Reviewer / Executor context 不会超过约 60K tokens。

---

## Issue 8 — 如何避免 Reviewer / Executor 无限 repair 或 clarification 循环

### Problem

自动循环可能出现重复 `REPAIR -> IMPLEMENTED -> REJECT`，或双方反复要求 clarification。

### Predicted Solution

未来可由 orchestrator 保存 repair count、重复 blocker fingerprint、message count 等，并在超过阈值时停止自动推进。

### Current Scope Note

**Miniloop 第一阶段暂不解决此 Issue。** 当前测试任务应选择可以有限步完成的 bounded task。

---

## Issue 9 — Human Decision Gate 如何接入自动循环

### Problem

真实工作流中存在只能由 Human Owner 决定的主观、敏感、高风险或合同修改问题。

### Predicted Solution

未来支持结构化 `HUMAN_DECISION_REQUIRED` 状态，由 orchestrator 暂停自动循环、持久化当前状态，并在收到 Human input 后恢复。

### Current Scope Note

**Miniloop 第一阶段暂不实现 Human Decision Gate。** Miniloop 的任务和测试必须避免需要 Human 才能消除的不确定性。

---

## Current Miniloop Priority

当前优先级不是一次性解决上述全部 Issue，而是先验证最小自动闭环是否成立。

Miniloop 至少需要覆盖：

1. Reviewer / Executor 上下文隔离与单模型权重复用；
2. Reviewer / Executor 之间的自动消息路由；
3. Reviewer 编译并发送 bounded execution instruction；
4. Executor 执行任务、自检并报告 evidence locator；
5. Reviewer 直接检查 evidence 并形成 `ACCEPT` 或 `REJECT`；
6. `REJECT` 后可以返回 Executor repair；
7. `ACCEPT` 后可以推进 Runtime。

暂不要求解决：

- 超长 conversation context / context reset；
- Human Decision Gate；
- 无限循环检测与自动终止策略；
- 多 Executor 并行；
- Web UI；
- production-grade orchestration。

本节同样只是当前预期。最终 Miniloop contract 以 `miniloop/docs/miniloop_static.md` 为准，执行状态以 `miniloop/docs/miniloop_runtime.md` 为准。
