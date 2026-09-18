# foundation_v1 F8 evidence-driven disposition

日期：`2026-09-18`

状态：`COMPLETE -- AWAITING INDEPENDENT F8 REVIEW`

本文件是 F8 的 Executor disposition，不是独立验收结论。它不修改
[foundation_v1 Static](../workloads/foundation_v1/workload_static.md) 或
[foundation_v1 Runtime](../workloads/foundation_v1/workload_runtime.md)，不关闭 foundation_v1，
不创建 F9，也不授权 GUI、治理历史迁移或 raw evidence 删除。

## 1. 审计基线和方法

审计基线为 source repository `main` commit
`18d296b22cd1b635500e42f11c9b97997f0ee47f`。审计开始时 local HEAD、`origin/main` 和
GitHub `refs/heads/main` 相同，工作树为空。Static SHA-256 为
`0995a0374205a7116b59aeb5ec20a468de22458a24066a9f0f5d71e32f07506e`。

直接读取并交叉核对的主要来源：

- [foundation_v1 Runtime](../workloads/foundation_v1/workload_runtime.md)，包含 F1-F7 的实现、
  REJECT、repair、independent review、transition 和 pending task 历史；
- [F7 real-service smoke compact evidence](f7-post-foundation-real-service-smoke-20260918.md)；
- [post-P6 failed-closed smoke compact evidence](post-p6-foundation-smoke-20260912.md)；
- [English README](../README.md) 和 [中文 README](../README.zh-CN.md) 中的 CLI、TUI、Human Gate、
  evidence 和安全边界；
- source Git commit graph，以及仍存在的 F7 disposable repository、bare remote 和 Git-ignored raw
  artifact hash。

F8 没有运行新的 real-service turn，也没有读取或复制 profile credential、prompt、peer payload、
stderr、完整 raw event 或 hidden reasoning。

## 2. 结论摘要

| Decision track | Disposition | 对 foundation closure 的影响 |
| --- | --- | --- |
| 简单本地 GUI | `DEFER` | 不阻塞关闭。当前没有被 CLI/TUI/Human Gate 留下且有直接 evidence 的使用缺口。 |
| 治理文档压缩 | `DEFER` | 不阻塞关闭。规模和重复已经可量化，但尚无恢复失败、上下文截断或事实漂移证据；先保留无损 proposal。 |
| Raw evidence lifecycle | `IMPLEMENT` | 本文件实施默认 policy，不实施清理器、不删除 raw。建议独立审核接受后将 PT-02 记为 `RESOLVED`。 |

Foundation recommendation：`CLOSE`，但仅在本 F8 disposition 经独立 Reviewer 接受并由 Human
Owner 执行治理 transition 后。当前没有 evidence 支持为 GUI、压缩迁移或清理器扩展 foundation。

本轮没有未决产品偏好阻塞 disposition，因此状态不是 `HUMAN DECISION REQUIRED`。未来实际 GUI、
不可逆 archive、raw 删除或自动清理仍各自需要 Human Owner 授权。

## 3. Quantified inventory

### 3.1 当前治理与 compact evidence

以下为基线 commit 上的 UTF-8 文件实测值：

| 文件 | 行数 | 字节数 | SHA-256 |
| --- | ---: | ---: | --- |
| `workloads/foundation_v1/workload_runtime.md` | 1,257 | 78,271 | `308a684640d1036d688cb838b6e1384e64760beacacd8eaf107ab51c96a95c0f` |
| `README.md` | 761 | 35,874 | `19bd18e4b5312e2dacac9d3043cfbbdbd6e3ad187506bf2a43b0c4b5cda9cc60` |
| `README.zh-CN.md` | 653 | 28,889 | `1ee24a7bad085eb15dcf13ab244afa2efcb19ca06d56bffa3d9d5766f6250850` |
| `evidence-summaries/f7-post-foundation-real-service-smoke-20260918.md` | 139 | 7,665 | `284bb8b652de19547ce9e0c1d357929b6131725dcde2570052844042b96ac3e1` |
| `evidence-summaries/post-p6-foundation-smoke-20260912.md` | 138 | 6,242 | `4a8a4098948fe9ee4f1f98cc2fba333ec5cc1957fb497283d8f67e5bbf2af4dd` |
| 合计 | 2,948 | 156,941 | 不适用 |

