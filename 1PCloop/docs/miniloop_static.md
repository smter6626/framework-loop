# 1PCloop Static

## 目标

在一台 Apple Silicon Mac 上实现并验证一个最小可运行的 Reviewer–Executor 自动闭环（1PCloop）。

本项目当前的稳定产出和目标是：

- 可运行、可审核的 engineering artifact；
- 可日常运行、可诊断、可恢复、状态可见且可维护的本地 Reviewer–Executor engineering
  foundation；
- 清晰的 operator 入口、Human Gate 和本地 observability；
- 可用于未来受控实验的 optional experimental harness；
- 对真实实现、失败模式、修复过程、角色隔离、context management、evidence handling 与 Human Gate 的可追溯记录。

### 2026-09-12 Human Owner current supersession

Human Owner 于 `2026-09-12` 明确把 1PCloop 从 paper/research-driven 路线转向 engineering
foundation，并暂停 P7。原因是近期 research/prior-work 审查表明，继续以 Framework paper
novelty 或扩大实验为目标不符合当前资源优先级。该判断是 Owner 的当前方向和资源决定，不是
“已穷尽所有文献”或关于相关研究空间的普遍科学结论。

本次授权 supersede：

- Framework-as-paper 或 paper-driven experiment 作为当前工程路线；
- P7 controlled fault injection 作为当前 foundation 完成前置条件；
- `researchPlan.md` 作为当前工程执行依据。

当前保持不变：双 profile role identity、orchestrator-mediated routing、repository-backed
authoritative state、Reviewer/Executor separation、deterministic context reconstruction、
runtime-enforced control output、evidence-backed acceptance、checkpoint/restart、workload
Runtime transition、local raw evidence 与 tracked summary、fail-closed 和
single-writer/no-concurrency boundary。P4–P6 的 accepted evidence 继续有效。

2026-09-09 完成的三轮 adversarial novelty audit 已表明，旧 `researchPlan.md` 中的 authoritative transition、decision-preserving memory、evidence sufficiency 等宽研究方向不再具备可支持的宽泛 novelty。因此：

- `Framework-as-paper` 暂停；
- Framework 保留为 methodology artifact；
- 1PCloop 保留为 engineering artifact / experimental harness；
- 工程验收、regression 通过或 P6 / P7 closure 不得自动升级为 scientific finding 或 paper novelty；
- 任何未来重新激活的 research track 或 cheap pilot 必须先由 Human Owner 明确开启，并在
  `researchPlan.md` 中通过相应研究 gate；foundation_v1 工程执行不受这些 research gate
  约束。

运行过程中仍可记录 research-question signal，但记录不表示 hypothesis 成立、literature novelty 已确认、已形成可发表 contribution 或已授权开展额外实验。已被后续 prior-work audit 覆盖的旧 RQ 只能作为历史记录、engineering requirement 或新 exact RQ 下的局部变量。

当前 active implementation 不再以“单个本地 Ollama/Qwen 模型实例 + 两个逻辑 session”为运行前提，而是使用同一台 M4 Max 上已经独立配置好的两个 ChatGPT/Codex identity：

```text
Reviewer = dym   = CODEX_HOME=/Users/smterpro/.codex-B
Executor = cheng = CODEX_HOME=/Users/smterpro/.codex-A
```

两个角色由 deterministic local orchestrator 显式调用、路由和切换。权威项目状态仍由 Static、Runtime、repository、实际 artifact 与 evidence 承担，而不是依赖任一 Codex conversation history。

目标链路为：

```text
Reviewer reads Static + Runtime + repository evidence
    -> Reviewer sends one bounded instruction
    -> orchestrator invokes Executor
    -> Executor performs authorized work
    -> Executor self-checks and reports evidence locator
    -> orchestrator returns the raw receipt to Reviewer
    -> Reviewer independently checks actual evidence
    -> ACCEPT or REJECT
    -> on REJECT: repair instruction -> Executor -> Reviewer
    -> on ACCEPT: Runtime transition
```

