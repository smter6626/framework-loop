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

当前两个 session mode 的三个 turn 均显式使用 `read-only` sandbox，并且不会自动修改 Runtime。后续允许 Executor mutation 的阶段需要单独扩展 capability boundary。

运行 transport self-check：

```bash
python3 -m unittest discover -s 1PCloop/tests -v
```
