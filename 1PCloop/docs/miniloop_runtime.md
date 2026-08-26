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

### Step 1 — Codex implementation: build the Miniloop framework skeleton

Status: `ACTIVE`

### Current Objective

停止继续纯理论展开，进入受控 implementation。

Codex 当前应基于已经锁定的 Static + Runtime 边界，实际搭建 Miniloop 的第一版大框架并运行能够运行的测试。实现过程中：

- 已锁定的架构原则直接实现，不重新设计；
- 普通 implementation detail 可以基于本机与 repository evidence 做最小、可逆的合理选择；
- 如果遇到会影响 architecture、role boundary、filesystem isolation、Runtime authority、control-plane semantics、security boundary 或 acceptance semantics 的未确认技术细节，不得自行冻结设计；
- 对该不确定子项停止扩展，记录 evidence / blocker / options，并回报 Human Owner，由 Human + Reviewer 侧讨论确认；
- 其他不受该问题阻塞的确定部分继续实现；
- 不因为存在局部未确认项而停止全部工作。

当前目标不是一次性宣称整个 Step 1 完成，而是先得到一个真实、可运行、可检查的大框架，以实际 evidence 驱动后续设计。

目标链路仍为：

```text
Reviewer reads Static + Runtime
    -> Reviewer compiles bounded execution instruction
    -> Python routes Reviewer raw output to Executor
    -> Executor performs real work in bounded Linux execution environment
    -> Executor self-checks and reports evidence locator
    -> Python routes Executor raw output to Reviewer
    -> Reviewer independently checks evidence
    -> repair or handoff / completion
```

### Locked Architecture — Do Not Redesign During This Implementation Pass

#### A. Python / LLM semantic boundary

- Python orchestrator 负责 deterministic transport / control，不负责理解 Agent 自由文本语义；
- Reviewer / Executor 之间传递 verbatim natural-language payload；
- Python 可以维护 sender、receiver、turn、run_id / session metadata；
- 不依赖 prompt-only JSON / XML / marker 让 Python理解 instruction、evidence、ACCEPT、REJECT；
- 不允许通过 `if "ACCEPT" in output` 等自由文本解析推动 authoritative transition；
- 简化原则：`LLM 理解 LLM；Python 路由 LLM。`

#### B. Same model, isolated sessions

- Reviewer / Executor 使用同一个 Ollama model ID / 同一份本地 Qwen weights；
- Python 分别维护 Reviewer 与 Executor conversation state；
- 两个 session 使用不同 system / role instruction；
- 不复制双方完整 history；只显式路由本轮 peer payload；
- 当前采用串行 inference，不加载两个同模型副本。

#### C. Ollama turn completion

- 使用 blocking Ollama chat request（例如 `stream=false`）作为单轮 inference completion signal；
- request 返回只代表当前 turn 生成完成，不代表语义上的 task completion；
- 不使用 `ollama ps` / busy polling 作为当前 turn 完成信号。

#### D. Receiver control plane

持久化 receiver control state 的核心值：

```text
executor
human
```

- Reviewer 拥有 receiver transition authority；
- Python 在程序启动时和每次 Reviewer inference 完成后读取 receiver；
- `executor` -> 自动 loop 可以继续并触发 Executor；
- `human` -> 自动 loop 停止，把控制权交回 Human；
- Executor 不获得 receiver setter；
- 使用窄 capability（如 `set_receiver(executor|human)`），而不是 Python解析 Reviewer 自由文本。

#### E. Executor Linux execution boundary

- Executor 使用 Linux VM / Linux sandbox 内的完整 shell 能力；
- shell capability 本身不通过 Python command blacklist 限制；
- filesystem boundary 由 VM / mount visibility 强制，而不是把 `cwd` 误当 sandbox；
- Executor writable mount 只包含授权 implementation workspace；
- Static、Runtime、receiver / control plane 不进入 Executor writable workspace；
- Apple Silicon / macOS-specific execution 移出 generic Linux Executor path，后续需要时单独处理；
- 当前 demo 优先选择不依赖 Apple-specific toolchain 的 bounded task。

