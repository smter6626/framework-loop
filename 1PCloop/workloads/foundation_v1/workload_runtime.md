# foundation_v1 — Runtime 当前权威状态

## 1. Current Status

- Task ID：`foundation_v1`
- 状态：`ACTIVE`
- 当前 verdict：`REJECTED -- SECOND NARROW REPAIR REQUIRED`
- 最近接受：`F5 -- ACCEPTED AFTER INDEPENDENT RE-REVIEW`
- 唯一 Active Step：`F6 -- 本地只读 TUI`
- 当前顶层 Step：`Step 6`
- Static identity：
  - path：`1PCloop/workloads/foundation_v1/workload_static.md`
  - SHA-256：`0995a0374205a7116b59aeb5ec20a468de22458a24066a9f0f5d71e32f07506e`
- 当前执行方式：Human-mediated Reviewer/Executor
- 最后更新：`2026-09-17`

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

### E. F3 — workload config 与 doctor/preflight/run/resume/status/inspect CLI

状态：`ACCEPTED AFTER REJECT → NARROW REPAIR → INDEPENDENT RE-REVIEW`

结果：

- implementation commit `fdb86b26b0d5fffde59673c015ddf642c0df5820` 建立 strict versioned
  workload config identity 与统一 `doctor/preflight/run/resume/status/inspect` operator CLI；新入口
  只编译到既有 runner，不复制 Reviewer–Executor 状态机；
- 独立 Reviewer 第一次审核发现 `inspect` 会把所有历史 `structured_evidence` 重新当作当前验收
  authority，从而令合法的 F1 corrected ACCEPT 因已 supersede 的旧 invalid locator 失败；该
  `REJECTED — NARROW REPAIR REQUIRED` 及 Executor self-audit 元信息记录于 commit
  `0cc5c7a63dac363f49ba00dcadb9d334b443af6e`；
- repair commit `a2379712b9e187a345c0694e1165fc4c4270ff64` 将 authoritative target evidence
  绑定到 exact Runtime transition plan/record、最终 Reviewer verdict bytes/hash、checkpoint
  instruction reference、correction resolution、唯一 summary entry 与 authoritative target HEAD；
- superseded verdict 继续接受 summary/raw/reference provenance 校验，但不恢复 authority；无 ACCEPT
  transition 的终态明确为 `NOT_APPLICABLE`，raw 缺失为 `UNAVAILABLE`，identity/bytes 冲突为
  `INVALID/FAIL`。

独立 re-review evidence：

- Executor repair F3 focused：`33 / 33`，`50.844s`；F2：`24 / 24`，`7.449s`；F1：
  `20 / 20`，`37.961s`；完整 ResourceWarning-strict regression：`147 / 147`，`190.195s`；
- Reviewer 独立复跑原 corrected-ACCEPT 阻塞路径及 transition/verdict/summary tamper、历史 raw
  修改/删除、HUMAN_GATE 和 correction-exhausted 分类：`4 / 4`，`16.569s`；
- Reviewer 独立复跑 F3 focused：`33 / 33`，`50.398s`；完整 ResourceWarning-strict regression：
  `147 / 147`，`176.960s`；
- 原阻塞复现现为 `overall_status=PASS`、`target_evidence=VALID`，同时初始 invalid locator 仍保留在
  history；authoritative identity tamper 为 `FAIL`，历史 raw 删除为 `UNAVAILABLE`；
- Python 3.9 compilation/import、`git diff --check`、提交范围、远端同步与 clean worktree 通过；
- 未运行 real-service smoke，按 Static 留至 F7，不阻塞 F3 deterministic acceptance。

当前语义：foundation_v1 的 AC-03 已满足，F3 operator/read-only inspect 可作为后续 F6/F7 的
稳定 CLI 基础。首次 REJECT、“Executor 自检并重跑全部测试后仍被独立 Reviewer 打回”及最终 repair
历史继续保留在 §8，不因 ACCEPT 删除。

### F. F4 -- 默认中文 Static/Runtime Prompt 模板规范化

状态：`ACCEPTED AFTER INDEPENDENT REVIEW`

结果：

- implementation commit `eeb75e11480ecc245e040862bd42a952ec008c97` 新增 tracked
  `1PCloop/templates/static_prompt_zh.md` 和 `runtime_prompt_zh.md`，并同步双语 README 与
  deterministic template tests；
- 两份模板固定记录 Framework v1.2 外部只读来源路径、SHA-256、非自动同步与未来独立审核边界；
- 除 provenance 第 3-10 行外，模板正文分别与固定来源逐字节一致，不引入 foundation 当前状态、
  paper/research 默认目标、credential 或真实 profile state；
- Static/Runtime 职责分离、Human Owner authority、Single Active Step、独立审核、Pending deadline、
  Human Gate、Supersession Persistence、Task-Local Freeze 和 privacy boundary 均有 deterministic
  coverage；常规 regression 只读取 tracked 模板，不依赖个人机器的 Tools 路径。

独立 review evidence：

- Executor F4 focused：`12 / 12`，`0.003s`；完整 ResourceWarning-strict regression：
  `159 / 159`，`175.673s`；
- Reviewer 独立复跑 F4 focused：`12 / 12`，`0.002s`；完整 ResourceWarning-strict regression：
  `159 / 159`，`186.554s`；
- Reviewer 重新验证两份 source hash、两份 target hash、普通 UTF-8 文件类型、非 symlink、README
  链接和去 provenance 后的逐字节 source equivalence；
- commit scope、`git diff --check`、non-force push、ref identity 和审核前 clean worktree 均通过；
- 未运行 real-service smoke，按 Static 留至 F7，不阻塞 F4。

当前语义：Static AC-06 已满足；PT-01 已以 commit
`eeb75e11480ecc245e040862bd42a952ec008c97` 的模板、来源 identity 与独立审核 evidence
关闭为 `RESOLVED`，因此 Step 5 gate 已解除。

