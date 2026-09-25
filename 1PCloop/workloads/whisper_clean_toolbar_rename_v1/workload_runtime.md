# Whisper Clean 工具栏与实时文件重命名 v1 -- Runtime 当前权威状态

## 1. Current Status

- Task ID: `whisper_clean_toolbar_rename_v1`
- 状态: `ACTIVE / W1 AWAITING MANUAL RUN`
- 当前 verdict: `NOT EVALUATED`
- 唯一 Active Step: `W1 -- Clean 工具栏与实时文件重命名`
- Static identity: `1PCloop/workloads/whisper_clean_toolbar_rename_v1/workload_static.md`; SHA-256 `eae16fa52bf532bc26accf7afecf78d0c4494128e57091ad613c621ace48948c`
- 固定 target baseline: `569e5c551c101811ed80fca23bd5708d6ac880cf`；target worktree 已在从该 commit 直接创建的 `codex/clean-toolbar-rename-v1` 分支，创建时无文件变化。
- 任务入口: Human Owner 2026-09-24 提出三项要求，并明确补充录音/转录进行中可重命名、Stop 后未开始新 Session 时可重命名、新 Session 建立后对象切换为新 Clean 文件。
- 最近 Pending 截止: 无。真实 macOS/音频功能检查是自动验收后的 Human gate，不是当前代码 blocker。
- 运行授权: Human Owner 于 2026-09-24 明确选择本人手动启动，并要求提供启动指令。本轮准备者只可完成治理、分支、config、doctor/preflight；不能替 Owner 执行 `run`。

## 2. Completed -- 只读准备

- 前序 `whisper_window_layout_v1` 的自动 L1 已完成，target commit `569e5c...`、framework evidence commit `bd3c088840342d59e79d224f6fd0ab8a49fe11a8`。Human Owner 在当前对话中报告真实 macOS布局验收 PASS；旧 task-local Runtime 已记录 Human acceptance 和 task closure，旧 machine block/run/evidence 未改写。
- 已只读检查 target `ui_app.py`、`transcript_store.py`、`transcription_controller.py`、`transcription_engine.py`、相关 UI/session tests 和文档。target 当前 branch/HEAD 为 `codex/bounded-scrollable-main-window-v1` / `569e5c...`，工作树 clean。
- 可行性结论: 三项 UI 调整无架构 blocker。实时重命名不能只移动 `ui_app.current_clean_path`：`TranscriptStore` 在 worker 写入期间持有 `_clean_file`，Controller 持有当前 Session owner，UI 又缓存路径。受控同目录文件改名、存储层路径/Session 身份同步和无覆盖错误处理具备实现路径；具体机制由 Executor 在 W1 先读依赖并设计，再由 Reviewer 用实际后续追加和失败注入审核。不得退化为只允许 Stop 后。
- 自动测试边界: offscreen Qt、fake engine/store 和临时目录足以验证布局、路径、并发写入逻辑与文件 bytes；它们不证明真实麦克风/Whisper/macOS交互。实际黑盒仍归 Human Owner。
- 旧目标 repo 的 LLM 设计资料假设固定 `clean.txt`，但当前生产 Python 路径扫描未发现已实施的其他固定读取方；W1 必须重扫最新代码，并在文档中留下将来读取方需处理重命名路径的限制。
- 初始化提交 `5c1cd6d3524ab493097df5a42a9b6b0b04126eca` 创建本 task Static/Runtime。两个 dedicated role runtime 的 `config.toml` 已按 Human 指定设为 Reviewer `gpt-6-sol/xhigh`、Executor `gpt-6-sol/high`；context window 512000 与 auto compact 260000 保持不变。本机 Codex Mix README 的 role 表已同步更新。本次激活没有修改 target 代码、framework runner、角色凭据或历史 evidence，也未调用 Codex Agent。
- Human 启动授权后，target worktree 从精确 `569e5c...` 创建本 task 的 `codex/clean-toolbar-rename-v1` 分支；branch 创建时 HEAD 不变且工作树 clean。

## 3. Active Step -- W1

