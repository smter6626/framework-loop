# 1PCloop 暂停/冻结的研究地图与未来实验启用规则

> **状态：** `PAUSED / FROZEN RESEARCH MAP`；`NOT AN ACTIVE ENGINEERING EXECUTION PLAN`。
>
> **当前 supersession：** Human Owner 于 `2026-09-12` 暂停 paper/research-driven 路线，
> 将当前工程资源转向 foundation_v1。本文件保留三轮 novelty audit、dead directions、窄候选
> 和未来 research gates，但不再驱动当前工程执行。
>
> **中心边界：** 当前没有 active paper experiment；候选 A/B/C 均未激活。未来只有 Human
> Owner 明确重新打开 research track 后，本文件才恢复为研究规划输入。foundation_v1 工程
> 工作不需要通过 research/advisor gate。

---

## 1. 文档职责

本文件冻结保留：

- 1PCloop 在暂停时点的研究定位；
- 已被删除的宽研究方向；
- 尚可保留的窄候选问题；
- 未来重新启用 research track 时的条件、停止条件与 claim boundary。

本文件不维护：

- P6.4 / P7 等工程执行状态，该状态只由 `1PCloop/docs/miniloop_runtime.md` 维护；
- 1PCloop 稳定工程约束和验收标准，该内容只由 `1PCloop/docs/miniloop_static.md` 维护；
- 三轮 audit 的完整 paper-by-paper 论证，详情保留在对应 kill report 与三轮中文研究地图。

当前工程状态只由全局 Runtime 与 foundation_v1 task-local Static/Runtime 维护。本文件不得用来
激活 P7、候选 A/B/C 或 foundation step，也不把 foundation_v1 的详细进度复制到研究地图。

---

## 2. 当前研究结论

### 2.1 Framework 的定位

Structured LLM Execution Framework v1.2 是从真实 long-running LLM / coding-agent failure 中形成的 repository-native methodology artifact。它能证明：

- independent problem formation；
- systems abstraction 与 failure-oriented design；
- 对 state、evidence、review、authority、recovery 和 Human boundary 的实践理解。

它不证明：

- 相关机制是首次提出；
- 该方法在因果上提高 reliability 或 productivity；
- Framework 应成为未来论文或博士 thesis 的中心。

`FRAMEWORK_AS_PAPER = 暂停`

### 2.2 1PCloop 的定位

1PCloop 已将 Framework 的部分机制实现为可运行的 Reviewer–Executor control plane，并已 operationalize：

- persistent Reviewer + fresh Executor；
- deterministic governance bootstrap；
- Static / Runtime freshness metadata；
- Runtime-enforced structured verdict；
- Reviewer-only verdict authority；
- evidence identity / hash checks；
- gated Runtime transition；
- checkpoint / resume / reconciliation；
- local raw evidence + bounded tracked summary；
- apply-once style transition behavior。

这些内容可作为 engineering evidence 与 future experimental treatment，但不建立：

- causal reliability gain；
- Framework comparative superiority；
- Reviewer false-acceptance reduction；
- natural failure prevalence；
- benchmark-quality long-horizon generalization。

`1PCLOOP_ENGINEERING_ARTIFACT = 保留`

`1PCLOOP_EXPERIMENTAL_HARNESS = 保留`

---

## 3. 已删除的宽研究方向

### 3.1 Execution governance / authoritative transition

原问题：

> 如何让 probabilistic Agent judgment 安全进入 deterministic authoritative workflow state？

Agentic Transaction Processing、Cordon、CapLease、CXI、SemIso、Atomix、code-review approval semantics 与传统 transaction / recovery work 已直接覆盖 proposal≠truth、state/evidence/authority validation、deterministic admission、stale rejection、supersession、compensation 与 recovery。

`VERDICT = A — DEAD`

### 3.2 Decision semantics under compression

原问题：

> 哪些信息必须 survive summarization / compression / handoff，才能保持 downstream decision behavior，而不只是 factual content？

*When “Must” Becomes “Maybe”*、*Remember the Decision, Not the Description*、AuthMem-Bench 及相关 memory / decision-abstraction work 已直接覆盖 operational preservation、decision-centric rate–distortion、minimal policy-relevant state、authority laundering 与 repeated consolidation drift。

`VERDICT = A — DEAD AS A BROAD DIRECTION`

### 3.3 Claim-relative evidence adequacy / layered acceptance

原问题：

> passing evidence 多少时候无法 discriminate 当前 acceptance claim，process / test / review / Human / formal transition 的混淆会造成多少 false success？

*Validation Evidence in LLM Repair Agents*、STING、SWE-bench audits、ClaimReceipt、UnderSpecBench 等已直接覆盖 evidence existence≠sufficiency、test pass≠semantic correctness 与 layered success notions。

