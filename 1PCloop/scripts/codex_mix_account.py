#!/usr/bin/env python3
"""Fail-closed Codex Mix account binding with recoverable auth projection.

Ordinary ChatGPT OAuth credentials are projected as the complete file expected
at ``CODEX_HOME/auth.json``. The projection is protected by the Codex Mix
switch lock, a per-role lock, and a persistent recovery transaction. Only
non-secret identity and recovery evidence may leave this module.
"""

from __future__ import annotations

import base64
import contextlib
import fcntl
import hashlib
import json
import os
import re
import shlex
import stat
import subprocess
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterator, List, Mapping, MutableMapping, Optional, Sequence, Tuple


ACCOUNT_SOURCE_CODEX_MIX_ACTIVE = "codex_mix_active"
ACCOUNT_SOURCE_RUNTIME_HOME = "runtime_home"
ACCOUNT_SOURCES = (ACCOUNT_SOURCE_CODEX_MIX_ACTIVE, ACCOUNT_SOURCE_RUNTIME_HOME)
TOKEN_EXPIRY_MARGIN_SECONDS = 300
FILE_CREDENTIAL_OVERRIDE = 'cli_auth_credentials_store="file"'
AUTH_ENVIRONMENT_EXCLUDE_OVERRIDE = (
    'shell_environment_policy.exclude=['
    '"CODEX_ACCESS_TOKEN","CODEX_API_KEY","OPENAI_API_KEY",'
    '"OPENAI_FEDERATION_RULE_ID","OPENAI_IDENTITY_TOKEN_FILE"]'
)
NOTIFY_DISABLED_OVERRIDE = "notify=[]"
CONFLICTING_AUTH_ENVIRONMENT = (
    "CODEX_ACCESS_TOKEN", "CODEX_API_KEY", "OPENAI_API_KEY",
    "OPENAI_FEDERATION_RULE_ID", "OPENAI_IDENTITY_TOKEN_FILE",
)
IMMUTABLE_SENTINELS = (
    ".codex-global-state.json", "installation_id", "state_5.sqlite",
    "thread_history_1.sqlite",
)
SQLITE_HOME_ASSIGNMENT = re.compile(
    r"^[ \t]*sqlite_home[ \t]*=[ \t]*(.*)$", re.MULTILINE
)
SENSITIVE_FIELD = re.compile(
    rb'(?i)(?:"|\b)(?:access_token|refresh_token|id_token)(?:"|\b)'
)
TRANSACTION_SCHEMA_VERSION = 1
TRANSACTION_STATES = frozenset({
    "INITIALIZED", "PREPARED", "PROJECTED", "CHILD_RUNNING", "CHILD_EXITED",
    "RESTORING", "RESTORED", "RECOVERED",
})
ROLE_HOME_NAMES = {
    "reviewer": "1pcloop-reviewer",
    "executor": "1pcloop-executor",
}


class AccountBindingError(RuntimeError):
    """Codex Mix identity, transaction, or retired-state evidence is unsafe."""


class CredentialExposureError(AccountBindingError):
    """An actual credential value appeared outside an authorized auth location."""


@dataclass(frozen=True)
class CodexMixPaths:
    user_home: Path
    canonical_home: Path
    control_root: Path
    accounts_root: Path
    active_auth: Path
    active_marker: Path
    switch_lock: Path
    baseline_file: Path
    retired_snapshot: Path
    codex_route: Path
    runtime_root: Path
    transactions_root: Path

    @classmethod
    def from_user_home(cls, user_home: Path) -> "CodexMixPaths":
        home = user_home.resolve()
        canonical = home / ".codex-mix"
        control = canonical / ".mix"
        return cls(
            user_home=home,
            canonical_home=canonical,
            control_root=control,
            accounts_root=control / "accounts",
            active_auth=canonical / "auth.json",
            active_marker=control / "active.json",
            switch_lock=control / "switch.lock",
            baseline_file=control / "original-baseline.json",
            retired_snapshot=(
                control / "forensics/runtime-cutover-20260918"
                / "retired-ab-final-snapshot.json"
            ),
            codex_route=home / ".codex",
            runtime_root=control / "runtimes",
            transactions_root=control / "transactions/1pcloop-auth",
        )


DEFAULT_PATHS = CodexMixPaths.from_user_home(Path.home())


