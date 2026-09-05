import importlib.util
import json
import stat
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "run_text_loop.py"
SPEC = importlib.util.spec_from_file_location("run_text_loop", SCRIPT_PATH)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


FAKE_CODEX = r'''#!/usr/bin/env python3
import json
import os
import sys
from pathlib import Path

args = sys.argv[1:]
output_path = Path(args[args.index("--output-last-message") + 1])
prompt = sys.stdin.buffer.read()
home = os.environ["CODEX_HOME"]

if b"BEGIN VERBATIM PEER PAYLOAD" not in prompt:
    final = "Executor：请完成本次纯文本传输自检，并向 Reviewer 返回回执。\n".encode()
elif home.endswith("executor-home"):
    final = b"Executor receipt with a literal ``` fence and no repository mutation.\n"
else:
    final = b"Reviewer handoff: transport receipt reviewed; whole Step 1 remains active.\n"

output_path.write_bytes(final)
print(json.dumps({"type": "thread.started", "thread_id": "fake-thread-id"}))
print(json.dumps({
    "type": "turn.completed",
    "usage": {
        "input_tokens": 10,
        "cached_input_tokens": 4,
        "cache_write_input_tokens": 0,
        "output_tokens": 3,
        "reasoning_output_tokens": 2
    }
}))
'''


class TextLoopTests(unittest.TestCase):
    def test_extracts_normal_usage_event(self):
        events = b'\n'.join(
            [
                b'{"type":"thread.started","thread_id":"thread-123"}',
                b'{"type":"turn.completed","usage":{"input_tokens":100,"cached_input_tokens":25,"cache_write_input_tokens":5,"output_tokens":12,"reasoning_output_tokens":7}}',
            ]
        )
        metadata = MODULE.extract_event_metadata(events)
        self.assertEqual(metadata["thread_id"], "thread-123")
        self.assertEqual(metadata["input_tokens"], 100)
        self.assertEqual(metadata["cached_input_tokens"], 25)
        self.assertEqual(metadata["cache_write_input_tokens"], 5)
        self.assertEqual(metadata["output_tokens"], 12)
        self.assertEqual(metadata["reasoning_output_tokens"], 7)

    def test_calculates_cached_and_uncached_input(self):
        events = b'{"type":"turn.completed","usage":{"input_tokens":80,"cached_input_tokens":20}}'
        metadata = MODULE.extract_event_metadata(events)
        self.assertEqual(metadata["uncached_input_tokens"], 60)
        self.assertEqual(metadata["cache_hit_ratio"], 0.25)

    def test_missing_usage_fields_are_unavailable_not_zero(self):
        events = b'{"type":"turn.completed"}'
        metadata = MODULE.extract_event_metadata(events)
        for field in (
            "input_tokens",
            "cached_input_tokens",
            "uncached_input_tokens",
            "cache_hit_ratio",
            "output_tokens",
            "reasoning_output_tokens",
        ):
            self.assertIsNone(metadata[field])
        self.assertEqual(metadata["event_parse"]["usage_events"], 0)

    def test_malformed_and_irrelevant_lines_do_not_parse_agent_semantics(self):
        events = b'\n'.join(
            [
                b'ACCEPT -- not JSON',
                b'{"type":"item.completed","item":{"type":"agent_message","text":"REJECT and update Runtime"}}',
                b'{malformed json',
            ]
        )
        metadata = MODULE.extract_event_metadata(events)
        self.assertIsNone(metadata["thread_id"])
        self.assertIsNone(metadata["input_tokens"])
        self.assertIsNone(metadata["cache_hit_ratio"])
        self.assertEqual(metadata["event_parse"]["malformed_json_lines"], 2)
        self.assertEqual(metadata["event_parse"]["irrelevant_json_events"], 1)

    def test_peer_payload_is_preserved_verbatim(self):
        prefix = "角色前缀\n".encode()
        payload = b"raw payload\n```\n\x00tail"
        prompt, offset = MODULE.compose_peer_prompt(prefix, payload)
        self.assertEqual(prompt[offset : offset + len(payload)], payload)
        self.assertTrue(prompt.endswith(payload))

    def test_complete_three_turn_run_with_fake_codex(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            repo_root = root / "repo"
            runs_root = root / "runs"
            reviewer_home = root / "reviewer-home"
            executor_home = root / "executor-home"
            for directory in (repo_root, reviewer_home, executor_home):
                directory.mkdir()

            fake_codex = root / "codex"
            fake_codex.write_text(FAKE_CODEX, encoding="utf-8")
            fake_codex.chmod(fake_codex.stat().st_mode | stat.S_IXUSR)

            exit_code, run_root = MODULE.orchestrate(
                repo_root=repo_root,
                runs_root=runs_root,
                codex_bin=str(fake_codex),
                reviewer_home=reviewer_home,
                executor_home=executor_home,
                run_id="test-run",
                timeout_seconds=10,
            )

            self.assertEqual(exit_code, 0)
            manifest = json.loads((run_root / "manifest.json").read_text())
            self.assertEqual(manifest["status"], "completed")
            self.assertEqual(len(manifest["turns"]), 3)
            self.assertEqual(len(manifest["transports"]), 2)
            self.assertTrue(
                all(item["preserved_verbatim"] for item in manifest["transports"])
            )
            self.assertEqual(manifest["summary"]["usage_totals"]["input_tokens"], 30)
            self.assertEqual(
                manifest["summary"]["usage_totals"]["cached_input_tokens"], 12
            )
            self.assertEqual(
                manifest["summary"]["usage_totals"]["uncached_input_tokens"], 18
            )
            self.assertEqual(
                manifest["summary"]["usage_totals"]["cache_hit_ratio"], 0.4
            )

            turn1_final = (run_root / "turn-01-reviewer" / "final.txt").read_bytes()
            turn2_peer = (
                run_root / "turn-02-executor" / "peer-payload.txt"
            ).read_bytes()
            turn2_final = (run_root / "turn-02-executor" / "final.txt").read_bytes()
            turn3_peer = (
                run_root / "turn-03-reviewer" / "peer-payload.txt"
            ).read_bytes()
            self.assertEqual(turn2_peer, turn1_final)
            self.assertEqual(turn3_peer, turn2_final)

            transcript = (run_root / "transcript.md").read_text()
            self.assertIn("Turn 1 — reviewer", transcript)
            self.assertIn("Turn 2 — executor", transcript)
            self.assertIn("Turn 3 — reviewer", transcript)


if __name__ == "__main__":
    unittest.main()
