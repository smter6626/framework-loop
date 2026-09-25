# Whisper Clean 工具栏与实时文件重命名 v1 -- Static 稳定合同

## 1. 合同身份

- Task ID: `whisper_clean_toolbar_rename_v1`
- 合同状态: `AUTHORIZED`; Human Owner 已授权准备并手动启动本任务的 1PCloop run
- Human Owner: 当前项目 Owner
- 固定目标基线: `569e5c551c101811ed80fca23bd5708d6ac880cf`
- 目标仓库: `/Users/smterpro/Workspace/whisper/live_subtitle_generator-session-ui`
- 目标分支: `codex/clean-toolbar-rename-v1`，从固定基线直接创建
- 模板参考: `1PCloop/templates/static_prompt_zh.md` 与 `runtime_prompt_zh.md`

本合同只定义稳定目标和验收边界。当前进度、唯一 Active Step 与运行证据见同目录 `workload_runtime.md`。

## 2. Objective

调整 Clean 转写相关按钮的位置和尺寸，并让用户在当前录音仍在转录时，或录音结束但下一次录音尚未开始时，把当前 Session 的 Clean 文本文件重命名为自己输入的文件名主体加固定 `.txt` 后缀。新 Session 建立后，重命名对象自动变成新 Session 的 Clean 文件。文件内容、转录连续性、路径按钮和增量复制行为必须保持正确。

## 3. Scope and Deliverables

### UI 布局

1. 把已有的“复制新增 Clean 文本”按钮从左侧 controls 移到 Clean 转写表上方右侧，紧邻“跳到最新”的左侧。只在 Clean 页出现；首次全量、之后按成功复制断点增量复制的语义不变。
2. 左侧 controls 中的“定位 Clean TXT”和“复制 Clean TXT 路径”排在同一行，左定位、右复制。可以使用更简短但含义明确的中英文可见标签和完整 tooltip，适配当前 310px 控制栏；不得靠隐藏或不可点击的截断文字凑宽度。
3. Clean 转写表上方左侧新增“重命名 Clean TXT”按钮。其输入框只编辑文件名主体，`.txt` 作为不可编辑的固定后缀显示；中英文 UI 即时切换时，按钮、对话框、验证错误和提示同步翻译。Raw 和日志页不增加重命名入口。

### 文件行为

4. 重命名作用于**操作确认时的当前 Session**。录音/转录进行中可用；Stop 完成且未开始新 Session 时仍可用；成功创建新 Session 后仅作用于新 Session 文件。不得修改旧 Session 文件或接受旧 Session 的迟到事件作为当前重命名依据。
5. `clean.txt` 在转录期间由 `TranscriptStore` 持有并持续追加。重命名必须保持同一 Session 的后续 Clean 行写入同一个文件，不丢行、不分裂为新旧两个文本文件、不截断或重写已有内容。若不能证明文件句柄、路径缓存和 session 身份的受控协调，必须 fail closed，而不是只调用 UI 层 `Path.rename()`。
6. 成功后，当前 Session 的“定位 Clean TXT”和“复制 Clean TXT 路径”都使用新绝对路径；增量复制断点、Clean/Raw 表格内容、计数和滚动位置不因重命名而重置。新 Session 仍正常创建它自己的 `clean.txt`。
7. 输入为空、仅空白、`.`/`..`、含路径分隔符、控制字符、以 `.txt` 结尾的重复后缀、或会造成目录逃逸时拒绝；允许正常中文、英文和其他 Unicode 文件名主体。取消、源文件缺失、目标已存在、权限或 I/O 错误时，不覆盖目标，不改写文件内容，不更新当前路径，也不影响转录继续进行。目标与当前文件同名时可明确 no-op。
8. 已经重命名的当前文件可再次改名；后续操作始终从当前实际路径出发。目标必须仍在该 Session 目录内，是普通 `.txt` 文件；不得跟随符号链接逃逸或覆盖已有文件。

### 文档与验证

