# 1PCloop

English | [简体中文](README.zh-CN.md)

1PCloop is a Reviewer–Executor automation loop that runs on one macOS machine. It uses two
isolated Codex identities to connect task contracts, authoritative current state, implementation,
independent review, Human Gates, and evidence retention into a sequential workflow that can be
recovered and audited.

```text
Human Owner
    |
    | defines objectives, authority, and Human-only decisions
    v
Static + Runtime
    |
    v
Python orchestrator
    |
    +--> Reviewer: reads governance/repository and compiles a bounded instruction
    |
    +--> Executor: implements, tests, and creates an ordinary descendant commit
    |
    +--> Reviewer: directly inspects commit, file, and test evidence
             |
             +--> ACCEPT: orchestrator validates and advances an authorized Runtime
             +--> REJECT: repair instruction goes to another Executor turn
             +--> HUMAN_GATE: stop and notify the Human Owner
```

## Delivered capabilities

The current implementation provides:

- explicit binding of two independent Codex profiles;
- automatic Reviewer → Executor → Reviewer routing with no Human copy/paste;
- complete identity/hash-bound framework and workload governance for the Reviewer;
- a bounded current-step instruction for the Executor;
- real changes, tests, and ordinary commits in an independent target repository;
- branch, HEAD, clean-worktree, ancestry, and governance-hash checks at control boundaries;
- Codex runtime-enforced output schemas plus local schema validation;
- verdict authority restricted to Reviewer review turns;
- locator, boundary, existence, reachability, and SHA-256 validation for evidence;
- Runtime writes gated by both an explicit Human CLI capability and workload Runtime opt-in;
- atomic Runtime transitions, overwrite-only checkpoints, and crash/restart reconciliation;
- Git-ignored raw evidence, concise per-turn summaries, and one framework evidence commit/push;
- up to two same-thread corrections for mechanically repairable Reviewer verdicts without
  replaying an already completed Executor;
- separate logical-outcome, Runtime-transition, and evidence-publication results;
- a versioned structured progress journal, atomic live-status snapshot, run/stage/timeout
  timing, and bounded terminal projection;
- pure mutation contract helpers with compatibility re-exports from the runner;
- a deterministic, read-only Human Gate projection shared by `status`, `inspect`, and
  `human-gate`;
- a local read-only TUI over the F2/F3/F5 operator projections;
- fail-closed behavior for state that cannot be explained mechanically.

These capabilities improve review independence, recoverability, and traceability. They do not
guarantee that an LLM is always correct and do not form an operating-system security boundary.

## Current implementation and extension boundary

The product already implements contract-backed context and a context-compiled fresh Executor.
The Reviewer receives complete governance with hashes and freshness metadata. Every Executor turn
uses a fresh session with a bounded instruction, and results return to the Reviewer only through
Git, artifacts, and evidence. Reviewer and Executor may use different model configurations; final
verdict authority belongs only to the Reviewer.

The current runner uses two Codex CLI profiles and runs one mutation Executor at a time. The
following belong to the extensible architecture described in the
[repository README](../README.md), not the current integrated product:

- independent per-role local/cloud/third-party provider adapters;
- formally validated Qwen/Ollama Executor plus cloud Reviewer deployment;
- Claude or other Agent-product adapters;
- multiple ephemeral workers selected by capability;
- governed image/vision routing;
- browser, MCP, plugin, and Computer Use capability/evidence/Human Gate integration;
- parallel mutation workers or multi-writer consistency.

A capability exposed by Codex CLI or a model is not automatically part of 1PCloop until the runner
places it inside identity, authority, evidence, and recovery contracts.

## Runtime environment

The default configuration targets:

- Apple Silicon Mac;
- macOS;
- Python 3.9 or later;
- an installed Codex CLI;
- two independent Codex identities/profiles.

Default role binding:

```text
Reviewer = CODEX_HOME=/Users/smterpro/.codex-mix/.mix/runtimes/1pcloop-reviewer
Executor = CODEX_HOME=/Users/smterpro/.codex-mix/.mix/runtimes/1pcloop-executor
```

Roles are defined by responsibilities, authority, and session state—not by model names. Reviewer
and Executor may use the same or different models. In practice, Reviewer capability and reasoning
effort should normally be at least as strong as the Executor's, especially for complex or
high-risk work. This is operational guidance, not a replacement for evidence and mechanical
validation.

The `~/.codex` symlink, foreground Codex GUI account, and open GUI windows do not select the role
runtime. Every invocation binds the intended `CODEX_HOME` explicitly. Codex Mix account aliases
(A-E in the vault as of 2026-11-18) are credential identities, not Reviewer/Executor roles.
Historical `~/.codex-A` and `~/.codex-B` homes are rejected as live role runtimes.

Both role homes must already exist as distinct, non-nested directories strictly under
`~/.codex-mix/.mix/runtimes/`, each with its own `config.toml` (no `.codex-A`/`.codex-B` path;
`sqlite_home` absent or equal to that role home) and a role `auth.json` file. The runner never
creates or migrates them.

Tracked workloads use `account_source=codex_mix_active`: a new run pins the current Codex Mix
active account, and both roles consume that account's quota while retaining separate runtime
state. Ordinary ChatGPT login uses a lock-protected, full `auth.json` file projection for one turn;
the original role bytes/mode are restored afterward and auth environment variables are not passed
to the Agent. Account drift, insufficient lifetime, A/B drift, or an unrecoverable credential
transaction fails closed. See the
[Codex Mix runtime-home and active-account guide](docs/codex-runtime-homes/README.md).

