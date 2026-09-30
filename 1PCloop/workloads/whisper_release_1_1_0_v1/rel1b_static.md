# Whisper 1.1.0 REL1B -- Static 稳定合同

## 1. 身份、来源与生效条件

- 父任务: `whisper_release_1_1_0_v1`；子步骤: `REL1B`，继承顶层 Step 1。
- 状态: `AUTHORIZED`。
- Human Owner: 本对话的项目 Owner。
- 父合同: [workload_static.md](workload_static.md)，固定 SHA-256 `47a90b305e5fa80eeec44dba75244e6a8482c1a121154c53a76f14d20dcc79a7`。
- 配套状态: [rel1b_runtime.md](rel1b_runtime.md)；父任务状态: [workload_runtime.md](workload_runtime.md)。
- 模板来源: `/Users/smterpro/Workspace/framework-loop/1PCloop/templates/static_prompt_zh.md` 与 `runtime_prompt_zh.md`。

Human 于 2026-09-29 先要求准备 REL1B Static/Runtime 供审核，随后指定本轮 Reviewer 为 `gpt-6.1-sol/xhigh`、Executor 为 `gpt-6.1-sol/high`，要求完成配置并提供指令由 Human 手动启动。该决定授权准备并执行本子步骤的实现、测试和独立审核，不授权助手自行启动。本合同不替代父合同；实际生产集成仍须等 REL1C 及整个 Step 1 接受后进入 Step 2。父合同冲突、敏感操作或新增权限必须先取得 Owner 决定。

## 2. 用人类语言说明本步

实现一个可靠的"合并管理员": 它先确认哪些代码确实被接受、允许合并到哪个仓库，再在隔离目录合并功能分支与 main，完成环境和测试检查，最后才允许普通 push。中途退出后，它先检查真实 Git 状态，不凭自己写的一句"成功"跳过检查。

本步交付的是这个工具和证明它可靠的测试，不是真正合并 main，也不是制作 ZIP。版本、App/ZIP 基础层由 REL1A 提供；构建和发布接口由 REL1C 补齐。

## 3. 范围与交付物

范围内:

1. 独立批准的校验协议，绑定被接受实现、工具字节、父/子合同和精确集成输入。
2. 本地原子 journal、明确状态、只读 status 和中断后恢复。
3. 固定 repo/ref 的 feature push 与非 fast-forward 集成实现，保护两边历史。
4. main push 前的锁定 Python 环境 bootstrap、完整严格回归及输入重验。
5. 真实生产 CLI 的 disposable Git 测试、失败/篡改矩阵及双语使用说明。

允许使用少量职责清楚的 helper；不能复制完整的旧候选控制器，把尚未审核的后半段一起变为生产入口。

范围外: 正式生产 push/merge、App 构建、ZIP 生成、Human artifact PASS、tag、draft、上传和发布；ASR/UI/模型行为、认证机制、framework runner、第三方依赖升级。未实现的 build/publish 子命令必须缺省不可用或明确拒绝，不能因 journal 写了未来状态而启用。

## 4. 稳定权限与信任边界

- Reviewer 只读；Executor 只能在固定 target 分支实现、测试并创建普通后继 commit，不执行真实远端 mutation，不改 Static/Runtime，不自行 ACCEPT。
- 集成控制器在未来生产阶段是受控 Git 工具，不是第二套 Agent mutation 状态机；不调用 Reviewer/Executor，不执行 LLM prose 中的任意命令。
- 测试只能操作 Downloads 下明确创建的 disposable 仓库、本地 bare remote 和 fixture 路径。测试 key 必须新建且仅用于 fixture，不能读取或使用个人 SSH/private key、Codex auth、gh token。
- 当前实现以及 controller 自身的 JSON/hash 不是批准权威。批准必须来自普通 Agent 不能写入的独立控制路径，并能证明与 Human 授权及独立审核的关联。
- 生产信任根不得由调用者的 `--allowed-signers`、journal、待审核仓库或 fixture 自行选择。批准、身份、公钥/信任配置变更和撤销均必须重新验证；缺失或不可信时禁止任何写操作。
- 可采用外部固定信任根校验 detached signature，但算法、部署位置和可信入口属于待审核实现方案。生产密钥创建、私钥读取或安装信任根不属于本步默认授权。真实部署必须经过额外的明确 Human 决定；本步可用隔离测试密钥证明协议，生产缺配置时保持禁用。
- 威胁模型是单 writer 下的错误输入、可变仓库/journal 与误恢复，不承诺抵抗已控制本机 Owner 或操作系统的攻击者。不得用此限制取消输入验证。

## 5. 必须成立的集成与恢复约束

