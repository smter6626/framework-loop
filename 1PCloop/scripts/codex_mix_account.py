#!/usr/bin/env python3
"""Fail-closed Codex Mix active-account binding for trusted 1PCloop turns.

This module reads the active Codex Mix projection without persisting credential
material. It supplies the current access token only in a child-process
environment and keeps Reviewer/Executor state in their dedicated CODEX_HOME.
"""

from __future__ import annotations

import base64
import contextlib
import fcntl
import hashlib
import json
import os
import re
import stat
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterator, Mapping, MutableMapping, Optional, Tuple


ACCOUNT_SOURCE_CODEX_MIX_ACTIVE = "codex_mix_active"
ACCOUNT_SOURCE_RUNTIME_HOME = "runtime_home"
ACCOUNT_SOURCES = (
    ACCOUNT_SOURCE_CODEX_MIX_ACTIVE,
    ACCOUNT_SOURCE_RUNTIME_HOME,
)
TOKEN_EXPIRY_MARGIN_SECONDS = 300
EPHEMERAL_CREDENTIAL_OVERRIDE = 'cli_auth_credentials_store="ephemeral"'
AUTH_ENVIRONMENT_EXCLUDE_OVERRIDE = (
    'shell_environment_policy.exclude=['
    '"CODEX_ACCESS_TOKEN","CODEX_API_KEY","OPENAI_API_KEY",'
    '"OPENAI_FEDERATION_RULE_ID","OPENAI_IDENTITY_TOKEN_FILE"]'
)
NOTIFY_DISABLED_OVERRIDE = "notify=[]"
CONFLICTING_AUTH_ENVIRONMENT = (
    "CODEX_API_KEY",
    "OPENAI_API_KEY",
    "OPENAI_FEDERATION_RULE_ID",
    "OPENAI_IDENTITY_TOKEN_FILE",
)
IMMUTABLE_SENTINELS = (
    ".codex-global-state.json",
    "installation_id",
    "state_5.sqlite",
    "thread_history_1.sqlite",
)
SQLITE_HOME_ASSIGNMENT = re.compile(
    r"^[ \t]*sqlite_home[ \t]*=[ \t]*(.*)$",
    re.MULTILINE,
)


class AccountBindingError(RuntimeError):
    """Codex Mix identity or retired-state evidence is inconsistent."""


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
                control
                / "forensics/runtime-cutover-20260918"
                / "retired-ab-final-snapshot.json"
            ),
            codex_route=home / ".codex",
            runtime_root=control / "runtimes",
        )


DEFAULT_PATHS = CodexMixPaths.from_user_home(Path.home())


@dataclass(frozen=True)
class ActiveAccountBinding:
    alias: str
    account_id_sha256: str
    access_token_expires_at: int

    def identity_metadata(self) -> Dict[str, str]:
        return {
            "account_alias": self.alias,
            "account_id_sha256": self.account_id_sha256,
        }

    def preflight_metadata(self, now: Optional[int] = None) -> Dict[str, Any]:
        current = int(time.time()) if now is None else int(now)
        return {
            **self.identity_metadata(),
            "access_token_ttl_seconds": max(
                0, self.access_token_expires_at - current
            ),
            "credential_storage": "ephemeral-child-environment",
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


def _auth_record(path: Path, label: str) -> Tuple[str, str, int]:
    value = _read_object(path, label)
    tokens = value.get("tokens")
    if not isinstance(tokens, dict):
        raise AccountBindingError(f"{label} has no tokens object")
    account_id = tokens.get("account_id")
    access_token = tokens.get("access_token")
    refresh_token = tokens.get("refresh_token")
    id_token = tokens.get("id_token")
    if not isinstance(account_id, str) or not account_id:
        raise AccountBindingError(f"{label} has no account identity")
    if not isinstance(access_token, str) or not access_token:
        raise AccountBindingError(f"{label} has no access token")
    if not isinstance(refresh_token, str) or not refresh_token:
        raise AccountBindingError(f"{label} has no refresh token")
    if not isinstance(id_token, str) or not id_token:
        raise AccountBindingError(f"{label} has no ID token")
    return account_id, access_token, _jwt_expiry(access_token)


def _account_digest(account_id: str) -> str:
    return hashlib.sha256(account_id.encode("utf-8")).hexdigest()


def _stat_record(path: Path) -> Optional[Dict[str, int]]:
    if not path.exists():
        return None
    value = path.stat()
    return {
        "size": value.st_size,
        "mtime_ns": value.st_mtime_ns,
        "inode": value.st_ino,
    }


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
                for name in (
                    "auth.json",
                    "config.toml",
                    *IMMUTABLE_SENTINELS,
                )
            },
            "sessions_file_count": _count_files(root / "sessions"),
            "archived_sessions_file_count": _count_files(
                root / "archived_sessions"
            ),
        }
    return result


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def capture_retired_tree(paths: CodexMixPaths) -> list:
    """Recreate the preserved A/B retirement snapshot byte-for-byte."""
    rows = []
    for root in (
        paths.user_home / ".codex-A",
        paths.user_home / ".codex-B",
    ):
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
    expected = _read_object_or_list(
        paths.retired_snapshot, "retired A/B snapshot"
    )
    if not isinstance(expected, list):
        raise AccountBindingError("retired A/B snapshot must contain a list")
    if capture_retired_tree(paths) != expected:
        raise AccountBindingError("retired A/B full-tree snapshot changed")


