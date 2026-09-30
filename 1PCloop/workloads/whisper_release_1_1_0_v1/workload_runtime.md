# Whisper 1.1.0 发布自动化 -- Runtime

## 1. 当前状态

- Task ID: `whisper_release_1_1_0_v1`
- 状态: `ACTIVE / STEP 1 CONTINUATION PREPARING TO RUN`
- Verdict: `NOT EVALUATED`
- 唯一 Active Step: `REL1` -- Step 1 发布工具、版本一致性与自动化边界；Step 2-5 均 `QUEUED`。
- Static: `/Users/smterpro/Workspace/framework-loop/1PCloop/workloads/whisper_release_1_1_0_v1/workload_static.md`
- Static identity: 见文末 "合同固定值"；经 Human 修改后须重新计算。
- 更新日期: 2026-09-29，America/Phoenix。
- 已确认发布身份: `1.1.0` / `Classroom Transcriber 1.1.0` / macOS Apple Silicon ZIP / 正式版 / ad-hoc / 中英 notes。
- 执行门禁: Human 已批准并授权启动/监控；准备独立 implementation run，完成机器审核后由本对话独立复核。未执行构建、集成、tag、draft、上传或发布。
- 当前 Config: 同目录 `workload_continuation_01.json`；独立 state root: `/Users/smterpro/Workspace/framework-loop/1PCloop/.local/state/whisper_release_1_1_0_v1-rel1-continuation-01`。原 `workload.json` 和失败 checkpoint 保留，不 resume 终态。
- 全局 Runtime 已指向本任务 `REL1`，旧 task 保持关闭/冻结。
- 隔离目录: `/Users/smterpro/Downloads/whisper-release-1.1.0.zFGKQr`；当前 Step 1 target: 其 `implementation-continuation-01/`，branch `codex/release-1-1-0-automation`，clean baseline `0388fa9daf65d5b5d0efae0e86eec824e33eab15`。原 `implementation/` 保留未验收草稿，原三个用户 worktree 保持不变。后续精确目录及清理提醒在 evidence 中维护。

## 2. 已完成的准备与直接事实

### 2.1 Human 决定和交接

- Human 先明确下一任务是 "让 1pcloop 完成除了黑盒测试以外的其他发布所需的自动化部分"；本对话于 2026-09-29 提出固定 `1.1.0`、正式版、Apple Silicon ZIP、审核后 main 集成、ad-hoc、中英说明及 same-artifact Human gate。
- Human 随后确认 "按上述方案，准备好 static 和 runtime 之后我来审阅，批准后就开始任务"。本轮只落实该文档准备权限，未把方向确认当作立即执行授权。
- 文档准备 commit `93e1ab6205d80a2e75580a6c559a7527f7bae29a` 普通 push 后，Human 于同日在本对话批准并要求助手启动、监控及再验证，最后由 Human 验收。该新决定激活本任务，不取消最终 artifact gate，也不授权提前发布。
- 已完整读取交接: `/Users/smterpro/Workspace/framework-loop/1PCloop/.local/handoffs/whisper-release-automation-preparation-handoff-20260929.md`。它是恢复索引，不代替代码或发布 evidence。
- 已完整读取 framework 中文 Static/Runtime 模板；重读实际 runner role prompts、target build/ZIP/spec 和相关现行/历史文档。没有仅凭交接记忆冻结实现接口。

### 2.2 初始仓库与远端快照 -- 2026-09-29

| 对象 | 直接核对结果 |
| --- | --- |
| Framework | `/Users/smterpro/Workspace/framework-loop`，`main`，准备编辑前 HEAD / origin/main `8ae5a7774697df4b6fc9a0760d06fcf24dca7907`，clean |
| Target feature | `/Users/smterpro/Workspace/whisper/live_subtitle_generator-session-ui`，`codex/clean-toolbar-rename-v1`，HEAD / tracking / GitHub feature `0388fa9daf65d5b5d0efae0e86eec824e33eab15`，clean |
| Target main | local origin/main / GitHub main `d0f581bb70379239c3147e5c8469d2285ad6620b` |
| 两分支关系 | merge-base `b5188ccc6aef591398fd8d31e162a29390b120e4`；feature 有 14 个 main 未包含的提交；main 不是 feature 祖先，不能 fast-forward |
| main worktree | `/Users/smterpro/Workspace/whisper/live_subtitle_generator-main-docs`，当前已占用 main；不在其中切分支或直接覆盖 |
| 其它 worktree | `/Users/smterpro/Workspace/whisper/live_subtitle_generator`，`codex/streaming-backend-upgrade`；不属于本任务自动集成目标，不混入未接受功能 |
| 最新正式 Release | `1.0.0`，标题 `Classroom Transcriber 1.0.0`，非 draft、非 prerelease、`isLatest=true`，发布于 `2026-08-21T23:52:25Z` |
| 新 tag | 本次 `git ls-remote` 未发现 `refs/tags/1.1.0`；启动/发布前仍须重新核对全部 draft/Release/tag，不能据此永久假设空闲 |

