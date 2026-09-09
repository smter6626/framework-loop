# 1PCloop 后续研究实验规划

## 1. 文档目的与边界

本文档只记录 1PCloop 后续的研究问题、实验设计、测量方法、分析方案与投稿目标，不记录 UI、运行器、checkpoint、日志目录、权限配置等工程基建的实现计划。

当前系统已有的工程结果仅被视为 research prototype 和实验条件，不直接视为研究结论。任何假设都必须经过预先定义的对照实验和独立 ground truth 验证后，才能形成论文 claim。

## 2. 研究目标

1PCloop 拟研究的核心问题是：

> 将 Agent 工作流的控制状态从 conversation history 外化为 repository-backed authoritative state，并结合角色隔离、独立 evidence review 与受约束的状态推进，能否降低长时程编码任务在中断、状态漂移和错误执行下的 false acceptance？

研究重点不是证明“两个 Agent 可以协作写代码”，而是比较不同控制条件下：

- 错误结果被正式接受的概率；
- 正确结果被完成和接受的概率；
- 中断后恢复到正确状态的概率；
- REJECT 后成功修复的概率；
- 为可靠性付出的 token、时间、Agent turn 与 Human Gate 成本。

## 3. 预期研究贡献

论文候选贡献应收敛为以下三类，最终是否成立由实验结果决定：

1. **问题定义：** 明确定义长时程编码 Agent 中 conversation state、authoritative state、execution success、test success、review verdict 与 formal acceptance 的差异。
2. **安全性质：** 定义并检验 evidence-gated acceptance、角色权限隔离、幂等状态推进、失配时 fail closed 等可观察性质。
3. **实证结果：** 通过对照组与受控故障，量化独立审核和 repository-backed control 对 false acceptance、恢复正确率及运行成本的影响。

如果实验无法证明总体收益，也应报告机制在哪些任务或故障类型下有效、无效或成本过高，避免把负面结果隐藏为工程细节。

### 3.1 Novelty风险：被视为简单Multi-Agent应用

一个需要主动面对的负面解释是：1PCloop只是常见的Reviewer–Executor工作流，再附加一些状态管理和工程保护。这个风险是实质性的，因为多Agent角色分工、critique–repair、persistent session、external memory、工具调用和测试执行都已有大量先例。

因此，Reviewer–Executor分解应被明确定位为**实验载体**，而不是论文的主要贡献。论文不应对下列单项机制主张novelty：

- 使用多个Agent；
- 设置Reviewer和Executor角色；
- 自动传递消息；
- persistent context或external memory；
- critique、REJECT和repair；
- 测试执行；
- structured output；
- 单独存在的普通access control。

需要研究的对象是长时程Agent工作流中的**control semantics**：

- authoritative external state与conversation/session state的区别；
- state freshness、invalidation和supersession；
- 不同角色的mutation与transition authority；
- evidence sufficiency与evidence-backed acceptance；
- execution success、test success、review verdict和authoritative transition的分层语义；
- 中断或状态不一致后的fail-closed recovery；
- 无法机械确认正确性时的Human Gate行为。

因此，论文不应把核心claim写成：

> Reviewer–Executor多Agent架构提高了编码性能。

更可辩护、但仍需要实验支持的claim是：

> 显式权限、可从外部重建的权威状态、基于证据的接受条件和恢复语义，能否减少长时程Agent工作流中的false acceptance与invalid state progression？

候选贡献是围绕workflow authority、state validity、evidence sufficiency和acceptance semantics，对已有机制进行明确整合与可操作化，并证明这种整合能够阻止可测量的故障；不能仅以系统包含这些机制为由宣称创新。

### 3.2 Novelty风险解除标准

只有同时满足以下条件，才能认为“简单Multi-Agent应用”的风险得到实质性缓解：

1. 递增baseline和消融能够区分多Agent分解与Framework控制机制的效果；
2. 结果表明multi-agent decomposition本身不能完全解释可靠性变化；
3. 至少一个Framework相对于简单Multi-Agent baseline新增的控制机制，在受控条件下可测量地降低false acceptance、stale-state failure、invalid transition或recovery error；
4. 该收益不是单纯由更多模型调用、更大token预算或更强模型造成；
5. 同时报告false rejection、Human Gate和运行成本，避免把“更保守”误写成“更正确”。

如果简单Reviewer–Executor baseline与完整Framework表现相近，则更强的治理机制尚未得到实证支持，应据实缩小或否定相关claim。获得上述证据之前，1PCloop只能描述为research prototype和hypothesis-generating system，不能描述为已经验证的新型Agent架构。

