# Whisper 会话与复制体验 v1 -- Runtime 当前权威状态

## 1. Current Status

- Task ID: `whisper_session_ui_v1`
- 状态: `ACCEPTED / TASK CLOSED WITH FOLLOW-UP UI DEFECT`
- 当前 verdict: `S2 INDEPENDENTLY ACCEPTED / HUMAN BLACK-BOX PASS`
- 唯一 Active Step: 无。S1、S2 和 Human Owner 真实功能黑盒均已完成。
- Step 1: `ACCEPTED / TARGET MAIN PUSHED`
- 最近 Pending 截止: 无
- Static identity: `1PCloop/workloads/whisper_session_ui_v1/workload_static.md`；SHA-256 `a361cf58b123db786505e12daec1673b39be5b1114d49b62d7b5779fffcc6d08`
- 当前证据快照: Step 1 target/framework evidence 已发布；Step 2 target commit `cb4261825b7d51d3ec33a97e083683c50e6b9e82` 已由 1PCloop Reviewer ACCEPT，framework evidence 和 target branch 均已推送；Human Owner 报告本轮功能实现无问题。
- 最后更新: 2026-09-18

## 2. Completed

- 治理启动: Human Owner 授权创建功能分支和中文 Static/Runtime，并明确仓库整理及 UI 实现应由 1PCloop 执行。本项不是 Step 1 的实现或验收。
- 分支准备: `codex/session-clipboard-ui-v1` 从 `multiLanguage_v1` 的 `1e0cdd9fda1870a8277a553c3f7af7cc67480fe9` 创建；没有 UI 代码提交。原 streaming branch 保持不变。
- Step 1 -- streaming 文档整理: target commit `d0f581bb70379239c3147e5c8469d2285ad6620b` 将三份固定来源文档逐字节归档到 `main`，增加归档 landing page 与准确导航，不包含代码实现。1PCloop Reviewer `ACCEPT`，machine transition ID `4030e8b7620a7debfe04484394ef7a7923a8d6128ee97a388fda52bdd6b0d41f`；framework evidence commit `19b1fa49649d556dd88cf4766d541af4ab15dd23` 已推送。Human-facing independent review 复核三个 source blob/SHA、27/27 链接、7-file allowlist、边界文案和 commit ancestry 后 ACCEPT；target `main` 已普通 non-force push，local/origin/GitHub ref 均为 `d0f581b...`。
- Step 2 -- 会话 UI 与剪切板改进: target commit `cb4261825b7d51d3ec33a97e083683c50e6b9e82` 是授权 baseline `1e0cdd9fda1870a8277a553c3f7af7cc67480fe9` 的唯一直接后继。实现 Clean TXT 绝对路径复制、新会话成功后清屏和旧事件隔离、按成功复制断点复制新增 Clean 文本，以及中文 `语言/Language` label。Executor 报告 focused 9/9、full discovery 117/117 和 UI support 22/22；同一 persistent Reviewer 独立复跑 focused/related 20/20、full discovery 117/117 和 UI support 22/22 后给出 `ACCEPT`。机器 transition ID 为 `b8e789c2331be4c34ffa1a2f18fa035206de32110e86cf732a1aa249fdcee2a5`，framework evidence commit `46461ad0073bdaae8ef32815a31778857fd35933` 已推送。Human-facing final review 另跑 focused UI/language 15/15，核对 branch ancestry、clean worktree、status/inspect PASS 后 ACCEPT；target feature branch 已普通 non-force push，local/origin/GitHub ref 均为 `cb42618...`。
- Human black-box closure: 2026-09-18 Human Owner 在真实 App 使用中确认本轮功能实现无问题，因此 Static 中 `TO_CONFIRM` 的真实功能黑盒项关闭为 `PASS`。同一次测试发现窗口纵向内容过长并超出可用窗口范围；该问题不否定 S2 的四项功能 verdict，作为独立 follow-up UI layout defect 保留。
- Target-side documentation handoff: target commit `fb7e38e4248b1b6fcf58a14193dbfe9315f90f34` 在功能分支新增 `docs/change_records/session_clipboard_ui_v1.md` 与索引，并同步 `docs/repo_map.md`。该 compact record 保存产品行为、架构边界、测试结论、Human black-box verdict、已知 layout defect 和跨仓库 commit/run/hash；完整 Static/Runtime/raw evidence 继续以本 framework 仓库为过程权威，不在目标仓库复制第二份可变 Runtime。

## 3. Completed Step Definition

### Step 2 -- 多语言版本上的会话 UI 与剪切板改进

