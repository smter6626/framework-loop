# Whisper Clean 全文恢复 R2 -- Runtime

## 1. Current Status

- Task ID: `whisper_clean_fulltext_recovery_r2`
- 状态: `IMPLEMENTED / MACHINE ACCEPTED / INDEPENDENTLY ACCEPTED / HUMAN MACOS VALIDATION PENDING`
- Verdict: `ACCEPT`；机器 Reviewer 与本对话独立审核均通过，真实麦克风/Finder/clipboard/macOS 交互仍由 Human Owner 验收
- 唯一 Active Step: 无；`R2` machine block 已 `COMPLETED`
- Static: `1PCloop/workloads/whisper_clean_fulltext_recovery_r2/workload_static.md`
- Static identity: SHA-256 `1d75a64ba29fd5c36689274ad2b2079ace822f2dfe91c35f7f4b98b251276d4c`
- Target: `/Users/smterpro/Workspace/whisper/live_subtitle_generator-session-ui`，branch `codex/clean-toolbar-rename-v1`，R2 baseline `b62ef6947d6a634c56e695740e4ea446751e6c79`，accepted HEAD `fb317ea4a2b1db557133e91590e852c0241a3cd8`
- Blocker: 无自动工程 blocker
- Pending Tasks: Human Owner 运行真实录音和 macOS UI/Finder/clipboard 黑盒验收；merge、tag、release 仍未授权

## 2. Completed -- R2 输入与 Human 决定

- W1 历史成功 run `20260925T061052Z-27529` 及其后续独立 AC-07 REJECT 均保留于 `1PCloop/workloads/whisper_clean_toolbar_rename_v1/workload_runtime.md`。
- R1 run `20260925T073217Z-31813` 的 target commit `b62ef6947d6a634c56e695740e4ea446751e6c79` 阻断同目录 move+decoy；Reviewer 严格回归 143/143 PASS，但因外部把 writer inode 移出 Session 后无可验证路径而给 `HUMAN_GATE / NOT_APPLIED / PUSHED`。证据见 `1PCloop/workloads/whisper_clean_rename_integrity_repair_v1/workload_runtime.md`、`1PCloop/evidence-summaries/20260925T073217Z-31813.md` 和 Git-ignored raw run。R1 的机器块及终态保持原样。
- Human Owner 于 2026-09-25 在当前对话明确选择新的异常恢复行为：路径不在原 Session 时弹出“是否创建 `<inputString>.txt`”；“是”要包含此前全部转录并承接后续写入，“否”不处理并继续转录，同时明确保存风险。之后 Human 要求先评估全文恢复难度，并认可 Store 层精确复制/Stop 前快照方案，最后授权“准备 R2”。这授权合同与准备文件，不授权本轮启动 Agent。
- Human Owner 于 2026-09-25 在读取本任务交接后明确要求“启动并监控 R2”。本次授权激活唯一 `R2/ACTIVE` machine block；它不扩大 Static、target push、merge、tag、release 或真实用户 Session 的授权边界。
- 首次启动因当前账号不支持 `gpt-6-sol` 失败后，Human Owner 明确授权改用 `gpt-5.6-sol` 重新开始，并保持 Reviewer `xhigh`、Executor `high`。本授权不允许改变账号、推理强度或其他边界。
- 直接代码核查：当前 Clean writer 以只写 `w` 模式打开；Store 的 `append_clean()` 和 `rename_clean()` 已有同一 `_clean_lock`，Stop 会关闭文件；UI 表格只保留解析后的时间/正文且事件可能排队，因此不能作为精确 Clean 字节的权威来源。隔离临时文件实验确认，改为可读写句柄后，在路径被移走、由 decoy 占用或 unlink 时，句柄仍可读取已写完整内容。该实验是可行性证据，不是 R2 实现或验收。

## 3. Proposed R2 -- 全文恢复与明确的“否”语义

