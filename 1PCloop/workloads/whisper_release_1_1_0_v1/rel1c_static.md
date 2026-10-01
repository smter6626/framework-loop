# Whisper 1.1.0 REL1C -- Static 稳定合同

## 1. 身份与审批边界

- 父Task: `whisper_release_1_1_0_v1`；子阶段: `REL1C`，属于顶层Step 1的实现工作。
- 状态: `AUTHORIZED`。
- Human Owner: 本对话项目Owner。
- 父合同: [workload_static.md](workload_static.md)，SHA-256 `47a90b305e5fa80eeec44dba75244e6a8482c1a121154c53a76f14d20dcc79a7`。
- 配套状态: [rel1c_runtime.md](rel1c_runtime.md)。模板参考framework现有中文Static/Runtime模板。

Owner于2026-10-01审阅草案后明确说"批准启动，给出启动指令；然后写一个交接文档-给你自己看"，据此批准REL1C合同及三个有界子循环，启动由Human手动执行，首先只激活REL1C1。该决定不授权生产信任部署或真实发布；普通Agent权限仍不含真实push/merge/tag/API写入、正式App构建或治理修改。父合同有冲突时暂停，不能用本子合同扩大权限。

## 2. 用人类语言说明目标

补齐发布工具的后半程，让已审核工具能够把固定源码构建成一个可验收的ZIP，在你验收该ZIP中的App后，只发布同一份文件，并能证明下载到的文件没有变。

REL1C交付的是实现、测试和操作说明。它不是实际生产集成、正式构建或人工黑盒验收。整个Step 1通过后，才依次进行真实集成、构建、你的最终ZIP验收和发布。

## 3. 范围与交付物

1. 构建与artifact控制: 接续已接受的集成事实，调用正式构建/验包链，固定source、工具/合同、App、ZIP size/hash和保留的解压目录；提供准确状态及停止/恢复行为。
2. Human gate: 区分实施ACCEPT、集成许可和最终artifact PASS；只接受独立可信控制路径记录的Owner决定，绑定具体产物而非一个布尔值。
3. 发布adapter: 固定GitHub repo/tag/title/唯一资产、中英notes；可靠处理tag、draft、上传、下载比对、正式/latest及公开后复核。
4. 恢复与串联: 副作用前持久意图，未知结果先对账；已完成动作不重放，无充分证明时停止。复用REL1B，不复制第二套Agent loop。
5. 修正PT-REL-01的notes事实与直接绑定hash/tests，更新双语用户/开发者说明，提供从指定解压App启动的人工流程。

不实现新ASR/UI/模型功能、跨平台、DMG/Actions/公证、框架认证或runner改造；不安装生产trust、不创建/读取个人私钥、不改历史Release或复制用户Session/模型。

## 4. 必须保留的稳定约束

### 固定产品与工程边界

- 产品/tag `1.1.0`，标题 `Classroom Transcriber 1.1.0`，repo `smter6626/live_subtitle_generator`，host `github.com`。
- 唯一主asset `ClassroomTranscriber-1.1.0-macOS-AppleSilicon.zip`，内容 `ClassroomTranscriber.app`；arm64、模型外置、ad-hoc、未公证。
- 正式Python/uv/whisper/第三方pins、bundle identifier和麦克风声明不变；父合同固定的canonical origins不改。
- 继承REL1A的版本/manifest/provenance/ZIP边界和REL1B的外部批准、原子持久化、真实Git事实和gate。必要耦合调整必须进入精确allowlist、保留负向验证并接受重新审核，不使旧局部ACCEPT自动扩张。
- notes修正只改变说明及直接hash绑定，不改版本/repo/asset/schema/签名路线；不能把hash改成从任意输入自动学习来绕过固定身份。

### 构建与包身份

- 仅在整个Step 1及精确集成结果被接受后，于任务管理的Downloads隔离目录从固定source正式构建。不能以当前实现branch HEAD或旧dist冒充最终main source。
- 原正式构建入口、Runtime verifier、source/App provenance和ZIP round-trip必须实际调用。构建前环境来源要可证明，禁止执行不可信ignored解释器或依据版本自报建立信任。
- 复用REL1B的invocation-local证明原则，但不能原样套用"构建过程所有文件不得变化": build/dist、生成icon及构建缓存的预期变化须由已审核构建协议精确限制；受测源码、工具、pins和非预期环境替换仍必须拦截。
- artifact/extraction与可清理build工作区分离。重新构建使用新attempt及新输出，不覆盖已固定ZIP、已验收解压目录或历史证据。
- 本地build provenance、manifest、日志hash及journal checksum仅提供身份/事实信息，不授予实施接受、Human PASS或发布权限。

### Human gate和发布

- 实施ACCEPT和Owner集成许可不能代替最终artifact PASS。Owner决定必须绑定repo/version、source、ZIP路径/size/SHA-256、App身份/保留解压目录、合同/工具身份及决定reference；字段和可信receipt协议由实现提出并审核。
- 普通Executor、journal或`--human-pass`之类自述不能制造可信PASS。测试签名/fixture PASS不能通过生产入口；可信receipt缺失、撤销、目标不符或实际ZIP/解压App变化时无写操作。
- PASS前禁止真实tag/draft/upload/publication；PASS后每阶段仍重验输入。改码、重建或ZIP bytes变化必须重新自动验包及人工验收。
- tag绑定完整source SHA；annotated tag须核peeled commit。不得由release create隐式选择default branch建tag，不使用force/clobber或自动生成未审核notes。
- 发布只能使用同一已验收ZIP。先核draft资产的真实下载size/hash再公开，公开后重验正式/latest、notes、tag、asset ID及公开下载bytes；服务字段的digest不能代替实际下载比对。
- 未知网络结果先读取真实对象；不能因为重算journal或同名对象出现就重复create/upload/publish。无法证明对象属于本任务，或陌生tag/release/asset、字段/bytes冲突，必须Human Gate，不删除重建。

