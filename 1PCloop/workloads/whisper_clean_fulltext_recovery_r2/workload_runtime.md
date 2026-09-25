# Whisper Clean 全文恢复 R2 -- Runtime

## 1. Current Status

- Task ID: `whisper_clean_fulltext_recovery_r2`
- 状态: `ACTIVE / FIRST RUN FAILED CLOSED / RETRY AUTHORIZED`
- Verdict: `NOT EVALUATED`；首次 run 未产生 Reviewer instruction、Executor commit 或 Reviewer verdict
- 唯一 Active Step: `R2 -- Clean 全文恢复与明确的否语义`
- Static: `1PCloop/workloads/whisper_clean_fulltext_recovery_r2/workload_static.md`
- Static identity: SHA-256 `1d75a64ba29fd5c36689274ad2b2079ace822f2dfe91c35f7f4b98b251276d4c`
- Target: `/Users/smterpro/Workspace/whisper/live_subtitle_generator-session-ui`，branch `codex/clean-toolbar-rename-v1`，R2 基线 `b62ef6947d6a634c56e695740e4ea446751e6c79`
- Blocker: 无；retry 启动前须以新 config 重新通过 doctor/preflight
- Pending Tasks: 使用 `workload_retry_01.json` 启动新 run 并监控到明确终态。旧任务真实音频/macOS Human gate 尚未执行，仍是自动验收后的独立 gate

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
2. 创建新的 state root `1PCloop/.local/state/whisper_clean_fulltext_recovery_r2`，不 `resume` W1/R1 终态，也不使用 runner 的 `retry` 字段：该字段只接受 `FAILED_CLOSED` 且相同初始 target HEAD，R1 是 `HUMAN_GATE` 且 target 已变化。
3. 重新检查 framework 本地/远端 main 和 target branch/HEAD/clean、R1 evidence、Static hash、Codex Mix 当前账号认证事务及 role 配置。新 run 绑定启动时激活账号，不沿用 R1 账号。
4. 对本目录 `workload.json` 跑 doctor/preflight；全部 PASS 后才可 `run`。旧 R1 config/state/raw 只读保留。真实 target branch 普通 push 只能在自动和本对话独立验收均通过后执行。

## 5. Machine state

本 Runtime 只有一个 `R2/ACTIVE` machine block，仅授权一次 schema-valid Reviewer `ACCEPT -> COMPLETED` transition。R1 的 Human Gate 及历史机器块不在这里迁移或改写。

<!-- 1PCLOOP_RUNTIME_STATE_BEGIN -->
{
  "active_step": {
    "id": "R2",
    "status": "ACTIVE"
  },
  "last_transition_id": null,
  "schema_version": 1,
  "transition_mode": "reviewer_accept_once",
  "workload_id": "whisper_clean_fulltext_recovery_r2"
}
<!-- 1PCLOOP_RUNTIME_STATE_END -->

## 6. R2 首次启动结果 -- 2026-09-25

- Run `20260925T085542Z-34665` 在 cycle 1 的初始 Reviewer turn 启动后约 6 秒收到 Codex service `invalid_request_error`: 当前 ChatGPT 账号不支持 `gpt-6-sol`。本机 CLI 为 `0.157.0`；Reviewer role 明确配置 `gpt-6-sol / xhigh`，模型名称和推理强度配置未被自动替换。
- 三层终态为 `FAILED_CLOSED / NOT_APPLIED / PUSHED`，exit code 1。没有 Reviewer instruction、Executor turn、target commit 或 Runtime transition。Target 保持 branch `codex/clean-toolbar-rename-v1`、HEAD `b62ef6947d6a634c56e695740e4ea446751e6c79`、工作树 clean。
- Framework evidence commit `6ee2ac5b7ddf6cefc2dafb3da1e21fb7548ea082` 已普通 push。Tracked summary 为 `1PCloop/evidence-summaries/20260925T085542Z-34665.md`，raw evidence 位于 Git-ignored `1PCloop/.local/runs/20260925T085542Z-34665/`；旧失败不得删除或覆盖。
- 认证事务正常收尾：role auth 已恢复且前后 SHA-256 相同，active identity 未变化，实际凭据扫描命中 0。失败不是 target 实现、R2 Static、认证投影或凭据泄漏问题。
- 当前 machine block 保持 `R2/ACTIVE`。Human Owner 已授权使用 `gpt-5.6-sol`、原推理强度和独立 `workload_retry_01.json` 新建 retry run；不得 resume 这个 terminal failure，也不得切换账号、改用 API Key 或改变推理强度。