其中双语 README 合计 1,414 行、64,763 字节；两份 tracked compact summary 合计 277 行、
13,907 字节。中英文 README 的结构重复是受支持语言的有意镜像，不是两份 Runtime。

Runtime 内部同时包含 7 个 F1-F7 completed summary、7 个 step transition block 和 13 个 dated
review section，其中 6 个是 REJECT heading，7 个是 ACCEPT heading。这里确有重复检索结构，但每类
记录承担不同作用：当前结果、状态迁移和独立审查 provenance 不能简单按相似文本去重。

### 3.2 Raw evidence inventory

- 当前 tracked `evidence-summaries/` 只有上述 2 个 compact summary，共 13,907 字节；它们是长期
  Git provenance，不含完整 raw payload。
- 当前 source checkout 的 `1PCloop/.local/runs/` 没有 run directory，并由 `.gitignore` 排除；
  它是未来 mutation run 的默认本地 raw 位置。
- F7 raw fixture `/private/tmp/1pcloop-f7-smoke.RBbAa8` 当前仍存在，关键 artifact hash 与 compact
  summary 一致。
- post-P6 raw fixture `/tmp/1pcloop-post-p6-smoke.jomR1L` 当前已经不存在。tracked compact summary
  仍存在，但不能据此猜测重建完整 raw evidence。
- `1PCloop/runs/` 另有 5 个早期、已 tracked 的历史 run directory，共 164 个文件、1,659,525
  字节。它们是既有冻结 provenance 的例外，不是新 mutation run 的默认 retention 形态；本轮不
  改写或删除它们。

F7 locator 的本轮只读复核结果：

- run ID `20260918T091536Z-19561`，raw root
  `/private/tmp/1pcloop-f7-smoke.RBbAa8/framework/1PCloop/.local/runs/20260918T091536Z-19561`；
- target local `smoke` HEAD `259046fef6823c0de309a01c1a04dd5c8260f597`，target bare remote
  `refs/heads/smoke` 仍为 baseline `0e4bcc50b04ba8a2425298481f70d4c61714535d`；
- framework local `main` 和 framework bare remote `refs/heads/main` 均为 evidence commit
  `4bb32caab152a59662f225c204f0f52dcc65e944`；
- final verdict SHA-256
  `849869db91641bf174f8200dc17e21e8af451f3174953ff5f7cbafcdccf36ec8`，唯一 transition ID
  `bea0f37639a523592863d79f832a2a9ce3f03bd101abcdafd49ebc086ba69851`；
- generated compact summary SHA-256
  `5df3ac7bde7c1e1d263d19f8ef1311b98179325bbf8603ab8aaf091dbc4aecfd`；
- raw `manifest.json`、`control-events.jsonl`、`live-status.json` 和 checkpoint SHA-256 分别为
  `215e34df583196b751750b589f7287619da6e22635537e42de553e687a985987`、
  `f9b8478d33b3e4106b8efc449bae7a2890aaf3e1d6ec7475e42413b1ae72e7e3`、
  `650dc1297dee51b0977b022f868d5f9b00b631bc34d79505a3ecc7e013051aa5` 和
  `233205d4dfda201d92dc49c21db44c696f4a1bb26b2f25cd78d09e03f88973ef`。

上述当前可用文件和 Git refs 均与 F7 compact summary 一致。post-P6 raw locator 的当前结果则为
`UNAVAILABLE`，与本文件提出的 lifecycle 问题形成直接对照。

### 3.3 信息角色

