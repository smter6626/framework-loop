# Miniloop Runtime

## 任务状态

`ACTIVE`

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

### 2026-09-05 — P4-A paired experiment execution evidence

Status: `EXPERIMENT COMPLETED — AWAITING REVIEW`

Step: `Step 1 P4-A`

Implementation commit:

- `0496fba156083f08e7d1975069330ec131d4ad0e` — 同一 orchestrator 的 control/treatment session mode、frozen experiment metadata、resume relationship fail-closed 验证与 tests。

Frozen experiment metadata:

```text
experiment_id = p4a-20260905-01
git_head = 0496fba156083f08e7d1975069330ec131d4ad0e
git_branch = main
git_status_clean = true
codex_version = codex-cli 0.153.4
run_order = ephemeral-control -> reviewer-resume-treatment
control = 2026-09-05T14:16:17.565+00:00 -> 2026-09-05T14:17:12.769+00:00
treatment = 2026-09-05T14:17:57.332+00:00 -> 2026-09-05T14:18:40.699+00:00

static_sha256 = f2fc9b87a11078c4cb5bf8cef1c9de95d297f2ad1e7e1164db8f096d573818fe
runtime_sha256 = 81f900d47c1ed35569ab65d1a257c625deaf1ede244ddc929e9c187012940f3c
reviewer_initial_prompt_sha256 = 45bffaf32f38e366c301ead816bb9841c53f41b8b09890c1f49acef9952cfabd
executor_prompt_sha256 = 35f282083549c4bf8713b41a45a0766e0992a04f1d0c25ffe4aeb4d70f833534
reviewer_review_prompt_sha256 = c909004ac949929fef4b80335a2b07b66b8e42b3a656bef923ef33c8e8cd6b59

Reviewer CODEX_HOME = /Users/smterpro/.codex-B
Reviewer config.toml sha256 = 11173f577eb124c2741f18c7bfde61d392756b002e01c92b0ae812eaeba814ef
Reviewer configured model / reasoning = gpt-5.6-terra / high

Executor CODEX_HOME = /Users/smterpro/.codex-A
Executor config.toml sha256 = ebcd087bb6d87b551b036cb035bd7d631a9cea731ad8dfca88c550e3e2dbb16c
Executor configured model / reasoning = gpt-6-astra / high

sandbox = read-only
approval_policy = never
```

Model 与 reasoning 值仅来自 experiment-start 时 `config.toml` 的顶层非敏感字段；当前 JSONL 没有独立报告 observed model configuration。Experiment metadata 没有读取或复制 `auth.json`、credential 或完整 profile state。

Measured results:

```text
Control — ephemeral-control
  Reviewer T1: input 59049, cached 42240, uncached 16809, cache 0.715338,
               output 818, reasoning 522, duration 27.405s
  Executor T2: input 15706, cached 11520, uncached 4186, cache 0.733478,
               output 78, reasoning 20, duration 12.449s
  Reviewer T3: input 33663, cached 24064, uncached 9599, cache 0.714850,
               output 415, reasoning 238, duration 15.345s
  Aggregate:   input 108418, cached 77824, uncached 30594, cache 0.717814,
               output 1311, reasoning 780, duration 55.199s

Treatment — reviewer-resume-treatment
  Reviewer T1: input 60526, cached 41216, uncached 19310, cache 0.680964,
               output 714, reasoning 429, duration 23.825s
  Executor T2: input 15503, cached 11520, uncached 3983, cache 0.743082,
               output 85, reasoning 23, duration 9.088s
  Reviewer T3: input 26014, cached 24320, uncached 1694, cache 0.934881,
               output 232, reasoning 175, duration 10.449s
  Aggregate:   input 102043, cached 77056, uncached 24987, cache 0.755133,
               output 1031, reasoning 627, duration 43.362s

Delta — Treatment minus Control
  Reviewer T3 uncached_input_tokens = -7905 (-82.3523%)
  Aggregate uncached_input_tokens   = -5607 (-18.3271%)
  Reviewer T3 cached_input_tokens   = +256
  Reviewer T3 input_tokens          = -7649
  Aggregate input_tokens            = -6375 (-5.8800%)
  Aggregate duration_seconds        = -11.837 (-21.4442%)
```

