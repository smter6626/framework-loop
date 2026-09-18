# Miniloop Runtime

## 任务状态

`ACTIVE -- FOUNDATION_V1 CLOSED / WHISPER_SESSION_UI_V1 ACTIVE`

本 Runtime 记录当前权威执行状态。稳定目标、硬约束和最终验收标准见：

`1PCloop/docs/miniloop_static.md`

---

## Current Effective State

```text
P4-A = ACCEPTED
P4-B = ACCEPTED
P5   = ACCEPTED
P5.1 real Git mutation smoke = ACCEPTED
P5.1 real medium-scale workload control-plane path = VERIFIED
P5.1 medium-scale workload Human Gate = ACCEPTED / PHASE CLOSED

Deterministic authoritative-context reconstruction
= ACCEPTED CURRENT CONTROL-PLANE MECHANISM

Multi-cycle mutation orchestration
= ACCEPTED CURRENT CONTROL-PLANE MECHANISM

Reviewer persistent + explicit resume
= PREFERRED IMPLEMENTATION CANDIDATE
= NOT A PERMANENT ARCHITECTURE INVARIANT

P6 control-plane hardening
= ACCEPTED / PHASE CLOSED
= P6.1 ACCEPTED / P6.2 ACCEPTED / P6.3 ACCEPTED / P6.4 ACCEPTED

P7 controlled REJECT -> REPAIR fault injection
= PAUSED BY HUMAN OWNER / NOT ACTIVE
= MAY RESUME ONLY AFTER EXPLICIT HUMAN REACTIVATION

Most recently closed engineering task
= foundation_v1 / ACCEPTED / PHASE CLOSED
= 1PCloop/workloads/foundation_v1/workload_runtime.md

Current external engineering task
= whisper_session_ui_v1 / ACCEPTED / TASK CLOSED WITH FOLLOW-UP UI DEFECT
= 1PCloop/workloads/whisper_session_ui_v1/workload_runtime.md

Overall 1PCloop completion
= AWAITING EXPLICIT HUMAN OWNER DECISION

Framework-as-paper
= PAUSED AFTER THREE-ROUND NOVELTY AUDIT

1PCloop current research role
= ENGINEERING ARTIFACT + EXPERIMENTAL HARNESS

researchPlan.md
= REPLACED ON 2026-09-09
= PAUSED / FROZEN RESEARCH MAP ON 2026-09-12
= NOT AN ACTIVE ENGINEERING EXECUTION PLAN
= CHEAP PILOTS REQUIRE EXACT-RQ + DIRECT-PRIOR + ADVISOR GATES
= FORMAL EXPANSION ALSO REQUIRES PILOT-RESULT + RESOURCE-DECISION GATES
```

Real workload run `20260906T102252Z-52187` stopped mechanically at
`STOPPED_FOR_HUMAN_REVIEW / target_head_unchanged` after the final no-op Executor
payload reached Reviewer review. Human Owner subsequently verified Japanese and
French live transcription, accepted the explicitly recorded residual manual-coverage
limits, and closed the `multiLanguage_v1` workload phase. No run #3 is required.
Target push and merge remain separate Human-controlled integration actions.

foundation_v1 is `ACCEPTED / PHASE CLOSED`: F1-F8 and task-local AC-01 through
AC-11 have independent evidence, and the task has no Active Step. Overall 1PCloop
remains `ACTIVE` only because the Static Completion Definition reserves the final
`ACTIVE -> COMPLETED` decision for the Human Owner. The closed task-local Runtime at
`1PCloop/workloads/foundation_v1/workload_runtime.md` is frozen by default; this
global Runtime retains the phase pointer and high-level transitions to avoid further
unbounded growth.

### 2026-09-18 -- external workload `whisper_session_ui_v1` activated

Human Owner authorized a new two-step external workload without reopening the
closed foundation_v1 task or paused P7. Step 1 asks 1PCloop to integrate three
streaming governance/investigation documents into the target `main`; that step is
accepted and pushed at `d0f581bb70379239c3147e5c8469d2285ad6620b`. Step 2 was
accepted at target commit `cb4261825b7d51d3ec33a97e083683c50e6b9e82`; its
framework evidence and target feature branch are pushed. Human Owner subsequently
reported that the implemented functions work correctly, closing the real-function
black-box gate. The same test found a separate layout defect: the main window is too
tall for the available window bounds. That defect is not retroactively part of S2;
the recommended next workload is bounded window height plus deliberate scrollable
content placement before any separate merge/release decision.
Both steps use separate target worktrees and separate runs.
The automatic Reviewer checks code logic and deterministic UI tests; real
audio-to-transcript black-box testing belongs to the Human Owner. Task-local
Static/Runtime and current step are at
`1PCloop/workloads/whisper_session_ui_v1/`.

### 2026-09-18 -- foundation_v1 phase closure

Status: `ACCEPTED / PHASE CLOSED -- AWAITING OVERALL HUMAN OWNER DECISION`

- F1-F7 implementation and real-service evidence are independently accepted;
- F8 disposition is independently accepted: local GUI `DEFER`, governance compression
  `DEFER`, raw evidence lifecycle `IMPLEMENT -- POLICY ONLY`;
- PT-01 and PT-02 are `RESOLVED`; foundation_v1 has no Active Step and no automatic F9;
- compact F7 and F8 evidence are tracked at
  `1PCloop/evidence-summaries/f7-post-foundation-real-service-smoke-20260918.md` and
  `1PCloop/evidence-summaries/f8-foundation-disposition-20260918.md`;
- P7 remains paused, and GUI/archive/cleaner/self-hosting/concurrency remain inactive;
- this phase closure does not itself declare overall 1PCloop `COMPLETED`.

## Lossless Historical Compaction

On `2026-09-06`, Human Owner authorized lossless Runtime compaction. The exact
pre-compaction Runtime is preserved at:

`1PCloop/docs/archive/miniloop_runtime_pre_compaction_20260906.md.gz`

Integrity metadata:

```text
source commit = 333c83e144a1b1f9c3157bcbf3af45959d9d8743
source Git blob = 0ab943228b097722f0db83f6029f6139d5d25cc1
uncompressed SHA-256 = dc31191718dc04784b44261ff0a10b4217861e73def34be2ac3089c424d9f090
uncompressed bytes = 73015
uncompressed lines = 1529
gzip SHA-256 = 76f146f8ea2f8cf72074ab8da95dbcea08c598fba5c00adca0f86a91304bdfc9
gzip bytes = 25786
```

The archive preserves verbatim the superseded P4-A planning/todo state, detailed
P4-A/P4-B execution evidence, interim effective-state snapshots and the unrelated
GitHub connector support diagnostic removed from this active Runtime. Those bytes
remain repository-backed provenance and can be reconstructed without conversation
history. This active Runtime retains immutable Done records, formal Reviewer
decisions, observed Research Questions, P5/P5.1 conclusions, current limitations
and the latest effective state.

The historical Markdown can be read without modifying the archive by running:

```text
gzip -dc 1PCloop/docs/archive/miniloop_runtime_pre_compaction_20260906.md.gz
```

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

### Step 1 prerequisite — Verify dual-Codex CLI profiles

Status: `COMPLETED`

Result:

- 已按 Static 中记录的当前角色绑定完成两个独立 Codex profile 的串行与并发 CLI smoke test；
- 串行 smoke test：

```text
CODEX_HOME="$HOME/.codex-A" codex exec 'Reply with exactly: CHENG_EXEC_OK'
-> CHENG_EXEC_OK

CODEX_HOME="$HOME/.codex-B" codex exec 'Reply with exactly: DYM_EXEC_OK'
-> DYM_EXEC_OK
```

- 并发 smoke test：

```text
A exit=0
CHENG_PARALLEL_OK

B exit=0
DYM_PARALLEL_OK
```

Evidence locator:

- `f4bdfae40e8453036b500d6a6a0fccbbdde09ab3` — 记录已验证的双 Codex execution environment；
- `e08df1137b651ac38f16af0154220ca2b8471bc0` — 记录串行、并发 smoke test 及其输出。

Commit Notes:

- Step: `Step 1 prerequisite`
- Environment contract commit: `f4bdfae40e8453036b500d6a6a0fccbbdde09ab3`
- Runtime evidence-record commit: `e08df1137b651ac38f16af0154220ca2b8471bc0`

Meaning:

双 profile 身份选择和 CLI 调用前置条件已经完成；当前尚未完成的是 Reviewer→Executor→Reviewer 的自动文本路由。

### Step 1 milestone — Verify text-only Reviewer→Executor→Reviewer transport

Status: `COMPLETED`

Result:

- 已实现 active `1PCloop/` 下的最小 Codex CLI 文本路由循环；
- 真实运行路径为：

```text
Reviewer (.codex-B)
  -> Executor (.codex-A)
  -> Reviewer (.codex-B)
```

- 三次 Codex invocation 均正常结束，exit code 均为 `0`；
- 两次 peer payload 分别为 `420` 和 `411` bytes；
- 两次发送方 `final.txt` 与接收方 `peer-payload.txt` 的 SHA-256 一致；
- 两次 transport 均记录 `preserved_verbatim=true`；
- 当前三个 turn 均显式使用 `read-only` sandbox；
- Orchestrator 不解析 peer natural-language payload 的语义，也不根据 `ACCEPT` / `REJECT` 等自由文本推进 Runtime；
- Reviewer 仅接受基础 transport milestone，没有接受整个 Step 1，也没有授权 Runtime transition。

Evidence locator:

- commit `7ef5c7aafcf66bbbf65e3bcca410a39c97035fac` — `Implement dual-Codex text routing loop`；
- `1PCloop/scripts/run_text_loop.py`；
- `1PCloop/runs/text-loop-20260905-01/manifest.json`；
- `1PCloop/runs/text-loop-20260905-01/transcript.md`；
- `1PCloop/README.md`。

Commit Notes:

- Step: `Step 1 text transport milestone`
- Implementation/evidence commit: `7ef5c7aafcf66bbbf65e3bcca410a39c97035fac`

Meaning:

基础 Reviewer→Executor→Reviewer 自动文本 transport 已通过。该完成记录只证明 profile invocation、opaque peer payload routing、process completion 和可检查 run evidence；不证明 mutation、independent implementation acceptance、repair loop、Runtime transition 或 Human Gate 已完成。

### Step 1 P3 — Usage/cache instrumentation + current ephemeral baseline

Status: `COMPLETED`

Result:

