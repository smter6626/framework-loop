# foundation_v1 — Runtime 当前权威状态

## 1. Current Status

- Task ID：`foundation_v1`
- 状态：`ACTIVE`
- 当前 verdict：`REJECTED — NARROW REPAIR REQUIRED`
- 唯一 Active Step：`F1 — Reviewer verdict 机械纠错与明确终态输出`
- 当前顶层 Step：`Step 1`
- Static identity：
  - path：`1PCloop/workloads/foundation_v1/workload_static.md`
  - SHA-256：`0995a0374205a7116b59aeb5ec20a468de22458a24066a9f0f5d71e32f07506e`
- 当前执行方式：Human-mediated Reviewer/Executor
- 最后更新：`2026-09-13`

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

## 3. Active Step

### F1 / Step 1 — Reviewer verdict 机械纠错与明确终态输出

#### Objective

当 schema-valid Reviewer verdict 因 evidence locator/hash 或其他机械条件验证失败时，在不重跑
已经成功的 Executor mutation 的前提下，让同一 Reviewer thread 获得确定性错误原因和当前
authoritative state，并最多纠正两次 control output；同时让终端明确区分 logical outcome、
Runtime transition 与 evidence publication。

#### Inputs 及固定 identity

- Static：`1PCloop/workloads/foundation_v1/workload_static.md`，SHA-256
  `0995a0374205a7116b59aeb5ec20a468de22458a24066a9f0f5d71e32f07506e`；
- 全局治理：`1PCloop/docs/miniloop_static.md`、`1PCloop/docs/miniloop_runtime.md`；
- runner：`1PCloop/scripts/run_mutation_loop.py`；
- evidence helper：`1PCloop/scripts/p63_evidence.py`；
- structured schemas：`1PCloop/schemas/*.schema.json`，只读；
- post-P6 observation：
  `1PCloop/evidence-summaries/post-p6-foundation-smoke-20260912.md`；
- P4–P6 tests 作为 regression boundary。

#### Permitted changes

- `1PCloop/scripts/run_mutation_loop.py`；
- 必要时 `1PCloop/scripts/p63_evidence.py`，但只能用于 F1 recovery/status 边界；
- `1PCloop/tests/test_run_mutation_loop.py`；
- `1PCloop/tests/test_runtime_transition.py`；
- `1PCloop/tests/test_evidence_summary.py`；
- `1PCloop/README.md` 中与 F1 operator behavior 直接相关的说明；
- 必要的新 F1 专项 test/helper 文件。

#### Prohibited changes

- 全局和 task-local Static/Runtime；
- `1PCloop/schemas/**`、roles、requirements；
- P4 transport behavior、closed workloads、历史 runs/evidence；
- 外部 Tools 模板、target remote/history；
- F2–F8 implementation；
- P7 fault injection、真实 Codex smoke、self-hosting 或 concurrency 功能。

#### Required evidence

- 一个普通 implementation commit 和精确文件列表；
- deterministic test 输出，固定 Executor/Reviewer call count、thread relationship、target HEAD、
  checkpoint 与最终 control states；
- 对 malformed correction、stale state、重复纠错和 correction exhaustion 的 fail-closed evidence；
- 完整 P4–P6 ResourceWarning-strict regression；
- README/operator behavior diff（如修改）；
- 独立 Reviewer 可直接读取的 commit、tests 和 fixture artifacts。

#### Acceptance criteria

1. Schema-valid verdict 的机械 validation failure 被分类为可纠正 control-output 错误时，不重跑
   已完成 Executor，target HEAD 保持原成功结果。
2. 纠错请求只发送到形成原 verdict 的同一 Reviewer thread，并包含 deterministic error code/
   reason、当前 target/governance identity、允许的 evidence boundary 和原 verdict locator/hash；
   不要求 Python 理解 peer_message。
3. Reviewer control-output correction 最多尝试 `2` 次；第二次仍不合法则保持
   `FAILED_CLOSED`，不进入无限循环。
4. Python 不删除、补写、替换或猜测 Reviewer evidence，不把命令描述自动转换为 locator。
5. 每次纠错 turn 继续使用 Reviewer verdict schema、验证 Reviewer profile/thread/resume 和当前
   authoritative freshness。
6. crash/resume 不重复 Executor、已完成纠错 turn、Runtime transition、summary entry、framework
   commit 或 push。
7. 最终终端和 structured status 明确显示：`logical_outcome`、`runtime_transition`、
   `evidence_publication`，且 publication success 不覆盖 logical failure。
8. 现有合法 ACCEPT、REJECT、HUMAN_GATE 和 P4–P6 regression 不回归。

#### Tests

- post-P6 failure fixture：第一次 Reviewer ACCEPT 使用非绝对 locator，纠错后提供合法 artifact；
- Executor call count 始终为 `1`，Reviewer 使用同一 verified thread；
- 第一次纠错成功后合法 transition 只应用一次；
- 两次纠错都失败后 logical outcome 为 `FAILED_CLOSED`，Runtime 不变；
- correction turn schema/role/thread/freshness/evidence negative cases；
- correction pending、turn 完成、transition/summary/finalization 各恢复边界；
- terminal/structured status 三层结果测试；
- 完整 ResourceWarning-strict regression。