### G. F5 -- runner 模块化和 Human Gate UX

状态：`ACCEPTED AFTER REJECT -> NARROW REPAIR -> INDEPENDENT RE-REVIEW`

结果：

- implementation commit `3f3bba9d94b5446008d6773792af00ded566a5ae` 提取无 runner 反向
  dependency 的 `mutation_contracts.py` 和纯 `human_gate.py`，增加 config-backed `human-gate`
  只读命令，并保持唯一 `orchestrate()` 与 runner re-export identity；
- 首次独立审核发现 Human Gate 未检查完整 target/framework authoritative identity，target 外部
  mutation 后仍允许开始新 run，而 `inspect` 已返回 FAIL；REJECT 及 Executor/Reviewer 全绿测试和
  原始复现记录于治理 commit `40c58a180e2daffeacb2e5bf65616e551d579e6a`；
- narrow repair commit `9262f9754d0632a555a4bbe8f821c1c7ccc5e4f0` 让 `status`、`inspect`、
  `human-gate` 共用一组 state-aware、只读的 authoritative-integrity 检查；gate projection
  冲突时统一 default-deny，F3 顶层字段与嵌套 `human_gate_projection` 分离；
- 合法 publication pending 仍为 `FINALIZATION_ONLY`，已完成的合法 Human Gate 仍须 Human review
  才能开始新 run；缺失 raw evidence 为 `UNAVAILABLE`，identity conflict 为 `INVALID`。

独立 re-review evidence：

- Executor repair focused `19 / 19`，`37.533s`；F3 operator `33 / 33`，`47.378s`；
  点名 F1-F4 regression `139 / 139`，`185.257s`；完整 ResourceWarning-strict regression
  `178 / 178`，`225.025s`；
- Reviewer 独立复跑 F5 focused `19 / 19`，其中 Human Gate `14 / 14`、contract `5 / 5`；
  完整 ResourceWarning-strict regression `178 / 178`，`224.051s`；
- Reviewer 重跑首次 REJECT 的 disposable target-dirty 复现：修改前三个命令均为
  `ACTIVE / NEW_RUN_AFTER_REVIEW`，`inspect=PASS`；target 变 dirty 后三命令均为
  `INVALID / HUMAN_REMEDIATION_REQUIRED`，allowed actions 不含 finalization 或新 run，
  `inspect=FAIL / STATE_UNAVAILABLE`；
- Reviewer 检查共享检查集、F3 顶层字段隔离、双语 README、四个文件的 commit scope、Static hash、
  `git diff --check`、远端同步与审核前 clean worktree；未运行 real-service smoke，仍留至 F7。

当前语义：Static AC-07、AC-08 与 AC-11 在 F5 范围内有充分 evidence。首次 REJECT 与
repair/re-review 链保留于 §8；F5 文件默认冻结，F6 不重开其 control contract。

## 3. Active Step

### F6 / Step 6 -- 本地只读 TUI

#### Objective

提供 macOS 本地终端中的可用 TUI dashboard，让 Human operator 不必从原始日志推断运行位置。
界面只读展示 F2 structured progress、F3 operator status/inspect 和 F5 Human Gate projection；
可以刷新、切换视图和退出，但不启动或恢复 Agent、不替 Human 选择 gate action。`run`/`resume`
继续使用现有 CLI。F6 不引入 Codex GUI automation、Web UI 或并发控制。

#### Inputs 及固定 identity

- Static：`1PCloop/workloads/foundation_v1/workload_static.md`，SHA-256
  `0995a0374205a7116b59aeb5ec20a468de22458a24066a9f0f5d71e32f07506e`；
- F2 accepted `control-events.jsonl`、`live-status.json`、timer/last-activity semantics；
- F3 accepted strict workload config、`status`/`inspect` 和 safe-next-action；
- F5 accepted nested Human Gate projection 和 shared authoritative-integrity checks，repair commit
  `9262f9754d0632a555a4bbe8f821c1c7ccc5e4f0`；
- `1PCloop/scripts/onepcloop.py`、`workload_operator.py`、`progress_status.py`、`human_gate.py`、
  双语 README 及相关 tests；
- Static AC-04、AC-05、AC-09、AC-11。

#### Permitted changes

- 新增独立 TUI/presenter module 与对应 tests；
- 在 `onepcloop.py` 增加 config-backed `tui` 入口；必要时增加只读 operator adapter，但不得
  改变 `status`、`inspect`、`human-gate` 的现有 JSON/output contract；
- 更新双语 README，说明启动、键位、刷新、非 TTY、缺失 evidence、退出与安全边界；
- 使用 Python 3.9/macOS 可用的本地终端能力；优先标准库，不新增依赖，除非有直接必要性
  evidence 并单独说明。

#### Prohibited changes

- 全局/task-local Static/Runtime、schema、roles、requirements、templates 和历史 evidence；
- 修改 F1-F5/P4-P6 authoritative behavior、runner state machine、checkpoint/recovery、Runtime
  transition、evidence publication 或 safe-next-action semantics；
- 从 raw Codex events、prompt、peer_message、stderr、命令输出或自然语言猜测 UI/control state；
- TUI 写入 checkpoint、event/status、summary、target/framework Git，或自动运行 `run`/`resume`、
  finalization、Human Gate action、repair；
- F7 real-service smoke、F8 GUI/治理压缩、P7、self-hosting、lock/watcher/concurrency、外部 Tools
  或 closed workload mutation、force push/history rewrite。

#### Required evidence

- event-source test 证明 presenter 只消费 F2/F3/F5 的 structured projections，不读取或解析
  natural-language payload；
- deterministic rendering/input tests 覆盖无 checkpoint、active turn、Human Gate、failed closed、
  publication pending/completed、raw unavailable 和 identity INVALID；
- run/stage elapsed、timeout remaining、last activity、cycle/role/state、target HEAD、logical outcome、
  Runtime transition、evidence publication 与 gate recovery/action 分层可见；
