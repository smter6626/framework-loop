# Whisper 1.1.0 REL1B -- Runtime

## 1. 当前状态

- 父 Task ID: `whisper_release_1_1_0_v1`；子步骤: `REL1B`；顶层编号仍为 `1`。
- 状态: `ACTIVE / FIRST RUN FAILED CLOSED / RETRY READY FOR MANUAL START`；Verdict: `NOT EVALUATED -- IMPLEMENTATION`。
- 唯一 Active Step: REL1B。首轮模型服务拒绝，尚无实施 verdict；REL1A 已完成，REL1C 和真实 Step 2-5 仍 QUEUED。
- 本步 Static: [rel1b_static.md](rel1b_static.md)；其 SHA-256 见第 10 节。
- 父合同与权威总状态: [workload_static.md](workload_static.md)、[workload_runtime.md](workload_runtime.md)。
- 最后更新: 2026-09-29，America/Phoenix；UTC 次日 run ID 不改变此本地日期。
- Human 已指定本轮模型并要求准备手动启动指令；此决定授权 REL1B 实施准备，启动由 Human 执行。本轮建立独立 config/active machine block，但不调用 Agent，不创建生产 key/批准，不 merge/build/push target/tag/API。

## 2. 已完成与继续基线

REL1A 已机器和本对话独立接受，不重做:

- 实现 commit `b28027927f23c3a2333b1ae9da0dd6989901e616`。
- Run `20260930T041657Z-42494`，三轮 `REJECT -> REPAIR -> REJECT -> REPAIR -> ACCEPT`。前两轮测试全绿仍暴露任意 manifest 和 dist 父目录 symlink 缺口，历史不得删改。
- Machine focused/full `78/78`、`172/172`；本对话 focused/full `73/73`、`172/172`，额外生产 CLI 和独立反例通过。不能混记 focused 数量或声称已构建新 App。
- Evidence: [REL1A 独立复核](../../evidence-summaries/whisper-release-rel1a-independent-review-20260929.md)，以及父 Runtime 第 14-17 节。
- Framework 独立接受记录 commit `2e03f7bbbf2e0779bf3b04b4dfbc2666028586e5`。

本轮直接核对:

| 对象 | 2026-09-29 只读快照 |
| --- | --- |
| Framework | `/Users/smterpro/Workspace/framework-loop`，main；准备前 local HEAD/origin/main/GitHub main 为 `2e03f7bbbf2e0779bf3b04b4dfbc2666028586e5`，clean。本文提交会正常前进 framework，不影响 target。 |
| 实现 target | `/Users/smterpro/Downloads/whisper-release-1.1.0.zFGKQr/implementation-phased`，branch `codex/release-1-1-0-automation`，HEAD `b28027927f23c3a2333b1ae9da0dd6989901e616`，clean；非 shallow，但尚无预期 main commit object。 |
| Target origin | `git@github.com:smter6626/live_subtitle_generator.git`，当前 fetch/push URL 相同。 |
| Remote main | `d0f581bb70379239c3147e5c8469d2285ad6620b`。 |
| Remote 历史 feature | `refs/heads/codex/clean-toolbar-rename-v1` = `0388fa9daf65d5b5d0efae0e86eec824e33eab15`；它是历史基线，不是本次待发布工具分支。 |
| Remote 发布分支/tag | 本次 ls-remote 无 `refs/heads/codex/release-1-1-0-automation` 或 `refs/tags/1.1.0`；不是永久不存在证明，也不是完整 GitHub Release/draft 检查。 |
| 分叉与 main 内容 | 在原 main-docs worktree 只读核验 merge-base `b5188ccc6aef591398fd8d31e162a29390b120e4`。main 修改双语 README/repo_map，新增 `docs/streaming_backend_upgrade/{README,runtime,static,update_plan}.md`。不得丢失或混入其它 streaming 功能分支。 |

本轮未 fetch/merge 来填充 target main object。正式控制器取得精确 object 后再核对，不能把缺对象当作祖先结论。此快照在真正启动或集成前必须重验。

## 3. 必须读取的上下文

1. 本 Static/Runtime 和父 Static/Runtime，父 Static SHA-256 `47a90b305e5fa80eeec44dba75244e6a8482c1a121154c53a76f14d20dcc79a7`。
2. 交接 `/Users/smterpro/Workspace/framework-loop/1PCloop/.local/handoffs/whisper-release-rel1a-accepted-next-rel1b-handoff-20260929.md` 全文。它是恢复索引，不是授权或测试 evidence。
3. 上述 REL1A 独立复核、实际 accepted target diff/source/tests。核心依赖在当前 target 下:
   - `scripts/release_identity.py`、`build_release_zip.py`、`build_macos.sh`、`bootstrap_python_env.sh`、`bootstrap_and_build.sh`、`verify_packaged_runtime.py`。
   - `packaging/release_contract.json`、`runtime_manifest.json`、正式 spec；`pyproject.toml`、`uv.lock`、`.python-version`、`.gitignore`。
   - 双语 README、`PACKAGING.md`、`docs/repo_map.md` 和相关 `testCodes/`。
