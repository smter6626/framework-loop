# Miniloop Runtime

## 任务状态

`ACTIVE`

当前任务：实现并验证最小可运行的单机 Reviewer–Executor 自动闭环。

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

### 2026-09-05 — 当前有效说明（中文）

状态：`ACTIVE`

Step：`Step 1`

上述两条英文说明仍作为原有记录保留。其当前有效含义如下：

- 当前活跃路径是 `1PCloop/`；`1PCloop/history/miniloop-skeleton-v0/` 仅作为只读的历史实现证据；
- 当前已验证的执行环境是在同一台 M4 Max 主机上使用两个独立 ChatGPT/Codex 身份：`Reviewer = dym = /Users/smterpro/.codex-B`，`Executor = cheng = /Users/smterpro/.codex-A`；
- 自动化路径使用每个进程显式设置的 `CODEX_HOME` 以及 `codex exec` / 程序化 CLI 调用；模型名称和 reasoning effort 属于运行时配置，而非架构不变量；
- 旧的 Ollama/Qwen 实现只保留为历史实现证据，不再是当前活跃的实现目标。

---

## 当前活跃步骤

### Step 1 — 构建在线的双 Codex 1PC Reviewer–Executor 循环

状态：`ACTIVE`

### 当前目标

在已验证的双 Codex 环境上实现第一个真实的自动化循环。

直接目标：

```text
dym / Reviewer
    -> bounded natural-language instruction
    -> deterministic Python transport
    -> cheng / Executor
    -> raw execution response
    -> deterministic Python transport
    -> dym / Reviewer
    -> review / repair / handoff decision
```

当前目标不是一次性完成全部历史 Miniloop 验收标准。下一里程碑是最小的纯文本 Reviewer→Executor→Reviewer 循环，回合之间不需要 Human 复制粘贴。

### 已验证的前置条件

#### A. 独立 profile home — 已验证

```text
cheng -> /Users/smterpro/.codex-A

dym   -> /Users/smterpro/.codex-B
```

已验证属性：

- 独立的认证状态；
- 独立的 session / history / profile-local 状态；
- 在正常 filesystem permission 允许时，两个身份都可以访问同一 repository；
- `~/.codex` 只是便利 symlink，并非 account identity 的权威来源。

当前便利 symlink：

```text
/Users/smterpro/.codex -> /Users/smterpro/.codex-B
```

因此 orchestrator 必须为每次角色调用显式设置 `CODEX_HOME`。

#### B. 角色绑定 — 已验证

当前默认角色绑定：

```text
Reviewer = dym / .codex-B
Executor = cheng / .codex-A
```

自动角色互换不在当前范围内。如 account usage 或其他运行条件要求互换角色，Human Owner 可以手动完成。

#### C. CLI 调用 — 已验证

在 repository working directory 中执行的串行 smoke test 已成功：

```text
CODEX_HOME="$HOME/.codex-A" codex exec 'Reply with exactly: CHENG_EXEC_OK'
-> CHENG_EXEC_OK

CODEX_HOME="$HOME/.codex-B" codex exec 'Reply with exactly: DYM_EXEC_OK'
-> DYM_EXEC_OK
```

两者都创建了新的 Codex session，并返回正常的最终响应。

#### D. 并发 CLI 进程 — 已验证

并行 smoke test 已成功：

```text
A exit=0
CHENG_PARALLEL_OK

B exit=0
DYM_PARALLEL_OK
```

因此，使用 `.codex-A` 和 `.codex-B` 的两个独立 Codex CLI process 可以在同一台物理 Mac 上共存。

GUI 同时启动的限制与自动化 1PCloop control path 无关。

#### E. 共享 executable / 隔离 profile — 已验证

观察到的行为：

- 一个 profile 触发了 Codex application/runtime update；
- 第二个 profile 随后启动时没有执行独立更新；
- profile 的 authentication / history / config 仍然相互独立。

对当前实现的解释：

```text
shared Codex executable/runtime installation
+
independent CODEX_HOME state
```

#### F. 当前角色 capability 行为 — 已观察