- Objective: 在 `multiLanguage_v1` 派生分支实现 Clean 路径复制、新会话清屏、按断点复制新增 Clean 文本，以及中文 `语言/Language` label；保持历史转录文件和既有多语言/转录行为。
- Inputs: target `/Users/smterpro/Workspace/whisper/live_subtitle_generator-session-ui`，branch `codex/session-clipboard-ui-v1`，baseline `1e0cdd9fda1870a8277a553c3f7af7cc67480fe9`；现有 PySide6 UI、controller/session event 与 `testCodes` 回归。
- Permitted changes: 与按钮、Qt clipboard、Clean/Raw 表格会话重置、迟到 event 隔离、计数/复制断点、双语 label 直接相关的 UI/controller 代码和自动测试；必要的中英文使用说明；普通 descendant commit。
- Prohibited changes: 本 Static/Runtime、framework 治理、streaming backend、Whisper runtime/model pin、转录/语言识别算法、原 streaming branch、target push/merge/tag/release/force，以及删除或改写历史 session 文件。
- Required evidence: 完整 target commit/diff/changed-file list；Qt offscreen 或等价模拟测试覆盖路径剪切板、新会话成功/失败、Stop 保留、迟到旧 event、首次/增量/空切片/新会话断点、Unicode 和中英文 retranslate；相关及完整可运行 regression 输出的绝对 locator；branch ancestry 和 clean status。
- Acceptance criteria: Static AC-02 至 AC-07。Reviewer 必须白盒检查 event/session ownership、clipboard 数据源和断点语义，不能把模拟测试表述成真实音频黑盒。
- Executor self-check: targeted UI tests、现有相关 tests、完整可运行 unittest discovery、Python compilation/import、`git diff --check`、changed-path/protected-path 检查；记录不能运行的检查及原因。
- Stop conditions / Human Gate: 必须改 Static/Runtime 或 streaming backend、需要真实用户音频/凭据、无法安全区分旧/新 session、需要 merge/release/tag、分支/HEAD/工作树不符。
- Executor report: 结果、逐文件设计和行为、测试命令/数量/耗时/绝对输出 locator、commit/parent/branch/clean status、已知限制；不得自行 ACCEPT 或宣称真实音频黑盒通过。
- 完成后停止于: `AWAITING_REVIEW`。

## 4. Independent Review

| 验收条件 | 直接 evidence | 充分性判断 | 结果 |
| --- | --- | --- | --- |
| AC-02 至 AC-07 -- UI 实现与回归 | target commit `cb4261825b7d51d3ec33a97e083683c50e6b9e82`；run `20260918T125410Z-30917`；framework summary `1PCloop/evidence-summaries/20260918T125410Z-30917.md`；自动回归及 Human-facing focused 15/15 | 足以验收代码逻辑和模拟/offscreen UI 行为；不包含真实音频黑盒 | ACCEPT |

- 独立 evidence access: `PASS -- raw evidence available，status/inspect 均 PASS，target evidence VALID`
- 独立 verdict formation: `PASS -- Reviewer 直接检查 commit、代码、测试与 branch 状态，并独立复跑测试`
- 独立 evidence-sufficiency judgment: `PASS FOR WHITE-BOX AND SIMULATED UI SCOPE`
- Review verdict: `ACCEPT S2`
- Human black-box verdict: `PASS -- Human Owner reported the implemented functions work correctly`
- Review limitations: 窗口高度和滚动可达性不在原 S2 四项功能合同内；实测发现该布局问题，必须在后续独立任务中处理。

## 5. State Transition

- Previous state: `Step 2 ACTIVE / reviewer_accept_once`。
- Triggering evidence and Human decision: Reviewer 对 target commit `cb42618...` 给出 schema-valid `ACCEPT`，Runtime transition 和 framework evidence publication 均成功；Human-facing final review 通过并依 standing authorization 推送 target feature branch。
- Current state: `S2 COMPLETED / transition disabled / HUMAN BLACK-BOX PASS / TASK CLOSED`。
- Meaning: 自动实现、白盒/模拟测试及 Human 功能黑盒均已关闭；新发现的窗口高度问题不得通过重开或改写 S2 处理。
- Transition authorized by: S2 machine capability gate、独立 Reviewer verdict 和 Human Owner 的预授权 push 规则。

## 6. Blockers and Human Decision Gates

- 当前 blocker: 无；本任务已关闭。
- Human Gate: merge、release、tag、force、改 streaming backend 或扩大范围仍须另行授权。窗口高度和滚动改进需要新的 task-local Static/Runtime，不在本任务追加实现。

## 7. Residual Validation Items

- 真实 macOS 功能黑盒: `PASS -- Human Owner confirmed the implemented functions work correctly`。
- 新 follow-up defect: App 窗口纵向内容过长，超出可用窗口范围。建议下一独立任务限定窗口高度，并在合适的内容区域增加滚轮滚动，同时保持主要转录视图和操作控件可达。