4. 必要时读取 framework 现有 runner/operator 以理解只读角色与普通后继 commit 边界，但不得修改它们。
5. 第二候选 `/Users/smterpro/Downloads/whisper-release-1.1.0.zFGKQr/quota-stopped-rel1-draft.tgz`，SHA-256 `b73f5601e692108bf466d692baf05138d30afac77ae6dbd2a3cf5a18f0b69817`，仅未接受参考。原 `implementation-continuation-01/` 不可编辑；不要整份复制其 controller。

旧候选已知问题: 信任根由 caller 选择，journal self-hash 不证明批准/测试 authority，分叉与恢复 gate 尚未接受，后半段 gh argv/二进制下载曾不正确。不能因草稿或旧测试存在就沿用结论。`release_contract.json` 与 REL1A helper EXPECTED_CONTRACT 精确相等，不可直接添加 controller 字段破坏身份层；本步控制输入应独立建模。

## 4. 唯一 Active Step -- 等待 Human 手动启动

### REL1B: 批准、持久 journal、分叉集成控制器

Objective: 实现 Static B-AC-01 至 08，并交付可独立复核的 controller 前半段；生产集成/build/publication 不在本 run 中执行。

允许文件:

- 新 `scripts/release_controller.py`，以及确有必要的纯批准/journal/Git integration helper，命名在 Reviewer instruction 中固定为精确 allowlist。
- 对应 `testCodes/test_release_controller.py` 和必要 focused helper tests。
- 双语 README、`PACKAGING.md`、`docs/repo_map.md` 中直接相关的操作与未实现边界。
- 若需单独 tracked control schema，先说明它与现有 product contract 的分离，Reviewer 明确允许该精确路径后再修改；不得包含真实批准、journal、私钥或凭据。

禁止文件与操作:

- Static/Runtime/global governance、framework 代码/schema/role/auth、历史 raw/summary/archive，原 dirty 候选、用户三个 worktree。
- REL1A 身份/ZIP/build/manifest/spec/pins、release notes 和产品代码不顺带重写；若发现本步不可避免需改 accepted 基础层，先提出 bounded proposal，不能先改后解释。
- 普通 Agent 真实 push/merge/branch switch/tag/GitHub API/正式 App build；测试只允许 disposable Git/bare remote 的受管 mutation。
- 生产密钥生成/读取、使用个人 key、安装信任配置或把候选/fixture 批准当作生产批准。

执行顺序:

1. 全文读输入，检查 target HEAD/branch/clean 和依赖影响。解释 trust boundary/状态模型，选最小方案；再由 Reviewer 给 Executor 有界指令。
2. 实现批准/journal/只读 status，再实现隔离 Git 集成与测试 gate。可模块化，不实现 REL1C 后半段。
3. 运行 focused 和完整 strict 回归，保存原始测试日志、失败反例、SHA/locator。所有临时 fixtures/logs 在 Downloads 下精确目录，不污染 source。
4. 普通后继 commit/clean，交回同 Reviewer 审核；REJECT 后仅做有界 repair，再测试/re-review。
5. Machine ACCEPT 只关闭 REL1B implementation；本对话再独立复核。未接受整个 Step 1 前不运行真正的 controller integration。

## 5. 测试与 Reviewer 的直接验证路线

| 路线 | 必须覆盖的反例和结论 |
| --- | --- |
| 批准与真实 CLI | 有效独立 fixture 批准；caller signer、错误 source/tool/contract/ref、篡改批准或撤销、缺生产 trust anchor；不得零成本自授予。测试必须进入实际 argparse/生产调用链，不能只给 helper 注入一个 fake True。 |
| 重新 hash journal | 修改 state、accepted commit、tool hash、remote/ref、管理路径、tests PASS、push receipt 后重新算合法 checksum；仍被批准或事实验证拒绝。未知/重复字段拒绝。 |
| 真正 Git 分叉 | Disposable main 与 feature 都有独有提交；取得完整 objects、merge parents/ancestry/tree 正确，两边文档/功能存在；内容冲突、缺对象、dirty、错误 fetch/push URL、不可信 hook/config 和远端前进都停止。 |
| gate 调用顺序 | 克隆内固定 Python 3.12.14、uv 0.12.5、frozen lock bootstrap -> 当前 full strict -> clean/identity/ref 重验 -> main non-force push。失败或 forged/过期 PASS 时 local bare main 不前进；解释器必须来自集成 clone。 |
| crash/reconcile | 意图写入、feature push、merge、环境准备、测试、main push 前后退出；已完成 push 后记录缺失/网络结果未知先 exact remote 对账；缺可信测试证明重测或停止，不能漏掉 gate。 |
| 路径与只读 | 文件/父目录 symlink、outside Downloads 管理路径、错误 mode、partial journal、原子写失败、输入权限/类型错误；重复 status 前后 bytes/refs 不变，不读取任意秘密文件。 |
| 前后边界 | 未来 build/tag/draft/upload/publish 入口不可执行；没有 Agent loop，实际外部 repo 未改；输出固定可读文本不含秘密或 forged line。 |
| 既有回归 | REL1A identity/ZIP/runtime 与全部 testCodes，锁/pins不变；Qt offscreen 只算逻辑测试，不是 Human 黑盒。 |

