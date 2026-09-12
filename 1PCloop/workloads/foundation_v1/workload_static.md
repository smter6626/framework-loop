# foundation_v1 — Static 稳定合同

## 1. 合同身份

- Task ID：`foundation_v1`
- 合同状态：`AUTHORIZED`
- Human Owner：1PCloop Human Owner
- 授权日期：`2026-09-12`
- 适用范围：P6 关闭后的 1PCloop engineering foundation
- 全局治理：`1PCloop/docs/miniloop_static.md` 与
  `1PCloop/docs/miniloop_runtime.md`

## 2. Objective

将 P6 后的 1PCloop 完善为可日常运行、可理解状态、可安全恢复、可维护的本地
Reviewer–Executor 工程工具。当前验收只依据工程行为和可定位 evidence；不要求建立论文
novelty、科学结论或研究实验结果。

## 3. Scope and Deliverables

本任务允许形成以下交付物。编号定义有序顶层阶段，但当前进度只记录在 task-local Runtime：

- F1：Reviewer verdict 机械纠错路径和明确终态输出；
- F2：run/stage timer、status 和 structured progress event；
- F3：简化 workload config，以及 doctor/preflight/run/resume/status/inspect CLI；
- F4：规范化默认中文 Static/Runtime Prompt 模板；
- F5：runner 模块化和 Human Gate UX；
- F6：本地 TUI；
- F7：完整 post-foundation real-service smoke；
- F8：依据使用 evidence 决定是否需要简单本地 GUI、治理压缩和进一步 evidence lifecycle
  功能。

### F4 Prompt 模板规范化范围

F4 可以在独立实现与验收步骤中创建：

```text
1PCloop/templates/static_prompt_zh.md
1PCloop/templates/runtime_prompt_zh.md
```

本合同初始化不创建模板副本。F4 使用以下只读固定输入：

```text
/Users/smterpro/Workspace/Tools/structured-llm-execution-framework/structured-llm-execution-framework_static.md
SHA-256: e3ff93b4136c0d3d87d7f1a319ca9c4513f831327daf18aea46f9f3d6659daf7

/Users/smterpro/Workspace/Tools/structured-llm-execution-framework/structured-llm-execution-framework_runtime.md
SHA-256: 3cbc4c93adff6ac2b1fb351a8a81f4b65dbd73b4de28ee2d0d4141522258ab54
```

规范化模板必须默认使用中文、保持可裁剪，并保留 Static/Runtime 职责分离、Single Active
Step、evidence-backed transition、Pending deadline、Human Gate、supersession 和
task-local freeze。不得把 Runtime progress 写进 Static，不得复制成不可维护的漂移版本；必须
记录来源路径与 hash，并经独立 Reviewer 验收。外部 Tools 文件不是 1PCloop 可修改对象。

### Out of scope

- P7 fault injection 或任何 defect injection；
- paper、novelty 论证或 research experiment；
- parallel Executor、multi-writer reconciliation、distributed deployment；
- production security boundary、production Web UI；
- Codex GUI automation、AppleScript 或键鼠模拟；
- 当前阶段的 self-hosting 实现。

## 4. Hard Constraints

1. 不弱化现有 fail-closed、evidence hash、role authority 或 Runtime transition capability gate。
2. Python 不从自然语言推断 verdict、evidence、控制状态或 UI 状态。
3. Executor 无权对自己的工作形成最终 `ACCEPT`，独立 Reviewer 必须直接检查 evidence。
4. UI/TUI/CLI 只能使用 structured control state，不得解析 peer_message 猜测状态。
5. 不记录、显示或提交 profile auth、credential、secret 或隐藏 reasoning。
6. 保持一个 Human contributor、一个 target 一个 active loop 的 single-writer/no-concurrency
   支持边界；不宣称 lock、watcher 或并发一致性。
7. 代码变更必须由独立 Reviewer 审核；Executor self-check 不构成最终 acceptance。
8. Static/Runtime 的实质性变化需要 Human Owner 授权；已完成 task 默认 task-local freeze。
9. 工程 acceptance 不以论文、novelty、研究启用门或研究结果为条件。
10. 已接受的 P4–P6 能力和历史 evidence 不得因本任务被追溯删除或降级。

## 5. Stable Background and Inputs

foundation_v1 继承以下已接受或已验证的工程基础，详细 evidence 以全局 Runtime 为准：

- P4 transport 与 deterministic context reconstruction 已接受；
- P5 mutation loop 和真实 workload control-plane 路径已验证；
- P6.1 checkpoint/restart/visible progress 已接受；
- P6.2 structured verdict 与 capability-gated Runtime transition 已接受；
- P6.3 evidence retention/finalization 已接受；
- P6.4 sequential lifecycle boundary 已接受；
- P6 已 `ACCEPTED / PHASE CLOSED`。

全局 evidence locator：`1PCloop/docs/miniloop_runtime.md`。

### 2026-09-12 post-P6 smoke 的稳定需求

- 机械 safety validation 按设计 fail closed；
- schema-valid Reviewer `ACCEPT` 仍可能携带机械不合法的 evidence locator；
- 可纠正的 Reviewer control-output 错误不应默认导致已经成功的 Executor mutation 再执行；
- logical outcome、Runtime transition 和 evidence publication state 必须在用户界面中明确区分。

Durable observation：
`1PCloop/evidence-summaries/post-p6-foundation-smoke-20260912.md`。

### Self-hosting 边界