- Objective: 当当前 Session Clean 路径经验证缺失时，给 Human 一次明确选择；“是”安全生成完整 `<stem>.txt` 并切换后续写入，“否”保持原句柄和当前转录但清楚显示路径/持久性风险。
- Inputs: R2 Static、W1/R1 Static/Runtime、R1 target commit/diff 与 run evidence、Store/Controller/UI/engine 直接代码；不能仅凭交接文档或 UI 表格。
- Permitted changes: R2 Static 第 4 节限定的 target Store/必要 Controller/UI、相关 tests 和准确的双语文档；普通 target 后继 commit。
- Prohibited changes: 旧 W1/R1 治理及 evidence、真实 Session、ASR/audio/model、framework runner、认证、未授权 target push/merge/release。
- Required evidence: 活跃和 Stop 后准确的原始 Clean 字节；外部 move/unlink、decoy/冲突/符号链接、临时复制失败及后续 append 的文件身份与顺序；“否”后不产生新文件且路径动作 fail closed；Qt 中英文本与 Session freshness；完整 tests、commit/diff/hash。
- Acceptance: R2-AC-01 至 R2-AC-06 由新的 Reviewer 独立判断；机器 ACCEPT 后还需本对话独立复核。真实麦克风/macOS 黑盒留给 Human。
- Stop conditions: 无法证明精确全文、切换丢行/重复、错误时覆盖或发布部分目标、误把不确定 I/O 当作缺失、须改变 Human 决定或目标分支身份时停止。
- Executor report: 修改逻辑、精确文件范围、active/Stop/No/失败矩阵、测试结果、完整 commit、未测边界；不得自行宣告最终 ACCEPT。

## 4. 启动前 gate

1. Human Owner 已明确授权启动并监控 R2；本 Runtime 已添加唯一 `R2/ACTIVE`、`reviewer_accept_once` machine block。
2. 首次 run 使用新的 state root `1PCloop/.local/state/whisper_clean_fulltext_recovery_r2`，未 resume W1/R1。首次 run 因模型可用性 `FAILED_CLOSED` 后，显式 `workload_retry_01.json` 绑定该失败和同一 target HEAD，并使用独立 retry state root。
3. 重新检查 framework 本地/远端 main 和 target branch/HEAD/clean、R1 evidence、Static hash、Codex Mix 当前账号认证事务及 role 配置。新 run 绑定启动时激活账号，不沿用 R1 账号。
4. 原 config 与 retry config 均在对应 run 前通过 doctor/preflight。旧 R1 config/state/raw 保持只读；target branch 仅在自动 ACCEPT 和本对话独立验收均通过后普通 push。

## 5. Machine state

本 Runtime 只有一个 `R2/ACTIVE` machine block，仅授权一次 schema-valid Reviewer `ACCEPT -> COMPLETED` transition。R1 的 Human Gate 及历史机器块不在这里迁移或改写。

<!-- 1PCLOOP_RUNTIME_STATE_BEGIN -->
{
  "active_step": {
    "id": "R2",
    "status": "COMPLETED"
  },
  "last_transition_id": "2a59a9c1a90be25cd3d66abc9dd1f6db6c326c0d0f93df1d0f56f72cfc7d2efc",
  "schema_version": 1,
  "transition_mode": "disabled",
  "workload_id": "whisper_clean_fulltext_recovery_r2"
}
<!-- 1PCLOOP_RUNTIME_STATE_END -->

## 6. R2 首次启动结果 -- 2026-09-25