- 非 TTY、窄终端、终端 resize、退出/异常清理有明确且可测试行为；刷新有界，不 busy-loop；
- 两次只读 UI refresh 前后 checkpoint、manifest、events/status、summary 与 target/framework Git
  状态不变；privacy fixture 不展示 prompt、peer、stderr、internal diagnostic 或 secret；
- F2/F3/F5 focused regression 与完整 ResourceWarning-strict regression、精确 commit scope。

#### Acceptance criteria

1. `onepcloop.py --config <absolute-config> tui` 在可交互 macOS 终端启动、显示并可退出；
   非 TTY 不发出屏幕控制序列，也不创建 run/checkpoint。
2. TUI 只从已验证的 structured control/status/checkpoint/event projection 和固定枚举构造显示；
   raw Codex/free-text payload 不是 UI 的控制或状态来源。
3. 操作者可区分正在执行、等待 Human、failed closed、evidence finalization、已发布等状态；计时
   与 F2 active-time 语义一致，不把进程停止期间 wall time 伪装为 run elapsed。
4. `INVALID`/`UNAVAILABLE` 有显著标识，且不显示比 F5 projection 更宽的允许动作；
   publication success 不能覆盖 logical failure，terminal gate 不显示为普通 Agent resume。
5. 至少支持可发现的刷新、视图切换/滚动和退出键；窄终端和 resize 不崩溃；渲染/输入错误后
   终端状态可恢复。UI 不执行 mutation 或 Human decision。
6. 重复打开/刷新不修改任何 authoritative artifact 或 Git state；privacy 与完整 strict
   regression 通过。F7 前不宣称 real-service end-to-end 已验收。

#### Tests

- pure presenter/data-source tests，不依赖真实 TTY 或 sleep；
- disposable config-backed read-only TUI integration/snapshot tests；
- fake terminal/input tests 覆盖键位、窄屏、resize、异常清理和非 TTY；
- F2 progress、F3 operator、F5 Human Gate 与完整 strict regression。

F6 不运行 real-service Codex smoke；真实可用性和合法 ACCEPT 闭环留到 F7。

#### Stop conditions / Human Gate

- TUI 需要改变 F2/F3/F5 accepted contract 或从 peer prose/raw payload 猜测状态；
- 需要自动 Human decision、mutation/resume、不可逆操作、新 dependency 或 Static 变化；
- 需要 F7 real-service smoke、F8 GUI、P7 或 concurrency 才能完成当前只读 dashboard。

#### Executor report format

```text
F6 implementation status: IMPLEMENTED / BLOCKED
branch / implementation commit / parent / working-tree state
changed files
TUI entrypoint, data source, screens and keys
timer/state semantics, INVALID/UNAVAILABLE behavior
read-only/privacy/non-TTY/resize/terminal-cleanup evidence
focused regressions and full ResourceWarning-strict regression
known limitations
recommended Runtime evidence summary
```

Executor 不得宣告 F6 accepted，也不得推进本 Runtime。

## 4. Queued

| Step | Deliverable | 状态 |
| --- | --- | --- |
| F7 / Step 7 | post-foundation real-service smoke | `QUEUED` |
| F8 / Step 8 | GUI/治理压缩/evidence lifecycle 的 evidence-driven 决策 | `QUEUED` |

顶层映射固定为：`F1 = Step 1`、`F2 = Step 2`、`F3 = Step 3`、`F4 = Step 4`、
`F5 = Step 5`、`F6 = Step 6`、`F7 = Step 7`、`F8 = Step 8`。

## 5. Blockers and Human Decision Gates

- F6 acceptance 当前仍被 stable no-checkpoint 的证据不足阻塞：`inspect` 对 checkpoint 不存在和
  checkpoint 已出现但 malformed/identity-invalid 使用同一个 generic failure；presenter 将后者仍
  误判为 stable absence。上一轮的合法 new-run 竞争和 Unicode `Zl/Zp` 边界已经修复。
- 剩余项属于 F6 只读 snapshot protocol 的窄修复，不需要 Human Owner 作新的产品或合同决定。
- framework/target overlap 禁止使实现采用 Human-mediated workflow；这是已知 self-hosting
  limitation，不是 F6 blocker。

## 6. Pending Tasks — Non-blocking Blocks

当前顶层 Step：`6`

| ID | 非阻塞性 block | 引入于 | 截止 Step | 剩余安全迁移次数 | 当前状态 | 关闭条件与所需 evidence |
| --- | --- | --- | --- | --- | --- | --- |
| PT-01 | 默认中文 Prompt 模板尚未规范化 | Step 1 | Step 5 | 0 | `RESOLVED` | F4 commit `eeb75e11480ecc245e040862bd42a952ec008c97` 记录固定来源 hash、tracked 模板、测试与独立 Reviewer acceptance |
| PT-02 | raw evidence 长期清理/保留策略未确定 | Step 1 | +∞ | +∞ | `PERMANENTLY_NON_BLOCKING` | F8 或未来 Human decision 记录 retention policy 与实际使用 evidence |

### Pending Gate Check

- 下一顶层 Step：`Step 7 / F7`
- 激活前必须关闭的 Pending Task：无；PT-01 已在其 Step 5 deadline gate 前关闭。
- Gate verdict：`CLEAR`
- 支持 evidence：F4 implementation commit `eeb75e11480ecc245e040862bd42a952ec008c97`
  与本次独立 review；PT-02 保持 `+∞`。
- GUI：仅在 F8 基于使用 evidence 决定；当前不是已承诺交付，也不是 F6 blocker。

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

F2 → F3 transition（历史状态）：

- Previous step state：F2 `REJECTED — NARROW REPAIR REQUIRED`；
- Triggering evidence：repair commit `54ccf66a1c95843ae680e0c8f50ed98c5df6c0a5`、
  Reviewer independent re-review、F2 focused `24 / 24`、F1 `20 / 20` 与完整 strict
  `114 / 114`；