@dataclass(frozen=True)
class ActiveAccountBinding:
    alias: str
    account_id_sha256: str
    access_token_expires_at: int
    transactions_recovered: int = 0

    def identity_metadata(self) -> Dict[str, str]:
        return {
            "account_alias": self.alias,
            "account_id_sha256": self.account_id_sha256,
        }

    def preflight_metadata(self, now: Optional[int] = None) -> Dict[str, Any]:
        current = int(time.time()) if now is None else int(now)
        return {
            **self.identity_metadata(),
            "access_token_ttl_seconds": max(0, self.access_token_expires_at - current),
            "credential_mode": "temporary-file-projection",
            "transactions_recovered": self.transactions_recovered,
        }


def _read_object(path: Path, label: str) -> Dict[str, Any]:
    if not path.is_file() or path.is_symlink():
        raise AccountBindingError(f"{label} is missing, not regular, or aliased")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise AccountBindingError(f"{label} is not valid JSON") from exc
    if not isinstance(value, dict):
        raise AccountBindingError(f"{label} must contain an object")
    return value


def _read_object_or_list(path: Path, label: str) -> Any:
    if not path.is_file() or path.is_symlink():
        raise AccountBindingError(f"{label} is missing, not regular, or aliased")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise AccountBindingError(f"{label} is not valid JSON") from exc


def _jwt_expiry(token: str) -> int:
    parts = token.split(".")
    if len(parts) != 3:
        raise AccountBindingError("active access token is not a JWT")
    encoded = parts[1] + ("=" * (-len(parts[1]) % 4))
    try:
        claims = json.loads(base64.urlsafe_b64decode(encoded).decode("utf-8"))
    except (ValueError, UnicodeError, json.JSONDecodeError) as exc:
        raise AccountBindingError("active access token claims are invalid") from exc
    expiry = claims.get("exp") if isinstance(claims, dict) else None
    if type(expiry) is not int:
        raise AccountBindingError("active access token has no integer expiry")
    return expiry


