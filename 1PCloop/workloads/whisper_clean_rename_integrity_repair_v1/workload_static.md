# Whisper Clean 重命名路径身份修复 v1 -- Static 稳定合同

## 1. 合同身份与权威

- Task ID: `whisper_clean_rename_integrity_repair_v1`
- 合同状态: `AUTHORIZED FOR PREPARATION`; 1PCloop 启动仍需 Human Owner 单独确认
- Human Owner: 当前项目 Owner
- 目标仓库: `/Users/smterpro/Workspace/whisper/live_subtitle_generator-session-ui`
- 目标分支: `codex/clean-toolbar-rename-v1`
- 修复基线: `352e62b2bf3cd3690e8eee57cb2e933f1405c6af`，必须是后续修复提交的祖先
- 上游稳定合同: `1PCloop/workloads/whisper_clean_toolbar_rename_v1/workload_static.md`，其 AC-05 至 AC-09 继续约束本修复；本合同不得静默缩小它
- 初始化依据: 2026-09-25 本对话独立 Reviewer 对上游 AC-07 的可复现 REJECT，以及 Human Owner 要求写修复流程文档

本文只规定新的有界修复目标、不可变边界和验收条件，不记录运行进度或继承旧机器 ACCEPT 作为修复 verdict。

## 2. Objective

消除当前 Clean 文件已经完成原子改名、但目标目录项在事后验证前被外部替换时，应用把另一个文件误认成当前 Clean 文件的缺陷。转录写入句柄、`TranscriptStore.clean_path`、UI 当前路径和“定位/复制 Clean 路径”必须保持同一受验证文件身份；不能把同名的 `decoy` 文件作为成功或可用路径暴露。

本任务只修复这个路径身份与失败处理缺口，并保留已实现的 UI 布局、双语、实时/Stop 后重命名、原子无覆盖、Session owner、历史 Session、增量复制及其它原合同语义。

## 3. 修复范围

- 检查 `transcript_store.py::TranscriptStore.rename_clean()` 成功的 no-replace 系统调用之后、后续 `lstat()`/身份验证失败时的路径状态，以及 `ui_app.py::MainWindow.rename_clean_file()` 对相关结果的处理。
- 如确有必要，最小调整 `transcription_controller.py` 的当前 Session 路径接口；不复制状态机或改变 Session 编号。
- 在 `testCodes/test_clean_rename.py` 等相关测试中注入真实文件操作：改名提交后把目标文件移到同一临时 Session 的另一路径，再在目标名创建另一个普通文件；检验写入句柄 inode、后续追加、Store/UI 缓存路径、Finder 定位和路径复制的一致性。还要覆盖同名符号链接或目标消失等可区分情况。
- 必要时同步双语 README、`docs/change_records/clean_toolbar_rename_v1.md` 和 `docs/repo_map.md`；文档必须反映真实的可恢复与 fail-closed 边界。
- 可以使用临时目录和虚构转录文本；不得改动、读取或移动真实用户 Session。

## 4. 硬约束

1. 不修改或删除旧 run `20260925T061052Z-27529` 的 Reviewer ACCEPT、机器 Runtime transition、framework evidence commit 和 raw/tracked evidence。后续独立 REJECT 是对旧 acceptance claim 的显式 invalidation，不是对历史记录的改写。
2. 不用已完成 W1 的 `workload_retry_01.json` 执行 `resume` 或新 `run`。后续 1PCloop 修复须用独立 task-local Runtime、config、state root 和新的 run ID，绑定启动时的 Codex Mix active account。
3. 不使用可能覆盖既有目标文件的普通 rename、copy、link 或 symlink 来掩盖缺陷；成功改名和后续写入仍须保持同一 Clean 文件身份。
4. 不能把未经文件身份验证的候选路径设为可用的 `clean_path`，也不能让“定位/复制路径”指向外部放入的同名文件。错误提示不能误称改名已安全完成。
5. 若原 Clean inode 已被外部移动到无法安全定位的地方，或在可验证范围内不能同时满足原合同“失败后路径有效”和持续写入，不得凭猜测选择路径或静默缩小原 AC-07；进入 `HUMAN DECISION REQUIRED`，说明事实和可选边界。修复任务不能自行把“当前路径有效”改成“随意不可用”。
6. 不改变 Whisper/ASR、音频、模型、语言识别、转录文本内容、Raw/Logs、Session 创建/Stop、增量复制断点或已验收的窗口滚动功能。
7. Executor 不得修改 framework Static/Runtime、凭据、历史 evidence、退休 `.codex-A`/`.codex-B` 或真实用户数据；不得自行宣告独立 ACCEPT。
8. 修复只能形成当前 target 分支上的普通后继提交；不得 force push、merge、tag、release 或在独立审核前推送 target 分支。