在成功的串行 `codex exec` smoke test 中：

```text
cheng / Executor:
  approval = never
  sandbox = workspace-write


dym / Reviewer:
  approval = never
  sandbox = read-only
```

这与预期的角色分工一致，但当前 1PCloop 不依赖新增 filesystem-level isolation 规则。

角色边界初步由角色指令和已有 profile 行为强制。除非实际违规证明其必要性，否则推迟采用更强的 capability enforcement。

#### G. Conversation 连续性 — 初始循环不要求

第一个活跃实现可以为每一回合使用新的 `codex exec` session。

权威上下文仍然外置：

```text
Static
+ Runtime
+ repository / artifacts / evidence
+ current bounded peer instruction
```

该循环不得依赖长期存续的 Codex conversation 来保存权威状态。

### 本轮锁定的架构

#### Python / LLM 语义边界

- Python 执行确定性的 transport/control。
- Reviewer / Executor peer payload 作为 natural language 原样传递。
- Python 可以维护 role、sender、receiver、run id、turn id、process status 和其他机械 metadata。
- Python 不得通过解析任意 prose 推断语义上的 acceptance。
- 不得实现 `if "ACCEPT" in output` 风格的权威状态转换。
- 原则保持不变：`LLM understands LLM; Python routes LLM.`

#### Reviewer / Executor 职责分工

Reviewer:

- 读取 Static / Runtime / repository evidence；
- 编制有边界的 Executor instructions；
- 独立评估 implementation / evidence；
- 负责 review / repair / handoff 的语义判断；
- 通常不执行主要 implementation mutation。

Executor:

- 执行有边界的 implementation work；
- 按 task 要求修改 implementation / tests / artifacts；
- 运行 execution-side checks；
- 报告 evidence；
- 不得 self-accept；
- 默认不得修改 Static / Runtime。

当前 enforcement priority 是 prompt-level role instruction。除非实际 evidence 显示有必要，否则不引入额外的 profile/config 阻碍。

### 下一轮的实现范围

仅实现足以验证 transport loop 的内容：

1. 在活跃的 `1PCloop/` implementation area 下创建最小 Python orchestrator；
2. 使用 `CODEX_HOME=/Users/smterpro/.codex-B` 显式调用 Reviewer；
3. 捕获 Reviewer final response；
4. 使用 `CODEX_HOME=/Users/smterpro/.codex-A` 将该 raw response 路由给 Executor；
5. 捕获 Executor final response；
6. 将 Executor raw response 路由回 Reviewer；
7. 保存足以检查全部三回合的确定性 run/turn logs 或 transcripts；
8. 不要求 GUI automation；
9. 不要求 session resume；
10. 暂不要求 code mutation、Runtime mutation、receiver tools、repair-limit logic 或 Linux sandbox enforcement。

### 此直接里程碑的验收

仅当 evidence 证明以下事项时，纯文本 routing milestone 才算满足：

1. Reviewer 确实通过 `.codex-B` 调用；
2. Executor 确实通过 `.codex-A` 调用；
3. Reviewer output 无需 Human copy/paste 即可到达 Executor；
4. Executor output 无需 Human copy/paste 即可到达 Reviewer；
5. 所有 Codex invocation 都正常终止；
6. 完整三回合 transcript 可供检查；
7. Python 不对 peer natural-language payload 做语义解析。

通过此里程碑并不代表完成 Step 1；它只证明基础在线 transport loop。

---

## 待办任务

### P1 — 旧 Codex-A 状态中的过期 rollout path

状态：`NON-BLOCKING`

在首次 `.codex-A` 新建 `codex exec` smoke test 中观察到：

```text
state db returned stale rollout path for thread ...
/Users/smterpro/.codex/sessions/...
```

同一次 invocation 随后成功创建了新的 session，返回 `CHENG_EXEC_OK` 并正常完成。并行 A/B `codex exec` 也以 exit code 0 完成。

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

以下前置条件已验证，且不是阻塞项：