| 信息类型 | 当前角色 | 是否可以仅靠 Git history 替代 |
| --- | --- | --- |
| Static | 稳定合同和 scope authority | 否 |
| Runtime 顶部 current status、唯一 Active Step、pending gate | 当前状态 authority | 否 |
| Runtime F1-F7 transition/review history | supersession 和决策 provenance | 否，除非先形成有 hash/index 的受审 archive |
| README | 稳定操作说明和边界 | 否；也不得提升为 Runtime authority |
| Tracked compact summary | durable locator、hash、结论和 Git identity | 否 |
| Git-ignored raw evidence | 深度审核、恢复、receipt 和完整 verdict evidence | 否；缺失后只能报告 `UNAVAILABLE` |
| Disposable `/tmp` fixture | 有限期验证环境 | 否；系统可能随时清理 |
| Git commit graph | 文件版本与提交 ancestry provenance | 不能单独表达当前 Active Step 或 raw availability |

## 4. Decision 1 -- 简单本地 GUI

Disposition：`DEFER`

### 4.1 支持 IMPLEMENT 的 evidence

- 当前启动仍要求准备 config 并输入 CLI；对不熟悉终端的 Human Owner，路径、命令和多个只读
  子命令存在学习成本。
- TUI 是交互式 TTY-only dashboard。非 TTY 明确退出，极窄终端只显示 resize/quit notice；它不
  提供图形化文件选择、通知或跨 run 历史浏览。
- Human Gate guidance 是固定文本而不是按钮。Human 仍需在界面之外完成 review/remediation，
  然后显式启动新命令。

这些是可能的 product friction，但 F1-F7 没有记录因它们导致的错误操作、无法恢复或任务失败。

### 4.2 反对 IMPLEMENT 的 evidence

- F3 已提供单一 config-backed `doctor/preflight/run/resume/status/inspect` 入口；F5 增加三个命令
  共用的 default-deny Human Gate projection。
- F6 TUI 已覆盖 run/cycle/role、F2 active-time、三层终态、integrity、Human Gate reason/action、
  no-checkpoint、`UNAVAILABLE` 和 `INVALID`，并经过两次自然 REJECT 和两次 repair。
- F7 在真实 PTY 中打开 TUI、刷新并退出，显示与 operator 相同的合法 terminal state；前后
  authoritative artifact 和 Git refs 不变。
- 当前 single-writer、one-active-loop 范围不需要多 run dashboard。GUI 不能用视觉便利绕过
  Human Gate 或扩大 state authority。

### 4.3 成本与风险

- 需要新的 event loop、macOS packaging、accessibility、resize/window lifecycle、异常 cleanup 和
  版本兼容测试。
- GUI 若直接读取 raw 或重新解释自然语言，会建立第二套 state model；若只包裹 operator，又会与
  已有 TUI 大量重复。
- 可点击 action 容易把只读 guidance 误解为授权执行，扩大 Human Gate、credential 和本地进程攻击
  surface。
- 当前没有可度量收益足以抵消维护和状态一致性成本。

### 4.4 重新评估触发条件

只有出现至少一项直接 evidence 时重新评估：

1. 有记录的操作流程无法通过 CLI/TUI 完成，而不是单纯偏好窗口界面；
2. accessibility 需求无法由当前终端满足；
3. 重复发生由 config 路径、状态阅读或 Human Gate guidance 引起的人为错误；
4. Human Owner 明确把非终端 operator 体验列为产品目标，并接受新增安全和维护 surface。

触发后应先形成独立 bounded GUI contract，规定只消费 F3/F5 projection、保持 read-only 和
default-deny；不得把 GUI 实现混入 foundation closure。

## 5. Decision 2 -- 治理文档压缩

Disposition：`DEFER`

### 5.1 支持 IMPLEMENT 的 evidence

- Runtime 已达到 1,257 行、78,271 字节；同一 step 的 outcome 会分别出现在 completed summary、
  transition 和 independent review 中。
- 13 个 dated review section 中保留了 6 次 REJECT、repair instruction、测试计数和 acceptance
  mapping。它们对 provenance 必要，但不都需要每次恢复当前状态时进入最短上下文。
- 双语 README 合计 64,763 字节，包含大量镜像说明；随着功能继续增加，人工同步成本会上升。