## 8. Pending Tasks -- Non-blocking Blocks

- 当前顶层 Step: 无 active machine step；任务已关闭。
- 无需以倒计时管理的非阻塞 block。
- Pending Gate Check: 无。窗口布局缺陷转交下一独立 workload，不作为本任务 pending。

## 9. Superseded Decisions

- 无。前一轮未提交的手工准备已撤回，不属于本任务的实现或验收 evidence。

## 10. Next Direction

- 不再启动新的 S2 run。后继 `whisper_window_layout_v1` 已以 target-side documentation commit `fb7e38e4248b1b6fcf58a14193dbfe9315f90f34` 为 baseline 独立初始化；其 Static/Runtime 位于 `1PCloop/workloads/whisper_window_layout_v1/`。本 closed task 只作为历史和产品语义输入，不再承担后续 Active Step。

## 11. Follow-up Handoff

- 后继任务: `whisper_window_layout_v1` -- 主窗口高度约束与垂直滚动可达性。
- 需要先确定: 目标可用屏幕高度/缩放条件、哪些控制区固定可见、哪个容器负责滚动、滚轮/触控板/键盘行为，以及 transcript tables 自身滚动与外层滚动如何避免冲突。
- 明确边界: 不修改 streaming backend、Whisper runtime、模型/语言算法、session ownership 或 clipboard 断点语义；不得将简单缩小字体当作唯一解决方案。

## Machine-owned State

<!-- 1PCLOOP_RUNTIME_STATE_BEGIN -->
{
  "active_step": {
    "id": "S2",
    "status": "COMPLETED"
  },
  "last_transition_id": "b8e789c2331be4c34ffa1a2f18fa035206de32110e86cf732a1aa249fdcee2a5",
  "schema_version": 1,
  "transition_mode": "disabled",
  "workload_id": "whisper_session_ui_v1"
}
<!-- 1PCLOOP_RUNTIME_STATE_END -->

该机器块只授权当前 S2 的一次 ACCEPT -> COMPLETED。下方 S1 transition record 保持历史原文；S2 不得改写、删除或把它重新解释为 UI acceptance。


<!-- 1PCLOOP_RUNTIME_TRANSITION_RECORD -->
```json
{
  "accepted_preimage_sha256": "9178ecd5b128c54c7da914ac29dbedc039980c6f9597b26e5764f4a10feb7e7a",
  "evidence": [
    {
      "kind": "commit",
      "locator": "d0f581bb70379239c3147e5c8469d2285ad6620b",
      "sha256": "af6accc5520f82e526b7ae2812f624112dff13ec3d62fdac4efae396c3012372"
    },
    {
      "kind": "file",
      "locator": "/Users/smterpro/Workspace/whisper/live_subtitle_generator-main-docs/docs/streaming_backend_upgrade/README.md",
      "sha256": "8c49658866eca0cee0460e9162486542e2543c4b27f62197adb976eaeff5f245"
    },
    {
      "kind": "file",
      "locator": "/Users/smterpro/Workspace/whisper/live_subtitle_generator-main-docs/docs/streaming_backend_upgrade/static.md",
      "sha256": "fa7ad06ff04d039dc0c76da11d647ccff537000d6ef3aa24fad64a791a80aa05"
    },
    {
      "kind": "file",
      "locator": "/Users/smterpro/Workspace/whisper/live_subtitle_generator-main-docs/docs/streaming_backend_upgrade/runtime.md",
      "sha256": "9354f271f905c895f9e477264bee19a9c47f18c82bc9ab417a815f3cf5c060b5"
    },
    {
      "kind": "file",
      "locator": "/Users/smterpro/Workspace/whisper/live_subtitle_generator-main-docs/docs/streaming_backend_upgrade/update_plan.md",
      "sha256": "ae4566dd27dca2ba96d5beedd8d35ab490a46e51188fa82cbd05eef4d7917c40"
    },
    {
      "kind": "file",
      "locator": "/Users/smterpro/Workspace/whisper/live_subtitle_generator-main-docs/README.md",
      "sha256": "ef2953b61c2942fa7767e96c9f7afe289d2abbb09ec004cdc249bb2826958492"
    },
    {
      "kind": "file",
      "locator": "/Users/smterpro/Workspace/whisper/live_subtitle_generator-main-docs/README.zh-CN.md",
      "sha256": "6e6f003f78b5b0a0e51c8306c520c298728b74ecfea1b2116797c25cc717452c"
    },
    {
      "kind": "file",
      "locator": "/Users/smterpro/Workspace/whisper/live_subtitle_generator-main-docs/docs/repo_map.md",
      "sha256": "40d215d5138a70bc566cb827d86c654264fef08253b5e14d6222ae8be8651474"
    }
  ],
  "new_state": {
    "active_step": {
      "id": "S1",
      "status": "COMPLETED"
    },
    "last_transition_id": "4030e8b7620a7debfe04484394ef7a7923a8d6128ee97a388fda52bdd6b0d41f",
    "schema_version": 1,
    "transition_mode": "disabled",
    "workload_id": "whisper_session_ui_v1"
  },
  "old_state": {
    "active_step": {
      "id": "S1",
      "status": "ACTIVE"
    },
    "last_transition_id": null,
    "schema_version": 1,
    "transition_mode": "reviewer_accept_once",
    "workload_id": "whisper_session_ui_v1"
  },
  "reviewer_verdict_locator": "/Users/smterpro/Workspace/framework-loop/1PCloop/.local/runs/20260918T123000Z-29001/cycle-01/reviewer-review/final.txt",
  "reviewer_verdict_sha256": "272f4650d4ddcb365a70ab67e290810df655ed1191debb17d41732a6b4d6a622",
  "schema_version": 1,
  "target_head": "d0f581bb70379239c3147e5c8469d2285ad6620b",
  "timestamp": "2026-09-18T12:37:41.143+00:00",
  "transition_id": "4030e8b7620a7debfe04484394ef7a7923a8d6128ee97a388fda52bdd6b0d41f"
}
```