- dual profile authentication；
- 显式 `CODEX_HOME` account selection；
- 串行 `codex exec`；
- 并发 A/B `codex exec`；
- shared repository accessibility。

当前尚未实现的事项是确定性的 Reviewer→Executor→Reviewer transport 本身。

---

## 本任务明确延后事项

在直接的纯文本 routing milestone 期间，不实现：

- automatic role swapping；
- GUI automation；
- 新的 filesystem hard-isolation configuration；
- Linux VM/container sandbox enforcement；
- 完整的 Human Decision Gate interaction/resume protocol；
- automatic infinite repair-loop detection；
- production-grade crash recovery；
- multi-Executor 或 distributed deployment；
- Web UI；
- long-history context management；
- old Codex session migration/repair；
- browser/plugin/node-repl profile cleanup；
- 不同 model / reasoning effort 的 performance comparison。

在 live transport loop 产出证明其必要性的 evidence 后，才可重新评估这些事项。

---

## 状态转换

### 先前状态

`ACTIVE — Step 1：使用 Ollama/Qwen 和隔离的 logical sessions 构建 Miniloop framework skeleton。`

该状态产出了有价值的历史 implementation work，随后保存在：

```text
1PCloop/history/miniloop-skeleton-v0/
```

但它不再是当前活跃的 runtime target。

### 当前状态

`ACTIVE — Step 1：构建在线的单机双 Codex Reviewer→Executor→Reviewer 循环。`

### 转换含义

项目已经从以 Ollama/Qwen 为中心的 prototype path，转向一台 M4 Max 上已验证的双 Codex Plus profile environment。

在关键层面，governance architecture 保持不变：

- Static / Runtime 是权威外部状态；
- Reviewer 和 Executor 仍是独立角色；
- Python 负责路由；LLM 负责理解；
- Reviewer 独立评估 Executor work；
- Human Owner 仍是最终权威。

只有具体的 inference/session substrate 已改变。

下一项 implementation action 现在是完全可操作的，而不再只是理论：将已验证的 CLI identities 自动化为三回合 Reviewer→Executor→Reviewer text loop。

---

## 已取代 / 已失效的决策

### 仅 prompt 的结构化 Agent messages 作为必需 transport protocol

状态：`SUPERSEDED`

Reviewer / Executor semantic payload 使用 natural-language text；Python 不负责任意 free-text 的语义解析。

### 轮询 Ollama process/load state 作为 inference-completion signal

状态：`SUPERSEDED`

当前活跃的 inference substrate 是 Codex CLI。process/command completion 是直接的机械回合完成信号；语义 task completion 仍由 Reviewer 判断。

### 相同本地 model / 相同 Qwen weights 作为硬性要求

状态：`SUPERSEDED FOR ACTIVE 1PCLOOP`

Reviewer 和 Executor 绑定到独立 Codex identities。它们的 model selection 可以不同，并可随时间变化。Model identity 不是角色不变量。

### Linux sandbox 作为第一个 live loop 的前置条件

状态：`DEFERRED`

直接目标是证明在线 Reviewer→Executor→Reviewer transport。仅当 evidence 要求时，才加入更强的 sandbox/capability enforcement。

### GUI Codex application 作为 automation surface

状态：`REJECTED / NOT REQUIRED`

当前 control path 使用每个 process 显式设置的 `CODEX_HOME` 和 Codex CLI/programmatic invocation。GUI simultaneous-launch behavior 不约束自动化循环。

---

## 下一步

1. 实现最小的纯文本 Python routing prototype。
2. 运行一轮完整的自动化 `dym Reviewer -> cheng Executor -> dym Reviewer` 三回合循环。
3. 保存精确的 prompts / responses / process results 作为 evidence。
4. 验证回合之间不需要 Human copy/paste。
5. 验证 Python 原样 transport peer text，而非解释其含义。
6. 如果纯文本 milestone 通过，则进入一个可丢弃的 code/artifact mutation task，由 Executor 写入并由 Reviewer 独立检查。
7. 仅在该 evidence 存在后，才决定接下来复用 historical Miniloop skeleton 的哪些 control-plane features。
