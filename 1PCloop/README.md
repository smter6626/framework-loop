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

默认 session mode 是 `ephemeral-control`，三个 turn 都使用 fresh `--ephemeral`。P4-A 的 `reviewer-resume-treatment` 使用同一脚本，但 Reviewer Turn 1 创建持久化 thread、Executor Turn 2 仍为 fresh `--ephemeral`、Reviewer Turn 3 显式恢复 Turn 1 的 thread。Treatment 必须与 control 共用 repository 外部的 frozen experiment metadata，例如：

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

每次运行会在 `1PCloop/runs/<run-id>/` 下保存：

- `manifest.json`：三个 process result、两次 transport 和汇总 usage/cache 的机械 metadata；
- `transcript.md`：完整三回合 prompt、final response 和 process result；
- 每个 turn 的 `prompt.txt`、`events.jsonl`、`stderr.txt`、`final.txt` 和 `process.json`；
- 接收回合的 `peer-payload.txt`，用于与发送方 `final.txt` 做逐字节核对。

Orchestrator 只为每次调用设置角色、`CODEX_HOME`、sandbox、turn/run metadata 和文件路径。发送方 final response 以原始字节追加到接收方 prompt；Python 不解析其自然语言语义，也不根据其中的 `ACCEPT` / `REJECT` 等文字推进 Runtime。

每个 `process.json` 还会从原始 `events.jsonl` 机械派生 `thread_id`、input/cached/uncached/output/reasoning token 和 cache hit ratio。缺失或类型不符合当前 machine-readable event schema 的 usage 字段记录为 `null`，不会被当成 `0`；原始 JSONL 保持不变。

当前两个 session mode 的三个 turn 均显式使用 `read-only` sandbox，并且不会自动修改 Runtime。后续允许 Executor mutation 的阶段需要单独扩展 capability boundary。

运行 transport self-check：

```bash
python3 -m unittest discover -s 1PCloop/tests -v
```
