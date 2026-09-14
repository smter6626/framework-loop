# foundation_v1 — Runtime 当前权威状态

## 1. Current Status

- Task ID：`foundation_v1`
- 状态：`ACTIVE`
- 当前 verdict：`NOT EVALUATED`
- 最近接受：`F1 — ACCEPTED AFTER REJECT → NARROW REPAIR → RE-REVIEW`
- 唯一 Active Step：`F2 — terminal timer、live status 与 structured progress event`
- 当前顶层 Step：`Step 2`
- Static identity：
  - path：`1PCloop/workloads/foundation_v1/workload_static.md`
  - SHA-256：`0995a0374205a7116b59aeb5ec20a468de22458a24066a9f0f5d71e32f07506e`
- 当前执行方式：Human-mediated Reviewer/Executor
- 最后更新：`2026-09-14`

本 Runtime 是 foundation_v1 的详细进度权威来源。全局 Runtime 只保留当前 task 指针与高层
transition。本文件不包含 `1PCLOOP_RUNTIME_STATE` machine block；现有 runner 禁止 framework
repo 与 target repo 重叠，foundation_v1 的状态由独立 Reviewer verdict 和 Human-authorized
治理提交推进。

## 2. Completed / Done

### A. 上一阶段关闭

状态：`COMPLETED`

```text
P6.1–P6.4 independently accepted
P6 accepted / phase closed
```

Evidence locator：

- `1PCloop/docs/miniloop_runtime.md`
- commit `2bc90d6500104bbb7e5d0b16ce82887974dce69e`

当前语义：foundation_v1 继承 P4–P6 已接受能力，不重开或重写其 evidence。

### B. 2026-09-12 post-P6 smoke observation

状态：

```text
COMPLETED OBSERVATION
SAFETY BEHAVIOR PASSED
END-TO-END RUN FAILED CLOSED
USABILITY GAP DISCOVERED
```

结果：真实 Reviewer→Executor→Reviewer 三个 Codex turn 均成功，target mutation 与独立
Reviewer `ACCEPT` 已形成；Reviewer verdict 同时携带两个机械不合法的非绝对 evidence
locator，orchestrator 因此以
`file/artifact evidence requires an absolute locator` 拒绝 authoritative transition。
workload Runtime 未推进，logical outcome 为 `FAILED_CLOSED`；随后 summary commit 与
framework-only push 成功。最终 checkpoint control state `FRAMEWORK_EVIDENCE_PUSHED` 只表示
evidence publication 完成，不表示 logical success。

Durable evidence locator：

- `1PCloop/evidence-summaries/post-p6-foundation-smoke-20260912.md`
- raw root：`/tmp/1pcloop-post-p6-smoke.jomR1L`

### C. F1 — Reviewer verdict 机械纠错与明确终态输出

状态：`ACCEPTED AFTER REJECT → NARROW REPAIR → INDEPENDENT RE-REVIEW`

结果：

- implementation commit `d57c1c146be9ea998572e3d09c923c4e9a77c517` 建立 typed/default-deny
  correction 状态机、同 Reviewer thread 最多两次纠错、Executor 不重跑、evidence-byte guard、
  crash/restart 幂等和三层最终状态；
- 独立 Reviewer 第一次审核发现公开 `FINAL_RESULT` 可被未编码换行伪造字段，因此形成
  `REJECTED — NARROW REPAIR REQUIRED`；拒绝记录 commit 为
  `83b23eaa841210b480013cdae9ad289c150603b4`；
- repair commit `0adf4e083b002dad8ccff226afb96a9b20210bdb` 引入统一 public-result
  boundary、单行 JSON scalar、`512` 字符 public reason 上限、固定 unclassified reason、
  local-only `internal_diagnostic`、duplicate-key 去回显和原始 Reviewer locator 提示修正；
- correction 状态机、16 个可纠正 code、两次上限、同线程 resume、Executor/transition/
  summary/commit/push 幂等边界在 repair 中保持不变。

独立 re-review evidence：

- Executor repair focused suite：`20 / 20`，`40.399s`；完整
  ResourceWarning-strict regression：`90 / 90`，`136.602s`；
