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
Reviewer = CODEX_HOME=/Users/smterpro/.codex-B
Executor = CODEX_HOME=/Users/smterpro/.codex-A
```

Roles are defined by responsibilities, authority, and session state—not by model names. Reviewer
and Executor may use the same or different models. In practice, Reviewer capability and reasoning
effort should normally be at least as strong as the Executor's, especially for complex or
high-risk work. This is operational guidance, not a replacement for evidence and mechanical
validation.

The `~/.codex` symlink, the foreground Codex GUI account, and open GUI windows do not select role
identity. Every invocation binds the intended `CODEX_HOME` explicitly.

## Installation

From the repository root:

```bash
python3 -m venv 1PCloop/.local/venv
1PCloop/.local/venv/bin/python -m pip install -r 1PCloop/requirements.txt
codex --version
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

Validate paths, branch, governance identity, profiles, schemas, framework remote, and working
trees without invoking an Agent:

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
--framework-repo
--framework-branch
--framework-remote
--framework-push-ref
--run-id
--runs-root
--state-root
--summary-root
```

This long-argument interface remains supported. The workload-config interface below compiles to
the same arguments and state machine.

## Workload config and operator CLI

`scripts/onepcloop.py` provides one versioned operator entry point:

```bash
1PCloop/.local/venv/bin/python 1PCloop/scripts/onepcloop.py \
  --config /absolute/path/workload.json doctor

# Replace doctor with: preflight, run, resume, status, inspect, or human-gate.
```

The strict JSON config has exactly these sections and fields:

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
    "reviewer_home": "/absolute/reviewer-profile",
    "executor_home": "/absolute/executor-profile"
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

Duplicate keys, unknown or missing fields, wrong types/versions, prohibited credential/prompt
fields, and identical Reviewer/Executor profiles are rejected. Relative paths resolve from the
config file's directory, never the caller's working directory. `~` is rejected and environment
or shell expansion is not performed. The raw file SHA-256, canonical resolved-config SHA-256,
absolute config path, and workload ID form the config identity. New config-backed runs bind that
identity to the checkpoint and manifest; resume rejects any byte, resolved-value, path, profile,
target, governance, Git, or storage drift. Legacy invocations record a `null` operator config
identity and remain resumable only through their legacy long arguments—they are never guessed
into the new contract.

Command behavior is:

- `doctor` checks Python/jsonschema, Codex executable/version, distinct profile directories, Git,
  target/framework identities, remote ref, governance/schemas, and ignored local storage. It
  creates no run/checkpoint and invokes no Agent.
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

The Human Gate projection is not an interactive decision surface and cannot resolve a gate.
The F6 TUI and F7 real-service smoke are not implemented.

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

Resume an incomplete run with exactly the same arguments plus `--resume`:

```bash
1PCloop/.local/venv/bin/python 1PCloop/scripts/run_mutation_loop.py \
  <all arguments from the original run> \
  --resume
```

Resume revalidates configuration, target, governance, turns, evidence, and framework identity.
Mechanically attributable Agent turns, Executor commits, corrections, Runtime transitions,
summaries, framework commits, and pushes are not repeated. If the runner cannot safely determine
whether an Executor changed the target, it enters a Human Gate instead of replaying blindly.

The config-backed `status`, `inspect`, and `human-gate` commands use the same read-only Human Gate
projection. They do not resume work or make Human decisions. Publication recovery may resume only
evidence finalization after a logical terminal; it cannot replay Reviewer or Executor turns.

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
these structured artifacts without changing F2 recovery semantics. Interactive TUI remains F6
scope.

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
tests/test_human_gate.py             Human Gate projection and read-only CLI
```

## Code and documentation map

```text
scripts/run_mutation_loop.py      current mutation orchestrator
scripts/mutation_contracts.py     side-effect-free control/message contracts
scripts/human_gate.py             pure Human Gate status projection
scripts/run_text_loop.py          read-only text-routing/context diagnostic runner
scripts/p63_evidence.py           summary, framework commit, and push helper
scripts/progress_status.py        F2 progress journal, live snapshot, and renderer
scripts/workload_operator.py      config, diagnostics, and read-only projections
scripts/onepcloop.py              unified operator CLI
schemas/                          runtime-enforced Agent output schemas
roles/                            text-routing role prompts
workloads/                        task-local governance
docs/miniloop_static.md           global stable contract
docs/miniloop_runtime.md          global history and current task pointer
evidence-summaries/               tracked compact evidence
runs/                             retained historical run evidence
history/                          frozen early implementation
```

Read the corresponding Runtime for current task state. This README documents stable architecture,
operation, delivered behavior, and known boundaries—not task progress.
