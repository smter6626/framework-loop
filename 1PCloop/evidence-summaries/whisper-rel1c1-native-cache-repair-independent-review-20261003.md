# Whisper C1原生验证缓存修复 -- 主助手独立审核

日期: 2026-10-03，America/Phoenix。

## 结论与范围

Verdict: `ACCEPT -- C1 LOCAL IMPLEMENTATION AT 5d33416af100a480f8a43f345a163b3b02e696f1`。

Human明确改用主助手Reviewer + 一个桌面Executor子智能体，不启动1PCloop。任务 `/root/c1_native_cache_repair` 只修改、测试并创建本地普通后继commit；主Reviewer未修改产品源码，使用实际源码/日志/提交字节和不同的独立反例验收。此记录不是新的machine verdict、same-thread receipt、Runtime transition或发布批准。

- Target: `/Users/smterpro/Downloads/whisper-rel1c1-continuation.2Mrct0/implementation`。
- Branch: `codex/release-1-1-0-automation`；parent `52237ae4ac893d7b46a8b0b48a10be137b90c6fc`；最终工作树clean。
- 普通后继 `5d33416af100a480f8a43f345a163b3b02e696f1`，message `Repair native release validation cache boundary`。
- 精确三路径: `scripts/release_workflow.py`、`testCodes/test_release_workflow.py`、`PACKAGING.md`；362新增/7删除。无target push/merge/tag/API、生产trust/认证变更、正式whisper/App构建或Human artifact PASS。
- C1局部覆盖C-AC-01至04、C-AC-07的build/artifact/Human gate恢复，以及C-AC-08的notes/回归部分。整个REL1C、父Step 1及真实发布未接受；C2/C3仍QUEUED，未启动。

## 为什么修复成立

原独立REJECT保留在 [20261002审核](whisper-release-rel1c1-independent-review-20261002.md)。正常原Python获取成功后，固定 `uv lock --check --offline` 新增解释器缓存，旧exact proof误报漂移。修复不排除cache、不跳lock验证、不修改已接受REL1B helper。

C1保留原prefix/base executable/版本/lock校验。只有after:python首次固定lock命令成功后，可新增至多一个 `.tools/cache/interpreter-v4/<16-lowercase-hex>/<16-lowercase-hex>.msgpack`，1..65536bytes、current-owner、regular single-link、0600/0644；新增目录仅为对应root/key、0700/0755。所有已存在input/source/tool/interpreter/cache bytes和identity必须完全不变。完整安全scan/delta和外部权威重验后才冻结全部新proof；Python probe/version命令、失败或再次调用不获例外，后续仍exact比较。

新增verifier使用专属process group、有界communicate和精确group清理，超时或遗留后台子孙停止。保留20s验证预算及原shell30s ack/lifetime协议，未使用无界等待。正常清理/超时测试不等于对SIGKILL或OS崩溃作无条件清理保证。

## 本次额外REJECT与修复过程

Executor首版原生组合1/1、191.128s及20-shape/9-command矩阵两项294.093s通过；checkpoint约26-27s。主Reviewer首版独立原生复现也通过，7个实际子进程边界反例符合预期。随后补进程组清理，小测试1/1、1.055s通过，但这些自检不能自动接受新版本。

主Reviewer对 `release_workflow.py` SHA `a233e5d6298d4ac89cdc3520c2a012f384f89a0ef71764be9b575c821e5fe891` 的新fixture复测，在原bootstrap/frozen sync/smoke成功后遇到 `ENVIRONMENT_VERIFY_TIMEOUT`，仅before:python完成、stateBUILDING，未进入Runtime/App。因此再次REJECT，未准入昂贵full。这是正常本机负载下重复扫描耗尽20s预算，不是额度失败。

失败result: `/Users/smterpro/Downloads/rel1c1-fixtures.subagent-final-native-review.VHocNx/native-python-controller-result.json`，SHA `5283662a9eddfdc0e11cad6fca39bab64ff131b61d2acfd58274c753fa918ce7`。其build log位于该root的 `case-9adbde183d214e8895b8e582e42c6fe5/workflow/evidence/attempt-e380b81bbf2c4a7597141631ea7ddb64/build.log`，SHA `11146c953a4c384454936d5b59dee7b7a48525b5546735e8e2cd1b787f140d58`。

同一Executor减少冗余审计: 验证入口/出口完整重验权威与Git/source，每个命令前仍完整proof，post-lock完整scan/delta，checkpoint最后再验；不接收caller-selected snapshot、不提高timeout或改shell/REL1B。修复后双方fresh原生复测通过，checkpoint约22-23s。

主Reviewer最初一个正向synthetic fixture错误地每次重写既有msgpack，代码正确拒绝；该错误fixture/log留在 `rel1c1-fixtures.subagent-independent-review.92QTtA`，纠正后通过，不作为产品finding。所有旧失败/partial/full中断和machine记录均未覆盖。

## 最终源码与直接验证

