# foundation_v1 — Runtime 当前权威状态

## 1. Current Status

- Task ID：`foundation_v1`
- 状态：`ACTIVE`
- 当前 verdict：`REJECTED — NARROW REPAIR REQUIRED`
- 最近接受：`F2 — ACCEPTED AFTER REJECT → NARROW REPAIR → RE-REVIEW`
- 唯一 Active Step：`F3 — workload config 与 doctor/preflight/run/resume/status/inspect CLI`
- 当前顶层 Step：`Step 3`
- Static identity：
  - path：`1PCloop/workloads/foundation_v1/workload_static.md`
  - SHA-256：`0995a0374205a7116b59aeb5ec20a468de22458a24066a9f0f5d71e32f07506e`
- 当前执行方式：Human-mediated Reviewer/Executor
- 最后更新：`2026-09-15`

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

### D. F2 — terminal timer、live status 与 structured progress event

状态：`ACCEPTED AFTER REJECT → NARROW REPAIR → INDEPENDENT RE-REVIEW`

结果：

- implementation commit `69cb4c13e1313fd88b15de93781d65400c2b5e71` 建立 versioned
  `control-events.jsonl`、atomic `live-status.json`、active-time run/stage/timeout/last-activity
  semantics、tool aggregation 和 structured terminal renderer；
- 独立 Reviewer 第一次审核发现 checkpoint cursor 后的完整 suffix 只验证部分 projection，且
  raw pump 的 legacy 输出绕过 structured tool throttle，因此形成 `REJECTED — NARROW REPAIR
  REQUIRED`；拒绝记录 commit 为 `a0776692a0507d238b3a2eb95a880f014db4844b`；
- repair commit `54ccf66a1c95843ae680e0c8f50ed98c5df6c0a5` 对完整 suffix 固定验证
  run/state/cycle/target/logical/runtime/publication projection，并为合法 state/turn/activity/finish
  suffix 建立显式 lifecycle；raw pump 同时改为服从 structured recorder 的节流决策；
- observation-disabled 路径保留 bounded、无 payload 的 `CODEX_FALLBACK`，F1 `FINAL_RESULT`
  和 authoritative transition semantics 保持不变。

独立 re-review evidence：

- Executor repair F2 focused：`24 / 24`，`7.666s`；F1 regression：`20 / 20`，
  `36.757s`；完整 ResourceWarning-strict regression：`114 / 114`，`141.310s`；
- Reviewer 独立复跑 F2 focused：`24 / 24`，`7.109s`；F1 regression：`20 / 20`，
  `35.739s`；完整 ResourceWarning-strict regression：`114 / 114`，`142.350s`；
- Reviewer 使用与首次 REJECT 相同的 rehashed forged suffix 重跑，现于
  `progress suffix cycle conflicts with checkpoint projection` fail closed；
- runner pump integration 直接保存 `63` 行 raw event，其中 `60` 条 tool activity 只形成首次与
  最终两条 structured tool event；正常 structured 路径不再重复 legacy machine/tool 输出；
- Python 3.9 compilation/import、`git diff --check`、提交范围、远端同步和 clean worktree 均通过；
- 未运行 real-service smoke；该验证仍属于 F7，不阻塞 F2 deterministic acceptance。

当前语义：foundation_v1 的 AC-04、AC-05 已满足；F2 observation 是可重建投影而不是第二份
Runtime。Event SHA-256 是 canonical byte identity，不是 keyed authority；checkpoint projection
仍是 resume reconciliation anchor。F2 的首次 REJECT 与 repair 历史继续保留在 §8。

## 3. Active Step

### F3 / Step 3 — workload config 与 doctor/preflight/run/resume/status/inspect CLI

#### Objective

在保留现有长参数 invocation 向后兼容的前提下，为 Human operator 提供一个版本化、可验证的
workload config 和统一命令入口，使 doctor、preflight、run、resume、status、inspect 使用同一
配置与状态 identity。Resume/status 不应要求用户重新拼接十多个参数；所有命令仍必须复用现有
preflight、checkpoint、F1 final result 和 F2 structured status/event，而不是创建第二套控制逻辑。

#### Inputs 及固定 identity

- Static：`1PCloop/workloads/foundation_v1/workload_static.md`，SHA-256
  `0995a0374205a7116b59aeb5ec20a468de22458a24066a9f0f5d71e32f07506e`；
