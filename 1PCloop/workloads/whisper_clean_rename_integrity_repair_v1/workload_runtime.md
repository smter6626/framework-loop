# Whisper Clean 重命名路径身份修复 v1 -- Runtime 准备状态

## 1. Current Status

- Task ID: `whisper_clean_rename_integrity_repair_v1`
- 状态: `PREPARED / NOT ACTIVE / AWAITING HUMAN RUN AUTHORIZATION`
- 当前 verdict: `NOT EVALUATED`，修复任务没有 Executor commit 或 Reviewer verdict
- 唯一 Active Step: 无；下方 R1 仅为待激活的有界修复 step
- Static identity: `1PCloop/workloads/whisper_clean_rename_integrity_repair_v1/workload_static.md`，SHA-256 `bc70ba55127ea3e5becfc33c9924948409d1247306610ee2948cbd7fee861bc4`
- Target: `/Users/smterpro/Workspace/whisper/live_subtitle_generator-session-ui`；当前拟使用 `codex/clean-toolbar-rename-v1`，固定修复基线 `352e62b2bf3cd3690e8eee57cb2e933f1405c6af`
- Blocker: 无代码可行性结论；Human 尚未授权启动新 1PCloop run，且新 config/机器块均未创建。若第 4 节 Human Decision Gate 触发，则暂停修复
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

## 4. Proposed R1 -- 修复候选路径身份错误

- Objective: 在改名提交后、目标身份验证前发生外部目录项替换时，应用不得将 decoy 路径作为当前 Clean 路径暴露，同时保持原文件写入连续和原任务 AC-05/06/07 的其它承诺。
- Inputs: 本 Static、上游 Static/Runtime、handoff 与直接 target/run evidence。Reviewer 需先验证固定基线、目标分支和原反例仍存在。
- Permitted changes: 本 Static 第 3 节限定的 target Store/UI/必要 Controller、tests 与精确文档更新；普通 descendant commit。
- Prohibited changes: 原 Static/机器 Runtime/transition record、历史 run 和 evidence、Whisper/ASR/audio/模型、真实用户 Session、认证材料、未授权 target push/merge/release。
- Required evidence: 改名前后 writer inode 和可访问路径身份，真实同目录 move + decoy 注入，持续追加 bytes，Store/UI 路径及路径按钮行为；目标缺失/符号链接、普通 I/O 错误、no-clobber 与 Session 切换回归；完整 commit/diff/tests locator。
- Acceptance: R-AC-01 至 R-AC-06 必须逐项由新 Reviewer 独立审核。原 run 的 ACCEPT 不算本修复的 PASS；仅重跑原 136 项也不充分。
- Stop conditions: 无法保持原合同的有效路径保证；需缩小外部 mutation 支持边界；路径与 writer 身份无法证明；target/framework HEAD 或治理 hash 漂移；需要写真实用户数据或更改旧机器块。此时输出 `HUMAN DECISION REQUIRED`，不要猜测恢复。
- Executor report: 设计选择、与原 inode/路径保证的关系、修改文件、对抗性与常规测试、完整 SHA、隐私/未测边界；不得自行形成最终 ACCEPT。

## 5. 激活前治理与运行 gate

1. 先取得 Human Owner 对启动 R1 的明确授权；本轮仅写准备文档，不运行 Agent。
2. 重新核对 framework `main` 本地/远端 clean、target branch/HEAD/clean、handoff hash、上游原合同及已完成机器块。不得删除或修改旧 run，也不得以原 `workload_retry_01.json` 执行新 run。
3. 用本 Runtime 的唯一新 machine block 激活 R1，设置独立 `workload_id=whisper_clean_rename_integrity_repair_v1`、`transition_mode=reviewer_accept_once`、`active_step={id:R1,status:ACTIVE}`、`last_transition_id=null`；建立独立 config、state root、新 run ID。该激活由治理准备者在授权后完成，不由 Executor 静默修改。
4. 使用 Codex Mix dedicated Reviewer/Executor homes；新 run 的额度账号取**启动时**的当前激活账号，不继承旧身份。doctor/preflight 必须验证认证事务、A/B retirement snapshot、role 配置和目标/framework Git 状态。
5. 新任务独立 ACCEPT 后，仍需本对话或 Human 指定的独立审核直接检查反例和充分性，再根据既有普通 push 授权决定目标分支 push。之后才交 Human 做真实音频/macOS验证。

## 6. Human Decision Gate

若外部进程可在验证后继续移动/替换当前文件，则任一固定路径都可能立即失效。这不是靠当前代码的一次 `lstat()` 就能证明永久有效。R1 可以修复已复现的提交后验证窗口，但不能静默宣称支持无锁、任意外部并发修改下的强一致性。若实现者判断原 Static 对这种环境要求的是无法机械保证的永久有效路径，必须先向 Human Owner说明限制，并请求选择：限定为本应用单 writer + 可检测外部 mutation，或批准新的协同/监控协议。批准前不得用较弱语义宣告 AC-07 已完成。

## 7. Machine state

本准备 Runtime **没有** `1PCLOOP_RUNTIME_STATE_BEGIN/END` machine block，因此不能被 mutation runner 当作可执行任务。只有第 5 节 gate 满足后才能添加新 R1 block。旧 W1 的 completed/disabled block 及历史 transition record 保持原状。