## 4. Research Questions 与假设

### RQ1：外部权威状态与恢复正确性

在 Agent conversation history 丢失、截断或过期后，repository-backed authoritative state 是否比只依赖历史 session 更能恢复正确的当前任务状态？

候选假设：

- **H1a：** 在受控中断后，使用 authoritative state 的实验组具有更高的正确恢复率。
- **H1b：** authoritative state 能减少重复执行、遗漏步骤和错误恢复旧结论。
- **H1c：** 当状态不可机械协调时，fail closed 会降低错误继续执行，但可能增加 Human Gate 比例。

### RQ2：独立 Reviewer 与 false acceptance

Reviewer 与 Executor 的独立程度是否会影响错误接受率、漏检率和最终任务成功率？

候选假设：

- **H2a：** 独立 Reviewer 比 Executor self-review 具有更低的 false acceptance rate。
- **H2b：** context isolation 比共享完整执行历史更不容易继承 Executor 的错误前提和自我辩护。
- **H2c：** 独立审核可能提高 false rejection 或运行成本，因此需要同时报告收益和代价。

### RQ3：REJECT → REPAIR 的实际价值

由 Reviewer 产生 bounded repair instruction、再由 fresh Executor 修复的闭环，是否比 one-shot execution 或 Executor self-repair 更可靠？

候选假设：

- **H3a：** Reviewer 驱动的 repair 能提高存在初始缺陷时的最终正确率。
- **H3b：** bounded repair instruction 能减少与缺陷无关的修改。
- **H3c：** repair 收益会因缺陷类型、Reviewer能力和初始 evidence 质量而变化。

### RQ4：结构化控制与自然语言语义的边界

将确定性的控制字段与自然语言 semantic payload 分离，是否比完全自由文本控制或完全结构化语义通信更可靠？

候选假设：

- **H4a：** 结构化控制字段能够降低非法 verdict 和错误状态推进。
- **H4b：** 保留 opaque natural-language payload 不会显著降低任务正确率，并能减少因固定语义模板不足造成的信息损失。
- **H4c：** 完全结构化语义协议可能更易机械处理，但在复杂 repair instruction 中可能产生表达约束。

### RQ5：证据保留策略的正确性—成本权衡

raw run history、curated evidence summary 和只保留最终结果三种策略，会如何影响后续 Reviewer 的判断、陈旧证据复用和上下文成本？

候选假设：

- **H5a：** curated evidence 能显著减少输入上下文，同时维持接近 raw evidence 的审核正确率。
- **H5b：** 长期暴露全部 raw history 会增加 stale evidence reuse 和无关上下文干扰。
- **H5c：** 过度压缩的摘要会遗漏足以改变 verdict 的信息。

### RQ6：角色特定的 session persistence policy

Reviewer persistent、Executor fresh 的非对称策略，是否优于两个角色都 persistent 或都 fresh？

候选假设：

- **H6a：** persistent Reviewer 有利于保持审核连续性并降低重复理解成本。
- **H6b：** fresh Executor 更不容易继承旧任务的错误假设或扩大当前任务范围。
- **H6c：** 角色非对称策略的收益取决于任务链长度和治理状态变化频率。

## 5. 优先级与论文主线

第一篇论文不应同时把全部 RQ 作为同等重要的主贡献。建议优先级如下：

1. **主线：RQ1 + RQ2**——权威状态恢复与独立审核是否降低 false acceptance。
2. **关键机制实验：RQ3**——受控 REJECT → REPAIR。
3. **成本和解释实验：RQ5**——可靠性与上下文成本的权衡。
4. **可选消融：RQ4 + RQ6**——用于解释效果来自哪里；若实验规模不足，可留待后续论文。

第一篇论文的候选题目：

> From Conversation State to Repository-Backed Control: Reliable Recovery and Acceptance for Long-Horizon Coding Agents

## 6. 实验对象与任务采样

### 6.1 两层任务集

正式实验使用两类任务。

**普通软件任务：**

- bug 修复；
- 小型功能实现；
- 局部重构；
- 测试补充；
- 配置、构建或兼容性修复。

普通任务用于测量系统是否仍能有效完成真实开发工作。

**治理与故障任务：**

- 初始 patch 存在可验证缺陷；
- Executor 自报成功但 evidence 不支持；
- conversation history 丢失或只保留不完整摘要；
- authoritative state 与 target revision 不一致；
- evidence 缺失、过期、越界或内容被替换；
- 在不同状态推进窗口发生中断；
- 旧 verdict 与当前仓库状态冲突。