- Verdict：F2 `ACCEPTED AFTER RE-REVIEW`；
- Current step：F3 / Step 3 `ACTIVE / NOT EVALUATED`；
- Pending countdown：PT-01 从 `2` 重算为 `1`，仍为 `OPEN_NON_BLOCKING`；PT-02 保持 `+∞`；
- Transition authorized by：独立 Reviewer verdict 与 Human Owner 的自动收尾授权。

F3 -> F4 transition（历史状态）：

- Previous step state：F3 `REJECTED — NARROW REPAIR REQUIRED`；
- Triggering evidence：repair commit `a2379712b9e187a345c0694e1165fc4c4270ff64`、
  Reviewer 原阻塞路径独立复现通过、F3 focused `33 / 33` 与完整 strict `147 / 147`；
- Verdict：F3 `ACCEPTED AFTER RE-REVIEW`；
- Current step：F4 / Step 4 `ACTIVE / NOT EVALUATED`；
- Pending countdown：PT-01 从 `1` 重算为 `0` 并成为 `DUE_NEXT`；F4 本身是关闭该项的当前
  Active Step，在 PT-01 `RESOLVED` 前禁止激活 F5；PT-02 保持 `+∞`；
- Supersession：F3 首次 REJECT 及其 self-audit 元信息继续作为 provenance；repair/re-review
  ACCEPT 只 supersede 当时的“当前拒绝状态”，不删除 rejection evidence；
- Transition authorized by：独立 Reviewer verdict 与 Human Owner 的自动收尾授权。

F4 -> F5 transition（历史状态）：

- Previous step state：F4 `ACTIVE / NOT EVALUATED`，PT-01 `DUE_NEXT`；
- Triggering evidence：implementation commit `eeb75e11480ecc245e040862bd42a952ec008c97`、
  fixed source/target hashes、逐字节正文 equivalence、Reviewer F4 focused `12 / 12` 与完整 strict
  `159 / 159`；
- Verdict：F4 `ACCEPTED AFTER INDEPENDENT REVIEW`；
- Current step：F5 / Step 5 `ACTIVE / NOT EVALUATED`；
- Pending update：PT-01 在 Step 5 activation gate 前以 F4 commit 与独立 review evidence 关闭为
  `RESOLVED`；PT-02 保持 `+∞ / PERMANENTLY_NON_BLOCKING`；
- Meaning：默认中文治理模板成为 tracked、provenance-bound 的稳定输入；F5 可以开始，F4 文件
  默认冻结；
- Transition authorized by：独立 Reviewer verdict 与 Human Owner 的自动收尾授权。

F5 -> F6 transition（当前状态）：

- Previous step state：F5 `REJECTED -- NARROW REPAIR REQUIRED`，首次拒绝及原始复现保留于 §8；
- Triggering evidence：repair commit `9262f9754d0632a555a4bbe8f821c1c7ccc5e4f0`、Reviewer
  target-dirty 原阻塞路径独立复测、F5 focused `19 / 19`、完整 strict `178 / 178`；
- Verdict：F5 `ACCEPTED AFTER INDEPENDENT RE-REVIEW`；
- Current step：F6 / Step 6 `ACTIVE / NOT EVALUATED`；
- Pending update：PT-01 保持 `RESOLVED`，PT-02 保持 `+∞ / PERMANENTLY_NON_BLOCKING`，
  下一 Step 7 gate 为 `CLEAR`；
- Meaning：F5 的共享只读 identity check 与嵌套 Human Gate projection 成为 F6 TUI 的稳定输入；
  F6 不重开 F5 control semantics；
- Transition authorized by：独立 Reviewer verdict 与 Human Owner 既有自动收尾授权。

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

### 2026-09-15 F3 independent re-review：`ACCEPTED`

审核对象：repair commit `a2379712b9e187a345c0694e1165fc4c4270ff64`，parent 为保存 F3
首次 REJECT 与 self-audit 元信息的 Runtime commit
`0cc5c7a63dac363f49ba00dcadb9d334b443af6e`。

Acceptance mapping：

| Criterion | Direct evidence | Sufficiency judgment | Result |
| --- | --- | --- | --- |
| exact authority selection | transition plan/record、最终 verdict bytes/hash、instruction reference、correction resolution、唯一 summary entry | 不再按全部历史 evidence 或“最后一个 ACCEPT”猜测，绑定链逐项闭合 | PASS |
| Supersession Persistence | corrected ACCEPT fixture 保留初始 invalid locator，最终 inspect 为 PASS/VALID | 历史错误保留 provenance，但不恢复当前 authority | PASS |
| target evidence integrity | full object ID、commit type/raw hash、authoritative HEAD reachability、file boundary/hash tests | commit/file evidence 均与最终授权 target state 直接绑定 | PASS |
| non-ACCEPT classification | HUMAN_GATE、FAILED_CLOSED、correction exhausted 与 capability-disabled 语义 | 无 ACCEPT transition 时明确 NOT_APPLICABLE，不把任务失败混同 evidence bundle 冲突 | PASS |
| unavailable/invalid/read-only | raw 删除/修改、identity tamper、两次 inspect 字节对比 | 缺失为 UNAVAILABLE，冲突为 INVALID/FAIL，inspect 不修复或修改 artifact | PASS |
| F1/F2/F3 compatibility | focused suites 与完整 strict suite | correction、event/recovery、operator CLI 和 publication 未出现 regression | PASS |

- 独立 evidence access：`SATISFIED`；
- 独立 verdict formation：`SATISFIED`；
- 独立 evidence-sufficiency judgment：`SATISFIED`；
- Reviewer 原阻塞路径及关键负向矩阵独立复跑：`4 / 4`，`16.569s`；
- Reviewer F3 focused：`33 / 33`，`50.398s`；
- Reviewer 完整 ResourceWarning-strict regression：`147 / 147`，`176.960s`；
- branch/local HEAD/origin/GitHub ref 均为 repair commit，工作树在审核前 clean；授权文件范围与
  `git diff --check` 通过；