- Objective: 将复制新增 Clean 文本移至 Clean 工具栏右上、将定位/复制路径按钮缩为左侧同一行，并实现当前 Session Clean 文件在录音中及 Stop 后安全重命名为固定 `.txt` 后缀的用户指定名称。
- Inputs: 本 Static；固定 target baseline；`ui_app.py::TranscriptTable`/`MainWindow`；`TranscriptStore` 写入句柄；Controller Session owner/event；相关 tests；已通过 Human 布局 gate 的旧任务结果。
- Permitted changes: Static 第 6 节列出的 target UI、必要 Controller/Store 同步、相关 tests 和 target-side 文档。只有证据证明直接依赖时才最小改 engine。
- Prohibited changes: 本 task Static/Runtime、旧 workload、framework runner、Whisper 模型/ASR/音频算法、真实用户输出、Git history rewrite、未授权 push/merge/release。
- Required evidence: 完整 target commit/parent/diff；当前 Session 在活跃写入、Stop 后、下一 Session、重复改名情况下的文件 bytes/identity 与路径证据；无覆盖/逃逸/取消/I/O 失败矩阵；Qt 左右布局、双语、滚动/focus 与增量复制回归；完整可运行测试输出及绝对 locator/hash；target change record。
- Acceptance: Static AC-01 至 AC-08 由独立 Reviewer 判断。AC-09 保留为后续 Human 实机 gate。
- Executor self-check: focused Qt/store/controller tests；现有 session clipboard、window layout、UI language、output/model tests；full unittest discovery；编译/import、`git diff --check`、branch/allowlist/clean status。测试需用虚构文本和临时 Session，不能操作真实历史 Session。
- Stop conditions: 无法证明转录期间持续追加到改名后的同一文件；只能用会覆盖现有目标的机制；Session/路径竞争无法 fail closed；需要改变 Static、ASR、真实用户文件、旧任务或 Git 基线时立即停下。
- Report: 给出路径 ownership 与并发控制设计、每个文件的改动、逐项直接 evidence、失败矩阵、完整 commit/parent/branch、未测真实黑盒和已知限制。Executor 不形成最终 ACCEPT。

## 4. Activation and Manual-Run Gate

1. Human PASS 治理收尾: 旧 task-local Runtime 与 global Runtime 只更新高层状态；旧 machine block、transition record、run evidence 和 target 代码保持不变。
2. Git 基线: framework `main` 与 target 原 feature branch local/remote/clean 一致；新 target branch 从固定 `569e5c...` 创建，不 merge/rebase 或切换到 `main` 基线。
3. 本 Static identity 已按启动授权更新并固定。下面只存在一个 W1 `ACTIVE` machine block；旧布局 L1 checkpoint 不复用。
4. 独立 `workload.json` 指向新分支和独立 state root，Reviewer/Executor 使用 Codex Mix dedicated homes 和 run-bound active account。
5. 手动 `run` 前必须确认当前 framework/target clean、`doctor` 和 `preflight` 均 PASS，role config 为 Reviewer `gpt-6-sol/xhigh`、Executor `gpt-6-sol/high`，且认证事务、active identity 与 A/B retirement snapshot 检查通过。任一检查失败，停止并报告，不运行 Agent。

## 5. Independent Review

- 尚无 W1 Executor diff、测试 artifact 或 Reviewer verdict。
- Reviewer 必须特别独立检查两个潜在 blind spot：一是“改名后原有打开句柄仍可写”不足以证明 UI/store/Controller 全部路径同步；二是单纯 `exists()` 后执行可能覆盖目标的 rename 不足以证明 no-clobber。
- 自动 ACCEPT 不能关闭 Human 的真实录音中改名和实际 Finder/clipboard gate。

## 6. Blockers, Pending and Next Action

- 代码可行性 blocker: 未发现。
- 当前执行 blocker: 无；`doctor`/`preflight` 是手动运行前的强制 gate，未通过即停止。
- Pending Tasks: 无。
- 下一步: Human Owner 使用独立 config 手动执行 `run`，结束时通知本对话进行独立验收；真实音频/macOS黑盒由 Human Owner 在自动审核之后另行核验。

## 7. Machine-owned State

<!-- 1PCLOOP_RUNTIME_STATE_BEGIN -->
{
  "active_step": {
    "id": "W1",
    "status": "ACTIVE"
  },
  "last_transition_id": null,
  "schema_version": 1,
  "transition_mode": "reviewer_accept_once",
  "workload_id": "whisper_clean_toolbar_rename_v1"
}
<!-- 1PCLOOP_RUNTIME_STATE_END -->

该机器块只授权 W1 的一次 schema-valid Reviewer `ACCEPT -> COMPLETED` transition。它不授权自动关闭 Human 真实录音 gate，也不授权 target merge、tag 或 release。