foundation_v1 修改 `framework-loop` 自身，而现有 mutation runner 禁止 framework repo 与
target repo 重叠。因此当前 foundation 实现继续使用 Human-mediated Reviewer/Executor 流程，
不得声称 1PCloop 已自动修改并验收自身。该限制不是 F1 blocker，也不要求本阶段实现
self-hosting。

## 6. Authority and Approval

- Human Owner：批准 Static 变化、研究轨道重启、敏感或不可逆操作及 task 最终关闭。
- 独立 Reviewer：直接检查 acceptance evidence、形成 verdict，并在获授权时推进 Runtime。
- Executor：只实现当前 Runtime 编译出的唯一 Active Step，运行 self-check 并提供 locator；
  不得自我验收或推进治理状态。
- Human Gate：合同变化、无法机械解释的状态、敏感输入、self-hosting 权限变化、对外发布或
  不可逆操作。

## 7. Permitted and Prohibited Mutations

### 允许

- 当前 Active Step 明确列出的 implementation、tests、CLI/TUI、文档和本地 disposable fixture；
- Git-ignored 本地 raw evidence；
- 经 Reviewer 验收和 Human 授权的 task-local Runtime transition；
- F4 中独立创建并验收的 1PCloop 中文模板。

### 禁止

- 未授权修改全局或 task-local Static/Runtime；
- 修改外部 Tools 模板；
- 修改 closed workload 或外部 target 历史；
- 记录 secret、auth、隐藏 reasoning 或完整 raw payload 到 tracked summary；
- reset、history rewrite、force push 或猜测性状态修复；
- 在 P7 未重新激活时执行 fault injection；
- 把未实现的 F2–F8 功能描述成当前能力。

## 8. Acceptance Criteria

| ID | 验收条件 | 所需直接 evidence | 通过边界 |
| --- | --- | --- | --- |
| AC-01 | 可纠正的 Reviewer verdict 机械验证失败不重跑已完成 Executor | deterministic call-count、checkpoint、target HEAD 测试 | 同一 Executor mutation 只执行一次，纠错只触发 Reviewer |
| AC-02 | 终态同时呈现 logical outcome、Runtime transition、evidence publication | structured terminal/status fixture | 三类状态独立可读，不以 publication success 代替 logical success |
| AC-03 | status/resume 不要求手工重拼全部参数 | CLI integration test 与保存配置 | 可从 run/workload identity 恢复安全命令上下文 |
| AC-04 | terminal timer 显示 run elapsed、stage elapsed、timeout remaining、last activity | deterministic clock/event test | 四项在 active turn 中持续可见且不泄露 raw payload |
| AC-05 | structured progress event 可供 CLI/TUI 读取 | schema/consumer test | 控制字段稳定，UI 不解析自然语言 |
| AC-06 | 默认中文 Static/Runtime Prompt 模板完成规范化 | F4 commit、来源 hash、模板 review | 可裁剪、职责分离且经独立 Reviewer 接受 |
| AC-07 | Human Gate 可清晰检查和处理 | status/inspect/resume test | 原因、允许动作、恢复边界可定位且不自动破坏性修复 |
| AC-08 | runner 模块化不破坏行为 | module tests 与完整 P4–P6 regression | 既有 control/evidence/recovery invariant 保持通过 |
| AC-09 | TUI 不从自由文本决定状态 | TUI event-source test | 只消费 structured events/checkpoint state |
| AC-10 | post-foundation real-service smoke 完成合法 ACCEPT 闭环 | F7 raw/compact evidence、target/framework Git identity | ACCEPT、Runtime transition、summary commit/push 均完成且 target 不被 push |
| AC-11 | 现有 P4–P6 regression 保持通过 | declared Python environment 的 strict suite | 无新增 regression 或 ResourceWarning |

foundation_v1 只有在 AC-01–AC-11 均有充分 evidence 并由独立 Reviewer 验收后才能关闭。F8
中的 GUI、压缩或进一步 lifecycle 功能只有在被 evidence 选择为必要交付时才增加对应 criterion。

## 9. Evidence Boundary

- Reviewer 必须直接访问 commit/diff、测试输出、structured event、checkpoint/status、模板 hash
  或 real-service smoke artifact；Executor 自述只用于定位。
- Tracked evidence 保存 compact observation、固定 identity 和必要 hash；prompt、events、stderr、
  process/checkpoint 正文及 hidden reasoning 保持在 Git-ignored local evidence。
- Disposable `/tmp` locator 可能被系统清理；关键长期结论必须进入 tracked compact summary。
- Evidence publication success 与 logical task success 必须分别记录。
- 禁止为满足验收而公开 credential、private profile state 或无关个人数据。

## 10. Change Control

- Human Owner 可授权修订本 Static；Reviewer/Executor 不得自行扩大 F1–F8。
- 进度、当前 Active Step、verdict、blocker 和 pending countdown 只写 task-local Runtime。
- 已验收阶段冻结；新目标使用新 task-local Static/Runtime，除非 Human Owner 明确 reopen。
- Static/Runtime/evidence identity 冲突时停止并进入 Human Gate，不做猜测性合并。
- Prompt 模板、P7、self-hosting、GUI 或 concurrency scope 的启用均需对应 Runtime gate 和授权。

## 11. Open Decisions

- `TO_CONFIRM`：F8 根据 F1–F7 的使用 evidence 判断是否需要简单本地 GUI；当前未承诺实现。
- `TO_CONFIRM`：raw evidence 的长期清理/保留策略；当前为 non-blocking，不影响 F1。
- `TO_CONFIRM`：是否需要 self-hosting；当前不是 foundation_v1 acceptance 前置条件。
