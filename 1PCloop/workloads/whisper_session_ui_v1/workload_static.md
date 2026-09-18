# Whisper 会话与复制体验 v1 -- Static 稳定合同

## 1. 合同身份

- Task ID: `whisper_session_ui_v1`
- 合同状态: `AUTHORIZED`
- Human Owner: 当前用户
- 适用范围: `live_subtitle_generator` 的 streaming 文档整理与多语言版本的会话 UI 改动
- 最后一次授权变更: 2026-09-18，Human Owner 明确授权创建新分支和中文治理文档，并要求后续实现交给 1PCloop
- 模板参考: `1PCloop/templates/static_prompt_zh.md` 与 `runtime_prompt_zh.md`

本合同只规定稳定目标、边界、权限和验收要求。当前步骤、verdict、blocker 与运行记录只看同目录的 `workload_runtime.md`。

## 2. Objective

先让 1PCloop 将既有 streaming 升级治理/调查资料整理进目标仓库 `main`，再让它在 `multiLanguage_v1` 基础上改善录音会话显示和剪切板操作。最终用户应能复制本次 `clean.txt` 绝对路径、在再次录音时看到清空后的新会话内容、按上次复制断点获取新增 Clean 文本，并看到中文界面的 `语言/Language` 标签。

代码逻辑和可模拟 UI 行为由独立 Reviewer 审核；真实音频到转录的黑盒测试由 Human Owner 自行执行。自动 ACCEPT 不能被表述成真实录音黑盒已经通过。

## 3. Scope and Deliverables

### Step 1 -- streaming 文档整理

- Target: `/Users/smterpro/Workspace/whisper/live_subtitle_generator-main-docs`，branch `main`。
- 固定只读来源: 原仓库 commit `73891f3a4b07e7d0f9fda3cc2cb1f35475727c84` 中的 `docs/streaming_backend_upgrade/static.md`、`runtime.md`、`update_plan.md`。
- 由 1PCloop Reviewer/Executor 决定 `main` 中合适的文件位置和最少量导航/定位说明，不由本对话预先替其整理。
- 三份资料必须在 `main` 中可定位，并记录来源 commit、Git blob 或 SHA-256。locked `update_plan.md` 正文必须逐字节保留，SHA-256 为 `ae4566dd27dca2ba96d5beedd8d35ab490a46e51188fa82cbd05eef4d7917c40`；来源 Static/Runtime 的 SHA-256 分别为 `fa7ad06ff04d039dc0c76da11d647ccff537000d6ef3aa24fad64a791a80aa05` 和 `9354f271f905c895f9e477264bee19a9c47f18c82bc9ab417a815f3cf5c060b5`。若确需改变后两者，必须解释修改及权威性，不得暗改锁定计划。
- streaming 文档在 `main` 可见，不代表 streaming backend 已实现，也不自动把文档中另一个任务的 `ACTIVE` 状态变成 `main` 的当前实施任务。必要时增加清楚的分支/状态说明。
- 不将 `multiLanguage_v1` 的代码或 streaming upgrade 分支整体 merge 到 `main`。

### Step 2 -- 多语言版本上的 UI 功能

