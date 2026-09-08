# 1PCloop active implementation

当前 active implementation 是最小的 Codex CLI 文本路由循环：

```text
Reviewer (.codex-B)
  -> Executor (.codex-A)
  -> Reviewer (.codex-B)
```

运行：

```bash
python3 1PCloop/scripts/run_text_loop.py
```

默认 session mode 是 `ephemeral-control`，三个 turn 都使用 fresh `--ephemeral`。`reviewer-resume-treatment` 使用同一脚本，但 Reviewer Turn 1 创建持久化 thread、Executor Turn 2 仍为 fresh `--ephemeral`、Reviewer Turn 3 在治理 hash 未改变或仅 Runtime 改变时显式恢复 Turn 1 的 thread。该 mode 可以单独用于 P4-B 验证；复现 P4-A paired experiment 时仍应让 treatment 与 control 共用 repository 外部的 frozen experiment metadata，例如：

```bash
python3 1PCloop/scripts/run_text_loop.py \
  --session-mode ephemeral-control \
  --runs-root /tmp/1pcloop-p4a-example \
  --run-id control \
  --experiment-file /tmp/1pcloop-p4a-example/experiment.json \
  --experiment-id p4a-example

python3 1PCloop/scripts/run_text_loop.py \
  --session-mode reviewer-resume-treatment \
  --runs-root /tmp/1pcloop-p4a-example \
  --run-id treatment \
  --experiment-file /tmp/1pcloop-p4a-example/experiment.json \
  --experiment-id p4a-example
```

Experiment metadata 会锁定 Git HEAD、Codex version、Static/Runtime/role-prompt hashes、显式 `CODEX_HOME`、A/B `config.toml` hash，以及能从顶层非敏感配置字段机械确认的 model/reasoning effort。它不会复制 `auth.json` 或其他 profile state。运行顺序固定为 control 后 treatment；context 不一致、T1 缺少 thread ID、resume process 失败或 T3 事件无法证明恢复了目标 thread 时均 fail closed，不会退化为 fresh T3。

P4-B 的 authoritative-context control layer 不依赖 Agent 自行读取治理文档：

- 每个 fresh Reviewer thread 都由 orchestrator 注入完整当前 Static 和 Runtime bytes；
- 每份治理输入记录 path、SHA-256、byte length、line count、Git HEAD 和 prompt byte offset，并在启动 Codex 前重新核对 source/prompt bytes；
- persistent Reviewer resume 前比较 session-known 与 current governance hashes；
- hashes 未变化时只注入机械 freshness metadata，不重复完整文档；
- Runtime hash 变化时在同一 thread 注入完整当前 Runtime；
- Static hash 变化时不 resume stale contract，而是创建新 thread 并完整 rebootstrap Static + Runtime；
- file missing、source/prompt mismatch 或 resume relationship mismatch 都 fail closed。

完整 governance bootstrap 只用于 Reviewer。Executor 仍保持 fresh `--ephemeral` 并接收 bounded Reviewer peer payload；repository task/evidence inspection 与 governance bootstrap 被 role prompt 明确区分。

每次运行会在 `1PCloop/runs/<run-id>/` 下保存：

- `manifest.json`：三个 process result、两次 transport 和汇总 usage/cache 的机械 metadata；
- `transcript.md`：完整三回合 prompt、final response 和 process result；
- 每个 turn 的 `prompt.txt`、`events.jsonl`、`stderr.txt`、`final.txt` 和 `process.json`；
- 接收回合的 `peer-payload.txt`，用于与发送方 `final.txt` 做逐字节核对。

Reviewer turn 的 `process.json` / `manifest.json` 还会包含 `authoritative_context`，记录 session-known/current hashes、bootstrap/refresh/rollover mode、注入文件、完整性 metadata、prompt offsets 与 launch 前 validation result。Executor turn 的该字段为 `null`。