- 已按当前 Codex CLI 的实际 JSON event schema，从原始 `events.jsonl` 机械提取 `thread_id` 与 `turn.completed.usage`；
- 每个 turn 的 `process.json` 已记录 `input_tokens`、`cached_input_tokens`、`cache_write_input_tokens`、`uncached_input_tokens`、`cache_hit_ratio`、`output_tokens` 与 `reasoning_output_tokens`；
- `manifest.json` 已汇总三个 turn 的 thread identifier、usage availability、token/cache total 与 duration；
- usage 字段缺失或类型不符合 schema 时记录为 `null`，不会被误记为 `0`；
- parser 只读取 machine-readable control event，不解析 Reviewer / Executor 的自然语言，也不会根据 `ACCEPT` / `REJECT` 推进 Runtime；
- 原始 `events.jsonl` 保持 Codex CLI stdout 的原始字节，metadata 仅为派生结果；
- 已完成一次真实 `--ephemeral` 三回合 baseline，三次调用均为 `read-only`，角色绑定保持 `.codex-B` / `.codex-A` / `.codex-B`；
- 两次 peer payload 均通过逐字节一致性检查，三个 process exit code 均为 `0`。

Baseline:

```text
Turn 1 Reviewer (.codex-B)
  thread_id              = 01a071c8-a6f8-7ef0-a2dc-f23dc9a23983
  input_tokens           = 56387
  cached_input_tokens    = 42240
  uncached_input_tokens  = 14147
  cache_hit_ratio        = 0.749109
  output_tokens          = 477
  reasoning_output_tokens = 183
  duration_seconds       = 20.577

Turn 2 Executor (.codex-A)
  thread_id              = 01a071c8-f661-7dc2-acdc-5b8e8dd62e05
  input_tokens           = 56133
  cached_input_tokens    = 38528
  uncached_input_tokens  = 17605
  cache_hit_ratio        = 0.686370
  output_tokens          = 297
  reasoning_output_tokens = 0
  duration_seconds       = 23.096

Turn 3 Reviewer (.codex-B)
  thread_id              = 01a071c9-50ba-7aa0-8f98-f01b8ede1b7e
  input_tokens           = 55214
  cached_input_tokens    = 46336
  uncached_input_tokens  = 8878
  cache_hit_ratio        = 0.839207
  output_tokens          = 614
  reasoning_output_tokens = 301
  duration_seconds       = 24.405

Total
  input_tokens           = 167734
  cached_input_tokens    = 127104
  uncached_input_tokens  = 40630
  cache_hit_ratio        = 0.757771
  output_tokens          = 1388
  reasoning_output_tokens = 484
  duration_seconds       = 68.078
```

Evidence locator:

- commit `b8ed49f5283c58ca8b314b49498f1881c63830a1` — instrumentation、tests 与真实 ephemeral baseline；
- `1PCloop/scripts/run_text_loop.py`；
- `1PCloop/tests/test_run_text_loop.py`；
- `1PCloop/runs/usage-baseline-20260905-01/manifest.json`；
- `1PCloop/runs/usage-baseline-20260905-01/transcript.md`；
- `1PCloop/runs/usage-baseline-20260905-01/turn-*/events.jsonl`；
- `1PCloop/runs/usage-baseline-20260905-01/turn-*/process.json`。

Commit Notes:

- Step: `Step 1 P3`
- Implementation/evidence commit: `b8ed49f5283c58ca8b314b49498f1881c63830a1`

Meaning:

P3 已完成并建立当前 `--ephemeral` baseline。该 evidence 只描述本次实际 token/cache/latency，不证明 `codex exec resume` 一定更省，也不启动 P4、workspace mutation、automatic Runtime semantic transition 或任何 persistent Executor session。

---

## Other Notes

### 2026-09-12 — Post-P6 engineering-foundation transition

Status: `CURRENT SUPERSESSION / HUMAN OWNER AUTHORIZED`

Human Owner changed the current execution priority after P6 closure:

```text
P6 closed
-> post-P6 smoke exposed a usability gap
-> P7 paused by Human decision
-> foundation_v1 activated
```

Reason and scope:

- current resources prioritize a daily-usable, diagnosable, recoverable and
  maintainable engineering foundation rather than continuing a paper-driven P7
  experiment sequence;
- this is a Human Owner direction/resource decision informed by recent prior-work
  review, not a claim that all literature or research space has been exhausted;
- P4–P6 accepted results remain valid and frozen; P6 is not reopened;
- P7 is retained as optional future reliability coverage but is not active and may
  run only after explicit Human reactivation;
- at this `2026-09-12` transition, `foundation_v1` became the sole current engineering
  task. Its stable contract and detailed state are task-local; the `2026-09-18`
  closure record above now supersedes its active status:
  - `1PCloop/workloads/foundation_v1/workload_static.md`;
  - `1PCloop/workloads/foundation_v1/workload_runtime.md`;
- the durable compact post-P6 observation is
  `1PCloop/evidence-summaries/post-p6-foundation-smoke-20260912.md`.

This global Runtime will record only future phase pointers and high-level
transitions; foundation step progress belongs in the task-local Runtime.

### 2026-09-09 — 研究方向收缩与旧计划失效

2026-09-08 至 2026-09-09 的三轮 adversarial novelty audit 对 Framework / 1PCloop 的宽研究方向作出了新的当前判断：

- execution governance / authoritative transition：`A — DEAD`；
- decision-semantics-preserving memory / compression：`A — DEAD AS A BROAD DIRECTION`；
- claim-relative evidence adequacy / layered acceptance：`A — DEAD`。

由此产生的当前 supersession：

- 旧 `researchPlan.md` 中的 RQ1–RQ6、“第一篇论文主线”和 full experiment matrix 不再是当前研究执行依据；
- `researchPlan.md` 已直接替换为当前方向、三个 narrow candidates 和研究启用门；
- Framework 保留为 methodology artifact，1PCloop 保留为 engineering artifact / experimental harness；
- 在本条 `2026-09-09` 记录形成时，P6.4 是 authoritative engineering step，但不是
  PhD 申请或 paper blocker；
- 在同一历史时点，P7 仍 deferred；旧 paper plan 不再授权其作为 research experiment。

本记录只追加 current correction / supersession，不回写或删除下方已保留的历史 RQ 记录和 Done evidence。

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

### 2026-09-05 — Ollama completion-signal supersession

Status: `SUPERSEDED`

Step: `Step 1`

Decision:

不再轮询 Ollama process/load state 作为 inference-completion signal。当前 active inference substrate 是 Codex CLI；process/command completion 是直接的机械回合完成信号，语义上的 task completion 仍由 Reviewer 判断。

### 2026-09-05 — Text-routing milestone review / token-cache direction

Status: `REVIEWED — BASIC TRANSPORT ACCEPTED`

Step: `Step 1`

Reviewed commit:

- `7ef5c7aafcf66bbbf65e3bcca410a39c97035fac`

Review conclusion:

- 当前 transport implementation 的核心边界成立：显式 `CODEX_HOME`、opaque peer payload、逐字节保存/核对、process result 落盘以及 Python 不理解自由文本语义；
- 当前三个 turn 全部使用 `--ephemeral`。这不等价于关闭服务端 prompt cache，但意味着 Reviewer 的第三回合不会直接继承第一回合的 Codex session working context；
- 因而在进入 workspace mutation 之前，应优先增加 token/cache 可观测性并做 session-resume 对照实验，避免在不知道真实 cached/uncached input 成本的情况下继续扩大循环；
- authoritative memory 仍然是 Static + Runtime + repository/evidence；Codex session 只能作为可丢失、可重建的 performance working memory，正确性不得依赖 session 持久化；
- prompt/cache 优化原则是稳定内容前置、动态 peer payload 后置，并尽量保持固定前缀字节稳定；
- `events.jsonl` 属于 machine-readable control evidence，可以由 Python 机械提取 thread/session identifier 和 usage fields；这不违反“LLM 理解 LLM；Python 路由 LLM”的语义边界；
- Reviewer 不应把“payload 字节未改变”表述成自己的语义审查结论。byte identity 的证明责任属于 orchestrator 的 SHA/byte comparison；Reviewer 负责语义上的 instruction/evidence review；
- `1PCloop/runs/` 如果长期累积并进入普通 repository inspection，会形成上下文污染和额外 token 开销。后续应区分 raw local run logs 与 curated evidence，避免无限增长的 run history 自动进入 Agent 工作上下文。

Recommended next sequence:

```text
1. 从 events.jsonl 机械提取 usage / thread metadata
2. 跑一次当前 --ephemeral baseline
3. 保存 input / cached_input / uncached_input / output / reasoning token 指标
4. 实现 Reviewer session resume，并保持 Static / Runtime / repository 为 authoritative state
5. 用同一类 transport task 做 ephemeral vs resume 对照
6. 只有在获得实际成本/缓存 evidence 后，再决定是否让 Executor 也长期 resume
7. 随后进入 disposable-file mutation + independent review milestone
```

### 2026-09-05 — P3 CLI event-schema observation

Status: `OBSERVED`

Step: `Step 1 P3`

Observed evidence:

- 当前真实 `codex exec --json` 输出以 `thread.started.thread_id` 提供可用 thread identifier；未观察到独立的 `session_id` 字段；
- usage 位于 `turn.completed.usage`，本次可用字段为 `input_tokens`、`cached_input_tokens`、`cache_write_input_tokens`、`output_tokens` 和 `reasoning_output_tokens`；
- `uncached_input_tokens` 与 `cache_hit_ratio` 是由 input/cached input 机械计算的派生值；
- 因本次运行使用 `--ephemeral`，不能仅凭记录到的 `thread_id` 宣称该 session 可 resume；
- P4 的 resume 成本/收益仍需单独、等价的对照 evidence，当前 baseline 不作该结论。

### 2026-09-05 — P3 review / P4-A activation

Status: `P3 ACCEPTED — P4-A ACTIVE`

Step: `Step 1 P4-A`

Reviewed commits:

- `b8ed49f5283c58ca8b314b49498f1881c63830a1` — P3 instrumentation、tests 与真实 `--ephemeral` baseline；
- `edffa4da603b5e930ba87eea7ecbb54752d83ccb` — P3 evidence 与 Runtime 状态同步。

Review conclusion:

- P3 在当前 scope 内通过，无 repair requirement；usage/thread parser 保持 machine-readable boundary，baseline evidence 可用于启动下一阶段；
- 当前 baseline 已证明 fresh/ephemeral 三回合并非零缓存命中：总 input `167734`，cached `127104`，uncached `40630`，aggregate cache hit `0.757771`。因此 P4 的问题不是“从零缓存变成有缓存”，而是 Reviewer session resume 能否进一步降低 uncached input、重复 context reconstruction 和 latency；
- baseline 原始事件显示 Reviewer Turn 1、Executor Turn 2、Reviewer Turn 3 都实际重新读取了 Static / Runtime。重复 authoritative-state reconstruction 已经是实测行为，而不是纯理论风险；
- 当前 Agent 自主使用 `sed` / `cat` 读取 governance docs。随着 Runtime 增长，固定行范围读取可能漏掉后部的当前 Active Step；这属于“内容未进入 context”的 reconstruction correctness 风险，不能由 session resume 本身修复；
- byte-level transport identity 继续由 orchestrator 的 SHA/byte comparison 证明；Reviewer 只负责语义审查；
- 当前 parser 的潜在 robustness 改进（例如多个 `turn.completed`、`cached_input_tokens > input_tokens` anomaly）是 non-blocking，不要求在 P4-A 前单独返工。