Framework 文档准备提交必然使上述 framework HEAD 前进，属于预期的本轮变化。批准后把新的精确基线写入启动快照，不沿用旧 HEAD 作为实际配置 identity。

### 2.3 当前代码与历史状态

- `pyproject.toml` 与 `uv.lock` 的本项目版本均为 `0.1.0`；正式 spec 尚未显式设置产品的两个 CFBundle version 字段。需由实现/测试确保真实 App metadata 为 `1.1.0`。
- `scripts/bootstrap_and_build.sh` 顺序执行 Python bootstrap、whisper runtime bootstrap、正式 `.venv` build；build 完成必须经过 packaged Runtime verifier 和 ad-hoc codesign。
- `scripts/build_release_zip.py` 显式接收 version，核验 clean source、App、ZIP/extracted bundle，但不设置项目版本、创建 tag 或调用 GitHub。返回的临时 extracted App 会随其临时目录结束而删除，因此 Human 验收要另建可保留的 Downloads 解压目录，不能复用该失效 locator。
- 旧 build 会清理其工作区的 `build`/`dist`。本任务应在新隔离 clone 构建，不能让重试删除已验收 ZIP；验收 artifact 须复制/固定到独立受管目录并验证 bytes。
- 现有 ZIP 不能独立证明 App 属于所记录 source commit；新流程必须补齐 fresh-build/source/artifact 绑定并拒绝旧产物。
- `PACKAGING.md` 尾部仍写 clean-machine E2E 未完成；`docs/deployment_runtime.md` 直接记录 Step 8/9 历史 PASS。应修正文档漂移，不推翻或重复伪造历史验收。
- R2 accepted code `fb317ea4a2b1db557133e91590e852c0241a3cd8`；focused 55/55、full strict 157/157、独立审核和 Human PASS 已在旧 Runtime 留存。后续文档整合为 `0388fa9...`，已删除 target `docs/change_records/`。这些是范围基线，不是新 1.1.0 ZIP 的 acceptance。
- Foundation closed、P7 paused、R2 task closed；不 resume 旧 terminal run，也不移动/覆盖旧失败、REJECT、Human gate 或 transition records。

## 3. 执行结构 -- 已批准

```text
Step 1: 普通 1PCloop 实现发布工具 -> Reviewer ACCEPT -> 本对话独立复核
Step 2: 已审核受控 workflow 集成并固定 main source commit
Step 3: 同一 workflow 正式 fresh build / package / 自动验证
Step 4: HUMAN GATE -- 你验证最终 ZIP 中的 App
Step 5: 同一 workflow 发布同一 ZIP / 下载复核 / 文档治理收尾
```

Step 1 的一次 `ACCEPT -> Runtime transition` 只关闭实现阶段，不代表整个发布完成。之后的阶段由专用控制程序和独立 evidence 驱动；不能在一个旧 checkpoint 上跨不同 target branch/HEAD 硬 resume。

发布程序接口尚未实现，不在此伪造启动命令。启动现有 implementation loop 与启动新的 release workflow 必须分别说明，不能把普通 `onepcloop.py run` 宣称为已有 end-to-end 发布入口。真实外部副作用在 Agent turn 之外执行，但须由纳入本任务的受控程序编排和记录，不退化为助手手动执行一串未经审核的命令。

## 4. Step 1 -- 发布工具、版本一致性与自动化边界

状态: `ACTIVE / REL1`。

