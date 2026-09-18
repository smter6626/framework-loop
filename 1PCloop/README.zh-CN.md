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
- 纯 mutation contract helper，并由 runner 兼容性 re-export 原公共名称；
- 由 `status`、`inspect` 和 `human-gate` 共用的确定性只读 Human Gate projection；
- 基于 F2/F3/F5 operator projection 的本地只读 TUI；
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

### 默认中文 Prompt 模板

- [Static Prompt 模板](templates/static_prompt_zh.md)用于建立、审查或经授权修订稳定任务合同。
  其只读 Framework v1.2 来源是
  `/Users/smterpro/Workspace/Tools/structured-llm-execution-framework/structured-llm-execution-framework_static.md`，
  固定 SHA-256 为
  `e3ff93b4136c0d3d87d7f1a319ca9c4513f831327daf18aea46f9f3d6659daf7`。
- [Runtime Prompt 模板](templates/runtime_prompt_zh.md)用于恢复权威状态、独立审核 evidence、维护唯一
  Active Step，并仅在 evidence 支持时推进状态。其只读 Framework v1.2 来源是
  `/Users/smterpro/Workspace/Tools/structured-llm-execution-framework/structured-llm-execution-framework_runtime.md`，
  固定 SHA-256 为
  `3cbc4c93adff6ac2b1fb351a8a81f4b65dbd73b4de28ee2d0d4141522258ab54`。

使用时打开对应 tracked 模板，复制 `## 可复制 Prompt` 下的内容，只替换有已知事实支持的
`{{...}}` 占位符；未知项继续显式保留，低风险任务可以删除没有价值的章节。外部 Tools 文件仅作为
只读 provenance 输入。本地快照不会自动同步；未来修改模板前必须重新核对来源路径和 hash，并接受
独立审核。

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

该长参数入口继续受支持。下面的 workload config 入口只把同一配置编译成这些参数，仍调用同一个
状态机。

## Workload config 与 operator CLI

`scripts/onepcloop.py` 提供统一的版本化入口：

```bash
1PCloop/.local/venv/bin/python 1PCloop/scripts/onepcloop.py \
  --config /absolute/path/workload.json doctor

# doctor 可替换为：preflight、run、resume、status、inspect、human-gate 或 tui。
```

严格 JSON config 只允许以下 section 和字段：

```json
{
  "schema_version": 1,
  "workload_id": "example-workload",
  "target": {"repo": "./target", "branch": "feature"},
  "governance": {
    "workload_static": "./workload_static.md",
    "workload_runtime": "./workload_runtime.md",
    "framework_repo": "../framework-loop",
    "framework_static": "../framework-loop/1PCloop/docs/miniloop_static.md",
    "framework_runtime": "../framework-loop/1PCloop/docs/miniloop_runtime.md"
  },
  "profiles": {
    "reviewer_home": "/absolute/reviewer-profile",
    "executor_home": "/absolute/executor-profile"
  },
  "execution": {
    "codex_bin": "/absolute/path/to/codex",
    "max_cycles": 8,
    "timeout_seconds": 900,
    "progress_interval_seconds": 15,
    "enable_runtime_transition": true
  },
  "evidence": {
    "runs_root": "../framework-loop/1PCloop/.local/runs",
    "state_root": "../framework-loop/1PCloop/.local/state",
    "summary_root": "../framework-loop/1PCloop/evidence-summaries"
  },
  "framework_git": {
    "branch": "main",
    "remote": "origin",
    "push_ref": "refs/heads/main"
  }
}
```

Duplicate key、未知/缺失字段、错误类型或版本、credential/prompt 类禁止字段以及相同的
Reviewer/Executor profile 都会被拒绝。相对路径只按 config 文件目录解析，与调用 cwd 无关；不支持
`~`，也不执行环境变量或 shell expansion。Raw 文件 SHA-256、canonical resolved-config SHA-256、
绝对 config path 和 workload ID 共同形成 identity。新 run 把它绑定到 checkpoint 与 manifest；
resume 对任何字节、resolved value、路径、profile、target、governance、Git 或 storage drift 都
fail closed。Legacy invocation 的 operator config identity 明确为 `null`，只能继续使用原长参数
resume，不会被猜测升级。

各命令语义：

- `doctor` 只读检查 Python/jsonschema、Codex executable/version、独立 profile、Git、target/
  framework identity、remote ref、governance/schema 和 ignored local storage；不创建 run/
  checkpoint，不调用 Agent。