Orchestrator 只为每次调用设置角色、`CODEX_HOME`、sandbox、turn/run metadata 和文件路径。发送方 final response 以原始字节追加到接收方 prompt；Python 不解析其自然语言语义，也不根据其中的 `ACCEPT` / `REJECT` 等文字推进 Runtime。

每个 `process.json` 还会从原始 `events.jsonl` 机械派生 `thread_id`、input/cached/uncached/output/reasoning token 和 cache hit ratio。缺失或类型不符合当前 machine-readable event schema 的 usage 字段记录为 `null`，不会被当成 `0`；原始 JSONL 保持不变。

上述 `run_text_loop.py` 的两个 session mode 均显式使用 `read-only` sandbox，并且不会自动修改 Runtime。P5/P5.1 的 mutation runner 已进入允许 Executor 修改目标仓库的实验阶段，其隔离策略与文本路由实验不同。

## P5/P5.1 的隔离定位

当前 mutation loop 的隔离方式是 Human Owner 有意选择的实验设计，不是遗漏 sandbox 配置：

- Reviewer 和 Executor 的 Codex CLI turn 均使用 `--dangerously-bypass-approvals-and-sandbox`。原因是 Executor 必须在目标仓库中修改文件、创建 `.git/index.lock` 并亲自提交 evidence；实测 `workspace-write` 会阻断这一闭环。由宿主 Python 代替 Executor 提交也会破坏“Executor 产出可审计 commit”的角色边界。
- Reviewer 通过 role prompt 被限制为只检查 evidence，禁止修改目标仓库、Git 状态和治理文件。
- Executor 只被授权修改指定目标分支的任务范围，运行测试，生成普通 descendant commit，并留下 clean worktree；不得 push、merge、reset、clean、stash、switch、改写历史、修改治理文件或扩大任务范围。
- Python orchestrator 在关键边界机械检查目标 branch、HEAD、cleanliness、commit ancestry、merge commit、治理文件 hash、Reviewer turn 前后的目标仓库不变性、instruction freshness 和 thread relationship；不满足条件时 fail closed。
- Static、Runtime、Reviewer 与 Executor 的 conversation state 仍然分离；Executor 只接收当前 bounded instruction 和必要的 peer payload，而不继承 Reviewer 的完整上下文。

该方案提供的是“角色能力约定 + turn 后机械审计”，不是操作系统级安全隔离。同一 macOS 用户下运行的 Codex 仍具有广泛文件系统能力；审计能发现已覆盖的越权结果，但不能保证在所有情况下阻止恶意进程在审计前造成影响。因此它适合作为当前 Reviewer–Executor orchestration、上下文隔离和 evidence boundary 的研究原型，不应被描述为 production security boundary。

若后续目标转为抵抗恶意或失控 Agent，需要另行引入更强的能力隔离，例如 Reviewer 专用只读 worktree、受约束的文件/Git capability proxy、独立用户或容器。那是下一层安全研究，不改变当前隔离方式属于有意设计这一事实。

## P6.1 checkpoint 与终端进度

mutation runner 从 P6.2 起显式依赖 `jsonschema`。首次运行、恢复或执行完整回归前，
先创建 repo-local Python 环境并安装声明依赖：

```bash
python3 -m venv 1PCloop/.local/venv
1PCloop/.local/venv/bin/python -m pip install -r 1PCloop/requirements.txt
```

`run_mutation_loop.py` 会为每个 workload key 维护一份可覆盖的本地 checkpoint：

```text
1PCloop/.local/state/<workload-id>/checkpoint.json
```

`1PCloop/.local/` 被 Git 忽略。默认 workload ID 是 `--workload-static` 所在目录名，也可以用 `--workload-id` 显式指定。checkpoint 在每个控制面边界原子替换，不保存逐版本历史。P6.3 起，逻辑终态还必须完成 evidence commit/push；只有 `FRAMEWORK_EVIDENCE_PUSHED` 才允许后续新 run 覆盖 checkpoint。

恢复未完成 run 时，使用与原 run 相同的 target、governance、角色配置和 cycle 上限，并增加：

