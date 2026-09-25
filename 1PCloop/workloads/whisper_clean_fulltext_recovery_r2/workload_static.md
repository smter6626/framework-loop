# Whisper Clean 全文恢复 R2 -- Static 稳定合同

## 1. 合同身份与 Human 决定

- Task ID: `whisper_clean_fulltext_recovery_r2`
- 合同状态: `AUTHORIZED FOR PREPARATION`; 启动 1PCloop run 仍须 Human Owner 另行授权
- Human Owner: 当前项目 Owner
- Target: `/Users/smterpro/Workspace/whisper/live_subtitle_generator-session-ui`
- Target branch: `codex/clean-toolbar-rename-v1`
- 固定 R2 基线: `b62ef6947d6a634c56e695740e4ea446751e6c79`；任何 R2 实现提交须为其普通后继
- 上游合同: `1PCloop/workloads/whisper_clean_toolbar_rename_v1/workload_static.md`；R1 合同和 Human Gate 见 `1PCloop/workloads/whisper_clean_rename_integrity_repair_v1/`

Human Owner 在 2026-09-25 本对话中决定：当当前 Session 的 Clean 文件在原 Session 目录中无法安全定位时，提供带明确风险说明的“是/否”选择。“是”在原 Session 目录创建用户指定的 `<inputString>.txt`，其中必须包含截至切换点的完整 Clean 转录内容，后续行继续写入该新文件；“否”不创建新文件，当前录音/转录继续。Human 同意不能仅靠 UI 表格重建精确全文，并认可 Store 层受控恢复方向。

本合同显式细化旧 AC-07 的外部 mutation 例外：应用内正常重命名与可定位失败仍须保持原文件身份和有效路径；原文件被外部移动/删除而无法在 Session 内定位时，不得猜测旧路径或误认 decoy，改用本合同的恢复选择。任意不合作的外部进程可以在检查后再次移动文件，本任务不承诺无锁的永久路径有效性。

## 2. Objective

在原 Session 目录中的 Clean 文件路径失效时，让用户选择安全恢复或保持现状。选择恢复后，新 `<stem>.txt` 必须包含该 Session 截至确认切换时的完整、原格式 Clean 内容；活跃转录随后只向新文件追加，不丢行、不重复、不覆盖其它文件。Stop 后、尚未开始新 Session 时也能生成相同的完整文件。正常重命名、R1 的 decoy 防护、现有 UI 和其它 Session 行为不回归。

## 3. 行为合同

1. 只对操作确认时的当前 Session 生效。新 Session 建立后，旧 Session 的对话框、迟到事件或文件状态不得改变新 Session 的文件。
2. 只在可靠检查确认原 Clean writer 在原 Session 目录内没有可验证的普通文件路径时显示恢复确认。权限错误、读取失败、Session 目录身份不符或其它无法判定状态不得伪装为“文件已消失”。文案说明“原 Session 路径不可用”，不声称文件内容已被删除；显示的是原路径提示，不是 decoy 的有效路径声明。
3. “是/Yes”：使用已输入且通过原文件名规则的主体，在经身份验证的原 Session 目录中生成固定 `.txt` 后缀的新文件。内容必须等于 Store 已实际写入的该 Session 全部 Clean 字节；不能从经过解析、可能排队或缺行的界面表格推测。活跃转录中，完整复制与 writer 切换必须同后续 append 串行化；Stop 后须仍有经过验证的精确内容来源。新文件形成并验证后才发布新路径。原外部文件若仍存在，不移动、不覆盖、不删除。
4. “否/No”：不创建、不重命名、不切换文件，活跃转录继续使用已有的打开句柄；Stop 后不再追加。界面须明确提示当前 Session 内没有可验证的 Clean 路径，继续写入不等于已安全保存；若旧文件实际上已被 unlink，App 退出或句柄关闭后内容可能无法找回。Finder、路径复制和成功提示不得把失效路径或 decoy 当作有效文件。用户在同一 App 会话内再次请求恢复时，应可重试；若精确内容已无法取得，则 fail closed。
5. 若目标 `<stem>.txt` 已存在、为符号链接、出现权限/磁盘/I/O 错误或 Session 目录身份不再可信，绝不覆盖既有条目，不发布部分文件为成功结果，也不切换 writer；应清楚报错并允许选择其它合法文件名。临时中间文件须受控清理，不能冒充最终文件。对旧文件被外部原地篡改、恶意并发再次移动等无法证明的情况，不猜测“全文已恢复”。
6. 正常路径下继续沿用 R1 的原子无覆盖、同 inode 重命名语义。仅 Human 明确选择“是”后的异常恢复允许生成新文件身份和完整内容副本；这不是普通重命名的静默降级。