- Reviewer verdict：`ACCEPTED`；
- Review limitation：未运行真实 Codex service，按 Static 留至 F7；完整 verdict/correction 内容在
  Git-ignored raw 被清理后明确降为 `UNAVAILABLE`，不猜测恢复。两者不阻塞 F3。

本次 ACCEPT supersede §8 中 F3 的当前拒绝状态，但保留首次 REJECT、Executor 两次自查补修、全部
测试全绿后仍被独立 Reviewer 打回及最终 repair 的完整语义链。它继续构成 self-application
evidence，不是 P7 fault injection。

### 2026-09-16 F4 independent review：`ACCEPTED`

审核对象：commit `eeb75e11480ecc245e040862bd42a952ec008c97`，parent
`4191024c5eef9c1d5332a3b2c76f70a252be9e6f`。

Acceptance mapping：

| Criterion | Direct evidence | Sufficiency judgment | Result |
| --- | --- | --- | --- |
| fixed provenance | template headers、Tools source hashes、target hashes | 来源路径/hash、Framework v1.2、只读与非自动同步边界完整一致 | PASS |
| source fidelity | 去除 target 第 3-10 行 provenance 后的独立 `cmp` | 两份 target body 分别与 fixed source 逐字节一致，无实质改写 | PASS |
| Static/Runtime separation | 模板正文、focused tests、双语 README | Static 不记录进度，Runtime 不静默改合同，复制使用方式明确 | PASS |
| governance invariants | Human Owner、Single Active Step、independent review、Pending、Human Gate、supersession tests | Static AC-06 所需 invariant 均有直接文本与 deterministic coverage | PASS |
| portability/privacy | test source inspection、UTF-8/regular-file checks、forbidden-state tests | regression 只读 tracked template，不要求外部 Tools 存在，不嵌入当前状态或 secret | PASS |
| compatibility | 159-test ResourceWarning-strict suite | 新文档/templates/tests 未改变 F1-F3/P4-P6 executable behavior | PASS |

- 独立 evidence access：`SATISFIED`；
- 独立 verdict formation：`SATISFIED`；
- 独立 evidence-sufficiency judgment：`SATISFIED`；
- Reviewer F4 focused：`12 / 12`，`0.002s`；
- Reviewer 完整 ResourceWarning-strict regression：`159 / 159`，`186.554s`；
- 两份 target template SHA-256：
  - Static：`880908226afbbd1c39262852586a4f87edab3d0d0994a758968188afd18ca8fd`；
  - Runtime：`7e9d7bccb10890f34b211235bdd585245d61e6aa6e3a75a6b87a7910193d94ea`；
- `git diff --check`、commit scope、non-force push、local/origin/GitHub ref 与审核前 clean worktree：
  通过；
- Reviewer verdict：`ACCEPTED`；
- Review limitation：模板不会自动同步未来 source 变化，且 real-service smoke 仍留至 F7；两者均为
  已声明边界，不阻塞 F4。

PT-01 由 `DUE_NEXT` 关闭为 `RESOLVED`，其历史 deadline 与 evidence 保留，不通过删除记录掩盖。

### 2026-09-16 F5 independent review：`REJECTED -- NARROW REPAIR REQUIRED`

审核对象：commit `3f3bba9d94b5446008d6773792af00ded566a5ae`，parent
`5dfbfcdc8ce20fcfea2d7aaa34de51f6413e71ca`。

#### Executor implementation 与 validation evidence

- 新增 pure `mutation_contracts.py` 与 `human_gate.py`，runner 通过 object-identity-preserving alias
  保持旧 import compatibility，且 `orchestrate()` 仍是唯一 mutation state machine；
- 新增 config-backed `human-gate`，并让 `status`、`inspect`、`human-gate` 调用同一纯 projection；
- Executor focused：`12 / 12`，`6.951s`；点名 F1-F4 regression：`139 / 139`，
  `193.946s`；完整 ResourceWarning-strict regression：`171 / 171`，`181.381s`；
- Python 3.9 compilation/import、dependency direction、privacy/read-only、allowlist、protected-path、
  `git diff --check`、non-force push、最终 refs 和 clean worktree 均由 Executor 报告通过；
- Reviewer 独立复跑 F5 focused：`12 / 12`，其中 contract `5 / 5`、Human Gate `7 / 7`；
- Reviewer 独立完整 ResourceWarning-strict regression：`171 / 171`，`195.553s`。

上述全绿结果证明 module extraction 与既有 regression 没有普遍破坏，但没有覆盖下述
acceptance-critical 交叉状态，因此不足以支持 F5 ACCEPT。

#### Reject finding -- Human Gate 动作未绑定完整 authoritative identity

`_gate_evidence_availability()` 只验证 local run root、manifest、event/live status、summary/raw
artifact 和 config identity。它没有验证 `inspect_run()` 已经要求的 authoritative target
branch/HEAD/cleanliness、framework evidence commit/remote push identity，以及适用时的最终 target
evidence authority。结果是 projection 可以在这些 identity 已冲突时继续报告 `AVAILABLE`，并允许
开始新 run。

Reviewer 使用 disposable config-backed Human Gate fixture 直接复现：先完成一个合法
`REVIEWER_HUMAN_GATE` run，再仅在 target 创建一个未跟踪文件。外部 mutation 前后的关键结果为：

```text
before mutation:
human-gate gate_status=ACTIVE
human-gate recovery_mode=NEW_RUN_AFTER_REVIEW
inspect overall_status=PASS
inspect safe_next_action=HUMAN_REVIEW_REQUIRED

after target becomes dirty:
human-gate gate_status=ACTIVE
human-gate evidence_availability=AVAILABLE
human-gate recovery_mode=NEW_RUN_AFTER_REVIEW
human-gate allowed_actions contains START_NEW_RUN_AFTER_HUMAN_REVIEW
inspect target check=FAIL
inspect overall_status=FAIL
inspect safe_next_action=STATE_UNAVAILABLE
```

