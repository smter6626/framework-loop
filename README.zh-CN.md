# Framework Loop

[English](README.md) | 简体中文

Framework Loop 是一个以 repository-backed governance 驱动的 Reviewer–Executor 自动化系统。
当前唯一主线是 **1PCloop**：在一台 Mac 上使用两个隔离的 Codex identity，自动完成任务编译、
代码执行、独立复核、修复循环、Human Gate 和可审计状态推进。

> **项目状态**
>
> - [`1PCloop/`](1PCloop/README.zh-CN.md)：唯一 active implementation 和维护主线。
> - [`2PCloop/`](2PCloop/)：历史设计归档，当前不启用、不实现，也没有 active Runtime。

## 它解决什么问题

长时间 coding-agent 工作容易把目标、当前进度、证据和批准权限混在聊天记录里。1PCloop 将它们
拆成稳定合同、当前状态和实际 artifact，让任务可以跨会话恢复，也让“执行完成”和“独立验收”
不再是同一个 Agent 的一次自我声明。

```text
                         Human Owner
                              |
                     Static / Runtime
                              |
                              v
                    deterministic orchestrator
                              |
                 +------------+------------+
                 |                         |
                 v                         v
             Reviewer                  Executor
          独立检查与裁决             实现、测试、提交
                 |                         |
                 +----------- Git / evidence
                              |
                  ACCEPT / REJECT / HUMAN_GATE
```

系统自动完成 Reviewer → Executor → Reviewer 的消息路由。Reviewer 接受时，orchestrator 才能在
Human 预先授权的范围内推进 Runtime；Reviewer 拒绝时，修复指令会回到 Executor；需要主观决定、
权限扩张或无法由证据解决的问题会自动停止在 Human Gate，并在终端和本地状态中留下明确提醒。

## 已实现基础与可扩展形态

1PCloop 已经实现四项核心能力的当前单 Reviewer/单 Executor 版本。后续工作是在不改变
Static/Runtime/evidence 治理语义的前提下，把同一基础扩展到本地模型、其他 Agent、视觉工具和
多个可替换 worker，而不是从零重新设计一个系统。

```text
                  Human Owner
                       |
          Static / Runtime / Git / Evidence       已实现
                       |
                       v
        Authoritative Context Construction         已实现
                       |
                       v
            persistent/resumable Reviewer          已实现
                       |
                       v
              fresh bounded Executor               已实现
                       |
                 artifact / evidence
                       |
                       v
               Reviewer final gate                 已实现

      local / cloud / vision / GUI worker adapters 可扩展
```

### Cost–quality decoupling

当前已经实现的基础是：Reviewer 与 Executor 使用独立 profile/session，可以选择不同模型和
reasoning effort；Executor 负责高消耗实现，只有 Reviewer 基于实际 evidence 形成的 verdict 才能
推进 Runtime。因此执行成本和最终 acceptance authority 已经不再绑定在同一个 Agent 上。

可扩展形态是把高 token、高工具调用频率的工作交给本地或更便宜的 Executor，把任务编译、证据
检查和最终 verdict 留给更强的云端 Reviewer。例如，在本机运行 Qwen 35B A3B MoE Q8 Executor，
同时使用 GPT-5.6 Sol Reviewer。当前 Codex CLI 已支持 Ollama/LM Studio 本地 provider；1PCloop
仍需为这种 mixed local/cloud 配置补充明确的 per-role provider 配置和端到端 evidence。

这种组合不保证本地模型首次生成质量与云端强模型相同。较弱 Executor 可能增加 repair 次数和
总耗时；优势是只有达到 Reviewer evidence gate 的结果才被接受，从而有机会降低云端成本而不必
同比降低最终验收门槛。

当前 Executor 已经是 fresh ephemeral session，不依赖前一轮 Executor conversation。未来接入本地
模型时，CLI session 可以继续每轮退出，而 Ollama/LM Studio service 和模型权重保持常驻。已有运行
也观察到稳定 prompt prefix 的高 cache hit；这与缩短 context window 是两个不同优化。Bounded
instruction 允许在质量相近时减少实际输入或配置更小窗口，但必须通过真实 workload 验证。

### Contract-backed context

这项能力已经实现，而且不只是 external memory：