- F1 accepted final-result/correction contracts；
- F2 accepted progress/status contracts：commits
  `69cb4c13e1313fd88b15de93781d65400c2b5e71`、
  `54ccf66a1c95843ae680e0c8f50ed98c5df6c0a5`；
- `1PCloop/scripts/run_mutation_loop.py`、`progress_status.py`、现有 README 和 test suites。

#### Permitted changes

- 现有 mutation runner 的 CLI/arg normalization；
- 必要的新 CLI/config/status helper 和入口脚本；
- workload config 示例或模板，但不得包含 credential；
- 与 F3 直接相关的 tests；
- F1/F2/P6 tests 只能做必要兼容调整；
- `1PCloop/README.md`、对应中文 README 中与实际 F3 operator 命令直接相关的说明。

#### Prohibited changes

- 全局和 task-local Static/Runtime；
- `1PCloop/schemas/**`、roles、requirements；
- F1 correction/public-result、F2 event/timing/reconciliation semantics；
- P4 transport、Runtime transition、evidence finalization 和 Git push semantics；
- closed workloads、历史 runs/evidence、外部 Tools 模板和 target history/remote；
- F4–F8 implementation、P7、真实 Codex smoke、TUI/GUI、self-hosting 或 concurrency 功能。

#### Required evidence

- versioned workload config contract、canonical resolved identity/hash 和 strict validation tests；
- doctor/preflight/run/resume/status/inspect 的 CLI integration evidence；
- resume/status 使用已保存 config/checkpoint identity、不要求重拼全部原始参数的测试；
- read-only command 无 Agent invocation、无 repository mutation 的 evidence；
- backward-compatible legacy CLI tests；
- privacy/path/unknown-field/duplicate-key/stale-config negative tests；
- 完整 ResourceWarning-strict regression、双语 operator docs、commit 和精确文件列表。

#### Acceptance criteria

1. Workload config 使用版本化、固定字段和 strict duplicate/unknown-field validation；相对路径
   按 config 文件目录确定性解析，resolved config identity/hash 写入或绑定 checkpoint。
2. Config 不包含或复制 auth、token、credential、完整 profile state；角色 profile 只记录获授权
   路径，仍要求 Reviewer/Executor identity 不同。
3. `doctor` 只读检查 Python dependency、Codex binary/version、profile、Git、framework remote、
   schema 和本地 ignore/storage prerequisite，不创建 run 或调用 Agent。
4. `preflight` 从 config 调用现有 preflight，输出 machine-readable 结果，不创建 mutation evidence。
5. `run` 从 config 编译成现有 runner 参数并执行当前 orchestrator，不复制状态机。
6. `resume` 通过 config/workload/run identity 定位 checkpoint，验证保存的 resolved configuration，
   不要求重输 target/governance/profile 等全部参数；任何 drift/override 冲突 fail closed。
7. `status` 只读投影 checkpoint、F2 live status/event 和 F1 final result，明确显示 control state、
   timers、last activity、logical/runtime/publication、observation availability 和下一安全动作；不从
   peer_message 推断语义。
8. `inspect` 只读定位并机械验证 run manifest、event/status、summary/checkpoint/commit identity；
   缺失 local raw evidence 必须明确报告 unavailable，不伪造成功。
9. Legacy `run_mutation_loop.py` 参数入口继续工作；新入口不能改变原有 default-deny、Runtime
   capability、correction、timing、event、transition 或 publication 语义。
10. F3 不解决 Human Gate、不做交互式选择、不实现 TUI/GUI；这些仍属于后续阶段。

#### Tests

- config parse/canonicalization/hash、relative path、duplicate/unknown/missing/invalid field；
- doctor success/failure matrix 且无 Agent/run side effect；
- preflight/run 参数等价性和 legacy CLI compatibility；
- resume 最小输入、config drift、错误 workload/run、缺失/旧 checkpoint；
- status 在 running、Human Gate、FAILED_CLOSED、publication failure、terminal complete、observation
  unavailable 和 raw-missing 情况下的 deterministic projection；
- inspect 正常、tampered、partial-tail、缺失 local artifact 和远端 identity 情况；
- stdout 使用稳定 JSON/安全文本，不泄露 auth、peer payload 或 internal diagnostic；
- F1、F2 focused regression 与完整 ResourceWarning-strict regression。

F3 不运行真实 Codex service；完整 post-foundation real-service smoke 留到 F7。

#### Stop conditions / Human Gate

