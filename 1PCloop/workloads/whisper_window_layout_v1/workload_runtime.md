# Whisper 主窗口高度与滚动 v1 -- Runtime 当前权威状态

## 1. Current Status

- Task ID: `whisper_window_layout_v1`
- 状态: `ACTIVE`
- 当前 verdict: `NOT EVALUATED`
- 唯一 Active Step: `L1 -- 限定主窗口高度并建立明确滚动边界`
- 最近 Pending 截止: 无
- Static identity: `1PCloop/workloads/whisper_window_layout_v1/workload_static.md`; SHA-256 `916a44790e67af5f3023d5b36e52fd14097b45348d50e857c9fa56abd753521b`
- Target identity: `/Users/smterpro/Workspace/whisper/live_subtitle_generator-session-ui`; branch `codex/bounded-scrollable-main-window-v1`; baseline `fb7e38e4248b1b6fcf58a14193dbfe9315f90f34`
- 当前 evidence snapshot: 前序 `whisper_session_ui_v1` 已关闭并有人类功能黑盒 PASS；Human Owner 同次测试确认主窗口过高；target branch 仍精确位于 `fb7e38e...` 且 clean；首次 L1 run 在 Reviewer 启动认证阶段 fail closed，尚无 layout 实现 commit
- 最后更新: 2026-09-24

## 2. Completed

- Previous workload freeze: `whisper_session_ui_v1` 已在 framework commit `efb7e1fd04a60b406c2fd7b59957c1797dcd990e` 记录 Human 功能黑盒 PASS 和独立 layout defect，后续不修改旧 Static/Runtime 来实现本任务。
- Target-side provenance: target commit `fb7e38e4248b1b6fcf58a14193dbfe9315f90f34` 增加 `docs/change_records/session_clipboard_ui_v1.md` 与 repo map 更新，是本任务固定 baseline。
- Branch preparation: `codex/bounded-scrollable-main-window-v1` 已从 `fb7e38e...` 创建。为避免重复安装约 3 GB 本地依赖，现有 `/Users/smterpro/Workspace/whisper/live_subtitle_generator-session-ui` worktree 已切换到该 branch，并复用 Git-ignored `.venv`、`.tools` 和 `external/whisper.cpp`；tracked worktree 保持 clean。
- Governance initialization: Human Owner 明确授权准备下一轮窗口高度修复及中文 Static/Runtime。本 task 与旧 S2 分离，只有 L1 一个顶层 Step。
- Operator readiness: framework commit `029f4484cb51cc2afe73f0a6e29a0ee5facc0701` 上运行 `window_layout.json` 的 doctor 8/8 PASS、preflight PASS。Config raw SHA-256 为 `3ff05a6d78d88aafe4516ea69e4bb369a9c2b68c69fd02c122b3bceb5488e745`，resolved SHA-256 为 `95527396a4e4eaa4bd00ee39583c4ff74733daeb7be1072b4d07de6c752c9019`；target clean 且精确位于 `fb7e38e...`，framework local/origin main 同步。该检查没有调用 Agent 或修改 target。
- Failed auth run: run `20260924T220337Z-47406` 在首次 Reviewer turn 因错误的 OAuth-token-to-`CODEX_ACCESS_TOKEN` transport 返回 401 并 fail closed。三层结果为 `FAILED_CLOSED / NOT_APPLIED / PUSHED`；framework evidence commit 为 `0da9c5fa4e384beda6e908a4028846f3acda7429`。该 run、checkpoint、raw/tracked evidence 永久保留，不能 resume、删除或改写。
- Human-authorized repair: 允许在 switch lock + role lock + 持久事务内临时投影完整 active `auth.json`，并在 turn 后恢复 role 原 bytes/mode。账号 identity 必须固定，A/B 快照必须不变，credential scan 必须为零。修复通过专项、完整回归和双 role real smoke 后，使用新的 retry config/run ID 明确记录 `retry_of=20260924T220337Z-47406` 与 `retry_reason=codex_mix_file_credential_projection_fix`。
- Auth repair validation: framework commit `8a055a38282e17e678324400ca01721568c43f30` 已普通 push。认证事务专项 14/14、完整 ResourceWarning-strict 回归 222/222 PASS；Reviewer fresh、同线程 resume、Executor ephemeral 三次真实 service smoke 均返回 `auth-ok`，无 401，role auth bytes/mode 已恢复，actual credential hit 为 0，A/B snapshot 和 active identity 不变。compact evidence: `1PCloop/evidence-summaries/codex-mix-auth-projection-repair-20260924.md`。
- Retry readiness: `window_layout_retry_01.json` raw SHA-256 `88506a4f6f5b8208cede4c7785cab856e1488a27f5fc4211206f41bfd14f3dfe`，canonical resolved SHA-256 `66162d42571ecf8085dc2385944ac4d665a2d80766d7abfcdaeae11edcfe1283`。post-push doctor 9/9、preflight PASS；target 仍 clean 且位于 `fb7e38e...`。retry 使用独立 state root，不改写旧失败 checkpoint。