| 最终文件 | SHA-256 |
| --- | --- |
| scripts/release_workflow.py | e5462cc5c05631d9a0452d4be03370a8bc8ad7be838113cae20902f3e3cae795 |
| testCodes/test_release_workflow.py | 33acae38c1acc559ec50bbdfcd791b4ccbd23fdaadf070ffc69134bc787f7702 |
| PACKAGING.md | 810365b53fd8567cc07f580d228797f0611183b6ad8c4c98666b516f1de48af5 |

Executor最终fresh严格回归 `255/255`，unittest2624.287s、wall2624.740s、exit0，`-B -W error::ResourceWarning`、Qt offscreen、外置TMPDIR；97份source和19157项`.venv/.tools`文件系统身份/hash前后完全相同。不是另一份独立full: 主Reviewer直接核该fresh完整证据，并用不同路线独立复测，未重复昂贵全量。

Full root: `/Users/smterpro/Downloads/rel1c1-fixtures.native-cache-repair.ByDMKC`。

| 文件 | SHA-256 |
| --- | --- |
| full-strict.log | 92ebe52cc1a563a56f3b9f1a70e8cd1ebf91c0d1c273b7010ecbc869db6d4e82 |
| full-strict-result.json | d14070624ca73abe635826ae3f0d5edba4f546a2c3192f960abda4a806d7e48c |
| full-inputs-before.json / full-inputs-after.json | 8545b93a570ddb4be89d40e1612be9fe82832135a668282250abaaabca76fc4d |
| executor-receipt.md | af331a8472a30d23a74ffe1b6d03c3a79dd16d93d9c8461816d35e475ba5cb03 |

Executor最终内存compile/direct import为 `COMPILE_IMPORT_OK 65536 6`，committed diff check通过。完整receipt保留自检的AWAITING状态及随后收到主Reviewer独立接受通知，不伪装为Executor自ACCEPT。

主Reviewer新root: `/Users/smterpro/Downloads/rel1c1-fixtures.subagent-optimized-review.7hK6F6`。

1. 原bootstrap、SHA核验uv0.12.5、新获取固定Python3.12.14、原frozen sync及5项smoke、真实controller/原shell六checkpoint/原ZIP链通过。Runtime/App仍signed synthetic，不是formal build。19027项proof；after:python23.020s、before:runtime22.438s、before:app22.067s、after:app22.063s，均小于原30s ack。
2. 七个实际signed synthetic子进程反例: 合法首次新增通过；version偷增、two-records、prior-cache-change、second-lock-replacement、lock-failure、extra-empty-directory分别拒绝。不是仅patch subprocess得到的结果。
3. 六项独立安全复测: 真uv两份offline wheels及中文数据；实际六checkpoint/ZIP/只读status；相同bytes但新inode缓存替换拒绝；正确签名/重算metadata仍拒绝ZIP与保留App的Frameworks成员差异；重算HUMAN_RECORDED仍拒绝缺Owner receipt；四个生产CLI命令缺trust停止。
4. `final_evidence_audit.py`核所有97份tested/current/committed blob、三路径/sole-parent/clean、full log/receipt/inputs hash、独立native fixture实际workflow字节与最终commit一致，全部通过。测试时HEAD仍52237ae但三份candidate bytes有直接hash绑定；不能只凭probe的HEAD字段认定它测的是旧源码。

| 独立文件 | SHA-256 |
| --- | --- |
| native-python-controller-result.json | de39c28590aa41cdc49d06c8b44324d7489bb9f4377e7dd902120d63d7aa2f80 |
| actual-child-boundary-result.json | f4016b9a214f0064db5bf4dcc3d9169ef7f545072c723fce60b3914dec4a1802 |
| independent-probes.json | a6c9f16bf98c3d67deaf16c258c88ac6ab7e4951d1439f1353299f118a4af59d |
| final-evidence-audit.json | d89b98ffc60aab8748c4ee6798345b7fba3ea8a057cde8667fa8b6f31b7cadc7 |

## Pending、历史与后续边界

PT-REL-01的候选notes逐段重读，准确区分新增语言/Session/Clean/R2功能和保留的1.0图标/反馈；包含标准GUI打开方式与候选/平台/实音频限制。notes、contract和EXPECTED_CONTRACT固定SHA仍为 `9901c141b3765dda965bc2fcacae5a24d4a721f0e6d1725ae1e7fc2c86d387cd`，直接固定hash tests包含在255项fresh回归中。仅接受此候选notes事实及绑定，父pending可RESOLVED，不代表公开Release notes/新artifact已被Human接受。顶层k=1不变。

旧machine checkpoint SHA `5a01ba9b993cbfb4dea2a9ac2d267d8e786aaa66d143fbc37ab903fa3d821060`、manifest SHA `d1079310d156c7a25a90e9cfeb8a996ed1598bf4bb60b13d37ab896e9c602afa`、旧transition/preimage/postimage原样保留。Static与封存REL1A/REL1B不改，旧独立full168个OK行仍是INTERRUPTED/NOT PASS。

单writer/无并发一致性边界保持；固定UV新布局、多文件或超限cache形态仍停止审核。真实Runtime/App构建、生产trust/transport、完整C2/C3、主仓库集成、最终ZIP Human PASS和发布仍未完成。所有Downloads evidence暂留供活跃任务审计，之后再由Human有界清理，不自动删除。