同一 authoritative state 因而产生互相矛盾的 operator guidance。该结果违反 F5 acceptance：

- identity 冲突必须为 `INVALID` 并 default-deny；
- `status`、`inspect`、`human-gate` 必须共享相同 gate classification/recovery boundary；
- AC-07 要求 Human Gate 的允许动作和恢复边界可安全定位，不能在 target state 已失配时建议开始
  新 run。

实现中 `status`/`inspect` 还通过 flat `**gate` merge 覆盖同名的
`checkpoint_state`、`logical_outcome`、`runtime_transition` 和 `evidence_publication` 字段。正常完整
checkpoint 中这些值目前通常相同，但 repair 必须消除该 collision risk，保证 F3 已接受的顶层字段
继续来自原 authoritative projection，而不是被 Human Gate 的 fallback/synthesized value 替换。

#### Required narrow repair

1. 让 Human Gate identity/evidence classification 覆盖或复用 `inspect` 的 authoritative target、
   framework commit/push 和适用的 authoritative target-evidence 检查，不复制第二套 mutation state
   machine；
2. 任一 authoritative identity conflict 必须统一得到 `gate_status=INVALID`、
   `recovery_mode=HUMAN_REMEDIATION_REQUIRED`，且不得包含 `FINALIZE_EVIDENCE` 或
   `START_NEW_RUN_AFTER_HUMAN_REVIEW`；缺失而非冲突的 local raw evidence 继续为 `UNAVAILABLE`；
3. 同一 checkpoint 下，`status`、`inspect` 和 `human-gate` 的 gate status/reason/actions/recovery
   必须一致；任何 `inspect overall_status=FAIL` 的 authoritative conflict 不得同时生成允许开始新 run
   的 gate guidance；
4. 消除 `**gate` 对 F3 既有顶层字段的覆盖风险。可以使用清晰命名的 nested projection，或使用不冲突
   字段名，但必须保持现有 F3 field semantics 和已记录的 F5 usability fields；
5. 增加至少 target dirty、wrong branch/HEAD、framework commit/remote mismatch、authoritative evidence
   conflict、raw unavailable，以及重复只读调用的 integration tests；断言三个命令一致、默认拒绝且
   bytes/Git state 不变；
6. 保持 contract extraction、runner re-export identity、唯一 `orchestrate()`、terminal
   finalization-only no-Agent-replay、privacy 和 F1-F4 behavior 不变；重跑 F5 focused、F1-F4 点名
   regression 与完整 ResourceWarning-strict suite。

Independent review verdict：

- 独立 evidence access：`SATISFIED`；
- 独立 verdict formation：`SATISFIED`；
- 独立 evidence-sufficiency judgment：`SATISFIED FOR REJECTION`；
- verdict：`REJECTED -- NARROW REPAIR REQUIRED`；
- 当前状态：F5 保持唯一 Active Step，F6 不激活，PT-01 保持 `RESOLVED`，PT-02 保持
  `+∞ / PERMANENTLY_NON_BLOCKING`；
- 本次再次形成“Executor 测试全绿但独立 Reviewer 发现跨模块状态盲点”的 self-application
  evidence；不是 P7 fault injection，也不运行 real-service smoke。

### 2026-09-17 F5 independent re-review：`ACCEPTED`

审核对象：repair commit `9262f9754d0632a555a4bbe8f821c1c7ccc5e4f0`，parent 为保存
首次 REJECT 的 Runtime commit `40c58a180e2daffeacb2e5bf65616e551d579e6a`。

Acceptance mapping：

| Criterion | Direct evidence | Sufficiency judgment | Result |
| --- | --- | --- | --- |
| 原 default-deny 阻塞 | Reviewer 独立重跑 target-dirty 前后 disposable fixture | 变 dirty 后三命令一致 `INVALID / HUMAN_REMEDIATION_REQUIRED`，不再允许 finalization 或新 run；`inspect` 为 `FAIL / STATE_UNAVAILABLE` | PASS |
| 共享 authoritative checks | `workload_operator.py` 中同一 state-aware check set 供 inspect 与 gate 使用；target/framework/ACCEPT conflict tests | 适用的 target branch/HEAD/cleanliness、commit/remote、最终 ACCEPT evidence 均纳入；合法未形成的 artifact 不被误判 | PASS |
| F3 字段兼容 | `status`/`inspect` 使用 `result.human_gate_projection`，双语 README 和 fallback isolation test | 既有顶层 checkpoint/logical/runtime/publication/safe action 字段不被 gate flat merge 覆盖 | PASS |
| Human Gate recovery/privacy | pending/completed、raw missing、重复只读 snapshot、terminal no-Agent-replay tests | `UNAVAILABLE` 与 `INVALID` 分离；合法 pending 只允许 finalization，terminal gate 不伪装成 resume | PASS |
| regression/scope | F5 focused、全量 strict、commit diff 和 Static hash | 仅改四个授权文件；runner、governance、schema、roles 和历史 evidence 未变 | PASS |

- 独立 evidence access：`SATISFIED`；
- 独立 verdict formation：`SATISFIED`；
- 独立 evidence-sufficiency judgment：`SATISFIED`；
- Reviewer F5 focused：`19 / 19`，Human Gate `14 / 14` 用时 `35.189s`，contract `5 / 5`
  用时 `0.075s`；
- Reviewer 完整 ResourceWarning-strict regression：`178 / 178`，`224.051s`；
- branch/local HEAD/origin/GitHub ref 均为 repair commit，审核前工作树 clean，Static SHA-256
  `0995a0374205a7116b59aeb5ec20a468de22458a24066a9f0f5d71e32f07506e` 不变，
  `git diff --check` 与修改范围通过；