### 5.2 反对 IMPLEMENT 的 evidence

- F1-F7 Reviewer 均能从当前 Runtime 恢复 transition 和 REJECT -> repair -> ACCEPT 链；没有发生
  因 Runtime 长度而截断、选错 Active Step 或遗漏 pending deadline 的记录。
- 当前 Runtime 顶部已经提供 compact current status，详细历史集中在后部；已有结构可让 Human
  先读当前状态再按需读取 provenance。
- 压缩错误的风险不是排版问题，而是丢失 supersession、Human authority、deadline 或 raw locator。
  F3、F5、F6 的自然 REJECT 都证明跨层 identity 很容易被看似合理的简化破坏。
- README 记录稳定使用合同，不应因 Runtime 变长而被改造成另一份进度权威。

### 5.3 成本与风险

- 需要定义 archive schema、section identity、index、重建器和 migration review；仅移动 Markdown
  不构成可证明的无损压缩。
- Git history 不能替代 searchable current index；只保留 commit hash 会让离线恢复和 pending gate
  审查依赖额外推理。
- 双语 README 自动去重可能牺牲任一语言的可读性，并产生 drift detection 的新维护面。

### 5.4 候选 archive/index 设计

本轮不执行下述迁移。若未来触发压缩，建议作为独立、bounded、可审核 deliverable：

1. 先把迁移前 Runtime 原始 bytes 作为 immutable tracked archive 保存，例如
   `workloads/foundation_v1/history/runtime-through-f8.md`，并记录完整 SHA-256、字节数和行数。
2. 新建 machine-readable index，逐条记录 `step_id`、event type、verdict、implementation/reject/
   repair/accept commit、parent/supersedes relation、pending change、Human decision、compact/raw
   locator 及 hash。Index 不复制 raw payload。
3. 精简后的 Runtime 仍是唯一 current authority，只保留当前状态、唯一 Active Step、blocker、
   pending table/gate、last accepted transition、archive/index identity 和 next direction。
4. README 继续只保存稳定 operator contract；不写 Active Step 或 review verdict。
5. 原 archive 一经接受即冻结。新 transition 追加新 archive segment/index entry，不覆盖旧 segment。

### 5.5 机械无损验证逻辑

候选迁移必须在临时副本中同时通过：

- archive bytes 的 SHA-256、行数、字节数与迁移前 Runtime 完全一致；
- index 恰好含 F1-F7 七个 transition，并能解析每个 implementation、所有 6 个 REJECT、每个 repair
  和最终 7 个 ACCEPT；F6 的两轮 REJECT/repair 不得折叠为一轮；
- 对每个 entry 执行 `git cat-file -e <commit>^{commit}`，并验证声明的 parent/supersedes edge；
- current Runtime 恰好只有一个 current status 和一个 Active Step，且其 Static identity 匹配；
- PT-01 的 `DUE_NEXT -> RESOLVED` 历史、PT-02 disposition、所有 deadline/current-step 值和
  `max(deadline_step - current_step - 1, 0)` 重算结果均可由 index 恢复；
- 所有 Human decision 记录 authority、日期、选择和受影响 step，不从自由文本猜测；
- 每个 compact/raw locator 均保留原字符串、availability 和 SHA-256；raw 已缺失时只允许
  `UNAVAILABLE`，不得以 compact summary 补造 raw；
- 使用 archive 加 ordered index 重建一份审计视图，并与 pre-migration inventory 做逐 section ID、
  commit、verdict、pending 和 locator 集合等价比较；任一缺项即 fail closed；
- 独立 Reviewer 在实际替换 current Runtime 前审核 temporary proposal。Human Owner 另行授权不可逆
  archive transition。

### 5.6 重新评估触发条件

出现任一直接信号时重新评估：Runtime 超过 2,000 行或 128 KiB；Reviewer 实际发生上下文截断或
恢复错误；current summary 与历史段出现事实漂移；每次审核读取历史的成本成为可测瓶颈；Human
Owner 明确要求长期 archive policy。在此之前，压缩收益不足以承担 migration 风险。