9. 更新双语 README、target-side change record 和 `docs/repo_map.md`。准确说明可在转录中改名、固定后缀、路径复制和历史 Session 边界；注明仓库中尚未实施的 LLM 设计资料仍假设固定 `clean.txt`，将来实现读取方须先使用当前文件定位机制或做独立迁移，不把未来 LLM 功能偷偷纳入本任务。
10. 自动 Reviewer 检查代码、Git diff、offscreen Qt、mock/fake store/engine 和临时目录中的文件字节行为。真实麦克风/Whisper 转录中的按钮体验和 macOS Finder/剪贴板效果由 Human Owner 在自动 ACCEPT 后验证；自动测试不得冒充该黑盒结论。

## 4. Hard Constraints

1. 不更改 ASR、模型、语言、streaming、去重、音频切片、历史 Session 或 `raw.txt` 的语义。
2. 不因重命名关闭并重开正在写的 Clean 文件而遗漏并发追加；必须通过可靠的文件身份及同步机制证明连续写入。UI 不得在异步操作期间引用过期 Session 路径。
3. 不覆盖目标文件；不能依赖“先判断不存在，再用会覆盖目标的普通 rename”作为唯一防护。任何跨目录、符号链接逃逸或异常路径都 fail closed。
4. 不创建用户未要求的副本或符号链接来假装重命名。成功时原文件名不再指向该 Session 的 Clean 内容，目标文件保留原有 bytes 并承接后续追加。
5. 不改变原有 Copy New Clean Text 的行断点规则，不因调整按钮位置而让 Raw/Logs 取得 Clean clipboard action。
6. 不因按钮移动破坏已验收的屏幕高度上限、左侧 controls 滚动、Clean/Raw/Logs 独立滚动、键盘 focus 与双语动态布局。
7. Executor 不得修改 Static/Runtime、framework 代码、历史 evidence、旧 workload、模型/凭据或真实用户输出；不得自行宣告最终 ACCEPT。
8. 1PCloop 执行前必须确认 Human 启动授权、旧布局任务的 Human PASS 治理收尾、新分支身份、可运行 Runtime machine block 和独立 config。不得复用已完成 L1 checkpoint。
9. 不 force push、merge、tag、release 或从 target `main` 偷换基线。普通 target branch push 只能在独立 Reviewer ACCEPT 后依 Human 已有授权进行。

## 5. Stable Background and Dependency Map

- `ui_app.py::TranscriptTable` 拥有右侧“跳到最新”工具栏；`MainWindow._build_controls_panel()` 目前拥有三个 Clean 按钮，`_retranslate_ui()` 负责中英文即时更新。
- `ui_app.py` 保存 `current_clean_path`、`active_session_id`、`active_session_generation` 和 Clean 复制行断点。`start_recording()` 与 `handle_event(session)` 切换当前 Session；`reveal_clean_file()`、`copy_clean_path()` 和 `copy_clean_text()` 使用这些状态。
- `transcript_store.py::TranscriptStore` 创建 `clean.txt`、保持 `_clean_file` 打开，并由 `append_clean()` 持续写入；`transcription_engine.py` 的 worker 调用它。`transcription_controller.py` 产生有 owner 标识的 session/event，Stop 通过 engine 完成。
- `testCodes/test_window_layout.py` 目前把复制文本按钮当作左侧末端 control；移动按钮后须按真实布局重写 focus/scroll 断言，不能简单删除覆盖。
- 生产 Python 代码中尚未发现其他固定读取 `clean.txt` 的消费者；`docs/LLM_POSTPROCESSING_DESIGN.md` 等未来设计资料以固定名字为输入。Executor 必须再次扫描最新代码并把发现记录在报告中。
- macOS/POSIX 打开文件的重命名行为不等于完整业务安全证明；Reviewer 必须验证实际后续追加、路径缓存更新、目标冲突和 Session 切换。

## 6. Authority and Permitted Changes