def _auth_record_from_bytes(content: bytes, label: str) -> Tuple[str, Tuple[bytes, ...], int]:
    try:
        value = json.loads(content.decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise AccountBindingError(f"{label} is not valid JSON") from exc
    tokens = value.get("tokens") if isinstance(value, dict) else None
    if not isinstance(tokens, dict):
        raise AccountBindingError(f"{label} has no tokens object")
    account_id = tokens.get("account_id")
    values = tuple(tokens.get(name) for name in (
        "access_token", "refresh_token", "id_token"
    ))
    if not isinstance(account_id, str) or not account_id:
        raise AccountBindingError(f"{label} has no account identity")
    if any(not isinstance(value, str) or not value for value in values):
        raise AccountBindingError(f"{label} has incomplete token material")
    return account_id, tuple(value.encode("utf-8") for value in values), _jwt_expiry(values[0])


def _auth_record(path: Path, label: str) -> Tuple[str, Tuple[bytes, ...], int]:
    if not path.is_file() or path.is_symlink():
        raise AccountBindingError(f"{label} is missing, not regular, or aliased")
    return _auth_record_from_bytes(path.read_bytes(), label)


def _account_digest(account_id: str) -> str:
    return hashlib.sha256(account_id.encode("utf-8")).hexdigest()


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _stat_record(path: Path) -> Optional[Dict[str, int]]:
    if not path.exists():
        return None
    value = path.stat()
    return {"size": value.st_size, "mtime_ns": value.st_mtime_ns, "inode": value.st_ino}


def _count_files(path: Path) -> int:
    if not path.exists():
        return 0
    return sum(1 for item in path.rglob("*") if item.is_file())


def capture_original_baseline(paths: CodexMixPaths) -> Dict[str, Any]:
    result: Dict[str, Any] = {}
    for alias in ("A", "B"):
        root = paths.user_home / f".codex-{alias}"
        result[alias] = {
            "root": str(root),
            "sentinels": {
                name: _stat_record(root / name)
                for name in ("auth.json", "config.toml", *IMMUTABLE_SENTINELS)
            },
            "sessions_file_count": _count_files(root / "sessions"),
            "archived_sessions_file_count": _count_files(root / "archived_sessions"),
        }
    return result


def capture_retired_tree(paths: CodexMixPaths) -> list:
    rows = []
    for root in (paths.user_home / ".codex-A", paths.user_home / ".codex-B"):
        if not root.is_dir() or root.is_symlink():
            raise AccountBindingError("retired account home is missing or aliased")
        for path in [root, *sorted(root.rglob("*"))]:
            info = path.lstat()
            row: Dict[str, Any] = {
                "root": str(root),
                "path": "." if path == root else path.relative_to(root).as_posix(),
                "mode": stat.S_IMODE(info.st_mode),
                "size": info.st_size,
                "mtime_ns": info.st_mtime_ns,
            }
            if stat.S_ISREG(info.st_mode):
                row.update(type="file", sha256=_sha256_file(path))
            elif stat.S_ISDIR(info.st_mode):
                row["type"] = "dir"
            elif stat.S_ISLNK(info.st_mode):
                row.update(type="symlink", target=os.readlink(path))
            else:
                row["type"] = "other"
            rows.append(row)
    return rows


def validate_retired_snapshot(paths: CodexMixPaths) -> None:
    expected = _read_object_or_list(paths.retired_snapshot, "retired A/B snapshot")
    if not isinstance(expected, list):
        raise AccountBindingError("retired A/B snapshot must contain a list")
    if capture_retired_tree(paths) != expected:
        raise AccountBindingError("retired A/B full-tree snapshot changed")


def validate_original_baseline(paths: CodexMixPaths) -> None:
    expected = _read_object(paths.baseline_file, "Codex Mix original baseline")
    actual = capture_original_baseline(paths)
    for alias in ("A", "B"):
        baseline = expected.get(alias)
        if not isinstance(baseline, dict):
            raise AccountBindingError("Codex Mix original baseline is incomplete")
        source_id, _, _ = _auth_record(
            paths.user_home / f".codex-{alias}" / "auth.json",
            f"historical account {alias}",
        )
        vault_id, _, _ = _auth_record(
            paths.accounts_root / alias / "auth.json", f"vault account {alias}"
        )
        if source_id != vault_id:
            raise AccountBindingError(
                f"historical account {alias} identity differs from its vault"
            )
        for name in IMMUTABLE_SENTINELS:
            if actual[alias]["sentinels"].get(name) != baseline.get("sentinels", {}).get(name):
                raise AccountBindingError(
                    f"historical account {alias} immutable baseline changed"
                )
        for field in ("sessions_file_count", "archived_sessions_file_count"):
            if actual[alias][field] != baseline.get(field):
                raise AccountBindingError(
                    f"historical account {alias} rollout inventory changed"
                )


def _active_state(
    paths: CodexMixPaths, *, minimum_ttl_seconds: int, now: Optional[int]
) -> Tuple[ActiveAccountBinding, bytes, Tuple[bytes, ...]]:
    if not paths.canonical_home.is_dir() or paths.canonical_home.is_symlink():
        raise AccountBindingError("canonical Codex Mix home is missing or aliased")
    if not paths.codex_route.is_symlink():
        raise AccountBindingError("~/.codex is not the managed Codex Mix route")
    route_target = Path(os.readlink(paths.codex_route))
    if not route_target.is_absolute():
        route_target = paths.codex_route.parent / route_target
    if route_target.resolve(strict=False) != paths.canonical_home.resolve():
        raise AccountBindingError("~/.codex does not resolve to canonical Codex Mix")

    marker = _read_object(paths.active_marker, "Codex Mix active marker")
    alias = marker.get("active_account")
    if not isinstance(alias, str) or not alias:
        raise AccountBindingError("Codex Mix active marker has no account alias")
    active_bytes = paths.active_auth.read_bytes()
    canonical_id, secrets, expiry = _auth_record_from_bytes(
        active_bytes, "Codex Mix active credential"
    )
    vault_id, _, _ = _auth_record(
        paths.accounts_root / alias / "auth.json", "Codex Mix active vault"
    )
    if canonical_id != vault_id:
        raise AccountBindingError(
            "Codex Mix active marker, projected credential, and vault disagree"
        )

    owners: Dict[str, str] = {}
    if not paths.accounts_root.is_dir() or paths.accounts_root.is_symlink():
        raise AccountBindingError("Codex Mix account vault is unavailable")
    for entry in sorted(paths.accounts_root.iterdir(), key=lambda item: item.name):
        candidate = entry / "auth.json"
        if not entry.is_dir() or entry.is_symlink() or not candidate.exists():
            continue
        candidate_id, _, _ = _auth_record(candidate, f"vault account {entry.name}")
        if candidate_id in owners:
            raise AccountBindingError("Codex Mix vault identities are duplicated")
        owners[candidate_id] = entry.name
    if owners.get(canonical_id) != alias:
        raise AccountBindingError(
            "Codex Mix active credential does not uniquely match its marker"
        )
    current = int(time.time()) if now is None else int(now)
    if expiry - current < minimum_ttl_seconds:
        raise AccountBindingError(
            "Codex Mix active access token lifetime is shorter than the turn timeout"
        )
    validate_original_baseline(paths)
    validate_retired_snapshot(paths)
    return ActiveAccountBinding(alias, _account_digest(canonical_id), expiry), active_bytes, secrets


def inspect_active_account(
    *, paths: CodexMixPaths = DEFAULT_PATHS, minimum_ttl_seconds: int = 0,
    now: Optional[int] = None,
) -> ActiveAccountBinding:
    recovered = recover_incomplete_transactions(paths=paths)
    binding, _auth, _secrets = _active_state(
        paths, minimum_ttl_seconds=minimum_ttl_seconds, now=now
    )
    return ActiveAccountBinding(
        binding.alias, binding.account_id_sha256,
        binding.access_token_expires_at, recovered,
    )


def validate_role_runtime_config(
    role_home: Path, *, paths: CodexMixPaths = DEFAULT_PATHS
) -> None:
    selected_home = role_home.resolve()
    runtime_root = paths.runtime_root.resolve()
    if selected_home == runtime_root or runtime_root not in selected_home.parents:
        raise AccountBindingError("role home is outside the Codex Mix runtime root")
    config_path = role_home / "config.toml"
    if not config_path.is_file() or config_path.is_symlink():
        raise AccountBindingError("role config.toml is missing or aliased")
    try:
        config = config_path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise AccountBindingError("role config.toml is unreadable") from exc
    for alias in ("A", "B"):
        if str(paths.user_home / f".codex-{alias}") in config:
            raise AccountBindingError(f"role config.toml references retired account {alias}")
    assignments = []
    for match in SQLITE_HOME_ASSIGNMENT.finditer(config):
        raw = match.group(1).split("#", 1)[0].strip()
        if len(raw) < 2 or raw[0] not in ("'", '"') or raw[-1] != raw[0]:
            raise AccountBindingError("role sqlite_home must be a TOML string")
        if raw[0] == '"':
            try:
                value = json.loads(raw)
            except json.JSONDecodeError as exc:
                raise AccountBindingError("role sqlite_home is invalid") from exc
        else:
            value = raw[1:-1]
            if "'" in value:
                raise AccountBindingError("role sqlite_home is invalid")
        assignments.append(value)
    if len(assignments) > 1:
        raise AccountBindingError("role config.toml repeats sqlite_home")
    if assignments:
        candidate = Path(assignments[0])
        if not candidate.is_absolute() or candidate.resolve() != selected_home:
            raise AccountBindingError(
                "role sqlite_home must resolve to its dedicated runtime"
            )


def _fsync_directory(path: Path) -> None:
    descriptor = os.open(str(path), os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _ensure_private_directory(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True, mode=0o700)
    if path.is_symlink() or not path.is_dir():
        raise AccountBindingError("credential transaction directory is unsafe")
    os.chmod(path, 0o700)


def _atomic_write(path: Path, content: bytes, mode: int = 0o600) -> None:
    temporary = path.with_name(f".{path.name}.1pcloop-{os.getpid()}-{uuid.uuid4().hex}")
    try:
        descriptor = os.open(str(temporary), os.O_WRONLY | os.O_CREAT | os.O_EXCL, mode)
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temporary, mode)
        os.replace(temporary, path)
        _fsync_directory(path.parent)
    finally:
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass


def _atomic_json(path: Path, value: Mapping[str, Any]) -> None:
    _atomic_write(
        path,
        (json.dumps(value, ensure_ascii=True, indent=2, sort_keys=True) + "\n").encode("ascii"),
    )


def _restore_file(path: Path, content: bytes, mode: int, mtime_ns: Optional[int] = None) -> None:
    _atomic_write(path, content, stat.S_IMODE(mode))
    if mtime_ns is not None:
        os.utime(path, ns=(mtime_ns, mtime_ns))
        _fsync_directory(path.parent)


def _role_for_home(role_home: Path, paths: CodexMixPaths) -> str:
    selected = role_home.resolve()
    for role, name in ROLE_HOME_NAMES.items():
        if selected == (paths.runtime_root / name).resolve():
            return role
    raise AccountBindingError("role home is not an authorized 1PCloop runtime")


def _role_lock_path(role: str, paths: CodexMixPaths) -> Path:
    return paths.transactions_root / ".locks" / f"{role}.lock"


def _lock_file(path: Path) -> Any:
    _ensure_private_directory(path.parent)
    handle = path.open("a+")
    os.chmod(path, 0o600)
    try:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError as exc:
        handle.close()
        raise AccountBindingError("credential transaction lock is already held") from exc
    return handle


def _process_identity(pid: int) -> Optional[Dict[str, Any]]:
    fields: Dict[str, str] = {}
    for key, option in (("pgid", "pgid="), ("start", "lstart="), ("command", "command=")):
        result = subprocess.run(
            ["ps", "-p", str(pid), "-o", option], stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL, text=True, check=False, timeout=3,
        )
        if result.returncode != 0 or not result.stdout.strip():
            return None
        fields[key] = result.stdout.strip()
    try:
        executable = shlex.split(fields["command"])[0]
    except (ValueError, IndexError):
        executable = "unavailable"
    try:
        pgid = int(fields["pgid"])
    except ValueError as exc:
        raise AccountBindingError("child process group is invalid") from exc
    return {
        "child_pid": pid,
        "child_pgid": pgid,
        "child_started_at": fields["start"],
        "child_executable": executable,
        "command_fingerprint": hashlib.sha256(
            fields["command"].encode("utf-8")
        ).hexdigest(),
    }


def _recorded_child_is_running(record: Mapping[str, Any]) -> bool:
    pid = record.get("child_pid")
    if type(pid) is not int or pid <= 0:
        return False
    current = _process_identity(pid)
    if current is None:
        return False
    expected = {
        key: record.get(key)
        for key in (
            "child_pid", "child_pgid", "child_started_at", "child_executable",
            "command_fingerprint",
        )
    }
    if current != expected:
        raise AccountBindingError(
            "credential transaction child PID exists but identity is ambiguous"
        )
    return True


def _safe_transaction_record(path: Path) -> Dict[str, Any]:
    record = _read_object(path, "credential transaction record")
    if record.get("schema_version") != TRANSACTION_SCHEMA_VERSION:
        raise AccountBindingError("credential transaction schema is unsupported")
    if record.get("state") not in TRANSACTION_STATES:
        raise AccountBindingError("credential transaction state is invalid")
    if record.get("role") not in ROLE_HOME_NAMES:
        raise AccountBindingError("credential transaction role is invalid")
    rendered_keys = " ".join(str(key) for key in record)
    if re.search(r"(?i)(?:access|refresh|id)_token|email|raw_account_id", rendered_keys):
        raise AccountBindingError("credential transaction contains a prohibited field")
    return record


def _remove_transaction(transaction_dir: Path) -> None:
    for path in transaction_dir.iterdir():
        if path.is_symlink() or not path.is_file():
            raise AccountBindingError("credential transaction cleanup found an unsafe entry")
        if path.name not in {"original-role-auth.json", "transaction.json"} and not (
            path.name.startswith(".transaction.json.1pcloop-")
            or path.name.startswith(".original-role-auth.json.1pcloop-")
        ):
            raise AccountBindingError("credential transaction cleanup found an unknown file")
        path.unlink()
    transaction_dir.rmdir()
    _fsync_directory(transaction_dir.parent)


def _recover_transaction(transaction_dir: Path, paths: CodexMixPaths) -> bool:
    record_path = transaction_dir / "transaction.json"
    backup = transaction_dir / "original-role-auth.json"
    if not record_path.exists():
        entries = list(transaction_dir.iterdir())
        if all(
            path.is_file() and not path.is_symlink()
            and path.name.startswith(".transaction.json.1pcloop-")
            for path in entries
        ):
            for path in entries:
                path.unlink()
            transaction_dir.rmdir()
            _fsync_directory(transaction_dir.parent)
            return True
        raise AccountBindingError("orphan credential transaction lacks recovery metadata")
    record = _safe_transaction_record(record_path)
    role_auth = paths.runtime_root / ROLE_HOME_NAMES[record["role"]] / "auth.json"
    if _recorded_child_is_running(record):
        raise AccountBindingError(
            "credential transaction child is still running "
            f"pid={record['child_pid']} pgid={record['child_pgid']}"
        )
    if record["state"] in {"RESTORED", "RECOVERED"}:
        if not role_auth.is_file() or _sha256_file(role_auth) != record.get("role_auth_original_sha256"):
            raise AccountBindingError("completed credential recovery does not match role auth")
        _remove_transaction(transaction_dir)
        return True
    if not backup.is_file() or backup.is_symlink():
        if (
            record["state"] == "INITIALIZED"
            and role_auth.is_file()
            and not role_auth.is_symlink()
            and _sha256_file(role_auth) == record.get("role_auth_original_sha256")
        ):
            _remove_transaction(transaction_dir)
            return True
        raise AccountBindingError("credential recovery copy is missing or aliased")
    content = backup.read_bytes()
    if _sha256_bytes(content) != record.get("role_auth_original_sha256"):
        raise AccountBindingError("credential recovery copy hash mismatch")
    mode = record.get("role_auth_original_mode")
    mtime_ns = record.get("role_auth_original_mtime_ns")
    if type(mode) is not int or type(mtime_ns) is not int:
        raise AccountBindingError("credential recovery metadata is incomplete")
    record["state"] = "RESTORING"
    _atomic_json(record_path, record)
    _restore_file(role_auth, content, mode, mtime_ns)
    if _sha256_file(role_auth) != record["role_auth_original_sha256"]:
        raise AccountBindingError("credential recovery verification failed")
    record["state"] = "RECOVERED"
    _atomic_json(record_path, record)
    _remove_transaction(transaction_dir)
    return True


def _transaction_directories(paths: CodexMixPaths) -> List[Path]:
    _ensure_private_directory(paths.transactions_root)
    return [
        path for path in sorted(paths.transactions_root.iterdir(), key=lambda item: item.name)
        if path.name != ".locks" and path.is_dir() and not path.is_symlink()
    ]


def recover_incomplete_transactions(
    *, paths: CodexMixPaths = DEFAULT_PATHS, switch_lock_held: bool = False
) -> int:
    """Recover stale transactions whose verified child no longer exists."""
    _ensure_private_directory(paths.transactions_root)
    switch_handle = None
    if not switch_lock_held:
        paths.switch_lock.parent.mkdir(parents=True, exist_ok=True)
        switch_handle = _lock_file(paths.switch_lock)
    recovered = 0
    try:
        for transaction_dir in _transaction_directories(paths):
            record_path = transaction_dir / "transaction.json"
            if record_path.exists():
                role = _safe_transaction_record(record_path)["role"]
                role_lock = _lock_file(_role_lock_path(role, paths))
            else:
                role_lock = None
            try:
                if _recover_transaction(transaction_dir, paths):
                    recovered += 1
            finally:
                if role_lock is not None:
                    role_lock.close()
    finally:
        if switch_handle is not None:
            switch_handle.close()
    return recovered


def _candidate_files(
    roots: Sequence[Path], git_repositories: Sequence[Path], *, since_ns: int,
    excluded: Sequence[Path],
) -> List[Path]:
    excluded_resolved = {path.resolve(strict=False) for path in excluded}
    result = set()
    for root in roots:
        if not root.exists() or root.is_symlink():
            continue
        for path in ([root] if root.is_file() else root.rglob("*")):
            try:
                resolved = path.resolve(strict=False)
                if (
                    resolved in excluded_resolved or path.is_symlink() or not path.is_file()
                    or path.stat().st_mtime_ns < since_ns
                ):
                    continue
            except OSError:
                continue
            result.add(resolved)
    for repo in git_repositories:
        if not (repo / ".git").exists():
            continue
        for args in (["ls-files", "-z"], ["ls-files", "--others", "--exclude-standard", "-z"]):
            completed = subprocess.run(
                ["git", *args], cwd=str(repo), stdout=subprocess.PIPE,
                stderr=subprocess.PIPE, check=False,
            )
            if completed.returncode != 0:
                raise AccountBindingError("credential scan could not enumerate Git files")
            for raw in completed.stdout.split(b"\0"):
                if not raw:
                    continue
                path = (repo / os.fsdecode(raw)).resolve(strict=False)
                if path not in excluded_resolved and path.is_file() and not path.is_symlink():
                    result.add(path)
    return sorted(result)


def scan_credential_exposure(
    *, secrets: Sequence[bytes], roots: Sequence[Path],
    git_repositories: Sequence[Path], since_ns: int, excluded: Sequence[Path],
    git_baselines: Optional[Mapping[Path, str]] = None,
) -> Dict[str, Any]:
    files = _candidate_files(
        roots, git_repositories, since_ns=since_ns, excluded=excluded
    )
    actual_hits: List[str] = []
    field_hits = 0
    for path in files:
        try:
            content = path.read_bytes()
        except OSError as exc:
            raise AccountBindingError("credential scan could not read an output file") from exc
        if any(secret and secret in content for secret in secrets):
            actual_hits.append(str(path))
        if SENSITIVE_FIELD.search(content):
            field_hits += 1
    for repo, baseline in (git_baselines or {}).items():
        completed = subprocess.run(
            ["git", "diff", "--binary", baseline], cwd=str(repo),
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
        )
        if completed.returncode != 0:
            raise AccountBindingError("credential scan could not inspect Git changes")
        locator = f"{repo.resolve()}:git-diff-from-{baseline}"
        if any(secret and secret in completed.stdout for secret in secrets):
            actual_hits.append(locator)
        if SENSITIVE_FIELD.search(completed.stdout):
            field_hits += 1
    result = {
        "actual_credential_hits": len(actual_hits),
        "field_name_hits": field_hits,
        "files_scanned": len(files),
        "git_diffs_scanned": len(git_baselines or {}),
        "hit_files": actual_hits,
    }
    if actual_hits:
        raise CredentialExposureError(
            "credential exposure detected in "
            f"{len(actual_hits)} output file(s): {', '.join(actual_hits)}"
        )
    return result


class AuthProjectionTransaction:
    def __init__(
        self, *, transaction_dir: Path, record: Dict[str, Any],
        record_path: Path, role_auth: Path,
    ) -> None:
        self.transaction_dir = transaction_dir
        self.record = record
        self.record_path = record_path
        self.role_auth = role_auth

    def _write(self) -> None:
        _atomic_json(self.record_path, self.record)

    def child_started(self, process: subprocess.Popen, _command: Sequence[str]) -> None:
        identity = None
        for _attempt in range(20):
            identity = _process_identity(process.pid)
            if identity is not None:
                break
            time.sleep(0.01)
        if identity is None:
            raise AccountBindingError("unable to capture Codex child identity")
        self.record.update(identity)
        self.record["state"] = "CHILD_RUNNING"
        self._write()

    def child_stopped(self, process: subprocess.Popen) -> None:
        if process.poll() is None:
            raise AccountBindingError("Codex child is still running at transaction close")
        self.record["child_exit_code"] = process.returncode
        self.record["state"] = "CHILD_EXITED"
        self._write()


@contextlib.contextmanager
def active_account_environment(
    base_environment: Mapping[str, str], *, binding: ActiveAccountBinding,
    role_home: Path, timeout_seconds: int, run_id: str = "unknown-run",
    turn: str = "unknown-turn", role: Optional[str] = None,
    scan_roots: Sequence[Path] = (), git_repositories: Sequence[Path] = (),
    paths: CodexMixPaths = DEFAULT_PATHS, now: Optional[int] = None,
) -> Iterator[Tuple[MutableMapping[str, str], Dict[str, Any], AuthProjectionTransaction]]:
    """Project active file credentials for one locked, recoverable Agent turn."""
    selected_home = role_home.resolve()
    selected_role = role or _role_for_home(selected_home, paths)
    if selected_role != _role_for_home(selected_home, paths):
        raise AccountBindingError("turn role does not match its dedicated runtime")
    if not role_home.is_dir() or role_home.is_symlink():
        raise AccountBindingError("role home is missing or aliased")
    role_auth = role_home / "auth.json"
    if not role_auth.is_file() or role_auth.is_symlink():
        raise AccountBindingError("role auth cache is missing or aliased")

    _ensure_private_directory(paths.transactions_root)
    switch_handle = _lock_file(paths.switch_lock)
    role_handle = None
    transaction_dir: Optional[Path] = None
    original_auth: Optional[bytes] = None
    original_stat: Optional[os.stat_result] = None
    cleanup_error: Optional[BaseException] = None
    body_error: Optional[BaseException] = None
    try:
        recover_incomplete_transactions(paths=paths, switch_lock_held=True)
        role_handle = _lock_file(_role_lock_path(selected_role, paths))
        current, active_auth, secrets = _active_state(
            paths,
            minimum_ttl_seconds=int(timeout_seconds) + TOKEN_EXPIRY_MARGIN_SECONDS,
            now=now,
        )
        if current.identity_metadata() != binding.identity_metadata():
            raise AccountBindingError(
                "Codex Mix active account changed after this run was bound"
            )
        git_baselines: Dict[Path, str] = {}
        for repository in git_repositories:
            completed = subprocess.run(
                ["git", "rev-parse", "HEAD"], cwd=str(repository),
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                check=False,
            )
            if completed.returncode != 0 or not completed.stdout.strip():
                raise AccountBindingError("credential transaction Git baseline is unavailable")
            git_baselines[repository.resolve()] = completed.stdout.strip()

        original_auth = role_auth.read_bytes()
        original_stat = role_auth.stat()
        original_sha = _sha256_bytes(original_auth)
        transaction_id = f"{int(time.time())}-{selected_role}-{os.getpid()}-{uuid.uuid4().hex}"
        transaction_dir = paths.transactions_root / transaction_id
        transaction_dir.mkdir(mode=0o700)
        os.chmod(transaction_dir, 0o700)
        backup = transaction_dir / "original-role-auth.json"
        record_path = transaction_dir / "transaction.json"
        record: Dict[str, Any] = {
            "schema_version": TRANSACTION_SCHEMA_VERSION,
            "transaction_id": transaction_id,
            "run_id": run_id,
            "turn": turn,
            "role": selected_role,
            "account_alias": binding.alias,
            "account_id_sha256": binding.account_id_sha256,
            "role_auth_original_sha256": original_sha,
            "role_auth_original_mode": stat.S_IMODE(original_stat.st_mode),
            "role_auth_original_mtime_ns": original_stat.st_mtime_ns,
            "state": "INITIALIZED",
            "started_at_ns": time.time_ns(),
        }
        _atomic_json(record_path, record)
        _atomic_write(backup, original_auth, 0o600)
        record["state"] = "PREPARED"
        _atomic_json(record_path, record)
        _atomic_write(role_auth, active_auth, 0o600)
        projected_id, _, _ = _auth_record(role_auth, "projected role credential")
        if _account_digest(projected_id) != binding.account_id_sha256:
            raise AccountBindingError("projected role credential identity mismatch")
        record["state"] = "PROJECTED"
        _atomic_json(record_path, record)
        transaction = AuthProjectionTransaction(
            transaction_dir=transaction_dir, record=record,
            record_path=record_path, role_auth=role_auth,
        )
        environment: MutableMapping[str, str] = dict(base_environment)
        for name in CONFLICTING_AUTH_ENVIRONMENT:
            environment.pop(name, None)
        metadata: Dict[str, Any] = {
            **binding.identity_metadata(),
            "credential_mode": "temporary-file-projection",
            "role_auth_sha256_before": original_sha,
            "role_auth_restored": False,
            "active_identity_unchanged": False,
            "transaction_recovered": binding.transactions_recovered > 0,
        }
        try:
            yield environment, metadata, transaction
        except BaseException as exc:
            body_error = exc
        finally:
            try:
                if record.get("state") == "CHILD_RUNNING":
                    if _recorded_child_is_running(record):
                        raise AccountBindingError(
                            "Codex child remained active during credential recovery"
                        )
                    record["state"] = "CHILD_EXITED"
                    _atomic_json(record_path, record)
                projected_after = role_auth.read_bytes() if role_auth.is_file() else b""
                projected_modified = projected_after != active_auth
                metadata["role_auth_modified_during_turn"] = projected_modified
                diagnostic_root = paths.user_home / "Library/Logs/DiagnosticReports"
                scan_error: Optional[BaseException] = None
                try:
                    metadata["credential_scan"] = scan_credential_exposure(
                        secrets=secrets,
                        roots=(
                            *scan_roots, role_home / "sessions",
                            role_home / "archived_sessions", role_home / "logs",
                            diagnostic_root, transaction_dir / "transaction.json",
                        ),
                        git_repositories=git_repositories,
                        git_baselines=git_baselines,
                        since_ns=record["started_at_ns"],
                        excluded=(role_auth, backup, paths.active_auth),
                    )
                except BaseException as exc:
                    scan_error = exc
                record["state"] = "RESTORING"
                _atomic_json(record_path, record)
                _restore_file(
                    role_auth, original_auth, original_stat.st_mode,
                    original_stat.st_mtime_ns,
                )
                restored_sha = _sha256_file(role_auth)
                if (
                    restored_sha != original_sha
                    or stat.S_IMODE(role_auth.stat().st_mode)
                    != stat.S_IMODE(original_stat.st_mode)
                ):
                    raise AccountBindingError("role auth restoration verification failed")
                post, _post_auth, _post_secrets = _active_state(
                    paths, minimum_ttl_seconds=0, now=now
                )
                if post.identity_metadata() != binding.identity_metadata():
                    raise AccountBindingError(
                        "Codex Mix active account changed during an Agent turn"
                    )
                metadata["role_auth_sha256_after"] = restored_sha
                metadata["role_auth_restored"] = True
                metadata["active_identity_unchanged"] = True
                record["state"] = "RESTORED"
                _atomic_json(record_path, record)
                _remove_transaction(transaction_dir)
                transaction_dir = None
                validate_retired_snapshot(paths)
                if scan_error is not None:
                    raise scan_error
                if projected_modified:
                    raise AccountBindingError(
                        "Codex modified the temporary role credential projection"
                    )
            except BaseException as exc:
                cleanup_error = exc
    except BaseException:
        if (
            transaction_dir is not None
            and original_auth is not None
            and original_stat is not None
        ):
            try:
                _restore_file(
                    role_auth, original_auth, original_stat.st_mode,
                    original_stat.st_mtime_ns,
                )
                if _sha256_file(role_auth) != _sha256_bytes(original_auth):
                    raise AccountBindingError("setup recovery verification failed")
                _remove_transaction(transaction_dir)
                transaction_dir = None
            except BaseException as recovery_exc:
                raise AccountBindingError(
                    "credential transaction setup recovery failed"
                ) from recovery_exc
        raise
    finally:
        if role_handle is not None:
            role_handle.close()
        switch_handle.close()
    if cleanup_error is not None:
        if isinstance(cleanup_error, CredentialExposureError):
            raise cleanup_error
        raise AccountBindingError("credential transaction recovery failed") from cleanup_error
    if body_error is not None:
        raise body_error