- Objective: 在固定功能基线上实现发布 workflow 及版本/打包支持，通过独立审核后才能进入真实集成/build/publication。
- 实现基线: `0388fa9daf65d5b5d0efae0e86eec824e33eab15`；在 Downloads 隔离 clone 新建 `codex/release-1-1-0-automation` 分支。若基线漂移先核对，不自动改为旧 main 或别的功能分支。原工作区的相对源码路径在本 clone 下均保持一致，实际 target 以 `workload.json` 为准。
- Permitted changes: target 的版本/lock 本项目元数据、必要 Release/Debug spec 与直接版本来源、`scripts/` 发布工具及直接打包依赖、相关 `testCodes/`、中英 README、PACKAGING、必要 repo map/技术说明、发布说明源文件。普通后继 commit，代码逻辑变化前先读依赖。
- Prohibited changes: 普通 Agent 的 push/merge/tag/真实 Release API；Static/Runtime；framework runner/schema/roles/认证；ASR/audio/model/Clean 功能；用户数据；第三方依赖升级；历史 tag/assets；未来 GUI/LLM/公证工程。
- 实现要求: fixed repo/ref/version/asset、阶段 journal/恢复、普通 loop acceptance 绑定、受控 integration/build、独立 artifact identity、可信 Human receipt、draft/asset 对账与 final publication、safe read-only status。公共终端以简明阶段/结论为主，安全 metadata 和详细日志落本地，不 dump 环境或凭据。
- Required evidence: 精确 diff/commit、调用链、修改影响、测试 artifacts、负向矩阵；证明没有第二套 Agent mutation state machine 或扩大普通 runner 权限。
- Tests: 相关 existing packaging/bootstrap/ZIP 回归、完整可运行 strict 回归、新 workflow focused tests。mock API 和 disposable Git 测试须覆盖版本不一致、dirty/remote drift、非 fast-forward 集成、旧 App、Human 未批准/改包、上传失败/未知结果、tag/Release/asset 冲突、resume 幂等。不得为测试访问真实 Release 写入接口；fixture Human PASS 不得被真实执行模式接受。
- Acceptance: REL-AC-01、02、07 的实现证据，REL-AC-03 至 06 的充分自动测试，以及 REL-AC-08 的准备期准确性；真实平台构建/Human/发布验证仍分别留给后续阶段。
- Stop: 需要框架新权限、凭据变更、扩大产品行为或不可证实的远端 mutation 时停止；提出 bounded proposal，不直接突破 Static。
- Executor report: 改动逻辑与依赖、精确文件、测试及不同失败路径、完整 commit、未实现边界；完成后 `AWAITING INDEPENDENT REVIEW`，不宣告发布成功。

## 5. Step 2 -- 受控集成与固定源码

状态: `QUEUED`，仅 Step 1 machine + 独立审核通过后可激活。

1. 核对已接受 implementation commit、工具 hash、当前批准 Static、feature/main 预期 refs 和 GitHub repo identity；必要时先普通 push 已接受实现分支。
2. 在 Downloads 独立 clone 中集成，保持原用户 worktree 无变化；处理当前非 fast-forward 关系，确保 remote main 和已接受 feature 均为最终 commit 祖先。冲突/意外 drift 停止，不自动丢弃一边。
3. 对集成结果核查 tree/diff、所有已接受功能和 main streaming 文档，执行相关完整回归并独立复核。检查版本/锁文件/正式 build 来源。
4. 仅门禁通过后普通 push main，核验远端 exact commit；固定 `release_source_commit` 和已审核工具 identity，后续 build 使用该源码。

Evidence: before/after refs、merge parents/ancestry、diff、tests、clean/remote receipt。集成的 merge commit 不进入普通 Executor mutation turn，也不让 runner 错把它判为 Agent 普通实现后继。

## 6. Step 3 -- 正式构建、固定 ZIP 与自动验包

状态: `QUEUED`，依赖已接受 Step 2 source identity。

- 从固定 source 在隔离 clone 使用现有正式 one-entry build；正式锁定 Python 3.12.14/uv/whisper runtime/manifest 不升级，不复用旧 App。
- 核验真实 plist version、签名、runtime components/architecture/dependency closure、下载器与模型 manifest、CLI smoke；ZIP 全边界/CRC、bytes/mode/symlink round-trip、解压 App verifier 必须通过。
- 记录 fresh-build source proof、App identity、唯一最终 ZIP path、size、SHA-256、验证结果；固定 artifact 后不被新 build 覆写。
- 新建 Downloads Human 验收目录，解压该 ZIP 并核对与固定 artifact 一致，给出从启动开始的人工流程。保留目录和 artifact 直到 gate/publication/recovery 完成。
- Build 或验包 FAIL: 不创建 tag/Release，保留诊断，修复后重新 build/review；不能因为已跑过旧源码测试跳过本阶段。