```text
Static       = 长期目标、硬约束和授权边界
Runtime      = 当前有效状态、唯一 Active Step 和 Human decision
Git/Evidence = 支持状态和 verdict 的可定位事实
```

Agent、模型和 session 可以替换，而任务不会随某段 conversation 一起丢失。新 Reviewer 可以从
带 hash 的治理文件恢复当前权威状态；fresh Executor 可以从 bounded instruction 开始；Human
可以按 commit、artifact 和 hash 随时复查。被 supersede 的旧结论不会因为仍存在于历史里就重新
取得权威。

后续 provider adapter 只需要服从同一 contract、identity、freshness 和 evidence boundary，不需要
为每个 Agent 产品重新发明项目 memory。

### Capability reuse

当前 1PCloop 已经复用 Codex CLI 的 shell、文件、Git 和工具调用能力，并在外层增加角色、权限、
evidence、Runtime transition 和 Human Gate，而不是由 orchestrator 重新实现 coding tools。

同一原则可以扩展到 vision、browser、MCP、plugin 和 Computer Use。Codex CLI 当前提供本地
Ollama/LM Studio provider 和 image input；Codex/ChatGPT 的 Computer Use 可以通过桌面端插件及
系统授权操作 GUI。对应官方边界见 [Codex CLI 命令参考](https://learn.chatgpt.com/docs/developer-commands?surface=cli)
和 [Computer Use](https://learn.chatgpt.com/docs/computer-use)。这些视觉/GUI 路径尚未接入当前
1PCloop runner。

今天接入 Codex、以后接入 Claude、其他云端 Agent 或本地视觉模型时，Static/Runtime 和
evidence contract 可以保持不变；主要迁移面收敛到 invocation、structured output、tool
capability、timeout/cancellation 和 identity adapter。换 Agent 的治理成本可以很低，但每个新
adapter 仍需要兼容性和安全验证。

GUI 操作可能影响 repository 外部状态。Computer Use 等能力接入后仍必须经过 app permission、
action/screenshot evidence、敏感操作审批和 Human Gate，不能绕过现有 authority boundary。

### Authoritative context-compiled workers

这项能力的窄版本也已经实现：Reviewer 在 fresh bootstrap 时获得完整、带 hash 的 framework/
workload Static 与 Runtime；Executor 每轮使用 fresh session，只获得角色约束、当前 bounded
instruction、target identity 和必要 evidence context。Executor 完成后只留下 Git/artifact evidence，
不需要把 conversation state传给下一轮。

```text
Tier 0  role、authority、Active Step、允许/禁止事项
Tier 1  当前任务所需的完整 Static/Runtime 原始字节与 hash
Tier 2  commit、artifact、test 和 evidence manifest
Tier 3  按需读取的 repository 文件、历史 evidence 和日志
```

可扩展形态是让 Reviewer/orchestrator 按任务选择不同 provider、模型和工具能力的 fresh worker：
local coding、cloud coding、test、vision 或 GUI worker。每个 worker 出生时获得机械编译的充分
authoritative context，REJECT 后可以替换 Executor，而不丢失合同、当前状态或验收历史。

当前只有一个固定、顺序运行的 Executor。未来 worker pool 仍应先保持 single writer：同一时刻
只允许一个 mutation worker 操作一个 target。并行写入需要额外的 worktree/branch、commit
attribution、冲突合并和 Runtime consistency 设计，不能从现有能力直接推断。

### 能力边界

| 能力 | 已实现 | 尚待扩展或验证 |
| --- | --- | --- |
| Role/model separation | 独立 Reviewer/Executor profile、session 和可不同模型配置 | 本地/云端 mixed-provider 的正式配置与 evidence |
| Contract-backed context | Static/Runtime/Git/evidence、hash/freshness、fresh reconstruction | 将同一 contract 封装为通用 provider adapter |
| Fresh worker | fresh bounded Executor，不依赖旧 Executor history | 多个可替换、按能力选择的 worker |
| Tool reuse | Codex CLI shell、文件、Git 和现有工具调用 | image、vision、browser、MCP、Computer Use 的治理接入 |
| Final authority | 一个 Reviewer 独立检查 evidence 并形成 verdict | Reviewer backend 可替换但仍保持唯一最终 authority |
| Mutation concurrency | single writer | 并行写入尚未设计或验证 |

当前可运行行为和命令以 [`1PCloop/README.zh-CN.md`](1PCloop/README.zh-CN.md) 为准。表中“尚待扩展”不是
当前已交付能力，但它建立在已经实现的治理核心之上。

## 核心概念

### Static：稳定合同

Static 记录跨会话仍然有效的内容：最终目标、硬约束、授权范围、禁止事项和验收标准。它不记录
当前做到了哪一步，也不能由普通 Executor 自行修改。

### Runtime：当前权威状态

Runtime 记录已经验收的结果、唯一 Active Step、当前 blocker、待处理项、Human decision 和
evidence locator。它回答“现在什么仍然有效、下一步是什么”，而不是复制聊天或 Git log。

### Git、artifact 与 evidence

Executor 的自然语言汇报只是索引。Reviewer 必须直接检查 commit、diff、测试输出、文件 hash
或其他实际 evidence，才能形成最终 verdict。

### External context

长期上下文保存在 Static、Runtime、Git 和 artifact 中，而不是绑定在某个 Codex conversation。
Reviewer 会获得完整、带 hash 的治理上下文；Executor 只获得完成当前步骤所需的 bounded
instruction。旧 conversation 可以丢弃，任务仍可从 repository state 重建。

## 为什么采用两个角色

Executor 专注于实现，Reviewer 专注于检查目标、diff、测试和证据。两者使用独立 identity、
独立 session/history 和不同职责提示，降低同一执行上下文对复核判断的影响。

实践中建议：

- Reviewer 的模型能力和推理强度不低于 Executor；
- 高风险或复杂任务可以让 Reviewer 使用更强模型；
- Reviewer 与 Executor 可以使用同型号或不同型号模型，角色边界不依赖模型名称；
- 更强 Reviewer 不能替代测试、hash、Git identity 和 Human Gate 等机械约束。

这种设计提高的是自我复核的独立性和可追溯性，不保证模型永远正确，也不是模型投票系统。

## 基本使用流程

1. 为任务建立一对 task-local Static/Runtime。
2. 准备独立、干净、位于正确分支的 target Git repository。
3. 运行 preflight，固定 target、governance、profile 和 evidence destination。
4. 启动 loop；orchestrator 自动调用 Reviewer 和 Executor。
5. 在终端观察进度、Human Gate 或最终结果。
6. 通过 Runtime、checkpoint、tracked summary 和 Git commit 恢复或审核结果。

完整安装、命令、文件格式、恢复方式和安全边界见
[`1PCloop/README.zh-CN.md`](1PCloop/README.zh-CN.md)。

## 已具备的能力

- 双 Codex identity 的显式角色绑定；
- Reviewer → Executor → Reviewer 自动路由；
- 完整治理上下文注入与 freshness 检查；
- bounded Executor context；
- 真实 repository mutation、测试和普通 Git commit；
- runtime-enforced structured verdict；
- 独立 evidence validation；
- ACCEPT 后的 capability-gated Runtime transition；
- REJECT 后的 bounded repair routing；
- Human Gate 自动停止和提示；
- checkpoint、crash/restart reconciliation 和幂等恢复；
- Git-ignored raw evidence、tracked summary、framework evidence commit/push；
- Reviewer verdict 的有限同线程纠错；
- logical outcome、Runtime transition 与 evidence publication 的独立结果显示。

## 当前边界

1PCloop 当前面向单 Human contributor、单 active loop、单 target writer 的本地工程使用。它不是
操作系统级安全沙箱，也不提供多 writer、并行 Executor、repository locking 或分布式一致性。
Target repository 不会被 orchestrator 自动 push 或 merge；无法解释的状态会 fail closed 或进入
Human Gate，而不是自动 reset、force push 或猜测性修复。

## Repository layout

```text
1PCloop/                 active 单机实现、文档、测试与 evidence
2PCloop/                 暂停的双机设计归档
```

`2PCloop` 只保存早期双机器构想，便于未来在 Human Owner 明确重启时参考。当前 issue、提交和功能
请求都应以 `1PCloop` 为目标，不应从 `2PCloop` 文档推断现行能力或路线。
