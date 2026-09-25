# Whisper Clean 重命名路径身份修复 v1 -- Runtime 当前状态

## 1. Current Status

- Task ID: `whisper_clean_rename_integrity_repair_v1`
- 状态: `HUMAN DECISION REQUIRED / R1 ACTIVE (NO TRANSITION)`
- 当前 verdict: `HUMAN_GATE`，首轮 Reviewer 未接受 R1，也未推进 Runtime
- 唯一 Active Step: `R1 -- 修复候选路径身份错误`
- Static identity: `1PCloop/workloads/whisper_clean_rename_integrity_repair_v1/workload_static.md`，SHA-256 `bc70ba55127ea3e5becfc33c9924948409d1247306610ee2948cbd7fee861bc4`
- Target: `/Users/smterpro/Workspace/whisper/live_subtitle_generator-session-ui`；当前拟使用 `codex/clean-toolbar-rename-v1`，固定修复基线 `352e62b2bf3cd3690e8eee57cb2e933f1405c6af`
- Blocker: Human Owner 必须裁定旧 AC-07 对外部任意移动文件的支持边界；在裁定前不启动新的修复 run、不推送 target 分支
- Pending Tasks: 无；原任务真实音频/macOS gate 仍未通过，不得在本修复中代替 Human 关闭

## 2. 必读交接与证据顺序

激活 R1、编译 Reviewer 首轮 instruction、进行 Executor 修复或独立复核之前，首先完整读取以下本地交接文档：

`/Users/smterpro/Workspace/framework-loop/1PCloop/.local/handoffs/whisper-clean-rename-review-pause-20260925.md`

预期 SHA-256: `1e6dc511b4f340351a68a86d8bbca24b1c1a96cbdf15fe3c1ed199d87ccc5f48`。该文件是 Git-ignored 本地恢复索引，不是 Static、Runtime 或授权来源。若文件缺失、hash 漂移或无法读取，不得凭当前对话记忆重建；停止启动，先由 Human 或治理准备者核实。读完后仍必须直接检查下列权威材料，不能只转述 handoff：

- 上游原合同: `/Users/smterpro/Workspace/framework-loop/1PCloop/workloads/whisper_clean_toolbar_rename_v1/workload_static.md`
- 上游 Runtime 和不可改写的机器块: `/Users/smterpro/Workspace/framework-loop/1PCloop/workloads/whisper_clean_toolbar_rename_v1/workload_runtime.md`
- 原成功 run raw: `/Users/smterpro/Workspace/framework-loop/1PCloop/.local/runs/20260925T061052Z-27529`
- 原 tracked summary: `/Users/smterpro/Workspace/framework-loop/1PCloop/evidence-summaries/20260925T061052Z-27529.md`
- Target 固定 commit/diff: `352e62b2bf3cd3690e8eee57cb2e933f1405c6af`；关键实现位于 `transcript_store.py`、`ui_app.py` 和 `testCodes/test_clean_rename.py`

以上文件内容若与实时 Git 状态冲突，先解决身份冲突；不得以 handoff 覆盖 Git、机器 Runtime 或 Human 决定。

## 3. Completed -- 只读复核事实