- Target: `/Users/smterpro/Workspace/whisper/live_subtitle_generator-session-ui`，branch `codex/session-clipboard-ui-v1`；该分支必须从 `multiLanguage_v1` commit `1e0cdd9fda1870a8277a553c3f7af7cc67480fe9` 派生，而非从 `main` 派生。
- 在现有“定位 Clean TXT”附近增加“复制 Clean TXT 路径”按钮。复制当前会话实际 `clean.txt` 的绝对路径到 macOS 系统剪切板，不复制内容；无有效会话时不可复制虚构路径；Stop 后仍可复制刚结束会话的路径，新会话建立后切换到新路径。使用 Qt clipboard API，不依赖 shell `pbcopy`。
- 成功创建新录音会话时，清空屏幕上的 Clean 与 Raw 两个转录表、重置对应计数与文本复制断点。Stop 本身不清屏，尾部结果继续可见。若 Start 在创建会话前失败，不应擦除旧显示。不得删改历史 `clean.txt`、`raw.txt`、日志或配置。旧会话的迟到 event 不能重新混入新会话。
- 增加“复制新增文本”按钮。复制当前屏幕 Clean 表格的文本列，不含时间戳、Raw、日志或尚未显示的文件内容。第一次成功复制从首行到当前末行；后续只复制上次成功复制行之后的新行，按显示顺序以 `\n` 连接。每次剪切板只写入本次切片，不追加旧剪切板。没有新行时不修改剪切板或断点；新会话重置断点。路径复制不改变文本复制断点。
- 把中文 UI 中现有的“界面语言”改为精确字符串 `语言/Language`。不得误改“音频/原文语言”控件。新增按钮必须有可理解的中英文 label，切换 UI 语言后立即更新。
- 允许修改相关 UI/controller 代码、自动测试及必要的中英文使用说明；不更换 streaming backend 或转录算法。

### 范围外

- streaming backend 的 embedded/rolling/AlignAtt 实施；
- main 与功能分支之间的代码 merge/cherry-pick；
- release、tag、打包发布、强推、历史改写；
- 真实音频录制/Whisper 转录由自动 Reviewer 代测，或自动宣告 Human 黑盒通过；
- 用户数据、模型、凭据或私有转录内容的提交。

## 4. Hard Constraints

1. 一个 1PCloop run 只绑定一个 target branch 和一个当前 Active Step。Step 1 的 `main` run 完成并独立验收后，才可在新 run 中执行 Step 2；不得在同一 run 中切换 target branch。
2. Reviewer 只读检查 target；Executor 只执行当前步骤、创建普通 descendant commit，不得修改 framework/workload Static/Runtime、推送 target、切换分支或扩大任务范围。
3. 目标分支、HEAD、clean worktree、治理 hash、evidence 和 Runtime transition 仍须通过 1PCloop 既有 fail-closed 检查。
4. 自动测试可使用 offscreen Qt、模拟 event/fake controller 和现有 regression；不得声称它们等价于真实音频黑盒。
5. 复制功能只处理用户当前会话的显示文本或路径，不改动转录文件内容、推理模型、语种识别规则与历史 evidence。
6. 原 `codex/streaming-backend-upgrade` 分支及其 task-local governance 保持原状。Step 1 仅在 `main` 形成文档集成，Step 2 仅在新功能分支形成 UI 变更。

## 5. Stable Background and Inputs

- 原仓库当前 checkout 为 `codex/streaming-backend-upgrade`，来源 commit `73891f3a4b07e7d0f9fda3cc2cb1f35475727c84`；`main` 基线为 `b5188ccc6aef591398fd8d31e162a29390b120e4`。
- `multiLanguage_v1` 基线为 `1e0cdd9fda1870a8277a553c3f7af7cc67480fe9`；其语言支持已由此前 workload 验收，但尚未 release 或 merge main。
- 当前 App 使用 PySide6，Clean/Raw 为只读转录表格；每次录音创建独立 session 目录与 `clean.txt`。现有 UI 提供“定位 Clean TXT”，但没有本任务要求的两个复制按钮和新会话清屏合同。
- `TO_CONFIRM`: Human Owner 的真实麦克风/打包 App 黑盒结果。该结果不由自动 Reviewer 推断；自动 loop 完成后单独报告。

## 6. Authority and Approval

- Human Owner: 决定合同变化、真实黑盒结论、是否 merge/release，以及任何超出两步的工作。
- 独立 Reviewer: 直接检查 commit/diff、代码路径、测试输出和证据充分性，形成 ACCEPT/REJECT/HUMAN_GATE；不得仅继承 Executor 自检结论。
- Executor: 仅可修改当前 Runtime Active Step 允许的 target 文件，运行自检并提交普通后继 commit；不得写治理文档或自我验收。
- Orchestrator: 仅在 CLI capability 与机器 Runtime block 双重授权并验证 Reviewer ACCEPT 后完成当前一步的 Runtime transition 和 framework evidence publication。
- 本对话可在每一步独立验收后，按 Human Owner 既有授权对对应 target branch 普通 non-force push；这不授权 merge、release 或 tag。

