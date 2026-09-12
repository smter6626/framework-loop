# 2026-09-12 post-P6 foundation smoke — Durable Compact Evidence

## 1. 结论

```text
COMPLETED OBSERVATION
SAFETY BEHAVIOR PASSED
END-TO-END RUN FAILED CLOSED
USABILITY GAP DISCOVERED
```

这不是整体 `PASS`。Target implementation 成功，Reviewer 独立检查后返回 schema-valid
`ACCEPT`，但其中两条 evidence locator 不符合机械边界，因此 orchestrator 正确拒绝
authoritative Runtime transition。Evidence publication 随后完成；publication success 不改变
logical failure。

## 2. 测试目的与隔离

目的：验证 P6 后真实 Reviewer → Executor → Reviewer、capability-gated Runtime transition 和
evidence finalization 路径，并观察日常运行的恢复/可用性边界。

隔离方式：

- disposable target：`/tmp/1pcloop-post-p6-smoke.jomR1L/target`；
- disposable framework：`/tmp/1pcloop-post-p6-smoke.jomR1L/framework`；
- local bare framework remote：
  `/tmp/1pcloop-post-p6-smoke.jomR1L/framework-remote.git`；
- local bare target remote：`/tmp/1pcloop-post-p6-smoke.jomR1L/target-remote.git`；
- source framework-loop HEAD：`2bc90d6500104bbb7e5d0b16ce82887974dce69e`；
- 正式 framework-loop、closed workload 和 target repository 均未修改；
- 未运行 P7，未注入 defect。

macOS 中 raw artifact 内嵌 locator 可能显示等价的 `/private/tmp/...` 实路径。本记录使用 Human
提供的 `/tmp/...` 入口；两者指向同一 disposable tree。

## 3. 固定 identity

| 对象 | Identity / SHA-256 |
| --- | --- |
| Target baseline | `79d67a5661328954bf651bbabf2e14f4fcc7bb05` |
| Target result commit | `4973f429c41466fbd2881d60a095fbbb53f21ace` |
| Target commit raw object SHA-256 | `0e21ee00c87c87684dfc3207f591941065678f0c8ef56b2d60498969aa74287f` |
| `smoke_value.txt` SHA-256 | `bf9c48430e45e3fcae52da57e16a93cfc9b2a850b1da5eddce41edbd248edc03` |
| Reviewer verdict `final.txt` SHA-256 | `a0713bc8dc9c38dc338bb72060f3c98982bf8029fa17bf2fb0c5ef0f197382b9` |
| Generated tracked summary SHA-256 | `b28d68c10818658bf8b53db9716ebe54e74a11d21888ea99c52e10ccfafb085a` |
| Raw manifest SHA-256 | `9846e3531a109bf245255636c4fdf0a57fc221997fcb2b5f8232c39847ff3233` |
| Final checkpoint SHA-256 | `af51fe029da37413e16ca59abc7c673d46a800adb00e57c9569e933ad75c31f9` |
| Disposable framework baseline | `a766f85cb8ccfa95e8eab17ef2a32425c7609604` |
| Disposable framework evidence commit | `3a7d073bb2e557b145a72a3aad83ca56f9f98183` |

以上 identity 于治理初始化时从仍存在的 raw tree 和 Git object 重新计算或直接解析，并与
Human 提供值一致。

## 4. Agent 结果

- Codex turn process success：`3 / 3`；
- Reviewer instruction：`30.746s`；
- Executor：`68.330s`；
- Reviewer review：`65.525s`；
- total Agent duration：`164.601s`；
- input tokens：`199228`；
- cached input tokens：`137472`；
- uncached input tokens：`61756`；
- output tokens：`6134`；
- reasoning output tokens：`1793`；
- Reviewer review 使用原 persistent thread 的显式 resume，relationship verified。

## 5. Target 结果

- branch：`smoke`；
- baseline → result：
  `79d67a5661328954bf651bbabf2e14f4fcc7bb05` →
  `4973f429c41466fbd2881d60a095fbbb53f21ace`；
- result commit 是 baseline 的一个普通直接 descendant；
- commit 只修改 `smoke_value.txt`；
- exact bytes：`P6_POSTHARDENING_SMOKE_OK\n`；
- `test_smoke.py` 的一个 unittest 通过；
- target worktree clean；
- target bare remote `refs/heads/smoke` 仍为 baseline
  `79d67a5661328954bf651bbabf2e14f4fcc7bb05`，target 未 push。

## 6. Reviewer verdict 与机械拒绝

Reviewer 直接检查 target commit、文件字节、测试和 clean worktree，返回 `ACCEPT`。Commit 与
file evidence 有效；verdict 同时包含两条机械不合法 evidence：

- `test` locator 是命令描述，不是允许边界内的绝对文件路径；
- `artifact` locator 是 Git status 描述，不是允许边界内的绝对文件路径。

Reviewer final JSON 通过 output schema，但 local authoritative evidence validation 拒绝该
`ACCEPT`：

```text
reason = file/artifact evidence requires an absolute locator
logical outcome = FAILED_CLOSED
exit code = 1
runtime_transition_applied = false
```

Disposable workload Runtime 的 machine block 仍保持 `S1 / ACTIVE`、
`transition_mode=reviewer_accept_once`、`last_transition_id=null`，未发生 Runtime transition。

## 7. Evidence finalization

- tracked summary entries：`3`；
- disposable framework baseline：`a766f85cb8ccfa95e8eab17ef2a32425c7609604`；
- framework evidence commit：`3a7d073bb2e557b145a72a3aad83ca56f9f98183`；
- evidence commit 只新增 generated tracked summary；
- framework-only push 成功，bare remote `refs/heads/main` 到达 exact evidence commit；
- final checkpoint control state：`FRAMEWORK_EVIDENCE_PUSHED`。

`FRAMEWORK_EVIDENCE_PUSHED` 只代表 evidence publication 完成。该 run 的独立 logical outcome
仍是 `FAILED_CLOSED`，不能从 control state 推断 end-to-end success。

## 8. 当前工程语义

- fail-closed safety behavior 正常；
- target implementation 成功且保留为本地未推送 commit；
- end-to-end authoritative transition 未完成；
- 可纠正的 Reviewer evidence-locator 错误暴露了 foundation_v1 F1 的 usability/recovery
  requirement：优先纠正 Reviewer control output，不默认重跑成功 Executor；
- UI/status 必须并列显示 logical outcome、Runtime transition 和 evidence publication；
- 本 observation 不是 P7、不是 research experiment，也不是完整 `PASS`。

## 9. Raw evidence 生命周期

Raw root：`/tmp/1pcloop-post-p6-smoke.jomR1L`。

关键 raw locator：

- `framework/1PCloop/.local/runs/post-p6-smoke-20260912/manifest.json`；
- `framework/1PCloop/.local/state/post-p6-smoke/checkpoint.json`；
- `framework/1PCloop/evidence-summaries/post-p6-smoke-20260912.md`；
- `framework/1PCloop/.local/runs/post-p6-smoke-20260912/cycle-01/reviewer-review/final.txt`。

`/tmp` 内容属于 disposable local evidence，未来可能被系统清理。本 tracked compact summary
保存不依赖当前对话的关键 observation 与 identity；不复制完整 prompt、events、stderr、
process JSON、checkpoint 正文或隐藏 reasoning。
