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

## Foundational Design Philosophy

当前设计先采用两个底层原则。它们不是对所有未来实现的永久技术限制，但 Miniloop 第一阶段默认围绕这两个原则设计。

### Principle A — 不指望 Python 理解自然语言

Python orchestrator 是 deterministic transport / control layer，不是 semantic reasoner。

因此不应要求 Python 从 Reviewer / Executor 的自由文本中推断：

- 哪一段是 reasoning；
- 哪一段是 instruction；
- 哪一段是 evidence；
- 哪一段代表 ACCEPT / REJECT；
- 某一句自然语言真正想表达什么控制意图。

Agent-to-agent 的自然语言内容默认视为 **opaque semantic payload**。Python 可以添加它自身确定的 transport metadata，例如 sender、receiver、turn、session，但不应尝试把 payload 的语义拆层。

简化原则：

```text
LLM 理解 LLM。
Python 路由 LLM。
```

### Principle B — 不指望 LLM 稳定输出结构化内容

不能把 Miniloop 的正确运行建立在以下假设上：

> 只要 prompt 写得足够严格，LLM 就会始终生成完全合法且语义稳定的 JSON / XML / marker / schema。

Prompt-only structured output 可能出现格式漂移、字段遗漏、额外解释、合法格式中的错误语义等问题。因此：

- 不应要求 Python 依赖自由生成的 JSON 来理解 Agent 输出；
- 不应通过字符串搜索，例如 `if "ACCEPT" in output`，决定 authoritative state transition；
- Agent-to-agent semantic communication 优先使用可被另一个 LLM 直接理解的自然语言原文；
- 若未来使用 tool calling、schema-constrained output 或其他 runtime-enforced structured control，它应属于独立的 control mechanism，而不是要求 Python 理解自由文本。

### Derived Communication Boundary

当前预测的最小通信边界为：

```text
Deterministic envelope owned by Python
+
Verbatim natural-language payload produced by LLM
```

例如 Python 可以确定：

```text
sender = reviewer
receiver = executor
turn = 4
payload = <reviewer raw output>
```

其中 `payload` 不进行语义拆分，直接交给目标 LLM 理解。

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

## Issue 2 — Reviewer 与 Executor 如何向对方发送消息

### Problem

Reviewer 需要向 Executor 下达执行或 repair 指令，Executor 需要向 Reviewer 汇报 implementation result、limitation 和 evidence locator。

如果要求 LLM 把这些内容稳定拆成 JSON 字段，再由 Python 解析并重新组装，会让 transport correctness 依赖 LLM 的格式化稳定性，同时要求一个没有自然语言理解能力的 Python 层承担语义拆分。

LLM 本身也没有后台线程，因此不能把“主动通信”理解成两个模型进程自行唤醒对方。

### Predicted Solution

由本地 Python orchestrator 实现 event loop 和 deterministic routing，但**不解析 Agent 自然语言输出的内部语义**。

基本机制：

```text
Reviewer inference
    -> reviewer raw natural-language output
    -> Python adds deterministic sender/receiver metadata
    -> payload forwarded verbatim
    -> Executor inference

Executor inference
    -> executor raw natural-language output
    -> Python adds deterministic sender/receiver metadata
    -> payload forwarded verbatim
    -> Reviewer inference
```

Reviewer / Executor 各自的高优先级 role instruction（例如 `agent.md` 进入 system instruction）应明确说明：

- 当前角色正在与另一个 LLM Agent 通信，而不是与 Human 对话；
- 对方具备自然语言理解能力；
- 当前输出可能被 orchestrator 原样转发给对方；
- 应直接向 peer agent 表达 execution instruction、review result、evidence locator 或 limitation，而不是依赖固定 JSON 模板。

Python 可以包装自己确定的信息，例如：

```text
[PEER MESSAGE FROM REVIEWER]

<verbatim reviewer output>
```

或者维护等价的内部 metadata，但不得要求 Python 判断 raw output 中哪一段属于 instruction / reasoning / evidence。

### Expected Verification

无需 Human 手工复制粘贴，即可完成至少一次：

```text
Reviewer -> Executor -> Reviewer
```