## 7. Permitted and Prohibited Mutations

- Step 1 允许 `main` 中与三份 streaming 资料及其准确导航直接相关的 `docs/`、README/repo map 变更；禁止应用代码、测试、模型、打包和无关治理修改。
- Step 2 允许功能分支中与会话表格、按钮、剪切板、事件隔离、相关测试和说明直接相关的变更；禁止 streaming backend、模型/运行时 pin、语言识别策略和无关文件修改。
- 两步都禁止改动外部 Tools/reference 仓库、用户真实录音、profile 凭据、历史 Git 记录或既有 1PCloop 已关闭 workload。

## 8. Acceptance Criteria

| ID | 验收条件 | Reviewer 所需直接 evidence | 通过边界 |
| --- | --- | --- | --- |
| AC-01 | streaming 资料可在 main 准确定位 | 固定来源 commit/blob/hash、target diff、README/repo map | 三份资料完整；locked plan 字节一致；不误称 backend 已实施；仅文档变更 |
| AC-02 | 功能分支确实基于 multiLanguage_v1 | merge-base/commit ancestry、branch、clean status | 不以 main 为功能基线；不改原 streaming branch |
| AC-03 | Clean 路径复制正确 | UI 代码路径、模拟 session 与 Qt clipboard 测试 | 复制当前 `clean.txt` 绝对路径；无会话、Stop、换会话行为明确 |
| AC-04 | 再次录音清屏且历史保留 | 新会话/失败 Start/Stop/迟到 event 测试，文件检查 | Clean/Raw 和计数、断点正确重置；历史文件不变 |
| AC-05 | Clean 新增文本按断点复制 | Qt clipboard 多轮点击测试、Unicode/空切片测试 | 不重不漏；仅文本列；无新行不改剪切板；新会话从首行重新开始 |
| AC-06 | UI label 与双语切换正确 | 直接控件文本测试 | 中文精确为 `语言/Language`；原文语言控件未误改；新按钮即时本地化 |
| AC-07 | 现有功能没有明显回归 | 目标仓库相关自动测试、完整可运行 regression、Reviewer 白盒检查 | 失败必须解释；不可将未运行的真实音频测试写成 PASS |

Step 1 只需满足 AC-01 及相应 Git/权限边界；Step 2 需满足 AC-02 至 AC-07。自动 Step 2 ACCEPT 后，最终真实音频黑盒结论仍由 Human Owner 决定。

## 9. Evidence and Privacy Boundary

- 固定 identity 使用完整 commit SHA、Git blob、SHA-256 与绝对 artifact locator；Reviewer 必须直接检查测试输出及必要代码路径。
- 原始 1PCloop turn/log 留在 Git-ignored 本地；tracked summary 只放精简结果、路径/identity 与限制。
- 不提交或公开真实用户音频、私有转录、模型、auth/profile 内容、隐藏 reasoning。
- `PUSHED` 只代表 evidence publication，不替代 target 功能正确或 Human 黑盒验收。

## 10. Change Control

- Static 实质变化需要 Human Owner 明确授权；Runtime 不得静默扩大范围。
- Step 1 机器 ACCEPT 只完成 Step 1，不自动激活 Step 2；激活前须核对 main 的 commit/push、Runtime transition、summary 与 Git clean 状态。
- Step 2 自动 ACCEPT 不等于整个产品任务关闭。真实录音黑盒保持待 Human 验证；发现问题可开启有边界 repair，不抹去原 verdict。
- 治理/分支/evidence 身份冲突时 fail closed，交由 Human 决定，不使用 reset/force 猜测性修复。

## 11. Open Decisions

- `TO_CONFIRM`: Human 实机黑盒测试结果及是否需要后续修复；不会阻止 Step 1 或 Step 2 的代码逻辑审核。
- `REQUIRES_OWNER_DECISION`: 任何功能分支 merge、release/tag 或 streaming backend 实施；当前没有授权。