- `preflight` 直接调用现有 runner validator，不创建 evidence 或调用 Agent。
- `run` 将 config 编译成现有参数并调用未复制、未改变的 Reviewer–Executor 状态机。
- `resume` 只读取 `<state_root>/<workload_id>/checkpoint.json`，从中取得 run ID 并验证保存的精确
  config identity；不扫描目录、不接受 override。
- `status` 投影 checkpoint、F2 observation 与 F1 final result，包括 cycle/role/timer/activity/
  target、logical outcome、Runtime transition、publication、Human Gate/failed-closed、artifact、
  observation availability，以及 `RESUME_ALLOWED`、`HUMAN_REVIEW_REQUIRED`、
  `TERMINAL_SUCCESS`、`TERMINAL_FAILURE`、`START_NEW_RUN_ALLOWED` 或 `STATE_UNAVAILABLE`。
- `inspect` 只读验证 config/checkpoint/manifest、F2 sequence/hash/suffix/live projection、tracked
  summary 与现存 raw artifact、framework evidence commit/push 和 target Git identity。对于
  ACCEPT transition，它把 transition record 精确绑定到 routed Reviewer verdict、correction
  resolution、唯一 summary entry、target HEAD 和 evidence list；已 supersede verdict 仅保留
  provenance，不恢复 authority。HUMAN_GATE、FAILED_CLOSED、REJECT/correction exhausted 和
  capability-disabled run 的 target evidence 为 `NOT_APPLICABLE`。缺失 Git-ignored raw evidence
  或 incomplete JSONL tail 为 `UNAVAILABLE`；完整冲突 evidence 为 `FAIL`。Overall `PASS` 只表示
  evidence package 内部一致，不表示任务已 ACCEPT。Inspect 不截断 journal，也不修复 artifact。
  Result 另外把 authoritative target evidence 分类为 `VALID`、`INVALID`、`UNAVAILABLE` 或
  `NOT_APPLICABLE`。
- `human-gate` 返回与 `status`、`inspect` 相同的 bounded Human Gate projection，不创建 run、
  checkpoint、Agent turn、repair 或 Human decision。
- `tui` 打开基于 `status`、`inspect` 和共用 Human Gate projection 的本地只读 dashboard，
  不调用 runner，也不执行恢复动作。

`status` 和 `inspect` 保留 F3 顶层 checkpoint、logical outcome、Runtime transition、
publication 和 safe action 字段。Human Gate 字段放在 `result.human_gate_projection`；
`human-gate` 则直接在 `result` 输出同一 projection。三个命令共用一组只读 authoritative-
integrity 检查，按适用状态验证本地 evidence、target branch/HEAD/cleanliness、已形成的
framework commit、已完成 push 的 remote ref，以及适用的 ACCEPT target evidence。必需 raw
evidence 缺失为 `UNAVAILABLE`；identity 冲突为 `INVALID`，不会建议 finalization 或新 run。
尚未形成 commit 或尚未完成 push 的合法中间态，不会仅因该 artifact 尚不存在而被判为冲突。

`doctor`、`preflight`、`status`、`inspect`、`human-gate` 各只输出一个 compact JSON object，包含
版本、命令、
config identity、overall status、checks/result 与公开 artifact locator。`PASS`/`UNAVAILABLE` 返回
0，`FAIL` 返回 1，无效 config 返回 2。输出不包含异常正文、profile 内容、prompt、peer message、
命令输出、stderr 或 internal diagnostic。`run`/`resume` 保留原 `PROGRESS` 和 F1 `FINAL_RESULT`。

`scripts/mutation_contracts.py` 持有无 side effect 的 control/message/public-result contract。
`scripts/human_gate.py` 只根据结构化状态和公开 locator 做纯 projection，不 import runner，也不读取
artifact。`scripts/workload_operator.py` 向纯 projection 和 `inspect` 提供共用的只读
integrity 结果。`run_mutation_loop.py` 为兼容既有 caller re-export 原公共 contract 名称，并继续
是唯一 mutation control state machine。

Human Gate state 固定为 `ACTIVE`、`NOT_APPLICABLE`、`UNAVAILABLE`、`INVALID`。Allowed action 仅有
`INSPECT_EVIDENCE`、`FINALIZE_EVIDENCE`、`REMEDIATE_EXTERNAL_STATE`、
`START_NEW_RUN_AFTER_HUMAN_REVIEW`、`NO_AUTOMATIC_REPAIR`。Recovery mode 固定为
`FINALIZATION_ONLY`、`HUMAN_REMEDIATION_REQUIRED`、`NEW_RUN_AFTER_REVIEW`、`NO_ACTION`。
未知或冲突状态默认只允许检查和 Human remediation，不自动 repair。Evidence package 完整不代表
Human Gate 已解决，publication 成功也不改变 logical outcome。

