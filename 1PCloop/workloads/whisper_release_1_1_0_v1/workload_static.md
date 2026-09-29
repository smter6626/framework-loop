# Whisper 1.1.0 发布自动化 -- Static 稳定合同

## 1. 合同身份与授权

- Task ID: `whisper_release_1_1_0_v1`
- 合同状态: `AUTHORIZED`
- Human Owner: 当前项目 Owner。
- 任务治理目录: `/Users/smterpro/Workspace/framework-loop/1PCloop/workloads/whisper_release_1_1_0_v1/`
- 产品仓库: `smter6626/live_subtitle_generator`。
- 当前功能源码工作区: `/Users/smterpro/Workspace/whisper/live_subtitle_generator-session-ui`。
- 模板: `/Users/smterpro/Workspace/framework-loop/1PCloop/templates/static_prompt_zh.md` 与 `runtime_prompt_zh.md`。

Human Owner 于 2026-09-29 在本对话确认下列发布方案，先审阅 Static/Runtime，随后明确授权 "可以，现在开始执行，你来负责启动+监控，完成后你也再做一次验证；然后我来验收"。本文已获批准，授权通过启动 gate 后执行自动化部分并停在最终 ZIP 的 Human 黑盒验收；未取得该 artifact 的 Human PASS 前仍不得创建真实 tag/draft、上传或发布。

## 2. 用人类语言说明目标

让 1PCloop 把已经验收的 Whisper 新功能真正交付成用户可下载的 1.1.0 App。它负责发布工具实现、独立审核、源码集成、正式构建、自动验证、上传和远端复核；Human 只承担最终 ZIP 中 App 的真实黑盒验收，以及异常时必须由 Owner 决定的事项。

最终必须证明：发布页面、Git tag、源码 commit、App 内版本和下载 ZIP 是同一条可核对的交付链。不能把 "源码测试全绿"、"进程退出成功"、"证据已 push" 或 "Release 页面已出现" 单独当作发布成功。

## 3. 已确认的发布身份

| 项目 | 固定值或合同 |
| --- | --- |
| 产品版本 | `1.1.0` |
| Git tag | `1.1.0`，不添加 `v` |
| Release 标题 | `Classroom Transcriber 1.1.0` |
| GitHub repo | `smter6626/live_subtitle_generator` |
| 发布类型 | 正式版，非 prerelease；成功后作为最新正式版本 |
| 平台 | macOS Apple Silicon / arm64；不增加 Intel、Universal2、Windows |
| 主资产文件名 | `ClassroomTranscriber-1.1.0-macOS-AppleSilicon.zip` |
| ZIP 主内容 | `ClassroomTranscriber.app`；模型仍由 Model Manager 下载/导入，不内置 |
| 签名路线 | 沿用 ad-hoc；明确未 Developer ID 签名/未公证的限制与标准 GUI 打开方式 |
| 发布说明 | 中英双语，说明新增功能、修复、模型外置及已知限制 |
| 构建源码 | 审核后集成到 `main` 的固定完整 commit；具体 SHA 由集成 evidence 决定，不猜测 |
| 人工 gate | 验收最终 ZIP 解压的 App；通过后仅发布该份已验收 ZIP |

允许的主资产只有上述 ZIP；紧凑 checksum/source metadata 可写入 Release notes 和 framework evidence，不默认增加其它下载资产。

## 4. 范围、交付物与非目标

### 范围内

