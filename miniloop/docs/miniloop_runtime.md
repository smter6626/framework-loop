# Miniloop Runtime

## Task Status

`ACTIVE`

当前 task：实现并验证最小可运行的本地 Reviewer–Executor 自动闭环。

本 Runtime 记录当前 authoritative execution state。稳定目标、硬约束和最终验收标准见：

`miniloop/docs/miniloop_static.md`

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

当前无已追加的 correction note。

`Other Notes` 的治理规则已锁定为：

- append-only；
- 旧 note 不得删除或直接修改；
- 后续可以追加新 note 来否定、纠正或 supersede 前面的判断；
- 每次追加 note 必须写明它对应的 Step 和 commit；
- 保留旧内容是为了维持可考古性（provenance / trace-back），而不是因为旧判断仍然具有当前 authority。

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

Miniloop v0 不通过自然语言判断一个 Agent “是否说完”，也不需要通过 `ollama ps` 或周期轮询模型 busy 状态来判断。

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

Miniloop v0 使用一个本地持久化 receiver control file 表示下一自动控制权属于谁。

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

Python 应在程序启动时和每次 Reviewer inference 完成后读取 receiver。如果读取到 `human`，不得继续触发 Executor。

#### 6. Reviewer owns receiver transition authority

Reviewer 是 acceptance / orchestration authority，因此 receiver transition 默认由 Reviewer 决定。

Executor 遇到 blocker、limitation 或无法继续的问题时，通过自然语言原文汇报给 Reviewer；Reviewer 再判断：

```text
继续自动执行 -> receiver = executor
需要 Human / 最终停止 -> receiver = human
```

实现上使用窄 capability，例如：

```text
set_receiver("executor")
set_receiver("human")
```

由 Python 校验允许值并写入 receiver control file。

#### 7. `human` is a generic handoff / stop state

`receiver = human` 只表示下一控制权属于 Human，而不是 Executor。

它可以覆盖：

- Reviewer 判断需要 Human 参与；
- 当前自动循环最终完成，需要把控制权交回 Human；
- 其他 Reviewer 判断不应继续自动触发 Executor 的情况。

具体原因由 Runtime / Reviewer natural-language report 表达，而不是编码进 receiver 文件。

#### 8. Local repository operation is primary; GitHub remote is not required for loop routing

Miniloop 的 Reviewer / Executor 主要操作本机 clone / working tree。GitHub remote 不是 Reviewer–Executor transport layer；SSH 只在需要 `git pull` / `git push` 等远端同步时使用。

Miniloop v0 不需要依赖 GitHub API 才能完成核心循环，也不要求自动 push 才能证明本地 Reviewer–Executor loop 成立。

### Locked local execution and capability decisions

#### 9. Executor receives full shell capability inside a Linux VM sandbox

Executor 需要完整 shell 能力，但不直接获得宿主 macOS 的完整 filesystem 访问。

当前方案锁定为：

```text
macOS host
├── Ollama / Qwen
├── Python orchestrator
├── Static / Runtime / control state
└── Linux VM sandbox
      └── Executor full shell
          └── mounted authorized workspace
```

Executor 在 Linux VM 内可以使用完整 shell / command semantics；Python 不通过分析 shell 字符串来判断其自然语言或命令语义。

安全边界来自 VM / mount visibility，而不是 `cwd`、shell command blacklist 或 prompt。

#### 10. Apple-specific work is separated from generic Linux execution

涉及 Apple Silicon / macOS-specific toolchain、framework、binary、Xcode、Mach-O 或其他无法在 Linux VM 中真实执行的操作，不强行塞入通用 Linux Executor sandbox。

这些操作应被移动到单独的 host-native execution path，在需要时以明确、独立的 capability / step 执行。

Miniloop 当前 prototype 应优先选择不依赖 Apple-specific host execution 的 bounded demo。

#### 11. Static and Runtime remain outside the Executor writable workspace

该规则与 Linux VM 不冲突，反而由 VM mount boundary 实现。

当前不要求物理移动现有文件路径；可以继续保留：

```text
miniloop/docs/miniloop_static.md
miniloop/docs/miniloop_runtime.md
```

关键要求是 Executor Linux VM 的 writable mount 只包含授权 implementation workspace，不挂载 Static、Runtime 或 control plane 文件。

因此 Executor 不是“看得到 Runtime 但被 prompt 告知不要改”，而是 writable workspace 本身不包含 Runtime / Static。

