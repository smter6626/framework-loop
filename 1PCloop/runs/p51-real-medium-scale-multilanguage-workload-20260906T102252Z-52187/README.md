# P5.1 真实中规模 multiLanguage_v1 工作负载运行证据

## 文件定位

本目录是 `framework-loop` 中 P5.1 真实中规模 mutation workload 的原始运行证据。

```text
framework repository:
  /Users/smterpro/Workspace/framework-loop

evidence directory:
  1PCloop/runs/p51-real-medium-scale-multilanguage-workload-20260906T102252Z-52187/

original orchestrator run_id:
  20260906T102252Z-52187

runner:
  1PCloop/scripts/run_mutation_loop.py

target repository:
  /Users/smterpro/Workspace/whisper/live_subtitle_generator

target branch:
  multiLanguage_v1
```

## 本次运行做了什么

这是 P5.1 在真实外部仓库上的第一次成功中规模 Reviewer–Executor mutation run。
它使用 persistent Reviewer、fresh ephemeral Executor、显式 Reviewer resume、无 Codex
filesystem sandbox 与 post-turn mechanical audit。

运行结果：

- 原始 run ID：`20260906T102252Z-52187`；
- `3` 个 cycle、`7 / 7` 个 Codex turn 成功；
- Cycle 1 创建实现 commit `0d3b9e6c0f57dbd87a214717c07e4de9a4025d75`；
- Cycle 2 创建文档 commit `b9f61b39384001eae07c94d114ae66dcba0873cb`；
- Cycle 3 Executor 无 mutation，HEAD 保持不变；
- Executor no-op payload 仍被路由到 Reviewer final review；
- orchestrator 最终机械停止于 `STOPPED_FOR_HUMAN_REVIEW`，原因是
  `target_head_unchanged`；
- target 最终 working tree 为 clean。

## 目录内容

- `manifest.json`：运行配置、cycle 状态、target HEAD 演进、mechanical checks、thread/
  resume metadata、token/cache/耗时汇总；本文件保持原始 JSON，不作人工改写。
- `cycle-*/reviewer-instruction/`：初始 Reviewer instruction 的 prompt、final message、
  raw Codex events、process metadata 和 stderr。
- `cycle-*/executor/`：每轮 Executor 的 prompt、原样 peer payload、final receipt、raw
  Codex events、process metadata 和 stderr。
- `cycle-*/reviewer-review/`：每轮 Reviewer review 的 prompt、原样 Executor payload、
  final review、raw Codex events、process metadata 和 stderr。

其中 `prompt.txt`、`final.txt`、`peer-payload.txt` 用于复核 opaque natural-language
transport；`events.jsonl` 是 Codex CLI 原始事件流；`process.json` 保存从 machine-readable
events 派生的命令、退出码、usage、SHA、时间和 session/resume 关系。

## 治理边界

本目录是原始 mechanical evidence，不是长期 authoritative state。本次运行的 curated
control-plane 结论记录在：

- `1PCloop/docs/miniloop_runtime.md`；
- `1PCloop/workloads/multiLanguage_v1/workload_runtime.md`；
- target repository 的两个 ordinary descendant commits。

README 仅为目录定位和证据阅读说明；它不替代 manifest、Git history、Static/Runtime 或
Human Owner 的最终产品验收与 merge 决策。
