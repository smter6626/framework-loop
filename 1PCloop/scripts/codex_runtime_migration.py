#!/usr/bin/env python3
"""Pure validation and transactional helpers for Codex runtime-home migration."""

from __future__ import annotations

import argparse
import json
import os
import re
import signal
from pathlib import Path
from typing import Any, Callable, Dict, Optional, Sequence


class MigrationSafetyError(RuntimeError):
    """Migration identity, configuration, or publication is unsafe."""


def _strict_json(path: Path) -> Dict[str, Any]:
    def pairs(items):
        result: Dict[str, Any] = {}
        for key, value in items:
            if key in result:
                raise MigrationSafetyError("auth JSON contains a duplicate key")
            result[key] = value
        return result

    try:
        value = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=pairs)
    except MigrationSafetyError:
        raise
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise MigrationSafetyError("auth JSON is unavailable or invalid") from exc
    if not isinstance(value, dict):
        raise MigrationSafetyError("auth JSON root must be an object")
    return value


def account_id(auth_path: Path) -> str:
    """Read only the stable account identity without exposing credentials."""
    value = _strict_json(auth_path)
    candidates = []
    direct = value.get("account_id")
    if isinstance(direct, str) and direct:
        candidates.append(direct)
    tokens = value.get("tokens")
    if isinstance(tokens, dict):
        nested = tokens.get("account_id")
        if isinstance(nested, str) and nested:
            candidates.append(nested)
    distinct = set(candidates)
    if len(distinct) != 1:
        raise MigrationSafetyError("auth JSON has missing or ambiguous account identity")
    return distinct.pop()


def validate_source_identities(
    *, source_a: Path, source_b: Path, vault_a: Path, vault_b: Path
) -> None:
    source_a_id = account_id(source_a / "auth.json")
    source_b_id = account_id(source_b / "auth.json")
    vault_a_id = account_id(vault_a)
    vault_b_id = account_id(vault_b)
    if source_a_id != vault_a_id:
        raise MigrationSafetyError("source A does not match vault account A")
    if source_b_id != vault_b_id:
        raise MigrationSafetyError("source B does not match vault account B")
    if source_a_id == source_b_id or vault_a_id == vault_b_id:
        raise MigrationSafetyError("account A and account B identities are not distinct")


def validate_target_identities(
    *,
    source_a: Path,
    source_b: Path,
    target_reviewer: Path,
    target_executor: Path,
    vault_a: Path,
    vault_b: Path,
) -> None:
    validate_source_identities(
        source_a=source_a, source_b=source_b, vault_a=vault_a, vault_b=vault_b
    )
    source_a_id = account_id(source_a / "auth.json")
    source_b_id = account_id(source_b / "auth.json")
    reviewer_id = account_id(target_reviewer / "auth.json")
    executor_id = account_id(target_executor / "auth.json")
    if reviewer_id != source_b_id:
        raise MigrationSafetyError("Reviewer target does not preserve source B identity")
    if executor_id != source_a_id:
        raise MigrationSafetyError("Executor target does not preserve source A identity")
    if reviewer_id == executor_id:
        raise MigrationSafetyError("Reviewer and Executor target identities are not distinct")


_SQLITE_KEY = re.compile(r'^\s*(?:sqlite_home|"sqlite_home"|\'sqlite_home\')\s*=\s*(.*)$')
_TABLE = re.compile(r"^\s*\[\[?.*\]\]?\s*(?:#.*)?$")


def _without_toml_comment(value: str) -> str:
    quote: Optional[str] = None
    escaped = False
    result = []
    for character in value:
        if escaped:
            result.append(character)
            escaped = False
            continue
        if quote == '"' and character == "\\":
            result.append(character)
            escaped = True
            continue
        if quote is None and character in ("'", '"'):
            quote = character
            result.append(character)
            continue
        if quote == character:
            quote = None
            result.append(character)
            continue
        if quote is None and character == "#":
            break
        result.append(character)
    if quote is not None:
        raise MigrationSafetyError("sqlite_home must be a single-line TOML string")
    return "".join(result).strip()


def configured_sqlite_home(config_path: Path) -> Optional[str]:
    try:
        lines = config_path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeError) as exc:
        raise MigrationSafetyError("config.toml is unavailable or invalid") from exc
    top_level = True
    found = []
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if _TABLE.match(line):
            top_level = False
            continue
        if not top_level:
            continue
        match = _SQLITE_KEY.match(line)
        if match is None:
            continue
        raw = _without_toml_comment(match.group(1))
        if raw.startswith('"""') or raw.startswith("'''"):
            raise MigrationSafetyError("multiline sqlite_home is not supported")
        if len(raw) < 2 or raw[0] not in ("'", '"') or raw[-1] != raw[0]:
            raise MigrationSafetyError("sqlite_home must be a TOML string")
        if raw[0] == '"':
            try:
                parsed = json.loads(raw)
            except json.JSONDecodeError as exc:
                raise MigrationSafetyError("sqlite_home string is invalid") from exc
        else:
            parsed = raw[1:-1]
            if "'" in parsed:
                raise MigrationSafetyError("sqlite_home literal string is invalid")
        if not isinstance(parsed, str) or not parsed:
            raise MigrationSafetyError("sqlite_home must be non-empty")
        found.append(parsed)
    if len(found) > 1:
        raise MigrationSafetyError("config.toml defines sqlite_home more than once")
    return found[0] if found else None