- Reviewer verdict：`ACCEPTED`；
- Review limitation：只读检查基于 single-writer 的即时状态，不提供并发快照；真实 Codex service
  与完整 post-foundation smoke 留至 F7。两者不阻塞 F5 deterministic acceptance。

本次 ACCEPT supersede §8 中 F5 的当前拒绝状态，但保留首次 REJECT、Executor/Reviewer 全绿仍被
打回、窄修复及独立 re-review 的完整 provenance；不是 P7 fault injection。

### 2026-09-17 F6 independent review：`REJECTED -- NARROW REPAIR REQUIRED`

审核对象：commit `79eacb69f104314b3f6149192c792111b2bb3982`，parent
`29fca30981ef467086bb961c4a1dd8bb5b338eca`。

#### Executor implementation 与 validation evidence

- 新增 config-backed `tui`、独立 `local_tui.py` presenter/data source 和 fake-terminal/disposable
  tests；data source 只调用既有 `status()`/`inspect_run()`，未修改 runner、operator control、
  Human Gate、Runtime 或 Static；
- Executor F6 focused `14 / 14`，`2.570s`；F2/F3/F5 focused `76 / 76`，`94.004s`；
  完整 ResourceWarning-strict regression `192 / 192`，`217.923s`；
- Executor 报告 Python 3.9 compilation/import、direct import、唯一 `orchestrate()`、read-only Git/
  artifact snapshot、privacy、non-TTY、resize、cleanup、allowlist、protected paths、diff、push、refs
  和 clean worktree 均通过；
- Reviewer 独立复跑 F6 focused `14 / 14`，`2.455s`；完整 ResourceWarning-strict regression
  `192 / 192`，`251.525s`；branch/local/origin/GitHub refs、五文件 scope、Static identity、
  `git diff --check` 与审核前 clean worktree 通过。

上述全绿 evidence 支持 TUI 的基本只读边界和已覆盖状态，但没有覆盖下述两个 presenter blind
spot，因此不足以支持 F6 ACCEPT。

#### Finding 1 -- no-checkpoint 特判吞掉启动竞争

`_snapshot_parts()` 仅根据 `status.result.run_id is None` 和 status gate 的
`reason_code=NO_CHECKPOINT` 设置 `no_checkpoint=true`。一旦为 true，当前实现跳过 gate、四层 state
和 run ID 的全部 status/inspect 对比。

Reviewer 构造了与真实顺序读取一致的边界：`status()` 先读到无 checkpoint，随后 run 在
`inspect_run()` 前创建，inspect 已看到 `run_id=new-run`、`FRAMEWORK_EVIDENCE_PUSHED` 和
`HUMAN_GATE`。当前结果仍为：

```text
no_checkpoint=true
consistent=true
banner=NO CHECKPOINT -- no run was opened
inspect overall_status=PASS
inspect run_id=new-run
```

该 snapshot 明确自相矛盾，却没有进入 `SNAPSHOT UNAVAILABLE`。这违反 F6 Runtime/README 和
Executor 报告中的边界：顺序读取期间状态变化应保守隐藏恢复 guidance，等待刷新。虽然当前
no-checkpoint actions 只有 `NO_AUTOMATIC_REPAIR`，没有直接扩大 mutation authority，但它会在 run
实际已启动时向 Human 显示错误的生命周期状态，因此是 live dashboard 的 acceptance blocker。

#### Finding 2 -- terminal string boundary 遗漏 Unicode line separators

`_public()` 只替换 Unicode category 以 `C` 开头的字符。项目在 F1/F2 已把 `Cc`、`Cf`、`Zl`、
`Zp` 共同定义为公开单行边界；当前 TUI 会原样保留 `U+2028 LINE SEPARATOR` 和
`U+2029 PARAGRAPH SEPARATOR`。Reviewer 直接复现：

```text
_public("safe\u2028forged-line") preserves U+2028
_public("safe\u2029forged-paragraph") preserves U+2029
```

现有 malicious-control test 只覆盖 ESC/LF，因此未发现该差异。当前 operator 字段已有较强 schema
约束，但 presenter 自身宣称 bounded printable rows，且是终端最终输出边界；应与既有 public-output
规则一致，而不是依赖每个未来上游字段永远排除 `Zl/Zp`。

#### Required narrow repair

1. 收紧 stable no-checkpoint 判定：只有 status 与 inspect 都证明同一 config 下尚无 checkpoint 时
   才显示 `NO CHECKPOINT`。如果 inspect 已观察到任意 run ID/checkpoint state 或与 no-checkpoint
   contract 不一致，必须 `consistent=false` 并显示 `SNAPSHOT UNAVAILABLE`；
2. 增加真实 data-source call ordering test，令第一次 status 返回无 checkpoint、第二次 inspect
   返回新建 run；断言 recovery/action 不显示，下一次一致 refresh 才显示新 run；同时覆盖反向
   transition 或删除/替换 checkpoint 的保守行为；
3. `_public()` 必须替换 `Cc`、`Cf`、`Zl`、`Zp`，或复用无 runner side effect 的既有 public-text
   helper；增加 `U+2028/U+2029`、CR/LF、ESC、NUL 和窄终端 regression，保持普通中文可显示；
4. 保持 data source 只调用 `status`/`inspect`，不读取 raw artifact，不改变 TUI 的只读、非 TTY、
   curses cleanup、1 秒 refresh、F2 active-time、F5 action/default-deny 和唯一 orchestrator 边界；
5. 重跑 F6 focused、F2/F3/F5 focused 与完整 ResourceWarning-strict regression，检查 direct import、
   protected paths、diff、普通 non-force push 和 clean refs。

Independent review verdict：