- 需要改变 Static、Runtime、F1/F2 或 authoritative transition semantics；
- 无法仅由 config/workload identity 安全定位唯一 checkpoint；
- resume 需要猜测已保存配置或自动接受 drift；
- 需要 credential、GUI/TUI、Human Gate decision、self-hosting、并发或破坏性 Git action；
- 新入口无法复用现有 runner 而必须复制控制状态机。

#### Executor report format

```text
F3 implementation status: IMPLEMENTED / BLOCKED
branch / implementation commit / parent / working-tree state
changed files
config schema/canonical identity and path semantics
doctor/preflight/run/resume/status/inspect behavior
read-only/no-Agent/no-mutation evidence
legacy compatibility and F1/F2 regression
focused tests and full strict regression
known limitations
recommended Runtime evidence summary
```

Executor 不得宣告 F3 accepted，也不得推进本 Runtime。

## 4. Queued

| Step | Deliverable | 状态 |
| --- | --- | --- |
| F4 / Step 4 | 默认中文 Static/Runtime Prompt 模板规范化 | `QUEUED` |
| F5 / Step 5 | runner 模块化和 Human Gate UX | `QUEUED` |
| F6 / Step 6 | 本地 TUI | `QUEUED` |
| F7 / Step 7 | post-foundation real-service smoke | `QUEUED` |
| F8 / Step 8 | GUI/治理压缩/evidence lifecycle 的 evidence-driven 决策 | `QUEUED` |

顶层映射固定为：`F1 = Step 1`、`F2 = Step 2`、`F3 = Step 3`、`F4 = Step 4`、
`F5 = Step 5`、`F6 = Step 6`、`F7 = Step 7`、`F8 = Step 8`。

## 5. Blockers and Human Decision Gates

- F3 已实现但存在一个阻止 acceptance 的跨阶段 evidence-supersession blocker，详见 §8；无需
  Human 决策，继续由 Executor 在 F3 inspect 范围内修复。
- 当前 framework/target overlap 禁止使实现采用 Human-mediated workflow；这是已知
  self-hosting limitation，不是 F3 blocker。

## 6. Pending Tasks — Non-blocking Blocks

当前顶层 Step：`3`

| ID | 非阻塞性 block | 引入于 | 截止 Step | 剩余安全迁移次数 | 当前状态 | 关闭条件与所需 evidence |
| --- | --- | --- | --- | --- | --- | --- |
| PT-01 | 默认中文 Prompt 模板尚未规范化 | Step 1 | Step 5 | 1 | `OPEN_NON_BLOCKING` | F4 commit 记录两个固定 Tools hash、模板测试并获独立 Reviewer acceptance；进入 F5 前必须关闭 |
| PT-02 | raw evidence 长期清理/保留策略未确定 | Step 1 | +∞ | +∞ | `PERMANENTLY_NON_BLOCKING` | F8 或未来 Human decision 记录 retention policy 与实际使用 evidence |

### Pending Gate Check

- 下一顶层 Step：`Step 4 / F4`
- 激活前必须关闭的 Pending Task：无
- Gate verdict：`CLEAR`
- Prompt 模板 deadline：必须在进入 `Step 5 / F5` 前由 F4 acceptance 关闭 PT-01。
- GUI：仅在 F8 基于使用 evidence 决定；当前不是已承诺交付，也不是 F3 blocker。

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

F1 → F2 transition（历史状态）：

- Previous step state：F1 `REJECTED — NARROW REPAIR REQUIRED`；
- Triggering evidence：repair commit `0adf4e083b002dad8ccff226afb96a9b20210bdb`、
  Reviewer independent re-review、focused `20 / 20` 与完整 strict `90 / 90`；
- Verdict：F1 `ACCEPTED AFTER RE-REVIEW`；
- Current step：F2 / Step 2 `ACTIVE / NOT EVALUATED`；
- Pending countdown：PT-01 从 `3` 重算为 `2`，仍为 `OPEN_NON_BLOCKING`；PT-02 保持 `+∞`；
- Transition authorized by：独立 Reviewer verdict 与 Human Owner 本次收尾授权。

Latest step transition：

- Previous step state：F2 `REJECTED — NARROW REPAIR REQUIRED`；
- Triggering evidence：repair commit `54ccf66a1c95843ae680e0c8f50ed98c5df6c0a5`、
  Reviewer independent re-review、F2 focused `24 / 24`、F1 `20 / 20` 与完整 strict
  `114 / 114`；
