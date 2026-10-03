# Whisper 1.1.0 REL1C1 -- 本对话独立复核

日期: 2026-10-02，America/Phoenix。

## 1. 结论

Verdict: `REJECT -- REL1C1 IMPLEMENTATION`。

存在一个已复现的阻塞: C1复用REL1B的环境验证，在冻结整个获取后缓存的snapshot之后调用 `uv lock --check --offline`。该命令成功但会正常新增解释器缓存，随后的exact snapshot比较误报 `ENVIRONMENT_CHANGED`，原始Python bootstrap成功后仍无法进入Runtime。

不是额度/网络/超时问题，也不是已证明的恶意替换。修复不能通过排除整个cache、任意接受新的snapshot、跳过lock验证或放宽解释器来源来实现。

此结论不改写机器ACCEPT、旧run或旧transition。C1尚未独立接受，C2/C3不激活；REL1A/REL1B已接受结果保持原范围有效。未生成正式App/ZIP、真实Human artifact PASS或发布对象。

- Target: `/Users/smterpro/Downloads/whisper-rel1c1-continuation.2Mrct0/implementation`。
- Branch: `codex/release-1-1-0-automation`。
- Reviewed commit: `52237ae4ac893d7b46a8b0b48a10be137b90c6fc`。
- Ordinary parent: `46eb6545e92fd833a6ed2f2814f4b4c262eb4f55`。
- 累计复核范围: accepted REL1B `91e547918a20383f9dc938440db890a7dae85226` 到当前HEAD，四个普通后继、20个changed paths及直接构建/包装/信任依赖。最后repair只三路径不替代累计审核。
- 本对话没有修改target tracked文件、提交产品代码、执行真实push/merge/tag/API、部署信任或读取个人凭据。

## 2. Executor全绿和机器审核 -- 不自动继承

机器run `20261002T023023Z-10810` 初始Reviewer在6.8分钟附近因宿主退出而中断；预检恢复一份认证事务，Human在独立终端resume。保存的attempt-01未被擦除，未完成instruction通过attempt-02重新执行。

延续cycle1提交46eb654，receipt准确披露partial/full未运行；机器Reviewer仍REJECT真实uv populated wheel-cache directory-link兼容问题。Cycle2提交52237ae，Executor selected5/5、240.664s及full strict251/251、2008.293s，均有实际日志、exit0及source/environment绑定。原Reviewer同thread显式resume后ACCEPT C1-local criteria。

- Final: `RUNTIME_TRANSITION_COMMITTED / APPLIED / PUSHED`，exit0。
- Framework evidence commit: `072980ffa4277a65df2333df2d8cdc36250d3ad5`；[machine summary](20261002T023023Z-10810.md)。
- Verdict bytes: `/Users/smterpro/Workspace/framework-loop/1PCloop/.local/runs/20261002T023023Z-10810/cycle-02/reviewer-review/final.txt`，SHA-256 `ce64bbf7133876ea38d9416d769f5515c08286847195bb40fa351d05c66c81a1`。
- Machine transition: `9899fb7ad8a4f3b01e1ad414ae0a1ff6bd7e62c58eb0b75e9b68f2d6951695c7`；preimage `ada47cdff44b8b37054e2bffe54fb0a353df8a3117b154a1fc225e9dcbefe2b0`；治理写入前实际Runtime postimage `590ab3902468e09ab68dda021078d11c14653fb2eb56611918b098eeb59b24d5`。
- 历史checkpoint SHA-256 `5a01ba9b993cbfb4dea2a9ac2d267d8e786aaa66d143fbc37ab903fa3d821060`；manifest `d1079310d156c7a25a90e9cfeb8a996ed1598bf4bb60b13d37ab896e9c602afa`。本次不修改。
- 五份完成process全部exit0/success，Reviewer原thread关系 verified、Executor fresh ephemeral；账号A、auth restored、active identity unchanged、actual credential hits=0，无遗留认证事务。