Human Gate projection 不能替 Human 解除 gate。TUI 只显示固定 allowed action 作为说明，
不提供执行按钮或命令。F7 real-service smoke 尚未实现。

## 本地只读 TUI

在 macOS 交互式终端中使用 config-backed 入口：

```bash
1PCloop/.local/venv/bin/python 1PCloop/scripts/onepcloop.py \
  --config /absolute/path/workload.json tui
```

`r` 刷新，`Tab` 切换摘要/检查视图，`j`/`k` 或方向键滚动，`?` 切换帮助，`q` 或 Esc 退出。
键位显示在页脚或帮助页。空闲时最多每秒刷新一次；支持 resize 和窄终端，并在退出时恢复终端。
非 TTY 仅返回纯文本错误，不输出屏幕控制序列。

`scripts/local_tui.py` 将 operator 数据源和纯呈现层分开。它只渲染结构化的 `status`/`inspect`
envelope 和嵌套 F5 Human Gate projection；不打开 raw Codex events、prompt、peer message、
stderr 或命令输出。界面显示 run/cycle/role、control state、target HEAD、F2 active-time
elapsed/timeout/activity、observation/integrity availability，以及相互独立的 logical、Runtime、
publication 三层状态。它不把停机 wall time 加进 F2 elapsed。Observation 不可用时隐藏未验证的
progress。连续读取的 `status` 和 `inspect` 不一致时，隐藏恢复动作直到刷新。`PUSHED` 只代表
publication，不代表 logical success。无 checkpoint 候选按 `status -> inspect -> status`
复核；普通已有 run 仍只读 `status -> inspect`。只有前后两份 status 是相同的精确
no-checkpoint projection、config 与 checkpoint locator 相同，且 inspect 没有真实 run
projection，才显示 `NO CHECKPOINT`。Inspect 的 generic checkpoint identity failure 不能单独
证明缺失；复核发生变化或 INVALID 时显示 `SNAPSHOT UNAVAILABLE`，隐藏恢复建议直到下次一致刷新。
最终终端行在宽度裁剪前转义 Unicode `Cc`、
`Cf`、`Zl` 和 `Zp`，嵌入的行/段分隔符不能伪造另一行。终端 Human Gate 不显示为普通 Agent
resume；`INVALID` 或 `UNAVAILABLE` 时不会给出比 F5 projection 更宽的建议。

TUI 不启动或恢复 Agent，不 finalization、repair identity，也不写 checkpoint、evidence、Git 或
governance。它是单 writer 边界内的本地 dashboard，不是 concurrency protocol 或 GUI。极窄终端
显示 resize/quit 提示而不显示完整视图。F7 real-service smoke 仍属后续工作。

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

Config-backed `status`、`inspect`、`human-gate` 使用同一个只读 Human Gate projection，不会自动
resume 或替 Human 作决定。Logical terminal 后如需恢复 publication，最多只恢复 evidence
finalization，不会重放 Reviewer 或 Executor turn。

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

Deterministic regression suite 在 `ResourceWarning` 提升为错误时通过。
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
tests/test_progress_status.py        structured progress/timing/status/recovery
tests/test_operator_cli.py           workload config/operator commands
tests/test_mutation_contracts.py     纯 contract 与 runner 兼容性
tests/test_human_gate.py             Human Gate projection 与只读 CLI
tests/test_local_tui.py              只读 TUI 呈现层与 disposable integration
```

## 代码和文档入口

```text
scripts/run_mutation_loop.py      当前 mutation orchestrator
scripts/mutation_contracts.py     无 side effect 的 control/message contract
scripts/human_gate.py             纯 Human Gate 状态 projection
scripts/local_tui.py              只读终端呈现层与 operator 数据源
scripts/run_text_loop.py          只读 text-routing/context diagnostic runner
scripts/p63_evidence.py           summary、framework commit 和 push helper
scripts/progress_status.py        F2 progress journal、live snapshot 和 renderer
scripts/workload_operator.py      config、diagnostics 和只读 projection
scripts/onepcloop.py              统一 operator CLI
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
