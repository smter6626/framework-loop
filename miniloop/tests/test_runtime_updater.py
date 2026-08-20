from __future__ import annotations

import hashlib
import re
import shutil
import tempfile
import unittest
from pathlib import Path

from miniloop.runtime_updater import RuntimeInvariantError, RuntimeUpdater


_H2 = re.compile(r"^## ([^\n]+)$", re.MULTILINE)


def section(text: str, name: str) -> str:
    matches = list(_H2.finditer(text))
    for index, match in enumerate(matches):
        if match.group(1) == name:
            end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
            return text[match.start() : end]
    raise AssertionError(f"section not found: {name}")


class RuntimeUpdaterTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        project = Path(__file__).resolve().parents[1]
        source = project / "docs" / "miniloop_runtime.md"
        self.path = Path(self.temporary.name) / "runtime.md"
        shutil.copyfile(source, self.path)
        self.updater = RuntimeUpdater(self.path)
        self.original = self.path.read_text(encoding="utf-8")

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def test_append_done_preserves_history_and_renders_provenance(self) -> None:
        old_done = section(self.original, "Done")
        self.updater.append_done(
            step="Step 9",
            commit="abcdef1234567",
            body="Result and evidence: `artifact.txt`.",
        )
        updated = self.path.read_text(encoding="utf-8")
        new_done = section(updated, "Done")
        self.assertIn(old_done.split("\n---\n")[0], new_done)
        self.assertIn("- Step: `Step 9`", new_done)
        self.assertIn("- Commit: `abcdef1234567`", new_done)
        self.assertEqual(
            section(updated, "Other Notes"), section(self.original, "Other Notes")
        )

    def test_other_notes_are_append_only_with_provenance(self) -> None:
        old_other = section(self.original, "Other Notes")
        self.updater.append_other_note(
            step="Step 1",
            commit="1234567abcdef",
            body="Supersedes an earlier implementation observation.",
        )
        updated = self.path.read_text(encoding="utf-8")
        new_other = section(updated, "Other Notes")
        self.assertIn(old_other.split("\n---\n")[0], new_other)
        self.assertIn("Provenance:", new_other)
        self.assertIn("- Commit: `1234567abcdef`", new_other)

    def test_mutable_sections_change_without_touching_done(self) -> None:
        old_done = section(self.original, "Done")
        old_other = section(self.original, "Other Notes")
        digest = self.updater.digest()
        next_digest = self.updater.replace_active_step(
            body="### Step X\n\nStatus: `ACTIVE`", expected_sha256=digest
        )
        updated = self.path.read_text(encoding="utf-8")
        self.assertEqual(section(updated, "Done"), old_done)
        self.assertEqual(section(updated, "Other Notes"), old_other)
        self.assertIn("### Step X", section(updated, "Active Step"))
        self.assertEqual(next_digest, hashlib.sha256(updated.encode()).hexdigest())

    def test_pending_add_progress_and_close_are_explicit(self) -> None:
        task = "### Docker daemon\n\nStatus: `PENDING`"
        self.updater.append_pending_task(body=task)
        progressed = "### Docker daemon\n\nStatus: `IN_PROGRESS`"
        self.updater.progress_pending_task(expected=task, replacement=progressed)
        self.updater.close_pending_task(
            expected=progressed,
            closure="Daemon evidence verified in `docker-info.txt`.",
        )
        pending = section(self.path.read_text(encoding="utf-8"), "Pending Tasks")
        self.assertIn(progressed, pending)
        self.assertIn("Status: `CLOSED`", pending)
        self.assertIn("Closure record:", pending)

    def test_stale_digest_and_missing_pending_target_do_not_write(self) -> None:
        with self.assertRaises(RuntimeInvariantError):
            self.updater.replace_next_steps(body="1. New", expected_sha256="0" * 64)
        self.assertEqual(self.path.read_text(encoding="utf-8"), self.original)
        with self.assertRaises(RuntimeInvariantError):
            self.updater.close_pending_task(expected="not present", closure="none")
        self.assertEqual(self.path.read_text(encoding="utf-8"), self.original)

    def test_provenance_and_section_injection_are_mechanically_rejected(self) -> None:
        with self.assertRaises(RuntimeInvariantError):
            self.updater.append_done(step="Step 2", commit="working-tree", body="x")
        with self.assertRaises(RuntimeInvariantError):
            self.updater.append_other_note(
                step="Step 2", commit="abcdef1", body="safe\n## Done\nrewrite"
            )
        self.assertEqual(self.path.read_text(encoding="utf-8"), self.original)


if __name__ == "__main__":
    unittest.main()