1PCloop 的目标不是实现完整生产级 Agent 平台，而是把当前已被人工使用验证的 Reviewer–Executor 工作流机械化，并证明它可以在无人手工复制粘贴 peer message 的情况下真实闭环运行。

---

## Current Execution Environment

### Physical host

当前 active host：

- Apple M4 Max；
- 48 GB Unified Memory；
- macOS；
- Reviewer 与 Executor 位于同一台物理机器。

因此本项目仍属于 **1PCloop**。角色隔离来自独立 Codex identity/profile state，而不是来自两台物理机器。

### Codex identity binding

当前存在两个独立 Codex profile：

```text
cheng
  CODEX_HOME=/Users/smterpro/.codex-A

dym
  CODEX_HOME=/Users/smterpro/.codex-B
```

已确认两边具有独立的：

- authentication state；
- session/history state；
- profile-local application state。

`/Users/smterpro/.codex` 不是 authoritative identity binding。它可以作为人工日常使用的 convenience symlink，但 automated orchestration 不得依赖它判断当前账号。

当前 convenience symlink 指向 `.codex-B`；这个事实不是 1PCloop invariant。

### Default role binding

当前默认角色：

```text
Reviewer = dym   = .codex-B
Executor = cheng = .codex-A
```

角色绑定是 operational configuration，不是理论要求。

如果 usage limit、模型可用性或其他实际原因需要交换账号角色，Human Owner 可以人工重新绑定 Reviewer / Executor。当前 scope **不要求自动 role swap / role migration**。

### Programmatic invocation

1PCloop 的 active automation path 是 Codex CLI / programmatic invocation，不是 GUI automation。

Canonical identity selection：

```text
CODEX_HOME=/Users/smterpro/.codex-A codex ...
CODEX_HOME=/Users/smterpro/.codex-B codex ...
```

已实测：

- A/B 分别执行 `codex exec` 成功；
- A/B 可以同时运行独立 `codex exec` process；
- 并发 smoke test 两边均正常返回并以 exit code 0 结束。

因此 GUI App 是否能够同时打开，不属于 1PCloop control path 的限制。

### Shared binary, isolated profiles

Codex executable/runtime installation 在两个 profile 间共享。

已观察到一个 profile 触发 Codex 更新后，另一个 profile 后续启动直接使用更新后的 binary，无需单独再次更新。

以下状态仍保持 profile-local：

- auth/account identity；
- sessions/history；
- profile configuration/state。

具体 Codex version、具体模型名称和 reasoning effort 都属于易变 runtime configuration，不写死为 Static requirement。

---

## Hard Constraints

### 1. Single-host dual-identity execution

- Reviewer 与 Executor 必须运行在当前同一台 physical Mac 上，除非 Human Owner 明确改变本项目 scope。
- 两个角色必须通过两个独立 Codex identity/profile state 承担。
- Orchestrator 必须对每次 role invocation 显式绑定目标 `CODEX_HOME`。
- 不得依赖当前 `~/.codex` symlink、当前 GUI foreground app 或人工账号切换来确定角色身份。

### 2. Role identity is not model identity

Reviewer / Executor 的角色由：

- role instruction；
- responsibility boundary；
- authoritative input；
- allowed action；
- review/acceptance authority；

定义，而不是由某个特定模型名称定义。

因此：

- Reviewer 与 Executor 可以使用不同模型；
- 模型可以随 Codex availability、usage 或 Human Owner 决策调整；
- 当前模型配置不能被当作框架 invariant；
- 不能把“Reviewer = 某型号模型”或“Executor = 某型号模型”写入理论 claim。

### 3. Orchestrator-mediated communication

Reviewer 与 Executor 之间的自动通信必须经过 deterministic orchestrator 显式路由。

“主动发送消息”在本任务中的含义是：