Operational consequences with the current Codex Mix deployment:

- choose the account in Codex Mix before starting a run; do not switch accounts during a run.
  Every turn holds `~/.codex-mix/.mix/switch.lock`, so Codex Mix switcher commands (including
  `codex-switch.py status`) report another operation in progress while a turn is active; a switch
  between turns makes the next turn fail closed;
- an unfinished record under `~/.codex-mix/.mix/transactions/1pcloop-auth/` makes Codex Mix refuse
  account switch, rollback, and arm until 1PCloop preflight recovers it or verified manual
  recovery is done; `codex-switch.py status` reports it as `auth_transactions_pending`;
- `codex_mix_active` preflight requires `~/.codex` to remain a symlink to `~/.codex-mix` and
  compares the retired `~/.codex-A`/`~/.codex-B` trees with the 21,091-entry snapshot under
  `~/.codex-mix/.mix/forensics/runtime-cutover-20260918/` and with
  `~/.codex-mix/.mix/original-baseline.json`. Keep both retired homes read-only: do not delete,
  move, open them as `CODEX_HOME`, or touch their files, or every run fails closed.

### Codex executable

Set `execution.codex_bin` to an absolute path. The Codex Mix records name the global fnm/npm
`@openai/codex` CLI for explicit CLI workflows such as 1PCloop; the most recent runs pinned
`/Users/smterpro/.local/share/fnm/node-versions/v24.18.0/installation/bin/codex`, which still
exists and reported `codex-cli 0.159.2` on 2026-11-18. A bare `codex` is resolved through `PATH`;
under fnm that can be a per-shell `fnm_multishells` path. Codex Desktop and Codex Mix use the
CLI bundled in `/Applications/ChatGPT.app/Contents/Resources/codex-cli/CodexCLI.app/Contents/MacOS/codex`,
which updates with ChatGPT.app and is not the 1PCloop CLI. Check the pinned version with
`<codex_bin> --version`; `doctor` only checks that `--version` succeeds and does not report the
version. The CLI must accept the
models configured in the two role `config.toml` files; a CLI upgrade is a Human-authorized,
recorded change, not an automatic fix.

## Installation

From the repository root:

```bash
python3 -m venv 1PCloop/.local/venv
1PCloop/.local/venv/bin/python -m pip install -r 1PCloop/requirements.txt
/absolute/path/to/codex --version   # the execution.codex_bin you will configure
```

`1PCloop/.local/` is Git-ignored and stores the Python environment, checkpoints, and future raw
run evidence.

## Static, Runtime, and external context

### Framework governance

- `docs/miniloop_static.md`: stable objectives, roles, authority, and safety boundaries for
  1PCloop as a whole.
- `docs/miniloop_runtime.md`: global milestones and the current task pointer; detailed task
  execution does not belong here.

### Task-local governance

Each sustained task should define:

```text
workloads/<workload-id>/workload_static.md
workloads/<workload-id>/workload_runtime.md
```

`workload_static.md` contains long-lived objectives, scope, prohibited actions, authority, and
acceptance criteria. `workload_runtime.md` contains accepted results, the one Active Step,
blockers, pending tasks, Human decisions, and evidence locators.

Static does not record progress; Runtime cannot silently amend Static. A completed task is frozen
by default, and a new objective should receive new task-local governance.

### Default Chinese prompt templates

- [Static prompt template](templates/static_prompt_zh.md) initializes, reviews, or performs an
  authorized revision of a stable task contract. Its read-only Framework v1.2 source is
  `/Users/smterpro/Workspace/Tools/structured-llm-execution-framework/structured-llm-execution-framework_static.md`
  at SHA-256
  `e3ff93b4136c0d3d87d7f1a319ca9c4513f831327daf18aea46f9f3d6659daf7`.
- [Runtime prompt template](templates/runtime_prompt_zh.md) restores authoritative state, reviews
  evidence independently, maintains the single Active Step, and advances state only when evidence
  supports it. Its read-only Framework v1.2 source is
  `/Users/smterpro/Workspace/Tools/structured-llm-execution-framework/structured-llm-execution-framework_runtime.md`
  at SHA-256
  `3cbc4c93adff6ac2b1fb351a8a81f4b65dbd73b4de28ee2d0d4141522258ab54`.

Open the appropriate tracked template, copy the content under `## 可复制 Prompt`, and replace only
the `{{...}}` placeholders supported by known task facts. Keep unknowns explicit and tailor away
sections that add no value for a low-risk task. The external Tools files are read-only provenance
inputs. These local snapshots do not synchronize automatically; any future template change must
recheck the source path and hash and receive independent review.

The orchestrator reconstructs Reviewer context from:

```text
framework Static
+ framework Runtime
+ workload Static
+ workload Runtime
+ target Git identity
+ current peer evidence
```

Conversation history is not authoritative memory. If a Reviewer thread cannot continue, it can
rebootstrap from repository-backed state. The Executor does not inherit the Reviewer's full
history; it receives only the current bounded instruction and necessary peer payload.

## Preparing a workload

### 1. Prepare an independent target repository