P4-A experiment decision:

- Human Owner 已明确授权启动 P4；
- P4 第一阶段严格限定为 paired experiment，只改变 Reviewer session lifecycle；
- Control 与 Treatment 必须在同一 repository HEAD、同一 Static/Runtime、同一 role prompts、同一角色绑定、同一 sandbox、同一 Codex/profile model configuration 下运行；
- 两组实验全部完成前，不得为了记录中间结果修改 Runtime 或其他会改变输入上下文的治理文件；
- Control：保持 Reviewer / Executor / Reviewer 三个 turn 全部 fresh `--ephemeral`；
- Treatment：Reviewer Turn 1 创建正常可持久化 thread，Executor 仍 fresh `--ephemeral`，Reviewer Turn 3 resume Turn 1 的同一 Reviewer thread；
- Treatment 不允许通过“先 `--ephemeral` 再 resume”的方式模拟 persistent Reviewer；应以当前 CLI 实际支持的正常持久化 thread + `codex exec resume` 机制实现，并先根据本机 `codex exec resume --help` / 实际 CLI schema 验证命令形式；
- P4-A 不改变 Executor session lifecycle，不进入 workspace-write，不进入 disposable mutation，不实现 automatic Runtime semantic transition；
- P4-A 完成后只根据真实 evidence 判断 Reviewer resume 是否值得保留，不预设 resume 一定更省。

## Reviewer Decision — P4-A

### 2026-09-05 — P4-A review decision

Status: `ACCEPTED — EXPERIMENTAL MILESTONE`

Step: `Step 1 P4-A`

Reviewed commits:

- `0496fba156083f08e7d1975069330ec131d4ad0e` — P4-A implementation；
- `3026ffe150d8dae9a22f1e21ed226203c2f5ecb0` — P4-A evidence 与 Runtime record。

Review conclusion:

- P4-A 在当前实验 scope 内通过，无 repair requirement；
- Treatment 已机械证明 Reviewer Turn 3 恢复了 Turn 1 创建的同一 persistent Reviewer thread，`resume_relationship_verified=true`，且不存在 resume-to-fresh fallback；
- 本次 paired evidence 中，Reviewer T3 `uncached_input_tokens` 从 `9599` 降到 `1694`，减少 `7905`（`-82.3523%`）；aggregate uncached input 从 `30594` 降到 `24987`，减少 `5607`（`-18.3271%`）；aggregate input 从 `108418` 降到 `102043`（`-5.8800%`）；aggregate duration 从 `55.199s` 降到 `43.362s`（`-21.4442%`）；
- 因此 `persistent Reviewer + explicit resume` 可以保留为下一工程阶段的 **preferred implementation candidate**；
- 该结论不把 Reviewer persistence 冻结为永久 architecture invariant。本次只有一个 `Control -> Treatment` pair，仍存在 cache-warm order、stochastic downstream prompt、单次 latency 与配置观测边界等已记录限制；
- 当前不要求为了继续工程工作先补 reversed-order replicate；若后续需要 benchmark-quality 因果结论，可再单独补充。

Critical reconstruction finding:

- P4-A 同时实证了 authoritative-context reconstruction correctness 风险；
- Control Reviewer T3 只读取 Static `1-240` 与 Runtime `1-260`，没有读到从 Runtime 第 `361` 行开始的当前 Active Step；
- Treatment Reviewer T1 也以固定 `sed` 范围读取并遗漏两份治理文件尾部；
- 因此“Agent 执行了 Static/Runtime read”不能被视为“Agent 已完整重建 authoritative context”的充分证据；
- session resume 可以减少重复 reconstruction，但不能修复首次 bootstrap 本身的不完整读取。

Architecture interpretation:

```text
Static + Runtime + repository/evidence
= authoritative memory

persistent role session
= disposable performance working memory
```

正确性仍必须可以在 session 丢失、rollover 或 fresh restart 后从 authoritative external state 重建；session persistence 只能优化成本与 working continuity，不能成为正确性的唯一来源。

## Human Owner Activation — P4-B

### 2026-09-05 — Deterministic authoritative-context reconstruction authorized

Status: `P4-B ACTIVE`

Step: `Step 1 P4-B`

Authorization:

- Human Owner 已明确接受上文 P4-A Reviewer decision，并授权进入 `Step 1 / P4-B — Deterministic authoritative-context reconstruction`；
- 上文 P4-A 的 Done、experiment evidence、review decision 与 provenance 保持不变；
- 本节 supersede 上文 `P4-B: NOT STARTED — REQUIRES HUMAN OWNER ACTIVATION`，作为当前 effective state。

当前有效状态：

```text
P4-A = ACCEPTED
P4-B = ACTIVE

Reviewer persistent + explicit resume
= preferred implementation candidate
= not a permanent architecture invariant
```

P4-B 唯一目标：

- 修复已经由 P4-A 实证的 authoritative-context reconstruction correctness 风险；
- 由 deterministic orchestration/control layer 机械读取完整当前 Static 与 Runtime，记录 path、SHA-256、byte length、line count、Git HEAD 与 bootstrap/session freshness metadata；
- fresh Reviewer bootstrap 必须把完整当前 Static 与 Runtime 作为 authoritative input，并可机械验证没有固定行范围截断；
- Reviewer resume 必须比较 session-known hashes 与 current hashes：unchanged 可以复用 working context，Runtime changed 必须 refresh/reconstruct，Static changed 默认 fail-safe rollover/full rebootstrap；
- governance file 缺失、bootstrap byte/hash mismatch 或 resume freshness mismatch 必须 fail closed；
- 保持 peer semantic payload byte preservation，不要求 Python 理解 Agent 自由文本；
- 单元测试后只做最小真实 Scenario A/B/C 验证，并记录 fresh bootstrap、unchanged resume、changed-Runtime stale-state protection 以及 token/cache/duration evidence；
- 完成后只进入 `P4-B IMPLEMENTED / VALIDATED — AWAITING REVIEW`，不得自行 `ACCEPT`。

明确禁止：

- 不实现 persistent Executor；
- 不进入 workspace-write、disposable-file mutation 或 `multiLanguage_v1` workload；
- 不实现 automatic Runtime semantic transition；
- Python 不解析 Reviewer / Executor natural language，不搜索 `ACCEPT` / `REJECT` 决定 task state；
- 不修改 `1PCloop/history/miniloop-skeleton-v0/**`；
- 不把 Reviewer persistence 宣布为永久架构 invariant；
- 不构建 RAG、vector DB、semantic Runtime parser 或未经 evidence 支持的复杂增量同步协议。

当前无已知 blocker。Implementation 必须在本 activation record 单独提交后开始。

---

## Reviewer Decision — P4-B

### 2026-09-05 — P4-B review decision

Status: `ACCEPTED — CONTROL-PLANE MILESTONE`

Step: `Step 1 P4-B`

Reviewed commits:

- `229f5577b3cea1d297096be6c54d596b9d27e507` — P4-B activation；
- `fe9b48697535107a0d0f1d8c5bb8c4483c616f5d` — deterministic authoritative-context implementation 与 tests；
- `43f5a727feaa646a5d384e305bce3ddb5e58b0ac` — validation evidence 与 Runtime record。

Review conclusion:

- P4-B 在当前 scope 内通过，无 repair requirement；
- fresh Reviewer bootstrap 已机械证明完整当前 Static + Runtime bytes 进入 prompt，并记录 source SHA、byte length、line count、Git HEAD 与 prompt offsets；launch 前 source/prompt byte verification 成立；
- unchanged Reviewer resume 以 session-known/current governance hashes 判断 freshness，未重复注入 governance full bytes，并机械证明恢复目标 Reviewer thread；
- Runtime hash 变化会进入 `runtime-refresh` 并注入完整新 Runtime；Static hash 变化会 fail-safe rollover 到新 persistent Reviewer thread，并完整 rebootstrap Static + Runtime；
- missing governance、source/prompt mismatch、persistent thread ID 缺失、resume process failure 和 resume relationship mismatch 均保持 fail closed；
- Executor 仍为 fresh ephemeral，peer payload byte preservation 与“Python 不解析 Agent natural language / ACCEPT / REJECT”的语义边界未回归；
- 18 项测试通过，真实 Scenario A/B 与临时 Git fixture Scenario C 足以支持本 control-plane milestone。Scenario C 使用 fake Codex、Static-change 未做真实服务 run，属于已知验证边界，不构成当前 blocker。

Cost interpretation:

- P4-B 的 correctness acceptance 不依赖其单次 aggregate token 指标优于 P4-A；
- 本次 P4-B Reviewer T1/T3 的真实 usage 与 latency 可作为 observation，但 P4-A/P4-B 的治理文档、role prompt、Executor cache state、随机输出和服务时序不同，因此不能作 benchmark-quality 因果比较；
- unchanged T3 未重复治理全文这一机制事实已经被 prompt/evidence 直接证明，persistent history 仍计入 reported total input 是正常边界。

Non-blocking boundaries before a medium-scale mutation loop:

1. 当前 `session_known` governance snapshot 只在一次三回合 `orchestrate()` invocation 内存中传递。若后续扩展为多轮 Reviewer→Executor→Reviewer 自循环，必须显式维护并在成功 refresh/rebootstrap 后更新 loop-scoped session-known governance state；不能把本次三回合实现误当作跨任意 cycle / process restart 已自动解决。
2. P4-B 证明的是 framework governance（Static/Runtime）freshness，不是目标代码仓库 snapshot isolation。进入外部 target-repo mutation 时，应独立记录并检查 target repository、branch、HEAD、working-tree state 与 mutation evidence，不能用 governance Git HEAD 代替 target-repo state。
3. P3 parser 的多个 `turn.completed` / `cached_input_tokens > input_tokens` 等 robustness 改进仍可保持 non-blocking，不影响 P4-B acceptance。

Architecture interpretation after review:

```text
Static + Runtime + repository/evidence
= authoritative external memory

persistent Reviewer session
= disposable performance working memory

deterministic governance bootstrap / freshness policy
= accepted current control-plane mechanism
```

Reviewer persistence 继续是 preferred implementation candidate，而不是永久 architecture invariant。

## Observed Research Questions — Non-Blocking Research Notes

