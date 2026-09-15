# 1PCloop

[English](README.md) | 简体中文

1PCloop 是运行在一台 macOS 机器上的 Reviewer–Executor 自动化闭环。它使用两个隔离的 Codex
identity，把任务合同、当前状态、代码执行、独立审核、Human Gate 和证据保存连接成一个可以恢复
和审计的顺序工作流。

```text
Human Owner
    |
    | 定义目标、权限和必须由人决定的事项
    v
Static + Runtime
    |
    v
Python orchestrator
    |
    +--> Reviewer：读取治理和 repository，形成 bounded instruction
    |
    +--> Executor：实现、测试、创建普通 descendant commit
    |
    +--> Reviewer：直接检查 commit、文件和测试 evidence
             |
             +--> ACCEPT：由 orchestrator 验证并推进获授权的 Runtime
             +--> REJECT：生成 repair instruction，进入下一轮 Executor
             +--> HUMAN_GATE：停止并提醒 Human Owner
```

## 最终交付能力

当前实现已经具备：

- 显式绑定两个独立 Codex profile；
- 自动执行 Reviewer → Executor → Reviewer 路由，无需人工复制 peer message；
- 给 Reviewer 注入完整、带 identity/hash 的 framework 和 workload 治理上下文；
- 只向 Executor 提供当前任务所需的 bounded instruction；
- 允许 Executor 在独立 target repository 中修改、测试并创建普通 Git commit；
- 在每个关键边界检查 branch、HEAD、clean worktree、commit ancestry 和治理 hash；
- 使用 Codex runtime-enforced output schema 和本地 schema validation；
- 只有 Reviewer review turn 拥有 ACCEPT/REJECT/HUMAN_GATE 权限；
- 对 commit、文件和测试 artifact 做 locator、边界、存在性和 SHA-256 验证；
- 只有 Human CLI capability 和 workload Runtime 同时授权时才写 Runtime；
- 原子 Runtime transition、checkpoint 和 crash/restart reconciliation；
- Git-ignored raw evidence、逐 turn concise summary、一次 framework evidence commit/push；
- 对可机械纠正的 Reviewer verdict 最多进行两次同线程 correction，不重跑已完成 Executor；
- 明确区分 logical outcome、Runtime transition 和 evidence publication；
- 在无法解释状态时 fail closed，而不是自动执行破坏性修复。

这些能力提高了 coding-agent 自我复核的独立性、可恢复性和可追溯性，但不保证 LLM 永远正确，
也不构成操作系统级安全隔离。

## 当前实现与可扩展边界

当前成品已经具备 contract-backed context 和 context-compiled fresh Executor：Reviewer 获得完整、
带 hash/freshness 的治理上下文，Executor 每轮使用 fresh session 和 bounded instruction，最终结果
只通过 Git、artifact 和 evidence 回到 Reviewer。Reviewer/Executor 的模型配置可以不同，最终
verdict authority 只属于 Reviewer。

当前 runner 的实际 backend 是两个 Codex CLI profile，并且一次只运行一个 mutation Executor。
以下能力属于仓库首页描述的扩展形态，不应被理解为当前已经接入：

- 独立的 per-role local/cloud/third-party provider adapter；
- Qwen/Ollama Executor 与云端 Reviewer 的正式端到端配置和验收 evidence；
- Claude 或其他 Agent 产品 adapter；
- 多个可按能力选择的 ephemeral worker；
- image/vision input 的治理路由；
- browser、MCP、plugin 和 Computer Use 的 capability/evidence/Human-Gate 集成；
- 并行 mutation worker 或 multi-writer consistency。

Codex CLI 或具体模型自身具备某项工具能力，不等于 mutation runner 已经把该能力纳入身份、权限、
evidence 和恢复合同。目标扩展和已实现基础的对应关系见[中文仓库首页](../README.zh-CN.md)。

## 运行环境

当前默认配置面向：

- Apple Silicon Mac；
- macOS；
- Python 3.9+；
- 已安装的 Codex CLI；
- 两个独立的 Codex identity/profile。

默认角色绑定：

```text
Reviewer = CODEX_HOME=/Users/smterpro/.codex-B
Executor = CODEX_HOME=/Users/smterpro/.codex-A
```

角色由职责、权限和 session state 定义，不由模型名称定义。Reviewer 和 Executor 可以使用相同或
不同模型。实际使用中建议 Reviewer 的模型能力和 reasoning effort 不低于 Executor，复杂或高风险
任务可以给 Reviewer 更强配置；这只是运行建议，不能替代 evidence 和机械校验。