### 隐私、权限和状态

- 新入口和helper须与REL1B同样受独立批准及完整工具字节绑定保护。不能为了可调用改用caller-selected trust或取消protected entry检查。
- 实现测试只使用新Downloads fixture、本地bare remote、synthetic bundle和受控fake GitHub响应/进程。禁止测试向真实GitHub写入；测试入口不得成为生产绕过开关。
- Git/gh transport的真实部署尚需Owner决定。禁止顺手读取token/private key、运行auth token/login/setup-git、改用户global Git配置或放松REL1B认证隔离。
- GitHub认证与Codex Mix额度账号是不同用途；不得从Codex auth.json提取OAuth token供Git/gh使用。
- 本地journal/status/公共reason不含认证材料；使用固定错误码和单行、bounded可读提示。schema version、字段/类型、重复key、权限、symlink、路径及原子写入均需验证。
- status只读，不联网副作用、创建目录、修复、构建或接受人工决定。发布状态与implementation logical/Runtime/evidence状态分开，不把PUSHED等同发布成功。

## 5. 可修改范围与变更控制

允许范围是产品仓库的release workflow/helper、直接测试、notes及直接身份绑定、双语README/PACKAGING/repo_map。每次loop只处理Runtime所编译的一项，Reviewer须固定具体路径，不能一次实现整个REL1C。

直接耦合到accepted基础层时，先说明必要性和影响，保留旧安全性质及回归。更改父/已关闭子Static、framework、认证、pins、产品行为、可信来源/签名路线或真实外部权限均需要新Owner决定；不由Runtime静默批准。

## 6. Acceptance Criteria

| ID | 必须证明什么 | Evidence与拒绝边界 |
| --- | --- | --- |
| C-AC-01 | 新控制链真实且权限分离 | 实际CLI/生产调用链及精确tool-set绑定；未审核/缺trust/未完成阶段不能启用后续动作，无第二套Agent loop。 |
| C-AC-02 | 构建只消费已接受的精确source | 实际构建入口调用顺序与fixture；source/工具/环境 drift、旧dist、dirty、失败/伪造provenance均停止，不伪称fixture为正式build。 |
| C-AC-03 | artifact和人工目录不被替换 | size/hash/App tree/extraction、no-clobber和安全路径实测；失败/重试不覆盖旧artifact，包装调用进入原ZIP/verifier链。 |
| C-AC-04 | Human PASS无法自授或错绑定 | 独立fixture批准通过；缺失/假签名/撤销/旧source/换ZIP/换App/错目录拒绝，零真实tag/API副作用。 |
| C-AC-05 | GitHub adapter字节和目标安全 | 固定repo/host/明确method与UTF-8 JSON或文件传输；中文、多行、@/引号/backtick/控制字符和错误responses实测，秘密/任意命令不进入终端，未批准时adapter不发写请求。 |
| C-AC-06 | 发布完整且同包 | local tag/peeled commit与fake draft/upload/download/publish/latest全链；唯一asset、notes/IDs和下载bytes一致；冲突/陌生对象和历史overwrite拒绝。 |
| C-AC-07 | 中断恢复无重复/误动作 | 意图、build、tag、draft、upload、publish及download边界的crash/未知结果/合法重算journal反例；只能机械对账或明确停止，不凭记录中的PASS跳gate。 |
| C-AC-08 | 全父合同覆盖与文档闭合 | REL1A/REL1B及当前完整strict回归、独立端到端fixture、父REL-AC-01至08的实现coverage；notes与绑定同步、历史/候选/真实发布状态正确。真实构建/黑盒/平台发布仍属父Step 2-5。 |

## 7. Evidence与未来人工复测

tracked compact evidence及进度留在framework，稳定产品说明和工具留在target；不重建逐轮change_records。原始测试/构建/adapter日志、fixture及checkpoint保持本地，记录完整commit、size/hash/locator，不提交真实批准、私钥、凭据、raw prompt或用户转录。

真正人工复测仍是父Step 4: 启动该最终ZIP解压App，验证模型、麦克风/Start/Stop、Session重置、复制、窗口/滚动、中英工具栏、录制中与停止后重命名、全文恢复Yes/No。记录实际硬件/语言/模型和限制，不要求重测所有语言。源码/Qt offscreen/fixture及旧App PASS均不替代本gate。

## 8. 仍需Owner决定的生产事项

- 独立生产trust、protected entry及可信签署/receipt控制路径如何部署；方案可继承REL1B，但本阶段不安装或生成生产key。
- Git普通push和GitHub API如何使用被批准的现有认证，最小权限与工具来源怎样固定；本合同不选择个人key、token存储方式或扩大读取权限。

以上不阻止批准后的纯实现/local测试，但阻止真实Step 2-5和生产可用性声明。若实现必须先获得新增敏感权限才满足criterion，立即停机请求Owner，不将缺权限降级为普通pending。父合同定义的最终产物Human PASS仍独立生效。