## 4. 范围与不可变边界

- 可改 target 的 `transcript_store.py`、必要的 `transcription_controller.py`、`ui_app.py`、直接相关 `testCodes/`、双语 README 和精确 change record/repo map。只有证明直接依赖时才最小改动 `transcription_engine.py`。
- 不改 Whisper/ASR、模型、音频采集、Raw/Logs、去重、Session 创建/编号、复制新增文本断点、已验收的布局/滚动或真实用户 Session。
- 不读取、移动或覆盖真实用户录音/输出；测试使用自动清理的临时 Session 和虚构文本。
- 不改旧 W1/R1 的 Static、Runtime 机器块、Reviewer verdict、checkpoint、raw/tracked evidence 或 Git 历史；不把 R1 的 `HUMAN_GATE / NOT_APPLIED / PUSHED` 改写为 ACCEPT。
- 不改 framework runner、角色配置、认证材料、`.codex-A`/`.codex-B`。不 force push、merge、tag、release；target feature branch 只在新的自动审核和本对话独立审核均通过后，依现有授权普通推送。
- R2 是新 workload，使用自己的 Runtime/config/state root/run ID。旧 W1/R1 的终态不得 resume；R1 的 Human Gate 是本合同的输入，不是新任务的 acceptance。

## 5. Acceptance Criteria

| ID | 验收条件 | Reviewer 需直接检查的证据与通过边界 |
| --- | --- | --- |
| R2-AC-01 | 基线和历史不变 | target `b62ef694...` 为祖先、新提交普通后继且工作树 clean；旧 W1/R1 run、机器块、verdict、evidence 原样保留；无 target push/merge。 |
| R2-AC-02 | 确认对话框正确 | 仅已验证的当前 Session 路径缺失触发；中英文“是/否”、原路径提示、全文恢复与“否”的保存风险清晰；不把 I/O 不确定性称为文件消失；取消或过期 Session 不改变文件。 |
| R2-AC-03 | 活跃转录全文恢复 | 在临时 Session 中先写 Unicode、时间戳等真实格式行，再外部移走/删除路径，点“是”后新文件字节等于截至切换点全部已提交 Clean 字节，之后 append 顺序正确、无重复/丢失；不靠 UI 表格作权威来源。 |
| R2-AC-04 | Stop 后全文恢复 | Stop 关闭 writer 后、下一 Session 前，仍可从可信精确快照生成相同全文；新 Session 之后不触碰旧文件；App 已失去可信全文来源时 fail closed，不谎称完整。 |
| R2-AC-05 | “否”和错误路径 | 点“否”不创建或切换文件，活跃转录继续，但 UI 显示路径不可用和风险；Finder/复制路径不输出 decoy；可在同一 App 会话重试。冲突目标、符号链接、权限、空间不足、复制或切换失败均不覆盖、不发布部分成功、不丢行。 |
| R2-AC-06 | 正常重命名及回归 | 同 inode 正常重命名、R1 同目录 move+decoy 处理、Session/复制断点、双语、布局保持；focused 测试、完整可运行严格回归、`git diff --check`、文档及独立白盒审核通过。真实麦克风、Finder 和剪贴板体验留给 Human Owner 后续黑盒验收。 |

## 6. Authority、证据与变更控制

- Human Owner 决定合同修改、新 run 启动、真实 macOS/音频验收、target 集成及 release。本文只授权准备；创建可执行机器块或调用 Agent 须再次取得明确启动授权。
- 1PCloop Reviewer 须独立检查源码、目标 commit、临时目录中的精确字节/文件身份测试和失败矩阵；Executor 的全绿报告不是最终 verdict。本对话在机器 ACCEPT 后还要做独立 evidence-sufficiency 复核。
- Evidence 可保留在 Git-ignored 本地 run 目录；tracked summary 只写紧凑结果、locator/hash，不复制私有转录、真实音频、prompt raw 或凭据。
- 如无法保证“是”后的精确全文和原子 writer 切换，或“否”的风险无法明确呈现，必须停止并请 Human 决定，不得宣告 R2 完成。