`~/.codex` symlink、Codex GUI 当前前台账号和 GUI 窗口都不参与 identity 判定。每次 CLI
invocation 都显式设置目标 `CODEX_HOME`。

## 安装

在仓库根目录执行：

```bash
python3 -m venv 1PCloop/.local/venv
1PCloop/.local/venv/bin/python -m pip install -r 1PCloop/requirements.txt
codex --version
```

`.local/` 被 Git 忽略，用于 Python 环境、checkpoint 和未来 raw run evidence。

## Static、Runtime 与 external context

### Framework Static/Runtime

- `docs/miniloop_static.md`：整个 1PCloop 的稳定目标、角色和安全边界；
- `docs/miniloop_runtime.md`：全局里程碑和当前 task 指针，不保存每个 task 的详细流水。

### Task-local Static/Runtime

每个持续任务应在 `workloads/<workload-id>/` 下建立：

```text
workload_static.md
workload_runtime.md
```

`workload_static.md` 保存长期稳定的目标、范围、禁止事项、权限和 acceptance criteria。
`workload_runtime.md` 保存已验收结果、唯一 Active Step、blocker、pending task、Human decision 和
evidence locator。

Static 不记录当前进度；Runtime 不得静默修改 Static。已经关闭的任务默认冻结，新目标应建立新的
task-local Static/Runtime。

Reviewer 的 external context 由 orchestrator 从以下来源重建：

```text
framework Static
+ framework Runtime
+ workload Static
+ workload Runtime
+ target Git identity
+ 当前 peer evidence
```

因此 conversation history 不是权威 memory。Reviewer thread 无法继续时，可以从 repository-backed
state 重新 bootstrap。Executor 不继承 Reviewer 的完整历史，只接收当前 bounded instruction 和
必要 peer payload。

## 准备一个 workload

### 1. 准备独立 target repository

Mutation runner 要求 target 与 framework repository 互不重叠。启动前 target 必须：

- 位于预期 branch；
- HEAD 可解析；
- working tree clean；
- 不包含未授权治理文件修改。

Executor 可以在该 branch 创建普通 descendant commit，但不得 push、merge、switch、reset、clean、
stash 或改写历史。

### 2. 编写 workload Static

至少明确：

- 目标和预期 artifact；
- 允许及禁止修改的路径；
- 必须运行的 self-check；
- Reviewer 需要直接检查的 evidence；
- Human Gate 条件；
- target branch 和集成边界。

### 3. 编写 workload Runtime

需要允许自动 ACCEPT → Runtime transition 时，在 Runtime 中放置唯一 machine-owned block：

```markdown
<!-- 1PCLOOP_RUNTIME_STATE_BEGIN -->
{
  "schema_version": 1,
  "workload_id": "example-workload",
  "transition_mode": "reviewer_accept_once",
  "active_step": {
    "id": "S1",
    "status": "ACTIVE"
  },
  "last_transition_id": null
}
<!-- 1PCLOOP_RUNTIME_STATE_END -->
```

两个 marker 必须各出现一次。Python 只理解 machine block，不解析周边 Markdown 的自然语言语义。
首版 transition 只把当前 step 改成 `COMPLETED`、把 `transition_mode` 改成 `disabled`，然后停止；
不会自动激活下一个 step。

## Preflight

先验证路径、branch、治理 identity、profile、schema、framework remote 和工作树，不调用 Agent：

```bash
1PCloop/.local/venv/bin/python 1PCloop/scripts/run_mutation_loop.py \
  --target-repo /absolute/path/to/target \
  --target-branch feature-branch \
  --workload-static /absolute/path/to/workload_static.md \
  --workload-runtime /absolute/path/to/workload_runtime.md \
  --workload-id example-workload \
  --enable-runtime-transition \
  --preflight-only
```

Preflight 是只读检查。失败时不会创建 run 或启动 Reviewer/Executor。

## 运行 mutation loop

```bash
1PCloop/.local/venv/bin/python 1PCloop/scripts/run_mutation_loop.py \
  --target-repo /absolute/path/to/target \
  --target-branch feature-branch \
  --workload-static /absolute/path/to/workload_static.md \
  --workload-runtime /absolute/path/to/workload_runtime.md \
  --workload-id example-workload \
  --enable-runtime-transition \
  --max-cycles 8 \
  --timeout-seconds 900 \
  --progress-interval-seconds 15
```