```text
Codex role inference
    -> orchestrator receives current role output
    -> orchestrator routes the peer payload
    -> target Codex role is invoked
```

不得假设某个 Codex conversation 可以在没有 orchestrator invocation 的情况下自行唤醒另一角色。

Reviewer / Executor role instruction 必须明确当前角色是在与另一个 LLM Agent 协作，而不是把 peer payload 误认为 Human message 的全部语境。

### 4. Do not rely on Python understanding natural language

Python orchestrator 是 deterministic transport / control layer，不是自然语言 semantic reasoner。

因此 1PCloop 不得要求 Python 从 Reviewer / Executor 的自由文本中可靠推断：

- reasoning；
- execution instruction；
- evidence 的语义；
- acceptance / rejection；
- limitation；
- 自由文本内部的其他 semantic field。

Agent-to-agent 自由文本默认视为 **opaque semantic payload**。

Python 可以添加自身确定的 metadata，例如：

```text
sender
receiver
turn
run id
process result
```

但不应通过解析 peer 自然语言重新构造 Agent 的语义内容。

该边界仍概括为：

```text
LLM 理解 LLM。
Python 路由 LLM。
```

以及：

```text
Deterministic transport/control metadata
+
Opaque natural-language LLM payload
```

### 5. Do not rely on prompt-only structured output for authoritative control

1PCloop 的正确运行不得建立在以下假设上：

> 只要 prompt 写得严格，LLM 就会始终稳定输出合法且语义正确的 JSON / XML / marker / schema。

因此：

- Agent-to-agent semantic communication 不应依赖 prompt-only JSON parsing；
- 不得用 `if "ACCEPT" in output` 一类字符串搜索直接决定 authoritative Runtime transition；
- 不得要求 Python 先解析 LLM 自由文本后才能把 peer message 交给另一角色；
- 如果后续需要 machine-executable control-plane signal，应使用独立 deterministic / runtime-enforced mechanism。

### 6. Repository-backed authoritative state

- Static 与 Runtime 是 1PCloop 的权威治理状态。
- Conversation history 不是 authoritative project state。
- Git、source code、test output、run log、generated artifact 可以作为共享 evidence surface。
- Executor 的自然语言总结本身不能替代它所指向的实际 evidence。
- 新开 Codex session 不应导致项目状态丢失；角色应能从 repository-backed state reconstruct 当前任务。

### 7. Role separation

#### Reviewer

Reviewer 负责：

- 读取 Static 和 Runtime；
- 检查当前状态一致性；
- 编译当前唯一 Active Step；
- 向 Executor 发送 bounded instruction；
- 独立访问并检查实际 evidence；
- 形成 `ACCEPT` 或 `REJECT` verdict；
- `REJECT` 时产生 repair instruction；
- evidence 足够时推进 Runtime；
- 只有在 Human Owner 已明确授权 stable-contract 变化时才修改 Static。

Reviewer 默认不承担当前 Active Step 的主要 implementation work。

#### Executor

Executor 负责：

- 接收当前 Active Step 所需的 bounded context；
- 执行被授权的 implementation / repository mutation；
- 调用允许的工具；
- 运行 self-check；
- 暴露实际 evidence locator；
- 向 Reviewer 汇报 implementation result、limitation 和 evidence locator。

Executor 默认不得：

- 修改 Static；
- 推进 Runtime；
- 给自己的工作做最终 `ACCEPT`；
- 自行扩大 Active Step scope。

### 8. Prompt-level role isolation first

当前 prototype 优先验证闭环本身。

Reviewer / Executor 的文件职责边界首先由 role prompt / developer instruction 约束，而不是立即新增复杂 filesystem whitelist 或额外 profile sandbox configuration。

原因：

- 当前人工使用中角色边界已经长期可执行；
- 额外强制配置会增加日常 Codex 使用摩擦；
- 目前没有 evidence 表明 prompt-level separation 不足。

