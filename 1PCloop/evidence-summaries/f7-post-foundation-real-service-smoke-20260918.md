# F7 post-foundation real-service smoke -- compact evidence

## Result and authority boundary

Executor observation: `PASS -- AWAITING INDEPENDENT F7 REVIEW`.
This is one real Codex-service Reviewer -> Executor -> Reviewer run, not an
independent acceptance verdict. The machine-validated logical outcome was
`RUNTIME_TRANSITION_COMMITTED`, the Runtime transition was `APPLIED`, and
evidence publication was `PUSHED`. These three states were checked separately.
No F7 acceptance, foundation closure, or F8 activation is claimed here.

The source framework-loop repository was clean at baseline commit
`975ecf6820d2d561759870a1d813e0974ec5da2a`. Its foundation_v1 Static
SHA-256 was
`0995a0374205a7116b59aeb5ec20a468de22458a24066a9f0f5d71e32f07506e`.
The source GitHub remote was not used for the smoke push. The only test push
went to the disposable framework's local bare remote. The target was not pushed.

## Disposable boundary and preflight

Raw fixture root: `/private/tmp/1pcloop-f7-smoke.RBbAa8`. The equivalent
`/tmp/1pcloop-f7-smoke.RBbAa8` path may appear in macOS tools.

| Object | Local path / branch | Preflight HEAD and remote ref |
| --- | --- | --- |
| Target | `/private/tmp/1pcloop-f7-smoke.RBbAa8/target` / `smoke` | `0e4bcc50b04ba8a2425298481f70d4c61714535d` |
| Target bare remote | `/private/tmp/1pcloop-f7-smoke.RBbAa8/target-remote.git` / `refs/heads/smoke` | `0e4bcc50b04ba8a2425298481f70d4c61714535d` |
| Framework | `/private/tmp/1pcloop-f7-smoke.RBbAa8/framework` / `main` | `af20cc1138e6a1243bd54082d2dda6b820b52fd2` |
| Framework bare remote | `/private/tmp/1pcloop-f7-smoke.RBbAa8/framework-remote.git` / `refs/heads/main` | `af20cc1138e6a1243bd54082d2dda6b820b52fd2` |

Both working trees were clean; both `origin` URLs were the local bare paths
above. The config was
`/private/tmp/1pcloop-f7-smoke.RBbAa8/workload.json`, raw SHA-256
`c5f411cdfe0aa7b14c405b6b234d6dd1a1af32341c9f4d1c99aaed684b4d62b4`,
resolved identity SHA-256
`2a4de57f4f4cc90936f2c5503ce2446c255413412fbfc9a48a73aea597544665`.
The actual CLI was `codex-cli 0.153.4`; both distinct role profiles reported
logged in. No credential or profile state was read or copied.

Config-backed `doctor` passed all eight checks and `preflight` passed.
The run was bounded to one cycle, with a 600-second limit per Agent turn.
The target's single unittest failed before the run because the value was
`PENDING`, as the fixture contract intended.

## Real turns and authoritative verdict

Run ID: `20260918T091536Z-19561`.
Git-ignored raw root:
`/private/tmp/1pcloop-f7-smoke.RBbAa8/framework/1PCloop/.local/runs/20260918T091536Z-19561`.
All three real process receipts reported success and exit code 0:

| Turn | Role/session | Duration | Process SHA-256 |
| --- | --- | ---: | --- |
| `cycle-01/reviewer-instruction` | Reviewer, new persistent | 46.219s | `3c67fac6f1931aad22126483e47e8f083ebac40eee2e88ef0a6ce03d3e32901e` |
| `cycle-01/executor` | Executor, fresh ephemeral | 27.257s | `ba156b4d1cf69473880f8a00b9e25a093b9ed8aa3578593b6c271eaa7f2f787d` |
| `cycle-01/reviewer-review` | Reviewer, explicit resume | 56.695s | `06afc7f708a6f53175aac693bd3c8f15e86ae1f8936960308eb6d8d4581e1289` |

The instruction and review receipts share Reviewer thread
`01a0b3cc-c9e1-7543-9d18-4852c8fe9454`; the review receipt records the
same resume target and `resume_relationship_verified=true`. The Executor used
a separate ephemeral thread. Both Reviewer receipts record read-only target
verification. The role profiles were distinct. No F1 verdict correction occurred;
the checkpoint's correction record is `null`. This run does not test the
correction path by injection.