- 完整保留并集成已接受的多语言、Session 显示重置与增量复制、Clean 路径复制、窗口高度/滚动、Clean 工具栏与重命名、R2 全文恢复；不得遗漏现有 `main` 的 streaming 治理文档整理结果。
- 用 1PCloop 普通 Reviewer/Executor loop 实现、测试和审核 workload 专用发布工具及必要的版本/打包改动。
- 补齐发布流程编排：把 implementation acceptance、integration、build、Human gate 和 publication 串成受控 workflow；不是助手在循环外逐条手工完成后声称 "1PCloop 已发布"。
- 同步 `pyproject.toml`、锁文件项目元数据及正式 App 版本来源。`CFBundleShortVersionString` 和 `CFBundleVersion` 均为 `1.1.0`；ZIP/tag/notes 版本与其一致。禁止把 runtime manifest 的 `schema_version` 当作产品版本修改。
- 在固定源码上使用现有正式构建链，新建 App/ZIP，复用 packaged Runtime 与 ZIP round-trip 验证；增加可靠 source/build/artifact 绑定及恢复记录。
- 独立审核接受后，由受控发布流程完成普通 target push、集成、tag、draft/upload/publication、下载比对及治理收尾。
- 更新双语 README、PACKAGING 及必要技术说明，修正 "历史 clean-machine 验收未完成" 等漂移，明确历史验证和本次新 artifact 验证的区别。

### 交付物

1. 经独立审核的发布实现、相关测试、可读操作说明和中英发布说明。
2. 仅记录安全字段的本地发布状态/恢复记录，绑定源码、版本、产物 size/hash、人工决定和远端对象身份。
3. 固定源码构建的最终 ZIP、自动验证结果及 Human 可操作的验收流程。
4. 正确 tag、正式 Release、远端下载字节核验、准确的当前 README 和 task-local closure evidence。

### 非目标

不实现新 ASR/LLM/UI 功能、跨重启 current-Clean resolver、GUI 发布管理器、GitHub Actions、DMG、Developer ID、公证、付费服务或新的跨平台支持；不重新激活 P7，不重开已关闭的 foundation/R2，也不重写旧失败与审核历史。

## 5. 稳定工程边界与执行主体

### 普通 Agent loop 与发布 workflow 分工

- 普通 runner 仍是 `/Users/smterpro/Workspace/framework-loop/1PCloop/scripts/run_mutation_loop.py`。Reviewer 只读；Executor 只在固定 target branch 实现并创建普通后继提交，不 push、不 merge、不切分支、不打 tag、不调用真实 Release API，不写治理文档。
- 本合同不覆盖 runner 的禁止项，也不授权为本任务放松普通 mutation 审核。发布工具的实现和真实发布副作用必须分离。
- 新的受控发布 workflow 是 workload 专用控制程序，不是获得任意 shell 权限的 Agent。只有已接受的实现及其固定工具身份可运行，阶段前验证当前批准合同、对应独立审核和精确输入；Reviewer 的 `ACCEPT` 不能自动等于整个 Release acceptance。
- 原则上发布工具及编排入口放在产品仓库的 `scripts/`，复用 1PCloop 的既有 implementation loop、evidence 和 Human gate。具体接口由实现阶段提出并接受独立审核。若证明必须改 framework runner/权限/认证模型，本合同不授权直接修改，须先提交有边界的扩展方案给 Owner。
- 受控程序不能解释 LLM prose 直接生成任意远端命令；repo/ref/version/title/asset 采用明确 allowlist。实现测试使用 mock 或 disposable local Git，不接触真实 Release。
- 本对话的助手承担启动/监控、独立复核和记录 Human 决定，不代替 Human 操作麦克风或自行生成 Human PASS。

### 源码集成与工作区

- 以已接受功能分支为实现基线，在新 `codex/` 发布准备分支工作，不从旧 main 丢失功能重新开始。
- 集成前固定预期 feature/main refs，验证 clean、remote identity 与祖先关系。必须同时保留功能与 main 历史；不得通过 reset、rebase、force push、随意 cherry-pick 或丢弃文档解决分叉。
- 集成在受控隔离 clone 中进行，保留现有三个用户 worktree，不切换/覆盖它们。单 writer 顺序运行；若出现不能机械证明的冲突或未预期远端漂移，停止报告，不任意合并。
- 构建在最终接受并集成的精确 commit 上进行，正式 Python/uv/whisper pin 不随版本更新漂移。不借用来源不明旧 `dist` App；必须有可独立核验的 fresh-build 绑定证据。
- 测试/集成/下载验证目录位于 `/Users/smterpro/Downloads/` 下的独立临时目录，精确路径在创建后记录；不操作用户真实 Session、模型库和旧 App。新建 clone 的受控构建产物可按既有脚本清理，不能用宽路径清理其它工作区。

