# Whisper 1.1.0 -- 正式包已通过自动与独立审核，等待人工测试

日期: 2026-10-09 America/New_York。本文是紧凑验收记录，不是Human PASS或发布授权。此前失败、REJECT和修复记录保持在task-local Runtime第23-25节，本文不覆写历史。

## 现在的结论

当前唯一步骤为精确最终ZIP的Human黑盒验收。修复后源码的真实完整回归297/297通过，正式fresh App/ZIP构建完成，主Reviewer独立验包通过。没有创建1.1.0 tag/draft/Release、上传或发布；也没有构造Human receipt。用户三个工作树、旧失败目录和诊断包均保留。

- 版本: 1.1.0，macOS Apple Silicon/arm64，模型外置，ad-hoc签名，未Developer ID签名/未公证。
- 正式source: `014a609fcc7ab26be8820f4399cdaa19225498e1`；tree `bac9cd36aa9d2adf646f8b62be43a95599b1c87d`。
- 父提交: `[79be5292e217cc600f6191882641320ca2437ce4, 2c3e284d2b1b2d748aca8c0c05b8e795452a16bb]`。
- actual merged-source strict: 297/297，4345.282s，controller/collector实际0/0；actualsource/environment前后unchanged，34工具和110tracked源码byte/mode固定。未假称另跑第二份完整回归。
- 正式build: 原CLI prepare、原BuildController/6 checkpoints、fresh固定Python/CMake/whisper/原PyInstaller/App/Runtime/provenance/ZIP链，328.533s，实际controller/collector0/0。workflow ARTIFACT/sequence5，human_receipt=null。
- 独立审核: 实际ZIP与保留App对应、构建App与保留App相同、版本1.1.0、provenance/源码绑定、原6检查点及日志hash、保留App的原Runtime verifier另跑exit0、codesign --verify --deep --strict exit0。state和receipt bytes前后不变。

## 只测试这一份正式包

ZIP:

`/Users/smterpro/Downloads/whisper-1.1.0-lightweight-retry4.KbFkF4/workflow/artifacts/attempt-286e5589e09943b39aa38553f24fa31c/ClassroomTranscriber-1.1.0-macOS-AppleSilicon.zip`

- Size: `48307378` bytes。
- SHA-256: `fbe14de7d68c519ddb817ef1f45166f3e39a24f0a27d290cd82d9c2c20717bdb`。
- Artifact ID: `616c47bd2585ba69b18001d3935e3308293b73d827c8d429092e5fb6c3d5ff80`。
- App tree SHA-256: `5be21a2a4860e5918cdd6e4bcdda2ddbd526b35a7a392e77abd129508605a379`。

已由原ZIP流程提取并验证的App:

`/Users/smterpro/Downloads/whisper-1.1.0-lightweight-retry4.KbFkF4/workflow/human/attempt-286e5589e09943b39aa38553f24fa31c/ClassroomTranscriber.app`

不要测试旧安装App、源码ui_app.py、旧失败attempt或native diagnostic ZIP来替代此包。不要修改/覆盖/移动当前固定ZIP及保留App，直到发布/恢复结束。

## 人工验证 -- 从启动开始

1. 先退出旧Whisper App，运行:

```bash
open -n "/Users/smterpro/Downloads/whisper-1.1.0-lightweight-retry4.KbFkF4/workflow/human/attempt-286e5589e09943b39aa38553f24fa31c/ClassroomTranscriber.app"
```

不需要bootstrap Python或whisper。若macOS提示未识别开发者，先用Finder右键该App -> 打开，按标准GUI确认；若仍阻止，反馈准确提示，不修改签名或移除安全属性。

2. 新建仅用于测试的输出目录，不污染项目目录:

```bash
mktemp -d /Users/smterpro/Downloads/whisper-1.1.0-human-test.XXXXXX
```

在App“选择输出位置”中选择刚输出的路径。可以选择已有可用模型；检查模型管理界面正常，不必重复下载全部模型。

3. 基础链路: 授予麦克风权限，真实说话/转录，Stop后确认输出和App正常。再次Start时表格应自动清空并开启新Session。用实际可用语言测试即可，不要求一次覆盖全部语言；记录模型、语言、macOS/机器和未测试范围。

