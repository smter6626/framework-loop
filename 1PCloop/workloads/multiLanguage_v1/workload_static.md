# live_subtitle_generator — multiLanguage_v1 Workload Static

## Status

`ACTIVE WORKLOAD CONTRACT`

This document defines the stable contract for the first medium-scale real workload
executed through the accepted 1PCloop P5 control plane.

It is authoritative for workload scope, hard constraints, and acceptance criteria.
The target Git repository is authoritative for implementation state.
The workload Runtime contains only Human-owned current execution state.

---

## Target

Repository:

`smter6626/live_subtitle_generator`

Target branch:

`multiLanguage_v1`

Branch basis:

`main`

Do not merge this workload branch into `main` automatically.

---

## Primary Objective

Generalize ClassroomTranscriber from an English/Chinese-specific original-language
selection system into a multilingual original-language system with explicit model
compatibility enforcement, while preserving the existing Chinese/English UI locales
and backward compatibility.

Existing original-language support must remain available:

- English (`en`)
- Chinese (`zh`)

Add first-class original-language support for:

- Japanese (`ja`)
- French (`fr`)
- Spanish (`es`)
- German (`de`)
- Korean (`ko`)

Also preserve the existing automatic/mixed-language path as the canonical UI option:

- Auto Detect (`auto`)

The application must therefore expose the following canonical original-language
choices after this workload:

- English
- Chinese
- Japanese
- French
- Spanish
- German
- Korean
- Auto Detect

---

## Canonical Language Representation

Use stable machine-readable Whisper language identifiers internally:

```text
English     = en
Chinese     = zh
Japanese    = ja
French      = fr
Spanish     = es
German      = de
Korean      = ko
Auto Detect = auto
```

There should be one clear authoritative normalization/conversion path rather than
multiple incompatible language representations spread through the application.

Where an external dependency requires another representation, keep the conversion
explicit and mechanically testable.

---

## Backward Compatibility

The existing mixed/automatic-language selection must remain backward compatible.

Canonical display:

`Auto Detect`

Canonical internal value:

`auto`

Existing persisted or legacy aliases must continue to normalize correctly, including
at least:

```text
Mixed Chinese/English
中英混合
mixed
auto
```

Do not silently invalidate existing saved configuration merely because the canonical
display label changes.

---

## UI Locale Boundary

The application's own UI localization remains limited to:

- English UI
- Chinese UI

Do not add Japanese, French, Spanish, German, or Korean as whole-application UI
locales in this workload.

Original-language option labels must, however, be appropriately localized inside the
existing two UI locales.

At minimum, the Chinese UI should display the added language choices using Chinese
labels:

```text
Japanese = 日语
French   = 法语
Spanish  = 西班牙语
German   = 德语
Korean   = 韩语
```

The English UI should display their English language names.

This distinction is required:

```text
original-language choices != application UI locales
```

---

## Whisper / Backend Propagation

The selected canonical original-language code must propagate to the actual
whisper.cpp/backend invocation.

For explicit languages, the backend must mechanically receive the correct language
argument, including:

```text
-l en
-l zh
-l ja
-l fr
-l es
-l de
-l ko
```

The Auto Detect path must preserve the repository's intended automatic-language
behavior rather than being silently converted into one explicit language.

Reviewer must inspect the actual backend command/config propagation rather than accept
UI-only evidence.

---

## `.en` Model Compatibility

English-only Whisper models, including model names such as:

```text
medium.en
small.en
base.en
```

must only permit English (`en`) as the original language.

The application must reject incompatible combinations such as:

```text
.en model + Chinese
.en model + Japanese
.en model + French
.en model + Spanish
.en model + German
.en model + Korean
.en model + Auto Detect
```

The rejection must be clear to the user.

Do not silently fall back to English, silently switch models, or silently reinterpret
the selected language.

Multilingual Whisper models should support all canonical language choices listed by
this workload.

---

## Session / Configuration Evidence