- Verdict：F2 `ACCEPTED AFTER RE-REVIEW`；
- Current step：F3 / Step 3 `ACTIVE / NOT EVALUATED`；
- Pending countdown：PT-01 从 `2` 重算为 `1`，仍为 `OPEN_NON_BLOCKING`；PT-02 保持 `+∞`；
- Transition authorized by：独立 Reviewer verdict 与 Human Owner 的自动收尾授权。

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

该次 F1 closure 后 foundation_v1 仍为 `ACTIVE`；当时 F1 已完成，F2 成为唯一 Active Step。

### 2026-09-15 F2 independent review：`REJECTED — NARROW REPAIR REQUIRED`

审核对象：commit `69cb4c13e1313fd88b15de93781d65400c2b5e71` —
`Add structured live progress status`，parent
`330ebb6104d0512ad6cba8cb45ab8593c4141dee`。该 parent 与此前 F2 handoff 基线之间的
README 系列提交 `f2d8948`、`c449fe5`、`330ebb6` 已由 Human Owner 明确授权，不构成本次
F2 执行纪律或代码审核问题。

Executor implementation/evidence：

- 新增 `1PCloop/scripts/progress_status.py` 和 `1PCloop/tests/test_progress_status.py`，修改
  mutation runner、README 及必要兼容测试；未修改 Static/Runtime/schema/role/requirements、
  `p63_evidence.py`、closed workload 或历史 evidence；
- 建立 schema version `1`、18 个固定字段、13 类事件、canonical SHA-256 event identity、
  `control-events.jsonl`、atomic `live-status.json`、active-time timing、tool aggregation 和
  `PROGRESS` renderer；
- Executor F2 focused suite：`18 / 18`，`6.453s`；F1 regression：`20 / 20`，
  `33.850s`；完整 ResourceWarning-strict regression：`108 / 108`，`129.377s`；
- Reviewer 独立复跑 F2 focused suite：`18 / 18`，`7.041s`；完整
  ResourceWarning-strict regression：`108 / 108`，`146.872s`；
- 上述测试全绿，但未覆盖以下两项 acceptance-critical blind spot，因此不足以支持 F2 ACCEPT。

#### Finding 1 — 完整 post-checkpoint suffix 未验证全部状态投影

`ProgressStatus._resume` 对 checkpoint cursor 之后的完整、newline-terminated event 只检查
`run_id` 和 `control_state`。Reviewer 构造了 sequence 连续、schema 合法且重新计算正确
`event_id` 的完整 suffix；它保持 `control_state=REVIEW_PENDING`，但写入：

```text
cycle=99
target_head=bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb
logical_outcome=RUNTIME_TRANSITION_COMMITTED
runtime_transition=APPLIED
evidence_publication=PUSHED
```

当前 resume 接受该完整行，并在其后追加恢复为 checkpoint projection 的 `run_resumed` event。
因此同一 journal 会永久同时保存一条伪造成功记录和一条真实恢复记录。这与 README 和 F2
合同中的“完整 event/checkpoint identity conflict 必须 fail closed”不符，也使未来 F3/F6
consumer 不能把已 reconcile journal 当作一致观察源。

Required repair：

1. 即使 cursor 位于尾部，也验证 `checkpoint_progress.control_state == checkpoint_state`；
2. 对 cursor 后 suffix 验证 immutable projection：至少 `run_id`、`control_state`、`cycle`、
   `target_head`、`logical_outcome`、`runtime_transition`、`evidence_publication` 必须与 checkpoint
   一致；
3. 对 run/stage elapsed anchor、event type、role、timeout 和 activity 定义合法的 suffix 演进；
4. 保留合法 state-entered、heartbeat、Codex/tool activity、turn start/finish 和 append-after-
   checkpoint crash；
5. 只有不以 newline 结束的 partial tail 可以截除，完整冲突行不得自动删除。

#### Finding 2 — legacy terminal 输出绕过 tool-event throttle

raw Codex pump 先调用 structured `tool_activity`，但无论该调用是否因 throttle 返回 `None`，
随后仍对每个 raw tool item 执行 legacy `describe_progress_event` + `emit_progress`。因此 structured
journal 虽然被节流，真实终端仍逐条刷屏，并同时存在 structured 与 legacy 两条显示路径；这与
“terminal renderer 消费 structured event/status”和 README 的 tool activity 节流说明不符。

Required repair：

1. structured observation 正常时，只由 structured recorder 的 emit/throttle 决策产生
   Codex/tool terminal projection；