Status: `HISTORICAL OBSERVATION ONLY — PRIORITY SUPERSEDED BY 2026-09-09 NOVELTY AUDIT`

本节记录在 1PCloop 当前实现、P4-A / P4-B 实验与 review 过程中自然暴露出的 research-question signals。  
这些内容只是研究方向观察，不属于当前 authoritative Active Step，不修改 Static，不改变已有 Acceptance Criteria，不授权新的 implementation / experiment，也不影响当前工程主线的执行顺序。

**2026-09-09 当前边界：** 下列 RQ 的原建议等级只是历史记录，不再表示当前 priority 或 novelty。当前研究方向、narrow candidates 与启用条件只看 `1PCloop/researchPlan.md`。

### RQ1 — Persistent session memory 与 authoritative external state 应如何分工？

**RQ 内容：**  
在 long-horizon Agent workflow 中，哪些信息可以由 persistent session 作为 working memory 保留，哪些信息必须由外部 authoritative state 承担？如何同时获得 session continuity / efficiency，又保证 correctness 不依赖不可验证或不可重建的 conversation state？

**解释：**  
P4-A 已实际比较 fresh Reviewer 与 persistent Reviewer + explicit resume，并观察到 Reviewer T3 uncached input 和 latency 明显下降。与此同时，当前 architecture 明确要求 Static + Runtime + repository/evidence 才是 authoritative memory，persistent session 只能作为可丢失的 performance working memory。

**建议等级：VERY HIGH**

### RQ2 — Agent “读取了状态”是否等价于“正确重建了 authoritative state”？

**RQ 内容：**  
如何保证 Agent reconstruction 得到的是完整、当前、可验证的 authoritative context，而不仅仅是机械上执行过一次 read command？

**解释：**  
P4-A 中已经观察到 Reviewer 使用固定 `sed` 范围读取治理文件，但实际遗漏了 Static / Runtime 后部的当前内容，说明 `read happened` 并不足以证明 `current authoritative context reconstructed`。P4-B 随后引入完整 byte injection、hash、length、line count、prompt offset 与 launch-before verification，对该 failure mode 做了专门控制。

**建议等级：VERY HIGH**

### RQ3 — 外部 authoritative state 改变后，应采用什么 refresh / invalidation / rollover policy？

**RQ 内容：**  
当 persistent Agent session 已持有旧治理状态，而外部 authoritative state 发生变化时，什么变化只需要增量 refresh，什么变化必须使旧 context 失效并触发完整 rebootstrap？

**解释：**  
P4-B 当前已形成初步 policy：unchanged governance 可复用 session；Runtime changed 时 refresh 当前 Runtime；Static changed 时 rollover 并完整重新注入 Static + Runtime。该机制已经具备明确的 state-validity / invalidation semantics，但不同 policy 的 correctness–cost trade-off 尚未系统比较。

**建议等级：VERY HIGH**

### RQ4 — Independent Reviewer 是否比 self-review 或 shared-context review 更能降低 false acceptance？

**RQ 内容：**  
Reviewer 与 Executor 的角色独立程度，会如何影响错误接受、漏检、repair quality 与最终任务可靠性？

**解释：**  
当前 Static 明确禁止 Executor 对自身工作进行最终 ACCEPT，并要求 Reviewer 直接检查实际 evidence，而不能仅相信 Executor 的自然语言 PASS。该设计已经形成可测试假设，但目前尚未通过 controlled comparison 验证不同 review independence level 对 false acceptance 的影响。

**建议等级：VERY HIGH**

### RQ5 — execution success、test pass、review verdict 与 formal acceptance 是否应被显式区分？

**RQ 内容：**  
在 Agent workflow 中，process exit success、test success、Executor self-report、Reviewer verdict 和 authoritative Runtime transition 是否应该属于不同层级的 completion / acceptance semantics？

**解释：**  
当前 1PCloop 已多次明确区分 process completion、transport correctness、semantic review 与 authoritative transition，并禁止 Python 通过搜索 `ACCEPT` / `REJECT` 自由文本直接推进 Runtime。说明系统已经隐式实现多层 acceptance semantics，但其对 silent failure / false acceptance 的实际价值仍可进一步实验化。

**建议等级：HIGH**

### RQ6 — Independent REJECT → REPAIR loop 相比 one-shot execution 能提高多少可靠性？

**RQ 内容：**  
由独立 Reviewer 驱动的 REJECT → bounded repair → new evidence → re-review 闭环，相比 one-shot execution 或 Executor self-repair，是否能系统性提高最终正确率？

**解释：**  
REJECT → REPAIR 已经是当前 Static Acceptance Criteria 的核心目标之一，但尚未成为中等规模真实 workload 上的 comparative experiment。该路径天然具备 success rate、repair count、false acceptance、token / latency cost 等可测指标。

**建议等级：MEDIUM-HIGH**

### RQ7 — Agent-to-Agent semantic payload 应使用 opaque natural language，还是强制 structured protocol？

**RQ 内容：**  
多 Agent 协作中，是否应该依赖 prompt-only JSON / XML / schema 进行 semantic communication，还是将自然语言作为 opaque semantic payload，并把 deterministic control metadata 独立放在 orchestration layer？

**解释：**  
当前 1PCloop 明确采用 “LLM 理解 LLM，Python 路由 LLM” 的边界，并已机械验证 peer payload byte preservation，同时禁止 Python 从自由文本中推断 authoritative state transition。该设计目前主要是 architecture choice，尚缺少与 structured-output alternatives 的系统 failure comparison。

**建议等级：MEDIUM**

### RQ8 — Reviewer 与 Executor 是否应采用不同的 session persistence policy？

**RQ 内容：**  
不同 Agent role 是否应该具有不同的 memory / session lifecycle，而不是统一采用 fresh 或 persistent session？

**解释：**  
P4-A 当前只让 Reviewer 使用 persistent/resume，而 Executor 继续保持 fresh ephemeral，这已经隐含 role-specific memory hypothesis。Reviewer 需要保持治理与 review continuity，而 Executor 更依赖 bounded current-task context；两种角色是否应采用不同 persistence policy 可以直接做 factorial comparison。

**建议等级：MEDIUM-HIGH**

### RQ9 — raw run history 与 curated authoritative evidence 应如何划界？

**RQ 内容：**  
长期 Agent workflow 是否应该让未来 Agent 访问全部 raw run history，还是需要把 raw logs 与 curated / accepted evidence 显式分离？

**解释：**  
当前 Runtime 已观察到 `1PCloop/runs/` 长期增长可能带来 context pollution、token burden 与 stale evidence exposure，因此已经提出 raw local logs 与 curated evidence 的边界问题。该问题可进一步研究不同 evidence-retention policy 对 retrieval correctness、stale-evidence reuse 与运行成本的影响。

**建议等级：MEDIUM-HIGH**

### RQ10 — 什么情况下 Agent 应 fail closed，而不是自行继续或恢复？

**RQ 内容：**  
面对 stale state、missing evidence、resume mismatch、治理状态冲突等 control-plane uncertainty 时，什么时候应该 fail closed、什么时候允许 automatic recovery、什么时候必须升级到 Human Gate？

**解释：**  
当前 P4-B 已对 governance missing、source/prompt mismatch、resume relationship mismatch 等情况采用 fail-closed behavior，并禁止 silent fallback。现有规则主要来自 reliability design judgment，尚未系统研究 conservative failure policy、automatic recovery 与 human escalation 之间的 trade-off。

**建议等级：MEDIUM-HIGH**

### Research-note boundary

以上 RQ 均为当前实现和实验过程中观察到的研究信号，不表示：

- 已证明对应 research hypothesis；
- 已确认 literature novelty；
- 已形成可投稿 research contribution；
- 当前 1PCloop 工程主线需要为了这些 RQ 改变执行顺序；
- Human Owner 已授权额外 research experiment。

后续只有在 Human Owner 明确决定把某个 RQ 提升为 research track 时，才单独定义 hypothesis、baseline、independent variable、dependent metrics、controlled experiment、replication 与 literature validation。

---

## Reviewer Decision — P5

### 2026-09-06 — Multi-cycle mutation orchestration accepted

Status: `ACCEPTED — FIRST MULTI-CYCLE MUTATION CONTROL PLANE`

Step: `Step 1 P5`

Implementation commit:

- `16c3f3311b3f0d2b04341a0078fdd95b402be63c` — `Add P5 multi-cycle mutation orchestrator`；
- path: `1PCloop/scripts/run_mutation_loop.py`；
- reviewed implementation SHA-256: `359221984c12f081d572ea3ba4aa9dd60b16f383ff1b1481df867aed896bbd19`；
- Git blob SHA: `615e63873a724bbc4e704a43c4db0367df663b04`。

Review history:

- first single-file review: `REPAIR REQUIRED`；
- required repairs were limited to target-HEAD instruction freshness and ensuring an unchanged-HEAD Executor still reaches the Reviewer review turn before the Human gate；
- repaired single-file implementation passed external code review；
- subsequent validation found no correctness bug requiring production-code repair。

Accepted behavior:

- Reviewer state persists across mutation cycles with explicit resume；
- Executor remains fresh ephemeral for every cycle and uses target `workspace-write`；
- Reviewer uses target `read-only` and its before/after target state is mechanically checked；
- framework Static/Runtime plus workload Static/Runtime are mechanically snapshotted with hashes/bytes/lines；
- fresh Reviewer receives the full four-document bootstrap；
- unchanged governance resumes the same Reviewer without repeating full governance bytes；
- Runtime-only governance changes refresh the changed Runtime document(s) on the same Reviewer thread；
- Static-class changes abandon the stale Reviewer thread and perform full rebootstrap on a new persistent Reviewer thread；
- loop-scoped Reviewer state tracks the target HEAD associated with the latest successful Reviewer instruction/review；
- target-HEAD drift invalidates a stale instruction and triggers Reviewer refresh before Executor launch；
- target branch, cleanliness, HEAD, ancestry/history, merge commits, governance changes and launch-time target state are mechanically checked；
- Executor unchanged HEAD is not interpreted as semantic completion: the Executor payload still reaches Reviewer review, after which the loop stops mechanically at `STOPPED_FOR_HUMAN_REVIEW / target_head_unchanged`；
- Python continues to route Agent natural-language payloads opaquely and does not classify `ACCEPT` / `REJECT` / `READY` / `BLOCKED` semantics。

Validation evidence:

Validation-only artifacts were intentionally kept outside the repository at:

```text
/Users/smterpro/Documents/deletable/p5-validation-20260906-01/
```

This directory is disposable local evidence, not permanent repository provenance.

Deterministic harness:

```text
6 / 6 PASS
```

