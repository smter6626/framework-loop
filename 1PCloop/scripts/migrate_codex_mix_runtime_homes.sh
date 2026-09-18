#!/bin/bash
set -euo pipefail

# Cold-copy the historical A/B homes into dedicated 1PCloop role runtimes.
# Default mode is read-only. Actual migration requires an explicit --execute.

umask 077

SCRIPT_DIR="$(cd -- "$(dirname -- "$0")" && pwd -P)"
MIGRATION_HELPER="$SCRIPT_DIR/codex_runtime_migration.py"

MODE="${1:---check-only}"
if [[ "$MODE" != "--check-only" && "$MODE" != "--execute" ]]; then
  echo "usage: $0 [--check-only|--execute]" >&2
  exit 64
fi

USER_HOME="${HOME:?HOME must be set}"
CANONICAL_HOME="$USER_HOME/.codex-mix"
MIX_ROOT="$CANONICAL_HOME/.mix"
RUNTIME_ROOT="$MIX_ROOT/runtimes"
REVIEWER_SOURCE="$USER_HOME/.codex-B"
EXECUTOR_SOURCE="$USER_HOME/.codex-A"
REVIEWER_TARGET="$RUNTIME_ROOT/1pcloop-reviewer"
EXECUTOR_TARGET="$RUNTIME_ROOT/1pcloop-executor"
ROUTE="$USER_HOME/.codex"

fail() {
  echo "MIGRATION REFUSED: $*" >&2
  exit 1
}

for command in python3 ps awk lsof ditto cmp dirname find mktemp mkdir mv pwd stat sed rm rmdir wc tr; do
  command -v "$command" >/dev/null 2>&1 || fail "required command is unavailable: $command"
done
[[ -f "$MIGRATION_HELPER" && ! -L "$MIGRATION_HELPER" ]] \
  || fail "migration safety helper is missing or aliased"

[[ -d "$CANONICAL_HOME" && ! -L "$CANONICAL_HOME" ]] \
  || fail "canonical ~/.codex-mix directory is missing or aliased"
[[ -d "$MIX_ROOT" && ! -L "$MIX_ROOT" ]] \
  || fail "canonical ~/.codex-mix/.mix directory is missing or aliased"
[[ -d "$MIX_ROOT/accounts" ]] || fail "Codex Mix credential vault is missing"
for account in A B C D; do
  [[ -f "$MIX_ROOT/accounts/$account/auth.json" ]] \
    || fail "credential vault entry is missing for account $account"
done
[[ -f "$CANONICAL_HOME/auth.json" ]] || fail "projected canonical credential is missing"
[[ -L "$ROUTE" ]] || fail "~/.codex is not the expected symlink route"

resolved_route="$(python3 - "$ROUTE" <<'PY'
import sys
from pathlib import Path
print(Path(sys.argv[1]).resolve())
PY
)"
[[ "$resolved_route" == "$CANONICAL_HOME" ]] \
  || fail "~/.codex does not resolve to canonical ~/.codex-mix"

for source in "$REVIEWER_SOURCE" "$EXECUTOR_SOURCE"; do
  [[ -d "$source" && ! -L "$source" ]] || fail "historical source is missing or aliased: $source"
  [[ -f "$source/auth.json" ]] || fail "source auth.json is missing: $source"
  [[ -f "$source/config.toml" ]] || fail "source config.toml is missing: $source"
done

for target in "$REVIEWER_TARGET" "$EXECUTOR_TARGET"; do
  [[ ! -e "$target" && ! -L "$target" ]] || fail "target already exists: $target"
done
[[ ! -e "$RUNTIME_ROOT" && ! -L "$RUNTIME_ROOT" ]] \
  || fail "dedicated runtime root must be absent for atomic publication"