The mutation runner requires the target and framework repositories to be non-overlapping. Before
launch, the target must:

- be on the requested branch;
- have a resolvable HEAD;
- have a clean working tree;
- contain no unauthorized governance changes.

The Executor may create ordinary descendant commits on that branch. It must not push, merge,
switch branches, reset, clean, stash, or rewrite history.

### 2. Write workload Static

At minimum, define:

- objective and expected artifact;
- permitted and prohibited mutation paths;
- required Executor self-checks;
- evidence the Reviewer must inspect directly;
- Human Gate conditions;
- target branch and integration boundary.

### 3. Write workload Runtime

To permit an automatic ACCEPT → Runtime transition, include exactly one machine-owned block:

```markdown
<!-- 1PCLOOP_RUNTIME_STATE_BEGIN -->
{
  "schema_version": 1,
  "workload_id": "example-workload",
  "transition_mode": "reviewer_accept_once",
  "active_step": {
    "id": "S1",
    "status": "ACTIVE"
  },
  "last_transition_id": null
}
<!-- 1PCLOOP_RUNTIME_STATE_END -->
```

Each marker must appear exactly once. Python understands this machine block but does not interpret
the surrounding Markdown. The initial transition completes the current step, changes
`transition_mode` to `disabled`, records `last_transition_id`, and stops. It does not activate the
next step automatically.

## Preflight

