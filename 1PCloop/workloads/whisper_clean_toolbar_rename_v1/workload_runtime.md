# Whisper Clean 工具栏与实时文件重命名 v1 -- Runtime 准备状态

## 1. Current Status

- Task ID: `whisper_clean_toolbar_rename_v1`
- 状态: `PREPARED / NOT ACTIVE / AWAITING HUMAN START AUTHORIZATION`
- 当前 verdict: `NOT EVALUATED`
- 唯一 Active Step: 无。下方 W1 只是待激活草案；本轮没有 1PCloop run。
- Static identity: `1PCloop/workloads/whisper_clean_toolbar_rename_v1/workload_static.md`; SHA-256 `823448659f5eaa99eaf05ce3063f12e9ff82e1462ff8c243e40510e7aed853ec`
- 固定 target baseline: `569e5c551c101811ed80fca23bd5708d6ac880cf`；target worktree 当前在 `codex/bounded-scrollable-main-window-v1`，不是本任务执行分支。
- 任务入口: Human Owner 2026-09-24 提出三项要求，并明确补充录音/转录进行中可重命名、Stop 后未开始新 Session 时可重命名、新 Session 建立后对象切换为新 Clean 文件。
- 最近 Pending 截止: 无。真实 macOS/音频功能检查是自动验收后的 Human gate，不是当前代码 blocker。
- 运行授权: 尚未给出。不得创建新 run、激活 W1 或调用 Agent。

## 2. Completed -- 只读准备

- 前序 `whisper_window_layout_v1` 的自动 L1 已完成，target commit `569e5c...`、framework evidence commit `bd3c088840342d59e79d224f6fd0ab8a49fe11a8`。Human Owner 在当前对话中报告真实 macOS布局验收 PASS；旧 task-local/global Runtime 尚未记录 closure。保留旧 run/evidence，不复用旧 L1 machine step。
- 已只读检查 target `ui_app.py`、`transcript_store.py`、`transcription_controller.py`、`transcription_engine.py`、相关 UI/session tests 和文档。target 当前 branch/HEAD 为 `codex/bounded-scrollable-main-window-v1` / `569e5c...`，工作树 clean。
- 可行性结论: 三项 UI 调整无架构 blocker。实时重命名不能只移动 `ui_app.current_clean_path`：`TranscriptStore` 在 worker 写入期间持有 `_clean_file`，Controller 持有当前 Session owner，UI 又缓存路径。受控同目录文件改名、存储层路径/Session 身份同步和无覆盖错误处理具备实现路径；具体机制由 Executor 在 W1 先读依赖并设计，再由 Reviewer 用实际后续追加和失败注入审核。不得退化为只允许 Stop 后。
- 自动测试边界: offscreen Qt、fake engine/store 和临时目录足以验证布局、路径、并发写入逻辑与文件 bytes；它们不证明真实麦克风/Whisper/macOS交互。实际黑盒仍归 Human Owner。
- 旧目标 repo 的 LLM 设计资料假设固定 `clean.txt`，但当前生产 Python 路径扫描未发现已实施的其他固定读取方；W1 必须重扫最新代码，并在文档中留下将来读取方需处理重命名路径的限制。
- 本次创建新 task 的 Static/Runtime，并按 Human Owner 指定将两个 dedicated role runtime 的 `config.toml` 分别设为 Reviewer `gpt-6-sol/xhigh`、Executor `gpt-6-sol/high`；context window 512000 与 auto compact 260000 保持不变。本机 Codex Mix README 的 role 表同步更新。没有修改 target、旧 Runtime、global Runtime、framework runner、角色凭据或历史 evidence；没有调用 Codex service。

## 3. Proposed W1 -- 待 Human 授权后成为唯一 Active Step