#### 12. Reviewer capability surface

Reviewer 需要：

- 读取 Static / Runtime；
- 读取所有当前任务相关 implementation / artifact / evidence；
- 独立运行测试或验证；
- 修改 Runtime；
- 使用 `set_receiver()` 控制下一 receiver。

Reviewer 不承担主要 implementation mutation。

Runtime modification 不使用完全无约束的普通 file write；由轻量 Python Runtime updater 提供机械约束。

#### 13. Executor capability surface

Executor 在授权 Linux VM workspace 内：

- 可以读取允许 workspace 中的所有文件；
- 可以修改允许 workspace 中除 governance/control 外的 implementation / test / artifact 文件；
- 可以使用完整 shell 能力执行 build、test、git、本地脚本等操作；
- 不获得 Runtime / Static 的 writable mount；
- 不获得 Runtime updater；
- 不获得 receiver setter。

当前设计优先通过“只把允许 workspace mount 给 Executor”形成边界，而不是靠 Python 对每一个文件路径做自然语言式判断。

### Locked Runtime structure and mutation rules

Runtime 的理想结构从当前设计起按以下语义维护：

```text
Done
  - completed historical record
  - Commit Notes

Other Notes (optional, append-only)

Active Step N
  - current authoritative step
  - optional Step N branches / alternatives

Pending Tasks
  - non-blocking blockers / deferred work that must not be lost

Next Steps
```

机械写入规则：

- `Done`：历史记录 immutable；
- `Commit Notes`：作为 Done provenance immutable；新增时必须标明 Step + commit；
- `Other Notes`：append-only；每条新 note 必须标明 Step + commit；可追加 correction / invalidation，但不删除旧 note；
- `Active Step`：允许 Reviewer 根据当前 evidence 更新；
- Active Step 下的可选 branch / alternative：允许更新；
- `Pending Tasks`：允许新增、推进和移除，但移除必须因为该 pending item 已实际处理、被吸收进 Active Step / Done，或被明确 supersede；不能因其“不阻塞”就静默丢失；
- `Next Steps`：允许随当前 evidence 更新。

Python Runtime updater 的职责是轻量、机械地检查这些结构性约束，不判断 Runtime 自然语言内容的真实语义。

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
   - Executor 必须在 Linux VM 的授权 workspace 中执行至少一个真实、可验证的 bounded task；
   - 产生 repository diff、test artifact、log 或其他可直接检查的 evidence；
   - Executor 运行 self-check 并向 Reviewer 说明可定位的 evidence；
   - Executor 不需要通过减少 shell 功能来实现 filesystem boundary。

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
   - Reviewer 可以通过受限 receiver control capability 将下一控制权设置为 `executor` 或 `human`；
   - Runtime updater 必须保护 Done / Commit Notes 的历史不可变性和 Other Notes 的 append-only 语义。

### Permitted Changes

允许为完成当前 Active Step：

- 在 `miniloop/` 下创建或修改 orchestrator source code；
- 创建 Reviewer / Executor system instruction 或 agent configuration；
- 创建 deterministic transport envelope / routing logic；
- 创建 receiver control file 及其受限 setter；
- 创建 Linux VM / sandbox 配置；
- 创建 Executor writable workspace；
- 创建 Reviewer / Executor capability wrapper；
- 创建轻量 Runtime updater；
- 创建 bounded demo / fixture / test；
- 创建 run logs、test outputs 或其他 evidence artifact；
- 创建必要的 README / run instruction；
- 在 evidence 支持 Reviewer verdict 后更新本 Runtime。

### Restricted Changes

当前 Active Step 不授权 Executor：

- 修改 `miniloop/docs/miniloop_static.md`；
- 修改 `miniloop/docs/miniloop_runtime.md`；
- 访问或修改 receiver / control plane state；
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
- Linux VM Executor sandbox / mount 配置；
- Executor 能使用完整 shell、但 Static / Runtime / control state 不位于其 writable workspace 的验证 evidence；
- Runtime updater 对 Done / Commit Notes immutable 和 Other Notes append-only 的验证；
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

## Pending Tasks

当前无已确认且需要持久化的 non-blocking pending item。

本 section 的语义已锁定：

- 当发现一个真实问题 / blocker，但它不阻塞当前 Active Step，且没有立即被处理掉时，必须记录到 `Pending Tasks`；
- “不阻塞当前步骤”不能成为不记录问题的理由；
- pending item 后续可以被处理、吸收进某个 Active Step、明确 supersede 或关闭；
- pending item 的生命周期变化必须显式记录，不能静默消失。