Where the application records session/transcription configuration, the resulting
state must remain semantically accurate.

Relevant fields should correctly represent both the human-facing original-language
label and the machine-facing Whisper language code.

In particular, existing concepts such as:

```text
original_language_label
whisper_language_code
```

must remain accurate for the newly added languages and Auto Detect path if those
fields exist in the current repository.

The repository is authoritative for the exact implementation location and schema;
Agents must inspect it rather than inventing parallel configuration structures.

---

## Transcript / Dedup Audit Boundary

Reviewer must inspect the existing transcript deduplication/tokenization path for
obvious blocker risk with the expanded language set.

In particular, if the repository still contains an English-centric tokenizer or
regular expression such as `TOKEN_RE`, Reviewer should determine whether it blocks
correct Japanese/Korean/Chinese behavior for this workload.

Do not automatically rewrite transcript dedup/tokenization merely because it appears
English-centric.

If evidence shows it blocks the required multilingual original-language behavior,
Reviewer may issue a bounded repair task.

If it is an existing limitation that does not block language selection, backend
propagation, model compatibility, or the required regression behavior, record it as a
follow-up limitation rather than expanding this workload.

---

## Documentation

Update the repository documentation affected by the feature.

At minimum inspect and update, where present:

- `README.md`
- `README.zh-CN.md`

Documentation should describe the supported original-language choices, Auto Detect
behavior, and `.en` model compatibility constraints accurately.

Do not turn this workload into a broad documentation rewrite.

---

## Test / Validation Requirements

Relevant deterministic tests should cover, where practical:

- canonical language normalization;
- legacy alias normalization;
- language-code mapping;
- English and Chinese preservation;
- Japanese mapping;
- French mapping;
- Spanish mapping;
- German mapping;
- Korean mapping;
- Auto Detect normalization;
- English/Chinese UI labels and added-language option labels;
- `.en` model compatibility rejection;
- multilingual-model compatibility;
- backend/whisper.cpp command propagation;
- session/config language label and code evidence;
- existing behavior affected by the changes.

Run the repository's full existing regression suite before final workload readiness:

```text
.venv/bin/python -m unittest discover -s testCodes -p 'test_*.py' -v
```

If the baseline suite already contains an unrelated failure before mutation, preserve
that fact as baseline evidence rather than silently attributing it to this workload.

---

## ASR Accuracy Boundary

Do not make multilingual WER/CER or subjective recognition quality a hard acceptance
criterion for this first medium-scale workload.

The repository does not currently provide a controlled multilingual audio corpus for
a valid comparative accuracy benchmark.

For this workload, deterministic language normalization, compatibility enforcement,
and correct backend language-code propagation are sufficient mechanical evidence.

Do not fabricate an ASR quality benchmark.

---

## Scope Flexibility

Reviewer and Executor may choose implementation details necessary to satisfy this
contract, including small coherent changes to:

- language configuration/normalization;
- UI selectors and localized option labels;
- validation;
- settings persistence;
- model compatibility checks;
- backend command construction;
- session configuration;
- tests;
- directly affected documentation;
- small refactors needed to remove hard-coded English/Chinese assumptions.

The Static intentionally does not prescribe exact classes, functions, modules, or UI
widget implementations.

Agents must inspect the target repository and prefer the smallest coherent design.

---

## Explicit Non-Goals

Do not expand this workload into:

- subtitle translation;
- translation between source languages;
- new whole-application UI locales beyond existing Chinese/English;
- replacing whisper.cpp or the current transcription engine;
- adding every language supported by Whisper;
- unrelated UI redesign;
- unrelated large refactors;
- packaging/release publication;
- GitHub release creation;
- cloud deployment;
- unrelated performance optimization;
- automatic merge to `main`;
- ASR accuracy benchmarking without a controlled corpus.

Supporting additional languages internally as a natural consequence of a clean
generic mapping is acceptable only if it does not broaden the user-facing acceptance
scope or create extra unreviewed behavior.