Self-check 命令逻辑: 在当前 target cwd 使用本 clone `.venv/bin/python -B -W error::ResourceWarning -m unittest discover -s testCodes -v`，`QT_QPA_PLATFORM=offscreen`，TMPDIR 指向新 Downloads fixture 目录。Focused 模块依实现结果列出，不预填未来测试数量。Python/uv/import、diff check 和精确文件 allowlist 一并核验。

Independent Review 尚未进行。Reviewer 必须直接读取 diff/production CLI/真实 Git facts/test artifacts，并自选至少一条 self-check 未充分覆盖的篡改或 crash 验证；依据 B-AC 逐项判断 sufficiency，不能继承"全绿即接受"。

## 6. 启动准备与机器边界

Human 2026-09-29 决定: "1pcloop这次的reviewer和Executer的模型配置分别改成6.1sol xhigh和6.1sol high；完成后给出1pcloop的启动指令我手动启动"。据此完成以下准备，实际 run 由 Human 启动:

1. Static 为 AUTHORIZED，记录上述 Human 决定并重新固定 hash；父 Runtime/global 指向本 Runtime，唯一 Active Step 为 REL1B。
2. 首轮config `workload_rel1b.json`及其state保留。当前启动用 [workload_rel1b_retry_cli_01.json](workload_rel1b_retry_cli_01.json)，同Static/Runtime/target，独立state root `/Users/smterpro/Workspace/framework-loop/1PCloop/.local/state/whisper_release_1_1_0_v1-rel1b-retry-cli-01`，显式引用原失败run，不resume或覆盖旧checkpoint；见第12节。
3. 本 Runtime 新建唯一 REL1B `ACTIVE / reviewer_accept_once` machine block，只准 `ACCEPT -> COMPLETED`。父 Runtime 原 REL1A COMPLETED machine block/transition record 不改写，旧 run 不 resume。
4. Max cycles 4、每 turn timeout 1800s、progress interval 15s；Reviewer `gpt-6.1-sol/xhigh`、Executor `gpt-6.1-sol/high`。这两个值分别保存于 `/Users/smterpro/.codex-mix/.mix/runtimes/1pcloop-reviewer/config.toml` 和 `1pcloop-executor/config.toml`；operator config 只选择 runtime homes，模型不写死在 `onepcloop.py`。其余配置不变，不自动换模型。
5. 新 run 固定启动时 Codex Mix active account；用户此前报告 acc3/marker C 只是历史观察，不能据此硬编码。双 role 独立 runtime、temporary auth projection/restoration/scan 与 A/B read-only snapshot沿用既有机制，不打印凭据。
6. Framework/target/治理 identity重验，doctor/preflight通过；使用临时 `caffeinate -i` 随runner结束释放，不改系统设置。

Doctor/preflight 只证明本机配置、认证 TTL、路径和治理门禁，不能证明当前账号实际服务支持该模型。若首次 turn 服务拒绝 `gpt-6.1-sol`，fail closed 并保留失败 evidence，不自动回退 5.6 或换账号。未为本轮预检发起额外模型 smoke/Agent 调用。

## 7. Blockers、决策与 Pending

- 当前等待 Human 手动启动；模型变更和 REL1B 实施准备已由上述决定授权，不是 implementation ACCEPT。
- 生产信任配置尚未存在: 不阻止批准后实现隔离 fixture/缺配置 fail-closed，但阻止真实 integration。执行中如必须部署 key 或新可信入口才能验证当前 criterion，停止给 Human 具体方案，不降级为普通 pending。
- 自动 merge 若遇内容冲突必须停止，不能悄悄覆盖 main 文档；真实冲突结果尚未知。
- 新 controller/测试量若仍无法在有界 turn 内完成，呈交更小编排，不牺牲 gate，也不自动把未来步骤算完成。

父任务 Pending 原记录仍以父 Runtime 为 authority，本表仅引用，不创建第二份独立倒计时:

