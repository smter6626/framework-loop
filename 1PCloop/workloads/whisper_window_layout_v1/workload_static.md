# Whisper 主窗口高度与滚动 v1 -- Static 稳定合同

## 1. 合同身份

- Task ID: `whisper_window_layout_v1`
- 合同状态: `AUTHORIZED`
- Human Owner: 当前项目 Owner
- 适用范围: `live_subtitle_generator` 多语言功能分支后继上的主窗口几何、内容布局与滚动可达性
- 固定 target baseline: `fb7e38e4248b1b6fcf58a14193dbfe9315f90f34`
- 固定 target branch: `codex/bounded-scrollable-main-window-v1`
- 最后一次授权变更: 2026-09-18 Human Owner 确认“UI 太长，直接超出窗口限制”，要求下一项 1PCloop 任务限定窗口高度并在合适区域增加滚轮滑动

## 2. Objective

修复主窗口纵向内容超过 macOS 可用窗口范围的问题，使 App 在受支持的 macOS 显示环境中首次显示和缩小窗口后仍保持边界内可操作，并让超出可见区域的控制项可通过明确的垂直滚动和键盘焦点访问。

本任务只改变窗口布局和可达性，不改变已经验收的转录、Session、clipboard、模型、语言或 evidence 语义。

## 3. Scope and Deliverables

### 范围内

- 主窗口初始 geometry、minimum size 和 screen available geometry 的协调。
- 主窗口现有左侧 controls、右侧 transcript/log tabs、status strip 之间的尺寸策略。
- 在适当内容边界引入垂直滚动，使较小可用高度下所有操作控件可达。
- 鼠标滚轮、触控板、scrollbar 和键盘 focus traversal 的可达性。
- 中文/English 即时 retranslate、窗口 resize、不同注入 screen geometry 下的 deterministic UI tests。
- `docs/change_records/`、`docs/repo_map.md` 和必要的双语使用说明同步。

### 交付物

- 一个从固定 baseline 直接派生的普通 target commit。
- 主窗口在测试矩阵内不超出 available screen height，且所有 controls 可访问。
- 对滚动 ownership、窗口 geometry、retranslation 和既有 S2 功能的自动回归 evidence。
- 独立 Reviewer 白盒检查和 Human Owner 最终真实 macOS 视觉/交互验证入口。

### 范围外 / Non-goals

- Streaming backend、Whisper Runtime、model pin、ASR、dedup、转录或语言识别算法。
- Session ownership、Start/Stop、迟到 event、Clean path copy 或 incremental text copy 语义。
- 全面视觉重设计、主题替换、字体整体缩小、控件文案重写或新的产品功能。
- GUI framework 更换、并发/locking、release、tag、merge 或 target `main` 集成。

## 4. Hard Constraints

1. 不得通过隐藏、删除或永久折叠现有 controls 解决高度问题。
2. 不得把“用户可以拖大窗口”或“要求全屏”当作可达性修复。
3. 不得把单纯缩小字体、间距或控件高度作为唯一解决方案。
4. 窗口 geometry 必须依据 Qt 提供的 available screen geometry 或可注入的等价 boundary；不得只针对当前开发机写死像素高度。
5. Transcript/Raw/Logs 现有内部滚动必须保持可用。外层滚动不得无条件吞掉 table 内部滚轮，也不得让左侧 controls 因右侧 table 的 scroll ownership 而不可达。
6. 小高度下必须存在清晰、单一的 control-content 垂直滚动路径；具体 Qt container 由 Executor 在读取代码后决定，Static 不预先指定实现类。
7. Tab/Shift-Tab 等键盘 focus traversal 必须能到达滚动区域内的 controls，并在需要时使 focused control 可见。
8. 既有 S2 四项功能、双语 label、模型管理、output location、Start/Stop 和退出行为不得回归。
9. Executor 不得修改本 Static、task Runtime、framework governance 或历史 evidence，不得自行宣告最终 ACCEPT。
10. 不得 force push、merge、tag、release 或 push target branch；target push 由独立 review 后的 Human-facing流程依既有授权另行执行。

## 5. Stable Background and Inputs

### 已确认事实

- Human Owner 已在真实 App 功能黑盒中确认 `session_clipboard_ui_v1` 功能无问题，同时观察到主窗口纵向内容过长并超出窗口限制。
- `fb7e38e4248b1b6fcf58a14193dbfe9315f90f34` 包含已验收实现、target-side change record 和更新后的 repo map，是本任务唯一 baseline。
- 当前主窗口顶层是 status strip 加水平 body；body 左侧是长 controls/session column，右侧是已有自身滚动行为的 transcript/log tabs。
- 已安装的 repo-local `.venv`、`.tools` 和 `external/whisper.cpp` 均为 Git-ignored 本地依赖，可供本任务复用，但不是提交内容。
- 旧 `whisper_session_ui_v1` task 已关闭，不得通过修改其 Static/Runtime 重开。

### 候选输入

- Qt `QScreen.availableGeometry()`、screen change/show/resize event 和 size policy 可作为实现候选；只有实际代码和测试证明后才能成为实现事实。
- 优先让 controls 区域滚动、保持 transcript tables 自身滚动是当前维护建议，不是不可修改的实现命令。Reviewer 应依据最终 event ownership 和用户可达性判断。

### 未知项

- `TO_CONFIRM`: Human Owner 的实际屏幕尺寸、缩放和 Dock/Menu Bar 组合不是固定合同输入；自动测试必须使用多个可注入 geometry，最终真实视觉结论由 Human Owner确认。
- `TO_CONFIRM`: 最终 layout 在真实 trackpad 上的滚动手感只能由 Human Owner 验证；自动测试负责结构、event routing 和可达性，不得代替该结论。

