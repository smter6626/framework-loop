# P4-B deterministic authoritative-context validation

Date: `2026-09-05`

Implementation HEAD: `fe9b48697535107a0d0f1d8c5bb8c4483c616f5d`

Codex CLI: `codex-cli 0.153.4`

## Scenario A — fresh Reviewer bootstrap

The real `reviewer-resume-treatment` run completed all three processes with exit code `0`.

Reviewer Turn 1 created persistent thread:

```text
01a0721d-4a79-7d63-8d9c-b60cae83eb2b
```

Mechanical authoritative-context evidence:

```text
injection_mode = full-bootstrap
injected_files = [static, runtime]
current_git_head = fe9b48697535107a0d0f1d8c5bb8c4483c616f5d

Static
  path = 1PCloop/docs/miniloop_static.md
  sha256 = f2fc9b87a11078c4cb5bf8cef1c9de95d297f2ad1e7e1164db8f096d573818fe
  bytes = 18039
  lines = 534
  prompt_offset = 2839

Runtime
  path = 1PCloop/docs/miniloop_runtime.md
  sha256 = e998c5124c65757f76183fc65a2fc9e0a75cce1e9627ad0ca42b0f2a89403fce
  bytes = 36759
  lines = 776
  prompt_offset = 20949

authoritative_payload_bytes = 56095
prompt_bytes = 57792
source_bytes_verified = true
prompt_bytes_verified = true
```

Independent `dd` slices at the recorded prompt offsets produced the same Static and Runtime SHA-256 values as the source files.

Turn 1 usage:

```text
input_tokens = 29247
cached_input_tokens = 11008
uncached_input_tokens = 18239
output_tokens = 148
reasoning_output_tokens = 90
duration_seconds = 7.331
```

## Scenario B — unchanged Reviewer resume

Reviewer Turn 3 compared session-known and current Static/Runtime hashes. Both pairs matched. The control layer selected `resume-unchanged`, injected no governance document bytes, and resumed the exact Turn 1 thread.

```text
injection_mode = resume-unchanged
injected_files = []
refresh_required = false
refresh_performed = false
authoritative_payload_bytes = 1324
prompt_bytes = 3192

resume_target_thread_id = 01a0721d-4a79-7d63-8d9c-b60cae83eb2b
observed_resume_thread_id = 01a0721d-4a79-7d63-8d9c-b60cae83eb2b
resume_relationship_verified = true
```

Turn 3 usage:

```text
input_tokens = 30300
cached_input_tokens = 28416
uncached_input_tokens = 1884
output_tokens = 154
reasoning_output_tokens = 108
duration_seconds = 6.675
```

Both peer transports remained byte-identical (`preserved_verbatim=true`). The real events contain no Agent-initiated `sed` or `cat` governance read.

## Scenario C — Runtime changed

An independent temporary Git fixture used the integration-test fake Codex process so the Runtime could be changed deterministically after Turn 1 without modifying authoritative repository history.

```text
Turn 1 known Runtime
  sha256 = d43aa2aa1f2fc7d0d473e924a5fa15034b02338c0abe52e5e1e50b04a6a5ebd8
  bytes = 32

Turn 3 current Runtime
  sha256 = cd25feeb9e09b28375f067e6e0f8693a436c8cf10080caa78842ec4d84e70deb
  bytes = 56

injection_mode = runtime-refresh
injected_files = [runtime]
refresh_required = true
refresh_performed = true
source_bytes_verified = true
prompt_bytes_verified = true
resume_relationship_verified = true
```

The Turn 3 prompt contains the complete 56-byte changed Runtime at the recorded offset. The stale 32-byte session-known Runtime hash was not treated as current.

This fixture validates deterministic control-plane behavior, not model semantics or real-service token cost. Its complete run artifacts, final fixture governance bytes, fake executable, and invocation log are preserved under `scenario-c-runtime-change-fixture/`.

## Cost comparison boundary

The accepted P4-A treatment measured Reviewer T1/T3 and aggregate values as follows:

```text
P4-A Reviewer T1: input 60526, cached 41216, uncached 19310, duration 23.825s
P4-A Reviewer T3: input 26014, cached 24320, uncached 1694, duration 10.449s
P4-A aggregate:   input 102043, cached 77056, uncached 24987, duration 43.362s
```

The P4-B validation measured:

```text
P4-B Reviewer T1: input 29247, cached 11008, uncached 18239, duration 7.331s
P4-B Reviewer T3: input 30300, cached 28416, uncached 1884, duration 6.675s
P4-B aggregate:   input 74389, cached 39424, uncached 34965, duration 19.981s
```

P4-B Turn 3 did not repeat full governance bytes, but persistent history still contributes to reported total input. Compared with the single accepted P4-A treatment, P4-B Turn 3 had `+190` uncached input tokens and `-3.774s` duration. Aggregate uncached input was `+9978`, dominated by this run's Executor Turn 2 reporting zero cached input (`14842` uncached), unlike P4-A. These are single-run observations with different governance/prompt bytes, stochastic outputs, cache state, and service timing; they are not a benchmark-quality causal estimate.

## Evidence locators

- Real run: `manifest.json`, `transcript.md`, and `turn-*/`.
- Changed-Runtime fixture: `scenario-c-runtime-change-fixture/run/manifest.json`, its `turn-*/`, `final-governance/`, `runtime-change-codex`, and `runtime-change-codex.calls`.
- Automated coverage: `1PCloop/tests/test_run_text_loop.py`.
