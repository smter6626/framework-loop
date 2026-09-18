# Whisper 会话与复制体验 v1 -- Runtime 当前权威状态

## 1. Current Status

- Task ID: `whisper_session_ui_v1`
- 状态: `ACTIVE`
- 当前 verdict: `NOT EVALUATED`
- 唯一 Active Step: `Step 1 -- streaming 文档整理进 main`
- Step 2: `QUEUED / NOT ACTIVE`
- 最近 Pending 截止: 无
- Static identity: `1PCloop/workloads/whisper_session_ui_v1/workload_static.md`；SHA-256 `a361cf58b123db786505e12daec1673b39be5b1114d49b62d7b5779fffcc6d08`
- 当前证据快照: 来源 commit `73891f3a4b07e7d0f9fda3cc2cb1f35475727c84`，target main baseline `b5188ccc6aef591398fd8d31e162a29390b120e4`
- 最后更新: 2026-09-18

## 2. Completed

- 治理启动: Human Owner 授权创建功能分支和中文 Static/Runtime，并明确仓库整理及 UI 实现应由 1PCloop 执行。本项不是 Step 1 的实现或验收。
- 分支准备: `codex/session-clipboard-ui-v1` 从 `multiLanguage_v1` 的 `1e0cdd9fda1870a8277a553c3f7af7cc67480fe9` 创建；没有 UI 代码提交。原 streaming branch 保持不变。

## 3. Active Step

### Step 1 -- streaming 文档整理进 main

- Objective: 在 main 的合适位置集成来源 commit 的三份 streaming 治理/调查资料，建立准确导航和 provenance，不合并多语言或 streaming 代码。
- Inputs: `73891f3a4b07e7d0f9fda3cc2cb1f35475727c84` 的 `docs/streaming_backend_upgrade/{static.md,runtime.md,update_plan.md}`；locked plan SHA-256 `ae4566dd27dca2ba96d5beedd8d35ab490a46e51188fa82cbd05eef4d7917c40`；target `/Users/smterpro/Workspace/whisper/live_subtitle_generator-main-docs`，branch `main`。
- Permitted changes: 仅 main 的相关 `docs/`、README/repo map 中确有必要的导航与状态说明；由 1PCloop 选择具体文件位置。普通 descendant commit。
- Prohibited changes: 应用代码、测试、模型、打包、原 streaming branch、framework/workload Static/Runtime、locked plan 正文字节、target push/merge/tag/release/force。
- Required evidence: 完整 target commit SHA/diff、三个来源及目标文件的 blob/hash、locked plan SHA、链接检查、main clean status；说明“资料入 main”与“backend 已实施”的区别。
- Acceptance criteria: Static AC-01、分支和权限边界。Reviewer 必须直接核对内容和定位；Executor 的自述不够。
- Executor self-check: 比对来源与目标字节/hash；检查 Markdown 导航、`git diff --check`、changed-file allowlist 和 target clean；不运行无关音频测试。
- Stop conditions / Human Gate: 来源 identity 不符、必须改 locked plan 正文、需要整体 merge 代码或 scope 扩大、目标 branch 不符合预期。
- Executor report: 结果、逐文件变更、固定 commit/hash/locator、自检命令与结果、限制；不宣告最终 ACCEPT。
- 完成后停止于: `AWAITING_REVIEW`。

## 4. Independent Review

| 验收条件 | 直接 evidence | 充分性判断 | 结果 |
| --- | --- | --- | --- |
| AC-01 -- main 文档整理 | 尚无目标实现提交 | 尚不可判断 | INSUFFICIENT |

- 独立 evidence access: `NOT APPLICABLE -- 尚未执行 Step 1`
- 独立 verdict formation: `NOT APPLICABLE`
- 独立 evidence-sufficiency judgment: `NOT APPLICABLE`
- Review verdict: `NOT EVALUATED`
- Review limitations: 真实录音测试不是本步骤要求。

## 5. State Transition

- Previous state: foundation_v1 已关闭，无当前工程 task。
- Triggering Human decision: 2026-09-18，Human Owner 规定先由 1PCloop 整理 streaming 文档，再在多语言基础上改 UI；本对话只创建分支和治理初始文件。
- Current state: `ACTIVE / Step 1`。
- Meaning: 仅允许编译 Step 1 的 Reviewer/Executor 指令；Step 2 尚未激活。
- Transition authorized by: Human Owner。

## 6. Blockers and Human Decision Gates

- 当前 blocker: 无。
- Human Gate: 变更 Static/locked plan、扩大 target branch 范围、merge/release/tag/force、改 streaming backend 或需真实音频黑盒结论时暂停并请 Human 决定。

## 7. Residual Validation Items

- 真实 macOS 录音 -> Whisper 转录 -> Stop -> 再次 Start、路径粘贴与文本切片粘贴由 Human Owner 在自动 Step 2 ACCEPT 后进行。此项不妨碍 Reviewer 基于代码和模拟 UI 测试验收 Step 2，但最终产品黑盒结论不能提前宣告。

## 8. Pending Tasks -- Non-blocking Blocks

- 当前顶层 Step: `1`。
- 无需以倒计时管理的非阻塞 block。人工黑盒属于明确的最终 Human 验证门，见第 7 节，不因 Step 1 -> Step 2 迁移而消失。
- Pending Gate Check: Step 2 激活前必须确认 Step 1 Reviewer ACCEPT、Runtime transition、framework evidence publication、target main 普通 push 和双方 clean/ref identity；缺任一项则阻止激活。

## 9. Superseded Decisions

- 无。前一轮未提交的手工准备已撤回，不属于本任务的实现或验收 evidence。

## 10. Next Direction

- Step 1 独立 ACCEPT 后，由 orchestrator 只把当前机器 Step 标记 `COMPLETED` 并停止。核对 target/framework refs 后，本对话依据已授权范围单独激活 Step 2，用功能分支的独立 config/new run 执行 UI 改动。
- Step 2 自动 ACCEPT 后，只可报告代码逻辑/自动测试结论并普通 push 功能分支；真实录音黑盒仍待 Human Owner。

## 11. Current Executor Handoff

- 本轮唯一任务: 整理三份 streaming 文档进 main，位置由 1PCloop 决定。
- 必须读取: 本 Static/Runtime、来源 commit 的三个文件、target main 的 README/repo map 和 1PCloop 相关治理。
- 可以修改: main 中与三份文件集成直接相关的文档与必要导航。
- 不得修改: 应用代码、测试、streaming source branch、framework/workload 治理、locked plan 正文字节。
- 必须返回: 完整 target commit、changed-file list、来源/目标 hash、导航及 `git diff --check` 等 evidence locator。
- 完成后停止于: `AWAITING_REVIEW`。

## Machine-owned State

<!-- 1PCLOOP_RUNTIME_STATE_BEGIN -->
{
  "schema_version": 1,
  "workload_id": "whisper_session_ui_v1",
  "transition_mode": "reviewer_accept_once",
  "active_step": {
    "id": "S1",
    "status": "ACTIVE"
  },
  "last_transition_id": null
}
<!-- 1PCLOOP_RUNTIME_STATE_END -->

该机器块只授权当前 S1 的一次 ACCEPT -> COMPLETED，不会自动激活 S2。S2 启用前需在完整保存 S1 transition record 的前提下，将机器块切换为 `S2/ACTIVE`、`reviewer_accept_once`、`last_transition_id=null`，并单独提交/推送 Runtime；不可在 S1 run 未完成时改动。