治理任务用于测量错误接受、恢复和升级决策，而不是普通 coding pass rate。

### 6.2 初始规模

建议先以 pilot 确认方差和实验成本，再决定正式样本量：

- pilot：10–15 个任务，覆盖至少 3 个仓库；
- 第一轮正式研究：30–60 个任务，覆盖至少 5 个仓库；
- 如果效应较小、任务差异较大或目标投稿要求更强，再扩展到更大的任务集。

任务应按 bug、feature、refactor、test/build 等类别分层采样，避免某个实验组只遇到较容易的任务。

### 6.3 纳入与排除规则

每个任务在实验前应固定：

- 起始 revision；
- 允许修改范围；
- 完成条件；
- hidden ground truth；
- 最大 Agent turn、token 或时间预算；
- 可接受的环境依赖。

任务不得因为某个实验组失败而在实验后随意删除。所有排除都应依据预先规定的环境故障、数据损坏或任务定义错误标准，并报告排除数量与原因。

## 7. 对照条件

建议至少比较以下实验组：

| 条件 | 执行与审核方式 | 主要用途 |
|---|---|---|
| A | 单 Agent one-shot，依据自身结果结束 | 最弱基线 |
| B | 单 Agent persistent session，并进行 self-review | 区分多轮思考和独立审核 |
| C | Reviewer–Executor 分角色、共享完整上下文，Reviewer可检查实际 evidence | 检验角色分工在不隔离上下文时的效果 |
| D | C + Reviewer–Executor context isolation | 检验context isolation的增量效应 |
| E | D + mechanically evidence-gated acceptance | 检验evidence gate的增量效应 |
| F | E + authoritative Runtime、capability-gated transition、recovery semantics与Human Gate | 检验完整Framework机制 |

如果预算有限，正式研究至少保留A、D、F；B、C和E可先用于较小规模的机制消融。但如果论文的主要目标是解除“只是简单Multi-Agent”的novelty风险，C、D、E、F之间至少要保留足够的相邻比较，不能只比较最弱单Agent与完整Framework。

所有实验组应尽可能保持以下条件一致：

- 使用相同任务起点；
- 使用相同模型版本或进行任务内配对；
- 使用相同工具权限和资源预算；
- 使用等价的任务描述与 acceptance criteria；
- 不因某个实验组结果较差而给予额外人工提示。

## 8. 受控故障注入

### 8.1 注入原则

每次故障注入必须预先记录：

- 故障类型；
- 注入位置和时机；
- 注入者；
- 预期可观察后果；
- 正确系统反应；
- ground truth；
- 允许的恢复边界。

注入故障必须明确标记为实验操控，不能在结果中误报为自然发生的 Agent 错误。

### 8.2 故障类别

1. **结果缺陷：** 编译失败、hidden test失败、边界条件遗漏、错误文件被修改、表面通过但不满足语义要求。
2. **证据缺陷：** evidence locator错误、hash不一致、引用旧commit、测试结果与当前HEAD不一致。
3. **状态缺陷：** stale Runtime、错误Active Step、旧Reviewer verdict、状态文件和仓库revision不一致。
4. **中断缺陷：** 在执行前、commit后、review前、verdict后或formal transition窗口中断。
5. **上下文缺陷：** Reviewer/Executor失去历史、获得截断历史、获得包含陈旧结论的history。

### 8.3 REJECT → REPAIR实验

至少有一组实验专门观察：

```text
initial defective result
→ Reviewer inspection
→ REJECT or incorrect ACCEPT
→ bounded repair instruction
→ fresh repair attempt
→ new evidence
→ re-review
→ final outcome
```

应区分：

- Reviewer是否发现缺陷；
- repair instruction是否准确定位问题；
- Executor是否只修改授权范围；
- repair是否真正解决ground truth中的缺陷；
- Reviewer是否依据新evidence更新判断；
- 最终是否发生错误接受或不必要拒绝。

## 9. Ground Truth

Reviewer verdict和Executor汇报都是被研究对象，不能作为最终正确性的唯一依据。

优先使用：

- hidden tests；
- 预先定义的行为断言；
- 静态或动态不变量；
- expected patch properties；
- 可独立运行的验证脚本；
- 与实验条件无关的人工审核。

需要人工标注时，标注者应尽可能不知道当前结果属于哪个实验组。对主观结果应使用至少两名标注者，并报告一致性和分歧处理方式。

