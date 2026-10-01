# Whisper 1.1.0 REL1C -- Runtime 初始化草案

## 1. 现在做到哪里，用人类语言说明

发布工具的"版本与验包基础层"和"合并管理员"已经审核通过。下一步不是你马上测App，而是让1PCloop补完构建、人工批准和发布管理员。代码完成并审核后，才真正集成/构建，再交给你验收最终ZIP解压App。

- 父Task: `whisper_release_1_1_0_v1`；子阶段REL1C；继承顶层编号 `k=1`。
- 状态: `QUEUED / DRAFT DOCUMENTS READY / AWAITING HUMAN REVIEW`。
- Verdict: `NOT EVALUATED`；唯一Active Step: 无。
- 建议首个实施子步骤: `REL1C1`；C1/C2/C3均QUEUED，不在本次文档准备激活。
- Static: [rel1c_static.md](rel1c_static.md)，SHA-256 `0078138f95b3bddac3065e8f4c9fa451391641e467b0e4df4ff101e843b23a83`；父Static SHA-256 `47a90b305e5fa80eeec44dba75244e6a8482c1a121154c53a76f14d20dcc79a7`。
- 最后更新: 2026-10-01，America/Phoenix。
- Human本次要求准备Static/Runtime，未要求启动。无REL1C config、ACTIVE machine block、run或实现commit；后续批准后再创建独立config/state及C1的一次machine transition。

## 2. Completed与不可丢失的背景

| 已接受结果 | 当前语义 | Evidence |
| --- | --- | --- |
| REL1A，accepted b28027927f23c3a2333b1ae9da0dd6989901e616 | 版本/manifest/App provenance/ZIP边界基础层。两个全绿后REJECT及修复历史保留，不把基础层接受当成新App验收。 | [独立summary](../../evidence-summaries/whisper-release-rel1a-independent-review-20260929.md)，父Runtime第17节。 |
| REL1B，accepted 91e547918a20383f9dc938440db890a7dae85226 | 批准/journal/分叉集成/gate/恢复。Machine run20261001T063859Z-6937正常ACCEPT；本对话fresh strict204/204，817.818s和组合伪造/只读验证通过。 | [独立summary](../../evidence-summaries/whisper-release-rel1b-independent-review-20261001.md)，[已关闭Runtime](rel1b_runtime.md)第17节。 |

REL1B曾模型拒绝、1800s与3600s超时。最后复用已核验evidence、补receipt/review才完成；说明不能把整个REL1C塞进一个turn或反复从零重写。旧configs/checkpoints/失败summaries、所有dirty候选及用户三个worktree保持不变。

本次准备快照:

- Framework main/local/origin `9edddbb3171c3d9007da04650124d680c0e73acc`，clean；本次正常文档提交会前进framework，不改变产品源码。
- 建议后续target沿用 `/Users/smterpro/Downloads/whisper-release-1.1.0.zFGKQr/implementation-rel1b-continuation-02`，branch `codex/release-1-1-0-automation`，clean HEAD91e5479；这不是最终release_source_commit。
- REL1B封存Runtime SHA-256 `4a2da8e35d2eace553031681936910972a98781b1ec39d5a98a67b659f72ef43`，本次不修改。
- 实际role配置Reviewer `gpt-6.1-sol/xhigh`、Executor `gpt-6.1-sol/high`，Codex CLI0.159.2。只读核验，未改配置或账号；新run绑定当时Codex Mix active账号，不硬编码历史C。
- 当前gh `/opt/homebrew/bin/gh`，version2.96.0；只查version/help，未检查或读取登录凭据、未运行真实API。
- 当前无正式新App/ZIP、Human artifact PASS或发布对象验收。生产trust/entry与认证transport未部署/验证，REL1B的local bare成功不能补足这些事实。

## 3. 编排建议 -- 三个小循环，不一次做完

| 子步骤 | 唯一交付 | Gate与后续 |
| --- | --- | --- |
| REL1C1 | 构建/固定artifact/Human receipt协议与notes修正 | machine + 本对话独立接受后才激活C2；不做GitHub adapter或真实build。 |
| REL1C2 | tag/draft/upload/download/publish/latest adapter及恢复 | 基于C1已接受HEAD继续；只fake transport/local Git，不打真实tag或发写API；接受后激活C3。 |
| REL1C3 | REL1B+C1+C2的统一workflow、端到端fixture、操作/部署proposal与全Step 1复核 | 先验收全部父合同的实现coverage，不把local测试当成生产门禁已通过。 |

C1/C2/C3是父Step 1的子步骤，不消耗顶层pending倒计时。各自使用新run/config/state，正常后继提交；旧终态不能resume。每次machine ACCEPT只关闭当前子步骤，下一项由治理在独立复核后激活，任何时候最多一个ACTIVE machine block。

生产执行仍依父计划: 整体Step 1通过 + Owner部署/transport决定 -> Step 2受控集成并固定main source -> Step 3正式build/ZIP自动验包 -> Step 4你验收该ZIP中的App -> Step 5只发布同一ZIP。不是普通Agent loop一接受就直接发布。

