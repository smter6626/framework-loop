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

`run_mutation_loop.py` 会为每个 workload key 维护一份可覆盖的本地 checkpoint：

```text
1PCloop/.local/state/<workload-id>/checkpoint.json
```

`1PCloop/.local/` 被 Git 忽略。默认 workload ID 是 `--workload-static` 所在目录名，也可以用 `--workload-id` 显式指定。checkpoint 在每个控制面边界原子替换，不保存逐版本历史。terminal checkpoint 可以由下一次新 run 覆盖；未完成 checkpoint 不会被静默覆盖。

恢复未完成 run 时，使用与原 run 相同的 target、governance、角色配置和 cycle 上限，并增加：

```bash
python3 1PCloop/scripts/run_mutation_loop.py \
  <原有参数> \
  --resume
```

恢复前会重新核对配置、治理 hash、target branch/HEAD 和工作树。已完成并记录的 Executor commit 或 Reviewer turn 不会重跑；无法机械归因的中途 target mutation 会停止到 Human Gate。checkpoint 中的 Reviewer thread 不可安全复用时，Reviewer 可以从 repository-backed governance 和已保存的 peer evidence 重新 bootstrap。

Codex 子进程输出现在边运行边写入原始 evidence，同时终端显示 turn 开始/结束、可公开的工具事件和定时 heartbeat。默认 heartbeat 间隔为 15 秒，可用 `--progress-interval-seconds` 调整。Ctrl-C 等可处理的父进程中断会先终止当前 Codex 子进程，避免它成为继续修改仓库的后台 Agent。

运行 transport self-check：

```bash
python3 -m unittest discover -s 1PCloop/tests -v
```