2. throttled `tool_activity` 返回 `None` 时不得输出 legacy tool line；
3. structured event 已渲染时不得再输出重复 legacy line；
4. observation layer 不可用时可保留 bounded、无 payload 且有节流的 legacy fallback；
5. 增加通过实际 runner pump 输入大量 raw tool events 的 integration test，不能只直接测试
   `ProgressStatus.tool_activity()`。

Independent review verdict：

- 独立 evidence access：`SATISFIED`；
- 独立 verdict formation：`SATISFIED`；
- 独立 evidence-sufficiency judgment：`SATISFIED FOR REJECTION`；
- verdict：`REJECTED — NARROW REPAIR REQUIRED`；
- 该次 REJECT 形成时的状态：F2 保持唯一 Active Step，F3 不激活，PT-01 倒计时保持 `2`，
  PT-02 保持 `+∞`；该状态随后由下方 F2 re-review ACCEPT supersede；
- 本次是 1PCloop 核心 Reviewer/Executor 治理思想用于实现自身的又一次自然 REJECT evidence，
  不是 P7 defect injection，也不重新激活 P7。

### 2026-09-15 F2 independent re-review：`ACCEPTED`

审核对象：repair commit `54ccf66a1c95843ae680e0c8f50ed98c5df6c0a5`，parent 为保存 F2
首次 REJECT 的 Runtime commit `a0776692a0507d238b3a2eb95a880f014db4844b`。

Acceptance mapping：

| Criterion | Direct evidence | Sufficiency judgment | Result |
| --- | --- | --- | --- |
| suffix immutable projection | `validate_checkpoint_suffix`、rehashed conflict tests及 Reviewer 原复现 | 七项 checkpoint projection 均固定验证，原 forged suffix 在 cycle mismatch 处 fail closed | PASS |
| suffix lifecycle/recovery | state/heartbeat/Codex/tool/turn/append-crash/repeated-resume/partial-tail tests | 合法 suffix 保留，完整冲突行不删除、不接受 | PASS |
| runner-level throttling | 63-line pump fixture，含60条 tool activity | raw bytes 全保留；structured tool event 仅首次与最终聚合，无正常路径 legacy duplication | PASS |
| observation fallback/privacy | disabled-observation integration test | fallback 仅固定 category/kind/count，无命令、参数、输出、peer 或 secret | PASS |
| F1/P6 compatibility | F1 focused 与完整 strict suite | FINAL_RESULT、correction、transition、summary和publication语义未回归 | PASS |

- 独立 F2 focused：`24 / 24`，`7.109s`；
- 独立 F1 regression：`20 / 20`，`35.739s`；
- 独立完整 ResourceWarning-strict regression：`114 / 114`，`142.350s`；
- Python 3.9 compilation/import、`git diff --check`、提交范围、远端和 clean worktree：通过；
- 独立 evidence access：`SATISFIED`；
- 独立 verdict formation：`SATISFIED`；
- 独立 evidence-sufficiency judgment：`SATISFIED`；
- Reviewer verdict：`ACCEPTED`；
- Review limitation：未运行真实 Codex smoke，按 Static 留至 F7；event SHA-256 只表示 canonical
  byte identity，checkpoint projection 仍是 reconciliation anchor。两者均不阻塞 F2。

本次 F2 的自然 REJECT → narrow repair → re-review → ACCEPT 继续构成 1PCloop 核心治理方法
用于实现自身的 evidence，不是 P7 fault injection。

### 2026-09-15 F3 independent review：`REJECTED — NARROW REPAIR REQUIRED`

审核对象：commit `fdb86b26b0d5fffde59673c015ddf642c0df5820` —
`Add workload operator CLI`，parent `ac3696812a9e5eef2f3b3db6bb873b8aee226463`。

#### Executor implementation 与 self-audit 元信息

Executor 没有在第一轮测试全绿后立即发布，而是在实现过程中两次主动发现不足、补实现并重新跑
完整严格回归：

1. 第一版 F3 focused suite 达到 `23 / 23`；Executor 随后扩充 doctor dependency/Git/target/
   remote/storage、status、manifest/framework commit conflict 等负向矩阵，达到 `26 / 26`；
2. 第一次完整 ResourceWarning-strict regression 达到 `140 / 140`，`164.356s`；发布前 self-audit
   发现 inspect 虽验证 summary/raw identity，但还应重验 summary 公开的 target commit/file
   evidence locator，因此补充该实现与测试；
