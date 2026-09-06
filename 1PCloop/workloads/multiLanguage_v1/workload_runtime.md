# live_subtitle_generator — multiLanguage_v1 Workload Runtime

## Status

`READY FOR FIRST P5 RUN`

Target repository:

`/Users/smterpro/Workspace/whisper/live_subtitle_generator`

Target branch:

`multiLanguage_v1`

## Current Human State

Human Owner has authorized preparation and execution of the first real P5
medium-scale workload after successful preflight.

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

No implementation work has yet been accepted for this workload.

Repository Git state is authoritative for implementation progress.
P5 run evidence is authoritative for mechanical Reviewer/Executor transport and
process evidence.

Do not duplicate repository implementation history into this Runtime.

## Current Blockers

None known before preflight.

## Human Gates

The loop may mutate `multiLanguage_v1`.

It may not:

- merge to `main`;
- push unless separately authorized;
- expand the workload beyond the Static contract;
- modify workload or framework governance.

Final workload acceptance remains with the Human Owner.

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