- Run `20260925T085542Z-34665` 在 cycle 1 的初始 Reviewer turn 启动后约 6 秒收到 Codex service `invalid_request_error`: 当前 ChatGPT 账号不支持 `gpt-6-sol`。本机 CLI 为 `0.157.0`；Reviewer role 明确配置 `gpt-6-sol / xhigh`，模型名称和推理强度配置未被自动替换。
- 三层终态为 `FAILED_CLOSED / NOT_APPLIED / PUSHED`，exit code 1。没有 Reviewer instruction、Executor turn、target commit 或 Runtime transition。Target 保持 branch `codex/clean-toolbar-rename-v1`、HEAD `b62ef6947d6a634c56e695740e4ea446751e6c79`、工作树 clean。
- Framework evidence commit `6ee2ac5b7ddf6cefc2dafb3da1e21fb7548ea082` 已普通 push。Tracked summary 为 `1PCloop/evidence-summaries/20260925T085542Z-34665.md`，raw evidence 位于 Git-ignored `1PCloop/.local/runs/20260925T085542Z-34665/`；旧失败不得删除或覆盖。
- 认证事务正常收尾：role auth 已恢复且前后 SHA-256 相同，active identity 未变化，实际凭据扫描命中 0。失败不是 target 实现、R2 Static、认证投影或凭据泄漏问题。
- 当前 machine block 保持 `R2/ACTIVE`。Human Owner 已授权使用 `gpt-5.6-sol`、原推理强度和独立 `workload_retry_01.json` 新建 retry run；不得 resume 这个 terminal failure，也不得切换账号、改用 API Key 或改变推理强度。


<!-- 1PCLOOP_RUNTIME_TRANSITION_RECORD -->
```json
{
  "accepted_preimage_sha256": "95b39fd05a05edbea17ba0f6968dc56a291cecc811ae2540742f0e656416fa08",
  "evidence": [
    {
      "kind": "commit",
      "locator": "fb317ea4a2b1db557133e91590e852c0241a3cd8",
      "sha256": "ed32f22ba2d6025e120bb88d6f3fc62e40f5e6ba528adfe8c1a5eb11db54546a"
    },
    {
      "kind": "file",
      "locator": "/Users/smterpro/Workspace/whisper/live_subtitle_generator-session-ui/transcript_store.py",
      "sha256": "131a41bc861ac05e46624a9d83396e669bcad65228465e7500fa72c732f1e660"
    },
    {
      "kind": "file",
      "locator": "/Users/smterpro/Workspace/whisper/live_subtitle_generator-session-ui/transcription_controller.py",
      "sha256": "29b97c75c9d90369289ecb7c07142e9e65648fb7816e4f4b56865fccaf2b6a48"
    },
    {
      "kind": "file",
      "locator": "/Users/smterpro/Workspace/whisper/live_subtitle_generator-session-ui/ui_app.py",
      "sha256": "537867b5bb91ba7c499d7de6db761d337f84ba9caa746a53818a2534b8e9f38c"
    },
    {
      "kind": "file",
      "locator": "/Users/smterpro/Workspace/whisper/live_subtitle_generator-session-ui/testCodes/test_clean_rename.py",
      "sha256": "69c3f03df532814114b139e18c4f1032389991c322bfad9e3d2952c41da7ec28"
    },
    {
      "kind": "file",
      "locator": "/Users/smterpro/Workspace/whisper/live_subtitle_generator-session-ui/docs/change_records/clean_fulltext_recovery_r2.md",
      "sha256": "d9a71ec543845fab63271fe18eddc4378627119e40ab4893db531e475d87bd58"
    },
    {
      "kind": "artifact",
      "locator": "/Users/smterpro/Workspace/framework-loop/1PCloop/.local/runs/20260925T085909Z-35123/cycle-02/executor/events.jsonl",
      "sha256": "a9bfdec7cd8fba01941f5f5e3d69d5e7b99d979c7c302c2e443c586e624ef980"
    },
    {
      "kind": "artifact",
      "locator": "/Users/smterpro/Workspace/framework-loop/1PCloop/.local/runs/20260925T085909Z-35123/cycle-02/executor/process.json",
      "sha256": "ca9b0445c17740daed281aee991cded61c02333f3e7160d9d955c1077c1c76ed"
    }
  ],
  "new_state": {
    "active_step": {
      "id": "R2",
      "status": "COMPLETED"
    },
    "last_transition_id": "2a59a9c1a90be25cd3d66abc9dd1f6db6c326c0d0f93df1d0f56f72cfc7d2efc",
    "schema_version": 1,
    "transition_mode": "disabled",
    "workload_id": "whisper_clean_fulltext_recovery_r2"
  },
  "old_state": {
    "active_step": {
      "id": "R2",
      "status": "ACTIVE"
    },
    "last_transition_id": null,
    "schema_version": 1,
    "transition_mode": "reviewer_accept_once",
    "workload_id": "whisper_clean_fulltext_recovery_r2"
  },
  "reviewer_verdict_locator": "/Users/smterpro/Workspace/framework-loop/1PCloop/.local/runs/20260925T085909Z-35123/cycle-02/reviewer-review/final.txt",
  "reviewer_verdict_sha256": "e76d1264427f5f743a61a8d6f1759c3550aa6c94a43e7b237b8b99be4b350400",
  "schema_version": 1,
  "target_head": "fb317ea4a2b1db557133e91590e852c0241a3cd8",
  "timestamp": "2026-09-25T09:21:48.881+00:00",
  "transition_id": "2a59a9c1a90be25cd3d66abc9dd1f6db6c326c0d0f93df1d0f56f72cfc7d2efc"
}
```