- Reviewer 独立复跑 focused suite：`20 / 20`，`35.718s`；完整
  ResourceWarning-strict regression：`90 / 90`，`134.455s`；
- Reviewer 重新执行 CR/LF、Unicode control、伪造字段和恶意 duplicate-key 最小复现，确认
  固定字段各占一个物理行、所有字符串可作为 JSON scalar 解析，未出现额外字段或 key 泄漏；
- Python 3.9 compilation/import、`git diff --check`、提交范围、远端同步和 clean worktree 均通过；
- 未运行 real-service smoke；该验证仍属于 F7，不阻塞 F1 deterministic acceptance。

当前语义：foundation_v1 的 AC-01 已满足；AC-02 中最终 logical outcome、Runtime transition、
evidence publication 的独立表达已满足。F2 继续完成持续计时、live status 和 structured event
基础。F1 的首次 REJECT 与 repair 历史继续保留在 §8，不因最终 ACCEPT 被删除。

## 3. Active Step

### F2 / Step 2 — terminal timer、live status 与 structured progress event

#### Objective

在不改变 Reviewer/Executor/Runtime/evidence 权威语义的前提下，为 mutation loop 建立同源的
机器可读 progress event、当前 live status snapshot 和面向终端的持续计时显示。运行者必须能
看到整次 run elapsed、当前 stage elapsed、Codex turn timeout remaining、last activity、cycle、
role/state，以及 F1 已建立的最终三层结果；未来 CLI/TUI 必须能够消费同一 structured source，
而不是解析自然语言或终端文本。

#### Inputs 及固定 identity

- Static：`1PCloop/workloads/foundation_v1/workload_static.md`，SHA-256
  `0995a0374205a7116b59aeb5ec20a468de22458a24066a9f0f5d71e32f07506e`；
- F1 accepted implementation：commits `d57c1c146be9ea998572e3d09c923c4e9a77c517`、
  `0adf4e083b002dad8ccff226afb96a9b20210bdb`；
- runner：`1PCloop/scripts/run_mutation_loop.py`；
- existing process/manifest/checkpoint/final-result formats and P4–F1 regression；
- post-P6 timing observation：
  `1PCloop/evidence-summaries/post-p6-foundation-smoke-20260912.md`。

#### Permitted changes

- `1PCloop/scripts/run_mutation_loop.py`；
- 与 progress event/status projection 直接相关的必要新 helper；
- `1PCloop/tests/test_run_mutation_loop.py` 和必要的新 F2 专项 test；
- F1/P6 regression test 只能为兼容性做最小调整；
- `1PCloop/README.md` 中与 F2 operator behavior 直接相关的说明。

#### Prohibited changes

- 全局和 task-local Static/Runtime；
- `1PCloop/schemas/**`、roles、requirements；
- F1 correction/error taxonomy/public-result semantics；
- P4 transport、Runtime transition、evidence finalization 与 Git push semantics；
- closed workloads、历史 runs/evidence、外部 Tools 模板和 target history/remote；
- F3–F8 implementation、P7、真实 Codex smoke、self-hosting 或 concurrency 功能。

#### Required evidence

- versioned structured progress-event contract 与实际 JSONL/fixture locator；
- live status snapshot，能从 structured state 得到当前 run/stage/turn 信息；
- deterministic fake-clock tests，覆盖 normal run、long turn、timeout、resume、clock anomaly 和终态；
- terminal output 与 structured event/status 同源的 evidence；
- no-payload/no-secret regression；
- 完整 ResourceWarning-strict regression、README diff、implementation commit 和精确文件列表。

#### Acceptance criteria

1. 每个 progress event 使用版本化、固定字段的 machine-readable envelope；事件内容不得来自
   peer_message 自由文本语义。
2. live status 至少包含 run ID、cycle、role、control state、run elapsed、stage elapsed、timeout
   remaining、last activity 和最终三层状态；不可用字段显式为 `null`，不得伪造 `0`。
3. active Codex turn 的 run/stage elapsed 单调不减，timeout remaining 不为负；非 Codex stage
   不伪造 timeout remaining。