常用可选参数：

```text
--reviewer-home
--executor-home
--framework-repo
--framework-branch
--framework-remote
--framework-push-ref
--run-id
--runs-root
--state-root
--summary-root
```

当前入口仍是显式参数 CLI；更高层的 workload config、doctor/status/inspect 命令和交互式界面
尚未提供。

## 自动循环语义

### Reviewer instruction

Reviewer 创建 persistent thread，读取完整当前治理和 target state，产生一个 bounded instruction。
Reviewer 不得修改 target、Git state 或治理文件。

### Executor mutation

Executor 使用 fresh ephemeral session，在 target 中实现任务、运行测试、创建 commit，并留下 clean
worktree。Executor 的总结不能触发 acceptance。

### Reviewer verdict

原 Reviewer thread 被显式 resume。Reviewer 必须重新读取实际 target、commit、文件、测试和
hash，并返回 runtime-enforced verdict。

```text
ACCEPT
  -> 机械验证身份、target、governance、evidence 和 capability
  -> 原子完成一次 workload Runtime transition

REJECT
  -> Runtime 不变
  -> 完整 repair instruction 路由给下一 fresh Executor

HUMAN_GATE
  -> Runtime 不变
  -> 自动停止，终端显示 Human Gate 状态和 evidence 位置
```

自由文本中出现 `ACCEPT`、`PASS`、`READY` 等词没有控制权限。

## Reviewer verdict correction

如果 Reviewer process、schema、profile、thread、read-only audit，以及实际 target/governance state
均已验证，但 verdict 中的 evidence locator、hash 或其他声明存在明确可纠正的机械错误，runner
会恢复同一个 Reviewer thread，要求重新检查并输出完整 verdict。

- 最多两个 correction turn；
- 不重跑已完成 Executor；
- Python 不删除、补写、转换或猜测 Reviewer evidence；
- correction 可以返回 ACCEPT、REJECT 或 HUMAN_GATE；
- schema/process/profile/thread 错误以及实际 state/evidence 漂移不进入 correction；
- 两次仍失败则 `VERDICT_CORRECTION_EXHAUSTED / FAILED_CLOSED`。

`file`、`artifact`、`test` evidence 必须指向 target/run boundary 内实际存在文件的绝对路径。
Shell command、Git-status 描述和 prose 不是 locator；没有实际输出文件时不应虚构 evidence。

## 运行状态、checkpoint 与恢复

默认 checkpoint：

```text
1PCloop/.local/state/<workload-id>/checkpoint.json
```

Checkpoint 在控制边界原子覆盖，保存当前 state、turn identity、Reviewer thread、target/governance
identity、correction attempt、Runtime transition、summary 和 publication recovery 数据。它是当前
恢复状态，不保存逐版本历史。

运行期间终端会显示：

- role、cycle、control state；
- Codex process start/finish；
- 有限的 machine-readable tool activity；
- 当前 turn elapsed heartbeat；
- summary、Runtime transition、framework commit/push 状态；
- Human Gate、error 和最终结果。

恢复未完成 run 时，使用完全相同的参数并增加：

```bash
1PCloop/.local/venv/bin/python 1PCloop/scripts/run_mutation_loop.py \
  <原运行的完整参数> \
  --resume
```

恢复时重新验证配置、target、governance、turn、evidence 和 framework identity。已完成且可机械
归因的 Agent turn、Executor commit、correction、Runtime transition、summary、framework commit
或 push 不会重复。无法安全确定 Executor 是否已修改 target 时会进入 Human Gate，而不是盲目
重跑。

当前版本尚未提供 run-wide/stage-wide timer、独立 status subcommand 或交互式 TUI/GUI。

## Evidence

未来 mutation run 的 raw evidence 默认位于：

```text
1PCloop/.local/runs/<run-id>/
```

其中可以包含：

- prompt；
- raw Codex `events.jsonl`；
- stderr；
- final message；
- peer payload；
- process metadata；
- manifest。

这些内容默认 Git-ignored，不作为长期 Git 历史。

每个完成 turn 会在以下 tracked summary 中生成一条 bounded entry：

```text
1PCloop/evidence-summaries/<run-id>.md
```