F1 不运行真实 Codex service；完整 post-foundation real-service smoke 留到 F7。

#### Stop conditions / Human Gate

- 无法确定 validation failure 是否允许纠错；
- target、governance、Reviewer thread 或原 verdict identity 已变化且无法机械重建；
- 纠错需要 Python 改写 Agent evidence 或改变 schema/Static；
- 达到两次纠错上限；
- 出现 framework/target overlap、自托管授权或未解释的 repository mutation；
- 需要 destructive Git action、对外发布、credential 或 Human 主观决定。

#### Executor report format

```text
F1 implementation status: IMPLEMENTED / BLOCKED
branch / implementation commit / parent / working-tree state
changed files
correction state-machine summary
Executor/Reviewer call-count and thread evidence
target/Runtime/summary/commit/push idempotence evidence
focused tests and full regression
known limitations
recommended Runtime evidence summary
```

Executor 不得宣告 F1 accepted，也不得推进本 Runtime。

## 4. Queued

| Step | Deliverable | 状态 |
| --- | --- | --- |
| F2 / Step 2 | terminal timer、status、structured progress event | `QUEUED` |
| F3 / Step 3 | config + doctor/preflight/run/resume/status/inspect CLI | `QUEUED` |
| F4 / Step 4 | 默认中文 Static/Runtime Prompt 模板规范化 | `QUEUED` |
| F5 / Step 5 | runner 模块化和 Human Gate UX | `QUEUED` |
| F6 / Step 6 | 本地 TUI | `QUEUED` |
| F7 / Step 7 | post-foundation real-service smoke | `QUEUED` |
| F8 / Step 8 | GUI/治理压缩/evidence lifecycle 的 evidence-driven 决策 | `QUEUED` |

顶层映射固定为：`F1 = Step 1`、`F2 = Step 2`、`F3 = Step 3`、`F4 = Step 4`、
`F5 = Step 5`、`F6 = Step 6`、`F7 = Step 7`、`F8 = Step 8`。

## 5. Blockers and Human Decision Gates

- 当前无阻止 F1 开始的 blocker。
- 当前 framework/target overlap 禁止使实现采用 Human-mediated workflow；这是已知
  self-hosting limitation，不是 F1 blocker。

## 6. Pending Tasks — Non-blocking Blocks

当前顶层 Step：`1`

| ID | 非阻塞性 block | 引入于 | 截止 Step | 剩余安全迁移次数 | 当前状态 | 关闭条件与所需 evidence |
| --- | --- | --- | --- | --- | --- | --- |
| PT-01 | 默认中文 Prompt 模板尚未规范化 | Step 1 | Step 5 | 3 | `OPEN_NON_BLOCKING` | F4 commit 记录两个固定 Tools hash、模板测试并获独立 Reviewer acceptance；进入 F5 前必须关闭 |
| PT-02 | raw evidence 长期清理/保留策略未确定 | Step 1 | +∞ | +∞ | `PERMANENTLY_NON_BLOCKING` | F8 或未来 Human decision 记录 retention policy 与实际使用 evidence |

### Pending Gate Check

- 下一顶层 Step：`Step 2 / F2`
- 激活前必须关闭的 Pending Task：无
- Gate verdict：`CLEAR`
- Prompt 模板 deadline：必须在进入 `Step 5 / F5` 前由 F4 acceptance 关闭 PT-01。
- GUI：仅在 F8 基于使用 evidence 决定；当前不是已承诺交付，也不是 F1 blocker。

## 7. State Transition

- Previous state：P6 `ACCEPTED / PHASE CLOSED`；P7 曾短暂作为下一 Active Step。
- Triggering decision：Human Owner `2026-09-12` 决定暂停 P7 和 paper/research-driven 路线，
  优先建立 engineering foundation。
- Current state：foundation_v1 `ACTIVE`；F1 为唯一 Active Step；P7 `PAUSED / NOT ACTIVE`。
- Meaning：保留 P4–P6 accepted evidence，以 task-local governance 开展日常可用性、诊断、恢复
  和维护工作。
- Transition authorized by：Human Owner。

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

当前状态：F1 保持唯一 Active Step；F2 不激活；Pending Task 倒计时不变化；Static 不变。

### Self-application interpretation

本次是 1PCloop 核心治理思想用于实现 1PCloop 自身的直接 evidence：task-local
Static/Runtime 编译 F1，Executor 提交实现，独立 Reviewer 直接检查 evidence 并形成明确
`REJECTED`，随后由 Runtime 保存 repair 原因和当前有效状态。由于现有 mutation runner 禁止
framework repo 与 target repo 重叠，该 self-application 仍是 Human-mediated
Reviewer/Executor workflow，不表示 runner 已经自动 self-host 或自动修改/验收自身。

foundation_v1 整体状态仍为 `ACTIVE`，不得宣告完成。

## 9. Next Direction

只执行 F1 的上述窄范围 repair。不得重写已通过审核的 correction 状态机，不得扩大错误重试
集合。F2–F8 保持 queued；不得提前创建 Prompt 模板、TUI、GUI 或 real-service smoke，也不得
启动 P7。repair 完成后停止于 `AWAITING INDEPENDENT RE-REVIEW`。