The final Reviewer verdict bytes are at
`cycle-01/reviewer-review/final.txt` under the raw root, SHA-256
`849869db91641bf174f8200dc17e21e8af451f3174953ff5f7cbafcdccf36ec8`.
Its schema-valid `ACCEPT` bound `S1`, the exact target HEAD, and the
pre-transition Runtime SHA-256. Its two mechanically valid evidence entries
were:

- commit `259046fef6823c0de309a01c1a04dd5c8260f597`, raw
  `git cat-file commit` SHA-256
  `ed628197eca451fdf208ec01955fb26c6f2d5572cd07626c3f360f08baf0327e`;
- file `/private/tmp/1pcloop-f7-smoke.RBbAa8/target/smoke_value.py`,
  SHA-256 `2a9fef061dbccd60b1932ae4e5df01b5ac8466a148d25a9e02c2fb4e208de6bf`.

The target result commit is an ordinary direct descendant of its preflight
HEAD and changes only `smoke_value.py`. The unchanged target test passed
`1/1` after the run. Target branch `smoke` and its worktree were clean.
The target bare remote `refs/heads/smoke` remained exactly
`0e4bcc50b04ba8a2425298481f70d4c61714535d`.

## Machine transition and evidence publication

Disposable workload Runtime:
`/private/tmp/1pcloop-f7-smoke.RBbAa8/framework/1PCloop/workloads/f7_smoke/workload_runtime.md`.
Its SHA-256 changed from
`940da8a9302b007c2cd02495b73c478c39bc4265fd9ac0a689355072d721c88a`
to
`bf3c0624737e1635405687f278c93636268b9e3ef69d5421eef6ec072f5f843a`.
There is exactly one machine transition record, ID
`bea0f37639a523592863d79f832a2a9ce3f03bd101abcdafd49ebc086ba69851`.
It binds the final verdict hash and target HEAD, changes `S1/ACTIVE` to
`S1/COMPLETED`, sets `transition_mode=disabled`, and activates no next step.
The checkpoint records `runtime_transition_applied=true`.

The disposable framework evidence commit
`4bb32caab152a59662f225c204f0f52dcc65e944` has parent
`af20cc1138e6a1243bd54082d2dda6b820b52fd2`. It changes only the
disposable workload Runtime and generated tracked summary, and a normal
non-force push made its local bare remote `refs/heads/main` equal that exact
commit. The generated summary is
`/private/tmp/1pcloop-f7-smoke.RBbAa8/framework/1PCloop/evidence-summaries/20260918T091536Z-19561.md`,
SHA-256 `5df3ac7bde7c1e1d263d19f8ef1311b98179325bbf8603ab8aaf091dbc4aecfd`.
It contains three bounded turn entries.

## Read-only operator and TUI observation

`status` reported `PASS`, observation `AVAILABLE`, run elapsed
`131.264s` active time, and `TERMINAL_SUCCESS`. `inspect` reported
`PASS`, 56 structured events, valid authoritative target evidence, and
passed checkpoint, manifest, observation, summary, framework commit/push,
and target identity checks. `human-gate` reported `NOT_APPLICABLE`,
`NOT_A_HUMAN_GATE`, and `NO_ACTION`. All three agreed on
`RUNTIME_TRANSITION_COMMITTED / APPLIED / PUSHED`.

The real PTY TUI opened, displayed the same terminal state and three separate
outcomes, accepted `r` refresh, and exited with `q` and code 0. It displayed
publication as distinct from logical outcome. Before and after these read-only
commands and TUI, the checkpoint, manifest, control-events, live-status,
generated summary, and disposable Runtime SHA-256 values and all three
repositories' Git states/refs were byte-identical.

Additional raw locators and SHA-256 values for independent review:

| Artifact under the raw root or state root | SHA-256 |
| --- | --- |
| `manifest.json` | `215e34df583196b751750b589f7287619da6e22635537e42de553e687a985987` |
| `control-events.jsonl` | `f9b8478d33b3e4106b8efc449bae7a2890aaf3e1d6ec7475e42413b1ae72e7e3` |
| `live-status.json` | `650dc1297dee51b0977b022f868d5f9b00b631bc34d79505a3ecc7e013051aa5` |
| `framework/1PCloop/.local/state/f7-real-service-smoke/checkpoint.json` | `233205d4dfda201d92dc49c21db44c696f4a1bb26b2f25cd78d09e03f88973ef` |

Raw prompts, peer payloads, full events, stderr, complete receipts, and
checkpoint bytes remain local and are not copied into this tracked summary.
The disposable `/tmp` tree can be removed by the operating system later;
the hashes, refs, result classification, and provenance above are durable.
Independent Reviewer acceptance is still required.
