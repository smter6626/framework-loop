"""Codex Mix active-account binding and retired-home guard tests."""

import base64
import hashlib
import importlib.util
import json
import os
import sys
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "codex_mix_account", ROOT / "scripts/codex_mix_account.py"
)
assert SPEC is not None and SPEC.loader is not None
ACCOUNT = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = ACCOUNT
SPEC.loader.exec_module(ACCOUNT)


class CodexMixAccountTests(unittest.TestCase):
    NOW = 2_000_000_000

    @staticmethod
    def jwt(expiry: int, marker: str) -> str:
        def encode(value):
            raw = json.dumps(value, separators=(",", ":")).encode("utf-8")
            return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")

        return f"{encode({'alg': 'none'})}.{encode({'exp': expiry, 'm': marker})}.sig"

    def write_auth(self, path: Path, identity: str, *, expiry: int = None):
        selected_expiry = expiry or (self.NOW + 7200)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps({
                "tokens": {
                    "account_id": identity,
                    "access_token": self.jwt(selected_expiry, identity),
                    "refresh_token": f"refresh-{identity}",
                    "id_token": f"id-{identity}",
                }
            }) + "\n",
            encoding="utf-8",
        )

    def fixture(self, root: Path):
        paths = ACCOUNT.CodexMixPaths.from_user_home(root)
        paths.canonical_home.mkdir()
        paths.control_root.mkdir()
        paths.accounts_root.mkdir()
        paths.runtime_root.mkdir()
        paths.codex_route.symlink_to(paths.canonical_home)

        for alias in ("A", "B", "C", "D"):
            self.write_auth(
                paths.accounts_root / alias / "auth.json",
                f"account-{alias}",
            )
        self.write_auth(paths.active_auth, "account-C")
        paths.active_marker.write_text(
            json.dumps({"version": 1, "active_account": "C"}) + "\n",
            encoding="utf-8",
        )

        for alias in ("A", "B"):
            historical = root / f".codex-{alias}"
            historical.mkdir()
            self.write_auth(historical / "auth.json", f"account-{alias}")
            (historical / "config.toml").write_text(
                f"model = 'fixture-{alias}'\n", encoding="utf-8"
            )
            for name in ACCOUNT.IMMUTABLE_SENTINELS:
                (historical / name).write_text(
                    f"{alias}:{name}\n", encoding="utf-8"
                )
            (historical / "sessions").mkdir()
            (historical / "archived_sessions").mkdir()

        paths.baseline_file.write_text(
            json.dumps(
                ACCOUNT.capture_original_baseline(paths),
                indent=2,
                sort_keys=True,
            ) + "\n",
            encoding="utf-8",
        )
        paths.retired_snapshot.parent.mkdir(parents=True)
        paths.retired_snapshot.write_text(
            json.dumps(
                ACCOUNT.capture_retired_tree(paths),
                indent=2,
                sort_keys=True,
            ) + "\n",
            encoding="utf-8",
        )

        reviewer = paths.runtime_root / "1pcloop-reviewer"
        executor = paths.runtime_root / "1pcloop-executor"
        reviewer.mkdir()
        executor.mkdir()
        self.write_auth(reviewer / "auth.json", "account-B")
        self.write_auth(executor / "auth.json", "account-A")
        (reviewer / "config.toml").write_text(
            "model = 'reviewer'\n", encoding="utf-8"
        )
        (executor / "config.toml").write_text(
            "model = 'executor'\n", encoding="utf-8"
        )
        return paths, reviewer, executor

    def test_active_binding_is_marker_vault_projection_without_token_leakage(self):
        with tempfile.TemporaryDirectory() as temporary:
            paths, _reviewer, _executor = self.fixture(Path(temporary))
            binding = ACCOUNT.inspect_active_account(
                paths=paths,
                minimum_ttl_seconds=1200,
                now=self.NOW,
            )
            self.assertEqual(binding.alias, "C")
            self.assertEqual(
                binding.account_id_sha256,
                hashlib.sha256(b"account-C").hexdigest(),
            )
            rendered = json.dumps(binding.preflight_metadata(now=self.NOW))
            self.assertNotIn("refresh-account", rendered)
            self.assertNotIn(self.jwt(self.NOW + 7200, "account-C"), rendered)
            self.assertNotIn("id-account", rendered)

    def test_active_binding_rejects_marker_projection_and_baseline_drift(self):
        with tempfile.TemporaryDirectory() as temporary:
            paths, _reviewer, _executor = self.fixture(Path(temporary))
            paths.active_marker.write_text(
                json.dumps({"version": 1, "active_account": "D"}) + "\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(
                ACCOUNT.AccountBindingError, "marker.*vault"
            ):
                ACCOUNT.inspect_active_account(paths=paths, now=self.NOW)

    def test_full_retirement_snapshot_rejects_non_sentinel_drift(self):
        with tempfile.TemporaryDirectory() as temporary:
            paths, _reviewer, _executor = self.fixture(Path(temporary))
            ordinary = paths.user_home / ".codex-A" / "ordinary-cache.txt"
            ordinary.write_text("new file\n", encoding="utf-8")
            with self.assertRaisesRegex(
                ACCOUNT.AccountBindingError, "full-tree snapshot changed"
            ):
                ACCOUNT.inspect_active_account(paths=paths, now=self.NOW)

            paths.active_marker.write_text(
                json.dumps({"version": 1, "active_account": "C"}) + "\n",
                encoding="utf-8",
            )
            retired = paths.user_home / ".codex-A" / "state_5.sqlite"
            retired.write_text("drift\n", encoding="utf-8")
            with self.assertRaisesRegex(
                ACCOUNT.AccountBindingError, "immutable baseline changed"
            ):
                ACCOUNT.inspect_active_account(paths=paths, now=self.NOW)

    def test_active_binding_rejects_short_lived_token(self):
        with tempfile.TemporaryDirectory() as temporary:
            paths, _reviewer, _executor = self.fixture(Path(temporary))
            self.write_auth(
                paths.active_auth,
                "account-C",
                expiry=self.NOW + 100,
            )
            with self.assertRaisesRegex(
                ACCOUNT.AccountBindingError, "lifetime"
            ):
                ACCOUNT.inspect_active_account(
                    paths=paths,
                    minimum_ttl_seconds=1200,
                    now=self.NOW,
                )

    def test_turn_environment_pins_account_and_preserves_role_auth(self):
        with tempfile.TemporaryDirectory() as temporary:
            paths, reviewer, _executor = self.fixture(Path(temporary))
            binding = ACCOUNT.inspect_active_account(paths=paths, now=self.NOW)
            before = (reviewer / "auth.json").read_bytes()
            environment = {
                "PATH": os.environ.get("PATH", ""),
                "CODEX_API_KEY": "wrong-source",
                "OPENAI_API_KEY": "wrong-source",
            }
            original_mode = (reviewer / "auth.json").stat().st_mode & 0o777
            with ACCOUNT.active_account_environment(
                environment,
                binding=binding,
                role_home=reviewer,
                timeout_seconds=1200,
                paths=paths,
                now=self.NOW,
            ) as (selected, evidence, transaction):
                self.assertNotIn("CODEX_ACCESS_TOKEN", selected)
                self.assertNotIn("CODEX_API_KEY", selected)
                self.assertNotIn("OPENAI_API_KEY", selected)
                self.assertEqual(evidence["account_alias"], "C")
                self.assertEqual(
                    json.loads((reviewer / "auth.json").read_text())["tokens"]["account_id"],
                    "account-C",
                )
                self.assertEqual(transaction.record["state"], "PROJECTED")
            self.assertEqual((reviewer / "auth.json").read_bytes(), before)
            self.assertEqual((reviewer / "auth.json").stat().st_mode & 0o777, original_mode)
            self.assertTrue(evidence["role_auth_restored"])
            self.assertTrue(evidence["active_identity_unchanged"])
            self.assertEqual(evidence["credential_scan"]["actual_credential_hits"], 0)
            self.assertFalse(any(
                item.is_dir() for item in paths.transactions_root.iterdir()
                if item.name != ".locks"
            ))

    def test_turn_environment_restores_unexpected_role_auth_mutation(self):
        with tempfile.TemporaryDirectory() as temporary:
            paths, reviewer, _executor = self.fixture(Path(temporary))
            binding = ACCOUNT.inspect_active_account(paths=paths, now=self.NOW)
            before = (reviewer / "auth.json").read_bytes()
            with self.assertRaisesRegex(
                ACCOUNT.AccountBindingError, "credential transaction recovery failed"
            ):
                with ACCOUNT.active_account_environment(
                    {},
                    binding=binding,
                    role_home=reviewer,
                    timeout_seconds=1200,
                    paths=paths,
                    now=self.NOW,
                ):
                    (reviewer / "auth.json").write_text(
                        "unexpected mutation\n", encoding="utf-8"
                    )
            self.assertEqual((reviewer / "auth.json").read_bytes(), before)

    def test_secret_scan_fails_without_printing_secret_and_restores(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            paths, reviewer, _executor = self.fixture(root)
            binding = ACCOUNT.inspect_active_account(paths=paths, now=self.NOW)
            before = (reviewer / "auth.json").read_bytes()
            leak_root = root / "outputs"
            leak_root.mkdir()
            secret = json.loads(paths.active_auth.read_text())["tokens"]["refresh_token"]
            with self.assertRaisesRegex(
                ACCOUNT.AccountBindingError, "credential exposure detected"
            ) as raised:
                with ACCOUNT.active_account_environment(
                    {}, binding=binding, role_home=reviewer,
                    timeout_seconds=1200, paths=paths, now=self.NOW,
                    scan_roots=(leak_root,),
                ):
                    (leak_root / "stderr.txt").write_text(secret, encoding="utf-8")
            self.assertNotIn(secret, str(raised.exception))
            self.assertIn("stderr.txt", str(raised.exception))
            self.assertEqual((reviewer / "auth.json").read_bytes(), before)

    def test_stale_projected_transaction_recovers_when_child_is_gone(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            paths, reviewer, _executor = self.fixture(root)
            original = (reviewer / "auth.json").read_bytes()
            mode = (reviewer / "auth.json").stat().st_mode & 0o777
            mtime = (reviewer / "auth.json").stat().st_mtime_ns
            paths.transactions_root.mkdir(parents=True)
            transaction = paths.transactions_root / "fixture-reviewer"
            transaction.mkdir(mode=0o700)
            backup = transaction / "original-role-auth.json"
            backup.write_bytes(original)
            os.chmod(backup, 0o600)
            (reviewer / "auth.json").write_bytes(paths.active_auth.read_bytes())
            record = {
                "schema_version": 1,
                "transaction_id": "fixture-reviewer",
                "run_id": "fixture-run",
                "turn": "reviewer-instruction",
                "role": "reviewer",
                "account_alias": "C",
                "account_id_sha256": hashlib.sha256(b"account-C").hexdigest(),
                "role_auth_original_sha256": hashlib.sha256(original).hexdigest(),
                "role_auth_original_mode": mode,
                "role_auth_original_mtime_ns": mtime,
                "state": "PROJECTED",
                "started_at_ns": 1,
            }
            (transaction / "transaction.json").write_text(
                json.dumps(record), encoding="utf-8"
            )
            recovered = ACCOUNT.recover_incomplete_transactions(paths=paths)
            self.assertEqual(recovered, 1)
            self.assertEqual((reviewer / "auth.json").read_bytes(), original)
            self.assertFalse(transaction.exists())

    def test_stale_transaction_with_matching_live_child_fails_closed(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            paths, reviewer, _executor = self.fixture(root)
            original = (reviewer / "auth.json").read_bytes()
            paths.transactions_root.mkdir(parents=True)
            transaction = paths.transactions_root / "fixture-live"
            transaction.mkdir(mode=0o700)
            (transaction / "original-role-auth.json").write_bytes(original)
            record = {
                "schema_version": 1,
                "transaction_id": "fixture-live",
                "run_id": "fixture-run",
                "turn": "reviewer-instruction",
                "role": "reviewer",
                "account_alias": "C",
                "account_id_sha256": hashlib.sha256(b"account-C").hexdigest(),
                "role_auth_original_sha256": hashlib.sha256(original).hexdigest(),
                "role_auth_original_mode": 0o644,
                "role_auth_original_mtime_ns": (reviewer / "auth.json").stat().st_mtime_ns,
                "state": "CHILD_RUNNING",
                "started_at_ns": 1,
                "child_pid": 123,
                "child_pgid": 123,
                "child_started_at": "fixture",
                "child_executable": "codex",
                "command_fingerprint": "a" * 64,
            }
            (transaction / "transaction.json").write_text(
                json.dumps(record), encoding="utf-8"
            )
            with patch.object(ACCOUNT, "_recorded_child_is_running", return_value=True):
                with self.assertRaisesRegex(
                    ACCOUNT.AccountBindingError, "still running"
                ):
                    ACCOUNT.recover_incomplete_transactions(paths=paths)
            self.assertTrue(transaction.exists())

    def test_crash_state_matrix_recovers_or_fails_closed(self):
        restorable = (
            "INITIALIZED", "PREPARED", "PROJECTED", "CHILD_EXITED",
            "RESTORING", "RESTORED",
        )
        for state in restorable:
            with self.subTest(state=state), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                paths, reviewer, _executor = self.fixture(root)
                original = (reviewer / "auth.json").read_bytes()
                original_stat = (reviewer / "auth.json").stat()
                paths.transactions_root.mkdir(parents=True)
                transaction = paths.transactions_root / f"fixture-{state.lower()}"
                transaction.mkdir(mode=0o700)
                backup = transaction / "original-role-auth.json"
                backup.write_bytes(original)
                os.chmod(backup, 0o600)
                if state not in {"INITIALIZED", "PREPARED", "RESTORED"}:
                    (reviewer / "auth.json").write_bytes(paths.active_auth.read_bytes())
                record = {
                    "schema_version": 1,
                    "transaction_id": transaction.name,
                    "run_id": "fixture-run",
                    "turn": "reviewer-instruction",
                    "role": "reviewer",
                    "account_alias": "C",
                    "account_id_sha256": hashlib.sha256(b"account-C").hexdigest(),
                    "role_auth_original_sha256": hashlib.sha256(original).hexdigest(),
                    "role_auth_original_mode": original_stat.st_mode & 0o777,
                    "role_auth_original_mtime_ns": original_stat.st_mtime_ns,
                    "state": state,
                    "started_at_ns": 1,
                }
                (transaction / "transaction.json").write_text(
                    json.dumps(record), encoding="utf-8"
                )
                self.assertEqual(
                    ACCOUNT.recover_incomplete_transactions(paths=paths), 1
                )
                self.assertEqual((reviewer / "auth.json").read_bytes(), original)
                self.assertFalse(transaction.exists())

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            paths, reviewer, _executor = self.fixture(root)
            paths.transactions_root.mkdir(parents=True)
            transaction = paths.transactions_root / "missing-backup"
            transaction.mkdir(mode=0o700)
            record = {
                "schema_version": 1, "transaction_id": "missing-backup",
                "run_id": "fixture-run", "turn": "reviewer", "role": "reviewer",
                "account_alias": "C", "account_id_sha256": "a" * 64,
                "role_auth_original_sha256": "b" * 64,
                "role_auth_original_mode": 0o600,
                "role_auth_original_mtime_ns": 1,
                "state": "PROJECTED", "started_at_ns": 1,
            }
            (transaction / "transaction.json").write_text(json.dumps(record))
            with self.assertRaisesRegex(
                ACCOUNT.AccountBindingError, "recovery copy is missing"
            ):
                ACCOUNT.recover_incomplete_transactions(paths=paths)
            self.assertTrue((reviewer / "auth.json").is_file())

    def test_python_body_exception_restores_before_reraising(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            paths, reviewer, _executor = self.fixture(root)
            binding = ACCOUNT.inspect_active_account(paths=paths, now=self.NOW)
            before = (reviewer / "auth.json").read_bytes()
            with self.assertRaisesRegex(RuntimeError, "body failed"):
                with ACCOUNT.active_account_environment(
                    {}, binding=binding, role_home=reviewer,
                    timeout_seconds=1200, paths=paths, now=self.NOW,
                ):
                    raise RuntimeError("body failed")
            self.assertEqual((reviewer / "auth.json").read_bytes(), before)

    def test_projection_setup_failure_restores_immediately(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            paths, reviewer, _executor = self.fixture(root)
            binding = ACCOUNT.inspect_active_account(paths=paths, now=self.NOW)
            before = (reviewer / "auth.json").read_bytes()
            original = ACCOUNT._auth_record

            def reject_projected(path, label):
                if label == "projected role credential":
                    raise ACCOUNT.AccountBindingError("injected setup failure")
                return original(path, label)

            with patch.object(ACCOUNT, "_auth_record", side_effect=reject_projected):
                with self.assertRaisesRegex(
                    ACCOUNT.AccountBindingError, "injected setup failure"
                ):
                    with ACCOUNT.active_account_environment(
                        {}, binding=binding, role_home=reviewer,
                        timeout_seconds=1200, paths=paths, now=self.NOW,
                    ):
                        self.fail("body must not start")
            self.assertEqual((reviewer / "auth.json").read_bytes(), before)
            self.assertFalse(any(
                path.is_dir() for path in paths.transactions_root.iterdir()
                if path.name != ".locks"
            ))

    def test_transaction_metadata_permissions_and_no_secret_values(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            paths, reviewer, _executor = self.fixture(root)
            binding = ACCOUNT.inspect_active_account(paths=paths, now=self.NOW)
            secrets = tuple(
                json.loads(paths.active_auth.read_text())["tokens"][name]
                for name in ("access_token", "refresh_token", "id_token")
            )
            with ACCOUNT.active_account_environment(
                {}, binding=binding, role_home=reviewer,
                timeout_seconds=1200, paths=paths, now=self.NOW,
                run_id="safe-run", turn="cycle-01/reviewer", role="reviewer",
            ) as (_environment, _evidence, transaction):
                rendered = transaction.record_path.read_text()
                self.assertEqual(transaction.transaction_dir.stat().st_mode & 0o777, 0o700)
                self.assertEqual(
                    (transaction.transaction_dir / "original-role-auth.json").stat().st_mode & 0o777,
                    0o600,
                )
                for secret in secrets:
                    self.assertNotIn(secret, rendered)
                self.assertNotIn("account-C", rendered)

    def test_role_config_rejects_retired_paths_and_escaped_sqlite_home(self):
        with tempfile.TemporaryDirectory() as temporary:
            paths, reviewer, executor = self.fixture(Path(temporary))
            ACCOUNT.validate_role_runtime_config(reviewer, paths=paths)
            ACCOUNT.validate_role_runtime_config(executor, paths=paths)

            config = reviewer / "config.toml"
            config.write_text(
                f"notify = ['{paths.user_home}/.codex-B/notifier']\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(
                ACCOUNT.AccountBindingError, "retired account B"
            ):
                ACCOUNT.validate_role_runtime_config(reviewer, paths=paths)

            config.write_text(
                f"sqlite_home = '{executor}'\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(
                ACCOUNT.AccountBindingError, "dedicated runtime"
            ):
                ACCOUNT.validate_role_runtime_config(reviewer, paths=paths)

            config.write_text(
                f"sqlite_home = '{reviewer}'\n",
                encoding="utf-8",
            )
            ACCOUNT.validate_role_runtime_config(reviewer, paths=paths)


if __name__ == "__main__":
    unittest.main()