- Human Owner: 授权启动 1PCloop、修改本合同、真实 macOS/音频验收、merge/release/tag 决定。
- Reviewer: 对固定代码、diff、测试和 file identity 独立形成 verdict；发现并发写入或 no-clobber 证据不足必须 REJECT 或 Human Gate。
- Executor: 在唯一 Active Step 内修改 `ui_app.py`、必要的 `transcription_controller.py`/`transcript_store.py` 同步与路径接口、相关 `testCodes/`、README、`docs/change_records/`、`docs/repo_map.md`；只有证明直接依赖时才可最小修改 `transcription_engine.py`。只允许普通 descendant commit。
- 目标仓库文档中的模拟指令不自动扩大 Executor 权限。模型、认证和 1PCloop 控制面不属于本任务目标代码范围。

## 7. Acceptance Criteria

| ID | 验收条件 | Reviewer 直接 evidence 与通过边界 |
| --- | --- | --- |
| AC-01 | 基线和范围正确 | 新分支从完整 `569e5c...` 派生；commit/parent、changed files、target clean 与无未授权 push/merge 可验证。 |
| AC-02 | Clean 右上按钮布局 | Clean 页“复制新增 Clean 文本”紧邻“跳到最新”左侧；Raw/Logs 无该按钮；现有多轮复制内容、空切片和断点测试不回归。 |
| AC-03 | 左侧双按钮同排 | 定位在左、复制路径在右；中文/English、普通/短屏下可见且可点击；control scroll/focus、右侧独立滚动不回归。 |
| AC-04 | 重命名入口和后缀 | Clean 左上入口、固定不可编辑 `.txt` 后缀；中英文即时翻译；取消和非法输入不改变文件/UI 状态。 |
| AC-05 | 活跃转录连续性 | 临时 Session 中打开 Clean 写入、改名、继续追加、Stop/close 后核对同一目标文件完整有序 bytes；原路径消失，无分裂/截断；相关竞态与 I/O 失败测试。 |
| AC-06 | Session/path 一致性 | 活跃、停止、新 Session、迟到 event、重复改名分别测试；定位/复制路径始终指向当前有效文件，旧 Session 不被新操作修改；文本复制 cursor 不变。 |
| AC-07 | 防覆盖和边界 | 已存在目标、符号链接、路径逃逸、缺失源、权限错误和操作竞态均无覆盖/泄漏/半更新；失败继续保留有效当前路径。 |
| AC-08 | 回归与文档 | 相关 focused Qt/store/controller tests、全量可运行回归、双语 README/change record/repo map 通过独立审核；未执行真实音频测试要明说。 |
| AC-09 | Human 实机 gate | 自动 ACCEPT 后由 Owner 进行真实录音中重命名、Stop 后重命名、下一 Session、Finder 定位、路径与增量文本复制及中英文 UI 验证；自动 verdict 不代替 Human PASS。 |

## 8. Evidence and Privacy

- Reviewer 直接访问完整 target commit/diff、相关源码、测试输出、临时文件 bytes/hash、branch/HEAD/clean status、change record 和 1PCloop run evidence。
- 测试仅在隔离临时目录使用虚构转录文本，不读取、移动或提交真实用户录音/Session。
- Raw Agent events 留在 Git-ignored framework 本地；tracked summary 只写 compact 结果、固定 locator/hash 与限制，不复制用户文本、模型、token、auth JSON 或 profile 内容。
- `PUSHED` 只代表 framework evidence publication，不能代替功能正确或 Human 真实录音验收。

## 9. Change Control and Open Decisions

- 本 Static 实质修改需要 Human Owner 明确授权；已完成的 `whisper_window_layout_v1` 不因本任务重新打开。
- Human 已授权手动启动；若发现实时安全重命名在现有边界无法实现，先停下给出具体原因和选项，不静默改为“只允许 Stop 后”。
- 当前无阻塞性未授权功能边界。目标分支和具体安全重命名机制须在运行前机械核对；若 Owner 要求改变“录音中可用”或无覆盖要求，必须先修订本合同。