- 原任务 W1 在 run `20260925T061052Z-27529` 的三个 cycles 中经历两次 Reviewer `REJECT`，第三次得到机器 Reviewer `ACCEPT`。旧 Runtime machine block 已 `COMPLETED/disabled`，framework evidence commit `5e544b3ac6700a14fde5177020ef6d6613f0d0f4` 已 push。三层逻辑终态为 `RUNTIME_TRANSITION_COMMITTED / APPLIED / PUSHED`。这些是历史控制面事实，不等于当前目标代码已获最终独立验收。
- 原 target 分支当前 HEAD `352e62b...`，从已验收 layout commit `569e5c...` 连续形成 3 个普通 commits。独立审核时 target 工作树 clean，但未推送到远端；在新 run 前必须重新检查，不依赖本段的旧快照。
- 独立 Reviewer 直接复跑 focused 34/34、完整 ResourceWarning-strict 136/136，均 PASS；随后使用隔离临时目录额外注入目标目录项替换，得到 `store_path_points_to_writer=False`、`store_path_content=decoy`、`writer_content=before|after|`。正常测试全绿不足以覆盖此竞态。
- 根因边界: `TranscriptStore.rename_clean()` 在原子无覆盖改名后先把 `clean_path` 设为候选目标，目标随后被移动/替换时抛出携带该路径的 `CleanRenameVerificationError`；UI 捕获后同样把候选目标保存为当前路径。打开的写入句柄继续指向旧 inode，路径按钮却指向新放入的同名文件。此为上游 Static AC-07 的具体反例。
- 独立 verdict: `REJECT / REPAIR REQUIRED`，目标分支暂不推送，Human 实机验收暂不开始。它显式 invalidates 原 run 对 AC-07 充分性的接受主张，不撤销机器已发生的 transition，也不删除旧 Reviewer verdict、test PASS 或 framework evidence。
- Human Owner 已完成 Codex Mix 切号。旧 PID 26957/26968 经精确 TERM 退出；当时的桌面 app-server PID 30383 只作为历史记录。未来 run 要重新绑定当前激活账号，不能继承旧 run 的账号身份。

## 4. Active R1 -- 修复候选路径身份错误

- Objective: 在改名提交后、目标身份验证前发生外部目录项替换时，应用不得将 decoy 路径作为当前 Clean 路径暴露，同时保持原文件写入连续和原任务 AC-05/06/07 的其它承诺。
- Inputs: 本 Static、上游 Static/Runtime、handoff 与直接 target/run evidence。Reviewer 需先验证固定基线、目标分支和原反例仍存在。
- Permitted changes: 本 Static 第 3 节限定的 target Store/UI/必要 Controller、tests 与精确文档更新；普通 descendant commit。
- Prohibited changes: 原 Static/机器 Runtime/transition record、历史 run 和 evidence、Whisper/ASR/audio/模型、真实用户 Session、认证材料、未授权 target push/merge/release。
- Required evidence: 改名前后 writer inode 和可访问路径身份，真实同目录 move + decoy 注入，持续追加 bytes，Store/UI 路径及路径按钮行为；目标缺失/符号链接、普通 I/O 错误、no-clobber 与 Session 切换回归；完整 commit/diff/tests locator。
- Acceptance: R-AC-01 至 R-AC-06 必须逐项由新 Reviewer 独立审核。原 run 的 ACCEPT 不算本修复的 PASS；仅重跑原 136 项也不充分。
- Stop conditions: 无法保持原合同的有效路径保证；需缩小外部 mutation 支持边界；路径与 writer 身份无法证明；target/framework HEAD 或治理 hash 漂移；需要写真实用户数据或更改旧机器块。此时输出 `HUMAN DECISION REQUIRED`，不要猜测恢复。
- Executor report: 设计选择、与原 inode/路径保证的关系、修改文件、对抗性与常规测试、完整 SHA、隐私/未测边界；不得自行形成最终 ACCEPT。

## 5. 激活前治理与运行 gate

1. Human Owner 已在当前对话明确授权由本助手启动并监控 R1；原准备阶段只写文档的边界由本次授权取代。
2. 重新核对 framework `main` 本地/远端 clean、target branch/HEAD/clean、handoff hash、上游原合同及已完成机器块。不得删除或修改旧 run，也不得以原 `workload_retry_01.json` 执行新 run。
3. 本 Runtime 的唯一 machine block 激活 R1，使用独立 `workload_id=whisper_clean_rename_integrity_repair_v1`、`transition_mode=reviewer_accept_once`、`active_step={id:R1,status:ACTIVE}`、`last_transition_id=null`；专用 config 为同目录 `workload.json`，state root 为 `1PCloop/.local/state/whisper_clean_rename_integrity_repair_v1`。新 run ID 由 runner 创建，不复用旧终态。
4. 使用 Codex Mix dedicated Reviewer/Executor homes；新 run 的额度账号取**启动时**的当前激活账号，不继承旧身份。doctor/preflight 必须验证认证事务、A/B retirement snapshot、role 配置和目标/framework Git 状态。
5. 新任务独立 ACCEPT 后，仍需本对话或 Human 指定的独立审核直接检查反例和充分性，再根据既有普通 push 授权决定目标分支 push。之后才交 Human 做真实音频/macOS验证。

