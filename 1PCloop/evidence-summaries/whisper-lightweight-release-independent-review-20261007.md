# Whisper 1.1.0 -- 轻量发布实现独立接受

日期: 2026-10-07 America/New_York。
Verdict: `ACCEPT -- LIGHTWEIGHT IMPLEMENTATION AT 6cbba5d02074311467be56ac349e44dea097a804`。
Reviewer reference: `lightweight-independent-review-20261007`。

只接受轻量发布实现、实际本地测试与恢复边界，不接受真实 main 集成、正式 App/ZIP、Human 精确包 PASS 或 Release 完成。

## 权威和改动范围

Human 选择 prompt-based Reviewer/Executor 分工，明确不部署 root 入口、生产签署 key、密码学 receipt、专属组或认证桥。父/REL1C Static 当前 hash 分别为 `82487f10e54e35c5364f14eb29622f74a714da8c3b3bc674a00a382b0a04d917`、`0fb58bd5f263ab9ae312a5956e3010882f73c80d79fb4d1952054acefe3513b9`。旧机制及所有历史验收保留，旧部署 proposal 已 superseded。

子 Executor `/root/lightweight_release` 在 clean0c 的普通后继6cb实施，11批准路径、841新增/5删除，工作树clean，未push target。主Reviewer直接重读入口、普通本地审计helper、四个耦合diff、原controller/构建/ZIP/发布依赖和四份说明。不复制三套流程，不用fixture Policy/key或monkeypatch作生产开关。旧protected入口默认兼容；原state、shell、build/ZIP/Runtime、pins与notes69013bca...不改。

新独立 LightweightPolicy 绑定工具/合同、精确source/refs/path及真实Reviewer/Human reference。ContextVar只在明确新入口中选择native Git/gh，finally恢复，mixed/other/nested policy拒绝。原生登录由native工具正常使用，Controller不提取/复制token/privatekey，不改全局配置，不读取Codex Mix或退休A/B。主Reviewer用实际过滤环境另查Git main/gh repo/push权限均成功。

哈希只绑定事实，不授予权限；不承诺同UID恶意Agent不可伪造本地决定。Human记录必须真实PASS、explicit publish_allowed=true并绑定精确source/ZIP/App；缺允许、FAIL、旧包/换包均不发布。未知远端结果先实际对账并要求明确exact-ID Reviewer reconciliation，不以matching names/重hash状态自动接管；原固定tag/notes/asset/下载/no-clobber/no-force链保留。

## 测试和独立路线

- 首轮12/12，473.188s、exit0，是CLI/doc/final-test增补前的早期代码，不冒充最终source全量。
- 最终delta6/6，85.533s、exit0，覆盖新typed/schema/reference/foreign-state边界及旧exact-type/missing-trust兼容。
- 原生组合360.405s、exit0，真实固定uv/Python/frozen sync/5smoke、原六checkpoint、原ZIP、local双父级/fakegh。Integration strict gate、Runtime/App和Human决定明确synthetic，不能交Human当正式包。
- 主Reviewer外置脚本六项独立反例107.858s、exit0: 实际CLI不回显caller marker；source parents错误零tag/API写；publish intent处撤销Human允许或远端notes漂移均保持draft、无PATCH；mixed/other/nested policy拒绝/reset；two readonlystatus及missing resume不变字节/ref。11路径source before/after一致。
- 唯一最终fresh full: `292/292 OK`、4963.629s，真实test exit0、collector exit0；collector总4976.132s。未发生对话工具父进程丢失导致退出码不可恢复的问题。源固定clean6cb，无途中编辑/重复full。
- 主Reviewer独立解析292 complete OK blocks(285单行及预期诊断后七项独立ok)，核完整unittest结尾、无ResourceWarning/未处理Traceback/FAIL/ERROR，不能仅检查日志最后一行(后面有buffered ZIP stdout)。另从Git对象重新核106 source tested/current/committed bytes与mode，19157环境before/after字节/身份一致，实际process与ownedgroup已退出。随测试PID防休眠进程已自动结束。

## 可恢复证据

Full root `/Users/smterpro/Downloads/rel1c1-fixtures.lightweight-full.9Twvhh/`。

| 文件 | SHA-256 |
| --- | --- |
| full-strict.log | 9914d19ae75482011e3fa820ea962e262f17ae678350e9ecd6b580597039752f |
| full-result.json | 7bf7866512972fe90e99366c1970aa4271725b40d475ad4bb847595ed00f401a |
| source-before.json / source-after.json | 4e72ce8abfdf6d338aa4c783241e171a1dd0302630275619b956cc491a9e739e |
| environment-before.json / environment-after.json | 9608afdc89aca17b9549c0dc2b8b062a2b62a588be51cfcba2f214ea8b4ecc49 |

局部root `/Users/smterpro/Downloads/rel1c-lightweight-check.wNr3ld/`: focused-first.log SHA b0d126d49b902184bc83a266e3eca6bfcb33a20c7e62e1d942a59691884e9031，focused-final-delta.log SHA8e44a693424945527bb92f2526f96bd1175092a390ca37c1935454566e7887d5，native-combined.log SHA35ed6ed30573553423cbdefda8cb0db31f311466a0afea5f1378693ecfc548d6，candidate-source-bindings.json SHA39f4387b63214bf133796f1670f405ead5693d0db4449db736d70920d082c397。

Native report `/Users/smterpro/Downloads/rel1c-lightweight-fixtures.z7t_0vw2/native-combined-result.json` SHA9e0f6fe2330c1746cefff792677d5aa93bfb90a789d632c972fb1575b3cd4b17。
Reviewer report `/Users/smterpro/Downloads/rel1c-lightweight-fixtures.review-t2tD7b/reviewer-probes.json` SHA09d67576c6d758555bb3ad8688c18effe3c454a056308671886af05a8f95dad8。

## 下一门

主Reviewer接受本实现后可依据既有Human授权切到实际交付。先fresh核固定origin/main/feature/tag/Release及普通本地approval draft，再用已审核入口真正集成/完整merged-source gate/普通push。final-main接受后才fresh正式build/ZIP/自动验包，最终ZIP的Human测试和明确发布允许仍必须取得，不能继承旧App PASS或synthetic结果。当前尚无正式包，不执行真实tag/draft/upload/publication。single-writer/无并发一致性、ad-hoc/未公证和硬件/语言覆盖限制保留；活跃证据不自动删除。