def validate_sqlite_home(config_path: Path, expected_home: Path) -> None:
    configured = configured_sqlite_home(config_path)
    if configured is None:
        return
    if "$" in configured:
        raise MigrationSafetyError("sqlite_home must not use environment expansion")
    selected = Path(configured).expanduser()
    if not selected.is_absolute():
        raise MigrationSafetyError("relative sqlite_home is unsafe for role runtime")
    if selected.resolve() != expected_home.resolve():
        raise MigrationSafetyError("sqlite_home points outside the selected role runtime")


def publish_runtime_root(
    stage_root: Path,
    runtime_root: Path,
    *,
    rename: Callable[[Path, Path], None] = os.rename,
) -> None:
    """Atomically publish both role homes as one previously absent root."""
    if not stage_root.is_dir() or stage_root.is_symlink():
        raise MigrationSafetyError("runtime publish stage is missing or aliased")
    for child in ("1pcloop-reviewer", "1pcloop-executor"):
        selected = stage_root / child
        if not selected.is_dir() or selected.is_symlink():
            raise MigrationSafetyError("runtime publish stage is incomplete or aliased")
    if runtime_root.exists() or runtime_root.is_symlink():
        raise MigrationSafetyError("runtime publish root already exists")

    stage_stat = stage_root.stat()
    stage_identity = (stage_stat.st_dev, stage_stat.st_ino)

    if stage_stat.st_dev != runtime_root.parent.stat().st_dev:
        raise MigrationSafetyError("runtime stage and target are not on one filesystem")

    try:
        rename(stage_root, runtime_root)
    except BaseException as exc:
        stage_present = stage_root.exists() or stage_root.is_symlink()
        runtime_present = runtime_root.exists() or runtime_root.is_symlink()

        # rename() may already have committed atomically before Python observed
        # an interrupt/exception. Reconcile against the original staging inode.
        if runtime_present and not stage_present:
            if runtime_root.is_symlink() or not runtime_root.is_dir():
                raise MigrationSafetyError(
                    "atomic runtime-root publication state is ambiguous; Human review required"
                ) from exc

            published_stat = runtime_root.stat()
            if (published_stat.st_dev, published_stat.st_ino) != stage_identity:
                raise MigrationSafetyError(
                    "atomic runtime-root publication state is ambiguous; Human review required"
                ) from exc

            for child in ("1pcloop-reviewer", "1pcloop-executor"):
                selected = runtime_root / child
                if not selected.is_dir() or selected.is_symlink():
                    raise MigrationSafetyError(
                        "atomic runtime-root publication state is ambiguous; Human review required"
                    ) from exc
            return

        if stage_present and not runtime_present:
            raise MigrationSafetyError(
                "atomic runtime-root publish failed; staged state remains unpublished"
            ) from exc

        raise MigrationSafetyError(
            "atomic runtime-root publication state is ambiguous; Human review required"
        ) from exc


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    source = subparsers.add_parser("validate-source")
    for name in (
        "source-a", "source-b", "vault-a", "vault-b",
        "reviewer-home", "executor-home",
    ):
        source.add_argument(f"--{name}", type=Path, required=True)

    copied = subparsers.add_parser("validate-copy")
    for name in (
        "source-a", "source-b", "vault-a", "vault-b",
        "target-reviewer", "target-executor",
        "reviewer-home", "executor-home",
    ):
        copied.add_argument(f"--{name}", type=Path, required=True)

    publish = subparsers.add_parser("publish-root")
    for name in ("stage-root", "runtime-root"):
        publish.add_argument(f"--{name}", type=Path, required=True)
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)
    try:
        if args.command == "validate-source":
            validate_source_identities(
                source_a=args.source_a,
                source_b=args.source_b,
                vault_a=args.vault_a,
                vault_b=args.vault_b,
            )
            validate_sqlite_home(
                args.source_b / "config.toml", args.reviewer_home
            )
            validate_sqlite_home(
                args.source_a / "config.toml", args.executor_home
            )
        elif args.command == "validate-copy":
            validate_target_identities(
                source_a=args.source_a,
                source_b=args.source_b,
                target_reviewer=args.target_reviewer,
                target_executor=args.target_executor,
                vault_a=args.vault_a,
                vault_b=args.vault_b,
            )
            validate_sqlite_home(
                args.target_reviewer / "config.toml", args.reviewer_home
            )
            validate_sqlite_home(
                args.target_executor / "config.toml", args.executor_home
            )
        else:
            def interrupted(_signum, _frame):
                raise InterruptedError("pair publish interrupted")

            handled = (signal.SIGINT, signal.SIGTERM, signal.SIGHUP)
            prior = {item: signal.getsignal(item) for item in handled}
            try:
                for item in handled:
                    signal.signal(item, interrupted)
                publish_runtime_root(args.stage_root, args.runtime_root)
            finally:
                for item, handler in prior.items():
                    signal.signal(item, handler)
    except MigrationSafetyError as exc:
        print(f"MIGRATION REFUSED: {exc}", file=os.sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