`VERDICT = A — DEAD`

### 3.4 旧 RQ1–RQ6 的当前含义

被替代的旧版 research plan 中，external authoritative state、independent Reviewer、REJECT→REPAIR、structured control、evidence retention 和 session persistence 被当作论文主线或主要消融。

这些内容现在只能作为：

- engineering requirement；
- experimental treatment / baseline；
- 新 exact RQ 下的局部变量；
- historical problem-formation record。

它们不再是当前的 paper-level novelty claim，也不得仅因换成 real repo / coding-agent workload 就重新升级。

---

## 4. 当前保留的窄候选

本节只记录尚未被完全直接覆盖的 causal slice。它们不是已建立的 novelty，也不是已授权的长期项目。

### 4.1 候选 A：Decision-existence-aware control

#### Exact RQ

> Agent 若显式区分 world-determined、latent-user、owner-constituted 和 delegated decision variable，是否能比 generic clarification / EVPI-style ask policy 更好地选择 discover、elicit、deliberate-and-ratify 或 autonomous action？

#### 直接 prior 边界

SAGE、*Ask or Assume?*、ClarifyCodeBench、*Clarify When Necessary*、UnderSpecBench、preference-construction literature 与 meaningful-human-control work 已覆盖 clarification utility、underspecification、constructed preference 和 decision authority 的主要 primitive。

只剩的窄 contrast 是：

> frozen hidden answer 与 not-yet-constituted owner choice 是否需要不同的 Agent interaction policy。

#### 候选 cheap pilot

- 24–40 组 paired scenarios；
- 四类 decision stratum：world-determined、latent-user、owner-constituted、delegated；
- 条件：default autonomous Agent、generic uncertainty prompt、existing ask-policy baseline、type-aware policy；
- 指标：fabricated-intent rate、wrong-action rate、unnecessary clarification、owner effort、framing sensitivity、completion time 与 task utility。

`STATUS = C — NARROW SURVIVING GAP / 首选便宜试验候选`

### 4.2 候选 B：Acceptance-induced verification suppression

#### Exact RQ

> 在 artifact、latent error 和 downstream task 完全相同时，`UNREVIEWED / SELF-CHECKED / REVIEWED / FORMALLY ACCEPTED` 状态标签本身是否会抑制后续 Agent 重新验证？

#### 直接 prior 边界

SWE-Milestone、Admission Without Answers、AgentAsk、faulty-agent resilience、memory-authority 与 trust-in-automation literature 已覆盖 error cascade、poisoned admission 和错误信任。

只剩的窄 contrast 是 formal status label 的 same-artifact causal effect。

#### 候选 cheap pilot

- 固定 artifact / latent error / downstream task；
- 只操控 governance status；
- 测量 test rerun、source inspection、status-citation、bug discovery latency、cascade depth 和 repair radius；
- 可比较 mechanical test badge、LLM Reviewer verdict、Human acceptance 与 scope-limited acceptance。

`STATUS = C — NARROW SURVIVING GAP / 更便宜的备选试验`

### 4.3 候选 C：Evidence-path independence

#### Exact RQ

> 在匹配 reviewer capability、compute、task 和 artifact 后，independent evidence selection 是否比 model/vendor diversity 更能解释 false-acceptance reduction，writer rationale exposure 是否会污染 Reviewer？

#### 直接 prior 边界

Cross-Model LLM Code Review、Preference Leakage、behavioral-entanglement 与 self-review work 已覆盖 generic independent reviewer、same-vs-cross-model review 和 correlated error。

只剩尚未在同一实验中正交拆分的 context、writer-rationale 与 evidence-path factors。

#### 候选 factorial

- Reviewer model / capability 固定；
- writer rationale：exposed vs hidden；
- evidence selection：writer-selected vs independently selected；
- 使用 hidden correctness oracle；
- 报告 false acceptance、false rejection、cost 与 regression。

`STATUS = C — NARROW SURVIVING GAP / 次选 systems factorial`

---

## 5. 新研究实验的启用门

研究启用分为两级：

- 开始 cheap pilot 前：必须通过 §5.1 问题存活门和 §5.2 advisor-judgment 门，并按 §5.3 预先定义试验；
- 从 cheap pilot 扩展到正式研究前：除上述条件外，还必须通过 §5.4 资源决策门。

### 5.1 问题存活门

- exact RQ 只包含一个可区分的 causal contrast；
- 能明确列出 strongest direct-answer prior；
- 能说明与 prior 的区别不是换名、换 domain 或把成熟 primitive 组合进 YAML；
- 若只剩 replication / benchmark extension，必须显式降级。

### 5.2 Advisor judgment 门

