# Whisper Release REL1A 独立复核 -- 2026-09-29

## 结论与边界

`ACCEPTED -- REL1A ONLY`。本次为本对话独立复核，不继承 Executor 或机器 Reviewer 的结论。接受版本/包身份、canonical manifest/输入、provenance 和无覆盖 ZIP 基础层；不是整个 Step 1、正式 App 构建、Human 黑盒或 Release acceptance。

- Target: `/Users/smterpro/Downloads/whisper-release-1.1.0.zFGKQr/implementation-phased`。
- Branch: `codex/release-1-1-0-automation`。
- Accepted commit: `b28027927f23c3a2333b1ae9da0dd6989901e616`。
- Baseline: `0388fa9daf65d5b5d0efae0e86eec824e33eab15`。
- 已核验三份 ordinary descendant commit、累计 17 文件 diff、clean 状态、product/lock 仅 root version 变化、manifest schema/pins 不变、现行文档 candidate 状态；源码无 ASR/UI/认证改动。

## Machine provenance 与明确 REJECT

Run `20260930T041657Z-42494`：cycle 1 commit `a6bf16df8c7dfd85d67c5631119bc7ea73d1131a` self-check 64/64、166/166 全绿，但机器 Reviewer 独立复跑后 REJECT。直接反例是可由 `--manifest` 引入弱化 dependency policy，且未进入 required provenance set；文档有 `/tmp`/历史步骤漂移。

Cycle 2 commit `b51c0eb9c16c598cebddbc9a915b7e4b0b37fe26` self-check 与独立复跑 68/68、170/170 全绿，仍 REJECT：ignored `dist/` 父目录为 symlink 时，leaf 检查接受外部 App/provenance。Cycle 3 修复严格真实目录/类型/解析父路径检查，机器 Reviewer 78/78、172/172 后 ACCEPT `b280279...`。

最终三层终态 `RUNTIME_TRANSITION_COMMITTED / APPLIED / PUSHED`，transition ID `99eabf1cdb7068992806e617bcffeaf7fd1e102cf06a8f03824152dfa7b78719`。Framework evidence commit `d7b3eb768c4b8bd3f56c97ac4ee6bb7ce0b2cc24`。七个 turn receipt 均成功、账号 A、role auth restored、actual credential hits=0。

- Raw: `/Users/smterpro/Workspace/framework-loop/1PCloop/.local/runs/20260930T041657Z-42494/`。
- Tracked machine summary: `/Users/smterpro/Workspace/framework-loop/1PCloop/evidence-summaries/20260930T041657Z-42494.md`。
- Final verdict: raw 下 `cycle-03/reviewer-review/final.txt`，SHA-256 `9766a0395f8d1053e284d4712246547dd4010607dfe5f1281a5ad2588846434d`。

## 本对话独立验证

使用 target-local `.venv/bin/python` 3.12.14、`-B -W error::ResourceWarning`、`QT_QPA_PLATFORM=offscreen`，临时测试路径固定在 Downloads。不启动 Codex、正式 build 或任何 Release 副作用。

| 直接 evidence | 结果 / sufficiency |
| --- | --- |
| 版本/包/环境/manifest/build/icon focused | 73/73 PASS，1.156s；组合与 machine 的 78 项不同，不混记 |
| 完整 testCodes strict discovery | 172/172 PASS，1.861s；Qt offscreen 不是实机黑盒 |
| 独立边界实验 | 修改 dependency prefixes、Python pin、额外 manifest 字段均拒绝；external symlinked dist 拒绝；真实 CLI 的旧 manifest/App/provenance override 均 exit 2 |
| 直接源码与 diff | 生产入口固定 tracked manifest、clone-local真实 dist/App/provenance；provenance 固定完整 required set和 App tree；hard-link no-clobber；retained extraction真实存在；依赖 pins不变 |
| pinned uv lock / shell / Git | lock --check PASS，17 packages；shell syntax PASS，累计 diff check PASS；测试前后 HEAD/branch/clean未变 |

本次不同于单纯重复 Executor tests：额外从实际 CLI 参数边界、独立 manifest mutation 和 external dist 身份构造验证。没有发现 REL1A 核心基础层剩余 blocker。

日志根: `/Users/smterpro/Downloads/whisper-release-1.1.0.zFGKQr/independent-rel1a.6NYyjO/`。

- `focused.txt`: SHA-256 `f7f7f991ab7bd2043d7399f68b7a7129d25efc71e68226938776129ec24ad5dc`。
- `full-strict.txt`: SHA-256 `8c15aac73396b93b2de12016f99d188d9e7f2d4387fd5fa0ed3e768c4f9a0aaa`。
- `independent-boundaries.txt`: SHA-256 `7f05a1809237fcf9d1dbfca9143059fa50f938d7c6b93f7faed2b1ca1d7488a5`。

## 后续必需工作

候选 notes 不是正式发布说明：漏列多语言、把 1.0.0 已有 icon/model-feedback/download-progress 混写为新增，尚缺标准 GUI 打开说明。已接受 1a 的身份/hash校验机制不代表发布 notes 内容最终正确；REL1C 必须纠正并同步其 fixed hash/tests，在 Step 3 build 前关闭该事项。

REL1B/REL1C、真实集成/build/Human gate/publication 均尚未执行。Target 发布准备分支尚未 remote push，local commits应保留；普通 Agent和助手不能绕过合同改用任意手动发布。下一个 run应新建 state并绑定当前 active account，不能把已结束的 A账号 run改绑 C账号 resume。本轮不激活或启动下一步。