如果后续真实运行出现越权修改，再基于实际 failure evidence 加强 filesystem/capability isolation。

### 9. Single authoritative Active Step

正常执行时，Runtime 最多只能有一个 authoritative Active Step。

Repair 仍属于当前 Active Step 的继续执行，不应在未验收当前 Step 时自行激活新的权威 Step。

### 10. Evidence-backed acceptance

Reviewer 最终 `ACCEPT` 必须基于 Reviewer 可以直接定位并检查的 evidence，而不是仅基于 Executor 的 `PASS` 或自然语言报告。

Runtime transition 必须能够指出支持该 transition 的 evidence locator。

### 11. Engineering foundation 与本地 UI/observability

当前允许进入 engineering scope：terminal status、run/stage timer、structured progress
events、doctor/preflight/status/resume/inspect CLI、Human Gate UX 和本地 TUI。后续只能根据
实际使用 evidence 决定是否需要简单本地 GUI。

“本地 1PCloop UI”用于展示和操作 structured control state；它不等于控制 Codex GUI 的
GUI automation。UI 不得通过解析自然语言猜测 authoritative state。

### 12. 默认中文 Prompt 模板方向

foundation_v1 将基于 Framework v1.2 的 Static/Runtime Prompt 模板建立 1PCloop task
bootstrap 规范，默认模板语言为中文。模板必须保持 Static/Runtime 职责分离、Single Active
Step、evidence-backed transition、task-local freeze、Human Gate、Pending deadline 和
supersession。

模板是可按任务风险与复杂度裁剪的治理工具，不是要求所有任务使用完整章节的固定 schema。
其只读固定输入为：

```text
/Users/smterpro/Workspace/Tools/structured-llm-execution-framework/structured-llm-execution-framework_static.md
SHA-256: e3ff93b4136c0d3d87d7f1a319ca9c4513f831327daf18aea46f9f3d6659daf7

/Users/smterpro/Workspace/Tools/structured-llm-execution-framework/structured-llm-execution-framework_runtime.md
SHA-256: 3cbc4c93adff6ac2b1fb351a8a81f4b65dbd73b4de28ee2d0d4141522258ab54
```

外部 Tools 路径是固定输入，不是 1PCloop 可直接修改的对象。模板规范化属于 foundation_v1
的独立 deliverable，未实现或验收前不得描述为当前能力。

---

## Stable Background

### Existing governance model

现有 `structured-llm-execution-framework` 的以下语义是 1PCloop 的治理基础：

- Static / Runtime 分离；
- Reviewer / Executor role separation；
- repository / artifact evidence；
- independent review；
- bounded Active Step；
- Human Owner authority。

### Context reconstruction already works in practice

现有人工工作流已经长期采用：

```text
Static
+ Runtime
+ repository/evidence
+ current bounded peer instruction
```

重新建立 session context。

因此 conversation continuity 不是本项目当前需要重新证明的核心理论问题。自动 prototype 可以优先使用 fresh `codex exec` session，而不是先实现 session-resume machinery。

### Current verified profile behavior

当前已经验证：

```text
.codex-A / cheng
  -> independent account/profile
  -> codex exec works

.codex-B / dym
  -> independent account/profile
  -> codex exec works
```

串行及并发调用均已成功。

当前观察到的具体模型、reasoning effort、sandbox mode 或 Codex version 只能作为 Runtime/evidence 记录，不能上升为永久 Static contract，除非 Human Owner 明确改变要求。

### Superseded implementation assumptions

以下内容属于早期 Miniloop/Ollama prototype 的 implementation assumption，**不再是 active 1PCloop Hard Constraint**：

- Ollama 必须作为 active runtime；
- Reviewer 与 Executor 必须复用同一个本地 Qwen model ID / weights；
- Reviewer / Executor 必须只是同一个 local model object 下的两个 logical history array；
- active prototype 必须依赖本地 27B/35B Qwen inference；
- 同模型权重复用是当前 1PCloop acceptance prerequisite。