### 版本与文档事实

- 产品版本一致性调整可更新锁文件中的本项目版本；第三方依赖 pin、artifact hashes、whisper commit 不得顺带升级。使用固定工具生成/核验锁文件，不把手改依赖当作 "仅改版本"。
- 集成/build 前文档应准确描述 1.1.0 的候选状态，不能提前声称已发布。Release 发布核验后再同步当前下载入口；后续 docs-only commit 不改变已固定 tag/source/artifact，不为文档重新构建发布包。
- 保留原 bundle identifier、麦克风权限声明、模型完整性合同、现有录音/Store/UI 行为。源码验收与新 ZIP 黑盒验收分别记录。
- 当前硬件/macOS 支持声明不得因本次构建自动扩张；旧 M4 Max/M5 验证是历史 evidence，不是 1.1.0 在所有机器上的新验收。

## 6. Human gate 与外部操作权限

本文经 Owner 审阅批准并授权开始后，预授权受控程序在对应门禁通过时执行范围内的普通 feature/main push 和集成；最终 Human 明确对固定 artifact 报告 PASS 后，才允许创建/推送新 `1.1.0` tag、创建 draft、上传、转正式版并标为 latest。此阶段不需逐条重复审批，但前置证据缺一不可。

发布之前必须取得具体 `source_commit + ZIP SHA-256 + exact bytes + 验收目录` 的 Human 决定。Agent/test fixture/程序进程成功不能写出有效 Human PASS；只能由可信控制路径引用本对话明确决定并固定对应 artifact，不能让普通 Executor 替 Human 写批准记录。

Human 验收 FAIL 或任何改码、重建、ZIP bytes 变化，使原 artifact 的通过结论不再适用于新产物。回到有界 repair/build/review，保留旧结果，新产物重新验收。不在 Human PASS 前创建真实 tag/draft 或上传候选资产。

出现签名路线改变、产品行为改变、集成冲突、版本/tag/asset 冲突、凭据或 repo identity 不确定、无法证明 Human 授权、需要覆写历史对象时，进入 Human gate，禁止猜测继续。

## 7. 发布与恢复硬约束

1. Tag 精确绑定已验收构建源码；同时验证远端 tag 及 annotated tag 的 peeled commit，禁止只比较 tag 名。
2. 不覆盖/删除旧 `1.0.0`、`0.2.0`、`v0.1.0` 或其它历史 tag、Release、资产；不用 force、asset clobber、覆盖同名 ZIP。
3. 每个副作用前持久记录阶段意图和固定 identity，完成后核验实际状态。网络中断/未知 API 结果先读远端对账，不能盲目再建对象或把失败记成功。
4. 同版本对象存在时，只有经过验证的本任务恢复记录及精确匹配的 repo/tag/source/release ID/asset ID/bytes/hash/notes 才允许幂等继续；陌生、字段冲突或内容无法证明的对象 fail closed。
5. Human PASS 后验证本地 ZIP 未变，再上传同一 artifact；远端重新下载到新目录，与已验收 ZIP 大小及 SHA-256 完全一致。公开前尽可能核验 draft 资产，公开后再次核验公开 metadata/tag/asset。
6. 发布状态、实现 loop 的 logical outcome、Runtime transition、evidence publication 分开保存和显示；framework evidence `PUSHED` 不证明产品 Release 成功。
7. 发布流程只可写指定 repo 的指定分支、新 tag/Release，以及本任务管理的本地路径。单 writer/无并发一致性承诺，阶段间与 resume 时重新验证关键 identity。
8. 恢复不自动换模型/额度账号，不回放已完成 Agent turn、integration、Human gate 或 upload。不同 implementation run 可绑定当时新 active account；同一 run 内仍固定原账号。