## 10. 主要指标

### 10.1 主要终点

第一篇论文建议预先指定两个主要终点：

1. **False Acceptance Rate：** ground truth 判定错误，但系统产生formal acceptance的比例。
2. **Recovery Correctness：** 中断或状态失配后，系统恢复到唯一正确后续动作的比例。

### 10.2 次要终点

- true acceptance rate；
- false rejection rate；
- 最终任务成功率；
- 首轮缺陷检出率；
- repair success rate；
- 平均repair轮数；
- invalid Runtime/state transition rate；
- stale或superseded state/evidence复用率；
- 重复执行、重复commit或重复transition次数；
- Human Gate比例；
- Human Gate中真正需要人工判断的比例；
- 与授权范围无关的修改数量；
- token、latency、Agent turns和模型调用次数；
- 输入context和evidence体积。

### 10.3 复合指标限制

不建议只报告一个自定义“总体可靠性分数”。正确率、安全性和成本应分别报告；如果使用复合指标，必须同时公开其组成项和权重，并提供不同权重下的敏感性分析。

## 11. 实验流程

每个任务的建议流程如下：

1. 固定任务版本、ground truth、实验条件和预算；
2. 随机化或平衡实验组执行顺序；
3. 在不查看最终结果的情况下应用预定故障条件；
4. 执行到终态或预算耗尽；
5. 独立运行ground-truth验证；
6. 提取预先定义的指标；
7. 记录所有失败、超时、Human Gate和环境异常；
8. 完成pilot后冻结正式实验协议；
9. 正式实验开始后，不根据中间结果修改主要终点或选择性停止。

为减少模型服务波动和任务难度造成的偏差，同一个任务应尽量在多个实验条件下配对运行，执行顺序应随机化或使用平衡顺序。

## 12. 重复运行与统计分析

### 12.1 重复策略

pilot阶段可先对每个任务—条件运行约3次，用于估计结果方差、失败类型和成本。正式重复次数应根据pilot观察到的效应大小和统计功效确定；若成本允许，可考虑每个任务—条件5次或更多。

如果服务无法固定随机种子，应明确把重复调用视为随机样本，而不能把单次结果当作确定性模型能力。

### 12.2 分析方法

- 对同一任务上的二元结果优先采用配对分析；
- 报告绝对差值、相对差值和95%置信区间；
- false acceptance等配对二元指标可使用McNemar检验或适合重复测量的混合效应模型；
- token、时间和turn数量通常偏态，应报告中位数、四分位数，并使用bootstrap置信区间或稳健模型；
- 仓库、任务类型和模型版本可作为分层变量或随机效应；
- 多个次要RQ同时检验时，应报告多重比较处理或明确其探索性性质；
- 除显著性外，必须报告效应大小和实际意义。

### 12.3 失败分析

所有错误至少归类为：

- implementation failure；
- reasoning failure；
- evidence failure；
- review failure；
- state reconstruction failure；
- protocol violation；
- environment/service failure；
- budget exhaustion；
- unnecessary Human Gate。

分类标准应在正式实验前固定。代表性案例可以做定性分析，但不能替代总体统计结果。

## 13. Evidence-retention子实验

针对RQ5，可在相同review任务上比较：

1. 提供完整raw history；
2. 只提供curated evidence summary和实际artifact locator；
3. 只提供最终自然语言结论；
4. 提供混入陈旧或已superseded evidence的history。

测量：

- verdict正确率；
- stale evidence引用率；
- 查验实际artifact的比例；
- 输入token和review latency；
- Reviewer遗漏关键证据的比例。

摘要条件必须由与任务执行相同的规则产生，不能在看到Reviewer结果后人工优化摘要。

## 14. 泛化实验

在主实验结果稳定后，再考虑以下泛化维度：

- 不同规模和语言的仓库；
- bug、feature、refactor等不同任务类型；
- 不同模型能力档位；
- Reviewer与Executor使用相同模型或不同模型；
- 短任务与多step长任务；
- natural failure与controlled injected failure。

第一篇论文不必穷尽所有组合。至少应避免只在单一仓库、单一任务和单次运行上形成泛化结论。

## 15. 有效性威胁

### 内部有效性

- Reviewer获得的信息量可能在不同实验组间不等价；
- 多一次模型调用本身可能提高表现，与角色隔离效应混淆；
- hidden tests覆盖不足可能把错误结果判为正确；
- 服务端模型更新、缓存或usage limit可能改变结果；
- 人工注入缺陷可能比自然缺陷更容易识别。