在投入数周或数月前，需要征求有相关 field map 的导师 / PI 意见，重点确认：

- 窄 gap 是否值得独立 paper；
- 它是否只是现有 work 的一个自然 ablation；
- 什么 pilot result 才值得扩展；
- 加入现有 Agent project 是否比继续独立 narrowing 更有价值。

Advisor feedback 是研究资源分配门，不是请求导师直接给 paper idea。

### 5.3 Cheap-pilot 门

- 先用 1–2 周可完成的规模检验 effect 是否存在；
- 优先建立 counterfactual control，不先扩张 benchmark；
- 预先定义主指标、failure criterion 和 expansion threshold；
- 试验失败或 effect 被 strong baseline 解释时立即停止，不用后验指标挽救。

### 5.4 资源决策门

只有当便宜试验结果表明以下至少一项时，才考虑扩展：

- 存在不能被 strong baseline 解释的稳定 effect；
- 发现一个比原候选更精确、更有科学价值的新 RQ；
- advisor 认为即使 effect 有限，该 benchmark / measurement 仍具有明确研究价值。

---

## 6. 统一测量与报告边界

任何已启用的实验至少应报告：

- 与 exact RQ 直接对应的 primary endpoint；
- false positive / false negative 或 risk–coverage trade-off；
- token、time、Agent turn 与 Human effort 成本；
- model / prompt / tool / artifact / task 的控制情况；
- failure taxonomy 与 strong alternative explanation；
- negative result 和停止条件。

不得将以下信号混合为一个“成功”：

```text
进程结束
工具或测试通过
Reviewer verdict
Human acceptance
Runtime transition
科学假设得到支持
```

这一分层是证据纪律，不是 novelty claim。

---

## 7. 与 1PCloop 工程路线的历史/冻结关系

### P6.4

P6.4 曾作为 active engineering step 完善 sequential lifecycle 与 external-mutation boundary，
随后已独立接受并随 P6 关闭。本段保留当时的研究边界，不是当前工程状态。

P6.4 当时可以继续，但：

- 不是 PhD 申请材料的 blocker；
- 不为旧 RQ1–RQ6 提供 novelty；
- 不得因为 regression / smoke 通过就记为 research finding。

### P7

P7 在 P6 关闭后曾被激活，随后由 Human Owner 于 `2026-09-12` 暂停。受控
REJECT→REPAIR fault injection 仍可作为未来 optional engineering coverage，但当前不 active，
generic repair-loop benefit 也不是已建立的 novelty。

只有 Human Owner 明确重新打开 research track，且以下情况之一发生时，才重新评估 P7 的
研究优先级：

- 某个经 exact-RQ / direct-prior / advisor-judgment 门通过的新问题确实需要该 treatment，且它被定义为受控 cheap pilot 或已通过 pilot 的扩展实验；
- 工程完整性本身对 artifact 展示或开源可用性具有明确价值。

---

## 8. Research track 重新启用后的候选顺序与当前停止规则

以下顺序仅在 Human Owner 重新启用 research track 后作为候选输入，并非当前执行计划：

1. 完成 Fall 2027 PhD SOP v0/v1；
2. 与 Professor YooJung Choi 沟通 research direction / problem selection；
3. 根据 advisor feedback 决定：做候选 A/B/C 的便宜试验、继续独立 narrowing，或优先加入现有 Agent project；
4. 只对通过启用门的 exact RQ 编写新实验计划。

当前明确停止并继续有效：

- 不继续从 Framework 挖第四个宽理论方向；
- 不进行 old RQ1–RQ6 的 full experiment matrix；
- 不在 advisor feedback 前把三个 narrow candidate 扩成数月项目；
- 不以“在 real repo 上实验”作为足以支持 novelty 的理由；
- 不把 Framework 或 1PCloop 写成已验证的 reliable-Agent architecture。

---

## 9. 研究来源与完整论证

当前研究方向来自下列文档：

- Round 1：`/Users/smterpro/Workspace/Research/probabilistic-circuits/repos/phd_prepare/audits/details/round1_execution_governance.md`
- Round 2：`/Users/smterpro/Workspace/Research/probabilistic-circuits/repos/phd_prepare/audits/details/round2_decision_semantics.md`
- Round 3：`/Users/smterpro/Workspace/Research/probabilistic-circuits/repos/phd_prepare/audits/details/round3_residual_directions.md`
- 三轮中文地图：`/Users/smterpro/Workspace/Research/probabilistic-circuits/repos/phd_prepare/audits/Framework_Research_Novelty_3Rounds_CN.md`

本文件只保存当前方向、启用门和停止规则。需要审核 exact prior 时，必须读取上述报告，不只依赖本文的压缩总结。
