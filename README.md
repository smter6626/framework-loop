# Framework Loop

Framework Loop 是一个以 repository-backed governance 驱动的 Reviewer–Executor 自动化系统。
当前唯一主线是 **1PCloop**：在一台 Mac 上使用两个隔离的 Codex identity，自动完成任务编译、
代码执行、独立复核、修复循环、Human Gate 和可审计状态推进。

> **项目状态**
>
> - [`1PCloop/`](1PCloop/)：唯一 active implementation 和维护主线。
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
[`1PCloop/README.md`](1PCloop/README.md)。

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
