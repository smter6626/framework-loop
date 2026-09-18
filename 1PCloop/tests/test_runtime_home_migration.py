"""Migration-ready Codex runtime-home policy and tooling tests."""

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MIGRATION = ROOT / "scripts/migrate_codex_mix_runtime_homes.sh"
GUIDE = ROOT / "docs/codex-runtime-homes/README.md"
CONFIGS = (
    ROOT / "workloads/whisper_session_ui_v1/feature_ui.json",
    ROOT / "workloads/whisper_session_ui_v1/main_docs.json",
    ROOT / "workloads/whisper_window_layout_v1/window_layout.json",
)
REVIEWER = "/Users/smterpro/.codex-mix/.mix/runtimes/1pcloop-reviewer"
EXECUTOR = "/Users/smterpro/.codex-mix/.mix/runtimes/1pcloop-executor"

HELPER_SPEC = importlib.util.spec_from_file_location(
    "codex_runtime_migration", ROOT / "scripts/codex_runtime_migration.py"
)
assert HELPER_SPEC is not None and HELPER_SPEC.loader is not None
HELPER = importlib.util.module_from_spec(HELPER_SPEC)
sys.modules[HELPER_SPEC.name] = HELPER
HELPER_SPEC.loader.exec_module(HELPER)


class RuntimeHomeMigrationTests(unittest.TestCase):
    def test_migration_script_is_valid_and_requires_explicit_execution(self):
        subprocess.run(["bash", "-n", str(MIGRATION)], check=True)
        source = MIGRATION.read_text(encoding="utf-8")
        self.assertIn('MODE="${1:---check-only}"', source)
        self.assertIn('[[ ! -e "$target" && ! -L "$target" ]]', source)
        self.assertIn("ditto --rsrc --extattr --acl", source)
        self.assertIn("manifest_protected_canonical_state", source)
        self.assertIn('root.glob("*.sqlite*")', source)
        for protected in (
            ".codex-global-state.json", "sessions", "archived_sessions",
            "installation_id", "auth.json", "config.toml", ".mix/accounts",
        ):
            self.assertIn(protected, source)
        self.assertIn('validate-source', source)
        self.assertIn('validate-copy', source)
        self.assertIn('publish-root', source)
        self.assertNotIn('mv "$STAGE/1pcloop-reviewer" "$REVIEWER_TARGET"', source)
        self.assertNotIn('mv "$STAGE/1pcloop-executor" "$EXECUTOR_TARGET"', source)
        self.assertNotIn("rebaseline", source.lower())

    @staticmethod
    def write_auth(path: Path, identity: str):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps({"tokens": {"account_id": identity}}) + "\n",
            encoding="utf-8",
        )

    def identity_fixture(self, root: Path):
        source_a = root / "source-A"
        source_b = root / "source-B"
        target_reviewer = root / "target-reviewer"
        target_executor = root / "target-executor"
        vault_a = root / "vault/A/auth.json"
        vault_b = root / "vault/B/auth.json"
        for home in (source_a, source_b, target_reviewer, target_executor):
            home.mkdir(parents=True)
        self.write_auth(source_a / "auth.json", "account-A")
        self.write_auth(source_b / "auth.json", "account-B")
        self.write_auth(target_reviewer / "auth.json", "account-B")
        self.write_auth(target_executor / "auth.json", "account-A")
        self.write_auth(vault_a, "account-A")
        self.write_auth(vault_b, "account-B")
        return source_a, source_b, target_reviewer, target_executor, vault_a, vault_b

    def test_source_and_copied_target_account_identities_are_exact_and_distinct(self):
        with tempfile.TemporaryDirectory() as temporary:
            values = self.identity_fixture(Path(temporary))
            source_a, source_b, reviewer, executor, vault_a, vault_b = values
            HELPER.validate_source_identities(
                source_a=source_a, source_b=source_b,
                vault_a=vault_a, vault_b=vault_b,
            )
            HELPER.validate_target_identities(
                source_a=source_a, source_b=source_b,
                target_reviewer=reviewer, target_executor=executor,
                vault_a=vault_a, vault_b=vault_b,
            )

            self.write_auth(vault_a, "wrong-A")
            with self.assertRaisesRegex(HELPER.MigrationSafetyError, "source A"):
                HELPER.validate_source_identities(
                    source_a=source_a, source_b=source_b,
                    vault_a=vault_a, vault_b=vault_b,
                )
            self.write_auth(vault_a, "account-A")
            self.write_auth(source_b / "auth.json", "account-A")
            self.write_auth(vault_b, "account-A")
            with self.assertRaisesRegex(HELPER.MigrationSafetyError, "not distinct"):
                HELPER.validate_source_identities(
                    source_a=source_a, source_b=source_b,
                    vault_a=vault_a, vault_b=vault_b,
                )

    def test_copied_target_identity_mismatch_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            values = self.identity_fixture(Path(temporary))
            source_a, source_b, reviewer, executor, vault_a, vault_b = values
            self.write_auth(reviewer / "auth.json", "account-A")
            with self.assertRaisesRegex(
                HELPER.MigrationSafetyError, "Reviewer target"
            ):
                HELPER.validate_target_identities(
                    source_a=source_a, source_b=source_b,
                    target_reviewer=reviewer, target_executor=executor,
                    vault_a=vault_a, vault_b=vault_b,
                )

    def test_sqlite_home_must_be_absent_or_exact_role_runtime(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            config = root / "config.toml"
            expected = root / "role-runtime"
            config.write_text("model = 'gpt-test'\n", encoding="utf-8")
            HELPER.validate_sqlite_home(config, expected)

            config.write_text(
                f"sqlite_home = {json.dumps(str(expected))}\n", encoding="utf-8"
            )
            HELPER.validate_sqlite_home(config, expected)

            for unsafe in (
                "/Users/smterpro/.codex-A", str(root / "other"), "relative/state"
            ):
                with self.subTest(unsafe=unsafe):
                    config.write_text(
                        f"sqlite_home = {json.dumps(unsafe)}\n", encoding="utf-8"
                    )
                    with self.assertRaises(HELPER.MigrationSafetyError):
                        HELPER.validate_sqlite_home(config, expected)

    def test_runtime_root_publish_is_single_and_failure_leaves_no_target(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            stage = root / ".runtime-stage"
            runtime_root = root / "runtimes"
            stage.mkdir()
            (stage / "1pcloop-reviewer").mkdir()
            (stage / "1pcloop-executor").mkdir()

            def fail_publish(_source, _destination):
                raise OSError("simulated atomic publish failure")

            with self.assertRaisesRegex(
                HELPER.MigrationSafetyError, "remains unpublished"
            ):
                HELPER.publish_runtime_root(
                    stage, runtime_root, rename=fail_publish
                )
            self.assertTrue((stage / "1pcloop-reviewer").is_dir())
            self.assertTrue((stage / "1pcloop-executor").is_dir())
            self.assertFalse(runtime_root.exists())

            HELPER.publish_runtime_root(stage, runtime_root)
            self.assertTrue((runtime_root / "1pcloop-reviewer").is_dir())
            self.assertTrue((runtime_root / "1pcloop-executor").is_dir())
            self.assertFalse(stage.exists())

    def test_tracked_workloads_use_dedicated_runtime_homes(self):
        for path in CONFIGS:
            with self.subTest(path=path):
                profiles = json.loads(path.read_text(encoding="utf-8"))["profiles"]
                self.assertEqual(profiles["reviewer_home"], REVIEWER)
                self.assertEqual(profiles["executor_home"], EXECUTOR)

    def test_guide_records_identity_role_and_checkpoint_boundaries(self):
        text = GUIDE.read_text(encoding="utf-8")
        for required in (
            "A、B、C、D 只表示 account identity",
            "historical source",
            "checkpoint.configuration.reviewer_home",
            "checkpoint.configuration.executor_home",
            "checkpoint.run_configuration.reviewer_home",
            "reviewer_state.reviewer_thread_id",
            "不得改写旧 process receipt",
        ):
            with self.subTest(required=required):
                self.assertIn(required, text)


if __name__ == "__main__":
    unittest.main()
