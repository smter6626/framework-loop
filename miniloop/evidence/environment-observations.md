# Step 1 environment observations — 2026-08-20

These are implementation-pass observations, not Miniloop acceptance.

## Host and Python

- Host command: `uname -a`
- Observed OS/kernel: Darwin 27.0.0, arm64 (`RELEASE_ARM64_T6041`)
- Python: `Python 3.9.6` at `/usr/bin/python3`

## Ollama

- `ollama --version`: `0.32.5`
- `qwen35b-64k:latest`: 23 GB, digest prefix `8eefd9471555`, Q4_K_M, advertised `tools` and `thinking` capabilities.
- `ollama show qwen35b-64k:latest --parameters`: `num_ctx 65536`.
- A real blocking wrapper request returned normally from the same requested model. With default thinking and an intentionally small `num_predict=128`, it ended with `done_reason=length` before producing content/tool calls (`ollama-smoke.json`). With thinking explicitly disabled for the bounded smoke, it ended with `done_reason=stop` and returned native tool call `set_receiver({"receiver":"human"})` (`ollama-smoke-no-thinking.json`). Neither returned tool call was executed against real control state.

## Docker / Linux sandbox blocker

Observed evidence:

- `docker --version`: Docker 29.6.1, build `8900f1d`.
- Active context: `desktop-linux` at `unix:///Users/smterpro/.docker/run/docker.sock`.
- `docker desktop status`: `Could not retrieve status. Is Docker Desktop running?`
- The configured socket does not exist.
- `docker info` and `docker image ls` fail before daemon communication.

Exact problem:

The Docker client is installed, but no reachable Docker Desktop daemon/socket is running. Therefore the generated Linux image cannot be built and the explicit bind-mount behavior cannot be executed/verified in this pass.

Why it matters:

Command construction tests prove which argv/mount the launcher requests; they cannot prove the actual VM/container filesystem view or writable-boundary enforcement. A real Executor shell run must not be claimed yet.

Options:

1. Human starts the existing Docker Desktop installation, authorizes the local `miniloop-executor:0.1` image build, and reruns the mount-isolation integration checks.
2. Human selects a different already-approved Linux VM/container runtime and the launcher abstraction is adapted after evidence collection.

Recommended option:

Option 1 is the smallest continuation because the repository already contains a Docker launcher and image skeleton, but starting/changing Docker Desktop remains a Human action.

What continued meanwhile:

Host-side unit/integration tests, deterministic scripted routing, Runtime invariant tests, mount argv validation, and real local Ollama blocking/native-tool smoke evidence.

## Network-policy uncertainty

Observed evidence:

Static/Runtime lock the filesystem mount boundary and complete Executor shell, but do not specify Docker network/egress behavior.

Uncertainty / blocker:

Choosing `none`, Docker bridge, or another network creates a security/capability policy beyond the locked filesystem contract.

Options:

1. `docker_network_mode=none` for an offline bounded demo.
2. Explicitly authorized Docker network/egress for tasks that need dependency access.

Recommended option:

Use `none` for the first bounded generic demo if its dependencies are prebuilt into the image. Decide broader egress separately when a concrete task needs it.

What continued without the decision:

The launcher and command preview are implemented, but configuration leaves `docker_network_mode` as `null`; `run()` mechanically refuses actual shell execution until the Human selects a policy.

## Authoritative-document integrity

- `miniloop_static.md` SHA-256: `f395c614ad89840d8d9aab9cb2887bf985e1a186d4e6849aaa63e425095ef3a8`
- `miniloop_runtime.md` SHA-256: `82d16282423199a060d4df18b830947857c0b0d33b2b09f9955097404290587f`
- `git diff -- miniloop/docs/miniloop_static.md miniloop/docs/miniloop_runtime.md`: no output.