def _read_object_or_list(path: Path, label: str) -> Any:
    if not path.is_file() or path.is_symlink():
        raise AccountBindingError(f"{label} is missing, not regular, or aliased")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise AccountBindingError(f"{label} is not valid JSON") from exc


def validate_original_baseline(paths: CodexMixPaths) -> None:
    expected = _read_object(paths.baseline_file, "Codex Mix original baseline")
    actual = capture_original_baseline(paths)
    for alias in ("A", "B"):
        baseline = expected.get(alias)
        if not isinstance(baseline, dict):
            raise AccountBindingError("Codex Mix original baseline is incomplete")
        source = paths.user_home / f".codex-{alias}" / "auth.json"
        vault = paths.accounts_root / alias / "auth.json"
        source_id, _, _ = _auth_record(source, f"historical account {alias}")
        vault_id, _, _ = _auth_record(vault, f"vault account {alias}")
        if source_id != vault_id:
            raise AccountBindingError(
                f"historical account {alias} identity differs from its vault"
            )
        for name in IMMUTABLE_SENTINELS:
            if (
                actual[alias]["sentinels"].get(name)
                != baseline.get("sentinels", {}).get(name)
            ):
                raise AccountBindingError(
                    f"historical account {alias} immutable baseline changed"
                )
        for field in (
            "sessions_file_count",
            "archived_sessions_file_count",
        ):
            if actual[alias][field] != baseline.get(field):
                raise AccountBindingError(
                    f"historical account {alias} rollout inventory changed"
                )


def _active_state(
    paths: CodexMixPaths,
    *,
    minimum_ttl_seconds: int,
    now: Optional[int],
) -> Tuple[ActiveAccountBinding, str]:
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
    vault_path = paths.accounts_root / alias / "auth.json"
    canonical_id, access_token, expiry = _auth_record(
        paths.active_auth, "Codex Mix active credential"
    )
    vault_id, _, _ = _auth_record(vault_path, "Codex Mix active vault")
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
        prior = owners.get(candidate_id)
        if prior is not None:
            raise AccountBindingError(
                f"Codex Mix vault identities are duplicated: {prior}/{entry.name}"
            )
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
    return ActiveAccountBinding(alias, _account_digest(canonical_id), expiry), access_token


def inspect_active_account(
    *,
    paths: CodexMixPaths = DEFAULT_PATHS,
    minimum_ttl_seconds: int = 0,
    now: Optional[int] = None,
) -> ActiveAccountBinding:
    binding, _token = _active_state(
        paths,
        minimum_ttl_seconds=minimum_ttl_seconds,
        now=now,
    )
    return binding