## 4. 待批准REL1C1 -- 精确执行范围

Objective: 在91e5479基础上，建立可测试的artifact/Human gate控制层，修正notes及直接hash绑定；以正确证据交回审核，不扩大到C2/C3。

### 开始前必须读取

1. 本Static/Runtime、父Static/Runtime；REL1A和REL1B独立summary及相关真实evidence，不能只根据交接记忆。
2. Target下 `scripts/release_identity.py`、`build_release_zip.py`、`bootstrap_and_build.sh`、`bootstrap_python_env.sh`、`bootstrap_whisper_runtime.sh`、`build_macos.sh`、`verify_packaged_runtime.py`、`package_runtime.py`。
3. `scripts/release_{approval,journal,integration,controller}.py`，确认新的入口不会绕过已接受trust/entry和工具集合。
4. `packaging/release_contract.json`、`runtime_manifest.json`、正式spec、`.python-version`、`pyproject.toml`、`uv.lock`、notes及直接tests/双语README/PACKAGING/repo_map。

### 允许路径 -- Reviewer须落实为具体allowlist

- 建议新增 `scripts/release_workflow.py`、`release_workflow_state.py`、`release_artifact.py`、`release_human_gate.py` 及四个对应 `testCodes/test_release_*.py`，分别隔离CLI/状态/包身份/人工批准。这是候选分工，不要求制造空模块；若必要名称/路径变化，先明确有界instruction，不能无界添加helper。
- `scripts/release_approval.py`及直接approval tests: 仅为新入口、完整trusted tool set和receipt验证进行必要耦合，不取消protected entry或fixture隔离。
- `RELEASE_NOTES_1.1.0.md`、`packaging/release_contract.json`、`scripts/release_identity.py`、`testCodes/test_release_identity.py`: 仅修正notes事实、计算固定notes SHA并同步JSON字段/EXPECTED_CONTRACT常量/直接tests。当前两处hash同为d7c90520a247cf2a743dc780e38a5a0abd5bc309a024e2c3d4f91f73bbaab938，必须一起改；不扩大schema或采用自动接受任意notes的逻辑。
- `testCodes/test_release_zip.py`及四份说明文档中直接C1操作/候选边界内容。
- 不修改其余accepted REL1A/REL1B helper、构建脚本、spec/manifest/pins或产品代码；若证明现有接口无法安全耦合，先提出具体path/影响/回归的bounded proposal，不先修改。

### 必须实现/验证

1. 从独立批准的最终source/集成事实进入build；以受管理的新attempt调用正式链，验证清洁源码、工具/合同/环境来源、App provenance和自动验包。单纯hash旧App或journal的BUILD_OK不构成fresh-build。
2. 验包后固定ZIP size/hash、App tree/versions、source/工具/合同、保留解压目录和stage outcome；重试不覆盖旧产物、路径/symlink/partial state/输出冲突均拒绝。
3. 明确新build会生成build/dist/icon/cache等预期输出，不能机械复用REL1B的完全不可变执行树快照。把允许变化限定为已审核正式构建链的生成路径，禁止借此允许替换bootstrap/解释器/源码或消费来源不明旧dist。
4. 设计独立可信Human receipt并测试真实fixture签名路径。integration owner批准、旧App/source PASS、Executor自述、可重算journal、错包/错source/撤销/重建都不能启用发布。缺生产trust时新入口无动作；未来publish命令在C1仍拒绝。
5. notes清楚列多语言、Session清屏/增量复制/Clean路径、窗口滚动、工具栏/重命名/R2全文恢复；把1.0已有icon/model反馈/download progress与本版新增区分，写中英模型外置、ad-hoc/未公证和标准macOS GUI打开说明。不写已经发布或扩大所有语言/机器验收范围。
6. 严格新schema、权限/原子persist/可读状态/隐私，测试build失败和中断、重新hash manifest/receipt/state、换包/换解压App、调用顺序及无真实外部写入。metadata保存在local文件，终端只给简明阶段/结论。

Required evidence: 修改逻辑和依赖影响、精确diff/commit/parent/allowlist、focused/full日志locator/hash、直接CLI和信任/换包反例、B-AC不弱化与C-AC-01至04/07/08局部coverage、未实现/未部署边界。Self-check全绿不等于最终验收。

## 5. 测试预算、证据与报告习惯