Evidence: source + build + artifact identity、自动验证原始输出的 locator/hash、解压目录及相关自动测试。通过只表示 "候选包可交付人工验收"。

## 7. Step 4 -- 最终 ZIP 的 Human 黑盒验收

状态: `QUEUED / FUTURE HUMAN GATE`。

Human 从指定 Downloads 目录启动 ZIP 解压 App，不使用旧已安装版本或直接 `ui_app.py`。

最低流程: 启动/标准 Gatekeeper GUI 路径、模型选择及 Model Manager 可用、麦克风权限、真实转录和 Stop、再次 Start 的 Session 清屏、增量复制断点/路径复制、窗口高度与滚动、工具栏位置、中英切换、录制中/Stop 后重命名，以及临时 Session 中可安全进行的全文恢复 Yes/No。

无需为本轮要求重新测试所有语言/所有 Mac；记录实际硬件/macOS/模型/语言、覆盖和限制，不扩大支持声明。测试只用临时输出，不移动真实转录。

必须记录 Human 对固定 `release_source_commit + artifact bytes/hash + 解压目录` 的明确 PASS/FAIL。未回复不等于通过。FAIL 导向有界 repair，新包重新通过自动验证和本 gate；PASS 才启用 Step 5 预授权。测试及审核元信息不得伪造 Human receipt。

## 8. Step 5 -- 同一 artifact 发布、远端核验与收尾

状态: `QUEUED`，发布授权依赖 Step 4 的真实固定-artifact PASS。

1. 重验工具、合同、source/ref、Human receipt、本地 ZIP bytes/hash；未知 drift 或恢复状态冲突暂停。
2. 检查远端 `1.1.0` tag/draft/Release/asset 是否存在。新对象按固定 source 建立；已有对象仅可按本任务持久恢复记录精确对账复用，禁止 overwrite/clobber。
3. 受控创建/推送精确 tag，建立 draft，上传已验收 ZIP；先从远端下载对比，再转正式/latest，并复核公开 metadata/tag/下载内容。
4. 上传/公开后结果未知先读远端，按真实 ID 和 bytes 恢复，不能把重试变成第二份 Release 或新未经验收 ZIP。
5. 普通文档-only更新 README 当前下载入口、准确打包说明及必要技术文档，记录发布 URL/tag/source/asset ID/size/hash。文档后继 commit 不修改 tag 和已验收产物；历史 product/deployment evidence 不重写。最终治理状态由 Reviewer/Orchestrator 更新，不授权普通 Executor自行接受。
6. 独立核验 REL-AC-01 至 08，记录残余支持/签名/并发限制，再关闭 task、清除全局 active 指针。提醒临时目录清理；必要审计保留后再按精确授权执行删除。

## 9. 启动前必须满足的 gate

1. Human 明确批准本文和 Static 并开始；批准若带修订先同步合同，不自行认为当前草案已生效。
2. 重新核对全部 branch/local/tracking/GitHub refs、clean 和版本占用；创建经批准的实现分支，但不先 merge/tag/release。
3. 准备独立 workload config/state root/evidence roots、唯一 Step 1 implementation machine block；全局 Runtime 仅指向本任务，旧 task freeze。
4. 模型先沿用最近已接受的 operational choice: Reviewer `gpt-5.6-sol / xhigh`、Executor `gpt-5.6-sol / high`。这是启动配置候选，不改变角色 config；启动前核对实际可用性，有变更须明确决定，不 auto fallback。
5. Codex Mix active account 新 run 固定、双 role runtime 隔离、认证事务完整恢复、凭据扫描零、A/B retirement snapshot 不变；不读取/打印 auth 来生成文档。
6. doctor/preflight、Runtime/Static exact hashes、目标/治理树不重叠、工具/read/write路径边界通过。新增发布 workflow 尚待 Step 1 实现，不能把原 runner config 的 capability 当作已有真实发布能力。

## 10. 审核与状态规则