这些旧实现及其 evidence 已保存在：

```text
1PCloop/history/miniloop-skeleton-v0/
```

该目录是 historical implementation snapshot，不应为了当前 active 1PCloop 开发而改写。

---

## Explicitly Out of Scope for Current 1PCloop

当前阶段明确不要求优先解决：

1. GUI automation、AppleScript composer control 或模拟键盘/鼠标发送；
2. 自动账号 role swap / quota-aware role migration；
3. production-grade quota management；
4. Reviewer / Executor 的新 filesystem hard-isolation system，除非真实越权 evidence 证明有必要；
5. conversation history 超长后的复杂压缩/迁移；
6. 多个并行 Executor或多个 active loop 操作同一 target；
7. 双物理机器 transport（属于 `2PCloop`）；
8. production Web platform、distributed observability、production-grade queue 或 distributed
   database；
9. 长期 memory database / vector database；
10. 把某个具体 Codex 模型组合证明为理论最优；
11. 修复不影响 fresh execution 的旧 Codex historical-session metadata。
12. repository lock、filesystem watcher、multi-writer reconciliation 或通用 concurrency
    consistency guarantee。

测试任务必须选择不依赖以上能力即可完成的 bounded scenario。

---

## Authority and Approval

- Human Owner 可以修改本 Static、改变角色绑定或改变 1PCloop stable contract。
- Reviewer 可以解释 Static、形成 verdict，并在 evidence 支持时更新 Runtime。
- Reviewer 只有在 Human Owner 已明确授权 stable-contract 变化时才应修改 Static。
- Executor 无权自行修改 Static。
- Executor 默认无权修改 Runtime。
- 若实现过程中发现必须改变 Hard Constraints 或 Acceptance Criteria 才能继续，该变化不能由 Executor 静默完成。

---

## Acceptance Criteria

1PCloop 只有在以下条件都有可定位 evidence 支持时，才可判定完成。

### A. Deterministic dual-profile invocation

必须证明：

- Reviewer invocation 显式绑定 `.codex-B`；
- Executor invocation 显式绑定 `.codex-A`；
- 角色调用不依赖 `~/.codex` symlink 或 GUI active profile；
- 两边 auth/session state 保持独立；
- 可以按 `Reviewer -> Executor -> Reviewer` 顺序稳定调用。

### B. Automatic inter-agent message routing

必须证明：

- Reviewer 自然语言输出可以由 orchestrator 自动转发给 Executor；
- Executor 自然语言输出可以由 orchestrator 自动转发给 Reviewer；
- peer message semantic payload 可以原样保留，不要求 Python 拆 instruction / reasoning / evidence 字段；
- role instruction 明确双方处于 LLM-to-LLM collaboration context；
- 完整往返不依赖 Human 手工复制粘贴；
- transport correctness 不依赖 prompt-only JSON / XML 格式。

### C. Bounded Executor context

必须证明 Executor 接收的是当前 Active Step 所需的 bounded execution context，而不是 Reviewer 的完整 conversation history。

在满足 bounded context 的前提下，Reviewer peer message 应允许作为完整自然语言 payload 直接传递。

### D. Real execution and evidence exposure

Executor 必须完成至少一个真实、可验证的 bounded implementation task，并：

- 对 repository 或明确测试 artifact 产生实际结果；
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

### F. PAUSED optional REJECT -> REPAIR reliability coverage

Human Owner 于 `2026-09-12` 暂停 P7，因此本项不再是当前 foundation_v1 完成前置条件。
未经 Human Owner 明确重新激活，不得执行 fault injection。未来重新激活时，可将以下路径作为
optional reliability coverage：

```text
Reviewer REJECT
    -> bounded repair instruction
    -> Executor repair
    -> new evidence
    -> Reviewer re-review
```