4. crash/resume 后计时和 event sequence 可机械重建，不因进程重启倒退、重复已有事件或把旧
   heartbeat 当成新 activity。
5. terminal renderer 只消费 structured event/status；TTY 与非 TTY 输出都不得泄露 prompt、
   peer payload、secret、完整命令输出或隐藏 reasoning。
6. 高频 Codex tool event 必须有明确节流/聚合边界，关键 state transition、error 和 final result
   不得丢失。
7. F1 `FINAL_RESULT` 的字段、JSON-scalar 编码、public/internal reason 分离和 publication/logical
   distinction 保持兼容。
8. 本步只建立 status 数据与 live rendering；F3 才实现 `status`/`resume` 等用户子命令，F6 才
   实现交互式 TUI。
9. 现有合法 ACCEPT、REJECT、HUMAN_GATE、correction、restart 与 P4–F1 regression 不回归。

#### Tests

- injectable fake clock 验证 run/stage elapsed、timeout remaining 和 last activity；
- state/role/cycle transition 事件顺序与稳定 sequence identity；
- restart 前后 elapsed/sequence/status reconstruction；
- timeout、process failure、Human Gate、corrected ACCEPT、publication failure/resume；
- control-character、超长字段和 raw payload 不进入公开 event/terminal；
- TTY/non-TTY renderer 的 bounded 输出；
- F1 focused regression 与完整 ResourceWarning-strict regression。

F2 不运行真实 Codex service；完整 post-foundation real-service smoke 留到 F7。

#### Stop conditions / Human Gate

- 需要改变 Static、F1 public-result contract 或现有 authoritative state semantics；
- 无法在 restart 后确定 elapsed/event identity 而只能猜测；
- UI 需求迫使提前实现 F3 CLI 或 F6 TUI；
- 需要记录 raw payload、credential 或 hidden reasoning；
- 出现 framework/target overlap、自托管权限、并发或破坏性 Git 需求。

#### Executor report format

```text
F2 implementation status: IMPLEMENTED / BLOCKED
branch / implementation commit / parent / working-tree state
changed files
progress event schema and storage
run/stage/timeout/last-activity semantics
resume/sequence/idempotence evidence
terminal/status projection evidence
focused tests, F1 regression and full strict regression
known limitations
recommended Runtime evidence summary
```

Executor 不得宣告 F2 accepted，也不得推进本 Runtime。

## 4. Queued

| Step | Deliverable | 状态 |
| --- | --- | --- |
| F3 / Step 3 | config + doctor/preflight/run/resume/status/inspect CLI | `QUEUED` |
| F4 / Step 4 | 默认中文 Static/Runtime Prompt 模板规范化 | `QUEUED` |
| F5 / Step 5 | runner 模块化和 Human Gate UX | `QUEUED` |
| F6 / Step 6 | 本地 TUI | `QUEUED` |
| F7 / Step 7 | post-foundation real-service smoke | `QUEUED` |
| F8 / Step 8 | GUI/治理压缩/evidence lifecycle 的 evidence-driven 决策 | `QUEUED` |

顶层映射固定为：`F1 = Step 1`、`F2 = Step 2`、`F3 = Step 3`、`F4 = Step 4`、
`F5 = Step 5`、`F6 = Step 6`、`F7 = Step 7`、`F8 = Step 8`。

## 5. Blockers and Human Decision Gates

- 当前无阻止 F2 开始的 blocker。
- 当前 framework/target overlap 禁止使实现采用 Human-mediated workflow；这是已知
  self-hosting limitation，不是 F2 blocker。

## 6. Pending Tasks — Non-blocking Blocks

当前顶层 Step：`2`

| ID | 非阻塞性 block | 引入于 | 截止 Step | 剩余安全迁移次数 | 当前状态 | 关闭条件与所需 evidence |
| --- | --- | --- | --- | --- | --- | --- |
| PT-01 | 默认中文 Prompt 模板尚未规范化 | Step 1 | Step 5 | 2 | `OPEN_NON_BLOCKING` | F4 commit 记录两个固定 Tools hash、模板测试并获独立 Reviewer acceptance；进入 F5 前必须关闭 |
| PT-02 | raw evidence 长期清理/保留策略未确定 | Step 1 | +∞ | +∞ | `PERMANENTLY_NON_BLOCKING` | F8 或未来 Human decision 记录 retention policy 与实际使用 evidence |