## 8. Acceptance Criteria

| ID | 验收条件 | Reviewer 直接 evidence 与通过边界 |
| --- | --- | --- |
| REL-AC-01 | 工作流和权限真实成立 | 工具源码、调用链、普通 Agent 限制、固定输入和阶段 gate 测试；真实副作用只由被接受的受控程序执行，没有放宽普通 runner 或把人工命令包装成 loop 成功。 |
| REL-AC-02 | 版本一致 | project/lock/App plist/ZIP/tag/notes 的真实值一致为 `1.1.0`；依赖 pin 与 manifest schema 不被误改；版本不匹配必须阻止发布。 |
| REL-AC-03 | 集成完整安全 | 精确 before/after refs、两边祖先与 tree/diff、集成后回归、clean 状态、普通 push receipt；包含已验收功能和 main 文档，不丢提交或改变用户 worktree。 |
| REL-AC-04 | fresh build 与包完整 | 固定 source、正式锁定环境、构建绑定记录、Runtime verifier、ZIP boundary/CRC/bytes/mode/symlink round-trip、解压 App 再验；旧 dist/dirty source/source drift 必须拒绝。 |
| REL-AC-05 | Human gate 真实且绑定 | Human 明确的最终 ZIP PASS、artifact size/hash/source、解压目录与验证范围；缺批准、伪造 self-report、换包或重建不能发布。 |
| REL-AC-06 | 发布对象正确 | `1.1.0` 远端 tag 与源码一致；标题/正式/latest/中英 notes 正确；唯一主 ZIP asset，公开下载 size/hash 精确相等；无历史 overwrite。 |
| REL-AC-07 | 失败恢复无重复副作用 | 覆盖 build 失败、gate 拒绝、upload 中断/结果不明、已有同名对象、remote drift、篡改状态/hash 的注入；只能证明安全恢复或明确暂停，不盲目 retry。 |
| REL-AC-08 | 文档准确及隐私 | README/技术说明发布前后状态与 evidence 一致；旧历史不重写；凭据/用户 Session/模型不入包或日志；任务 Runtime 显式关闭，保留 artifact/release 固定 locator 和剩余限制。 |

## 9. Evidence、认证与关闭

- 治理及紧凑审计留在 framework，产品仓库保留稳定用户/开发者文档和发布工具，不重新建立逐轮 `docs/change_records/`。
- Raw run、构建日志和安全发布 checkpoint 保存本地；tracked summary 记录精确 commit/hash/locator/结果，不复制 raw prompt、私有转录或凭据。必要 evidence 在任务/recovery 活跃期间不得自动删除。
- Reviewer/Executor 沿用 Codex Mix 当前 active account 的受事务保护 auth 投影与独立 runtime homes；账号/模型具体值在启动 gate 固定，不更改认证机制，不写退休 `.codex-A`/`.codex-B`。
- 不输出 gh token、Codex auth、原始 account ID、邮箱或完整环境；不要求重新登录/换认证服务。凭据不确定或泄露立即 fail closed。
- 清理 Downloads 临时验证目录必须在不影响恢复/审计后提醒 Human，并按明确授权针对精确路径执行，不把 task closure 当作无限清理权限。
- 最终关闭需要自动 release evidence、独立验收与真实 Human artifact PASS；历史任务保持冻结。任何实质合同变更由 Owner 批准，Runtime 不能静默扩大权限。

具体源码 SHA、构建/ZIP hash、workflow 接口和临时目录都由执行 evidence 确定，属于 Runtime 事实，不是尚未选择的发布版本或可任意替换的合同输入。
