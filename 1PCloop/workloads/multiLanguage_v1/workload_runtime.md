# live_subtitle_generator — multiLanguage_v1 Workload Runtime

## Status

`COMPLETED — HUMAN ACCEPTED / TARGET INTEGRATION PENDING`

Target repository:

`/Users/smterpro/Workspace/whisper/live_subtitle_generator`

Target branch:

`multiLanguage_v1`

Current target HEAD:

`b9f61b39384001eae07c94d114ae66dcba0873cb`

## Current Human State

The first successful real medium-scale P5 workload run completed, reached the Human
gate, and has now been accepted by the Human Owner for this workload phase. Reviewer
and Human evidence do not require run #3.

Reviewer / Executor binding for this workload:

```text
Reviewer = /Users/smterpro/.codex-A
Reviewer model = gpt-5.6-sol
Reviewer reasoning effort = xhigh

Executor = /Users/smterpro/.codex-B
Executor model = gpt-5.6-terra
Executor reasoning effort = high
```

Target languages:

```text
Japanese
French
Spanish
German
Korean
```

Reviewer accepted the implementation/documentation slices produced by run #2. Human
Owner subsequently completed a bounded manual transcription smoke, accepted the
remaining explicitly recorded coverage limits, and closed this workload phase.

Target branch publication and merge remain separate integration actions; neither is
implied by workload acceptance.

Repository Git state is authoritative for implementation progress.
P5 run evidence is authoritative for mechanical Reviewer/Executor transport and
process evidence.

Do not treat the semantic Reviewer observations below as Python-derived control
metadata. They were human-reviewed from opaque Agent final messages.

## Current Blockers / Known Limits

No control-plane or workload correctness blocker is currently identified.

Known non-blocking items:

- the baseline project-local Python environment assertion remains the same pre-existing
  failure and is outside this workload scope;
- `TOKEN_RE` remains ASCII-centric for pure CJK/Korean overlap in transcript dedup;
  Reviewer classified this as non-blocking for this workload boundary;
- manual live transcription was completed for Japanese and French, but Spanish,
  German, Korean and Auto Detect were not manually exercised because of time limits;
- `.en` rejection and UI-locale preservation were not reported as part of the Human
  manual smoke; their current evidence remains automated tests and Reviewer inspection.

## Remaining Human-controlled Integration Actions

The workload Human acceptance gate is resolved. No run #3 is required by current
Reviewer or Human evidence.

The workflow may not automatically:

- merge `multiLanguage_v1` to `main`;
- push target changes unless separately authorized;
- expand the workload beyond the Static contract;
- modify workload or framework governance as part of Executor work.

Target push and merge remain Human-controlled repository integration decisions.

## Baseline Validation

Baseline target state:

- branch: `multiLanguage_v1`
- HEAD: `b5188ccc6aef591398fd8d31e162a29390b120e4`
- working tree: clean
- Python: `3.12.14`
- environment restored successfully with `uv sync --frozen`

Baseline regression:

- 100 tests executed
- 99 passed
- 1 pre-existing environment-contract failure

Pre-existing failure:

`test_python_environment.PythonEnvironmentTests.test_environment_is_project_local_and_uses_managed_python`

Observed reason:

The exact Python 3.12.14 interpreter installed by uv is located under the
user-level uv managed-Python directory:

`/Users/smterpro/.local/share/uv/python/cpython-3.12.14-macos-aarch64-none/bin/python3.12`

The repository test expects the base Python to be project-local/project-managed.

This failure existed before any P5 Executor mutation and must not be attributed to
the multiLanguage_v1 workload unless later changes materially alter it.

All other baseline tests passed.

Human Owner has not authorized unrelated repair of this environment-contract issue
as part of multiLanguage_v1.

## 2026-09-06 — First real mutation attempt failed closed and was recovered

Run:

`20260906T083312Z-48975`

Observed control-plane failure:

- Reviewer completed the first bounded instruction;
- Executor modified source/tests and ran validation;
- the then-active Codex `workspace-write` sandbox blocked `.git/index.lock`, so the
  Executor could not create the required Git commit;
- target HEAD remained at baseline while the working tree became dirty;
- P5 correctly failed closed instead of accepting the Executor's natural-language
  completion report;
- Human Owner saved recovery evidence externally and restored the target to clean
  baseline `b5188ccc6aef591398fd8d31e162a29390b120e4` before retry.

This failed attempt produced no accepted implementation commit for this workload.
The control-plane repair and disposable real-commit smoke are recorded in framework
Runtime; they are not redefined here.

## 2026-09-06 — Real mutation run #2 reached Human Gate

Status: `REVIEWER ACCEPTED — HUMAN MERGE/FINAL PRODUCT ACCEPTANCE PENDING`

Run:

`20260906T102252Z-52187`

Target:

- repository: `live_subtitle_generator`
- branch: `multiLanguage_v1`
- baseline HEAD: `b5188ccc6aef591398fd8d31e162a29390b120e4`
- final HEAD: `b9f61b39384001eae07c94d114ae66dcba0873cb`
- final working tree: clean

Mechanical orchestrator result:

- status: `STOPPED_FOR_HUMAN_REVIEW`
- reason: `target_head_unchanged`
- cycles: `3`
- turns: `7`
- successful turns: `7 / 7`
- Reviewer thread: `01a0763e-0f68-76b2-b1d7-e4be01989dbc`

Target history created by the run:

1. `0d3b9e6c0f57dbd87a214717c07e4de9a4025d75` — `Add multilingual language selection validation`
2. `b9f61b39384001eae07c94d114ae66dcba0873cb` — `docs: describe multilingual original language choices`

Cycle progression:

- Cycle 1: `b5188ccc... -> 0d3b9e6c...`, `head_changed=true`
- Cycle 2: `0d3b9e6c... -> b9f61b39...`, `head_changed=true`
- Cycle 3: `b9f61b39... -> b9f61b39...`, `head_changed=false`
- the unchanged-HEAD Executor payload still reached Reviewer review before the
  orchestrator stopped at the Human gate

Reviewer semantic observation (human-reviewed from opaque final messages; not parsed by Python):

- Reviewer rejection count: `0`
- Reviewer repair-request count: `0`
- Cycle 1 review accepted the implementation slice and issued one bounded documentation task
- Cycle 2 review judged the workload ready for Human Owner review
- Cycle 3 review reaffirmed that no further Executor mutation was required

Product evidence:

- canonical original-language choices: `en`, `zh`, `ja`, `fr`, `es`, `de`, `ko`, `auto`
- legacy automatic/mixed aliases normalize to canonical Auto Detect behavior
- application UI locales remain English and Chinese
- bilingual original-language labels are present
- session/config evidence carries canonical language label/code
- whisper.cpp `-l` propagation is covered, including `auto`
- `.en` models reject every non-English choice including Auto Detect, with no silent fallback/model switch
- both READMEs document the eight choices/codes, legacy Auto Detect aliases, UI-locale distinction, and `.en` restriction
- `TOKEN_RE` remains ASCII-centric for pure CJK/Korean dedup overlap; Reviewer classified this as a known non-blocking limitation under the workload boundary

Regression evidence:

- prescribed full suite: `106` tests
- result: `105 passed / 1 failed`
- sole failure remains the pre-existing project-local Python-path assertion recorded in Baseline Validation
- no workload-caused regression was identified

Usage/cache observation for this single real workload run:

```text
Turn  Role/Session                 Input    Cached   Uncached  Cache-hit  Output  Reasoning  Duration
T1    Reviewer / new-persistent    466366   394752   71614     0.846442   4363    2910       108.071s
T2    Executor / fresh-ephemeral   965834   895232   70602     0.926900   10292   3917       237.905s
T3    Reviewer / resume            363738   348288   15450     0.957524   3217    2206       76.843s
T4    Executor / fresh-ephemeral   329448   275200   54248     0.835337   4010    1050       101.975s
T5    Reviewer / resume            418545   404480   14065     0.966395   1696    622        50.208s
T6    Executor / fresh-ephemeral   70306    62464    7842      0.888459   623     143        25.924s
T7    Reviewer / resume            338084   333696   4388      0.987021   825     288        26.150s
```

By role:

- Reviewer — 4 turns: input `1586733`, cached `1481216`, uncached `105517`, aggregate cache hit `0.933500`, output `10101`, reasoning `6026`, duration `261.272s`
- Executor — 3 turns: input `1365588`, cached `1232896`, uncached `132692`, aggregate cache hit `0.902832`, output `14925`, reasoning `5110`, duration `365.804s`

Total:

- duration: `627.076s`
- input: `2952321`
- cached input: `2714112`
- uncached input: `238209`
- aggregate cache hit ratio: `0.919315`
- output: `25026`
- reasoning output: `11136`
- cache-write input tokens: `0`

Interpretation boundary:

These token/cache values are observations from one real workload run, not a controlled benchmark or causal performance result. Reviewer persistence/resume correlates with very high cache-hit ratios in later Reviewer turns, but this run alone does not isolate the effect of session persistence from prompt shape, repository state, service-side cache state, or task complexity.

## 2026-09-06 — Human Gate manual smoke and phase acceptance

Status: `HUMAN ACCEPTED — WORKLOAD PHASE CLOSED`

Human-observed evidence:

- Japanese live audio was successfully transcribed through Whisper;
- French live audio was successfully transcribed through Whisper;
- observed Japanese/French transcription quality was subjectively comparable to the
  existing Chinese/English experience;
- the earlier source-run blocker, `whisper-cli not found`, was operationally closed
  before these successful transcriptions.

Manual-coverage boundary:

- Spanish, German, Korean and Auto Detect were not manually exercised because of
  available testing time;
- no controlled multilingual corpus was used, so this is not WER/CER evidence;
- `.en` rejection behavior and UI-locale/code preservation were not reported as
  manually exercised in this Human Gate;
- those unexercised paths remain supported by deterministic tests, common canonical
  mapping/propagation code and independent Reviewer inspection, but are not described
  as Human-tested.

Human verdict:

Human Owner accepts the workload with those limits explicitly recorded and closes
the `multiLanguage_v1` implementation/validation phase. No run #3 or additional
language smoke is required for this phase unless later evidence invalidates the
current conclusion.

This verdict does not push the target branch and does not merge it into `main`.