Coverage included preflight failures, four-document freshness behavior, Reviewer thread/hash/known-target-HEAD state, target `A -> B` stale-instruction refresh, `B -> C` launch-race fail-close, descendant/dirty/branch/rewrite/merge/governance invariants, no-op Reviewer-review ordering, opaque byte/SHA/offset preservation, and natural-language non-parsing.

Real Codex no-op smoke:

```text
Reviewer new persistent
-> Executor fresh ephemeral / workspace-write
-> Reviewer explicit resume
-> STOPPED_FOR_HUMAN_REVIEW
reason = target_head_unchanged
```

Reviewer thread relationship:

```text
created  = 01a07591-2dc3-7b52-a5a4-0cb87ac8936c
target   = 01a07591-2dc3-7b52-a5a4-0cb87ac8936c
observed = 01a07591-2dc3-7b52-a5a4-0cb87ac8936c
verified = true
```

Disposable target repository:

```text
branch       = p5-validation
initial HEAD = 2268166e745f66525e2c549ee803b68c31e74303
final HEAD   = 2268166e745f66525e2c549ee803b68c31e74303
clean before = true
clean after  = true
```

Both Reviewer turns recorded `reviewer_target_read_only_verified=true`. The real smoke also verified that Codex `--cd` pointed to the disposable target while `--output-last-message`, JSONL, stderr, process and peer-payload evidence were successfully written outside the target repository.

Single-run usage observation:

```text
Reviewer initial: input 105626, cached 80128, uncached 25498, output 569, reasoning 258, duration 20.419s
Executor:         input  30717, cached 25728, uncached  4989, output 341, reasoning 117, duration 14.925s
Reviewer review:  input 112509, cached107776, uncached  4733, output 701, reasoning 253, duration 21.789s
Total:            input 248852, cached213632, uncached 35220, output1611, reasoning 628, duration 57.133s
```

These values are validation observations only, not a P4/P5 causal benchmark or performance claim.

Known non-blocking boundaries:

1. Workload Runtime is still a read-only authoritative input during a P5 v1 run. P5 does not yet persist Reviewer semantic decisions as a per-cycle workload-runtime checkpoint or promise crash/restart reconstruction of those semantic decisions.
2. P5 does not hold an exclusive lock on the target repository. It instead uses repeated branch / clean / HEAD checks and fail-closed validation to detect external mutation.
3. The target-HEAD refresh path was validated deterministically but was not exercised against the live Codex service because the production runner intentionally has no test hook for injecting a safe external commit between Reviewer instruction and Executor launch.

These limitations do not block the first real medium-scale workload.

## P5.1 — Current real-mutation execution-policy repair

### 2026-09-06 — Codex filesystem sandbox disabled for the current experiment

Status: `IMPLEMENTED AND DETERMINISTICALLY VALIDATED — REAL WORKLOAD NOT RE-RUN`

First real mutation run:

```text
run_id = 20260906T083312Z-48975
target baseline = b5188ccc6aef591398fd8d31e162a29390b120e4
```

该 run 中 Reviewer 正常完成首轮 instruction；Executor 完成 source/test 修改及测试，但 Codex `workspace-write` sandbox 阻止创建 `.git/index.lock`，因此无法创建 Git commit。目标 HEAD 保持不变且 working tree 变脏，P5 按既有 invariant 正确进入 `FAILED_CLOSED`。Human Owner 随后已将目标仓库恢复至 clean baseline `b5188ccc6aef591398fd8d31e162a29390b120e4`。

P5.1 当前决定：在本次 real-mutation experiment 中，Reviewer 与 Executor 的 Codex filesystem sandbox 均禁用。角色隔离暂由 prompt 明确定义；Reviewer 仅 inspection/review，不得修改 target 或其 Git state，Executor 仅可在 bounded task 范围内修改 target 并创建 ordinary descendant commit。两者均不得修改 framework/workload governance 或无关外部文件。

现有确定性 post-turn 审计继续生效，包括 target branch/HEAD/cleanliness、Reviewer target immutability、ordinary descendant history、merge prohibition、governance hashes、instruction freshness、thread relationship 与 fail-closed behavior。Python 仍仅执行机械路由与验证，不解析 Agent natural-language semantics。

该 execution policy 是当前实验的临时选择，**不是 permanent architecture invariant**。本 repair 完成后尚未重新运行 `multiLanguage_v1` real mutation workload。

### 2026-09-06 — P5.1 real mutation smoke accepted

Status: `ACCEPTED — REAL MUTATION PATH VERIFIED`

Disposable smoke root:

`/Users/smterpro/Documents/deletable/p51-real-mutation-smoke-20260906`

Run:

`20260906T092213Z-51515`

Purpose:

Verify that the P5.1 no-filesystem-sandbox execution policy closes the real
`.git/index.lock` blocker observed in the first `multiLanguage_v1` attempt.

Observed real Codex sequence:

Reviewer new persistent
→ Executor fresh ephemeral
→ Reviewer explicit resume
→ Executor fresh ephemeral no-op
→ Reviewer explicit resume
→ `STOPPED_FOR_HUMAN_REVIEW`

Cycle 1:

- before: `e35162dc38a8aa891a02333c56e1d8829d45a66f`
- after: `d8d535452dc11c132749782b9e9a4dccd9431b2a`
- `head_changed = true`

The Executor successfully:

- created `P51_SMOKE.txt`;
- wrote the exact required bytes `P5.1 real mutation smoke PASS\n`;
- created ordinary descendant commit `d8d535452dc11c132749782b9e9a4dccd9431b2a`;
- changed no existing tracked file;
- left the target working tree clean.

The Reviewer independently inspected the actual target commit, parent, file bytes,
tree contents and cleanliness and required no repair.

Cycle 2:

- before: `d8d535452dc11c132749782b9e9a4dccd9431b2a`
- after: `d8d535452dc11c132749782b9e9a4dccd9431b2a`
- `head_changed = false`

The Executor correctly performed no mutation. The Reviewer still received and
reviewed the Executor payload before the orchestrator mechanically stopped:

- status: `STOPPED_FOR_HUMAN_REVIEW`
- reason: `target_head_unchanged`

This real-service smoke verifies that disabling the Codex filesystem sandbox for
the current experiment permits the Executor to complete the required
workspace-mutation + Git-commit path while existing post-turn mechanical auditing
remains effective.

The earlier `.git/index.lock` blocker is therefore closed for the current P5.1
execution policy.

This acceptance does not make no-sandbox execution a permanent architecture
invariant.

### 2026-09-06 — P5.1 real medium-scale workload completed

Status: `REAL WORKLOAD CONTROL-PLANE PATH VERIFIED`

Real workload run:

`20260906T102252Z-52187`

Target:

- repository: `live_subtitle_generator`
- branch: `multiLanguage_v1`
- baseline HEAD: `b5188ccc6aef591398fd8d31e162a29390b120e4`
- final HEAD: `b9f61b39384001eae07c94d114ae66dcba0873cb`
- final working tree: clean

Control-plane result:

- `3` cycles;
- `7 / 7` Codex turns successful;
- Cycle 1 and Cycle 2 each created one ordinary descendant target commit;
- Cycle 3 was a clean Executor no-op;
- Reviewer was created once as a persistent thread and explicitly resumed for all
  three review turns;
- observed Reviewer resume relationships were mechanically verified;
- the unchanged-HEAD Executor payload still reached the Reviewer review turn;
- final status: `STOPPED_FOR_HUMAN_REVIEW`;
- final reason: `target_head_unchanged`.

Observed sequence:

```text
Reviewer new persistent
-> Executor fresh ephemeral / mutation commit
-> Reviewer explicit resume / independent review
-> Executor fresh ephemeral / mutation commit
-> Reviewer explicit resume / independent review
-> Executor fresh ephemeral / no-op
-> Reviewer explicit resume / final review
-> mechanical Human gate
```

Usage/cache observation:

```text
Reviewer aggregate:
  turns      = 4
  input      = 1586733
  cached     = 1481216
  uncached   = 105517
  cache hit  = 0.933500
  output     = 10101
  reasoning  = 6026
  duration   = 261.272s

Executor aggregate:
  turns      = 3
  input      = 1365588
  cached     = 1232896
  uncached   = 132692
  cache hit  = 0.902832
  output     = 14925
  reasoning  = 5110
  duration   = 365.804s

Total:
  input      = 2952321
  cached     = 2714112
  uncached   = 238209
  cache hit  = 0.919315
  output     = 25026
  reasoning  = 11136
  duration   = 627.076s
```

Later Reviewer resume turns observed cache-hit ratios of `0.957524`, `0.966395`,
and `0.987021`.

These are single-run observations only. They do not establish a causal benchmark
for persistent Reviewer sessions because prompt shape, target state, service-side
cache state, and task complexity were not independently controlled here.

Semantic-boundary observation:

Human review of the opaque Reviewer final messages found `0` rejection events and
`0` repair-request events in this run. Cycle 1 accepted the implementation slice
and issued one bounded documentation task; Cycle 2 judged the workload ready for
Human review; Cycle 3 reaffirmed the no-op handoff.

These are Human semantic observations, not Python-derived control-plane fields.
Python did not classify `ACCEPT`, `REJECT`, `READY`, or equivalent wording. It
stopped only after the mechanical unchanged-HEAD condition, after the no-op
Executor payload had still been routed to Reviewer review.

Target regression was repeatedly reported/reproduced as `106` tests with `105`
passes and the same single pre-existing project-local Python-path assertion
failure. Reviewer also audited the existing ASCII-centric `TOKEN_RE` behavior and
classified it as non-blocking for this workload boundary.

Effective interpretation:

- the `.git/index.lock` blocker exposed by run `20260906T083312Z-48975` is closed
  for the current P5.1 execution policy;
- P5.1 is now supported by deterministic validation, a disposable real-Git-mutation
  smoke, and one real medium-scale external-repository workload;
- disabling the Codex filesystem sandbox remains a temporary implementation choice,
  not a permanent architecture invariant;
- current role separation is prompt-defined and mechanically audited after turns;
  it is not a hard filesystem capability boundary;
- final target merge and product acceptance remain outside Python and belong to
  the Human Owner.

### 2026-09-06 — P5.1 Human Gate accepted and stage closed

Status: `HUMAN ACCEPTED — MEDIUM-SCALE WORKLOAD PHASE CLOSED`

Human Gate result:

- Japanese live audio was successfully transcribed through Whisper;
- French live audio was successfully transcribed through Whisper;
- observed Japanese/French quality was subjectively comparable to the existing
  Chinese/English experience;
- the source-run `whisper-cli not found` environment blocker was operationally
  closed before successful transcription;
- Spanish, German, Korean and Auto Detect were not manually exercised because of
  available testing time;
- `.en` rejection and UI-locale/code preservation were not reported as manually
  exercised in this Human Gate;