- 沿用"先逻辑 -> 读取影响/依赖 -> 微调 -> 最小实现 -> 测试 -> 审核/治理"的规则；Executor不改Static/Runtime。
- 实现turn建议沿用3600s、maxcycles4、progress15s；这不是已创建的启动config。新run实际模型/账号/配置由启动gate再核。
- 当前完整回归已测约14分钟，至少预留15-20分钟用于必要full strict以及receipt/提交收尾；先完成小范围实现，不临近上限启动额外昂贵smoke，不把测试放后台后假装已结束。
- 默认运行当步focused和当前完整 `.venv/bin/python -B -W error::ResourceWarning -m unittest discover -s testCodes -v`，QT offscreen、TMPDIR指向新Downloads fixture。不用其它worktree或system Python代替锁定环境。
- 真实formal build不在实现turn执行。测试命令/产物清楚标注synthetic/callback/fake transport，不冒充正式包或Human PASS；昂贵端到端smoke留在C3，不加入discovery制造递归。
- 若无改码且有充分source/环境/log hash/provenance，来源核验后可显式复用已有效的evidence；改码/过期/缺失则重跑相关验证，不以预算不足取消gate。
- 未完成/失败仍及时输出完整schema-valid receipt，交回窄REJECT/repair或Human Gate；不fabricate全绿，不自行接受或激活下项。
- 原始fixtures/logs放Downloads，保留失败/history。ACCEPT的file/test/artifact引用必须是target/current run root内绝对现存路径；需要导入时只复制经隐私/hash验证的非秘密日志到target已ignored logs子目录，不复制auth/keys/raw Session，不改原件。

## 6. 待审与生产Human Gates

| 项目 | 当前影响 | 决定前禁止什么 |
| --- | --- | --- |
| Owner批准本REL1C草案及三循环安排 | 阻止启动C1，不是一般pending。 | 创建ACTIVE machine state、启动Agent。 |
| 生产trust/entry及签署/receipt路径部署 | 不阻止批准后的local实现/fixture；阻止真实Step 2-5。 | 安装root目录、生成/读取生产私钥、自授批准或宣称生产已可用。 |
| 被批准的Git/gh认证transport | 不阻止fake/local adapter测试；阻止真实push/API与生产可用性声明。 | 读取token/private key、改变auth/global Git配置或放松隔离。 |
| 精确最终artifact的Human PASS | 未来Step 4，实际产物身份尚不存在。 | 提前tag/draft/upload/publish，不接受泛指的旧人工PASS。 |

需要敏感部署、认证改变或扩大accepted基础层时，另给明确方案/范围/代价，请Owner决定；本次没有偷偷执行这些动作。

## 7. Pending与deadline gate

父Runtime是唯一pending authority，本表只引用，不创建另一个倒计时。

| ID | 内容 | deadline / k / remaining | 状态与关闭条件 |
| --- | --- | --- | --- |
| PT-REL-01 | notes事实/新增旧功能区分/GUI说明 | 3 / 1 / max(3-1-1,0)=1 | OPEN_NON_BLOCKING；拟在C1修正notes及固定hash/tests并独立接受，再由父Runtime登记RESOLVED。未实施前不关闭。 |

C1/C2/C3不推进顶层k。Step 2前必须先整体Step 1接受及部署/transport门禁就绪；Step 3前PT-REL-01必须RESOLVED。没有为赶进度延期或把它改为永久pending。

## 8. Independent Review初始状态

REL1C没有实施commit/测试输出，C-AC各项均 `NOT EVALUATED`。Reviewer必须直接检查实际代码、artifact/test输出、fake API请求字节/local Git refs和独立反例，不能继承Executor或旧REL1B结论。每个子步骤机器接受后仍有本对话独立复核；C3检查全父合同的实现coverage，而不是直接宣布真实发布AC全通过。

## 9. 官方接口与已重读依赖的风险提示

- 已读本机gh2.96.0的create/upload/edit/api help及官方[create手册](https://cli.github.com/manual/gh_release_create)、[upload手册](https://cli.github.com/manual/gh_release_upload)、[api手册](https://cli.github.com/manual/gh_api)。CLI/API细节在C2实现前重新核对，不复制早期未接受草稿的错误argv。
- create在tag缺失时有自动建tag行为；正式adapter须先明确验证tag/peeled source，禁止隐式default branch。upload的clobber会先删除旧asset，明确禁止。JSON请求应明确method，并通过UTF-8 JSON/file bytes传输，不把多行notes塞进会解释@/类型的参数；用fake进程捕获实际stdin/argv验证。
- REL1A的正式ZIP helper已经返回artifact path/size/hash和持久extracted App；REL1C应记录并保护这些实际返回值，不重造旁路。它也严格比对release_contract与EXPECTED_CONTRACT，因此修notes必须同步两处固定值和tests。
- REL1B生产环境禁credential helper、SSH agent/identity，故本地Git success没有证明真实GitHub认证可用。C2/C3必须提出可审核transport边界，不以获得"自动化可跑"的理由放松认证或读取秘密。
- Legacy候选含错误trust选择和gh参数，仍是未接受历史输入；不恢复旧authority、不重新解包旧全流程controller。

## 10. 下一步及状态迁移

Previous: REL1A/REL1B accepted，REL1C未准备。Human本次请求触发仅文档初始化；Current: REL1C DRAFT/QUEUED、无Active Step。

你审阅本Static/Runtime后，若批准三循环安排，下一次才激活C1、固定Static hash、创建独立operator config/state、核target/refs/认证/doctor/preflight并给启动指令。启动由当次Human选择手动或明确要求助手启动，不继承旧run启动方式自动执行。

本次无模型变更、Agent调用、新clone/正式build/集成/tag/API、Human receipt创建或清理删除。父/REL1B Static和封存Runtime保持原样，global只更新导航与高层方向。