1. repo 固定 `smter6626/live_subtitle_generator`，仅父合同列出的 canonical origin；读写 origin 都要校验，拒绝 push URL 重定向、危险 remote 配置和不可信 Git hook/命令注入。远端对象完整 SHA 固定，不使用浮动或缩写 revision 作为 authority。
2. 批准必须固定 implementation commit、accepted tool set/hash、预期 main/feature refs、基线、合同和管理目录。最终 REL1C 实现会前进源码，因此正式集成使用未来重新审核/批准的最终输入，不能永远以本步基线或 REL1B commit 代替。
3. 新隔离 clone 内取得并核验所需 commit，再检查祖先关系。不能因 main object 尚未 fetch 而改用旧值或假设 fast-forward。
4. 当前已知分叉需要真实 merge，保留双方完整 ancestry；禁止 reset/rebase/force push、随意 cherry-pick、`ours/theirs` 丢弃一边。内容冲突或远端漂移停止，要求有界决策/repair。
5. 合并 tree 保留已接受功能及 main 的 streaming 文档。合并改变受审核工具字节或出现无法解释的内容差异时，不能沿用旧批准，必须重新审核。原三个用户 worktree 不切换、不写入。
6. 在集成 clone 中使用其自身固定 Python/uv/lock bootstrap，完整 strict 回归成功、日志 locator/hash 有效、源码 clean、输入和远端 refs 再验后，才允许 main 普通非 force push。不能借用另一个 worktree 的解释器。
7. 每个副作用前原子持久化明确意图，完成后核对事实。journal 文件 `0600`、目录 `0700`；同目录临时写入、fsync 文件、原子替换及目录 fsync。拒绝 symlink/path escape、异常类型、重复/未知字段、错误权限和不完整持久状态。
8. journal checksum 只能检测字节损坏，不能授予批准、测试通过、已 push 或未来发布权限。重算 checksum 的篡改必须由外部批准和实际 Git/证据校验拦截。
9. 恢复时验证批准、源码/工具/合同、管理路径、merge parents/tree、测试证据和远端实际 ref。成功 push 后 crash 可按 exact commit 对账，不重复 push；未知结果先只读对账。
10. 缺少可信 bootstrap/test 完成证明时，重新运行安全的本地检查或停止；不能仅因 journal 写了 PASS 而跳过。重复检查允许，重复已验证远端副作用不允许。
11. main 已成功更新但本地证明丢失时，不自动 rollback 或把陌生同名 commit 当作本任务完成；明确报告 reconciliation/Human gate。单 writer 支持边界内仍需 mutation 前重验，普通 push 被拒绝不能 force。
12. status 严格只读，不创建目录/journal、不修复、不 fetch/push；人类终端给简明阶段/结论，安全 metadata 和完整诊断保留本地，不回显秘密或任意异常文本。

## 6. 验收条件

| ID | 必须证明什么 | 直接 evidence 与拒绝边界 |
| --- | --- | --- |
| B-AC-01 | 分工与未来门禁 | 实际生产 CLI/调用链；普通 Agent 权限不扩大，无第二套 Agent loop；build/tag/publish 无法被 CLI 或 journal 启用。 |
| B-AC-02 | 批准不可自授予 | 合法外部 fixture 批准通过；caller-selected signer、替换批准/工具/合同、重算 journal、测试 key 注入生产入口均拒绝；生产未配置时无写操作。 |
| B-AC-03 | journal 安全持久化 | 原子写入及 crash fixtures；权限、symlink、schema、checksum、路径和状态冲突均不启动危险动作；status 重复调用 bytes/refs 不变。 |
| B-AC-04 | 分叉集成正确 | 实际 disposable Git merge，两个父级/ancestry/tree、main streaming 文档和 feature 内容均保留；缺对象正确取得，冲突/dirty/ref/origin/hook drift 停止。 |
| B-AC-05 | push 前测试 gate | 生产命令调用顺序与真实 CLI fixture；锁定环境和当前完整 strict 测试先于 main push；失败、伪造 PASS、过期结果和测试后源码变化不 push。 |
| B-AC-06 | 恢复无误动作 | merge、bootstrap/test、feature push、main push 前后 crash/unknown outcome；事实精确一致才恢复，不重复已完成副作用、不跳测试、不污染用户 worktree。 |
| B-AC-07 | 既有结果不回归 | REL1A identity/ZIP/runtime、现有产品及全量 strict 测试；依赖 pins、产品行为、合同、历史失败/REJECT 不改变。 |
| B-AC-08 | 可操作与隐私 | 双语文档准确区分 fixture/生产/尚未实现；脱敏日志、read-only status、精确 commit/test locator；凭据和私有 Session 不进入输出/Git。 |

上述局部条件映射父合同 REL-AC-01/03/07/08；fixtures 不构成真实 main 集成、最终 ZIP 或 Release acceptance。

## 7. 审核与变更

Executor self-check 全绿后仍需同 Reviewer 直接审核，再由本对话独立复核。必须独立判断 evidence sufficiency，并从真实 CLI、重算 journal 篡改、实际分叉 Git 和测试 gate 找反例，不能只重跑同一测试。

实质范围/权限/信任模型变化先呈交 Human；本步完成不自动激活 REL1C 或真实 Step 2。父合同与历史完成结论保持冻结；REJECT 和 repair 作为 provenance 保留，旧未接受候选不能因复用而恢复权威。