- those unexercised paths retain deterministic-test, shared implementation-path and
  Reviewer-inspection evidence, but are not classified as Human-tested.

Human Owner accepts those explicit residual limits. This closes the current
medium-scale workload phase without run #3. It does not claim multilingual WER/CER,
push the target branch, or merge the target into `main`.

Stage summary and next-phase analysis:

`1PCloop/docs/p51_medium_scale_stage_summary.md`

Framework interpretation:

- research relevance is materially stronger because evidence now spans a real
  sandbox failure, fail-closed recovery, policy repair, deterministic validation,
  disposable Git smoke, real external-repository mutation, independent review,
  mechanical Human Gate and live transcription;
- this remains a research-ready prototype signal rather than a research conclusion:
  there is one real medium-scale workload, no replicate, no comparative self-review
  arm, no real loop rejection/repair event and only partial language smoke;
- overall 1PCloop remains `ACTIVE` under the Static Completion Definition;
- recommended next work is P6-A controlled `REJECT -> REPAIR -> re-review`, followed
  separately by P6-B capability-gated authoritative verdict/Runtime transition;
- crash/restart reconstruction and a durable curated-evidence policy remain pending
  control-plane work.

## 2026-09-06 — P5 non-blocking cleanup completed

Status: `CLOSED — EVIDENCE RECORDED`

The three implementation-adjacent non-blocking items recorded during P3/P5 are no
longer open cleanup work:

1. **Event-metadata robustness.** `run_text_loop.py` now treats more than one
   `turn.completed` usage record as ambiguous instead of silently selecting the last;
   it also marks cache-derived metrics unavailable when
   `cached_input_tokens > input_tokens`, so no negative uncached-token value is
   emitted. Unrelated valid output metrics remain available. The shared P5 runner
   uses this helper. New regression coverage plus the existing text/mutation suites
   passed `25 / 25`.
2. **Project-local Python environment.** The target's formal
   `bootstrap_python_env.sh --recreate` path recreated the ignored `.venv` against
   the already-frozen project `.tools/python` location. This resolves the former
   pre-existing assertion caused by an old virtual environment pointing at user-level
   uv Python; no tracked dependency contract changed.
3. **CJK/Korean exact transcript overlap.** Target commit
   `088f1071280e656f85b5abb2bbce1fc06bc9925c` publishes character-level comparison
   tokens for continuous Japanese/Chinese/Korean text, preserving the established
   ASCII word/contraction path. Japanese/Korean exact-boundary regression tests and
   the target's full suite passed `108 / 108`. This is deliberately not a claim of
   fuzzy semantic deduplication, manual Korean transcription, or multilingual
   WER/CER.

The remaining Spanish/German/Korean/Auto Detect manual-smoke gap is an explicitly
accepted Human Gate coverage boundary, not an unacknowledged blocker. Historical
references to stale Codex rollout paths, prior profile-internal locations, and raw
run-log growth remain archived context rather than active work: the current execution
path does not depend on them, and raw P5.1 evidence plus the lossless Runtime archive
are already committed.

No further P5 non-blocking cleanup is pending. P6 crash/restart reconstruction,
capability-gated authoritative Runtime transition, rejection/repair evidence, and
curated-evidence policy remain intentionally scoped next-phase control-plane work;
they must not be mislabeled as small maintenance fixes.

## 2026-09-06 — P6 Human-authorized control-plane hardening plan

Status: `ACCEPTED / PHASE CLOSED — P6.1, P6.2, P6.3 AND P6.4 ACCEPTED`

This section records the authoritative P6 plan that superseded the earlier proposed
sequencing placing controlled `REJECT -> REPAIR -> re-review` before Runtime
transition work. The Human Owner decided that P6 would first close the known
control-plane gaps below and defer controlled rejection/fault injection to P7.

The plan itself was not evidence that its mechanisms had already been accepted. Each
subphase therefore had to be implemented, mechanically tested, independently reviewed
and separately recorded before its status could change to accepted.

### P6.0 — Approved scope and authority boundary

Status: `DECISION COMPLETE — DEFINES P6 IMPLEMENTATION BOUNDARY`

The approved scope is:

1. implement runtime-enforced structured Agent outputs and a capability-gated
   Reviewer `ACCEPT -> workload Runtime transition` path;
2. implement an overwrite-in-place local checkpoint sufficient for crash/restart
   reconstruction, plus live terminal progress output;
3. stop committing future raw run evidence by default; retain it locally under a
   Git-ignored path and commit a concise LLM-authored per-turn evidence summary;
4. retain the current sequential, non-awaiting Reviewer/Executor lifecycle and do
   not add background Agents, locks, watchers, or multi-writer coordination;
5. do not extend or live-test concurrent target-HEAD refresh in P6; document the
   single-contributor/single-loop operating assumption and existing deterministic-only
   validation boundary;
6. defer controlled `REJECT -> REPAIR -> re-review` fault injection until P7.

Only a workload Runtime that explicitly opts into orchestrator-mediated Reviewer
transition may be mutated by the P6 loop. Framework Static and framework Runtime
remain read-only governance inputs during the loop under test. The closed
`multiLanguage_v1` workload is not a destructive P6 transition fixture: its current
Static says that its Runtime is Human-owned, and its accepted history must not be
retroactively repurposed. P6 validation must use a disposable repository and paired
workload governance, or a new bounded workload whose Static explicitly grants this
capability.

Executor remains unable to accept its own work or modify any Runtime. Reviewer may
request a transition only through the validated control-plane output described below.
Python remains prohibited from searching free text for `ACCEPT`, `REJECT`, readiness,
or any equivalent semantic marker.

Human-mandated execution protocol used for the remaining P6.x subphases:

1. reason about the intended change logic before editing;
2. inspect the affected behavior, files and dependencies and read the necessary
   sources first;
3. use that observed context to revise the initial change logic when needed;
4. implement only the resulting bounded subphase;
5. run proportionate focused and regression tests;
6. update this Runtime after testing with the implementation result, evidence
   locator, observed limitations, and a concise description of test logic rather
   than copying complete test source.

This protocol governed P6.2 and later P6.x work through P6 closure.

### P6.1 — Overwrite-only local checkpoint and visible execution progress

Status: `IMPLEMENTED AND DETERMINISTICALLY ACCEPTED`

Implement one current local checkpoint per workload/run key under a Git-ignored path,
with a default layout equivalent to:

```text
1PCloop/.local/state/<workload-id>/checkpoint.json
```

The checkpoint is recovery state, not long-term research evidence. Each transition
must atomically replace the same file through a temporary file, flush/fsync as needed,
and `os.replace`; it must not create an append-only checkpoint history. A later run
may overwrite a terminal checkpoint. An incomplete checkpoint must not be silently
discarded by a new run: the runner must resume it or stop for an explicit Human
discard decision.

Minimum checkpoint state machine:

```text
PREFLIGHT_PASSED
REVIEWER_INSTRUCTION_RUNNING
INSTRUCTION_READY
EXECUTOR_RUNNING
EXECUTOR_COMMITTED
REVIEW_PENDING
REVIEW_COMPLETED
RUNTIME_TRANSITION_PENDING
RUNTIME_TRANSITION_COMMITTED
HUMAN_GATE
FAILED_CLOSED
```

Minimum checkpoint content:

- schema version, run/workload ID and cycle number;
- current state and last completed state transition;
- Reviewer thread ID when available;
- target repository, branch, known HEAD and worktree expectation;
- framework/workload Static and Runtime hashes;
- current instruction, Executor receipt and Reviewer verdict local locators plus
  content hashes;
- whether the per-turn summary was already appended;
- whether Runtime transition, framework evidence commit and push were already
  completed.

Restart behavior must be idempotent:

- compare checkpoint state against the actual branch, HEAD, worktree and governance
  hashes before resuming;
- resume only the next incomplete action;
- never re-run an Executor whose commit is already recorded and verified;
- never append or apply the same Runtime transition twice;
- reuse the Reviewer thread when its relationship can still be verified;
- if the Reviewer thread is unavailable, create a fresh Reviewer and fully bootstrap
  it from repository-backed governance plus the pending evidence payload;
- if actual state cannot be reconciled mechanically, fail closed or enter Human Gate
  instead of reset, checkout, stash, history rewrite, or guessed recovery.

The runner must also emit live, flushed terminal progress. A long Codex turn may not
appear silent until `subprocess.run()` returns. The implementation should stream
process output to local raw evidence while showing concise terminal events and a
periodic elapsed-time heartbeat, including at least:

```text
timestamp / run / cycle / role / state / elapsed time / target HEAD
```

Terminal output should expose turn start, useful tool/test activity, turn completion,
validation, verdict, transition, Human Gate and failure. It should not dump the entire
raw JSONL stream or hidden reasoning to the terminal.

P6.1 acceptance requires deterministic crash simulation after the important state
boundaries, successful reconstruction of the exact next action, proof that Executor
commits and Runtime transitions are not duplicated, and captured evidence that
progress is visible and flushed while a turn is still running.

Implementation result:

- implementation commit: `b2afc37113250dc5180879a053a3b9c99f8dfb1d`;
- `run_mutation_loop.py` now maintains one schema-versioned checkpoint at
  `1PCloop/.local/state/<workload-id>/checkpoint.json` by default;
- checkpoint writes use a same-directory temporary file, file flush/fsync,
  `os.replace`, and directory fsync where available, so advancing a state replaces
  the prior checkpoint rather than creating checkpoint history;
- `.gitignore` excludes `1PCloop/.local/`; an accidentally generated development
  checkpoint was removed after validation, so no P6.1 checkpoint artifact was
  committed;
- a non-terminal checkpoint blocks a new run unless `--resume` is explicit; a
  terminal checkpoint may be replaced by a later run;
- the checkpoint records configuration identity, run/cycle, state transition,
  Reviewer thread and known hashes/HEAD, complete cycle/process recovery metadata,
  instruction/receipt references and hashes, target before/after state, plus reserved
  summary/Runtime-transition/commit/push flags for later P6 phases;
- resume revalidates the exact configuration, run root, target branch/HEAD/worktree
  and governance hashes, then continues from the next incomplete state;
- completed Reviewer/Executor artifacts are reloaded only after their final-message
  hashes and successful process records validate;
- an Executor commit checkpointed before a crash is reviewed after restart without
  launching the Executor again;
- a crash before Executor launch permits one safe retry only when target HEAD and the
  clean worktree still equal the checkpointed preimage;
- an unrecorded target commit observed from `EXECUTOR_RUNNING` is not attributed to
  the Executor and stops at `HUMAN_GATE / executor_outcome_ambiguous_after_restart`;
- an incomplete/uncertain Reviewer attempt can be replaced by a fresh fully
  bootstrapped Reviewer because Reviewer is read-only and conversation state is not
  authoritative;