def validate_role_runtime_config(
    role_home: Path,
    *,
    paths: CodexMixPaths = DEFAULT_PATHS,
) -> None:
    """Reject executable config paths that escape into retired A/B homes."""
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
        retired = str(paths.user_home / f".codex-{alias}")
        if retired in config:
            raise AccountBindingError(
                f"role config.toml references retired account {alias}"
            )
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
        value = assignments[0]
        candidate = Path(value)
        if not candidate.is_absolute() or candidate.resolve() != selected_home:
            raise AccountBindingError(
                "role sqlite_home must resolve to its dedicated runtime"
            )


def _restore_file(path: Path, content: bytes, mode: int) -> None:
    temporary = path.with_name(f".{path.name}.1pcloop-restore-{os.getpid()}")
    try:
        with temporary.open("xb") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temporary, stat.S_IMODE(mode))
        os.replace(temporary, path)
        directory = os.open(str(path.parent), os.O_RDONLY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    finally:
        if temporary.exists():
            temporary.unlink()


@contextlib.contextmanager
def active_account_environment(
    base_environment: Mapping[str, str],
    *,
    binding: ActiveAccountBinding,
    role_home: Path,
    timeout_seconds: int,
    paths: CodexMixPaths = DEFAULT_PATHS,
    now: Optional[int] = None,
) -> Iterator[Tuple[MutableMapping[str, str], Dict[str, Any]]]:
    """Hold the Codex Mix switch lock and inject one pinned active token."""
    selected_home = role_home.resolve()
    runtime_root = paths.runtime_root.resolve()
    if selected_home == runtime_root or runtime_root not in selected_home.parents:
        raise AccountBindingError("role home is outside the Codex Mix runtime root")
    if not role_home.is_dir() or role_home.is_symlink():
        raise AccountBindingError("role home is missing or aliased")
    role_auth = role_home / "auth.json"
    if not role_auth.is_file() or role_auth.is_symlink():
        raise AccountBindingError("role auth cache is missing or aliased")
    original_auth = role_auth.read_bytes()
    original_mode = role_auth.stat().st_mode
    original_sha = hashlib.sha256(original_auth).hexdigest()

    paths.switch_lock.parent.mkdir(parents=True, exist_ok=True)
    with paths.switch_lock.open("a+") as lock:
        try:
            fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise AccountBindingError(
                "Codex Mix switch operation is already in progress"
            ) from exc

        current, access_token = _active_state(
            paths,
            minimum_ttl_seconds=(
                int(timeout_seconds) + TOKEN_EXPIRY_MARGIN_SECONDS
            ),
            now=now,
        )
        if current.identity_metadata() != binding.identity_metadata():
            raise AccountBindingError(
                "Codex Mix active account changed after this run was bound"
            )

        environment: MutableMapping[str, str] = dict(base_environment)
        for name in CONFLICTING_AUTH_ENVIRONMENT:
            environment.pop(name, None)
        environment["CODEX_ACCESS_TOKEN"] = access_token
        metadata = {
            **binding.identity_metadata(),
            "credential_storage": "ephemeral-child-environment",
            "role_auth_sha256_before": original_sha,
        }
        body_error: Optional[BaseException] = None
        try:
            yield environment, metadata
        except BaseException as exc:
            body_error = exc
            raise
        finally:
            after_bytes = role_auth.read_bytes() if role_auth.is_file() else b""
            after_sha = hashlib.sha256(after_bytes).hexdigest()
            metadata["role_auth_sha256_after"] = after_sha
            metadata["role_auth_unchanged"] = after_sha == original_sha
            post_error: Optional[BaseException] = None
            try:
                post, _unused = _active_state(
                    paths,
                    minimum_ttl_seconds=0,
                    now=now,
                )
                if post.identity_metadata() != binding.identity_metadata():
                    raise AccountBindingError(
                        "Codex Mix active account changed during an Agent turn"
                    )
                if after_sha != original_sha:
                    _restore_file(role_auth, original_auth, original_mode)
                    raise AccountBindingError(
                        "Codex modified the role auth cache despite ephemeral binding"
                    )
            except BaseException as exc:
                post_error = exc
            if body_error is None and post_error is not None:
                raise post_error