## 6. Decision 3 -- Raw evidence lifecycle

Disposition：`IMPLEMENT`，含义是立即采用本节 default-safe policy；本轮不删除任何 raw evidence，
不实现自动清理器。

### 6.1 支持 IMPLEMENT 的 evidence

- PT-02 自 Step 1 起保持 `PERMANENTLY_NON_BLOCKING`，F8 明确要求 disposition。
- post-P6 `/tmp` raw 已实际消失，而 compact summary 仍在；这证明 `/tmp` 不是 retention guarantee，
  也证明 compact provenance 与完整 raw availability 是两种不同状态。
- F7 raw 当前仍可用，独立 Reviewer 曾借助 receipts、verdict bytes、checkpoint、events 和 Git object
  重建 transition。这些内容在 active/review/recovery 期间有直接价值。
- F3/F5 已规定 raw 缺失为 `UNAVAILABLE`，identity conflict 为 `INVALID`；系统不会从 summary 或
  Agent 自述猜测重建 raw。
- Raw 可能包含 prompt、peer payload、stderr、完整 events 和 internal diagnostic，长期无限保留会
  增加 privacy、磁盘和本地访问风险。

### 6.2 反对自动或立即清理的 evidence

- F1 correction、F3 supersession、F5 identity conflict 和 F7 transition rebuild 都需要比 compact
  summary 更细的 raw identity 才能独立复核。
- Terminal publication success 不等于 logical success；仅看到 `PUSHED` 不能判断 evidence 已无恢复
  价值。
- Human Gate、publication pending、correction pending、REJECT repair 和 crash recovery 都可能继续
  引用现有 raw bytes。删除会把可恢复状态永久降为 `UNAVAILABLE`。
- `/tmp` 的系统清理时间不可控，不能充当主动 lifecycle policy。

### 6.3 默认 retention classes

| Class | 状态 | 默认保留期 | 清理权限 |
| --- | --- | --- | --- |
| `ACTIVE_RECOVERY` | Agent turn、correction、transition、publication、resume 或 identity review 未完成 | 无期限；不得自动清理 | 不可清理 |
| `HUMAN_OR_REVIEW_PENDING` | HUMAN_GATE、REJECT、FAILED_CLOSED、独立审核未完成或 finding 未 disposition | 无期限，直到 Human/Reviewer 明确 disposition；之后至少再保留 180 天 | 仅 Human Owner 明确授权 |
| `ACCEPTED_TERMINAL` | 独立接受、三层终态 settled、compact summary 已 commit/push | 从 independent acceptance 与 workload closure 两者较晚日期起至少 90 天 | 仅 Human Owner 明确授权 |
| `DISPOSITIONED_INCIDENT` | 已完成审计的失败/安全事件，不再需要恢复 | 从最终 disposition 与 workload closure 两者较晚日期起至少 180 天 | 仅 Human Owner 明确授权 |
| `DISPOSABLE_TMP` | `/tmp` 或 `/private/tmp` fixture | 不提供 durability guarantee；需要跨 session/review 时必须在运行前选择持久 Git-ignored root | 不得把系统清理解释为授权删除 |

F7 raw 属于 `ACCEPTED_TERMINAL`，最早清理日必须从 foundation 实际 closure 而不是本文件日期计算。
post-P6 raw 属于 `MISSING_UNPLANNED`：它保持缺失，不能补写成已授权清理，也不能据 compact summary
恢复为 `AVAILABLE`。

### 6.4 Index、hash 和 privacy boundary

未来新 run 的 tracked compact summary 应继续永久保留，并至少记录：run ID、三层终态、target/
framework Git identity、Runtime transition ID、raw root locator、关键 artifact hash、retention class、
independent review reference 和 raw availability。若 Human 授权清理，再追加不含 raw 内容的
`AUTHORIZED_DELETED` tombstone、授权 reference 和时间；不得覆盖原 locator/hash。