可以正常运行。

Repair instruction 可以作为 Reviewer 自然语言输出原样路由给 Executor；orchestrator 不得要求 Python 先理解并拆分其语义。

### G. ACCEPT -> Runtime transition

必须证明：

- Reviewer 可以在 evidence 足够时形成 `ACCEPT`；
- `ACCEPT` 后 Runtime 才发生对应 authoritative transition；
- transition 记录 evidence locator；
- Executor 不能自行完成最终 acceptance 或 Runtime progression；
- authoritative transition control 不依赖 Python 从自由文本中字符串搜索或推断 `ACCEPT`。

### H. No semantic-parser dependency

必须证明核心消息往返在以下条件下仍然成立：

- Python 不理解 Reviewer / Executor 自然语言内容；
- Python 只负责能够确定的 role identity、sender / receiver、process、turn / run metadata；
- Reviewer / Executor 允许轻微自然语言格式漂移，只要 peer LLM 能理解实际语义；
- 系统不因 Agent 未严格遵循某个 prompt-only JSON 模板而失去基本路由能力。

### I. Fresh-session reconstruction compatibility

必须证明 automated loop 不依赖某个历史 Codex conversation 才能继续工作。

至少一个 demonstration 应允许角色通过：

```text
Static
+ Runtime
+ repository/evidence
+ bounded peer message
```

在 fresh Codex invocation 中恢复执行所需 context。

### J. Reproducible end-to-end run

Repository 中必须保留足够的 source、role instructions、configuration、test/demo command 与 run evidence，使 Human Owner 能重新运行至少一个完整 demonstration，并观察到：

```text
Reviewer
-> Executor
-> Reviewer
-> optional REJECT / repair
-> Reviewer ACCEPT
-> Runtime progression
```

---

## Immediate Implementation Order

> **历史边界：** 以下列表记录 1PCloop 初始 bootstrap 时的实现顺序，不表示当前 active step。当前唯一有效的工程状态和下一步只看 `1PCloop/docs/miniloop_runtime.md`。

当前优先顺序：

1. **DONE — account/profile bootstrap**：建立 `.codex-A` / `.codex-B` 两个独立 profile；
2. **DONE — CLI invocation smoke**：分别通过显式 `CODEX_HOME` 调用 A/B；
3. **DONE — concurrent process smoke**：验证 A/B `codex exec` 可同时正常完成；
4. **NEXT — text-only routing loop**：实现 Reviewer -> Executor -> Reviewer 的无人复制粘贴三段自动调用；
5. 让 Executor 修改 disposable artifact；
6. Reviewer 独立读取 evidence 并 verdict；
7. 验证 REJECT -> REPAIR；
8. 接入 ACCEPT -> Runtime authoritative transition；
9. 再根据实际 failure evidence 增加 circuit breaker、Human Gate 或 capability enforcement。

不要在第 4 步之前提前实现与已观察问题无关的复杂 infrastructure。

---

## Completion Definition

当前完成判断由 `foundation_v1` task-local Static/Runtime 中的 acceptance criteria 和独立
Reviewer evidence 决定。只有 foundation_v1 的必需工程交付均通过独立验收后，Human Owner
才决定 overall 1PCloop 是否从 `ACTIVE` 迁移为 `COMPLETED`。

该完成定义只针对 engineering artifact。Framework-as-paper、论文 novelty、controlled research outcome 或某个 narrow candidate pilot 都不是 1PCloop 工程完成的前置条件。

P7 fault injection、完整 GUI、paper novelty 和 research experiment 同样不是当前 completion
前置条件；其中任何一项只有在 Human Owner 明确重新激活或 evidence-driven 决策选择后才进入
对应 task scope。

在此之前，即使：

- 两个 Codex profile 均能调用；
- 两个 CLI process 可以并发；
- 某个 Executor implementation 单独成功；

也不等于整个 1PCloop 已完成。