The recommended and only policy-compliant entry is the workload-config CLI described in
[Workload config and operator CLI](#workload-config-and-operator-cli):
`onepcloop.py --config <workload.json> preflight` and then `run`. The long-argument examples in
this section and the next are the legacy direct runner interface; see the account policy below
before using them.

Validate paths, branch, governance identity, profiles, schemas, framework remote, and working
trees without invoking an Agent (legacy long-argument form):

```bash
1PCloop/.local/venv/bin/python 1PCloop/scripts/run_mutation_loop.py \
  --target-repo /absolute/path/to/target \
  --target-branch feature-branch \
  --workload-static /absolute/path/to/workload_static.md \
  --workload-runtime /absolute/path/to/workload_runtime.md \
  --workload-id example-workload \
  --enable-runtime-transition \
  --preflight-only
```

A failed preflight does not create a run or launch Reviewer/Executor.

## Running the mutation loop

```bash
1PCloop/.local/venv/bin/python 1PCloop/scripts/run_mutation_loop.py \
  --target-repo /absolute/path/to/target \
  --target-branch feature-branch \
  --workload-static /absolute/path/to/workload_static.md \
  --workload-runtime /absolute/path/to/workload_runtime.md \
  --workload-id example-workload \
  --enable-runtime-transition \
  --max-cycles 8 \
  --timeout-seconds 900 \
  --progress-interval-seconds 15
```

Common optional arguments:

```text
--reviewer-home
--executor-home
--codex-bin
--account-source
--framework-repo
--framework-branch
--framework-remote
--framework-push-ref
--framework-static
--framework-runtime
--run-id
--runs-root
--state-root
--summary-root
```

Both interfaces drive the same state machine and enforce the same account policy. Every new
run requires `account_source=codex_mix_active`: `run`, `preflight`, `doctor`, and a long-argument
invocation without `--resume` reject `runtime_home` before any Agent starts. The long-argument
parser exposes `--account-source {codex_mix_active,runtime_home}` with default
`codex_mix_active`. `runtime_home` lets each Codex child authenticate with whatever `auth.json`
is already in its role runtime (a migration-era cache) without `switch.lock`, active-account
projection, or the retired A/B snapshot check; it is accepted only together with `--resume`, to
finish a checkpoint that recorded it. Both refusals—`runtime_home` for a new run, and a resume
whose account source differs from the checkpoint—report `error_code="ACCOUNT_SOURCE_NOT_ALLOWED"`
in `FINAL_RESULT` with the reason in plain text.

The long-argument interface remains legacy: it has no retry arguments and records a `null`
operator config identity. Use the config CLI for new work. Its `--codex-bin` default is the
`codex` found on `PATH` at parse time.

## Workload config and operator CLI

`scripts/onepcloop.py` provides one versioned operator entry point:

```bash
1PCloop/.local/venv/bin/python 1PCloop/scripts/onepcloop.py \
  --config /absolute/path/workload.json doctor

# Replace doctor with: preflight, run, resume, status, inspect, human-gate, or tui.
```

The strict JSON config has exactly these required sections and fields, plus the optional
top-level `retry` section described below:

```json
{
  "schema_version": 1,
  "workload_id": "example-workload",
  "target": {"repo": "./target", "branch": "feature"},
  "governance": {
    "workload_static": "./workload_static.md",
    "workload_runtime": "./workload_runtime.md",
    "framework_repo": "../framework-loop",
    "framework_static": "../framework-loop/1PCloop/docs/miniloop_static.md",
    "framework_runtime": "../framework-loop/1PCloop/docs/miniloop_runtime.md"
  },
  "profiles": {
    "reviewer_home": "/Users/<user>/.codex-mix/.mix/runtimes/1pcloop-reviewer",
    "executor_home": "/Users/<user>/.codex-mix/.mix/runtimes/1pcloop-executor",
    "account_source": "codex_mix_active"
  },
  "execution": {
    "codex_bin": "/absolute/path/to/codex",
    "max_cycles": 8,
    "timeout_seconds": 900,
    "progress_interval_seconds": 15,
    "enable_runtime_transition": true
  },
  "evidence": {
    "runs_root": "../framework-loop/1PCloop/.local/runs",
    "state_root": "../framework-loop/1PCloop/.local/state",
    "summary_root": "../framework-loop/1PCloop/evidence-summaries"
  },
  "framework_git": {
    "branch": "main",
    "remote": "origin",
    "push_ref": "refs/heads/main"
  }
}
```

Replace `<user>` with the macOS user name; on this Mac the two homes are the
`/Users/smterpro/...` paths listed under Runtime environment. Both homes must be absolute or
config-relative paths that resolve strictly inside `~/.codex-mix/.mix/runtimes/`; a config that
omits `account_source` fails with `CONFIG_INVALID`. A config may still name
`"account_source": "runtime_home"`, but only to resume a checkpoint that recorded it: `doctor`
reports the `account_source` check as `FAIL`, and `preflight` and `run` refuse to start a new run
with it.

Optional explicit retry of a failed run:

```json
"retry": {"retry_of": "<failed-run-id>", "retry_reason": "<non-empty reason>"}
```

`retry` must contain exactly these two fields. Preflight accepts it only when the source run's raw
`manifest.json` and tracked summary exist, exactly one checkpoint with that run ID exists under
the parent of `state_root`, that checkpoint is `FRAMEWORK_EVIDENCE_PUSHED` with logical outcome
`FAILED_CLOSED`, and its initial target repo/branch/HEAD equal the current clean target. A retry
is a new run, never `resume`; give it a new `state_root` (as the tracked `*_retry_01.json` configs
do) and its run configuration records `retry_of` and `retry_reason`.

Duplicate keys, unknown or missing fields, wrong types/versions, prohibited credential/prompt
fields, and identical Reviewer/Executor profiles are rejected. Relative paths resolve from the
config file's directory, never the caller's working directory. `~` is rejected and environment
or shell expansion is not performed. The raw file SHA-256, canonical resolved-config SHA-256,
absolute config path, and workload ID form the config identity. New config-backed runs bind that
identity to the checkpoint and manifest; resume rejects any byte, resolved-value, path, profile,
target, governance, Git, or storage drift. Legacy invocations record a `null` operator config
identity and remain resumable only through their legacy long arguments—they are never guessed
into the new contract.

The workload configs already tracked under `workloads/` are historical records bound to finished
runs. Several point at target clones that no longer exist (for example
`workloads/whisper_release_1_1_0_v1/workload_rel1c1_continuation_01.json`), and their config
identity is part of recorded evidence. Do not edit or reuse them for new work: create a new
workload directory with its own Static, Runtime, and config.

Command behavior is:

- `doctor` checks Python/jsonschema, Codex executable/version, distinct profile directories, the
  configured account source, Git, target/framework identities, remote ref, governance/schemas, and
  ignored local storage. It creates no run/checkpoint and invokes no Agent. With
  `codex_mix_active`, the account check is the same Codex Mix binding preflight uses: it reads the
  active marker and credential identity (reporting only alias, account ID hash, and token TTL) and
  may recover a pending 1PCloop auth transaction whose child is verified to have exited.
- `preflight` calls the existing mutation-runner validator and emits its report without creating
  evidence or invoking an Agent.
- `run` compiles config into the existing runner and executes the unchanged Reviewer–Executor
  state machine.
- `resume` reads exactly `<state_root>/<workload_id>/checkpoint.json`, obtains its run ID, and
  validates the saved exact config identity. It never scans directories or accepts overrides.
- `status` projects checkpoint, F2 live/event observation, and F1 final-result fields, including
  cycle/role/timers/activity/target, logical outcome, Runtime transition, publication,
  Human-Gate/failed-closed flags, artifact locators, observation availability, and one mechanical
  safe action: `RESUME_ALLOWED`, `HUMAN_REVIEW_REQUIRED`, `TERMINAL_SUCCESS`,
  `TERMINAL_FAILURE`, `START_NEW_RUN_ALLOWED`, or `STATE_UNAVAILABLE`.
- `inspect` read-only validates config/checkpoint/manifest identity, F2 sequence/hash/suffix and
  live projection, tracked summary and available raw-artifact hashes, framework evidence
  commit/push, and target Git identity. For an ACCEPT transition it binds the transition record to
  the exact routed Reviewer verdict, correction resolution, unique summary entry, target HEAD,
  and evidence list; superseded verdict evidence remains provenance and is not re-authorized.
  HUMAN_GATE, FAILED_CLOSED, REJECT/correction-exhausted, and capability-disabled runs report
  target evidence as `NOT_APPLICABLE`. Missing Git-ignored raw evidence or an incomplete JSONL
  tail is `UNAVAILABLE`; conflicting complete evidence is `FAIL`. An overall `PASS` means the
  evidence package is internally consistent, not that the task was accepted. Inspect never
  truncates the journal or repairs an artifact. The result separately classifies authoritative
  target evidence as `VALID`, `INVALID`, `UNAVAILABLE`, or `NOT_APPLICABLE`.
- `human-gate` returns the same bounded Human Gate projection used by `status` and `inspect`. It
  creates no run, checkpoint, Agent turn, repair, or Human decision.
- `tui` opens a local read-only dashboard over `status`, `inspect`, and their shared Human Gate
  projection. It does not call the runner or execute a recovery action.

`status` and `inspect` keep their F3 top-level checkpoint, logical outcome, Runtime transition,
publication, and safe-action fields. Their Human Gate fields are grouped under
`result.human_gate_projection`; `human-gate` returns that projection directly in `result`.
All three use one read-only authoritative-integrity check set. It validates local evidence,
target branch/HEAD/cleanliness, formed framework commit identity, completed remote push identity,
and authoritative ACCEPT target evidence when applicable. Missing required raw evidence is
`UNAVAILABLE`; an identity conflict is `INVALID` and never suggests finalization or a new run.
An unformed commit or incomplete push is not an identity conflict merely because its artifact
does not yet exist.

`doctor`, `preflight`, `status`, `inspect`, and `human-gate` print exactly one compact JSON object with
`schema_version`, command, config identity, overall status, checks/result, and public artifact
locators. `PASS` and `UNAVAILABLE` return 0; `FAIL` returns 1; invalid config returns 2. Exceptions,
profile contents, prompts, peer messages, command output, stderr, and internal diagnostics are not
included. `run` and `resume` retain existing `PROGRESS` plus F1 `FINAL_RESULT` output.

`scripts/mutation_contracts.py` owns side-effect-free control/message/public-result contracts.
`scripts/human_gate.py` is a pure projection over structured state and public locators. It does
not import the runner or inspect artifacts. `scripts/workload_operator.py` supplies the shared
read-only integrity result to the pure projection and to `inspect`.
`run_mutation_loop.py` re-exports its historical contract names for compatibility and remains
the only mutation control state machine.

Human Gate states are `ACTIVE`, `NOT_APPLICABLE`, `UNAVAILABLE`, and `INVALID`. Allowed actions
are limited to `INSPECT_EVIDENCE`, `FINALIZE_EVIDENCE`, `REMEDIATE_EXTERNAL_STATE`,
`START_NEW_RUN_AFTER_HUMAN_REVIEW`, and `NO_AUTOMATIC_REPAIR`. Recovery modes are
`FINALIZATION_ONLY`, `HUMAN_REMEDIATION_REQUIRED`, `NEW_RUN_AFTER_REVIEW`, and `NO_ACTION`.
Unknown or conflicting state defaults to inspection and Human remediation, never automatic
repair. A complete evidence package does not resolve a Human Gate, and successful evidence
publication does not change the logical outcome.

The Human Gate projection cannot resolve a gate. The TUI displays its fixed actions as guidance,
not buttons or commands. The independently accepted F7 real-service smoke is recorded in
[`f7-post-foundation-real-service-smoke-20260918.md`](evidence-summaries/f7-post-foundation-real-service-smoke-20260918.md).
The independently accepted
[`F8 foundation disposition`](evidence-summaries/f8-foundation-disposition-20260918.md) closes
`foundation_v1`: GUI and governance compression are deferred, while the default-safe raw evidence
lifecycle policy is active without authorizing deletion or a cleaner. There is no current
engineering task; overall 1PCloop remains `ACTIVE` until the Human Owner makes the completion
decision reserved by the global Static.

## Local read-only TUI

On a macOS interactive terminal, launch the config-backed dashboard with:

```bash
1PCloop/.local/venv/bin/python 1PCloop/scripts/onepcloop.py \
  --config /absolute/path/workload.json tui
```

`r` refreshes, `Tab` switches summary and inspection, `j`/`k` or arrow keys scroll, `?` toggles
help, and `q` or Esc quits. The keys are shown in the footer or help view. The dashboard refreshes
at most once per second while idle, handles resize and narrow terminals, and restores terminal
settings on exit. Non-TTY use exits with a plain error message and no screen control sequences.

`scripts/local_tui.py` separates the operator data source from the pure presenter. It renders only
the structured `status`/`inspect` envelopes and nested F5 Human Gate projection; it never opens
raw Codex events, prompts, peer messages, stderr, or command output. It displays run/cycle/role,
control state, target HEAD, F2 active-time elapsed/timeout/activity, observation and integrity
availability, and the three independent logical/Runtime/publication states. It does not add
offline wall time to F2 elapsed values. When observation is unavailable, unverified progress is
hidden. If consecutive `status` and `inspect` reads disagree, recovery actions are hidden until
refresh. For a no-checkpoint candidate, the data source reads `status -> inspect -> status`;
ordinary existing runs use only `status -> inspect`. `NO CHECKPOINT` requires identical exact
no-checkpoint status projections before and after inspect, matching config and checkpoint
locators, and no real run projection from inspect. Inspect's generic checkpoint identity failure
alone does not prove absence. A changed or invalid bracket displays `SNAPSHOT UNAVAILABLE`
without recovery guidance until a consistent refresh. Final terminal rows escape Unicode
`Cc`, `Cf`, `Zl`, and `Zp` characters before width bounding, so embedded line or paragraph
separators cannot forge another row. `PUSHED` is only publication, not logical success; a terminal
Human Gate is never shown as ordinary Agent resume. `INVALID` or `UNAVAILABLE` never gets broader
advice than the F5 projection.

The TUI never starts or resumes an Agent, finalizes evidence, repairs identity, or writes
checkpoint, evidence, Git, or governance state. It is a single-writer local dashboard, not a
concurrency protocol or GUI. A very narrow terminal shows a resize/quit notice rather than the
full view. F7 exercised this TUI in a real PTY without changing authoritative artifacts. The F8
disposition defers a separate local GUI until direct usability or accessibility evidence justifies
its additional state, security, packaging, and maintenance surface.

## Automatic loop semantics

### Reviewer instruction

The Reviewer creates a persistent thread, reads complete current governance and target state, and
returns one bounded instruction. It must not modify the target, Git state, or governance.

### Executor mutation

The Executor uses a fresh ephemeral session to implement the task, run tests, create a commit, and
leave a clean working tree. Its report cannot trigger acceptance.

### Reviewer verdict

The original Reviewer thread is explicitly resumed. It must inspect the actual target, commits,
files, tests, and hashes before returning a runtime-enforced verdict.

```text
ACCEPT
  -> mechanically validate identity, target, governance, evidence, and capability
  -> atomically complete one authorized workload Runtime transition

REJECT
  -> Runtime remains unchanged
  -> route the complete repair instruction to the next fresh Executor

HUMAN_GATE
  -> Runtime remains unchanged
  -> stop automatically and display Human Gate state and evidence location
```

Words such as `ACCEPT`, `PASS`, or `READY` in free text have no control authority.

## Reviewer verdict correction

If the Reviewer process, schema, profile, thread, read-only audit, and actual target/governance
state are valid, but evidence locators, hashes, or other declarations contain a specifically
classified mechanical error, the runner resumes the same Reviewer thread and requests a complete
corrected verdict.

- At most two correction turns are allowed.
- An already completed Executor is not replayed.
- Python never deletes, fills, converts, or guesses Reviewer evidence.
- A correction may return ACCEPT, REJECT, or HUMAN_GATE.
- Schema/process/profile/thread failures and actual state/evidence drift are not correctable.
- Two failed corrections end in `VERDICT_CORRECTION_EXHAUSTED / FAILED_CLOSED`.

Every `file`, `artifact`, or `test` locator must be an absolute path to an existing file inside
the target/run boundary. A shell command, Git-status description, or prose is not a locator. Do
not invent evidence when no real output file exists.

## Checkpoints and recovery

Default checkpoint:

```text
1PCloop/.local/state/<workload-id>/checkpoint.json
```

The checkpoint is atomically replaced at control boundaries. It records control state, turn
identity, Reviewer thread, target/governance identity, correction attempts, Runtime transition,
summary progress, and publication recovery. It is the current recovery state, not checkpoint
history.

During a run, the terminal reports:

- role, cycle, and control state;
- Codex process start/finish;
- bounded machine-readable tool activity;
- current-turn elapsed heartbeats;
- summary, Runtime-transition, framework commit/push state;
- Human Gates, errors, and the final result.

Resume an incomplete config-backed run with the unchanged config:

```bash
1PCloop/.local/venv/bin/python 1PCloop/scripts/onepcloop.py \
  --config /absolute/path/workload.json resume
```

A legacy long-argument run is resumed with exactly the same arguments plus `--resume`:

```bash
1PCloop/.local/venv/bin/python 1PCloop/scripts/run_mutation_loop.py \
  <all arguments from the original run> \
  --resume
```

Long-argument runs started before `--account-source` existed recorded `runtime_home`; resume them
by adding `--account-source runtime_home`.

Resume revalidates configuration, target, governance, turns, evidence, and framework identity.
Mechanically attributable Agent turns, Executor commits, corrections, Runtime transitions,
summaries, framework commits, and pushes are not repeated. If the runner cannot safely determine
whether an Executor changed the target, it enters a Human Gate instead of replaying blindly.

The config-backed `status`, `inspect`, and `human-gate` commands use the same read-only Human Gate
projection. They do not resume work or make Human decisions. Publication recovery may resume only
evidence finalization after a logical terminal; it cannot replay Reviewer or Executor turns.

### Stopping and resuming

Each Codex child is started in its own session (`start_new_session=True`), so terminal Ctrl+C
reaches the runner's foreground process group, not the Codex child directly. The runner then
sends SIGTERM to the child's process group, waits 5 seconds, sends SIGKILL if needed, and unwinds
the credential transaction, restoring and verifying the role `auth.json`; if that recovery cannot
be verified, the transaction record stays for the next preflight. The interrupt is not converted
into `FINAL_RESULT`; the checkpoint stays at its last control boundary.

- Press Ctrl+C once and wait for the runner to exit. Do not press it repeatedly, and do not use
  `kill -9` or `pkill` by process name: that can skip auth restoration, leave an unfinished
  transaction that blocks Codex Mix switching, or leave tool subprocesses behind.
- After stopping, run `status` and `inspect` with the same config. Also check the target branch,
  HEAD, and cleanliness, and that no 1PCloop auth transaction is pending (`auth_transactions_pending`
  in `codex-switch.py status`).
- Run `resume` only when `status` reports `RESUME_ALLOWED` and the checks agree. An Executor that
  committed without a receipt may lead to a Human Gate, and a dirty target fails closed. Resume
  does not continue the interrupted Agent's internal reasoning; it restarts from the checkpoint.

Optionally, for long runs, wrap the command with `/usr/bin/caffeinate -i` so the Mac does not
idle-sleep; the assertion ends when the runner exits:

```bash
/usr/bin/caffeinate -i \
  1PCloop/.local/venv/bin/python 1PCloop/scripts/onepcloop.py \
  --config /absolute/path/workload.json run
```

## Structured progress and live status

Every non-preflight mutation run writes two observation artifacts under its existing Git-ignored
run root:

```text
<run-root>/control-events.jsonl
<run-root>/live-status.json
```

`control-events.jsonl` is an append-only, schema-versioned orchestrator event stream. Each event
has a contiguous sequence number and a SHA-256 `event_id` over its canonical envelope. The fixed
fields project run ID, cycle, role, checkpoint control state, target HEAD, run/stage elapsed time,
active-turn timeout remaining, last machine activity, aggregated tool activity, logical outcome,
Runtime transition, and evidence publication. Unavailable values are `null`; events never contain
prompts, peer messages, evidence summaries, commands, command output, stderr, or hidden reasoning.
Raw Codex `events.jsonl` remains separate and byte-preserved.

`live-status.json` is an atomically replaced projection of the latest structured event. It is
derived observation state, not another Runtime and not an authority for transition or recovery.
The overwrite path uses a same-directory temporary file, fsync, and `os.replace`.

Timing semantics are:

- run elapsed accumulates only time during active orchestrator invocations; stopped wall time
  between crash and resume is excluded;
- stage elapsed resets only when the checkpoint control state changes; resuming the same state
  continues the checkpointed/event-derived accumulated value;
- elapsed values clamp monotonic-clock rollback and never decrease or become negative;
- timeout remaining exists only during an active Codex subprocess turn, never increases, clamps
  at zero, and becomes `null` when the turn ends;
- last activity changes only for explicit state, resume, Codex machine, heartbeat, tool, logical,
  evidence-finalization, error, or finish events—not from Agent natural language.

On resume, the journal validates every complete JSONL line, event ID, contiguous sequence, run
identity, checkpoint cursor, and any post-checkpoint event suffix. The checkpoint progress state
must equal the outer checkpoint state. Every complete suffix event must preserve the checkpoint's
run ID, control state, cycle, target HEAD, logical outcome, Runtime-transition projection, and
evidence-publication projection. Sequence/ID/time/activity/tool fields may advance only through
the declared state-marker, resume, turn-start, active Codex/heartbeat/tool, turn-finish,
correction, logical, evidence, error, and finish transitions. Run/stage values cannot precede the
checkpoint anchors, role/timeout changes must match turn lifecycle, and `run_finished` requires an
already checkpointed logical outcome. A partial final JSONL line is discarded as an incomplete
observation write; every complete conflicting line fails closed even when its unkeyed event hash
is internally valid. Existing events are never duplicated. Sequence and active elapsed time
continue from the validated maximum without treating an old heartbeat as new activity.
`live-status.json` is safely regenerated from the next event.

Tool activity records only the machine item category (`command_execution`, `mcp_tool_call`, or
`web_search`) and an aggregate count. It emits immediately, then at most once per configured
progress interval, with a final flush when necessary. State changes, errors, Human Gates, logical
outcomes, evidence-finalization changes, and `run_finished` are never throttled.

When structured observation is available, the raw Codex pump never emits a second legacy machine
or tool line: terminal visibility follows the structured recorder's emit/throttle decision. If
event append becomes unavailable, a separate fixed-category `CODEX_FALLBACK` path exposes
low-frequency machine events and at most an initial plus final aggregated tool line. It never
includes commands, arguments, output, peer content, or secrets.

The terminal renderer consumes the same event object and emits fixed `PROGRESS` lines with JSON
scalar values. TTY and non-TTY currently use the same durable line-oriented form. Control
characters reuse the F1 public-string boundary. A live-status or terminal-render failure marks
that projection unavailable but cannot apply, roll back, or block an otherwise valid Runtime
transition; an event-append failure similarly degrades observation without changing authoritative
control state. Event/checkpoint identity conflict at resume still fails closed.

F1 `FINAL_RESULT` remains unchanged and is emitted after the final `run_finished` projection.
F2 was independently accepted after its initial review rejected incomplete checkpoint-suffix
validation and duplicate legacy tool output; repair commit
`54ccf66a1c95843ae680e0c8f50ed98c5df6c0a5` closes both findings. The F3 operator commands consume
these structured artifacts without changing F2 recovery semantics. The local TUI displays their
read-only projections without replacing the F2 terminal or recovery contract.

## Evidence

Raw evidence for future mutation runs defaults to:

```text
1PCloop/.local/runs/<run-id>/
```

It may include prompts, raw Codex `events.jsonl`, stderr, final messages, peer payloads, process
metadata, the raw manifest, `control-events.jsonl`, and `live-status.json`. These files are
Git-ignored by default and do not become long-lived Git history.

Every completed turn creates one bounded entry in:

```text
1PCloop/evidence-summaries/<run-id>.md
```

The entry records role/cycle, time, target/governance identity, the LLM-authored
`evidence_summary`, and raw locators/hashes without copying complete prompts, peer messages,
events, stderr, or hidden reasoning.

At a logical terminal state, the runner creates one allowlisted evidence commit in the framework
repository and pushes it non-force to the configured framework remote. It never pushes or merges
the target repository.

## FINAL_RESULT

Every non-preflight invocation ends with fixed public fields:

```text
FINAL_RESULT
run_id="example"
logical_outcome="RUNTIME_TRANSITION_COMMITTED"
exit_code=0
runtime_transition="APPLIED"
evidence_publication="PUSHED"
reason="one_reviewer_accept_transition_completed"
error_code="RUNTIME_TRANSITION_COMMITTED"
run_root="/absolute/path/to/run"
```

Values after `=` are single-line JSON scalars, so embedded line breaks cannot forge new fields.
The public reason is limited to 512 characters. Full internal exceptions remain only in the local
`internal_diagnostic`.

Always inspect all three result dimensions:

```text
logical_outcome
runtime_transition
evidence_publication
```

For example, `evidence_publication="PUSHED"` means that evidence for a failed or successful run
was published; it does not mean that the task was accepted. The shell exit code is not a
substitute for Human-Gate or Runtime semantics.

## Isolation and safety boundary

To let the Executor create real Git commits, the mutation runner currently invokes both roles
with `--dangerously-bypass-approvals-and-sandbox`. Its safety boundary combines:

- separate profiles and sessions;
- role prompts and bounded instructions;
- non-overlapping target/framework paths;
- before/after read-only audits for Reviewer turns;
- target branch/HEAD/cleanliness/ancestry validation;
- governance and evidence hashes;
- explicit commit allowlists;
- fail-closed behavior and Human Gates.

This is not a production security boundary against a malicious local process. Codex running as
the same macOS user still has broad file access. The supported deployment has one Human
contributor, one active loop, and one target writer. Parallel Executors, multi-writer
reconciliation, repository locks, watchers, and distributed consistency are not supported.

## Validated results

Repository-backed evidence covers:

- independent sequential invocation of two Codex identities;
- byte-preserving Reviewer/Executor message routing;
- persistent Reviewer resume and fresh-session reconstruction;
- unchanged-governance, Runtime-change, and Static-change freshness policies;
- real mutation, testing, commit, and independent review in disposable Git targets;
- multi-cycle changes and a Human Gate on a real medium-scale external project;
- fail-closed handling for invalid schemas, stale state, wrong roles/threads, and bad evidence;
- crash-boundary recovery for Runtime transition and summary/commit/push;
- same-thread Reviewer verdict correction with fixed limits and Executor idempotence;
- terminal protection against control characters, unbounded reasons, and field injection.
- structured progress sequence/identity recovery, monotonic active timing, live projection,
  tool-activity throttling, and observation-failure isolation.

The deterministic regression suite passes with `ResourceWarning` promoted to an error.
Historical experiments, phase verdicts, and complete evidence locators live
in `docs/miniloop_runtime.md`, `evidence-summaries/`, `runs/`, and Git history; this README does
not duplicate progress records.

## Tests

Run the complete strict regression:

```bash
1PCloop/.local/venv/bin/python \
  -W error::ResourceWarning \
  -m unittest discover \
  -s 1PCloop/tests \
  -v
```

Focused suites:

```text
tests/test_run_text_loop.py          text transport and context reconstruction
tests/test_run_mutation_loop.py      mutation state machine and restart
tests/test_runtime_transition.py     structured verdict and Runtime transition
tests/test_evidence_summary.py       summary, commit, and push recovery
tests/test_verdict_correction.py     verdict correction and public result
tests/test_progress_status.py        structured progress, timing, status, and recovery
tests/test_operator_cli.py           workload config and operator commands
tests/test_mutation_contracts.py     pure contracts and runner compatibility
tests/test_codex_mix_account.py      active-account, token, and A/B baseline binding
tests/test_human_gate.py             Human Gate projection and read-only CLI
tests/test_local_tui.py              read-only TUI presenter and disposable integration
tests/test_prompt_templates.py       Chinese Static/Runtime prompt templates and provenance
tests/test_runtime_home_migration.py runtime-home migration tooling and tracked home policy
```

## Code and documentation map

```text
scripts/run_mutation_loop.py      current mutation orchestrator
scripts/mutation_contracts.py     side-effect-free control/message contracts
scripts/codex_mix_account.py      fail-closed Codex Mix active-account binding
scripts/human_gate.py             pure Human Gate status projection
scripts/local_tui.py              read-only terminal presenter and operator data source
scripts/run_text_loop.py          read-only text-routing/context diagnostic runner
scripts/p63_evidence.py           summary, framework commit, and push helper
scripts/progress_status.py        F2 progress journal, live snapshot, and renderer
scripts/workload_operator.py      config, diagnostics, and read-only projections
scripts/onepcloop.py              unified operator CLI
scripts/codex_runtime_migration.py
                                  validation/transaction helpers for runtime-home migration
scripts/migrate_codex_mix_runtime_homes.sh
                                  completed one-time A/B -> role runtime cold copy (--check-only default)
schemas/                          runtime-enforced Agent output schemas
roles/                            text-routing role prompts
workloads/                        task-local governance
docs/miniloop_static.md           global stable contract
docs/miniloop_runtime.md          global history and current task pointer
docs/codex-runtime-homes/README.md
                                  Codex Mix role runtime homes and active-account binding
templates/                        default Chinese Static/Runtime prompt templates
evidence-summaries/               tracked compact evidence
runs/                             retained historical run evidence
history/                          frozen early implementation
```

Read the corresponding Runtime for current task state. This README documents stable architecture,
operation, delivered behavior, and known boundaries—not task progress.