#### F. Role capability boundary

Reviewer：

- 可读取 Static / Runtime；
- 可读取任务相关 implementation / artifact / evidence；
- 可独立运行测试 / verification；
- 可通过受限 updater 修改 Runtime；
- 可调用 receiver setter；
- 不承担主要 implementation mutation。

Executor：

- 在授权 Linux workspace 内拥有完整 shell；
- 可读取 / 修改该 workspace 中 implementation / tests / artifacts；
- 不获得 Static / Runtime writable access；
- 不获得 Runtime updater；
- 不获得 receiver setter；
- 不负责最终 acceptance。

#### G. Runtime mutation invariants

Runtime 结构按以下语义维护：

```text
Done
  - completed historical records
  - Commit Notes

Other Notes
  - append-only correction / invalidation / supersession notes

Active Step
  - current authoritative work
  - optional branches / alternatives

Pending Tasks
  - non-blocking blockers / deferred work that must not be lost

Next Steps
```

机械规则：

- `Done` immutable；
- 已进入 Done 的 `Commit Notes` immutable；新增 Done / Commit Notes 时必须注明 Step + commit；
- `Other Notes` append-only；每个新 note 必须注明 Step + commit；历史错误通过追加 correction / supersession 说明，不删除旧记录；
- `Active Step` mutable；
- `Pending Tasks` 可新增 / 推进 / 显式关闭，不得静默丢失；
- `Next Steps` mutable；
- Python Runtime updater 只执行轻量机械约束，不判断自然语言内容真实性。

### Codex Implementation Scope for This Pass

优先实际实现并测试：

1. Python project / orchestrator skeleton；
2. Reviewer / Executor 两套隔离 logical session；
3. 同一 Ollama model ID 的 blocking serial inference wrapper；
4. deterministic envelope + verbatim peer payload routing；
5. receiver control file + allowed-value enforcement + reviewer-only setter boundary；
6. deterministic run / event logging；
7. lightweight Runtime updater skeleton and mechanical invariant tests；
8. Executor Linux sandbox abstraction / launcher skeleton；
9. authorized writable workspace mount boundary；
10. Reviewer / Executor role instructions / configuration skeleton；
11. unit / integration tests that do not require unresolved design assumptions；
12. README / run instructions sufficient to reproduce the implemented skeleton.

### Technical-Uncertainty Reporting Rule

Codex 遇到以下情况时应回报，而不是自行扩大 contract：

- 本机现有 virtualization / container runtime 行为与预期不一致；
- 需要改变 Static / Runtime authority；
- 需要让 Executor 看见或修改 governance / control files；
- 需要 Python 解析 Agent natural language 才能继续；
- 需要改变 receiver semantics；
- 需要改变 Reviewer / Executor acceptance authority；
- 需要额外 host-native privileged capability；
- 现有 Runtime invariant 无法机械实现而必须解释语义；
- 实现选择会形成新的不可逆 / 高影响 architecture constraint。

回报至少包含：

```text
Observed evidence
Exact uncertainty / blocker
Why current contract does not determine it
Option A / B / ...
Recommended option if evidence supports one
What implementation can continue without this decision
```

这些问题若不阻塞整个 Step，应同时记录到 `Pending Tasks`，然后继续其他确定工作。

### Environment Fact for Implementation

- Host: Apple Silicon Mac, M4 Max, 48 GB Unified Memory；
- Ollama 已安装，现有 Qwen3.5 35B-class / ~64K context baseline 已能运行；
- 当前 Miniloop implementation 优先继续使用现有 baseline，不因新模型下载阻塞；
- Docker 已安装在本机；当前 pass 可以只读检查现有版本 / runtime / settings evidence，但不得擅自升级、重装或进行需要 Human 决策的全局配置变更。

### Permitted Changes

允许 Codex 为当前 implementation pass：

- 在 `miniloop/` 下创建 / 修改 implementation source、tests、config、workspace、sandbox scripts、logs、README；
- 创建 receiver control implementation；
- 创建 Runtime updater implementation；
- 创建 Reviewer / Executor role instruction；
- 运行本地只读环境探测；
- 运行不违反当前边界的 tests / demo；
- 生成 evidence artifact。