| ID | 内容 | 截止顶层 Step | 当前 k / 剩余次数 | 状态 / 处理 |
| --- | --- | --- | --- | --- |
| PT-REL-01 | notes 漏多语言、混写旧功能为新增、缺 GUI 打开说明 | 3，正式 build 前 | 1 / max(3-1-1,0)=1 | OPEN_NON_BLOCKING；REL1C修正 notes/fixed hash/tests并独立接受；不在本步顺带修改。 |

REL1B/repair 与 REL1C 都继承父级 1，不消耗顶层迁移次数。真实 Step 2前须整个 Step 1接受且 production trust gate就绪；Step 3前 PT-REL-01必须 RESOLVED。

## 8. 当前状态迁移与历史保留

先从"REL1B QUEUED"补充为"REL1B 文档 DRAFT，可供 Human 审阅"；Human 随后指定模型并要求手动启动，现为 "REL1B ACTIVE / READY FOR MANUAL START"。仅激活本实施步骤，没有新的 implementation acceptance/run result。REL1A 已接受、两个失败 run、两轮 REJECT、原 artifact 和 hash 全部保留。

原总 Runtime 第 4 节残留"REL1A 是 Active"只做语义修正，不改变完成 machine block 或过去真实执行历史。新文档不恢复未接受旧 controller，也不把 source Human PASS当新 ZIP PASS。

## 9. 后续方向与报告

本步完成后先独立复核和治理收尾，再准备 REL1C；整个 Step 1接受后才做实际集成 -> fresh build/ZIP -> Human exact-artifact PASS -> same ZIP publication。

Executor 报告应包含: 逻辑/依赖影响、批准信任模型与未部署边界、精确文件和 commit/parent、tests/log locator/hash、实际 CLI 与 Git反例、恢复覆盖、外部副作用零证明、限制/待决项。停止于 `IMPLEMENTED / VALIDATED -- AWAITING INDEPENDENT REVIEW`，不自行 ACCEPT，不推进 REL1C，不写治理。

## 10. Static 固定值

REL1B Static SHA-256: `2f2503a27e174dbbd3064faa6cc1b22c3a0389a12176f78ae92ecc12269190b5`。

批准后如改动内容须重新固定 hash；此值只是文档 byte identity，不是批准证明。

## 11. 当前 implementation machine state

只授权 REL1B implementation 的一次 `ACCEPT -> COMPLETED`。Machine ACCEPT 不等于本对话独立复核、生产集成、Human artifact PASS 或发布完成，不自动激活 REL1C。

<!-- 1PCLOOP_RUNTIME_STATE_BEGIN -->
{
  "active_step": {
    "id": "REL1B",
    "status": "ACTIVE"
  },
  "last_transition_id": null,
  "schema_version": 1,
  "transition_mode": "reviewer_accept_once",
  "workload_id": "whisper_release_1_1_0_v1"
}
<!-- 1PCLOOP_RUNTIME_STATE_END -->

## 12. 模型拒绝、CLI stable升级和手动retry -- 2026-09-29

- 首轮 `20260930T060931Z-48717`: doctor 9/9与preflight PASS；Reviewer首次服务请求HTTP 400，提示 `The 'gpt-6.1-sol' model is not supported when using Codex with a ChatGPT account.`。这是启动失败，不是Reviewer REJECT；Executor未运行，无产品改动或实施commit。
- 三层 `FAILED_CLOSED / NOT_APPLIED / PUSHED`，exit1；framework evidence commit `8bd6c871cd115ba4406d85c5abda5dfa18173b74`，summary [20260930T060931Z-48717.md](../../evidence-summaries/20260930T060931Z-48717.md)。Role auth restored、active identity unchanged、actual credential hits=0。
- 原checkpoint `/Users/smterpro/Workspace/framework-loop/1PCloop/.local/state/whisper_release_1_1_0_v1-rel1b/whisper_release_1_1_0_v1/checkpoint.json`，SHA-256 `52745c6e04da160f49e22885d08addbcc7ad12a5e228f417b0d0c6024034d233`。原config/checkpoint/raw/summary不改写。
- Human要求检查最新版并授权升级，随后自行重启。npm当前latest stable为0.159.2，已从0.157.0升级并核验；未安装alpha，不改模型、账号、auth、canonical或退休A/B。
- 新config固定已升级npm CLI绝对路径，避免其它终端PATH选旧版；`retry_of=20260930T060931Z-48717`，reason `codex_cli_stable_upgrade_0_157_0_to_0_159_2`，新的state/new run ID，target路径/branch/clean HEAD符合原失败初始状态。不是terminal checkpoint resume。
- 升级不证明模型服务权限已解决。本轮不发起额外service smoke或Agent、不自动fallback；Human重新doctor/preflight通过后run，若仍模型拒绝则保留新失败并停止。实施门禁与真实发布gate不变。
