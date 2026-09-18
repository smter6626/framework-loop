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

每个 Codex child process 会同时将 `CODEX_HOME` 和 `CODEX_SQLITE_HOME` 设置为同一个 role runtime，
避免父 shell 中残留的 SQLite override 把 state DB/WAL 写到 canonical 或退休 home。process receipt 同时
记录这两个解析后的路径。不过
[OpenAI 官方文档](https://developers.openai.com/docs/config-file/environment-variables)规定
`config.toml` 的 `sqlite_home` 优先于 `CODEX_SQLITE_HOME`，因此 migration 还会检查 copied config：
`sqlite_home` 只能缺省，或精确解析到对应的新 role runtime；相对路径、旧 A/B 或任何其他目录都会
fail closed。

当前 tracked workload config 已指向新 runtime，但本次变更没有创建或复制这些目录。执行迁移前，
1PCloop 暂时处于有意的 fail-closed 状态。

## Cold-copy migration script

脚本位置：

```text
1PCloop/scripts/migrate_codex_mix_runtime_homes.sh
```

默认只检查，不迁移：

```bash
./1PCloop/scripts/migrate_codex_mix_runtime_homes.sh --check-only
```

未来经 Human 明确授权后才可执行：

```bash
./1PCloop/scripts/migrate_codex_mix_runtime_homes.sh --execute
```

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
4. `reviewer_state.reviewer_thread_id` 决定后续 Reviewer 必须恢复哪个 thread；
5. 已完成 turn 的 `process.json.codex_home` 是历史 authority evidence，当前恢复校验要求它与 invocation
   home 相符；
6. manifest 和 raw process receipt 是历史证据，不能为了迁移而静默改写。

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
  (.codex_home == "/Users/smterpro/.codex-mix/.mix/runtimes/1pcloop-reviewer" or
   .codex_home == "/Users/smterpro/.codex-mix/.mix/runtimes/1pcloop-executor")
' {} +
```

最后证明退休 home 没有新增或修改 regular file，同时新 runtime 产生了 session/activity：

```bash
find ~/.codex-A ~/.codex-B -type f -newer /tmp/1pcloop-retired-home-marker -print
find ~/.codex-mix/.mix/runtimes/1pcloop-reviewer \
     ~/.codex-mix/.mix/runtimes/1pcloop-executor \
     -type f -newer /tmp/1pcloop-retired-home-marker -print
```

第一条 `find` 必须无输出；第二条应只在两个 dedicated runtime 下显示新 activity。smoke 期间不得切换
Codex Mix interactive account 来解释 role identity，因为 interactive credential projection 与 1PCloop
runtime home 是不同维度。