详细 artifact list、size、mtime 和 hash manifest 可以放在 Git-ignored local `raw-index.json`。
Tracked index 只保存审计所需 identity，不保存 prompt、credential、profile state、peer payload、
stderr、完整 events 或 hidden reasoning。既有 tracked historical `runs/` 保持冻结例外，未来默认不
把 raw 加入 Git。

### 6.5 人工清理 gate

只有全部条件成立时，Human Owner 才能授权一次具体路径的可恢复清理操作：

1. run 已 terminal，且不处于 correction、resume、finalization、Human Gate remediation 或 independent
   review；
2. logical outcome、Runtime transition 和 evidence publication 分别有最终值；
3. compact summary 已验证、commit 并 push，所列 Git object、locator 和 hash 已复核；
4. 所有 REJECT/finding 已 supersede 或明确 disposition，没有后续 review 引用 raw；
5. 对应 retention period 已届满；
6. Human Owner 针对 exact normalized path、run ID 和 inventory hash 明确授权；
7. 删除前生成 dry-run inventory，拒绝 symlink、宽目录、glob、`~`、repository root 或未解析变量；
8. 删除后只更新 availability/tombstone，不改 verdict、Runtime transition 或历史结论。

本 policy 不授权后台 timer、watcher、自动 cleaner 或批量删除。任何未来 cleaner 都是新的 bounded
deliverable，必须独立审核 destructive-path safety。

### 6.6 缺失与恢复边界

- Active/recovery evidence 永不自动清理。
- Raw 缺失后，`inspect` 必须继续报告 `UNAVAILABLE`；不能根据 compact summary、commit message、
  Reviewer prose 或相似 run 猜测 bytes。
- `UNAVAILABLE` 不自动变为 `INVALID`，也不表示 task logical failure；但依赖这些 bytes 的独立复核
  不能宣称完整。
- Compact summary 永久保留 locator、hash 和当时结论，即使 raw 后续经授权删除。
- Disaster recovery 只能恢复仍有独立 copy/hash 支持的 artifact，不能重建 prompt、receipt 或 verdict
  bytes 并声称与原件相同。

### 6.7 成本、风险和重新评估触发条件

成本是维护 retention metadata、Human authorization 和本地存储；风险是保留过久造成隐私/磁盘
压力，或过早删除破坏恢复。Default-safe gate 优先避免第二种不可逆风险。

当磁盘压力有量化 evidence、出现法规/组织 retention 要求、使用共享主机、需要加密归档、compact
index 字段不足，或 Human Owner 要求自动化清理时重新评估。任何自动化都不得改变
`UNAVAILABLE`/`INVALID` 和 active evidence no-delete 语义。

### 6.8 PT-02 disposition

建议：`PT-02 -> RESOLVED AFTER INDEPENDENT F8 ACCEPTANCE`。

理由：本节已经给出可执行的默认保留期、active/recovery no-delete、Human authorization、清理
条件、index/hash、privacy 和 raw-missing 语义。PT-02 要求的是策略决定，不要求自动清理器。实际
Runtime 状态只能由后续独立验收和 Human-authorized governance transition 更新；本轮不修改 Runtime。

## 7. F1-F7 commit/provenance chain

以下 commit 均已作为 Git commit object 解析，并核对其 parent/subject。表中最后一列是记录当前
step acceptance/activation 的 governance commit，不表示 Executor 可以自行验收。