- Codex execution now uses a streaming subprocess path: raw stdout/stderr are written
  while the process runs, selected public event types and a periodic heartbeat are
  printed with timestamp/run/cycle/role/state/elapsed/target-HEAD context, and output
  pipes are closed deterministically;
- handled parent interruptions terminate the active Codex child before propagating
  the interruption, preserving the sequential non-background-Agent lifecycle;
- new CLI controls are `--state-root`, `--workload-id`, `--resume`, and
  `--progress-interval-seconds`; README documents the operator path.

P6.1 test logic/evidence summary:

1. **Atomic overwrite test.** Write two different checkpoint states to one path,
   reload the file, verify only the second state remains, and verify the checkpoint
   directory contains no versioned/temp history file.
2. **Explicit-resume gate.** Inject a deterministic process-level stop immediately
   after `INSTRUCTION_READY`; verify a new non-resume run is rejected, then resume
   the existing run and reach the expected Human Gate.
3. **Pre-Executor idempotence.** Stop immediately after the durable
   `EXECUTOR_RUNNING` state but before launch; verify zero Executor calls before the
   stop and exactly one Executor call across the resumed run.
4. **Post-commit idempotence.** Use a fake Executor that creates a real ordinary Git
   descendant commit, stop immediately after `EXECUTOR_COMMITTED`, resume, and verify
   that the target commit is retained, the Executor call count remains exactly one,
   and Reviewer review completes.
5. **Review-boundary idempotence.** Independently stop at `REVIEW_PENDING` and
   `REVIEW_COMPLETED`; verify resume invokes the missing review exactly once in the
   former case and invokes no additional Reviewer in the latter case.
6. **Ambiguous mutation safety.** Stop before Executor launch, insert an otherwise
   valid external descendant commit, then resume; verify no Executor is launched and
   the run stops for Human review instead of claiming or overwriting the commit.
7. **Live-progress test.** Run a deliberately slow fake Codex event stream with a
   short heartbeat interval and capture stdout; verify process-start, in-flight
   heartbeat, process-finish, target HEAD and terminal checkpoint are visible.
8. **Existing invariant regression.** Re-run Reviewer-read-only, Executor-clean-tree,
   governance-protection, opaque-payload transport, thread-resume and target-history
   tests to ensure checkpoint/restart behavior did not weaken the P5 boundary.
9. **Resource lifecycle check.** Run the complete suite with Python
   `ResourceWarning` promoted to an error, verifying the streaming implementation
   leaves no unclosed stdout/stderr pipe warning.
10. **Real-target read-only preflight.** Run P6.1 CLI preflight against
    `live_subtitle_generator` branch `multiLanguage_v1` at
    `088f1071280e656f85b5abb2bbce1fc06bc9925c`; verify the target is clean, all four
    governance inputs are readable/hashed, both profiles resolve, and no run or
    checkpoint is created.

Observed result:

```text
python3 -m unittest discover -s 1PCloop/tests -v
32 tests run / 32 passed
ResourceWarning strict run / passed
real target --preflight-only / passed
```

Interpretation boundary:

- deterministic crash tests raise immediately after durable checkpoint boundaries;
  they do not yet constitute a real `kill -9` experiment during a live Codex service
  turn;
- if a crash occurs during an Executor turn after an unrecorded commit, P6.1 chooses
  Human Gate rather than unsafe automatic replay;
- P6.1 does not parse verdict JSON, mutate Runtime, generate tracked evidence
  summaries, or change future raw-run retention; those remain P6.2/P6.3 scope;
- Runtime-transition states and associated idempotence flags exist as reserved
  checkpoint fields, but no authoritative Runtime write is enabled by P6.1.

P6.1 satisfies its deterministic acceptance boundary. The authoritative Active Step
therefore advances to P6.2.

### P6.2 — Runtime-enforced JSON verdict and authoritative Runtime transition

Status: `IMPLEMENTED AND DETERMINISTICALLY ACCEPTED`

Use the Codex CLI runtime-enforced `--output-schema` mechanism. Prompt-only requests
to emit JSON are insufficient. P6 turn schemas must preserve a complete Agent-to-Agent
message while exposing a small enumerated control wrapper and an evidence-summary
field. Python may validate and route those declared fields; it must not infer new
semantic fields from the embedded natural-language message.

The Reviewer review schema must include at least:

```json
{
  "schema_version": 1,
  "verdict": "ACCEPT | REJECT | HUMAN_GATE",
  "active_step_id": "string",
  "reviewed_target": {
    "branch": "string",
    "head": "commit sha"
  },
  "expected_runtime_sha256": "string",
  "evidence": [
    {
      "kind": "commit | test | file | artifact",
      "locator": "string"
    }
  ],
  "evidence_summary": "string",
  "peer_message": "string",
  "next_instruction": "string or null",
  "runtime_transition": {
    "new_status": "string",
    "next_active_step": "object or null"
  }
}
```

Exact production schema may split common turn fields from verdict-only fields, but
must retain the following behavior:

- the complete schema-conforming raw payload is transported to the peer without
  Python rewriting its natural-language meaning;
- every turn supplies a concise LLM-authored `evidence_summary`;
- only Reviewer review turns can carry an authoritative verdict;
- Executor output cannot trigger acceptance or Runtime progression;
- `ACCEPT` requires a non-empty mechanically checkable evidence list, an exact current
  target branch/HEAD, the exact Runtime preimage hash, current governance hashes, and
  a verified Reviewer session/role relationship;
- commit locators must exist and be reachable from the current target HEAD; file and
  artifact locators must satisfy the configured evidence boundary;
- stale hash, stale HEAD, missing evidence, wrong role, malformed JSON or schema
  mismatch fails closed;
- `REJECT` requires one bounded `next_instruction` and performs no Runtime transition;
- `HUMAN_GATE` stops and performs no Runtime transition;
- `ACCEPT` must not carry a repair instruction and may progress only the explicitly
  authorized workload Runtime.

The workload Runtime should contain one uniquely delimited machine-owned current-state
JSON block. Python validates and replaces only that block and appends a deterministic
transition record; it does not semantically parse the surrounding Markdown. Runtime
write must use a validated preimage hash and atomic replacement. The transition record
must include transition ID, prior/new state, Reviewer verdict locator, target HEAD,
evidence locators and hashes, and timestamp.

The initial safe behavior is to apply one accepted transition and stop after recording
`RUNTIME_TRANSITION_COMMITTED`. Continuous next-step execution may be enabled only
after this one-transition path passes deterministic tests and a disposable real smoke.

P6.2 acceptance tests must cover valid ACCEPT, invalid/schema-breaking output, stale
Runtime hash, stale target HEAD, missing or unreachable evidence, attempted Executor
ACCEPT, REJECT without Runtime mutation, HUMAN_GATE without Runtime mutation, atomic
write failure, and restart after a completed write without duplicate transition.

Implementation result:

- implementation commit: `d56a5c6fd0bffe183f368d52ca4f555cbefae9e6`;
- Reviewer instruction, Executor receipt and Reviewer verdict use three independent
  schemas, and every fresh, ephemeral or resumed turn supplies its own
  `--output-schema`;
- final output is validated again locally against the same schema, with duplicate
  keys and non-standard JSON constants rejected;
- only the Reviewer review turn has verdict authority; Reviewer instruction and
  Executor receipt cannot carry an authoritative verdict;
- Runtime transition requires both the Human CLI capability
  `--enable-runtime-transition` and an opted-in workload Runtime machine block;
- ACCEPT mechanically verifies target repository/branch/HEAD/cleanliness,
  framework and workload governance hashes, Runtime preimage, active step,
  Reviewer thread/profile relationship, and every evidence locator/hash;
- the deterministic orchestrator performs a same-directory temporary write,
  flush/fsync, `os.replace`, postimage verification and one appended transition
  record, then stops after one transition;
- restart reconciliation covers `RUNTIME_TRANSITION_PENDING`, an already-written
  postimage without a committed checkpoint, and `RUNTIME_TRANSITION_COMMITTED`
  without replaying the transition;
- the complete schema-conforming peer JSON bytes continue to be routed verbatim;
  Python does not re-encode or summarize the peer message.

Test logic/evidence summary:

1. A valid Reviewer ACCEPT advances one opted-in disposable Runtime exactly once.
2. Malformed JSON, schema-invalid output and output from a role without verdict
   authority fail closed, including free text containing `ACCEPT`.
3. Stale Runtime/governance/target state or a mismatched active step fails closed.
4. Missing, unreachable, out-of-boundary or hash-mismatched evidence fails closed.
5. REJECT and HUMAN_GATE reach their defined control states without writing Runtime.
6. A simulated atomic-replace failure retains a complete preimage; deterministic
   stops at the PENDING, post-write and COMMITTED boundaries resume without
   duplicating Agent turns, Runtime writes or transition records.
7. A fresh Reviewer reconstruction must perform the complete governance bootstrap;
   tests also preserve protected-governance and target-cleanliness checks.
8. The focused P6.2 suite passed `21 / 21`; the complete P4/P5/P6.1/P6.2 regression
   passed `53 / 53` with `ResourceWarning` promoted to an error.
9. A disposable real-service smoke completed `3 / 3` turns, mechanically verified
   the Reviewer resume relationship, applied one Runtime transition and stopped at
   `RUNTIME_TRANSITION_COMMITTED`.

Interpretation boundary:

- `jsonschema` is a new explicit runtime dependency; the runner must use a Python
  environment with `1PCloop/requirements.txt` installed;
- raw smoke evidence remains disposable local evidence rather than durable Git
  provenance;
- raw evidence default migration, tracked per-turn summaries and terminal-state
  automatic commit/push remain P6.3 work;
- validation did not perform a real `kill -9`, P7 fault injection or a live
  concurrent target-HEAD experiment;
- the supported operating boundary remains single writer with no concurrency
  guarantee;
- the closed `multiLanguage_v1` workload was neither reopened nor used as a Runtime
  transition fixture.

At the P6.2 checkpoint, the independent Reviewer verdict closed P6.2 while P6 as a
whole remained active; P6.3 then became the sole authoritative Active Step, P6.4
remained queued, and P7 remained deferred.

### P6.3 — Local raw evidence and tracked per-turn summary

Status: `IMPLEMENTED, VALIDATED AND INDEPENDENTLY ACCEPTED`

Future raw evidence must default to a Git-ignored path equivalent to:

```text
1PCloop/.local/runs/<run-id>/
```

This includes prompts, raw `events.jsonl`, stderr, process detail, peer payload copies,
checkpoint material and full final-message bytes. Existing committed historical runs
remain untouched; adding an ignore rule does not rewrite or shrink existing Git
history.

The tracked durable artifact should be equivalent to:

```text
1PCloop/evidence-summaries/<run-id>.md
```