### 构念有效性

- formal acceptance不完全等价于软件质量；
- pass rate不能单独代表长期可靠性；
- token和latency不能完整代表实际成本；
- Human Gate增加既可能表示保守可靠，也可能表示系统缺乏自主能力。

### 外部有效性

- 少量仓库不能代表真实软件生态；
- 单一模型或单一Agent产品限制可迁移性；
- 小型patch任务不代表长期连续开发；
- 受控故障结果不一定等同于自然生产故障。

### 结论有效性

- 样本量不足可能造成高方差；
- 多次试验后选择最好结果会夸大性能；
- 任务间不独立可能导致置信区间过窄；
- 只报告成功案例会形成选择性偏差。

## 16. 阶段划分与研究决策门

### 阶段A：研究定位确认

- 完成相关工作检索；
- 明确最接近的独立verification、state continuity和coding-agent研究；
- 冻结第一篇论文的主RQ、主要终点和baseline；
- 写出哪些内容是已有工作、哪些是待验证差异。
- 建立“已有单项机制—1PCloop操作化方式—对应消融条件—可测故障”的novelty矩阵；
- 明确哪些结果会支持核心claim，哪些结果将迫使论文降级为负面结果、经验报告或研究原型说明。

### 阶段B：Pilot

- 使用10–15个任务验证实验定义是否可执行；
- 估计false acceptance发生率、运行成本和方差；
- 检查ground truth能否独立判断；
- 根据pilot预先确定正式样本量和统计方案。

Pilot只用于调整协议，不与后续正式结果混合报告为确认性证据；如果合并，必须明确标记并做敏感性分析。

### 阶段C：正式主实验

- 对预先登记的任务和实验组执行配对重复实验；
- 以RQ1/RQ2为主，RQ3为关键机制验证；
- 保留所有失败、超时和异常结果；
- 在完成预定样本前不依据中间结果改变主要claim。

### 阶段D：消融与泛化

- 根据主实验结果选择必要的RQ4、RQ5或RQ6消融；
- 在额外仓库或模型上验证方向是否一致；
- 分析可靠性收益来自角色隔离、状态外化、证据审核还是额外计算量。
- 直接检验简单Reviewer–Executor是否已经能够解释完整Framework的效果；若可以，则不得继续宣称额外治理机制具有独立贡献。

### 阶段E：论文分析

- 汇总定量结果与置信区间；
- 进行失败类型和代表性案例分析；
- 明确不支持的假设和适用边界；
- 将系统能力描述限制在实验真实覆盖范围内。

## 17. 投稿目标与时间预期

当前成果应被定位为 research prototype，而不是已经完成的研究结论。

在实验条件准备完成后，如果能投入约4–6个月接近全职研究时间，可以把完成一篇CCF B或相近层级会议的投稿作为进取但现实的目标；如果以兼职方式推进，6–12个月更合理。这里指完成投稿，不承诺几个月内录用。

如果“B区”指中科院二区期刊，可以在形成完整实验后准备投稿，但审稿、返修和正式录用周期不由实验进度决定，通常需要更长时间。最终目标应根据投稿当年的学校或机构认定目录确认。

投稿前至少应满足：

- 有明确且经过相关工作检索支持的novelty定位；
- 不再以单个真实workload作为主要证据；
- 有预先定义的baseline和ground truth；
- 有足够重复运行和不确定性报告；
- 有受控REJECT → REPAIR和中断恢复数据；
- 明确报告false acceptance与可靠性成本；
- 结论没有超出实验覆盖的仓库、任务和模型范围。
- 至少一个Framework相对于简单Multi-Agent baseline新增的控制机制产生可测量的独立收益。

## 18. 通俗解释

当前项目已经像一辆装有安全员、行车记录仪和故障恢复机制的实验车，但“这辆车能开”还不是论文结论。

后续实验要让不同安全配置的车走相同路线，并在预先选定的位置制造断电、导航过期、证据丢失和司机交出错误结果等情况。然后用独立终点检测，而不是司机或安全员自己的口头汇报，判断车辆是否真的到达目的地。

最终要回答的不是“系统有没有运行成功过”，而是：

- 它比简单方案少犯了多少危险错误；
- 哪个机制真正产生了这个差异；
- 遇到什么问题时仍然无效；
- 为避免错误付出了多少时间、token和人工成本。

只有这些比较得到稳定、可复现的数据后，1PCloop才能从有研究潜力的工程原型转化为可以支撑论文主张的实证研究。