### Pending Gate Check

- 下一顶层 Step：`Step 3 / F3`
- 激活前必须关闭的 Pending Task：无
- Gate verdict：`CLEAR`
- Prompt 模板 deadline：必须在进入 `Step 5 / F5` 前由 F4 acceptance 关闭 PT-01。
- GUI：仅在 F8 基于使用 evidence 决定；当前不是已承诺交付，也不是 F2 blocker。

## 7. State Transition

Foundation activation transition（`2026-09-12` 历史状态）：

- Previous state：P6 `ACCEPTED / PHASE CLOSED`；P7 曾短暂作为下一 Active Step。
- Triggering decision：Human Owner `2026-09-12` 决定暂停 P7 和 paper/research-driven 路线，
  优先建立 engineering foundation。
- State at activation：foundation_v1 `ACTIVE`；F1 为唯一 Active Step；P7
  `PAUSED / NOT ACTIVE`。
- Meaning：保留 P4–P6 accepted evidence，以 task-local governance 开展日常可用性、诊断、恢复
  和维护工作。
- Transition authorized by：Human Owner。

Latest step transition：

- Previous step state：F1 `REJECTED — NARROW REPAIR REQUIRED`；
- Triggering evidence：repair commit `0adf4e083b002dad8ccff226afb96a9b20210bdb`、
  Reviewer independent re-review、focused `20 / 20` 与完整 strict `90 / 90`；
- Verdict：F1 `ACCEPTED AFTER RE-REVIEW`；
- Current step：F2 / Step 2 `ACTIVE / NOT EVALUATED`；
- Pending countdown：PT-01 从 `3` 重算为 `2`，仍为 `OPEN_NON_BLOCKING`；PT-02 保持 `+∞`；
- Transition authorized by：独立 Reviewer verdict 与 Human Owner 本次收尾授权。

## 8. Independent Review

- 审核对象：commit `d57c1c146be9ea998572e3d09c923c4e9a77c517` —
  `Add recoverable Reviewer verdict correction`；
- 实现范围：`1PCloop/scripts/run_mutation_loop.py`、`1PCloop/README.md`、
  `1PCloop/tests/test_run_mutation_loop.py` 和新增
  `1PCloop/tests/test_verdict_correction.py`；
- 独立 evidence access：`SATISFIED`；Reviewer 直接检查 commit/diff、错误分类、correction
  状态机、checkpoint/recovery、终态输出和测试；
- 独立 verdict formation：`SATISFIED`；
- 独立 evidence-sufficiency judgment：`SATISFIED FOR REJECTION`；
- Executor focused suite：`16 / 16`，`38.038s`；完整 ResourceWarning-strict regression：
  `86 / 86`，`125.269s`；
- Reviewer 独立复跑 focused suite：`16 / 16`，`34.925s`；完整
  ResourceWarning-strict regression：`86 / 86`，`129.677s`；
- correction 主路径、同 Reviewer thread、最多两次、Executor 不重跑、实际
  target/governance/framework/evidence 漂移 default-deny，以及 transition/summary/push
  recovery 均未发现阻塞问题。

### 2026-09-13 Reviewer verdict：`REJECTED — NARROW REPAIR REQUIRED`

拒绝原因不是 correction 状态机，而是 F1 新增的公开 `FINAL_RESULT` 未真正满足
“稳定、单行、bounded、不泄露 raw payload”的合同：

- `emit_final_result` 直接以 `key=value` 打印未经单行编码的字符串值；
- 未分类异常进入 `logical_outcome.reason` 时没有公开长度限制或换行清理；
- `strict_json` 的 duplicate-key 错误会原样包含由输入控制的 key 名；
- 因此恶意或异常 reason 可以插入额外换行，伪造后续 `error_code`、`run_root` 等字段。

Reviewer 的最小复现：

