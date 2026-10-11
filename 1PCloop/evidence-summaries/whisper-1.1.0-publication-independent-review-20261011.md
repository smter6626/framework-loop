# Whisper 1.1.0 -- Human 验收、同包发布与独立复核

日期: 2026-10-11 America/Phoenix。Verdict: `PASS / RELEASE VERIFIED / TASK CLOSED`。

## 真实授权与验收范围

Human 回报精确正式包手测未发现异常，随后明确要求“现在发布release，你来操作”，并在获知 Homebrew 权限检查影响后批准“可以改，改完发布”。没有把旧源码 App 或诊断包的通过结论用于本次发布。

结果文件只读校验确认使用正式 retry4 保留 App、large-v3、英语、中文 UI，约25分26秒，218块全部按顺序处理，Raw568/Clean514与日志一致，按实际去重算法重算的 Clean 逐字节一致，尾段和正常关闭完整。一个0.011s启动漂移警告已处理；保守去重仍保留短句/标点，重叠切片最大时间回退2.72s。没有原始音频真值，不声称每句话准确或全部交互/语言/模型均逐项实测。私有 Session/转录未复制到 Git。

## 固定发布事实

| 项目 | 实际核验 |
| --- | --- |
| Repo | `smter6626/live_subtitle_generator` |
| Release | [Classroom Transcriber 1.1.0](https://github.com/smter6626/live_subtitle_generator/releases/tag/1.1.0)，ID `409876735` |
| 状态 | 正式/latest，draft=false，prerelease=false，published_at `2026-10-11T19:39:52Z` |
| Tag | `1.1.0`，annotated object `32b21b1b2f660d2315d60569cae94ecd5b3b440b` |
| Source / peeled commit | `014a609fcc7ab26be8820f4399cdaa19225498e1` |
| Source tree | `bac9cd36aa9d2adf646f8b62be43a95599b1c87d` |
| 唯一主资产 | `ClassroomTranscriber-1.1.0-macOS-AppleSilicon.zip`，ID `631624978` |
| 大小 / SHA-256 | `48307378` / `fbe14de7d68c519ddb817ef1f45166f3e39a24f0a27d290cd82d9c2c20717bdb` |
| Artifact ID | `616c47bd2585ba69b18001d3935e3308293b73d827c8d429092e5fb6c3d5ff80` |
| Workflow | publication `COMPLETE`，intent=null，最终真实进程exit0 |

人类已验收本地ZIP、草稿实际下载、公开实际下载及主助手独立直接下载均为同一大小/hash。主复核latest API、完整notes、唯一资产、正式URL、远端tag/peeled source。旧1.0.0/0.2.0/v0.1.0 Release IDs仍存在，没有删除、覆盖或重复上传。

## 真实中间失败与有界恢复

1. 最初预检拒绝 Homebrew Cellar 的0775，不发生远端写入。Human明确批准暂改0755并恢复后，原Publisher创建精确tag和草稿，但因GitHub实际草稿html_url为 `untagged-*` 而 `REMOTE_RELEASE_CONFLICT`，未上传；权限已恢复。
2. 主按前置远端不存在、当前精确ID/notes/source/tag/草稿更新时间和本次调用历史独立对账，保留原状态，不重建草稿。新增任务本地 exact-ID draft-URL adapter，原产品工具/source/App/ZIP不修改。13个边界检查通过。
3. 原发布状态机随后上传同ZIP，但实际草稿资产browser_download_url也为 `untagged-*`，触发 `REMOTE_ASSET_CONFLICT`，未公开；权限已恢复。
4. 再次按精确Asset ID/size/digest/更新时间独立对账，保留原DRAFT reconciliation副本。adapter扩展仅接受同一已观察草稿资产链接，且实时要求该Release仍为草稿；公开Release和资产仍使用原正式URL检查。最终23个release/asset正负边界检查通过。
5. 复用原Publisher.execute、receipt/source/tag/notes/资产验证、draft下载、公开前再次下载、PATCH发布、latest/public下载及原PublicationStore。没有复制状态机、关闭校验、冒用fixture、修改源工具hash、猜测陌生对象归属或重传资产。最终 `PUBLICATION_VERIFIED_SAME_ARTIFACT`，实际exit0。三个权限事务均恢复0775且目录identity不变。

这不是“原CLI首次全链无故障成功”。未来发布应明确修复Homebrew祖先权限和GitHub草稿URL兼容性，不能复制本次固定ID或假设原入口无需处理。该维护观察不影响已验证的1.1.0下载包。

## 持久 evidence

根: `/Users/smterpro/Downloads/whisper-1.1.0-lightweight-retry4.KbFkF4`。

- `publication-final-independent-review.json`: SHA-256 `38b0d0e3ae94552f63408472e2663f4913cb2f143c143b092c6e87871ea72316`。
- `decisions/artifact-human.json`: `0225459efcfd674c43e9677636f5173bd076180359bebdf13f792590ef34d895`。
- `decisions/publication-plan.json`: `3f68f041a5d1b300181ca730669adc242680c50f000c2513a468eb971eabab0e`。
- `workflow/publication/state.json`: `e8bec96876a636c3a49a52f7562eb094791d69d62e76ce1a708b59160bdfaf99`。
- `publish_existing_verified_draft.py`: `38cbfcef8f94fb3cc40f92c37dbbc6bb8a474520731bfe2db16616c8fba138e1`。
- 三份 `publication-permission-operation*.json`、DRAFT/UPLOADED reconciliation及原下载/响应文件保留；无认证材料。
- 主独立直接下载: `/Users/smterpro/Downloads/whisper-1.1.0-public-download-check.CMnpx3/ClassroomTranscriber-1.1.0-macOS-AppleSilicon.zip`，同上述size/hash。
- 构建/实际297strict/source/签名/ZIP/保留App证据仍见 [正式包review](whisper-1.1.0-prehuman-release-package-review-20261009.md)，不重新声称跑过一份full。

## 文档与关闭

产品docs-only后继commit `6f415266a78e6df06d54e1ae55d5da42afbf7e51`，parent为固定构建source014a。仅中英README、PACKAGING、历史deployment追加及新稳定发布详情；当前下载入口改1.1.0，保留历史硬件验证与签名/模型/并发边界。6/6 release-identity strict focused和41条本地链接/UTF-8/精确allowlist/diff检查通过，普通main push成功。没有改tag/正式包或用户worktree。

REL-AC-01至08由实现/集成/包/真实Human/远端/恢复与准确文档分别覆盖；安全范围仍为轻量prompt约束、单writer、arm64、模型外置、ad-hoc未公证、最低macOS和未测组合不作保证。父/子任务关闭，无Active Step；P/F及旧machine blocks/transition/所有REJECT和失败根不改，不自动激活其它任务。临时目录暂保留，清理另需精确授权。