4. UI和复制: 缩小窗口检查左侧滚动及按钮可达性；中英切换；“定位Clean”和“复制Clean路径”同一行；“复制新增文本”在Clean上方右侧、跳到最新左侧；重命名按钮在Clean上方左侧。第一次复制应包含当前Clean全文，第二次只复制新增行，无新行不应改变剪贴板。定位/路径复制应指向当前文件。

5. 重命名: 录制中改为一个中文名称，确认后续转录仍进入新文件；Stop后再改一次；.txt后缀固定，输入无需后缀。已有同名文件不得被覆盖。再次Start后对象应变为新Session的clean.txt，不能修改上一Session。

6. 全文恢复Yes/No: 只用刚创建的临时Session。先有几段Clean文本，然后将当前Clean TXT移到Session目录之外的临时备份目录(不要删除真实转录)。再次点击重命名，输入新名称，确认出现路径不可用/恢复提示。

- 选No: 不应创建或切换新文件，转录仍可继续；No不承诺文件关闭后在原路径持久保存，不据此宣称文件已恢复。
- 再尝试选Yes: 应在原Session目录创建新名称.txt，包含此前完整Clean历史，后续文本继续进入新文件；复制路径和定位都应跟随新文件。

7. 正常Stop和退出。若失败，保留弹窗/截图以及测试Session的session.log，说明操作顺序，不删除日志或包。

测完回复此“retry4正式包通过/不通过”，并明确“允许发布同一ZIP”或“暂不发布”。没有回复、仅之前源码App通过，均不能转成该包Human PASS。临时测试输出目录在反馈后可另行清理；正式ZIP、保留App和审计目录当前仍需要保留，之后会提醒有界清理。

## 直接证据和边界

- task-local Runtime: `1PCloop/workloads/whisper_release_1_1_0_v1/rel1c_runtime.md` 第23-25节。
- actualintegration raw: `/Users/smterpro/Downloads/whisper-1.1.0-lightweight-retry4.KbFkF4/integration-operation/operation-result.json`，SHA `832ab3bdb77fde0b06611d49daab2f02b63dba096eb8763fac47c79aaa061bcd`。
- strict raw: 同根 `integration/evidence/strict-d64331a00cd3406faf3e348a7ab937c1.log`，SHA `ceabe327d1666135474df93a972bfb21331a4b2cd3df8a40296ddba3703ecc01`。
- formalbuild raw: 同根 `build-operation/operation-result.json`，SHA `8af287c4310156b6311e62bb5ee7451b50342059d557732dcfacb22b8243d966`。
- build/package raw: 同根 `workflow/evidence/attempt-286e5589e09943b39aa38553f24fa31c/{build,package}.log`，SHA分别 `0cfed7ffae060fe3cb70f0642a99c5d536a016f799a1e85b3bc4177355cff90d` / `487c1e6aa20b97f9d2bcbe40dcb6081a811a7ffa16b04e42abdfd407296e196a`。
- 主独立source报告: `/Users/smterpro/Downloads/rel1c-lightweight-review-environment.BQuaEt/retry4-actual-final-main-review.json`，SHA `db3d68db27af1bdb435da860a7216b6637ab872502a5c3c81d5befb699ece8e8`。
- 主独立artifact报告: 同根 `retry4-independent-artifact-review.json`，SHA `4554ad92a24a50933a623387b2b6a8d68cf7bccf13996b267db113e366b27936`。
- build provenance SHA `e353cbb2a0dd31739036a58ada902bcdd9d8801cf7454f0b5b0ba22015f597c9`，独立保留App verifier log SHA `4097890935c36d19430e2f95731ef22218dac728853def125177846462acb816`。

当前仍single-writer/no-concurrency、不抵抗同UID恶意伪造批准，未公证，不扩大硬件/语言支持声明。所有认证沿用正常nativeGit/gh，未复制凭据或部署旧root/key/group机制。发布必须重验相同artifact、真实Human决定、fixedrepo/tag/assets及远端下载bytes；在此之前不进行真实发布写操作。