```text
reason input = first line\nerror_code=FORGED\nrun_root=/forged

observed FINAL_RESULT fragment:
reason=first line
error_code=FORGED
run_root=/forged
error_code=UNCLASSIFIED_CONTROL_FAILURE
run_root=/real
```

同一检查还证明 duplicate JSON key 名
`SECRET\nerror_code=FORGED` 会进入当前 exception text。该行为允许终端字段注入，并与 README
记录的 `reason=<bounded reason>` 冲突。测试全部通过不能覆盖这个未测试边界。

Required narrow repair：

1. 在 `final_result` 构造边界生成明确长度上限的单行 public reason；
2. 未分类异常使用固定通用 public reason，详细异常只保留在 Git-ignored local raw evidence；
3. 对所有公开字符串值进行不会产生新记录行的稳定编码，禁止 CR/LF 字段注入；
4. `strict_json` 的公开错误不得回显任意 duplicate-key 名称；
5. 增加 multiline、CR/LF、超长 reason、恶意 duplicate-key 和 forged-field regression；
6. 重新运行 F1 focused suite 与完整 ResourceWarning-strict regression。

该次 REJECT verdict 形成时的状态：F1 保持唯一 Active Step；F2 不激活；Pending Task
倒计时不变化；Static 不变。该状态随后被下方 `2026-09-14` re-review ACCEPT supersede。

### Self-application interpretation

本次是 1PCloop 核心治理思想用于实现 1PCloop 自身的直接 evidence：task-local
Static/Runtime 编译 F1，Executor 提交实现，独立 Reviewer 直接检查 evidence 并形成明确
`REJECTED`，随后由 Runtime 保存 repair 原因和当前有效状态。由于现有 mutation runner 禁止
framework repo 与 target repo 重叠，该 self-application 仍是 Human-mediated
Reviewer/Executor workflow，不表示 runner 已经自动 self-host 或自动修改/验收自身。

### 2026-09-14 Independent re-review：`ACCEPTED`

审核对象：repair commit `0adf4e083b002dad8ccff226afb96a9b20210bdb`，parent 为保存首次
REJECT 的 Runtime commit `83b23eaa841210b480013cdae9ad289c150603b4`。

Acceptance mapping：

| Criterion | Direct evidence | Sufficiency judgment | Result |
| --- | --- | --- | --- |
| public result 单行且 bounded | central builder、JSON scalar、512 字符上限及 adversarial tests | CR/LF、Unicode control、超长字段和伪造 key 均被直接覆盖 | PASS |
| public/internal diagnostic 分离 | checkpoint/manifest fixture 与 unclassified secret test | public 使用固定 reason，完整异常只留 local `internal_diagnostic` | PASS |
| duplicate-key 不泄漏 | malicious duplicate-key direct test | 继续拒绝重复 key，但不回显输入控制 key | PASS |
| F1 correction 不回归 | 既有 correction/recovery tests 与完整 strict suite | 同线程、两次上限、Executor 不重跑及 transition/publication 幂等保持通过 | PASS |
| operator contract | README diff 与原始 Reviewer prompt test | 输出格式、locator 规则和 F2 边界与实现一致 | PASS |

- 独立 evidence access：`SATISFIED`；
- 独立 verdict formation：`SATISFIED`；
- 独立 evidence-sufficiency judgment：`SATISFIED`；
- Reviewer verdict：`ACCEPTED`；
- Review limitation：未运行真实 Codex smoke，按 Static 留至 F7；不阻塞本步 deterministic
  acceptance。

本次自然发生的 REJECT → narrow repair → independent re-review → ACCEPT 是 1PCloop 核心治理
方法用于实现自身的直接 evidence，但不是人为 defect injection，也不重新激活 P7。

foundation_v1 整体状态仍为 `ACTIVE`；F1 已完成，F2 为唯一 Active Step。

## 9. Next Direction

只执行 F2。F1 已冻结为 accepted evidence；F3–F8 保持 queued。不得提前实现 config/CLI
subcommands、Prompt 模板、Human Gate UX、TUI、GUI 或 real-service smoke，也不得启动 P7。
F2 实现完成后停止于 `AWAITING INDEPENDENT REVIEW`。