## 7. R2 retry、独立审核与 target push -- 2026-09-25

- Retry run `20260925T085909Z-35123` 使用 `gpt-5.6-sol`，Reviewer `xhigh`、Executor `high`，doctor 9/9 PASS、preflight PASS。它绑定首次 terminal failure `20260925T085542Z-34665`、相同 target baseline 和独立 state root；旧失败 evidence 未覆盖。
- Cycle 1 Executor commit `b9016520c9d136d0ed861b807f6e9e25d7f39d5d` 实现 Store 精确全文快照、active/Stop 后恢复、无覆盖切换、Controller ownership guard 和中英 Yes/No 风险 UX。机器 Reviewer 用真实临时 Session 复现“发布后 Session 路径被替换并出现同名 decoy”反例，尽管 focused 52/52、full 154/154 全绿，仍对 R2-AC-03/R2-AC-05 给 `REJECT`。
- Cycle 2 repair commit `fb317ea4a2b1db557133e91590e852c0241a3cd8` 在 Store 状态发布前重新验证 no-follow Session pathname identity 和 destination inode，并仅通过原 verified directory fd 清理自有 recovery inode。新增 active、stopped/snapshot、destination-replacement 三类竞态测试；最终 focused 55/55、ResourceWarning-strict full 157/157 PASS。
- 同一 Reviewer thread 对 cycle 2 给 schema-valid `ACCEPT`，请求唯一 `R2 -> COMPLETED` transition。三层终态为 `RUNTIME_TRANSITION_COMMITTED / APPLIED / PUSHED`，exit code 0；transition ID `2a59a9c1a90be25cd3d66abc9dd1f6db6c326c0d0f93df1d0f56f72cfc7d2efc`，framework evidence commit `46357c0c7fed016224e773578e7aae89cdc56c2b` 已普通 push。
- 本对话直接审核最终 diff、关键 Store/Controller/UI 边界和 evidence，独立复跑 focused 55/55 与 full 157/157，compile/import、`git diff --check`、commit/file hashes 和 clean worktree 全部通过。未发现新的自动工程 blocker。
- 五个 Agent turn 均 exit 0；role auth 每轮恢复且前后 SHA-256 相同，active identity 未变化，实际凭据扫描命中 0。失败 run 和 retry run 的 raw/tracked evidence 均保留。
- 按既有授权，target branch `codex/clean-toolbar-rename-v1` 已普通 push；local HEAD、`origin/codex/clean-toolbar-rename-v1` 与 GitHub ref 均为 `fb317ea4a2b1db557133e91590e852c0241a3cd8`。未 merge、tag 或 release。
- 剩余 gate 仅为 Human Owner 的真实录音、录制中/停止后重命名恢复、Finder/clipboard 与 macOS 对话框黑盒验收。自动 Reviewer ACCEPT 不替代该 gate。
