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

---

## 当前活跃步骤

### Step 1 — P3 已完成；等待 Human Owner 决定是否启动 P4

状态：`AWAITING HUMAN DIRECTION`

### 当前目标

P3 的 usage/cache instrumentation 与真实 `--ephemeral` baseline 已完成。当前没有被授权自动执行的下一阶段；保持现有 transport 和 capability boundary，等待 Human Owner 明确决定是否启动 P4 Reviewer-session resume 对照实验。

### 当前运行观察

Baseline run `usage-baseline-20260905-01` 已证明：

```text
Reviewer (.codex-B) -> Executor (.codex-A) -> Reviewer (.codex-B)
all process exit codes = 0
preserved_verbatim = true / true
all sandboxes = read-only
all invocations = --ephemeral
total input/cached/uncached = 167734 / 127104 / 40630
aggregate cache_hit_ratio = 0.757771
total output/reasoning = 1388 / 484
total duration_seconds = 68.078
```

当前不把 `thread_id` 等同于已验证可恢复的 session，也不据此推断 resume 收益。P4、workspace-write、disposable mutation、automatic Runtime semantic transition 均未启动。

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

状态：`NOT STARTED / REQUIRES HUMAN OWNER ACTIVATION`

若 Human Owner 后续明确启动 P4，则实现 Reviewer session resume 并使用等价 transport task 对比 ephemeral 与 Reviewer-resume 的 token、cache 和 latency。第一版只要求 Reviewer 持久化；Executor 是否 persistent 由 evidence 决定。

P4 必须继续满足：

- Static / Runtime / repository/evidence 仍为 authoritative memory；
- Reviewer / Executor session 仅为 non-authoritative performance working memory；
- Runtime 更新后，resume session 必须重新读取或明确刷新当前 Runtime；
- fresh-session reconstruction 在架构上仍然可行；
- Static contract 显著变化时可以 rollover role session；
- peer natural-language payload 保持 opaque，不引入 Python semantic parser；
- baseline 与 resume run 都保存可检查的原始 JSONL 和派生机械指标；
- 不因 P4 实验自动进入 workspace mutation、implementation acceptance 或 Runtime mutation loop。

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