本对话直接验证6项ACCEPT evidence、97份source hashes同时匹配当前文件/committed blobs、98份Executor evidence文件、两个test log hash、四个sole-parent后继、notes固定hash及未修改pins/产品功能。REL1B approval原代码保持byte-identical prefix。

## 3. 独立验证与通过的局部检查

新Downloads fixture root:

`/Users/smterpro/Downloads/rel1c1-fixtures.independent-review.7tQftM`

1. 固定hash uv0.12.5在独立cache中offline/no-index/no-deps安装两个本地产生的synthetic wheels，带中文文件；两份native wheel directory-link及38项snapshot通过，没有获取解释器或执行这些包。
2. 使用独立fixture签名和真实local Git，实际BuildController/原bootstrap_and_build.sh配signed synthetic children完成六个checkpoint、原ZIP链及两次verifier；精确fixture Human receipt通过。重复status两次，fixture bytes/identity不变。
3. 在before:runtime把物理archive目录换成内容相同但inode不同的新目录，返回 `ENVIRONMENT_CHANGED`，没有进入Runtime。
4. 修改ZIP中的Frameworks成员，保留Human App，重算artifact/state并正确签署fixture PASS，仍返回 `ZIP_APP_MISMATCH`。
5. 删除独立Owner receipt而重算 `HUMAN_RECORDED`，返回 `PATH_MISSING`；checksummed高级状态不能自授批准。
6. 四个生产CLI命令均因 `TRUST_UNAVAILABLE` 停止，没有部署或外部写动作。

六项均符合预期，但它们不证明下面的原始Python获取路径可用，也不是正式产物验收。

## 4. 阻塞的独立验证路线

独立probe不是再次复制synthetic Python输出。Fixture在签署前填入完整当前tracked源码，Python child使用逐字节原 `scripts/bootstrap_python_env.sh`；Runtime/App仍为独立签署synthetic children，且本次未执行到它们。新attempt内从空环境下载SHA校验的uv0.12.5、获取Python3.12.14、原 `uv sync --frozen`、原environment smoke。所有获取均局限Downloads fixture，不复制旧环境。

首次原控制路径返回 `ENVIRONMENT_CHANGED`。随后两次新fixture复现，并用只读snapshot差异与subprocess调用前后cache目录记录定位:

```text
原Python bootstrap: PASS
原environment smoke: 5/5 PASS
after:python准备冻结获取后的snapshot
verify_environment -> 原Integration.verify_environment
uv --version: exit0，cache无新增
uv lock --check --offline: exit0
新增 .tools/cache/interpreter-v4/72477d20415402fe/<workspace-specific>.msgpack
check_environment_proof: ENVIRONMENT_CHANGED
已完成events: [before:python]
持久state: BUILDING
Runtime/App: 未启动
```

最后一次新增文件为 `interpreter-v4/72477d20415402fe/4b92f2209323edb6.msgpack`，3949bytes；hash `43c76f6b80d5bf7f0c672a7f8bf1c0bfb3b50738f80ad9725a7f6d245f4d1f5d`。该leaf依workspace不同而变化，不应硬编码这一文件名。

Root cause:

- `scripts/release_workflow.py:389-391`先固定包括整个cache的proof，接着调用verify_environment。
- `scripts/release_workflow.py:338-339`直接复用 `release_integration.Integration.verify_environment`。
- 原 `release_integration.py:436-439`的uv lock验证产生cache后调用动态派发的C1 exact proof比较。REL1B原snapshot有不同cache政策，不能直接继承其验证副作用假设。
- 现有native wheel tests使用已有可信clone interpreter且不执行完整原Python bootstrap/lock-check组合，synthetic uv脚本也不产生解释器缓存，所以251/251不能覆盖本反例。

这使正式受控build在正常环境获取后无法继续，违反C-AC-02及C-AC-01正常调用链要求，足以阻塞C1接受。不要求在本轮执行正式whisper/App build来证明此缺陷。

## 5. 独立完整回归状态 -- 不声称PASS

启动过当前target原 `.venv/bin/python -B -W error::ResourceWarning -m unittest discover -s testCodes -v`，QT offscreen、bytecode disabled、TMPDIR为上述新Downloads root，source/environment-before快照保留。