---

## Reviewer Role

Reviewer:

```text
CODEX_HOME = /Users/smterpro/.codex-A
intended model = gpt-5.6-sol
intended reasoning effort = xhigh
```

Reviewer responsibilities:

- independently inspect the actual target repository;
- break the workload into one bounded implementation task at a time;
- inspect actual commits, diffs, tests, command construction, and evidence;
- detect regressions, incomplete propagation, stale language assumptions, missing
  compatibility enforcement, and weak tests;
- request bounded repair where evidence is insufficient;
- audit transcript/dedup behavior only to the extent defined above;
- avoid unnecessary architectural expansion;
- never modify the target repository.

Reviewer natural-language decisions remain opaque peer communication.
Python does not interpret Reviewer semantic verdict words.

---

## Executor Role

Executor:

```text
CODEX_HOME = /Users/smterpro/.codex-B
intended model = gpt-5.6-terra
intended reasoning effort = high
```

Executor responsibilities:

- execute only the current bounded Reviewer instruction;
- inspect existing code before modifying it;
- make coherent target-repository changes;
- add/update relevant tests;
- run appropriate validation;
- create an ordinary Git commit for meaningful mutations;
- leave the target branch clean;
- report evidence and limitations accurately;
- never self-accept the whole workload.

---

## Git / Mutation Rules

Target mutation is restricted to:

```text
repository = live_subtitle_generator
branch = multiLanguage_v1
```

Agents must not:

- push;
- merge;
- switch branch;
- rewrite history;
- reset;
- clean;
- stash;
- modify framework governance;
- modify workload governance.

Each meaningful Executor mutation must advance the target branch through ordinary
descendant commits.

---

## Acceptance Criteria

The workload is ready for Human review only when Reviewer has independently inspected
the repository and there is evidence that all of the following hold:

A. Canonical original-language choices include English, Chinese, Japanese, French,
Spanish, German, Korean, and Auto Detect with correct canonical Whisper codes.

B. Legacy automatic/mixed-language aliases normalize backward-compatibly to `auto`.

C. Existing English/Chinese UI locales remain the only application UI locales, while
the original-language choices are correctly labeled in both existing locales.

D. The backend receives the correct explicit whisper.cpp `-l` code for every explicit
supported language, and Auto Detect preserves the intended automatic path.

E. `.en` Whisper models permit only English and clearly reject every non-English or
Auto Detect selection without silent fallback.

F. Session/config evidence accurately records the selected original-language label and
Whisper language code where those concepts exist.

G. Automated/deterministic validation covers normalization, aliases, mapping, UI
labels/options, model compatibility, backend command propagation, Auto Detect, and
affected existing behavior where practical.

H. The full existing regression suite has been run and its result is reported.

I. README documentation affected by the feature is accurate in both English and
Chinese where the corresponding files exist.

J. Reviewer has audited the transcript dedup/tokenization path for blocker risk and
has either verified no blocking issue or explicitly reported a bounded limitation.

K. Target branch is clean, changes are ordinary descendant commits, and unrelated
redesign has not been introduced.

L. Known limitations are explicitly reported.

Reviewer readiness is not automatic final acceptance or merge authorization.
Final workload acceptance and any merge remain Human Owner decisions.

---

## Evidence Principle

Repository state is authoritative for implementation.

Preferred evidence includes:

- Git commits and diffs;
- automated tests;
- deterministic normalization/compatibility checks;
- actual backend command construction;
- session/config evidence;
- build/startup checks where practical.

Executor prose alone is not sufficient evidence.

---

## Governance Boundary

This Static is read-only during the loop.

Changes to this contract require Human Owner authorization.

The P5 orchestrator may detect Static changes and invalidate/roll over Reviewer
working context according to the accepted freshness policy.

Do not modify framework Static/Runtime, workload governance, or historical snapshots
as part of target implementation.