Resume mechanical proof:

```text
created_thread_id         = 01a071ee-e9a1-7a40-89f5-098da93d94f7
resume command target     = 01a071ee-e9a1-7a40-89f5-098da93d94f7
resume_target_thread_id   = 01a071ee-e9a1-7a40-89f5-098da93d94f7
observed thread.started   = 01a071ee-e9a1-7a40-89f5-098da93d94f7
resume_relationship_verified = true
T3 --ephemeral            = false
```

Treatment T1 没有使用 `--ephemeral`；Executor T2 仍使用 fresh `--ephemeral`；T3 只有一次显式 resume invocation。没有发生 resume-to-fresh fallback。两组各三个 process 均 exit code `0`，四次 peer transport 均通过 SHA/byte identity 检查。

Observed Static / Runtime read behavior:

- Control Reviewer T1 使用固定 `sed` 范围读取 Static `1-520`、Runtime `1-620`；frozen Static 共 `534` 行，因此遗漏 Static `521-534`；
- Control Reviewer T3 只读取 Static `1-240` 与 Runtime `1-260`；frozen Runtime 的 Active Step 从第 `361` 行开始，因此该 fresh review turn 没有通过该命令读到当前 Active Step；
- Treatment Reviewer T1 使用固定范围读取 Static `1-480` 与 Runtime `1-520`，遗漏两份文件尾部；
- Treatment Reviewer T3 resume 后没有再次执行 Static / Runtime read command；
- 两组 Executor T2 均未执行 Static / Runtime read command；
- P4-A 按约束没有修改 role prompt 或 context-read policy；这些 reconstruction correctness 观察只作为后续候选 P4-B evidence。

Experiment limitations / confounders:

- 本次只有一个 `Control -> Treatment` pair，服务端 prompt-cache warm order 仍是 confound；没有自行追加 reversed-order replicate；
- role prompt prefix 与治理文件已冻结，但两次 Reviewer 的 stochastic output 不同，使后续 T2/T3 的完整动态 prompt hash 不同；
- duration 包含单次实验的 service、network、inference 与 tool-execution variation；
- 更高 cache-hit ratio 不被单独解释为更低成本；主要 observation 同时报告 total input 与 uncached input；
- 固定 `sed` 范围存在实际遗漏，因此本实验不能证明 authoritative reconstruction 已完整或最优；
- 单个 pair 只构成本次 run evidence，不决定 Reviewer resume 的最终架构地位。

Evidence locator:

- `1PCloop/runs/p4a-paired-20260905-01/experiment.json`；
- `1PCloop/runs/p4a-paired-20260905-01/comparison.json`；
- `1PCloop/runs/p4a-paired-20260905-01/control/manifest.json`；
- `1PCloop/runs/p4a-paired-20260905-01/control/transcript.md`；
- `1PCloop/runs/p4a-paired-20260905-01/treatment/manifest.json`；
- `1PCloop/runs/p4a-paired-20260905-01/treatment/transcript.md`；
- 两组各 turn 的原始 `events.jsonl` 与派生 `process.json`。

Decision boundary:

P4-A 实验执行已完成，现在等待 Reviewer / Human Owner 审阅。该记录不是最终 `ACCEPT`，不自动保留或放弃 Reviewer resume，不启动 P4-B、persistent Executor、workspace mutation 或 automatic Runtime transition。

---

## 当前活跃步骤

### Step 1 — P4-A paired experiment completed; awaiting review

状态：`EXPERIMENT COMPLETED — AWAITING REVIEW`

### 当前目标

向 Reviewer / Human Owner 提交 frozen P4-A paired evidence，等待对 Reviewer resume 的 evidence-backed 决策。当前不再执行额外 Codex experiment call，不做 reversed-order replicate，也不进入 P4-B。

本次实验研究问题保持为：

> 在其他条件保持一致时，仅把 Reviewer 的第三回合从 fresh ephemeral thread 改为 resume Reviewer 第一回合的持久化 thread，是否能降低 uncached input、重复上下文重建或 latency？

当前结果显示本次 Treatment 的 Reviewer T3 与 aggregate uncached input 都低于 Control，但受单次顺序、cache warm-order、stochastic downstream prompt 和固定范围 reconstruction 等限制，尚未形成最终架构结论。不在本阶段回答 Executor 是否应 persistent，也不进入代码 mutation。