## 3. Active Step

### L1 -- 限定主窗口高度并建立明确滚动边界

- Objective: 让主窗口在多个可注入 macOS available geometry 下首次显示和 resize 后不超出可用高度，并让所有 controls 可经清晰的滚动/键盘路径访问，同时保持 transcript tabs 自身滚动和已验收功能。
- Inputs 及固定 identity: 本 Static 和 Runtime；target `fb7e38e...`；`ui_app.py` 当前 root/status/body/controls/tabs layout；`docs/change_records/session_clipboard_ui_v1.md`；现有 `testCodes/test_session_clipboard_ui.py`、`testCodes/test_ui_language.py`、UI/output/model tests。
- Permitted changes: `ui_app.py` 的 geometry/layout/size policy/scroll/focus 最小修改；相关 `testCodes/`；必要的 README、`docs/change_records/` 和 `docs/repo_map.md`；一个普通 descendant commit。
- Prohibited changes: Static/Runtime/framework governance；streaming/Whisper/model/ASR/dedup；controller/store/settings/session/clipboard 语义；历史 evidence；target push/merge/tag/release/force。
- Required evidence: 完整 target commit、parent、diff 和 changed-file list；多组 short/normal geometry 的窗口 bounds artifact；scroll range、首尾 control 可见、wheel/focus traversal、table scroll ownership、resize/retranslate evidence；S2 focused、相关 UI 和 full discovery 输出的绝对 locator 与 SHA-256；branch/clean status；target-side layout change record。
- Acceptance criteria: Static AC-01 至 AC-08。Reviewer 必须判断测试 seam 是否真实覆盖 show/minimum-size/scroll ownership，而不能只接受 widget 存在或 Executor 截图描述。
- Executor self-check: targeted layout tests；S2 clipboard/session regression；UI language/output/model related tests；完整可运行 unittest discovery；UI support checks；Python compile/import；`git diff --check`；changed/protected path；重复 resize/retranslate 无异常。
- Stop conditions / Human Gate: 需要隐藏/删除 controls、改变功能语义、改 controller/session/clipboard/backend、无法避免 screen hard-code、需要主观重设计、分支/HEAD/工作树漂移或需要 merge/release 时停止。
- Executor report format: 结果；选择的 scroll/geometry ownership 及理由；逐文件变更；geometry/scroll/focus 测试矩阵；完整命令、数量、耗时、绝对 locator/hash；commit/parent/branch/clean status；未验证的真实 macOS视觉/trackpad限制。不得自行 ACCEPT。
- 完成后停止于: `AWAITING_REVIEW`。

## 4. Independent Review

| Acceptance criterion | Direct evidence | Evidence sufficiency judgment | Result |
| --- | --- | --- | --- |
| AC-01 至 AC-08 | 尚无 layout 实现 commit | 尚不可判断 | INSUFFICIENT |

- 独立 evidence access: `NOT APPLICABLE -- 尚未执行 L1`
- 独立 verdict formation: `NOT APPLICABLE`
- 独立 evidence-sufficiency judgment: `NOT APPLICABLE`
- Review verdict: `NOT EVALUATED`
- Review limitations: 自动 Reviewer 可以验收代码、模拟 geometry、event routing 和回归；真实 macOS视觉边界和 trackpad 手感仍由 Human Owner最终确认。

## 5. State Transition

- Previous state: 前序 external workload `whisper_session_ui_v1` `ACCEPTED / TASK CLOSED WITH FOLLOW-UP UI DEFECT`。
- Triggering evidence 或 Human decision: 2026-09-18 Human Owner 确认功能实现无问题，但 UI 太长并直接超出窗口限制，明确指定下一项 1PCloop 任务为限定窗口高度并增加适当滚动。
- Current state: `ACTIVE / L1`。
- Meaning: 只授权实现和验证窗口 geometry/scroll accessibility；不重开 S2，不授权目标集成或发布。
- Transition authorized by: Human Owner。

## 6. Blockers and Human Decision Gates

- 当前 blocker: 无。认证事务修复和 retry doctor/preflight 已验证；下一动作是启动新的 L1 retry run。
- Human Gate: Static 变化、隐藏/删除 controls、范围扩大到功能语义、主观视觉重设计、target merge/release/tag/force 或无法通过 deterministic UI evidence 判定时暂停。

## 7. Residual Validation Items

- 自动 L1 ACCEPT 后仍需 Human Owner 在真实 macOS App 上确认：初始窗口完全处于可用屏幕内；较小高度下可以用鼠标/触控板访问底部 controls；Clean/Raw/Logs 滚动自然；中英文切换和 S2 功能无视觉回归。
- 本地 bootstrap 依赖约 3 GB，当前为下一轮实现和人工测试保留；任务最终关闭后再单独决定清理，不属于 L1 acceptance。

## 8. Pending Tasks -- Non-blocking Blocks