After every completed turn, Python appends a deterministic heading and mechanical
metadata plus that turn's LLM-authored `evidence_summary`. Each entry should include
role/cycle, time, input/output target HEAD, relevant governance hashes, cited evidence,
test result when supplied, verdict when applicable, and hashes/locators for local raw
evidence. A compact machine-readable manifest may also be committed when it contains
only the fields required to audit control transitions; full process/event duplication
must remain local.

Appending happens locally after each turn and is checkpointed so restart cannot
duplicate paragraphs. To avoid replacing raw-log growth with commit-count growth,
the framework repository is committed once when the run reaches `ACCEPT`,
`HUMAN_GATE`, or `FAILED_CLOSED`, rather than once per turn. The commit may include
only the summary, compact manifest, accepted Runtime transition and directly required
small governance changes. It must not push or merge the target repository.

After the framework evidence commit, push it to the configured framework remote. A
push failure must be visible in the terminal and checkpoint, preserve the local commit,
and stop safely rather than discard evidence or repeat the accepted target work.

P6.3 acceptance requires proof that new raw evidence is ignored/untracked, summary
entries are complete and non-duplicated across restart, terminal-state framework
evidence is committed once, and push failure is recoverable without replaying Agent
work.

Implementation and independent review result:

- implementation commit: `c782be79890155a706d1492384aa530afc16333f`;
- future mutation-loop raw evidence now defaults to Git-ignored
  `1PCloop/.local/runs/<run-id>/`, while explicit `--runs-root` remains supported and
  committed `1PCloop/runs/` history remains unchanged;
- every completed turn produces one deterministic tracked summary entry containing
  schema-declared evidence summary and bounded mechanical metadata, without copying
  complete peer messages, prompts, events, stderr, process JSON or hidden reasoning;
- summary text is encoded in a fixed Markdown/JSON envelope so multiline text,
  headings, backticks, HTML markers and Unicode cannot inject a second entry or
  control marker;
- summary append uses checkpointed entry bytes and preimage/postimage hashes plus a
  same-directory temporary file, flush/fsync and `os.replace`; restart reconciles
  pre-write, post-write/pre-checkpoint and checkpointed-entry boundaries without
  repeating the Agent turn or summary entry;
- logical outcome remains distinct from evidence finalization through
  `EVIDENCE_FINALIZATION_PENDING`, `FRAMEWORK_EVIDENCE_COMMITTED` and
  `FRAMEWORK_EVIDENCE_PUSHED`;
- one terminal framework evidence commit is bound to the run ID, expected ordinary
  parent, exact path set/blob hashes and configured framework branch/remote/ref/URL;
  its allowlist contains the current run summary and, only after an actually applied
  legal transition, the framework-resident workload Runtime;
- framework push is non-force and framework-only. A rejected push retains the local
  commit; resume verifies or pushes that exact commit without rerunning Agents,
  rewriting Runtime, appending summary entries or creating a second commit;
- Runtime transition recovery remains idempotent while evidence commit/push is
  pending. The target repository is never committed or pushed by the framework
  finalizer.

Independent Reviewer test/evidence summary:

1. The focused P6.3 suite passed `17 / 17` in `36.692s`, covering ignored raw
   storage, ordered bounded summaries, injection-safe text, summary/commit/push crash
   boundaries, terminal outcomes, framework allowlists and target-push prohibition.
2. The complete P4/P5/P6.1/P6.2/P6.3 regression passed `70 / 70` in `97.213s` with
   `ResourceWarning` promoted to an error; `git diff --check` also passed.
3. Disposable real-Git smoke evidence at
   `/private/var/folders/10/81g7llps60j555m_0191lzsc0000gn/T/1pcloop-p63-final-git-smoke-sciux3jb`
   retained `3` Agent calls and `3` summary entries across resume. Its summary
   SHA-256 is
   `ecd10ada6a030a404859fdd4f7736fd84b2e1baa68bcada46887c8ef5eaa0e16`.
4. The smoke created evidence commit
   `b9e629bafce32bdcd92bda092fdd7c867cb04516`; after the first push was rejected,
   resume advanced the framework remote to that exact commit without replay. The
   target remote remained
   `afcb2f064c4c169f1b6bf7a63a4aee80f52d41f3` before and after.

Interpretation boundary:

- the smoke used real disposable Git repositories and a local bare remote, while
  Codex turns used the deterministic test substitute rather than the real Codex
  service;
- validation did not perform a real `kill -9`, P7 fault injection or a live
  concurrent target-HEAD experiment;
- supported operation remains single writer with no concurrency guarantee;
- raw evidence remains Git-ignored local evidence, and old checkpoints are not
  upgraded automatically;
- these limits do not block the independent Reviewer acceptance of P6.3.

At the P6.3 checkpoint, the independent Reviewer verdict closed P6.3 while P6
remained active overall; P6.4 then became the sole authoritative Active Step, and
P7 remained deferred.

### P6.4 — Sequential lifecycle and external-mutation boundary

Status: `IMPLEMENTED, VALIDATED AND INDEPENDENTLY ACCEPTED`

The supported operating assumption is:

```text
one Human contributor
+ one active loop per target repository
+ Reviewer/Executor processes exit after each turn
+ no stopped Agent can continue accessing or mutating the repository
```

P6 will not implement an awaiting Agent, background Agent process, repository lock,
filesystem watcher, multi-Executor queue, or multi-writer reconciliation. Existing
low-cost turn-boundary assertions for branch, HEAD, cleanliness, descendant history,
Reviewer read-only behavior and governance hashes should remain because they also
detect loop/self-state errors. Unexpected state still fails closed; P6 does not
attempt automatic reset or destructive repair.

Target-HEAD refresh receives no new implementation or live concurrent-commit test in
P6. The README must state that the path has deterministic validation only, that the
supported deployment assumes a unique contributor plus the loop as the only normal
writer, and that no concurrency consistency guarantee is claimed. The existing
mechanical checks may remain, but must not be described as a fully validated
multi-contributor coordination mechanism.

Implementation and independent review result:

- implementation commit: `c33c0d2a34a37eb7e85ca0f81664de3e9922bf70` —
  `Document P6.4 sequential lifecycle boundary`;
- the commit changes only `1PCloop/README.md` and adds one directly locatable P6.4
  section for the current sequential lifecycle, unsupported concurrency features,
  external mutation, mechanical checks, Target-HEAD refresh and P7 boundary;
- the documented supported model is one Human contributor, one active loop per
  target and sequential orchestrator-triggered Reviewer/Executor processes; a
  persistent Reviewer thread is resumable session state rather than a background
  Agent process;
- existing branch/HEAD/cleanliness/history/governance/checkpoint/evidence checks are
  retained as sequential-state validation and fail-closed/Human-Gate detection, not
  represented as locking, multi-writer reconciliation or a concurrency protocol;
- Executor validation ran `test_run_mutation_loop.py` with `12 / 12` passing in
  `8.083s`; the independent Reviewer reran the same focused suite with `12 / 12`
  passing in `7.995s`;
- the independent Reviewer also verified `git diff --check`, the README-only commit
  path set, clean synchronized `main`, and consistency between the documentation and
  implementation, then returned `ACCEPT P6.4` with no repair requirement.

Interpretation boundary:

- supported operation remains single writer with no concurrency guarantee;
- P6.4 did not add a lock, watcher, daemon, awaiting/background Agent, parallel
  Executor, multi-writer reconciliation or distributed transaction;
- Target-HEAD refresh has deterministic validation only; no live concurrent
  Target-HEAD commit experiment was performed;
- P6.4 did not modify the REJECT path or execute P7 fault injection.

The independent Reviewer verdict closes P6.4.

### P6 completion gate

P6 may be accepted only after all of the following are true:

1. the local overwrite-only checkpoint and restart state machine pass deterministic
   crash-boundary tests;
2. terminal progress remains visible during long Reviewer and Executor turns;
3. runtime-enforced schemas reject malformed or stale control output;
4. a valid Reviewer ACCEPT atomically advances exactly one opted-in workload Runtime
   and cannot be replayed;
5. REJECT and HUMAN_GATE do not advance Runtime;
6. raw evidence defaults to ignored local storage;
7. a concise per-turn LLM evidence summary plus compact required metadata is committed
   once at terminal state and pushed to the framework remote;
8. the single-writer/no-concurrency boundary is documented;
9. existing text-loop and mutation-loop deterministic regressions remain green;
10. a disposable real-Git smoke demonstrates the accepted one-transition path without
    modifying or reopening the closed `multiLanguage_v1` workload.

P6 completion decision — `ACCEPTED / PHASE CLOSED`:

- criteria 1–2 are covered by the accepted P6.1 checkpoint/restart and live-progress
  evidence;
- criteria 3–5 are covered by the accepted P6.2 schema, authority, capability-gated
  transition, REJECT/HUMAN_GATE and replay-prevention evidence;
- criteria 6–7 are covered by the accepted P6.3 ignored-raw-evidence, tracked-summary,
  one-commit and recoverable framework-push evidence;
- criterion 8 is covered by the accepted P6.4 README boundary;
- criterion 9 is covered by the P6.3 `70 / 70` ResourceWarning-strict regression;
- criterion 10 is covered by the P6.2 disposable real-Codex/real-Git one-transition
  smoke, which did not modify or reopen the closed `multiLanguage_v1` workload.

All P6 subphases are independently accepted and the completion gate is satisfied.
P6 is closed without claiming locking, concurrency safety, a real `kill -9`, a live
concurrent Target-HEAD experiment or P7 fault injection. At the P6-closure
checkpoint, P7 became the next Active Step; the Human Owner's `2026-09-12`
engineering-foundation decision above supersedes that activation.

### P7 sequencing decision

Status: `PAUSED BY HUMAN OWNER / NOT ACTIVE`

P7 在 P6 关闭时曾被激活为下一 engineering-coverage step。Human Owner 于 `2026-09-12`
暂停该状态并将当前资源转向 foundation_v1；这是 current authoritative supersession。P7
未删除，只有 Human Owner 明确重新激活后才可执行。旧 paper/research 路线不构成重新激活授权。

P7 retains the authorized objective of introducing a controlled, explicitly recorded
defect in a disposable repository or dedicated test branch to exercise:

```text
Reviewer detects defect
-> REJECT
-> bounded repair instruction
-> fresh Executor repairs
-> same Reviewer re-reviews
```

The injected commit, actor, timing, expected defect and experiment boundary must be
recorded so the result is not misreported as a naturally occurring Executor error.
No defect has been introduced and no P7 fault injection has been completed. While P7
is paused, its objective is retained only as historical/future scope. foundation_v1
was the sole current engineering task from its `2026-09-12` activation through its
`2026-09-18` accepted phase closure; there is now no active engineering task.
