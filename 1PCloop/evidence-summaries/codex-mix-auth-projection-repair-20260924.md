# Codex Mix file credential projection repair - 2026-09-24

## Scope

This repair replaces the invalid ordinary-OAuth-to-`CODEX_ACCESS_TOKEN` path with a recoverable
full-file projection for dedicated Reviewer and Executor runtimes. Historical failed run
`20260924T220337Z-47406` and evidence commit `0da9c5fa4e384beda6e908a4028846f3acda7429`
remain unchanged.

## Implemented safety boundary

- A new run pins the Codex Mix active alias and account ID SHA-256.
- Every turn holds the Codex Mix switch lock and one role lock.
- The original role `auth.json` is backed up under a 0700 transaction directory with 0600 files.
- The complete canonical active `auth.json` is atomically projected with mode 0600.
- The child receives `CODEX_HOME` and `CODEX_SQLITE_HOME`, but no auth token environment variable.
- `cli_auth_credentials_store="file"`, auth environment exclusion, and `notify=[]` are forced.
- PID, PGID, process start identity, executable, and command fingerprint are persisted without
  storing the full command or child environment.
- Normal exit, nonzero exit, timeout, invalid output, and Python exceptions share the same restore
  path. The original role bytes and mode are verified after atomic restoration.
- Preflight recovers incomplete transactions only after proving the recorded child is gone.
  A matching live child, ambiguous PID identity, missing backup, or hash conflict fails closed.
- Codex Mix switch, rollback, and arm operations refuse unfinished 1PCloop auth transactions.
- The 21,091-entry retirement snapshot is validated before and after each turn.
- Output scanning uses actual in-memory credential values without printing or hashing them into
  tracked evidence. Run artifacts, role sessions/logs, crash reports, tracked/untracked Git files,
  and Git diff bytes are covered. Actual credential hits fail closed.

## Deterministic validation

- Codex Mix auth transaction focused suite: 14/14 PASS.
- Mutation runner focused suite: 13/13 PASS.
- Runtime-home migration/documentation suite: 7/7 PASS.
- Explicit retry identity test: PASS.
- Full `-W error::ResourceWarning` regression: 222/222 PASS in 238.635 seconds.
- Python 3.9 compilation, `git diff --check`, role-config path validation, and live Codex Mix
  preflight: PASS.
- Codex Mix backend pending-transaction guard fixture: PASS.

The crash matrix covers initialized transaction metadata, role-auth backup, projected credential,
child-running refusal, child-exited recovery, restore-in-progress recovery, restored-before-delete
cleanup, missing backup refusal, setup exception, Python body exception, unexpected role-auth
mutation, and actual-secret scan failure. Each case either restores verified original bytes/mode or
stops with persistent recovery evidence.

## Real service smoke

Local ignored evidence root:

```text
/Users/smterpro/Workspace/framework-loop/1PCloop/.local/auth-smoke-wuqrm3yb
```

Three bounded Codex service turns returned exactly `auth-ok`:

1. Reviewer fresh persistent turn.
2. Reviewer explicit resume of the same observed thread.
3. Executor fresh ephemeral turn.

All three exited zero with no 401, restored the corresponding role-auth bytes/mode, reported zero
actual credential hits, left no auth transaction, kept active identity unchanged, and preserved the
A/B retirement snapshot. The target repository was not used or modified.

Compact smoke summary SHA-256:

```text
ae003a1eef8cbac7fe028be419e49106deca29ddce68688a1c5953f1c2750556
```

This tracked summary intentionally omits account labels, raw account IDs, token values, token
hashes, auth JSON, child environments, prompts, stderr bodies, and session content.

## Retry boundary

The next layout run must use `window_layout_retry_01.json`, a new run ID, and a distinct state root.
It records:

```json
{
  "retry_of": "20260924T220337Z-47406",
  "retry_reason": "codex_mix_file_credential_projection_fix"
}
```

Preflight requires exactly one immutable terminal-failure checkpoint for that run ID and requires
the current target repo, branch, clean state, and HEAD to match the failed run's initial target.
The old run cannot be resumed or overwritten.
