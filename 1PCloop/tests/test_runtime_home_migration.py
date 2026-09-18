"""Migration-ready Codex runtime-home policy and tooling tests."""

import json
import subprocess
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


class RuntimeHomeMigrationTests(unittest.TestCase):
    def test_migration_script_is_valid_and_requires_explicit_execution(self):
        subprocess.run(["bash", "-n", str(MIGRATION)], check=True)
        source = MIGRATION.read_text(encoding="utf-8")
        self.assertIn('MODE="${1:---check-only}"', source)
        self.assertIn('[[ ! -e "$target" && ! -L "$target" ]]', source)
        self.assertIn("ditto --rsrc --extattr --acl", source)
        self.assertIn("manifest_protected_canonical_state", source)
        self.assertNotIn("rebaseline", source.lower())

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