3. 后续 self-audit 又发现 pre-F3 legacy checkpoint 缺少 `operator_config_identity` 的兼容边界
   需要限定：只有 legacy 长参数 invocation 可把缺失解释为明确 legacy `null`，config-backed
   resume 必须拒绝猜测升级；补齐后重新运行 F3/F2/F1 和完整回归；
4. 最终 Executor evidence：F3 focused `26 / 26`，`24.394s`；F2 `24 / 24`，`7.233s`；
   F1 `20 / 20`，`35.718s`；完整 strict `140 / 140`，`168.175s`；Python 3.9
   compilation/import 与 `git diff --check` 通过。

该过程证明 Executor self-check 有效并实际改变了最终实现，但 self-check 与全部既有测试通过仍不
足以替代独立 Reviewer 的跨阶段 evidence-sufficiency 检查。

#### Reviewer independent validation

- Reviewer 独立复跑 F3 focused：`26 / 26`，`23.845s`；
- Reviewer 独立复跑完整 ResourceWarning-strict regression：`140 / 140`，`168.763s`；
- config identity、doctor/preflight/run/resume/status、read-only inspect、legacy checkpoint 限定、
  双语文档和授权文件范围未发现其他阻塞；
- 测试全绿仍未覆盖一个 F1 correction 与 F3 inspect 交叉场景。

#### Reject finding — inspect 恢复了已 supersede verdict 的 evidence authority

`inspect_run.target_evidence_check` 遍历 tracked summary 中所有历史 Reviewer
`structured_evidence`，并要求每条 evidence 当前都通过语义验证。F1 correction 的设计会有意
同时保留：

```text
initial schema-valid ACCEPT with invalid locator
→ same-thread correction
→ corrected ACCEPT with valid evidence
→ Runtime transition applied
```

最初 invalid verdict 是不可删除的 provenance，但已被 corrected verdict supersede，不再具有当前
acceptance authority。当前 F3 inspect 没有绑定最终 Runtime transition/verdict identity，而是把该
旧 invalid locator 恢复成当前验收要求。

Reviewer 使用 config-backed、transition-enabled disposable fixture 复现：

```text
corrected ACCEPT run exit code = 0
Runtime transition = applied
framework evidence commit/push = success

inspect overall_status = FAIL
target_evidence = FAIL
other checks = PASS
```

该结果违反 `Supersession Persistence`：历史错误必须保留并验证 provenance 完整性，但不能因为
仍存在于 summary 而自动恢复为当前 authoritative verdict。

Required narrow repair：

1. 从 Runtime transition record、最终 verdict locator/hash、checkpoint instruction reference、
   correction resolution 和 summary entry 建立 exact authoritative evidence binding；
2. 只对最终真正授权 transition 的 evidence 做当前语义验证；
3. 原 invalid/superseded evidence 继续由 summary bytes、entry hash、raw identity 和 correction
   reference 验证，不能删除或静默忽略 provenance；
4. commit evidence 还必须重验 object type、raw hash 和从 authoritative target HEAD 的可达性；
5. HUMAN_GATE、FAILED_CLOSED、REJECT/correction exhausted 等没有 ACCEPT transition 的终态不应
   因缺少 authoritative target evidence 自动 FAIL，应明确区分 `NOT_APPLICABLE`、
   `UNAVAILABLE`、`INVALID` 与 `VALID`；
6. 增加 corrected ACCEPT inspect PASS、最终 evidence tamper FAIL、历史 invalid evidence 保留、
   non-ACCEPT terminal、raw missing 和只读重复 inspect 测试。

Independent review verdict：

- 独立 evidence access：`SATISFIED`；
- 独立 verdict formation：`SATISFIED`；
- 独立 evidence-sufficiency judgment：`SATISFIED FOR REJECTION`；
- verdict：`REJECTED — NARROW REPAIR REQUIRED`；
- 当前状态：F3 保持唯一 Active Step，F4 不激活，PT-01 倒计时保持 `1`，PT-02 保持 `+∞`；
- 本次“Executor 主动发现问题并重写、所有测试全绿、独立 Reviewer 仍因新 blind spot 打回”是
  1PCloop 区分 self-check 与 independent review 的直接 self-application evidence，不是 P7
  defect injection。

## 9. Next Direction

只执行 F3 的上述 inspect authoritative-evidence binding 窄 repair。不得重写已经通过审核的
config、doctor/preflight/run/resume/status 或 legacy checkpoint 主体。F1、F2 保持 accepted；
F4–F8 保持 queued；P7 保持暂停。Repair 完成后停止于
`AWAITING INDEPENDENT RE-REVIEW`。
