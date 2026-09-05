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

每次运行会在 `1PCloop/runs/<run-id>/` 下保存：

- `manifest.json`：三个 process result、两次 transport 和汇总 usage/cache 的机械 metadata；
- `transcript.md`：完整三回合 prompt、final response 和 process result；
- 每个 turn 的 `prompt.txt`、`events.jsonl`、`stderr.txt`、`final.txt` 和 `process.json`；
- 接收回合的 `peer-payload.txt`，用于与发送方 `final.txt` 做逐字节核对。

Orchestrator 只为每次调用设置角色、`CODEX_HOME`、sandbox、turn/run metadata 和文件路径。发送方 final response 以原始字节追加到接收方 prompt；Python 不解析其自然语言语义，也不根据其中的 `ACCEPT` / `REJECT` 等文字推进 Runtime。

每个 `process.json` 还会从原始 `events.jsonl` 机械派生 `thread_id`、input/cached/uncached/output/reasoning token 和 cache hit ratio。缺失或类型不符合当前 machine-readable event schema 的 usage 字段记录为 `null`，不会被当成 `0`；原始 JSONL 保持不变。

当前文本里程碑的三个 turn 均显式使用 `read-only` sandbox，并且不会自动修改 Runtime。后续允许 Executor mutation 的阶段需要单独扩展 capability boundary。

运行 transport self-check：

```bash
python3 -m unittest discover -s 1PCloop/tests -v
```
