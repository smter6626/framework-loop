# Miniloop implementation skeleton

This first implementation is a runnable deterministic transport/control skeleton for the authoritative contract in `docs/miniloop_static.md` and current state in `docs/miniloop_runtime.md`. It does **not** claim Step 1 or the full Miniloop acceptance criteria are complete.

## What is implemented

- one blocking, `stream=false` Ollama client guarded by a serial inference lock;
- one configured model ID shared by isolated `reviewer_messages` and `executor_messages` histories;
- deterministic envelopes whose natural-language `payload` is delivered byte-for-byte as the peer's user message;
- persistent `executor|human` receiver state, read at startup and after every Reviewer inference;
- runtime-enforced native tool calls for control-plane operations, separate from free text;
- Reviewer-only receiver setter, restricted Runtime updater, and read-only verification shell;
- Executor-only full `/bin/sh -lc` tool inside a Linux container;
- a single explicit read/write `/workspace` host mount; governance and control paths are rejected if they fall inside that mount;
- append-only JSONL event logs with run/event/turn/session metadata and full routed payload evidence;
- mechanical Runtime invariants and unit/integration tests.

Python never searches output for `ACCEPT`, `REJECT`, evidence fields, blockers, JSON, XML, or markers. Native tool-call arguments are validated as deterministic control data. A normal Agent text response is opaque transport data.

## Layout

```text
config/miniloop.json       local model and path configuration
control/receiver           persistent two-value receiver state
roles/                     isolated Reviewer/Executor system instructions
src/miniloop/              implementation
tests/                     stdlib unittest suite
scripts/                   deterministic demo and bounded Ollama smoke probe
workspace/                 only writable host mount for Executor
logs/                      live JSONL run logs (gitignored)
evidence/                  generated check evidence
```

`docs/miniloop_static.md`, `docs/miniloop_runtime.md`, and `control/receiver` are never mounted into the Executor container. The Reviewer receives Static/Runtime in its private initial context; the Executor receives only the current peer payload plus its own system instruction/history.

## Run checks

From the repository root, no package installation is required:

```sh
PYTHONPATH=miniloop/src python3 -m unittest discover -s miniloop/tests -v
PYTHONPATH=miniloop/src python3 -m miniloop --config miniloop/config/miniloop.json show-receiver
PYTHONPATH=miniloop/src python3 -m miniloop --config miniloop/config/miniloop.json show-sandbox-command 'pwd && touch proof.txt'
PYTHONPATH=miniloop/src python3 miniloop/scripts/self_check.py \
  --output miniloop/evidence/self-check.json
```

Run the deterministic orchestrator demo without Ollama or Docker execution:

```sh
PYTHONPATH=miniloop/src python3 miniloop/scripts/run_scripted_demo.py \
  --output miniloop/evidence/scripted-demo.jsonl
```

This demo exercises Reviewer → Executor → Reviewer → repair → Executor → Reviewer, then stops only after a native `set_receiver(human)` call. It operates on temporary Runtime/receiver copies and does not target the authoritative Runtime.

Run one bounded live Ollama/native-tool smoke request:

```sh
PYTHONPATH=miniloop/src python3 miniloop/scripts/ollama_smoke.py \
  --disable-thinking \
  --output miniloop/evidence/ollama-smoke-no-thinking.json
```

## Live loop

Prerequisites are an already-running local Ollama service, the configured local model, a running Docker daemon, a locally available configured container image, and a Human-selected `docker_network_mode`. Miniloop does not install Docker, start Docker Desktop, change global settings, or implicitly pull an image (`docker run` uses `--pull=never`). The supplied `sandbox/Dockerfile` is the reproducible image skeleton with Python, Git, and basic build tools; building it is a separate Human-authorized action:

```sh
docker build -t miniloop-executor:0.1 miniloop/sandbox
```

With `control/receiver` set by the Human to `executor`:

```sh
PYTHONPATH=miniloop/src python3 -m miniloop \
  --config miniloop/config/miniloop.json \
  run --kickoff 'Review the authoritative Active Step and issue one bounded instruction.'
```

The loop intentionally has no natural-language completion parser and no repair-count/semantic stop heuristic. It stops automatically only when the receiver control file reads `human` after a Reviewer inference/tool phase, or when the process is interrupted. Full Human-gate resume semantics remain out of scope.

## Current sandbox caveat

The launcher constructs a Linux Docker invocation with a read-only container root, a read/write Executor workspace mount (read-only for Reviewer verification), dropped capabilities, and no governance/control mount. Actual mount isolation must still be verified against a running local daemon and locally built image. The current contract does not define an Executor network/egress policy. `docker_network_mode` therefore remains `null`, and `run()` refuses execution before Docker until the Human selects a policy; command preview remains available for mount-boundary inspection.
