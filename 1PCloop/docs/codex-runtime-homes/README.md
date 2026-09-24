# Codex Mix 与 1PCloop runtime home 架构

## 当前架构

本机 Codex Mix 的稳定边界如下：

```text
~/.codex -> ~/.codex-mix

~/.codex-mix
  auth.json                         当前 projected credential
  .mix/accounts/A-D/auth.json       credential vault
  .mix/runtimes/
    1pcloop-reviewer/               Reviewer 专用 CODEX_HOME
    1pcloop-executor/               Executor 专用 CODEX_HOME
```

- `~/.codex-mix` 是 canonical interactive Codex state。
- `~/.codex-mix/.mix/accounts/A-D/auth.json` 是 A-D 账号的 credential vault。
- `~/.codex-mix/auth.json` 是 Codex Mix 当前投影给交互式 Codex 的 credential。
- `~/.codex -> ~/.codex-mix` 是正常 route，不是异常 alias。
- A、B、C、D 只表示 account identity，不表示 Reviewer 或 Executor role。
- `~/.codex-A`、`~/.codex-B` 是 historical source，迁移后不得继续作为 live runtime。
- Reviewer/Executor role 由独立 runtime home、运行合同和 session state 定义，不由 A-D 名称定义。

[OpenAI 官方环境变量文档](https://developers.openai.com/docs/config-file/environment-variables)
把 `CODEX_HOME` 定义为 Codex 配置、认证、日志、session、skills 和独立包元数据的根目录；SQLite
state 默认也跟随该根目录。因此 role runtime 必须整体迁移，不能只复制 `config.toml` 或
`auth.json`。

## 1PCloop 目标绑定

```text
Reviewer CODEX_HOME:
~/.codex-mix/.mix/runtimes/1pcloop-reviewer

Executor CODEX_HOME:
~/.codex-mix/.mix/runtimes/1pcloop-executor
```

1PCloop 在解析 workload config 和 mutation runner preflight 两层执行 fail-closed validation：

- Reviewer 和 Executor runtime home 必须不同；
- 两者解析后都必须是 `~/.codex-mix/.mix/runtimes/` 的严格后代；
- 两个 home 不得相同，也不得互为父子目录；
- 任一路径只要解析为 `~/.codex-A`、`~/.codex-B` 或其内部路径，启动必须失败；
- symlink 或其他 alias 不能绕过该检查；
- 目标 runtime 不存在时，`doctor` / preflight 必须失败，不能回退到 A/B。

所有 tracked workload 还必须设置：

```json
"account_source": "codex_mix_active"
```

role runtime 与额度账号是两个独立维度：

- Reviewer/Executor 的 `CODEX_HOME` 继续固定在两个 dedicated runtime，用于隔离配置、session、skills、
  SQLite 和 persistent Reviewer thread；
- 每个新 run 在 preflight 时读取 `~/.codex-mix/.mix/active.json`，并验证 marker、
  `~/.codex-mix/auth.json` 和对应 A-D vault 的 `account_id` 一致；
- run 只记录账号别名和 `account_id` 的 SHA-256，不保存原始 account ID 或 token；
- 普通 ChatGPT 登录不再把 OAuth cache 中的 `tokens.access_token` 误用为
  `CODEX_ACCESS_TOKEN`。每个 turn 在锁内把完整 canonical `auth.json` 临时投影到对应 role runtime，
  并强制 `cli_auth_credentials_store="file"`；
- 子进程环境会移除 `CODEX_API_KEY`、`OPENAI_API_KEY` 和 workload identity 覆盖，避免额度来源被
  其他环境变量替换；
- CLI override 将全部认证环境变量从 Agent shell environment 中排除，并为该 turn 设置
  `notify=[]`。Codex child 只通过 role runtime 的文件 credential 登录；
- run 启动后账号 identity 被固定。若 Codex Mix 在两个 turn 之间或 turn 期间切换账号，当前 run
  必须 fail closed，不能让同一 run 混用多个额度账号；
- access token 的剩余寿命必须至少覆盖 turn timeout 加 300 秒；
- preflight 和每个 turn 前后都会把 A/B 当前全树与保存的 21,091-entry retirement snapshot 精确比较；
  任意文件新增、删除、内容、类型、路径、mode、size 或 mtime 变化都会 fail closed；
- role runtime 原有 `auth.json` 只作为迁移历史缓存，不决定 1PCloop 的额度来源。turn 前先将其原始
  bytes、mode、mtime 和 SHA-256 保存到 `~/.codex-mix/.mix/transactions/1pcloop-auth/` 的 0600
  短期恢复文件；turn 后原子恢复并验证。允许 inode/ctime 改变，不允许内容或 mode 漂移；
- 每个 turn 同时持有 `switch.lock` 和 role lock。未完成事务会阻止新 turn 和 Codex Mix
  switch/rollback/arm。若 1PCloop 父进程崩溃，preflight 只在已验证 child 不存在时自动恢复；匹配的
  child 仍运行、备份缺失、hash 冲突或 PID identity 模糊时必须 fail closed；
- process receipt 只保存 alias、account ID SHA-256、恢复结果和零泄露扫描计数。完整 auth、原始
  account ID、邮箱、token 和子进程完整环境不得进入 prompt、evidence、Git、日志或通知程序。

[OpenAI 官方认证文档](https://learn.chatgpt.com/docs/auth?translationFallback=zh-Hans)说明基于文件的
登录缓存通常位于 `CODEX_HOME/auth.json`，并应像密码一样保护。
[OpenAI 官方 access-token 文档](https://learn.chatgpt.com/docs/enterprise/access-tokens)
明确把 `CODEX_ACCESS_TOKEN` 定义为单独创建的 Codex programmatic access token。普通 ChatGPT
OAuth cache 不是这种 token，所以 1PCloop 使用受事务保护的完整文件投影，不把 OAuth access token
塞进程序化 token 入口，也不把 role 中可能刷新的 credential 回写 canonical/vault。

每个 Codex child process 会同时将 `CODEX_HOME` 和 `CODEX_SQLITE_HOME` 设置为同一个 role runtime，
避免父 shell 中残留的 SQLite override 把 state DB/WAL 写到 canonical 或退休 home。process receipt 同时
记录这两个解析后的路径。不过
[OpenAI 官方文档](https://developers.openai.com/docs/config-file/environment-variables)规定
`config.toml` 的 `sqlite_home` 优先于 `CODEX_SQLITE_HOME`，因此 migration 还会检查 copied config：
`sqlite_home` 只能缺省，或精确解析到对应的新 role runtime；相对路径、旧 A/B 或任何其他目录都会
fail closed。

当前 tracked workload config 已指向新 runtime，两个 runtime 已完成 cold-copy 和 post-migration
validation。迁移种子仍是 Reviewer=B、Executor=A，但这只说明历史 state/session 来源，不再决定后续
1PCloop 的额度账号。额度账号始终来自每次 run 启动时的 Codex Mix active projection。

两个 runtime 的 `config.toml` 也已清除可执行的 A/B 回链：`notify` 改用
`~/.codex-mix/computer-use/...`，迁移遗留的 A/B project trust 条目已移除。日常检查可运行：

```bash
rg -n '/Users/smterpro/\.codex-[AB]|~/.codex-[AB]' \
  ~/.codex-mix/.mix/runtimes/1pcloop-reviewer/config.toml \
  ~/.codex-mix/.mix/runtimes/1pcloop-executor/config.toml
```

预期无输出。历史 session/evidence 中仍可出现 A/B provenance 文本，但不得作为新进程的配置路径。
`codex_mix_active` preflight 会执行同样的拒绝检查，并额外要求 `sqlite_home` 缺省或精确指向当前
role runtime；因此之后重新引入任何 A/B config 回链都会阻止 1PCloop 启动。

## 已执行的 cold-copy migration

脚本位置：

```text
1PCloop/scripts/migrate_codex_mix_runtime_homes.sh
```

脚本默认只检查，不迁移：

```bash
./1PCloop/scripts/migrate_codex_mix_runtime_homes.sh --check-only
```

历史迁移曾在 Human 明确授权后使用：

```bash
./1PCloop/scripts/migrate_codex_mix_runtime_homes.sh --execute
```

当前目标 runtime 已存在，因此脚本会 fail closed。不要为了日常运行再次执行 migration。

脚本的 fail-closed 边界：

- ChatGPT、Codex 或 1PCloop 相关进程存在时拒绝运行；
- canonical home 或 A/B source 下有打开文件时拒绝运行；
- 仅当两个目标都不存在时运行；
- source A 的 `account_id` 必须与 vault A 相同，source B 必须与 vault B 相同，A/B 必须互不相同；
- 使用 macOS `ditto --rsrc --extattr --acl` 完整 cold-copy B -> Reviewer、A -> Executor；
- 复制 regular files、directories、symlinks、SQLite/WAL、session、auth、config，并保留权限、时间、
  xattr、resource fork 和 ACL；
- 在 publish 前比较 source/target 的路径、类型、权限、owner、group、时间、大小、SHA-256、symlink
  target 和 xattr manifest；
- 目标必须是独立 inode，不得是 source alias；
- copy 后再次验证 Reviewer target 保留 B identity、Executor target 保留 A identity，且二者 distinct；
- 两个 role home 先共同写入一个 staging root，再以一次同文件系统 rename 原子发布整个
  `runtimes/` 根目录。正式根目录必须事先不存在；publish 失败时 staging 保持未发布状态，
  不会出现只发布一个 role home 的半迁移状态；
- 迁移前后核对 canonical 顶层全部 `*.sqlite*`、`.codex-global-state.json`、`sessions/`、
  `archived_sessions/`、`installation_id`、auth/config、history 和 `.mix/accounts` 未变化；
- 不删除 A/B，不修改 framework checkpoint，不修改 canonical history/session，不 rebaseline。

脚本不会输出 credential 内容，也不会把 manifest 持久写入任何 Codex home。

## Persistent Reviewer 与 checkpoint 约束

完整 cold-copy 会把旧 B 中的 Reviewer session 文件和 thread state 复制到新 Reviewer runtime，因而在
Codex storage 层最大限度保留 `codex exec resume <thread-id>` 所需材料。但是，现有 1PCloop checkpoint
还包含更严格的身份绑定，不能只改 workload JSON 后直接 resume。

当前约束包括：

1. workload config 的 raw SHA-256 和 canonical resolved SHA-256 被保存为
   `configuration.operator_config_identity`；
2. `checkpoint.configuration.reviewer_home` 和 `executor_home` 必须与当前 invocation 精确相同；
3. `checkpoint.run_configuration` 也保存两个 home 和 operator config identity；
4. 新 run 还保存 `account_source=codex_mix_active`、active alias 和 account ID SHA-256；resume 时当前
   Codex Mix identity 必须与 checkpoint 完全一致；
5. `reviewer_state.reviewer_thread_id` 决定后续 Reviewer 必须恢复哪个 thread；
6. 已完成 turn 的 `process.json.codex_home` 是历史 authority evidence，当前恢复校验要求它与 invocation
   home 相符；
7. manifest 和 raw process receipt 是历史证据，不能为了迁移而静默改写。

因此：

- 已完成的历史 run 保持 immutable，不迁移 checkpoint，也不重新 resume；
- 尚未启动的 workload 直接在 cold-copy 后使用新 runtime；
- 未完成的旧 checkpoint 当前不得手改或 resume，必须先实现并独立审核一次性的 checkpoint-home
  migration transaction。

该 transaction 至少需要原子完成并验证以下内容：

```text
checkpoint.configuration.reviewer_home
checkpoint.configuration.executor_home
checkpoint.configuration.operator_config_identity.raw_sha256
checkpoint.configuration.operator_config_identity.resolved_sha256
checkpoint.run_configuration.reviewer_home
checkpoint.run_configuration.executor_home
checkpoint.run_configuration.operator_config_identity
reviewer_state.reviewer_thread_id             保持不变
```

还必须追加不可变 migration record，记录 old/new home、cold-copy source/target manifest hash、旧/新 config
identity 和 Reviewer thread ID。runner 只能把旧 `process.json.codex_home` 当作 migration 前 provenance；
migration 后的新 turn 必须写入新 home。不得改写旧 process receipt、manifest 或 summary。当前版本没有实现
该 transaction，所以本轮不修改任何 checkpoint。

## 迁移后最小 smoke test

先记录退休 A/B 的时间边界：

```bash
touch /tmp/1pcloop-retired-home-marker
```

运行目标 workload 的 `doctor`、`preflight` 和一次有界 smoke。完成后验证 process receipt：

```bash
RUN=/absolute/path/to/1PCloop/.local/runs/<new-run-id>
find "$RUN" -name process.json -exec jq -e '
  select(has("codex_home")) |
  ((.codex_home == "/Users/smterpro/.codex-mix/.mix/runtimes/1pcloop-reviewer" or
    .codex_home == "/Users/smterpro/.codex-mix/.mix/runtimes/1pcloop-executor") and
   .account_source == "codex_mix_active" and
   .account_binding.credential_mode == "temporary-file-projection" and
   .account_binding.role_auth_restored == true and
   .account_binding.active_identity_unchanged == true and
   .account_binding.credential_scan.actual_credential_hits == 0)
' {} +
```

同一 run 的所有 receipt 还必须记录相同的 `account_binding.account_alias`，并与 run 启动前
`codex-switch.py status` 的 `marker` 相同。receipt 只能保存 alias 和 account ID SHA-256，不能出现 access
token、refresh token 或 ID token。

最后证明退休 home 没有新增或修改 regular file，同时新 runtime 产生了 session/activity：

```bash
find ~/.codex-A ~/.codex-B -type f -newer /tmp/1pcloop-retired-home-marker -print
find ~/.codex-mix/.mix/runtimes/1pcloop-reviewer \
     ~/.codex-mix/.mix/runtimes/1pcloop-executor \
     -type f -newer /tmp/1pcloop-retired-home-marker -print
```

第一条 `find` 必须无输出；第二条应只在两个 dedicated runtime 下显示新 activity。Codex Mix interactive
account 决定本次 run 的额度来源，runtime home 决定 role state。运行期间如果尝试切换账号，switch lock
或下一 turn 的 identity check 必须使操作 fail closed，不能静默改变额度账号。

终态 `inspect` 会逐字节重验 run 自己的 framework evidence commit，并要求该 commit 仍可从当前
framework local/remote branch 到达。后续普通治理 commit 不会使旧 run 失效；force-push、历史改写、
evidence commit 损坏或不可达仍会 fail closed。
