# Whisper 1.1.0 -- 正式构建前的生产部署决定

日期: 2026-10-03 America/Phoenix。
状态: `PROPOSAL / NOT AUTHORIZED OR DEPLOYED`。本文是主Reviewer整理的待Human决定方案，不是批准记录、生产key、Human产物PASS或已完成发布的证据。

## 1. 目前为什么不能直接交你验包

C2/C3 local实现已独立接受；完整strict日志279/279 OK，额度中断丢失原父进程的OS exit明确不可恢复，来源/环境/完整逐项结果已独立核验。接受证据见 [独立summary](../../evidence-summaries/whisper-c2-c3-independent-review-20261003.md)。现行安全合同要求实际集成/build只能从已审核、独立批准的受控入口执行。固定生产trust根当前不存在，Git普通push的认证在原控制器里被有意关闭，所以不只是少一份配置文件。

不能用测试key、普通journal的PASS、助手手动合并/拼构建命令或直接复用个人SSH文件绕开这些门禁。也不能把本地synthetic App/ZIP交你当正式产物验收。

## 2. 请求Owner决定的两件事

1. 是否批准部署受保护的发布入口、可信Python及独立签署/receipt控制路径。
2. 是否批准通过现有GitHub登录，为指定repo建立有界HTTPS Git与gh API认证桥。当前Git桥尚未实现，批准后仍须有界实现/测试/独立审核，不是假装仅复制配置就能push。

本对话已向Human提出异步选择，尚未收到具体决定。任何预选项不等于提交授权。若Human选择"先给方案"，也不自动等于允许部署。

## 3. 建议信任与签署方案

- 固定目录沿用 `/Library/Application Support/ClassroomTranscriberRelease/1.1.0`。
- root拥有的entry包含最终已接受工具集合及必要数据；按签署manifest的精确字节部署，不从未审核工作区动态import，也不使用caller提供的trust路径。
- 控制器Python须固定可信来源/版本和运行时完整性，不能把target现有可写`.venv`直接当作生产信任。具体安装路径/文件清单/hash在部署前单独列清供Owner确认。
- 只为本次1.1.0创建新的专用签署key，不复用个人SSH/key。私钥在独立受保护位置，root拥有0600；不进入target/framework、evidence、prompt、终端或通知。创建及使用均需明确Owner授权，本文未执行。
- 签署只服务严格区分的purpose: 最终Step1审核/集成许可、精确final-main独立审核、精确ZIP的Human决定、发布plan及必要恢复对账。没有Human对同一ZIP的明确PASS，就不能生成artifact-human PASS。
- 发布程序只验证receipt，不包含自签署或自授审核能力。外部签署控制路径必须能引用本对话实际决定/独立证据，不能按LLM prose或布尔值签名。
- root安装/签署若需要sudo密码，由Human在自己的终端输入；不索取或保存密码，不在未授权时探测sudo或尝试安装。

## 4. 建议GitHub认证方案及明确缺口

倾向使用现有GitHub登录及HTTPS，不复用Codex Mix OAuth、不读取个人SSH私钥，不改用户全局Git配置。

现C2已实现的gh协议:

- Owner签署精确resolved gh executable及SHA。
- 固定 `<trust-root>/github-auth`，root拥有0750；Owner明确选择仅用于该发布操作的专属group，签署具体GID，不自动使用staff或其它宽共享组。
- 仅允许root拥有0440、相同GID、regular/single-link/no-symlink的`config.yml`与`hosts.yml`。执行UID只有读/遍历权限，没有写权限。
- Python控制程序只验metadata，不读取token字节；native gh读取获准认证。无token环境注入、环境dump或认证内容入日志/evidence。失效/刷新需Owner维护，不静默改认证源。
- 当前没有创建该group/目录、读取现有gh凭据、导出token或更改登录。

尚需Owner授权之后实现并审核的Git桥:

- 只适用于Workflow作用域及固定HTTPS repo，legacy默认隔离不变。
- 用独立批准的精确native gh/固定credential桥处理Git凭据协议，不把token放进URL、Python变量、Agent环境、命令参数或证据。
- 可执行字节、认证来源、repo/ref、Owner permission reference必须外部签署绑定；无批准时仍停止。
- Git仍禁任意hooks/includes/aliases/redirects/global配置/其它helpers和force；每次使用前重验transport及任务identity。先local/fake进程矩阵，再真实只读身份/权限检查；实际普通feature/main push只由审核后的controller执行。
- 不能在获批准前新增桥或放松现有`credential.helper=`、`IdentityFile=none`、`IdentityAgent=none`规则。

这里的"现有登录"不授权助手显示/复制个人token。如何安全向受保护目录提供认证、是否使用既有安全存储以及执行身份/组，仍须Owner确认具体方案；不要求把token贴到对话中。

## 5. 批准后到人工验收的执行顺序

1. 接受最终C2/C3完整测试和独立复核结果；固定最终工具/合同/source identity。
2. 按Owner选定方案实现并独立审核必要生产transport扩展，再准备精确部署清单/签署输入。未审核的bridge不能直接启用。
3. Owner确认root安装、签署及认证来源/权限后，部署并验证protected entry及missing/wrong/revoked参数停止行为。不能声称纸面proposal即生产ready。
4. 受控`prepare`进行实际隔离集成与完整回归/普通push，停在final-main独立审核；主Reviewer核准确source/parents/tree/refs，可信签署路径记录该独立接受，不代替Human产物验收。
5. 同一受控入口在新attempt执行fresh正式Python/whisper/App/build/ZIP/解压自动验包，固定source、size/hash、保留App目录和完整evidence。
6. 停在父Step4，把精确ZIP和从启动开始的人工流程交Human。此时才是"你来验收"，不是现在的source/fixture测试。

## 6. 明确不会提前做的事

- 不把本proposal、代码测试PASS或Owner部署许可当作ZIP Human PASS。
- 精确ZIP Human PASS前，零真实tag/draft/upload/publish/latest写操作。
- 不覆盖历史Release/asset、不force、不clobber，不把未知结果盲目重试。
- 不改用户三个worktree、旧dirty草稿、真实Session/模型/旧App或历史失败evidence。
- 未批准敏感部署/认证时，已授权本地实现/测试仍可完成；之后准确停在Owner gate，不宣称整个发布或人工验收前工作已全部完成。

## 7. Owner回复时需要确认什么

可以先确认采用或修改本方案。真正执行前需明确: 是否允许新专用key及root-owned入口/可信Python；谁控制签署；执行UID/专属group；获准GitHub认证来源及最小repo权限；是否允许在受控部署路径中由native gh使用该认证。具体路径/hash由部署清单确定，不能用泛泛"都可以"省略身份检查。

最终发布权限仍以父Static为准，并依赖精确产物Human PASS。本文不扩大权限。
