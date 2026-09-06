# P5.1 真实中规模工作负载阶段总结

## 文件定位

```text
framework repository:
  /Users/smterpro/Workspace/framework-loop

framework Static:
  1PCloop/docs/miniloop_static.md

framework Runtime:
  1PCloop/docs/miniloop_runtime.md

workload Static:
  1PCloop/workloads/multiLanguage_v1/workload_static.md

workload Runtime:
  1PCloop/workloads/multiLanguage_v1/workload_runtime.md

raw run evidence:
  1PCloop/runs/p51-real-medium-scale-multilanguage-workload-20260906T102252Z-52187/

target repository:
  /Users/smterpro/Workspace/whisper/live_subtitle_generator

target branch / final HEAD:
  multiLanguage_v1 / b9f61b39384001eae07c94d114ae66dcba0873cb
```

## 阶段结论

P5.1 已从 deterministic validation 和 disposable smoke 推进到真实 external-repository
medium-scale workload，并通过 Human Gate。本阶段形成了以下完整 evidence chain：

```text
P5 deterministic validation
-> first real workload exposes .git/index.lock sandbox blocker
-> fail closed and Human recovery
-> P5.1 no-filesystem-sandbox repair
-> deterministic regression validation
-> disposable real Git mutation smoke
-> real 3-cycle / 7-turn external-repository workload
-> two ordinary descendant target commits
-> final Executor no-op
-> Reviewer final review
-> mechanical Human Gate
-> Japanese/French live transcription smoke
-> Human acceptance with explicit residual coverage limits
```

本阶段不需要 run #3。`multiLanguage_v1` workload 已由 Human Owner 接受并关闭；target
branch 是否 push、是否 merge 到 `main` 仍是独立的 repository integration 决策。

## Human Gate 证据边界

Human Owner 实际验证了 Japanese 和 French 的 Whisper live transcription，两者主观效果
与现有 Chinese/English 体验接近。该结果提高了对真实 runtime propagation 的信心，但不是
controlled corpus、WER/CER benchmark 或所有语言的穷尽验证。

Spanish、German、Korean、Auto Detect、`.en` rejection 和 UI-locale/code preservation
没有在本次 Human smoke 中逐项手测。它们的当前支持来自 deterministic tests、共享的
canonical mapping/propagation path、Git implementation evidence 和 Reviewer 独立检查。
阶段接受不把这些路径描述为“Human-tested”。

## Research 相关性评估

Research 雏形的相关性和成熟度相比 P4/P5 初期明显提高，原因不是单纯“功能做完了”，
而是系统现在拥有一条可复核的真实失败—修复—再验证链：

1. **Ecological validity 提高。** Evidence 不再只来自 text transport、fake Codex 或
   disposable no-op，而是来自真实外部仓库、真实 source/tests/docs mutation、真实 Git
   metadata write 和真实音频转录。
2. **Failure-driven architecture evidence 增加。** 首次 workload 暴露 `.git/index.lock`
   blocker，control plane fail closed；P5.1 不是预设成功，而是针对真实 failure 修复后逐层
   重建 evidence。
3. **Role/session/state 分层得到联合观察。** Persistent Reviewer、fresh Executor、
   deterministic authoritative reconstruction、opaque peer payload 和 repository-backed
   state 在同一真实 workload 中共同运行。
4. **多层 acceptance boundary 得到实证。** Process success、test evidence、Reviewer
   semantic judgment、mechanical Human Gate 和 Human product acceptance 没有被混成一个
   `PASS` signal。
5. **效率指标可观测。** 七轮真实运行保留了 token/cache/latency 数据，后续可以形成
   controlled comparison；当前单次结果仍不能支持 session persistence 的因果 claim。
6. **Evidence-retention 问题变成真实研究对象。** Raw run 已完整保存，Runtime 又完成了
   lossless compaction，RQ9 不再只是抽象设想。

当前 evidence 对 RQ1、RQ2、RQ3、RQ5、RQ8、RQ9、RQ10 提供了更强的工程观察基础。
RQ4 仍缺少 independent-review 与 self-review 的对照；RQ6 仍缺少真实 loop 内的
REJECT→REPAIR event；RQ7 仍缺少 opaque natural language 与 structured protocol 的受控比较。

因此，项目已经更接近 research-ready prototype，但仍不是 research conclusion：只有一个
真实中规模 workload、没有 replicate、Human smoke 只覆盖两种新增语言、Reviewer rejection
count 为零，也没有证明 literature novelty。

## 下一阶段建议：P6

下一阶段应继续保持单变量、分阶段验证，不直接扩展成多 Executor 或生产平台。

### P6-A — Controlled REJECT → REPAIR → re-review

构造一个 bounded disposable 或小型真实 workload，使初始 evidence 中存在可机械定位的缺陷，
并真实运行：

```text
Reviewer detects insufficient/incorrect evidence
-> Reviewer issues one bounded repair instruction
-> fresh Executor creates repair evidence/commit
-> persistent Reviewer resumes and independently rechecks
-> Human classifies the opaque semantic sequence
```

需要记录 rejection/repair count、修复轮数、false acceptance、最终 correctness、token 与
latency。Python 继续不解析 Reviewer 自由文本。

### P6-B — Authoritative verdict/Runtime transition channel

在不解析自然语言的前提下增加独立 control channel。候选设计是 Reviewer-only、
capability-gated 的窄工具，例如提交：

```text
verdict = ACCEPT | REJECT | HUMAN_GATE
active_step_id
evidence_locator(s)
expected governance/target hashes
```

Python 只校验 schema、capability、hash freshness、evidence locator 和允许的 state-machine
transition；Reviewer 的完整 reasoning 仍作为 opaque natural-language payload。Executor 不得
拥有最终 ACCEPT 或 Runtime transition capability。

### P6-C — Crash/restart reconstruction

把目前仅存在于单次 Python process memory 的 loop state 持久化，包括 Reviewer thread ID、
known governance hashes、known target HEAD、cycle、payload SHA 和 last completed transition。
重启时必须检测 drift、保证 idempotence，并在状态不充分时 fail closed。

### P6-D — Curated evidence policy

定义 raw run、curated evidence 与 Runtime 之间的长期边界：哪些 raw artifacts 必须保留，
哪些可以压缩，哪些只需 manifest/hash/locator，以及如何避免未来 Agent 默认加载全部历史日志。

### 后续而非立即优先

- 对 no-sandbox policy 研究更强的 capability boundary；
- 对 independent Reviewer 与 self-review 做 controlled comparison；
- 对 opaque natural language 与 structured semantic protocol 做 controlled comparison；
- target locking、并发和多 Executor；
- GUI、分布式部署、RAG 或长期 memory database。

## 阶段关闭后的权威状态

```text
multiLanguage_v1 workload phase = HUMAN ACCEPTED / CLOSED
target push/merge                  = NOT PERFORMED
P5.1 real control-plane path       = VERIFIED
overall 1PCloop                    = ACTIVE
recommended next phase             = P6-A, then P6-B
```