消息往返，并且 transport 不依赖 prompt-only JSON formatting 或 Python 对自由文本进行语义解析。

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

Executor 在自然语言报告中提供实际 evidence locator；Reviewer 通过自己的工具直接读取或重新检查：

- git diff / commit；
- test result；
- source code；
- generated artifact；
- 其他 acceptance criteria 所需 evidence。

Reviewer 独立形成 verdict，并独立判断 evidence 是否充分。

Python 不需要从 Executor 报告中抽取 `evidence` JSON 字段；Reviewer 本身负责理解报告并访问 evidence。

### Expected Verification

应能构造一个 Executor self-check 为 `PASS`、但实际不满足 acceptance criteria 的测试案例，并验证 Reviewer 可以独立 `REJECT`。

---

## Issue 5 — Reviewer verdict 如何变成 Runtime transition

### Problem

`ACCEPT` 不能只是聊天中的一句话；它需要在满足条件后改变 authoritative Runtime state。

同时，Python 不应通过解析自由文本、搜索 `ACCEPT` 关键字或依赖 prompt-only JSON verdict 来决定状态迁移。

### Predicted Solution

将 **semantic communication** 与 **control-plane transition** 分离。

Reviewer 可以用自然语言向 Executor / Human 表达 review reasoning；真正触发 Runtime transition 的 control signal 应通过 deterministic orchestration mechanism 实现。

可能方案包括 runtime-enforced tool call、显式 orchestrator API 或其他不要求 Python 理解自由文本的机制。具体方案暂不冻结，需由 Miniloop implementation evidence 决定。

无论采用何种方案，orchestrator 在允许 Runtime transition 前仍应验证：

- transition authority 来自 Reviewer role；
- 对应当前唯一 Active Step；
- acceptance 所需 evidence 可定位；
- transition 不违反 Static。

---

## Issue 6 — Executor 应该收到多少 Reviewer context

### Problem

如果把 Reviewer 的全部 conversation history、Static、Runtime 和所有历史 evidence 原样复制给 Executor，会破坏角色隔离并增加无关上下文。

### Predicted Solution

Reviewer 使用自己的上下文理解 Static / Runtime，并在发给 Executor 的自然语言 peer message 中表达当前 bounded instruction。

Orchestrator 负责把该 message 原样路由给 Executor，同时只附加执行当前 Active Step 所需的确定性 context / metadata；不复制 Reviewer 完整 conversation history，也不尝试把 Reviewer 输出自动拆成多个语义字段。

具体的 bounded context 构造方式可根据 prototype evidence 调整。

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

未来支持明确的 `HUMAN_DECISION_REQUIRED` control state，由 orchestrator 暂停自动循环、持久化当前状态，并在收到 Human input 后恢复。

具体 signaling mechanism 不应依赖 Python 解析 LLM 自由文本，后续根据实际 implementation 决定。

### Current Scope Note

**Miniloop 第一阶段暂不实现 Human Decision Gate。** Miniloop 的任务和测试必须避免需要 Human 才能消除的不确定性。

---

## Current Miniloop Priority

当前优先级不是一次性解决上述全部 Issue，而是先验证最小自动闭环是否成立。

Miniloop 至少需要覆盖：

1. Reviewer / Executor 上下文隔离与单模型权重复用；
2. Reviewer / Executor 之间基于原始自然语言 payload 的自动消息路由；
3. Reviewer 向 Executor 表达 bounded execution instruction；
4. Executor 执行任务、自检并报告 evidence locator；
5. Reviewer 直接检查 evidence 并形成 acceptance decision；
6. `REJECT` 后可以返回 Executor repair；
7. `ACCEPT` 后可以推进 Runtime；
8. Python 不需要理解 Agent 自然语言，Miniloop 也不依赖 LLM 稳定生成 prompt-only structured output。

暂不要求解决：

- 超长 conversation context / context reset；
- Human Decision Gate；
- 无限循环检测与自动终止策略；
- 多 Executor 并行；
- Web UI；
- production-grade orchestration。

本节同样只是当前预期。最终 Miniloop contract 以 `miniloop/docs/miniloop_static.md` 为准，执行状态以 `miniloop/docs/miniloop_runtime.md` 为准。