- 当前顶层 Step: `1`，映射为 `L1`。
- 当前没有需要倒计时管理的 non-blocking block。
- Pending Gate Check: `CLEAR`。

## 9. Superseded Decisions

- 无。旧 S2 verdict 保持有效；本任务只承接其明确记录的 layout follow-up。

## 10. Next Direction

- 完成认证事务修复、双 role real smoke 和新 retry config 的 doctor/preflight 后，启动新的 config-bound retry run；不得 resume 失败 run。
- 若自动 Reviewer ACCEPT，仅关闭代码/模拟 UI gate并由 Human-facing reviewer普通 push target branch；随后提供真实 macOS人工 checklist。若 REJECT，沿同一 L1 repair cycle处理，不扩大合同。

## 11. Current Executor Handoff

- 本轮唯一任务: 实现并测试 Static 定义的主窗口高度约束和滚动可达性。
- 必须读取: 本 Static/Runtime；`ui_app.py` root/controls/tabs/retranslate/resize 相关代码；S2 change record；现有 session clipboard、UI language、output/model tests；双语 README 和 repo map。
- 可以修改: L1 permitted changes 内的 target UI、tests 和必要文档。
- 不得修改: 本 Static/Runtime、framework、backend/model/ASR、controller/store/settings/session/clipboard 语义、历史 evidence 或 closed workload。
- 必须返回的 evidence locator: target commit/parent/diff；geometry/scroll/focus artifacts；targeted/related/full test logs及 SHA；changed-path/protected-path；branch/clean status和limitations。
- 完成后停止于: `AWAITING_REVIEW`。

## Machine-owned State

<!-- 1PCLOOP_RUNTIME_STATE_BEGIN -->
{
  "active_step": {
    "id": "L1",
    "status": "COMPLETED"
  },
  "last_transition_id": "e273ff320e67a1875dc2c5e2157db497411d315a04ee7e299df5924564e71c18",
  "schema_version": 1,
  "transition_mode": "disabled",
  "workload_id": "whisper_window_layout_v1"
}
<!-- 1PCLOOP_RUNTIME_STATE_END -->

该机器块只授权 L1 的一次 schema-valid Reviewer `ACCEPT -> COMPLETED` transition。它不授权自动关闭 Human 真实 macOS视觉 gate，也不授权 target push、merge、tag 或 release。


<!-- 1PCLOOP_RUNTIME_TRANSITION_RECORD -->
```json
{
  "accepted_preimage_sha256": "4cd9ef55c5b03ce0bad158de109a36f885824e0c4c76383777106ac19c68fb86",
  "evidence": [
    {
      "kind": "commit",
      "locator": "569e5c551c101811ed80fca23bd5708d6ac880cf",
      "sha256": "1a052b74aef9786569885121dfd68012d35e41a23aad12065c9ce64e2e5695c7"
    },
    {
      "kind": "file",
      "locator": "/Users/smterpro/Workspace/whisper/live_subtitle_generator-session-ui/ui_app.py",
      "sha256": "c80cfca171d547e25bd312e22177de95996cba4d8da83c00505b3c148cc680a3"
    },
    {
      "kind": "file",
      "locator": "/Users/smterpro/Workspace/whisper/live_subtitle_generator-session-ui/testCodes/test_window_layout.py",
      "sha256": "ee15a137d2fb2af77aa895246876c176c963562afa872c7029beddb41656a9c2"
    },
    {
      "kind": "file",
      "locator": "/Users/smterpro/Workspace/whisper/live_subtitle_generator-session-ui/docs/change_records/window_layout_v1.md",
      "sha256": "655ae0397ecf9cb899305554b0ac0e0f9d8ea8d73ef3f09463e001e11fdfded6"
    }
  ],
  "new_state": {
    "active_step": {
      "id": "L1",
      "status": "COMPLETED"
    },
    "last_transition_id": "e273ff320e67a1875dc2c5e2157db497411d315a04ee7e299df5924564e71c18",
    "schema_version": 1,
    "transition_mode": "disabled",
    "workload_id": "whisper_window_layout_v1"
  },
  "old_state": {
    "active_step": {
      "id": "L1",
      "status": "ACTIVE"
    },
    "last_transition_id": null,
    "schema_version": 1,
    "transition_mode": "reviewer_accept_once",
    "workload_id": "whisper_window_layout_v1"
  },
  "reviewer_verdict_locator": "/Users/smterpro/Workspace/framework-loop/1PCloop/.local/runs/20260924T225838Z-88499/cycle-01/reviewer-review/final.txt",
  "reviewer_verdict_sha256": "824dbb6faf42d00d7f7ea73939d9c0c11e887db9ab6a33e23544c24392310602",
  "schema_version": 1,
  "target_head": "569e5c551c101811ed80fca23bd5708d6ac880cf",
  "timestamp": "2026-09-24T23:15:31.401+00:00",
  "transition_id": "e273ff320e67a1875dc2c5e2157db497411d315a04ee7e299df5924564e71c18"
}
```