<!-- 1PCLOOP_RUNTIME_TRANSITION_RECORD -->
```json
{
  "accepted_preimage_sha256": "3e1bae436c41eaee9b081d9e45121dae87d9ebf0cc878e3fb165d9aa34555579",
  "evidence": [
    {
      "kind": "commit",
      "locator": "cb4261825b7d51d3ec33a97e083683c50e6b9e82",
      "sha256": "fe122dd6132b2eaecc8634654c3a22363ed1e4cf9570ac2b3f3e967df3a6e4f5"
    },
    {
      "kind": "file",
      "locator": "/Users/smterpro/Workspace/whisper/live_subtitle_generator-session-ui/ui_app.py",
      "sha256": "2f148857e38583e5372165c72d217566c65c69b72805f6821df6578b13ef75b0"
    },
    {
      "kind": "file",
      "locator": "/Users/smterpro/Workspace/whisper/live_subtitle_generator-session-ui/transcription_controller.py",
      "sha256": "3221797e4a767f6a4f4d43a4b793f0c210cae32c7d73728db68a4b0e062c88df"
    },
    {
      "kind": "file",
      "locator": "/Users/smterpro/Workspace/whisper/live_subtitle_generator-session-ui/testCodes/test_session_clipboard_ui.py",
      "sha256": "7eb1e47edbd47ec8ea91f774b1b2802bf3001f95f050289cf4d988bcce72dfc0"
    },
    {
      "kind": "artifact",
      "locator": "/Users/smterpro/Workspace/framework-loop/1PCloop/.local/runs/20260918T125410Z-30917/cycle-01/executor/events.jsonl",
      "sha256": "81dab58b9dd2e8f4f4bba2f958c1c88d285f370e7af068174963e26c6959c64d"
    },
    {
      "kind": "artifact",
      "locator": "/Users/smterpro/Workspace/framework-loop/1PCloop/.local/runs/20260918T125410Z-30917/cycle-01/executor/process.json",
      "sha256": "05e43c03f1fa54d91cfb5d8b4040d86a034f738e8727433382ec458fd425f537"
    }
  ],
  "new_state": {
    "active_step": {
      "id": "S2",
      "status": "COMPLETED"
    },
    "last_transition_id": "b8e789c2331be4c34ffa1a2f18fa035206de32110e86cf732a1aa249fdcee2a5",
    "schema_version": 1,
    "transition_mode": "disabled",
    "workload_id": "whisper_session_ui_v1"
  },
  "old_state": {
    "active_step": {
      "id": "S2",
      "status": "ACTIVE"
    },
    "last_transition_id": null,
    "schema_version": 1,
    "transition_mode": "reviewer_accept_once",
    "workload_id": "whisper_session_ui_v1"
  },
  "reviewer_verdict_locator": "/Users/smterpro/Workspace/framework-loop/1PCloop/.local/runs/20260918T125410Z-30917/cycle-01/reviewer-review/final.txt",
  "reviewer_verdict_sha256": "0c448e1074fe90f42b28e519c29ea7b716ed4fb8367848e36a7fa8549695e9a4",
  "schema_version": 1,
  "target_head": "cb4261825b7d51d3ec33a97e083683c50e6b9e82",
  "timestamp": "2026-09-18T13:10:17.955+00:00",
  "transition_id": "b8e789c2331be4c34ffa1a2f18fa035206de32110e86cf732a1aa249fdcee2a5"
}
```