- Objective: 将复制新增 Clean 文本移至 Clean 工具栏右上、将定位/复制路径按钮缩为左侧同一行，并实现当前 Session Clean 文件在录音中及 Stop 后安全重命名为固定 `.txt` 后缀的用户指定名称。
- Inputs: 本 Static；固定 target baseline；`ui_app.py::TranscriptTable`/`MainWindow`；`TranscriptStore` 写入句柄；Controller Session owner/event；相关 tests；已通过 Human 布局 gate 的旧任务结果。
- Permitted changes: Static 第 6 节列出的 target UI、必要 Controller/Store 同步、相关 tests 和 target-side 文档。只有证据证明直接依赖时才最小改 engine。
- Prohibited changes: 本 task Static/Runtime、旧 workload、framework runner、Whisper 模型/ASR/音频算法、真实用户输出、Git history rewrite、未授权 push/merge/release。
- Required evidence: 完整 target commit/parent/diff；当前 Session 在活跃写入、Stop 后、下一 Session、重复改名情况下的文件 bytes/identity 与路径证据；无覆盖/逃逸/取消/I/O 失败矩阵；Qt 左右布局、双语、滚动/focus 与增量复制回归；完整可运行测试输出及绝对 locator/hash；target change record。
- Acceptance: Static AC-01 至 AC-08 由独立 Reviewer 判断。AC-09 保留为后续 Human 实机 gate。
- Executor self-check: focused Qt/store/controller tests；现有 session clipboard、window layout、UI language、output/model tests；full unittest discovery；编译/import、`git diff --check`、branch/allowlist/clean status。测试需用虚构文本和临时 Session，不能操作真实历史 Session。
- Stop conditions: 无法证明转录期间持续追加到改名后的同一文件；只能用会覆盖现有目标的机制；Session/路径竞争无法 fail closed；需要改变 Static、ASR、真实用户文件、旧任务或 Git 基线时立即停下。
- Report: 给出路径 ownership 与并发控制设计、每个文件的改动、逐项直接 evidence、失败矩阵、完整 commit/parent/branch、未测真实黑盒和已知限制。Executor 不形成最终 ACCEPT。

## 4. Activation Gate -- 下一次 Human 授权后依次执行

1. 依据 Human 已报告的 PASS，对 `whisper_window_layout_v1` task-local Runtime 和 global Runtime 做治理收尾；不改旧 machine transition record、run evidence 或 target 功能代码。
2. 核对 framework `main` 与 target branch/local/remote/clean 身份。若任何身份漂移，先重新评估，不按本草案猜测继续。
3. 从 target commit `569e5c...` 新建 `codex/clean-toolbar-rename-v1` 分支；不 merge/rebase 已有分支，不切到 target `main` 作为基线。
4. 再确认本 Static SHA 和目标事实；必要时按 Human 明确授权修订。把本 Runtime 改成 `ACTIVE`，只激活 W1，加入唯一有效的 machine state block：`schema_version=1`、`workload_id=whisper_clean_toolbar_rename_v1`、`transition_mode=reviewer_accept_once`、`active_step={id:W1,status:ACTIVE}`、`last_transition_id=null`。
5. 创建独立 `workload.json`、独立 state root、新 run ID。Reviewer/Executor 使用 Codex Mix dedicated homes 和 run-bound active account，不复用布局任务的 checkpoint。
6. 跑 `doctor` 与 `preflight`；验证 role config 目标为 Reviewer `gpt-6-sol/xhigh`、Executor `gpt-6-sol/high`，并确认认证事务、active identity、A/B retirement snapshot 和 worktree 状态均通过。只有全部通过且 Human 已授权启动，才执行 `run`。

## 5. Independent Review

- 尚无 W1 Executor diff、测试 artifact 或 Reviewer verdict。
- Reviewer 必须特别独立检查两个潜在 blind spot：一是“改名后原有打开句柄仍可写”不足以证明 UI/store/Controller 全部路径同步；二是单纯 `exists()` 后执行可能覆盖目标的 rename 不足以证明 no-clobber。
- 自动 ACCEPT 不能关闭 Human 的真实录音中改名和实际 Finder/clipboard gate。

## 6. Blockers, Pending and Next Action

- 代码可行性 blocker: 未发现。
- 当前执行 blocker: Human 尚未授权启动新 1PCloop run；前序 Human PASS 尚待写入 tracked Runtime；新分支、config 和 machine block 尚未建立。这些是明确准备 gate，不是功能拒绝。
- Pending Tasks: 无。
- 下一步: 等 Human Owner 明确授权后，先完成第 4 节的治理/分支/config/preflight，再运行 W1；本次不启动。

## 7. Machine State

本准备文档**故意没有** `1PCLOOP_RUNTIME_STATE_BEGIN/END` machine block，因此不能通过 mutation runner 的 Runtime preflight。只有第 4 节 gate 全部满足并取得 Human 启动授权后，才可添加 `ACTIVE` block；不得从旧布局任务复制已完成 block。