```bash
1PCloop/.local/venv/bin/python 1PCloop/scripts/run_mutation_loop.py \
  <原有参数> \
  --resume
```

恢复前会重新核对配置、治理 hash、target branch/HEAD 和工作树。已完成并记录的 Executor commit 或 Reviewer turn 不会重跑；无法机械归因的中途 target mutation 会停止到 Human Gate。checkpoint 中的 Reviewer thread 不可安全复用时，Reviewer 可以从 repository-backed governance 和已保存的 peer evidence 重新 bootstrap。

Codex 子进程输出现在边运行边写入原始 evidence，同时终端显示 turn 开始/结束、可公开的工具事件和定时 heartbeat。默认 heartbeat 间隔为 15 秒，可用 `--progress-interval-seconds` 调整。Ctrl-C 等可处理的父进程中断会先终止当前 Codex 子进程，避免它成为继续修改仓库的后台 Agent。

运行完整 mutation 回归：

```bash
1PCloop/.local/venv/bin/python -m unittest discover -s 1PCloop/tests -v
```

## P6.2 structured verdict 与单次 Runtime transition

P6 mutation runner 的每个 turn 都通过 Codex CLI `--output-schema` 请求 runtime-enforced
JSON，并用同一份 JSON Schema 在本地再次验证。运行与测试统一使用上面安装了
`1PCloop/requirements.txt` 的 repo-local Python 环境。

三份 schema 分别是 `schemas/reviewer_instruction.schema.json`、
`schemas/executor_receipt.schema.json` 和 `schemas/reviewer_verdict.schema.json`。
所有对象禁止额外字段；所有 turn 都保留完整 `peer_message` 和至多 2000 字符的
`evidence_summary`。只有 Reviewer review schema 包含 `verdict`。Python 校验 wrapper，
仍将完整 final JSON 原始字节传给 peer，不重新编码、截取或改写自然语言。
P4 文本 runner 与 `roles/*.md` 仍用于原来的纯文本实验；mutation runner 使用脚本中的 P6 role prompt。

本机 `codex-cli 0.153.4` 的 `exec --help` 和 `exec resume --help` 均列出
`--output-schema`。构造形式为：

```text
codex exec [--ephemeral] --json --color never ... --output-schema <file> -
codex exec --json --color never ... --output-schema <file> resume <thread-id> -
```