| Step | Implementation/evidence | REJECT/repair chain | Acceptance transition |
| --- | --- | --- | --- |
| F1 | `d57c1c146be9ea998572e3d09c923c4e9a77c517` | `83b23eaa841210b480013cdae9ad289c150603b4` -> `0adf4e083b002dad8ccff226afb96a9b20210bdb` | `9a58e07ee1e7e562f4d0f699317ba1cdefec4ccb` |
| F2 | `69cb4c13e1313fd88b15de93781d65400c2b5e71` | `a0776692a0507d238b3a2eb95a880f014db4844b` -> `54ccf66a1c95843ae680e0c8f50ed98c5df6c0a5` | `ac3696812a9e5eef2f3b3db6bb873b8aee226463` |
| F3 | `fdb86b26b0d5fffde59673c015ddf642c0df5820` | `0cc5c7a63dac363f49ba00dcadb9d334b443af6e` -> `a2379712b9e187a345c0694e1165fc4c4270ff64` | `4191024c5eef9c1d5332a3b2c76f70a252be9e6f` |
| F4 | `eeb75e11480ecc245e040862bd42a952ec008c97` | 无 REJECT | `5dfbfcdc8ce20fcfea2d7aaa34de51f6413e71ca` |
| F5 | `3f3bba9d94b5446008d6773792af00ded566a5ae` | `40c58a180e2daffeacb2e5bf65616e551d579e6a` -> `9262f9754d0632a555a4bbe8f821c1c7ccc5e4f0` | `29fca30981ef467086bb961c4a1dd8bb5b338eca` |
| F6 | `79eacb69f104314b3f6149192c792111b2bb3982` | `e2e15f4b68ab95eeefbfad9c7096dd5e621f16e1` -> `004364290b39d94274b1816c18040fe912f883cf` -> `36ca71ca7e88c79eb8e02ff36c1bfd6207db2b25` -> `397fb36c86aef02ea28d0f150e27ae826b53a1c5` | `975ecf6820d2d561759870a1d813e0974ec5da2a` |
| F7 | `e2c472c9bcaa43188b9d9df4d8d59d28b953fe3a` | 无 REJECT | `18d296b22cd1b635500e42f11c9b97997f0ee47f` |

这条链保留全部自然 REJECT -> repair -> ACCEPT provenance。F7 bounded smoke 未自然触发 F1
correction；不能从无 correction 的成功 run 推断 correction path 得到 real-service 覆盖。

## 8. AC-01 至 AC-11 coverage matrix

| AC | 直接 evidence | 当前状态 | Remaining limitation |
| --- | --- | --- | --- |
| AC-01 | F1 correction commits、Runtime F1 acceptance mapping、deterministic call-count/checkpoint/target tests | `COVERED` | F7 真实 smoke 未自然触发 correction；只有 deterministic 和早期治理 evidence。 |
| AC-02 | F1 三层 final result；F7 实际 `RUNTIME_TRANSITION_COMMITTED / APPLIED / PUSHED`；post-P6 的 `FAILED_CLOSED / NOT_APPLIED / PUSHED` 对照 | `COVERED` | 三层语义仍需 operator 正确解读，publication 不能替代 logical outcome。 |
| AC-03 | F3 config/operator implementation、REJECT/repair/re-review；README config-backed commands | `COVERED` | Legacy long-argument run 仍要求原参数；config identity drift fail closed。 |
| AC-04 | F2 active-time timer、injectable clock 和 recovery tests；F6 TUI 只投影这些值 | `COVERED` | 停机 wall time有意不计入；不是跨主机时钟。 |
| AC-05 | F2 versioned event/live projection、suffix validation、tool throttling；F6 structured-only data source | `COVERED` | Event hash 是 byte identity，不是 keyed authority；checkpoint 仍是 reconciliation anchor。 |
| AC-06 | F4 tracked 中文模板、固定 source hash、逐字节正文 equivalence、独立 review | `COVERED` | 模板不会自动同步未来 Tools source。 |
| AC-07 | F5 Human Gate projection、authoritative-integrity repair、三命令一致性和 default-deny tests | `COVERED` | Projection 只给 guidance，不替 Human review/remediation；single-writer snapshot。 |
| AC-08 | F5 contract extraction/re-export identity、唯一 orchestrate、F1-F4/P4-P6 regression | `COVERED` | 模块化没有引入 provider abstraction、self-hosting 或 concurrency。 |
| AC-09 | F6 TUI structured projection、两轮 REJECT/repair、privacy/Unicode/snapshot tests、F7 真实 PTY | `COVERED` | 顺序 `status/inspect/status` 不是原子并发 snapshot；TUI 仅本地 TTY。 |
| AC-10 | F7 compact/raw evidence、真实三 turn、机械 ACCEPT、唯一 Runtime transition、framework push 和 target no-push | `COVERED` | Raw fixture 在 `/private/tmp`，未来可能消失；关键 identity 已 tracked。 |
| AC-11 | F1-F6 每步 ResourceWarning-strict regression；F6 最终 `197 / 197`；F7 source diff 仅新增 compact evidence | `COVERED` | F8 是文档审计，不重跑 Python suite；后续代码变更必须重新验证。 |

