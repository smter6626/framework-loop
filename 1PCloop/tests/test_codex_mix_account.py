"""Codex Mix active-account binding and retired-home guard tests."""

import base64
import hashlib
import importlib.util
import json
import os
import sys
import tempfile
import unittest
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
            with ACCOUNT.active_account_environment(
                environment,
                binding=binding,
                role_home=reviewer,
                timeout_seconds=1200,
                paths=paths,
                now=self.NOW,
            ) as (selected, evidence):
                self.assertIn("CODEX_ACCESS_TOKEN", selected)
                self.assertNotIn("CODEX_API_KEY", selected)
                self.assertNotIn("OPENAI_API_KEY", selected)
                self.assertEqual(evidence["account_alias"], "C")
                self.assertNotIn(selected["CODEX_ACCESS_TOKEN"], json.dumps(evidence))
            self.assertEqual((reviewer / "auth.json").read_bytes(), before)
            self.assertTrue(evidence["role_auth_unchanged"])

    def test_turn_environment_restores_unexpected_role_auth_mutation(self):
        with tempfile.TemporaryDirectory() as temporary:
            paths, reviewer, _executor = self.fixture(Path(temporary))
            binding = ACCOUNT.inspect_active_account(paths=paths, now=self.NOW)
            before = (reviewer / "auth.json").read_bytes()
            with self.assertRaisesRegex(
                ACCOUNT.AccountBindingError, "modified the role auth cache"
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