### P4-A 实验矩阵

```text
Control
  Turn 1 Reviewer (.codex-B) = fresh --ephemeral
  Turn 2 Executor (.codex-A) = fresh --ephemeral
  Turn 3 Reviewer (.codex-B) = fresh --ephemeral

Treatment
  Turn 1 Reviewer (.codex-B) = new persistent thread (no --ephemeral)
  Turn 2 Executor (.codex-A) = fresh --ephemeral
  Turn 3 Reviewer (.codex-B) = resume Turn 1 Reviewer thread
```

### 配对实验约束

Control 与 Treatment 必须保持：

- 同一 `git HEAD`；
- 同一 `miniloop_static.md` 与 `miniloop_runtime.md` 内容；
- 同一三个 role prompt 内容；
- 同一 Reviewer/Executor `CODEX_HOME` 绑定；
- 同一 `read-only` sandbox；
- 同一 approval policy；
- 同一 Codex executable/version；
- 同一 profile model / reasoning-effort 配置；
- 同一 transport task 语义与相同的 deterministic orchestration behavior。

两组运行开始前应机械记录至少：

```text
git_head
codex_version
static_sha256
runtime_sha256
role_prompt_sha256(s)
reviewer_codex_home
executor_codex_home
requested/observed model configuration if mechanically available
requested/observed reasoning effort if mechanically available
session_mode for each turn
```

如果当前 JSONL 不可靠提供 model/reasoning 字段，不得伪造；可以从 experiment-start snapshot 的 profile configuration 中机械记录可确认值，或只记录对应配置文件 hash + 明确 limitation。

### 实现要求

1. 保留 P3 现有 usage/thread instrumentation 与原始 JSONL；
2. 扩展 orchestrator，使同一实现可以明确运行 `ephemeral control` 与 `reviewer-resume treatment`，不要复制两套独立脚本；
3. Treatment Reviewer Turn 1 必须生成可被后续恢复的正常持久化 thread，并记录其 `thread_id`；
4. Treatment Reviewer Turn 3 必须显式 resume 该 `thread_id`，并把 resume relationship 作为机械 metadata 落盘；
5. Executor 在 P4-A 中仍保持 `--ephemeral`；
6. 三个 turn 仍全部 `read-only`；
7. peer payload 仍原样 transport，继续做 byte/SHA 验证；
8. Python 不解析 Reviewer/Executor 自由文本，不用 `ACCEPT` / `REJECT` 推进状态；
9. Control 与 Treatment 都保存 `events.jsonl`、`process.json`、`manifest.json`、prompt/final/transport evidence；
10. 记录并比较每个 turn 与 aggregate 的：
    - `input_tokens`
    - `cached_input_tokens`
    - `uncached_input_tokens`
    - `cache_hit_ratio`
    - `output_tokens`
    - `reasoning_output_tokens`
    - `duration_seconds`
11. 主要判断指标优先看 Reviewer Turn 3 与全局 `uncached_input_tokens`，cache-hit ratio 只作为辅助；高 cache-hit ratio 本身不等价于更低总 token/cost；
12. 若 resume 失败、thread 不可恢复、CLI schema 与预期不符或实验条件无法锁定，fail closed 并保存 evidence，不退化成静默 fresh session；
13. 不在两组 paired run 中间修改 Runtime/Static/role prompts；两组都完成后才允许更新 Runtime；
14. P4-A 完成后给出 evidence-backed comparison，不允许只凭单次主观延迟或 cache ratio 宣称优胜。

### Reconstruction correctness 约束

P4-A 不同时优化 context-read policy，以免把变量混在一起；但必须记录当前 read behavior 作为 evidence。

当前已知风险：Agent 可能用固定 `sed` 行范围或整份 `cat` 自主读取 Static/Runtime。P4-A 中暂不修改这些 role prompts，以保持 Control/Treatment 可比性；实验报告必须明确：session resume 只能测试 session lifecycle，不能证明 authoritative reconstruction 已最优或完整。

如果 P4-A 完成，下一候选阶段为 P4-B：在固定更优 session mode 后，再单独优化 Reviewer/Executor 的 authoritative context-read policy，避免把两种优化收益混在同一个实验里。