## 5. Authority 与启动边界

- Human Owner: 授权启动受控修复 run、改变原合同、判断无法机械解决的外部 mutation 支持边界、完成真实 macOS/录音 Human gate、决定 merge/release。
- 1PCloop Reviewer: 独立查看确切 target commit、源码、失败复现、测试输出和身份链，形成新修复 verdict；不能继承旧 run 的 ACCEPT。
- Executor: 只在新 Runtime R1 激活后改动第 3 节限定的 target 文件，运行测试并提交普通后继 commit。
- 当前仅授权创建治理准备文档。本 Static 不自动启动 Agent、不授权修改原任务机器块，也不把独立修复结论预写为 PASS。

## 6. Acceptance Criteria

| ID | 条件 | Reviewer 必须直接取得的 evidence | 通过边界 |
| --- | --- | --- | --- |
| R-AC-01 | 基线与历史完整 | 分支、完整 target HEAD/parent/diff，旧机器块和 run hashes | 修复 commit 为 `352e62b...` 的普通后继；旧 ACCEPT/REJECT/evidence 都保留；没有 target push/merge |
| R-AC-02 | 可复现缺陷被阻断 | 在临时目录真实移动原目标文件并放入同名 decoy 的失败注入，Store/UI 路径和 inode/bytes 检查 | 从任何公开路径操作都不能定位或复制 decoy 为当前 Clean；正确文件中的 `before/after` 连续且未分裂 |
| R-AC-03 | 成功和普通失败不回归 | 活跃追加、Stop 后、重复重命名、冲突目标、权限和验证 I/O 错误矩阵 | 正常成功保持路径/写入句柄同一身份；失败不覆盖目标、不截断文本、不丢行；原合同 AC-05/06/07 继续成立 |
| R-AC-04 | UI 与 Session 一致 | 中英文、当前/新/旧 Session、Finder 和路径复制的模拟 UI 测试 | UI 不缓存未经证实的路径；旧 Session 迟到事件不污染当前会话；原复制断点和窗口布局不回归 |
| R-AC-05 | 异常无法机械恢复时停机 | 无安全可定位路径的注入与控制面处理路径 | 不猜测 inode 所在路径，也不偷偷放宽原 Static；给出 Human Decision Gate 和安全证据，不把不确定状态判为 ACCEPT |
| R-AC-06 | 回归、文档与最终交接 | focused 测试、完整可运行回归、target 文档、`git diff --check`、独立 Reviewer 白盒结论 | 所有当前范围的证据充分；真实音频/macOS Human gate 明确保留，不由自动测试替代 |

## 7. Evidence 与隐私

- 直接证据必须包括完整 commit SHA、文件身份/bytes 测试结果、测试命令与输出定位、Git clean 状态、Reviewer 对反例的独立判断。
- 原失败复现可以在本地临时目录重复，但不得使用真实录音或真实用户 Session；tracked summary 只保留紧凑证据和 locator，不收录音频、私有转录、凭据或 raw Agent 输出。
- 原 run 的 framework `PUSHED` 只证明证据发布，不证明本修复通过，也不授权 target push。

## 8. Change Control

- 修复尝试不能把原任务 Static、已完成机器 transition 或历史 Reviewer verdict 当作可改文本。若判断合同边界需要缩小，先请 Human Owner 明确选择并记录授权；在此之前维持独立 REJECT。
- 独立 Reviewer 对新修复 ACCEPT 后，才可依既有自动 push 授权普通推送 target 分支；之后仍须 Human 对真实录音中改名、Stop 后改名、新 Session、Finder、clipboard 和双语界面作黑盒验收。
- 本 task 完成后冻结；后续 feature 不加入 R1。