- 独立审核尚未发生；本轮没有 Executor report，所有 implementation/build/publication claim 均 `NOT EVALUATED`。
- Reviewer 必须直接访问源码/commit/实际 artifact/remote evidence，独立形成 verdict 和 evidence sufficiency 判断；Executor 全绿不能替代反例路线验证。
- 一次只激活一个顶层 Step。repair 子步骤继承父编号；implementation machine ACCEPT 与后续 workflow 状态单独核对。
- Step 迁移均引用固定 evidence 或显式 Human 决定；Static 变化必须由 Owner 授权。保留失败/retry/REJECT/Human gate，不能删历史制造 "从未出错"。
- 本任务初始无 Pending Tasks；待批准和尚未执行步骤是启动/验收 gate，不假装成 non-blocking pending。将来若引入 pending，必须标 deadline_step 和 `max(n-k-1, 0)`；激活到期 Step 前解决或升级 blocking。
- Residual: ad-hoc/未公证、minimum macOS 未定、未测硬件、single-writer/无并发保证等属于已披露范围限制，不在本任务无限扩展。
- Current Executor Handoff: 仅实现 Step 1 的发布工具/版本/测试/文档；按照当前 Reviewer 有界指令执行，不执行真实集成、构建发布或 Step 2-5 的远端 mutation。成功后停止于本步独立审核，不自行宣布整体发布成功。
- Next Direction: 完成 doctor/preflight 后启动 `REL1`；机器审核结束再独立复核，只有 Step 1 通过才运行受控 Step 2-3，随后停在 Step 4 Human gate。

## 11. 直接输入导航

- 交接: `/Users/smterpro/Workspace/framework-loop/1PCloop/.local/handoffs/whisper-release-automation-preparation-handoff-20260929.md`
- 新 Static: 同目录 `workload_static.md`。
- 已关闭 R2: `/Users/smterpro/Workspace/framework-loop/1PCloop/workloads/whisper_clean_fulltext_recovery_r2/workload_runtime.md`
- 全局治理: `/Users/smterpro/Workspace/framework-loop/1PCloop/docs/miniloop_static.md` 与 `miniloop_runtime.md`；当前认证 supersession 以 `/Users/smterpro/Workspace/framework-loop/1PCloop/docs/codex-runtime-homes/README.md` 和全局相关授权段为准，不复活历史 A/B live-role 描述。
- 普通运行边界: `/Users/smterpro/Workspace/framework-loop/1PCloop/scripts/run_mutation_loop.py`、`workload_operator.py`、`onepcloop.py`、`p63_evidence.py`；实现时先读实际依赖。
- Target 必读: `/Users/smterpro/Workspace/whisper/live_subtitle_generator-session-ui/PACKAGING.md`、`pyproject.toml`、`uv.lock`、双语 README；`packaging/runtime_manifest.json`、Release/Debug spec；`scripts/bootstrap_and_build.sh`、`bootstrap_python_env.sh`、`bootstrap_whisper_runtime.sh`、`build_macos.sh`、`build_release_zip.py`、`verify_packaged_runtime.py`、`package_runtime.py`。
- Target 历史参考: 同工作区 `docs/deployment_static.md`、`deployment_runtime.md`、`product_polish_static.md`、`product_polish_runtime.md`、`repo_map.md` 及相关 `testCodes/test_*packag*`、`test_release_zip.py`、bootstrap/build/manifest tests。它们提供工程约束/旧验收 evidence，不覆盖本任务权限或重新激活旧工作线。

## 12. 合同固定值

Static SHA-256: `47a90b305e5fa80eeec44dba75244e6a8482c1a121154c53a76f14d20dcc79a7`。

上述为获授权合同固定值；启动前核对实际文件 hash，不把合同批准当作 artifact acceptance。

## 13. REL1 implementation machine state

本机器块只授权 Step 1 的一次 `ACCEPT -> COMPLETED`。Step 2-5 不由同一 implementation checkpoint 自动激活，也不把一次 machine ACCEPT 当作真实发布。

<!-- 1PCLOOP_RUNTIME_STATE_BEGIN -->
{
  "schema_version": 1,
  "workload_id": "whisper_release_1_1_0_v1",
  "transition_mode": "reviewer_accept_once",
  "active_step": {
    "id": "REL1",
    "status": "ACTIVE"
  },
  "last_transition_id": null
}
<!-- 1PCLOOP_RUNTIME_STATE_END -->

## 14. REL1 首轮失败与安全 continuation -- 2026-09-29 本地日期