不得：

- 修改 `miniloop/docs/miniloop_static.md`；
- 把 Step 1 标记为 `COMPLETED`；
- 重写 `Done` / 旧 Commit Notes / 旧 Other Notes；
- 自行改变已经锁定的 architecture；
- 擅自安装 / 升级 Docker 或进行全局系统级配置改变；
- 自动 push / publish；
- 引入必须依赖的 cloud LLM API；
- 扩大到 Web UI、多 Executor、distributed / production-grade platform。

### Required Evidence from Codex Pass

Codex 结束本轮实现后至少报告：

- changed files；
- implementation summary；
- exact commands / tests run；
- test results；
- local environment observations relevant to Linux sandbox；
- current working features；
- remaining uncertainties / blockers；
- Pending Tasks candidates；
- evidence locators；
- 未实现内容及原因。

不得仅以自然语言“已完成”替代实际 repository / test evidence。

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

当前没有已知 blocker 阻止 Codex 开始大框架 implementation。

implementation-level evidence 尚未形成，因此不得预先声称 Router、context isolation、Runtime updater、VM isolation、receiver handoff 或 end-to-end loop 已经实现。

从现在开始，未确认 technical detail 应优先通过实际 implementation / environment evidence 暴露；只有当该 detail 会影响已锁定 contract 或形成新的高影响边界时，才回到 Human Owner 讨论确认。

---

## Explicitly Deferred for This Task

当前 Miniloop 不处理：

- conversation history 超过约 60K tokens 后的 context management；
- 完整 Human Decision Gate 的交互、决策输入和自动恢复协议；
- 无限 repair / clarification loop 的自动检测与终止；
- production-grade VM / container hardening；
- 通用 Apple-specific host execution framework；
- 多 Executor / Web UI / distributed deployment / production queue / memory database。

`receiver = human` 作为 deterministic stop / handoff primitive 已纳入当前设计，但不等于本阶段必须完成完整 Human Gate workflow。

---

## State Transition

### Previous state

`ACTIVE — Step 1`，核心 Router、receiver、Linux execution boundary、role capability 和 Runtime mutation invariants 已在设计讨论中锁定，但尚未进入实际 implementation evidence 阶段。

### Current state

`ACTIVE — Step 1: Codex implementation — build the Miniloop framework skeleton`

### Transition Meaning

当前不再继续以纯设计讨论推进 Step 1。

Codex 现在应实际实现已经确定的框架部分；普通实现细节由 evidence 驱动做最小可逆选择。遇到 contract 无法决定、会改变关键边界的技术问题时，Codex 应记录并回报 Human Owner，而不是自行扩大设计。

Active Step 仍然属于原来的 Step 1，没有发生 acceptance，也没有进入 Done。

---

## Superseded / Invalidated Decisions

### Prompt-only structured Agent messages as required transport protocol

Status: `SUPERSEDED`

Reviewer / Executor semantic payload 使用自然语言原文；Python 不承担自由文本语义解析。

### Polling Ollama process/load state as inference-completion signal

Status: `SUPERSEDED`

使用 blocking Ollama request completion 作为单轮 inference 完成信号。

### Host-side unrestricted Executor shell

Status: `SUPERSEDED`

Executor 完整 shell 放入 Linux execution sandbox；filesystem boundary 由 VM / mount visibility 强制。

---

## Next Steps

1. 将本 Runtime + Static 作为 authoritative implementation contract 交给 Codex；
2. Codex 实际搭建 Miniloop framework skeleton 并运行可运行的 tests；
3. Codex 对不确定 technical detail 提交 evidence-backed report，而不是自行冻结高影响设计；
4. Human Owner / Reviewer 只针对实际 blocker / uncertainty 做后续确认；
5. 根据实现 evidence 再决定 repair、继续实现或更新 Pending Tasks；
6. 在满足全部 Acceptance Criteria 之前，Step 1 保持 `ACTIVE`。