### P4-A 验收条件

P4-A 可以提交给 Reviewer 审阅，当且仅当：

- Control 和 Treatment 都在同一 frozen experiment context 下完成；
- 两组均保持三个 process 正常结束或对失败做完整 evidence 记录；
- Treatment 机械证明 Reviewer Turn 3 使用了 Turn 1 的目标 thread，而不是创建 fresh replacement；
- 两组 token/cache/duration 指标均可比较，缺失字段明确为 `null`；
- transport byte identity 仍成立；
- tests 覆盖 control/treatment command construction、resume metadata 和 failure behavior；
- 实验结束前 Static/Runtime/role prompts 未在 Control 与 Treatment 之间变化；
- Runtime 最终只在 paired experiment 完成后更新；
- 未进入 Executor persistence、workspace mutation 或 automatic Runtime transition。

---

## 待办任务

### P1 — 旧 Codex-A 状态中的过期 rollout path

状态：`NON-BLOCKING`

在首次 `.codex-A` 新建 `codex exec` smoke test 中观察到：

```text
state db returned stale rollout path for thread ...
/Users/smterpro/.codex/sessions/...
```

同一次 invocation 随后成功创建了新的 session，返回 `CHENG_EXEC_OK` 并正常完成。

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

### P3 — Usage/cache instrumentation

状态：`COMPLETED`

已从 `events.jsonl` 机械提取 Codex machine-readable usage/thread metadata，并提升到 `process.json` / `manifest.json`；真实 `--ephemeral` baseline 见 commit `b8ed49f5283c58ca8b314b49498f1881c63830a1` 与 `1PCloop/runs/usage-baseline-20260905-01/`。

当前 evidence 不对 session resume 的 token/cache 收益作定量结论。

### P4 — Role-session resume policy

状态：`P4-A EXPERIMENT COMPLETED — AWAITING REVIEW`

P4 当前只完成了 P4-A Reviewer session lifecycle paired experiment；没有授权任何后续自动执行。

P4-A 完成后必须先由 Reviewer / Human Owner 审阅结果，再决定是否：

- 保留 Reviewer persistent/resume；
- 启动 P4-B context-read optimization；
- 测试 Executor persistent session；
- 或放弃 session persistence，返回 fresh reconstruction 路径。

未经新的 evidence-backed decision，不自动进入上述任一分支。

### P5 — Raw run-log growth / curated evidence boundary

状态：`DEFERRED / NON-BLOCKING`

当前 milestone run 可以作为 evidence 保留，但长期运行时不应默认让无限增长的 raw `1PCloop/runs/` 成为 Agent 普通 repository inspection 的上下文负担。

后续在 mutation milestone 前后确定：

- raw runs 是否默认本地保留 / gitignore；
- 哪些 accepted run 提炼为 curated `1PCloop/evidence/`；
- 保留哪些最小 artifact 足以复现 transport/process claims。

---

## 当前阻塞项

未确认任何阻塞项。

---

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

### Effective-state supersession

本节 supersede 上文仍写作 `P4-A EXPERIMENT COMPLETED — AWAITING REVIEW` 的旧 active-state 文本；旧记录保留用于 provenance，不回写删除。

当前有效状态：

```text
P4-A — Reviewer-session resume paired experiment
Status: ACCEPTED

Reviewer persistent + explicit resume
Status: PREFERRED IMPLEMENTATION CANDIDATE
        NOT A PERMANENT ARCHITECTURE INVARIANT

P4-B — Deterministic authoritative-context reconstruction
Status: NOT STARTED — REQUIRES HUMAN OWNER ACTIVATION
```

P4-B 的候选目标是：在保留更优 Reviewer session mode 的前提下，单独解决 fresh/bootstrap reconstruction 的完整性与成本问题，使 Agent 能机械可验证地获得当前 authoritative Static/Runtime state，同时避免依赖固定 `sed` 行范围或每轮无条件重复灌入整份治理文档。

本次 review **不授权自动启动 P4-B**，也不授权 persistent Executor、workspace mutation、automatic Runtime semantic transition 或 medium-scale workload。下一阶段必须由 Human Owner 明确授权。