## 6. Human Decision Gate

若外部进程可在验证后继续移动/替换当前文件，则任一固定路径都可能立即失效。这不是靠当前代码的一次 `lstat()` 就能证明永久有效。R1 可以修复已复现的提交后验证窗口，但不能静默宣称支持无锁、任意外部并发修改下的强一致性。若实现者判断原 Static 对这种环境要求的是无法机械保证的永久有效路径，必须先向 Human Owner说明限制，并请求选择：限定为本应用单 writer + 可检测外部 mutation，或批准新的协同/监控协议。批准前不得用较弱语义宣告 AC-07 已完成。

## 7. Machine state

本 Runtime 只有一个 R1 ACTIVE machine block。首轮 R1 的 `HUMAN_GATE` 未产生 transition；旧 W1 的 completed/disabled block 及历史 transition record 保持原状。

<!-- 1PCLOOP_RUNTIME_STATE_BEGIN -->
{
  "active_step": {
    "id": "R1",
    "status": "ACTIVE"
  },
  "last_transition_id": null,
  "schema_version": 1,
  "transition_mode": "reviewer_accept_once",
  "workload_id": "whisper_clean_rename_integrity_repair_v1"
}
<!-- 1PCLOOP_RUNTIME_STATE_END -->

## 8. R1 首轮运行结果 -- 2026-09-25

- 受控 run: `20260925T073217Z-31813`，新 config `workload.json`，新 state root；启动前 doctor 9/9 PASS、preflight PASS。原 W1 终态未 resume 或覆盖。
- Reviewer instruction 独立复现原同目录移动加 decoy，并要求 Store/Controller/UI 在公开路径前验证写入句柄 inode。Executor 提交目标普通后继 `b62ef6947d6a634c56e695740e4ea446751e6c79`，parent 为固定修复基线 `352e62b2bf3cd3690e8eee57cb2e933f1405c6af`；target 工作树 clean，分支未 push。
- 同一 Reviewer thread 复审确认：同目录移位加 decoy 的原反例已被阻断，Finder/路径复制改为通过 Store 重新验证；Reviewer 独立完整 ResourceWarning-strict 回归 143/143 PASS，`git diff --check` PASS。
- Reviewer verdict: `HUMAN_GATE`。当外部进程将原 Clean inode 移出 Session，测试显示 `clean_path=None`，路径操作 fail closed，而打开的写入句柄仍可继续追加。这避免指向 decoy，但不能满足上游 AC-07 对失败后有效当前路径的字面承诺。Human Owner 需选择“应用单 writer + 可检测外部 mutation”边界，或要求更强的协调/监控机制；未经选择不得自行缩小 Static 或宣告 ACCEPT。
- 三层终态: `HUMAN_GATE / NOT_APPLIED / PUSHED`，exit 0。framework evidence commit `ae15960ad25da06c8cf687f2a46bad917c9d520c` 已普通 push；本 run 的 raw 位于 `1PCloop/.local/runs/20260925T073217Z-31813/`，tracked summary 为 `1PCloop/evidence-summaries/20260925T073217Z-31813.md`。`PUSHED` 仅代表证据发布。
- 事后只读 `status`、`inspect`、`human-gate` 均 PASS 并指向 `HUMAN_REVIEW_REQUIRED`。三个 Agent turn 的 role auth 均恢复，active identity 未变，实际凭据扫描命中 0。真实音频/macOS Human gate 尚未开始。
- 下一步只等待 Human 对合同边界做显式决定；之后另行规划修复或验收，不复用本终态 run。