- 独立 evidence access：`SATISFIED`；
- 独立 verdict formation：`SATISFIED`；
- 独立 evidence-sufficiency judgment：`SATISFIED FOR REJECTION`；
- verdict：`REJECTED -- NARROW REPAIR REQUIRED`；
- 当前状态：F6 保持唯一 Active Step，F7 不激活；PT-01 保持 `RESOLVED`，PT-02 保持
  `+∞ / PERMANENTLY_NON_BLOCKING`；
- 本次仍是 1PCloop self-application 中“Executor 和完整回归全绿，但独立 Reviewer 发现未覆盖
  lifecycle/output boundary”的 evidence，不是 F7 smoke 或 P7 fault injection。

### 2026-09-17 F6 first independent re-review：`REJECTED -- SECOND NARROW REPAIR REQUIRED`

审核对象：repair commit `004364290b39d94274b1816c18040fe912f883cf`，parent 为保存首次
F6 REJECT 的 Runtime commit `e2e15f4b68ab95eeefbfad9c7096dd5e621f16e1`。

#### Repair evidence 与已关闭 finding

- `_public()` 改为复用无 runner side effect 的 `mutation_contracts.escape_public_text()`；Reviewer
  直接验证 LF/CR/NUL/ESC、`Cf`、`Zl`、`Zp` 均被 ASCII escape，普通中文保持不变；该 finding
  `CLOSED`；
- status 无 checkpoint、inspect 已看到合法 `new-run` 的原始竞争现为
  `no_checkpoint=false / consistent=false / SNAPSHOT UNAVAILABLE`；下一次两侧一致后才显示 run；
- Executor F6 focused `17 / 17`，`2.773s`；F2/F3/F5 `76 / 76`，`99.081s`；完整 strict
  `195 / 195`，`245.219s`；Python 3.9、direct import、唯一 `orchestrate()`、scope、protected
  paths、diff、push、refs 和 clean worktree 报告通过；
- Reviewer 独立 F6 focused `17 / 17`，`2.471s`；完整 ResourceWarning-strict regression
  `195 / 195`，`246.114s`；commit scope、Static identity、refs 与审核前 clean worktree 通过。

#### Remaining reject finding -- generic identity failure 不能证明 checkpoint 缺失

repair 中 `_stable_no_checkpoint()` 要求 inspect 仅含一个固定
`CHECKPOINT_IDENTITY_FAILED`。但 F3 `inspect_run()` 对以下两种情况返回相同 envelope：

```text
A. checkpoint path 不存在
B. checkpoint path 已存在，但 bytes malformed 或 config/identity invalid
```

因此该 generic failure 不是“checkpoint missing”的结构化证据。Reviewer 直接使用真实 operator
复现：先调用 `status()` 得到 no checkpoint，再于同一路径写入 `{}` checkpoint，随后调用
`inspect_run()`。当前 presenter 结果为：

```text
checkpoint_exists=true
checkpoint_bytes={}\n
inspect overall_status=FAIL
inspect code=CHECKPOINT_IDENTITY_FAILED
no_checkpoint=true
consistent=true
banner=NO CHECKPOINT -- no run was opened
```

实际 authoritative path 已存在冲突状态，界面却将其降级为 absence，而不是
`SNAPSHOT UNAVAILABLE`/identity remediation。这仍违反“只有双方证明 absence 才显示 NO CHECKPOINT”
以及 Static 的 default-deny 边界。新增 matrix 只模拟合法 new run、disappearance 和 run-ID replacement，
没有覆盖 malformed/identity-invalid checkpoint 在两次读取之间出现。

#### Required second narrow repair

1. 不得把 generic `CHECKPOINT_IDENTITY_FAILED` 本身当作 checkpoint 缺失证明；
2. 在不读取 raw checkpoint、不复制 operator parser 的前提下，为 stable absence 增加可区分证据。
   推荐在 `OperatorDataSource.read()` 对 no-checkpoint 候选执行 bounded status bracket：
   `status_before -> inspect -> status_after`，并把第二次 status 的结构化结果带给 presenter；只有前后
   status 都是同一 exact no-checkpoint projection 且 inspect 没有 run projection 时才显示稳定 absence；
3. 如果第二次 status 为 INVALID、出现 run、config identity/locator 改变或任一投影不一致，必须
   `SNAPSHOT UNAVAILABLE`，不显示 recovery actions；不得由 TUI 直接 `exists()`/open/read checkpoint；
4. 增加真实 disposable operator tests：status 后写入 `{}`、config-identity-invalid checkpoint、
   合法 new run，以及 stable absence；断言 malformed/invalid appearance fail closed，下一次一致状态
   才可显示；
5. 保留已通过的 Unicode escape、只读、privacy、non-TTY、cleanup、active-time 和 F5 default-deny
   behavior；重跑 F6 focused、F2/F3/F5 和完整 strict suite。

Independent re-review verdict：

- 独立 evidence access：`SATISFIED`；
- 独立 verdict formation：`SATISFIED`；
- 独立 evidence-sufficiency judgment：`SATISFIED FOR REJECTION`；
- verdict：`REJECTED -- SECOND NARROW REPAIR REQUIRED`；
- 当前状态：F6 继续唯一 Active Step，F7 不激活；PT-01 `RESOLVED`，PT-02
  `+∞ / PERMANENTLY_NON_BLOCKING`；
- 第一次 repair 的成功内容保留，不要求回退或重写；剩余 blocker 仅限 absence proof。

## 9. Next Direction

只执行 F6 second narrow repair：为 stable no-checkpoint 增加不依赖 generic identity failure 的
结构化 absence proof，覆盖 malformed/identity-invalid checkpoint 在顺序读取期间出现。保留已经
通过的合法 new-run race 和 Unicode 修复；F1-F5 保持 accepted；不得读取 raw checkpoint、重写
operator/orchestrate、修改 Static/Runtime、运行 F7 smoke 或提前实现 F8/P7。修复后停止于
`AWAITING SECOND INDEPENDENT RE-REVIEW`。