# Process-name checks are intentionally broad. False positives require the
# operator to close the process or inspect it manually; the script never guesses.
active_processes="$(
  ps -axo pid=,ppid=,command= | awk -v self="$$" -v parent="$PPID" '
    $1 != self && $1 != parent &&
    tolower($0) !~ /migrate_codex_mix_runtime_homes\.sh/ &&
    tolower($0) !~ /chatgpt for chrome/ &&
    tolower($0) !~ /chatgpthelper/ &&
    tolower($0) ~ /(chatgpt|codex|onepcloop|run_mutation_loop\.py)/ { print }
  '
)"
[[ -z "$active_processes" ]] || {
  echo "$active_processes" >&2
  fail "ChatGPT, Codex, or 1PCloop appears to be running"
}

check_no_open_files() {
  local root="$1"
  local output
  output="$(mktemp "${TMPDIR:-/tmp}/1pcloop-lsof.XXXXXX")"
  if lsof -nP +D "$root" >"$output" 2>&1; then
    sed -n '1,20p' "$output" >&2
    rm -f "$output"
    fail "open files exist under $root"
  else
    local status=$?
    if [[ $status -ne 1 ]]; then
      sed -n '1,20p' "$output" >&2
      rm -f "$output"
      fail "unable to prove that $root has no open files"
    fi
  fi
  rm -f "$output"
}

check_no_open_files "$CANONICAL_HOME"
check_no_open_files "$REVIEWER_SOURCE"
check_no_open_files "$EXECUTOR_SOURCE"

python3 "$MIGRATION_HELPER" validate-source \
  --source-a "$EXECUTOR_SOURCE" \
  --source-b "$REVIEWER_SOURCE" \
  --vault-a "$MIX_ROOT/accounts/A/auth.json" \
  --vault-b "$MIX_ROOT/accounts/B/auth.json" \
  --reviewer-home "$REVIEWER_TARGET" \
  --executor-home "$EXECUTOR_TARGET"

echo "Readiness PASS: applications are closed, sources are valid, targets do not exist."
echo "Reviewer: $REVIEWER_SOURCE -> $REVIEWER_TARGET"
echo "Executor: $EXECUTOR_SOURCE -> $EXECUTOR_TARGET"

if [[ "$MODE" == "--check-only" ]]; then
  echo "CHECK ONLY: no files were copied or modified."
  exit 0
fi

LOCK="$MIX_ROOT/.1pcloop-runtimes-migration.lock"
mkdir "$LOCK" 2>/dev/null || fail "another runtime-home migration may be active"
STAGE=""
SCRATCH=""

cleanup() {
  if [[ -n "${STAGE:-}" && -d "$STAGE" && "$STAGE" == "$MIX_ROOT"/.1pcloop-runtimes-stage.* ]]; then
    rm -rf -- "$STAGE"
  fi
  if [[ -n "${SCRATCH:-}" && -d "$SCRATCH" && "$SCRATCH" == "${TMPDIR:-/tmp}"/1pcloop-migration.* ]]; then
    rm -rf -- "$SCRATCH"
  fi
  if [[ -n "${LOCK:-}" && -d "$LOCK" && "$LOCK" == "$MIX_ROOT/.1pcloop-runtimes-migration.lock" ]]; then
    rmdir "$LOCK" 2>/dev/null || true
  fi
}
trap cleanup EXIT INT TERM
STAGE="$(mktemp -d "$MIX_ROOT/.1pcloop-runtimes-stage.XXXXXX")"
SCRATCH="$(mktemp -d "${TMPDIR:-/tmp}/1pcloop-migration.XXXXXX")"