schema 放在 `exec` 公共参数区；Executor 使用 ephemeral，Reviewer 创建 persistent thread
并在 review 显式 resume。恢复过程中因不完整 Reviewer attempt 而创建 fresh persistent
Reviewer 时，必须完整 bootstrap 四份治理文件。local schema validator 也拒绝重复 JSON key、
非标准数值、未知字段及错误角色 wrapper。
[Codex CLI 参数说明](https://learn.chatgpt.com/docs/developer-commands?surface=cli) 与
[Structured Outputs 支持的 schema 子集](https://developers.openai.com/api/docs/guides/structured-outputs)
可供核对。由于服务端 schema 子集不支持 `if/then/else`、`allOf`，verdict 与 nullable 字段的
跨字段关系在本地机械验证；枚举、必填字段、长度和 nullability 在 schema 中声明。

Runtime 写权限默认关闭。只有 Human 启动参数 `--enable-runtime-transition` 与 workload
Runtime machine block 同时授权，合法 Reviewer ACCEPT 才能触发写入。示例 block：

```markdown
<!-- 1PCLOOP_RUNTIME_STATE_BEGIN -->
{
  "schema_version": 1,
  "workload_id": "disposable-workload",
  "transition_mode": "reviewer_accept_once",
  "active_step": {"id": "S1", "status": "ACTIVE"},
  "last_transition_id": null
}
<!-- 1PCLOOP_RUNTIME_STATE_END -->
```

两个 marker 在文件中必须各出现一次，之间必须为合法 JSON。`workload_id` 必须与 CLI
workload key 一致。配套 workload Static 必须由 Human 明确授权这一 orchestrator capability；
Python 不解析周边 Markdown 的授权语义。不要把已关闭、Human-owned 的 `multiLanguage_v1`
改成 fixture。P6 测试使用临时 Git repository 和独立 workload governance。

```bash
1PCloop/.local/venv/bin/python 1PCloop/scripts/run_mutation_loop.py \
  --target-repo /absolute/disposable/target \
  --target-branch p62-fixture \
  --workload-static /absolute/disposable/governance/workload_static.md \
  --workload-runtime /absolute/disposable/governance/workload_runtime.md \
  --workload-id disposable-workload \
  --enable-runtime-transition
```

Runtime 必须是 target/run/state/profile 目录之外的独立普通文件；拒绝符号链接、硬链接及
protected governance alias。实际写入路径仅来自 `--workload-runtime`，绝不来自 Agent
字段。Framework Static/Runtime 和关闭 workload 的两份治理文件始终拒绝作为写入目标。
两个 Agent 仍禁止直接写任何治理文件；P5.1 的 prompt-defined role isolation 和 turn 后
机械审计继续生效。

ACCEPT 会验证成功的 Reviewer profile、thread/bootstrap/resume 关系、四份 governance
hash、target repo/branch/HEAD、clean worktree、Runtime preimage 和 active step。evidence
至少包含一个完整、存在、从当前 HEAD 可达的 commit ID；不接受 `HEAD` 等浮动 revision。
每条 evidence 都必须有 `kind`、`locator` 和 `sha256`。commit SHA-256 是
`git cat-file commit <full-id>` 原始字节的 SHA-256。`file`、`artifact`、`test` 的 locator
必须是 target 或当前 run root 内实际文件的绝对路径，SHA-256 必须与实际字节一致；symlink
逃逸失败。`test` 指向已保存的测试输出文件，Python 校验其存在与 hash，测试语义由 Reviewer
独立检查。ACCEPT 不得包含 repair instruction。

REJECT 必须给出一个非空、至多 8000 字符的 `next_instruction`，Runtime 不变；在原有
cycle/no-op 停止边界允许继续时，完整 Reviewer wrapper 传给下一 fresh Executor。
HUMAN_GATE 不修改 Runtime，checkpoint 记录 `HUMAN_GATE` logical outcome；终端指向
tracked summary 中的 Human 原因，不打印完整 peer payload。自由文本中的
ACCEPT/REJECT/READY/BLOCKED 没有控制权限。

一次合法 transition 的状态顺序是：

```text
REVIEW_COMPLETED -> RUNTIME_TRANSITION_PENDING
-> same-directory temp write + flush/fsync + os.replace + directory fsync
-> exact postimage/state verification -> RUNTIME_TRANSITION_COMMITTED -> stop
```

首版只把同一个 step 从 `ACTIVE` 改为 `COMPLETED`，`next_active_step` 必须是 null；同时
将 `transition_mode` 改为 `disabled`，保存 `last_transition_id`，不启动下一个 Active Step。
只替换 machine block 内容，其他现有字节保留，并在文件尾追加 deterministic JSON transition
record，包含唯一 ID、旧/新状态、accepted preimage hash、Reviewer verdict locator/hash、
target HEAD、evidence locator/hash 和 UTC 时间。

PENDING checkpoint 复用 P6.1 恢复系统，保存原始 preimage、固定 transition record 和预期
postimage hash。使用原参数加 `--resume`：写入前中断会重新校验全部 evidence 并应用一次；
写入后、COMMITTED checkpoint 前中断会识别精确 postimage，只补记 COMMITTED；COMMITTED
恢复只验证结果，不再写 Runtime。I/O 错误保留可恢复状态；无法解释的 Runtime 字节或过期
evidence 会 fail closed/Human Gate，不猜测性修复。旧 P6.1 checkpoint 因缺少 schema/config
绑定不能直接升级恢复，需要 Human 处理旧 run。checkpoint 与 Runtime 是可信的本地恢复
输入，不提供同时回滚这两者之后的外部防篡改账本。

验证：

```bash
1PCloop/.local/venv/bin/python -m unittest discover -s 1PCloop/tests -p test_runtime_transition.py -v
1PCloop/.local/venv/bin/python -m unittest discover -s 1PCloop/tests -v
1PCloop/.local/venv/bin/python -W error::ResourceWarning -m unittest discover -s 1PCloop/tests -v
```

P6.2 不迁移 raw evidence 默认目录、不实现 per-turn summary retention 或 commit/push
automation；`evidence_summary` 仅提前提供给 P6.3。当前运行假设一个 Human contributor、一个
loop、顺序退出的 Agent process；没有 lock/watcher 或多 writer 一致性保证。target-HEAD
refresh 只有 deterministic validation，本阶段未做 live concurrent-HEAD 实验或 P7 fault injection。

### P6.2 implementation validation observation — 2026-09-07

The independent Reviewer accepted P6.2 from this implementation/test evidence. P6 remains
active, with P6.3 as its next Active Step. No closed-workload governance was updated.

Validation environment: Python 3.9, `jsonschema 4.25.1`, local Codex CLI `0.153.4`.
The commands above were run with `/tmp/1pcloop-p62-venv/bin/python`:

- P6.2 focused suite: **21 tests passed**, including parameterized invalid-output,
  freshness, capability, evidence and restart cases.
- Full P4/P5/P6.1/P6.2 regression: **53 tests passed**.
- Full regression with `-W error::ResourceWarning`: **53 tests passed**, with no
  ResourceWarning, unraisable exception or traceback in the captured log.
- `git diff --check`: passed; the four protected governance files, P4 helper/tests,
  P4 role files and `.gitignore` remain unchanged.

Test logic: valid ACCEPT checks unchanged Markdown history, a single appended record,
exact completed machine state, target cleanliness and unchanged peer payload bytes.
Negative cases vary schema, role/profile, resume relationship, target/governance/Runtime
freshness, active step, evidence existence/reachability/hash/boundary, and both capabilities.
REJECT routing is exercised deterministically with ordinary disposable commits; HUMAN_GATE
prints its reason and leaves Runtime untouched. Atomic replace failure verifies the full
preimage and temporary-file cleanup. Stops at PENDING, after Runtime replace and at COMMITTED
verify no repeated Executor/Reviewer calls or transition records. Recovery also checks changed
file evidence, invalid checkpoint state, post-replace I/O failure and full fresh Reviewer bootstrap.
These are deterministic boundary tests, not live kill-9 or P7 defect-injection experiments.

A real Codex/real Git disposable smoke completed the persistent Reviewer → ephemeral Executor
→ resumed Reviewer path, with **3/3 successful turns**, verified resume relationship and
verbatim peer transport. Executor created only `P62_SMOKE.txt`, committed it, and left the
fixture target clean. Reviewer independently inspected the commit/file and reran the byte
assertion. The orchestrator applied one opted-in S1 completion and stopped at
`RUNTIME_TRANSITION_COMMITTED`. A subsequent `--resume` using the final implementation
verified the exact result without another Agent turn or Runtime write.

```text
local smoke root = /private/var/folders/10/81g7llps60j555m_0191lzsc0000gn/T/1pcloop-p62-real-smoke-_zmixrkj
raw run          = <local smoke root>/runs/smoke/
compact check    = <local smoke root>/validation-summary.json
initial target   = 228e0d9d11f7067e2a60ef8750b1719ed95059ee
final target     = 4e8a9f26715c7e7719b3067f4162fc3c5b69acdd
Reviewer thread  = 01a07c98-2aca-79e1-a2d7-a538a61d4c87
transition ID    = 7eb03f31dc67fa6bb6b66fea11e6453a6b42464cc4acbaa1cfd49bfc06d4d598
Runtime preimage = 26add868b797042a19a4a00d7cbf4a17c60679ec0828937e1fcae47e24824799
Runtime postimage= 455bc07c9c542e1260abb7cc343d5db4d2c73024521717a32db852d0e4d0bfd2
verdict SHA-256  = 762893bae32cecfd97e7a9f24016885ef5901d5686afabdf573c2b3cccae75dd
```

The smoke root is disposable local evidence, not retained Git provenance. The tests and this
compact observation are tracked; no raw evidence migration or summary commit/push automation
was introduced. Neither the real `multiLanguage_v1` workload nor its target was used for
mutation/transition tests, and no target push or merge occurred.

## P6.3 local raw evidence 与 tracked summary

mutation runner 的未来 raw evidence 默认写到：

```text
1PCloop/.local/runs/<run-id>/
```

显式 `--runs-root` 仍可覆盖该位置。既有 `1PCloop/runs/` 历史不会移动或重写。
默认 tracked artifact 是 `1PCloop/evidence-summaries/<run-id>.md`；每个完成的 turn
对应一个 deterministic entry ID。条目只保存 target/governance metadata、schema 声明的
`evidence_summary`、Reviewer verdict/evidence（如有）以及 raw 文件 locator、SHA-256 和
byte length，不复制 prompt、peer message、events、stderr、hidden reasoning 或 process 正文。

`evidence_summary` 以 JSON string 写入固定 Markdown envelope；换行、heading、反引号和
HTML angle bracket 都会被确定性转义，Unicode 保持可读。summary 的每次逻辑 append 先把
entry bytes 与 preimage/postimage hash 写入 checkpoint，再通过同目录临时文件、fsync 和
`os.replace` 替换。恢复只接受精确 preimage 或 postimage；额外字节、部分写入、hash 错误
或缺失 entry 均 fail closed。

逻辑结果与 evidence finalization 分开记录：

```text
RUNTIME_TRANSITION_COMMITTED | HUMAN_GATE | FAILED_CLOSED
-> EVIDENCE_FINALIZATION_PENDING
-> FRAMEWORK_EVIDENCE_COMMITTED
-> FRAMEWORK_EVIDENCE_PUSHED
```

一次 run 只创建一个 framework evidence commit。commit allowlist 仅包含该 run 的 summary，
以及确实位于 framework repository 内且已由 P6.2 合法写入的 workload Runtime。提交前验证
framework branch/HEAD、干净的起始状态、显式 path set、blob content hash、ordinary parent
和 run-ID trailer；stage 只调用 `git add -- <explicit paths>`。Static、`.local`、target 文件、
closed workload 和预先存在的修改不在 allowlist。

默认 framework 配置是当前 repository、`main`、`origin` 和 `refs/heads/main`。disposable
framework repository 可通过以下参数显式注入：

```text
--framework-repo <repo-root>
--framework-branch <branch>
--framework-remote <remote>
--framework-push-ref refs/heads/<branch>
--summary-root <tracked-summary-directory>
```

framework 与 target 必须是不重叠的独立 Git repository；framework Static/Runtime 和 summary
必须位于 framework repo 内。push 只在 framework repo 中执行非 force refspec，并在前后
验证 remote ref。push 失败保留本地 commit 与 `FRAMEWORK_EVIDENCE_COMMITTED` checkpoint；
`--resume` 只重试 push。若远端已收到 exact commit 但 checkpoint 尚未更新，恢复只补记
`already-present`，不会重跑 Agent、重写 Runtime、追加 summary 或创建第二个 commit。

P6.3 configuration 将 summary 路径、framework repo/branch/remote/ref 与 schema hash 写入
checkpoint。缺少这些字段的旧 checkpoint 不会自动升级；如需处理，必须由 Human 明确处置，
不能让新 run 猜测性覆盖。实时终端只显示 summary/commit/push 的 pending、written、
reconciled、succeeded 或 failed 控制事件，不输出完整 LLM summary 或 raw 内容。

专项验证：

```bash
1PCloop/.local/venv/bin/python -m unittest discover -s 1PCloop/tests -p test_evidence_summary.py -v
```