前一turn被主动中断时测试进程也停止，日志有168个 `... ok` 完成行，后续测试未收尾；没有完整unittest summary或full-strict-result.json。因此本对话full是 `INTERRUPTED / NOT PASS`，不能写成168/168或251/251独立通过。Executor251/251属于已核验历史证据，未伪称重跑。

已确认阻塞后不为获得更多绿灯重复昂贵full。窄repair必须补真实Python获取/验证组合的正负向测试，并完成修改后的fresh strict full，再独立re-review。

## 6. Evidence locator/hash

下列文件均在上述root，保留供repair与re-review；不复制fixture私钥、auth或raw Session进tracked文档。

| 文件 | SHA-256 / 语义 |
| --- | --- |
| evidence-audit.json | 239d2e3d4b6007d7e1d860b5b92e574bc0aed1fe183e5e862e07933cc5877c99；machine/source/evidence核验 |
| independent-probes.json | f7812d61bb8a68148e8bdbda78eac9ab36981d6f5227ff08eb03fbfddf0be57c；六项独立局部probe |
| native-python-controller-result.json | c2f1b1f2135fa889f02f53973ded28d30ac5d0eedd2f783333e3805c37845444；原获取+命令副作用+proof差异 |
| native-python-controller-command-audit.log | 310224cfe836745225ff9cc80261d2fe7ca641757d48eb8e41e721a5d961d1e7；最后一次原控制路径拒绝 |
| native-python-controller.log | eda073a7ced3926d58bbf917cec10cb7e70443f974c49a9aad7ce51b5d8f34c7；首次未加诊断的控制路径拒绝 |
| full-strict.log | 1f8d61b929edc7b8dfedc29808dc3207544286c312f9d440f267f1264d419b75；中断partial，不是PASS |
| native_python_controller_probe.py | 79f5939cc6db8c2de4cbff9883874f8f3296ab66b6db3632165f707dad7bd2bb；原获取/只读诊断复现脚本 |
| independent_probes.py | 7a46633f9bc42cf988da2b4c45c6f332701ff4f8d8a958857f939ab683fdf853；六项独立局部probe脚本 |

最后一次原Python bootstrap的完整log在root下 `case-e507f634c996498c87d01d31d0ceb6e4/workflow/evidence/attempt-cfa9cdda1160493fbcf04417e2ed4ea6/build.log`，SHA-256 `55abe55a7b1828bf24f4e80a9f7f8f5c4cf7de6f3bf6f2dc59146298ad473867`，包含实际固定获取、5/5 environment smoke及bootstrap PASS。

复现/审计脚本 `native_python_controller_probe.py`、`independent_probes.py`、`audit_evidence.py` 均为本对话新fixture代码，不在target tracked测试中。最小复现从target的Python执行该probe，TMPDIR/Qt/bytecode按第5节固定。每次生成新case和attempt；签名仅为fixture用途，不能成为生产批准。

## 7. 窄修复边界与后续

建议mutation allowlist保持 `scripts/release_workflow.py`、`testCodes/test_release_workflow.py`、`PACKAGING.md`。将C1的正常验证缓存副作用纳入明确受控协议，同时保持所有已获取解释器/依赖/source/tool/既有cache字节的检查；不得全目录忽略或直接采纳任意post-snapshot。原REL1B helper不因复用不合适就修改，若额外path确实必要先有界说明。

独立测试必须包含完整当前tracked源码、原Python bootstrap、固定获取和实际controller/原shell的组合；可以在Python验证后用synthetic Runtime/App继续或有界停机，禁止真实App构建。保持所有替换/unsafe-link/writable/cache/interpreter、ZIP/App和签名receipt反例。检查验证耗时与ack/lifetime协议匹配，不通过无界等待放松停止语义。

旧machine block/record与checkpoint/manifest保持原样；独立REJECT在Runtime另记。下一步需要新的有界repair Runtime/config/state，不能resume已ACCEPT的终态或改旧hash。本次未准备或启动新run、未激活C2、未关闭PT-REL-01。