## 6. Authority and Approval

- Human Owner: 修改合同、确认主观布局体验、批准 merge/release/tag 和最终真实视觉结论。
- 1PCloop Reviewer: 读取固定 Static/Runtime、代码、diff、tests 和 artifacts，独立形成代码/模拟 UI verdict。
- Executor: 仅在 Active Step 授权范围内修改 target UI/layout、tests 和必要文档，运行测试并提交一个普通 descendant commit。
- Human Decision Gate: 需要改变功能语义、扩大到 backend/model/session/clipboard、选择需要主观产品取舍的重设计、无法在不隐藏 controls 的情况下满足 geometry、或需要 merge/release 时暂停。
- 普通 target branch push 仅在独立 ACCEPT 后依据 Human Owner 已有自动 push 授权执行；force push 永不授权。

## 7. Permitted and Prohibited Mutations

### 允许

- `ui_app.py` 中与主窗口 geometry、layout、size policy、scroll/focus 可达性直接相关的最小修改。
- `testCodes/` 中针对窗口 bounds、scroll ownership、resize、focus、retranslation 和回归的测试。
- `README.md`、`README.zh-CN.md`、`docs/change_records/`、`docs/repo_map.md` 的必要同步。
- 一个普通 target commit；测试产生的 Git-ignored cache/build/runtime artifact。

### 禁止

- 修改 `transcription_engine.py`、`stream_transcribe.py`、Whisper/runtime/model manifests、transcript content algorithm 或 audio pipeline。
- 修改 `transcription_controller.py`、`transcript_store.py`、settings persistence、Session identity 和 clipboard cursor，除非 Reviewer 先证明现有 UI layout 无法在不改它们的情况下工作并进入 Human Gate。
- 修改 framework 代码、closed workload governance、schemas、roles 或历史 evidence。
- 把 prompt、stderr、raw Agent event、凭据、本机用户数据或测试录音复制进 target Git。
- 删除已安装本地依赖、历史 Session、模型或用户输出。

## 8. Acceptance Criteria

| ID | 验收条件 | 所需 evidence | 通过边界 |
| --- | --- | --- | --- |
| AC-01 | Baseline 和范围正确 | branch、parent、diff、changed-file list、clean status | commit 是 `fb7e38e...` 的普通后继；无范围外文件或 target push |
| AC-02 | 初始窗口不超出可用高度 | 可注入多组 available geometry 的 Qt tests；Reviewer 代码检查 | show 后窗口 frame/client geometry 被安全约束，minimum size 不迫使窗口超过 available height；不依赖单一硬编码屏幕高度 |
| AC-03 | 小高度下 controls 全部可达 | scroll range、最后一个 control 可见性、resize 和 focus traversal tests | 顶部与底部 controls 均能经 scrollbar/滚轮或键盘到达；没有永久隐藏或只能全屏访问的 control |
| AC-04 | 滚动 ownership 清晰 | wheel/scroll event 或等价 state tests，Reviewer 白盒检查 | controls 区域可滚动；Clean/Raw/Logs 自身滚动保持工作；外层不会无条件劫持 table scrolling |
| AC-05 | 动态行为稳定 | resize、screen geometry change、中文/English retranslate、narrow/short geometry tests | 切换语言和调整窗口后 bounds/scrollability 仍成立，关键 label 与内容不被截断到不可操作 |
| AC-06 | 既有功能无回归 | S2 focused tests、相关 UI tests、完整可运行 discovery、UI support checks | session reset、stale-event rejection、path/text copy、Start/Stop、model/output/language 行为继续通过；未运行项必须解释 |
| AC-07 | 文档和 evidence 可维护 | target change record、repo map、绝对测试 artifact locator、hash、commit evidence | 目标仓库能独立理解 layout 设计和限制；framework 保留完整过程 evidence；不复制敏感/raw payload |
| AC-08 | Human 真实 UI gate 明确 | 自动 ACCEPT 后的启动指令和人工 checklist | 自动 Reviewer 不宣告真实 macOS视觉/trackpad PASS；最终任务关闭保留 Human gate |

## 9. Evidence and Privacy Boundary

- Reviewer 必须直接访问固定 Static/Runtime、target commit/diff、修改后的 UI/tests、测试输出文件、branch/HEAD/clean status 和 target change record。
- Evidence 使用完整 commit SHA、文件 SHA-256、绝对 locator 和 1PCloop tracked summary 固定；最终 target-side record 只保留可移植的 commit/run/hash 和紧凑结论。
- Raw Agent events、完整 prompts/process metadata 和本机绝对 locator 可以保留在 framework Git-ignored raw evidence 中。
- 不得提交录音、transcript、模型、用户设置、凭据、剪贴板内容或其他个人数据。

## 10. Change Control

- 本 Static 的任何实质变化都需要 Human Owner 明确授权。
- Runtime 只能推进当前状态，不能改变 window bounds、scroll、回归或 Human gate 的验收边界。
- Task 完成后 Static 默认冻结；新视觉问题使用新的 task-local Static/Runtime。
- 若代码事实、Runtime 与本 Static 冲突，停止 mutation 并输出 `HUMAN DECISION REQUIRED`。

## 11. Open Decisions

- 无阻塞性 Owner decision。具体 Qt scroll container、geometry helper 和 test seam 由 Executor 在合同边界内选择，并由 Reviewer 独立审核。