manifest_tree() {
  local root="$1"
  local output="$2"
  local comparison_mode="${3:-strict}"
  python3 - "$root" "$output" "$comparison_mode" <<'PY'
import hashlib
import json
import os
import stat
import sys
from pathlib import Path

root = Path(sys.argv[1])
output = Path(sys.argv[2])
comparison_mode = sys.argv[3]
if comparison_mode not in {"strict", "copy"}:
    raise SystemExit("invalid manifest comparison mode")
rows = []

def xattrs(path):
    result = {}
    try:
        names = os.listxattr(path, follow_symlinks=False)
    except (AttributeError, OSError):
        return result
    for name in sorted(names):
        try:
            value = os.getxattr(path, name, follow_symlinks=False)
        except OSError:
            continue
        result[name] = hashlib.sha256(value).hexdigest()
    return result

paths = [root]
paths.extend(sorted(root.rglob("*"), key=lambda item: item.relative_to(root).as_posix()))
for path in paths:
    info = path.lstat()
    relative = "." if path == root else path.relative_to(root).as_posix()
    row = {
        "path": relative,
        "mode": stat.S_IMODE(info.st_mode),
        "uid": info.st_uid,
        "gid": info.st_gid,
        "xattrs": xattrs(path),
    }
    if comparison_mode == "strict":
        row["mtime_ns"] = info.st_mtime_ns
    if stat.S_ISREG(info.st_mode):
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
        row.update(type="file", size=info.st_size, sha256=digest.hexdigest())
    elif stat.S_ISDIR(info.st_mode):
        row["type"] = "directory"
    elif stat.S_ISLNK(info.st_mode):
        row.update(type="symlink", target=os.readlink(path))
    else:
        row.update(type="other", size=info.st_size)
    rows.append(row)
output.write_text(
    "\n".join(json.dumps(row, sort_keys=True, separators=(",", ":")) for row in rows) + "\n",
    encoding="utf-8",
)
PY
}

manifest_protected_canonical_state() {
  local output="$1"
  python3 - "$CANONICAL_HOME" "$output" <<'PY'
import hashlib
import json
import sys
from pathlib import Path

root = Path(sys.argv[1])
output = Path(sys.argv[2])
selected = [
    root / "auth.json",
    root / "config.toml",
    root / ".codex-global-state.json",
    root / "history.jsonl",
    root / "installation_id",
    root / "sessions",
    root / "archived_sessions",
    root / ".mix/accounts",
]
selected.extend(sorted(root.glob("*.sqlite*")))
rows = []
for base in selected:
    if not base.exists() and not base.is_symlink():
        continue
    paths = [base]
    if base.is_dir() and not base.is_symlink():
        paths.extend(sorted(base.rglob("*")))
    for path in paths:
        info = path.lstat()
        row = {"path": path.relative_to(root).as_posix(), "mode": info.st_mode, "size": info.st_size, "mtime_ns": info.st_mtime_ns}
        if path.is_file() and not path.is_symlink():
            digest = hashlib.sha256()
            with path.open("rb") as handle:
                for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                    digest.update(chunk)
            row["sha256"] = digest.hexdigest()
        elif path.is_symlink():
            row["target"] = path.readlink().as_posix()
        rows.append(row)
output.write_text("\n".join(json.dumps(row, sort_keys=True) for row in rows) + "\n", encoding="utf-8")
PY
}

manifest_protected_canonical_state "$SCRATCH/canonical-before.jsonl"
manifest_tree "$REVIEWER_SOURCE" "$SCRATCH/reviewer-source.jsonl"
manifest_tree "$EXECUTOR_SOURCE" "$SCRATCH/executor-source.jsonl"

ditto --rsrc --extattr --acl "$REVIEWER_SOURCE" "$STAGE/1pcloop-reviewer"
ditto --rsrc --extattr --acl "$EXECUTOR_SOURCE" "$STAGE/1pcloop-executor"

manifest_tree "$REVIEWER_SOURCE" "$SCRATCH/reviewer-source-after.jsonl"
manifest_tree "$EXECUTOR_SOURCE" "$SCRATCH/executor-source-after.jsonl"

# Source stability remains strict, including mtime_ns.
cmp -s "$SCRATCH/reviewer-source.jsonl" "$SCRATCH/reviewer-source-after.jsonl" \
  || fail "Reviewer source changed during migration"
cmp -s "$SCRATCH/executor-source.jsonl" "$SCRATCH/executor-source-after.jsonl" \
  || fail "Executor source changed during migration"