Matrix 结论：AC-01 至 AC-11 均有直接、已记录 evidence；没有第二个 Active Step。当前唯一 Active
Step 仍是 Runtime 中的 F8，直到独立 Reviewer 和 Human-authorized transition 改变它。

## 9. 已知限制

1. F7 真实 bounded run 没有自然触发 F1 correction；没有人为注入错误。
2. 系统仍是 single-writer/no-concurrency；TUI 的顺序读取不是锁或原子 snapshot。
3. 当前 foundation 是 Human-mediated，不 self-host；runner 也禁止 framework 与 target 重叠。
4. `/tmp` 和 `/private/tmp` 可被系统清理。post-P6 raw 已缺失，F7 raw 当前存在不代表永久可用。
5. 当前安全边界不抵抗同一 macOS user 下的恶意本地进程。
6. GUI、自动 archive 和自动 cleaner 都没有实现，也没有由本 disposition 授权。

这些限制已经显式进入 disposition，不被 `CLOSE` recommendation 隐藏。

## 10. Foundation CLOSE / EXTEND recommendation

Recommendation：`CLOSE foundation_v1 AFTER INDEPENDENT F8 ACCEPTANCE`。

理由：

- F1-F7 和 F7 real-service smoke 已为 AC-01 至 AC-11 提供直接 evidence；
- GUI 的当前必要性没有 evidence，治理压缩没有现实失败信号，两者均可安全 `DEFER`；
- raw lifecycle 的 policy 已在 F8 明确，不需要为 policy 再实现 destructive cleaner；
- 剩余 limitation 是明确的产品边界，不是 foundation acceptance blocker；
- 为没有必要性 evidence 的功能创建 F9 会违反 F8 的 evidence-driven scope。

不建议 `EXTEND`。如果将来触发 GUI、archive migration 或 cleaner 条件，应由 Human Owner 新建独立
Static/Runtime 或明确授权 bounded follow-up，每个 deliverable 单独审核，不能在 foundation_v1
closure 中静默扩 scope。

实际关闭、PT-02 Runtime 状态变更和后续任务激活仍属于独立 Reviewer/Human Owner authority。
本文件不宣告 F8 ACCEPTED，也不执行这些 transition。

## 11. 独立复核建议

Reviewer 应至少直接重做：

1. 核对 source branch/refs、Static hash、本文 commit scope 和 clean worktree；
2. 重算第 3 节全部 tracked 文件行数、字节数和 SHA-256；
3. 对第 7 节每个 commit 执行 commit-object/parent 检查，并对照 Runtime 的 REJECT/repair/ACCEPT；
4. 验证 F7 raw 若仍存在时的 artifact hash、target/framework/bare refs；若已消失，明确记为
   `UNAVAILABLE`，不得因此改写当时已 tracked 的审核结论；
5. 验证 post-P6 raw 当前缺失和 compact summary 当前存在的区分；
6. 检查 AC-01 至 AC-11 恰好各一行、Runtime 当前恰好一个 Active Step、PT-01/02 和 deadline 历史
   没有遗漏；
7. 验证所有相对 Markdown link、UTF-8、`git diff --check` 和 allowlist；
8. 判断 `GUI=DEFER`、`compression=DEFER`、`raw lifecycle=IMPLEMENT`、`PT-02=RESOLVED`
   recommendation 和 foundation `CLOSE` 是否 evidence-sufficient。

独立 Reviewer 接受前，最终状态保持：`AWAITING INDEPENDENT F8 REVIEW`。