---

## Current Blockers

None confirmed.

当前尚未形成 implementation-level evidence，因此不得预先声称 context switching、message routing、tool permission、independent review、VM isolation 或 Runtime transition 已经实现。

Python Router v0 的 session routing、verbatim peer-message transport、Ollama inference-completion signal、receiver-based handoff / stop mechanism、Linux VM Executor sandbox 方向、角色 capability 边界和 Runtime mutation invariants 已形成当前设计决策。

仍可在 Codex implementation 前继续具体化但不构成 blocker 的实现细节包括：

- receiver control file 的具体路径与最小持久化格式；
- Linux VM 技术选型与启动方式；
- Reviewer 独立测试时具体采用 host-side tool、read-only mount 或其他验证 execution path；
- Runtime updater 的具体函数接口名称。

这些属于 implementation detail；只要实现不违反上述锁定边界，不需要在 Runtime 中提前冻结。

---

## Explicitly Deferred for This Task

当前 Miniloop 不处理：

- conversation history 超过约 60K tokens 后的 context management；
- 完整 Human Decision Gate 的交互、决策输入和自动恢复协议；
- 无限 repair / clarification loop 的自动检测与终止；
- production-grade VM / container hardening；
- 通用 Apple-specific host execution framework。

`receiver = human` 作为 deterministic stop / handoff primitive 已纳入当前设计，但不等于本阶段必须完成完整 Human Gate workflow。

Apple-specific operation 已确认为 generic Linux sandbox 之外的独立执行类别，但 Miniloop v0 demo 不要求实现完整 host-native execution framework。

这些 deferred 问题不应阻塞当前 Active Step。

---

## State Transition

### Previous state

`ACTIVE — Step 1`，Router v0 的 context / message / completion / receiver 设计已基本锁定，但 local shell sandbox、Runtime mutation invariant 和 non-blocking issue persistence 尚未确定。

### Evidence

Human Owner 在当前设计讨论中确认：

- Executor 使用 Linux VM 获得完整 shell 能力；
- Apple-specific work 从 generic Linux execution 中移出，单独执行；
- Static / Runtime 不进入 Executor writable workspace，该规则与 VM mount boundary 配合；
- Reviewer 可以读取和测试任务相关文件，并允许通过受限 Runtime updater 修改 Runtime；
- Executor 可在授权 workspace 内修改 implementation / tests / artifacts，但不能修改 Runtime / Static；
- `Done` / `Commit Notes` 作为 historical provenance 不允许回写；
- `Other Notes` 为 append-only，可以追加后续 correction / supersession，但不删除旧记录；
- 新写入的 Commit Notes 和 Other Notes 必须带 Step + commit provenance；
- Runtime 新增 `Pending Tasks`，用于保存未立即解决的 non-blocking blocker / work item。

### Current state

`ACTIVE — Step 1: Build and demonstrate the first end-to-end Miniloop`

当前设计已经收敛到：

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
+
Linux VM Executor full-shell sandbox
+
governance/control outside Executor writable workspace
+
lightweight invariant-enforcing Runtime updater
```

### Meaning

Active Step 没有改变，也尚未产生 implementation acceptance evidence。本次 Runtime 更新仅持久化已经由 Human Owner 确认的 execution sandbox、capability 和 Runtime-history 规则，为后续 Codex implementation 提供稳定边界。

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

### Host-side unrestricted Executor shell

Status: `SUPERSEDED`

Previous considered direction:

Executor 在 macOS host 的固定 cwd 中使用 shell，并主要通过路径约定 / prompt 限制访问范围。

Current decision:

Executor 的完整 shell 运行在 Linux VM sandbox 中；filesystem boundary 由 VM / mount visibility 实现，而不是把固定 cwd 误当成安全边界。

---

## Next Steps

当前下一步不再重新讨论已锁定的 session / peer-message / completion / receiver / sandbox / Runtime-history 规则。

进入 Codex implementation 前，只需要根据实现便利性选择不影响上述 contract 的具体技术细节，例如：

- Linux VM / container runtime 的具体实现；
- executor workspace mount path；
- receiver file path；
- Runtime updater function names；
- Reviewer validation execution path。

这些细节如果没有产生新的约束冲突，可以由 Codex 在当前边界内实现并通过 evidence 验证。