# Copy equivalence deliberately excludes mtime_ns. ditto may recreate selected
# cache/tmp files with a new modification timestamp while preserving their
# actual bytes and all integrity-relevant metadata.
manifest_tree "$REVIEWER_SOURCE" "$SCRATCH/reviewer-source-copy.jsonl" copy
manifest_tree "$EXECUTOR_SOURCE" "$SCRATCH/executor-source-copy.jsonl" copy
manifest_tree "$STAGE/1pcloop-reviewer" "$SCRATCH/reviewer-target.jsonl" copy
manifest_tree "$STAGE/1pcloop-executor" "$SCRATCH/executor-target.jsonl" copy

cmp -s "$SCRATCH/reviewer-source-copy.jsonl" "$SCRATCH/reviewer-target.jsonl" \
  || fail "Reviewer source/target manifest mismatch"
cmp -s "$SCRATCH/executor-source-copy.jsonl" "$SCRATCH/executor-target.jsonl" \
  || fail "Executor source/target manifest mismatch"

python3 "$MIGRATION_HELPER" validate-copy \
  --source-a "$EXECUTOR_SOURCE" \
  --source-b "$REVIEWER_SOURCE" \
  --vault-a "$MIX_ROOT/accounts/A/auth.json" \
  --vault-b "$MIX_ROOT/accounts/B/auth.json" \
  --target-reviewer "$STAGE/1pcloop-reviewer" \
  --target-executor "$STAGE/1pcloop-executor" \
  --reviewer-home "$REVIEWER_TARGET" \
  --executor-home "$EXECUTOR_TARGET"

reviewer_source_files="$(find "$REVIEWER_SOURCE" -type f | wc -l | tr -d ' ')"
reviewer_target_files="$(find "$STAGE/1pcloop-reviewer" -type f | wc -l | tr -d ' ')"
executor_source_files="$(find "$EXECUTOR_SOURCE" -type f | wc -l | tr -d ' ')"
executor_target_files="$(find "$STAGE/1pcloop-executor" -type f | wc -l | tr -d ' ')"
[[ "$reviewer_source_files" == "$reviewer_target_files" ]] \
  || fail "Reviewer regular-file count mismatch"
[[ "$executor_source_files" == "$executor_target_files" ]] \
  || fail "Executor regular-file count mismatch"

[[ "$(stat -f '%i' "$REVIEWER_SOURCE")" != "$(stat -f '%i' "$STAGE/1pcloop-reviewer")" ]] \
  || fail "Reviewer target is not an independent copy"
[[ "$(stat -f '%i' "$EXECUTOR_SOURCE")" != "$(stat -f '%i' "$STAGE/1pcloop-executor")" ]] \
  || fail "Executor target is not an independent copy"

manifest_protected_canonical_state "$SCRATCH/canonical-after.jsonl"
cmp -s "$SCRATCH/canonical-before.jsonl" "$SCRATCH/canonical-after.jsonl" \
  || fail "canonical auth/config/state/history/sessions changed during migration"

[[ ! -e "$RUNTIME_ROOT" && ! -L "$RUNTIME_ROOT" ]] \
  || fail "dedicated runtime root appeared during migration"
python3 "$MIGRATION_HELPER" publish-root \
  --stage-root "$STAGE" \
  --runtime-root "$RUNTIME_ROOT"
STAGE=""

reviewer_count="$(wc -l <"$SCRATCH/reviewer-target.jsonl" | tr -d ' ')"
executor_count="$(wc -l <"$SCRATCH/executor-target.jsonl" | tr -d ' ')"
echo "MIGRATION PASS: independent cold copies created and verified."
echo "Reviewer manifest entries: $reviewer_count"
echo "Executor manifest entries: $executor_count"
echo "Reviewer regular files: $reviewer_target_files"
echo "Executor regular files: $executor_target_files"
echo "Historical ~/.codex-A and ~/.codex-B were not deleted or modified."
echo "Canonical state DB/history/sessions and credential projection were not modified."