- Run `20260929T233941Z-37891`：doctor 9/9、preflight PASS，Reviewer instruction turn 成功；Executor 在 1200 秒上限后失败，没有完整 final receipt、实现 commit 或最终 Reviewer verdict。三层终态 `FAILED_CLOSED / NOT_APPLIED / PUSHED`，exit code 1；evidence commit `7c33a5478df19e6ed469e5633c3d6fb022a2dea5`，summary `/Users/smterpro/Workspace/framework-loop/1PCloop/evidence-summaries/20260929T233941Z-37891.md`。时间戳为 UTC 次日不改变本地日期；只记录 runner 的 timeout，不把它误标为 Reviewer REJECT。
- 两角色 process receipt 直接核验：原 auth 恢复成功、前后 hash 相同、active identity 不变、actual credential hits=0；对应拥有的 runner/child PID 已不存在。失败不是认证或目标代码已审核拒绝；未执行 main 集成、正式构建、tag/draft/upload/publication。
- 原 target HEAD 未变，留下 17 份未提交候选文件。没有 reset、stash、删除或由助手把草稿提交为“实现”。在原目录保留它们，另建干净 clone 继续同一 REL1，避免 dirty preflight 或覆写失败历史。
- 草稿快照: `/Users/smterpro/Downloads/whisper-release-1.1.0.zFGKQr/failed-rel1-draft.tgz`，SHA-256 `43f0d0ef6262228c99a04bd9cd3d94aa501cca4c9e80d1ab3dff6ecd9d1d84da`。仅含 17 个产品代码/测试/文档候选，未纳入 credentials、用户 Session、模型或 generated runtime。
- 草稿只是未接受的参考。新 Reviewer 应读取 archive 和源码、独立评估，再给 Executor 有界重用/修复指令；仅在当前干净 clone 内由 Executor 实现/测试/提交，不能把旧候选直接当作 acceptance。
- 旧 run 记录包含误用 Python 3.9 的 import failure，之后控制器测试曾由失败修到 15/15 PASS，但 ZIP 测试没有通过。助手使用现有产品环境 Python 3.12.14 对草稿做独立 focused 检查：43 tests，42 PASS/1 ERROR；错误是正式 entry 要求当前 repo 的 `.venv/bin/python`，不能借用另一 worktree 的 interpreter path。日志 `/Users/smterpro/Downloads/whisper-release-1.1.0.zFGKQr/verification-focused.txt`，SHA-256 `c8f256a839edc994fc7ad9c891350409db0dd1c4f1da133d852ac61f96ad9fb1`。这不是正式 build 或 task ACCEPT。
- 新 clone 已运行现有 `scripts/bootstrap_python_env.sh`，固定 uv 0.12.5 / Python 3.12.14 / frozen lock，environment smoke 5/5 PASS；只创建 Git-ignored `.tools`/`.venv`，source HEAD/branch/clean 均未变，未构建 App。后续 Agent 测试必须使用本 clone 的 `.venv/bin/python`，不要降级或放宽 interpreter gate。
- 直接代码检查还发现需要新 Reviewer 核验的缺口：草稿 `integrate()` 要求 main 已为 feature 祖先，无法处理本任务已知分叉；release contract 指向旧 feature ref 而不是新发布准备分支；merge/push 恢复和集成后测试 gate 不足。GitHub adapter 使用了本机 `gh api` 不支持的 `--repo`、`gh release upload` 不支持的 `--json`/错误 release-ID 参数，且用 text mode 下载 ZIP；这些不能靠 fake Publisher 全绿证明生产可用。本机 `gh api --help` 与 `gh release upload --help` 已只读核对，未调用远端写入。
- 还必须补查生产路径的实际 trust anchor、重新计算 journal hash 后的 state/identity 篡改、Human receipt 每次恢复重验、实际 extraction bytes/source proof、失败输出隐私，以及上传/公开后真实下载对账。上述是未接受草稿的调查方向，不代替新 Reviewer 的直接 verdict。
- continuation 使用新的 target path 和 state root，因此是同任务的 fresh implementation continuation，不冒充严格要求同 target identity 的 `retry` API，也不 resume 旧失败。新的 turn timeout 固定为 1800 秒，给剩余实现/测试留有边界；原 run 的 1200 秒历史和 config 不改。scope、模型/推理强度、账号固定机制和 Step 2-5 门禁保持原合同。
- 必须以正确 target-local Python 完成 focused/full strict 回归和真实 CLI adapter 无网络 fixture 测试；保留 1PCloop `REJECT -> REPAIR -> re-review`。continuation 完成机器审核前，Step 2-5 继续 queued。