Entry 保存 role/cycle、时间、target/governance identity、LLM `evidence_summary` 和 raw locator/hash，
不复制完整 prompt、peer message、events、stderr 或 hidden reasoning。

到达 logical terminal 后，runner 在 framework repository 中创建一次 allowlisted evidence commit，
并 non-force push 到配置的 framework remote。它不会 push 或 merge target repository。

## FINAL_RESULT

每次非 preflight invocation 返回前都会输出固定字段：

```text
FINAL_RESULT
run_id="example"
logical_outcome="RUNTIME_TRANSITION_COMMITTED"
exit_code=0
runtime_transition="APPLIED"
evidence_publication="PUSHED"
reason="one_reviewer_accept_transition_completed"
error_code="RUNTIME_TRANSITION_COMMITTED"
run_root="/absolute/path/to/run"
```

等号右侧是单行 JSON scalar，不能通过换行伪造额外字段。Public reason 最长512字符；完整内部异常
只保存在本地 `internal_diagnostic`。

必须同时查看三类结果：

```text
logical_outcome
runtime_transition
evidence_publication
```

例如 `evidence_publication="PUSHED"` 只表示失败或成功的 run evidence 已发布，不表示任务已经
ACCEPT。Shell exit code 也不能替代 Human Gate/Runtime 语义。

## 隔离和安全边界

Mutation runner 为了允许 Executor 创建真实 Git commit，Reviewer 和 Executor 当前使用
`--dangerously-bypass-approvals-and-sandbox`。安全边界由以下组合提供：

- 独立 profile/session；
- role prompt；
- bounded instruction；
- target/framework 路径分离；
- Reviewer turn 前后 read-only audit；
- target branch/HEAD/cleanliness/ancestry 检查；
- governance/evidence hash；
- explicit allowlist；
- fail-closed 和 Human Gate。

这不是抵抗恶意本地进程的 production security boundary。同一 macOS 用户下的 Codex 仍有广泛
文件访问能力。当前支持一个 Human contributor、一个 active loop、一个 target writer；不支持
并行 Executor、多 writer reconciliation、repository lock、watcher 或分布式一致性。

## 已验证结果

Repository-backed evidence 已覆盖：

- 两个 Codex identity 的独立串行调用；
- Reviewer/Executor 消息的逐字节路由；
- persistent Reviewer resume 和 fresh-session reconstruction；
- governance unchanged/runtime-changed/static-changed freshness policy；
- disposable Git target 的真实 mutation、test、commit 和 independent review；
- 一个真实中等规模外部项目的多轮修改和 Human Gate；
- schema-invalid、stale state、错误 role/thread、缺失或错误 evidence 的 fail-closed；
- Runtime transition 与 summary/commit/push 的 crash-boundary recovery；
- Reviewer verdict correction 的同线程、次数上限和 Executor 幂等；
- public terminal result 的控制字符、长度和字段注入防护。

当前 deterministic regression suite 包含90项测试，并在 `ResourceWarning` 提升为错误时通过。
历史实验、阶段 verdict 和完整 evidence locator 位于 `docs/miniloop_runtime.md`、
`evidence-summaries/`、`runs/` 和 Git history；README 不复制这些进度记录。

## 测试

运行完整严格回归：

```bash
1PCloop/.local/venv/bin/python \
  -W error::ResourceWarning \
  -m unittest discover \
  -s 1PCloop/tests \
  -v
```

专项测试：

```text
tests/test_run_text_loop.py          text transport/context reconstruction
tests/test_run_mutation_loop.py      mutation state machine/restart
tests/test_runtime_transition.py     structured verdict/Runtime transition
tests/test_evidence_summary.py       summary/commit/push recovery
tests/test_verdict_correction.py     verdict correction/public result
```

## 代码和文档入口

```text
scripts/run_mutation_loop.py      当前 mutation orchestrator
scripts/run_text_loop.py          只读 text-routing/context diagnostic runner
scripts/p63_evidence.py           summary、framework commit 和 push helper
schemas/                          runtime-enforced Agent output schemas
roles/                            text-routing role prompts
workloads/                        task-local governance
docs/miniloop_static.md           全局稳定合同
docs/miniloop_runtime.md          全局历史和当前 task 指针
evidence-summaries/               tracked compact evidence
runs/                             已保留的历史运行 evidence
history/                          已冻结的早期实现
```

任务当前状态应读取对应 Runtime；README 只描述稳定架构、操作方式、已交付能力和已知边界。
