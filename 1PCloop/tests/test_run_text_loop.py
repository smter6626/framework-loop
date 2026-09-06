import importlib.util
import hashlib
import json
import stat
import subprocess
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
binary_name = Path(sys.argv[0]).name
is_resume = "resume" in args

if home.endswith("executor-home"):
    if "runtime-change" in binary_name:
        runtime_path = Path.cwd() / "1PCloop/docs/miniloop_runtime.md"
        runtime_path.write_bytes(runtime_path.read_bytes() + b"runtime growth after T1\n")
    if "static-change" in binary_name:
        static_path = Path.cwd() / "1PCloop/docs/miniloop_static.md"
        static_path.write_bytes(static_path.read_bytes() + b"static growth after T1\n")

with Path(sys.argv[0]).with_suffix(".calls").open("a", encoding="utf-8") as calls:
    calls.write(json.dumps(args) + "\n")

if is_resume and "resume-failure" in binary_name:
    print(json.dumps({"type": "error", "message": "forced resume failure"}))
    sys.exit(7)

if b"BEGIN VERBATIM PEER PAYLOAD" not in prompt:
    final = "Executor：请完成本次纯文本传输自检，并向 Reviewer 返回回执。\n".encode()
elif home.endswith("executor-home"):
    final = b"Executor receipt with a literal ``` fence and no repository mutation.\n"
else:
    final = b"Reviewer handoff: transport receipt reviewed; whole Step 1 remains active.\n"

output_path.write_bytes(final)
thread_id = args[args.index("resume") + 1] if is_resume else "fake-thread-id"
if is_resume and "resume-mismatch" in binary_name:
    thread_id = "wrong-thread-id"
is_persistent_create = not is_resume and "--ephemeral" not in args
if not (is_persistent_create and "missing-thread" in binary_name):
    print(json.dumps({"type": "thread.started", "thread_id": thread_id}))
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
    def run_fake_loop(self, root, *, binary_name="codex", session_mode=None):
        repo_root = root / "repo"
        runs_root = root / "runs"
        reviewer_home = root / "reviewer-home"
        executor_home = root / "executor-home"
        for directory in (repo_root, reviewer_home, executor_home):
            directory.mkdir()
        docs_root = repo_root / "1PCloop/docs"
        roles_root = repo_root / "1PCloop/roles"
        docs_root.mkdir(parents=True)
        roles_root.mkdir(parents=True)
        (docs_root / "miniloop_static.md").write_bytes(
            b"# Static\ncomplete static tail\n"
        )
        (docs_root / "miniloop_runtime.md").write_bytes(
            b"# Runtime\ncomplete runtime tail\n"
        )
        (roles_root / "reviewer-initial.md").write_bytes(b"reviewer initial\n")
        (roles_root / "executor.md").write_bytes(b"executor\n")
        (roles_root / "reviewer-review.md").write_bytes(b"reviewer review\n")
        subprocess.run(["git", "init", "-q"], cwd=repo_root, check=True)
        subprocess.run(["git", "add", "1PCloop"], cwd=repo_root, check=True)
        subprocess.run(
            [
                "git",
                "-c",
                "user.name=1PCloop Test",
                "-c",
                "user.email=1pcloop@example.invalid",
                "commit",
                "-qm",
                "fixture",
            ],
            cwd=repo_root,
            check=True,
        )

        fake_codex = root / binary_name
        fake_codex.write_text(FAKE_CODEX, encoding="utf-8")
        fake_codex.chmod(fake_codex.stat().st_mode | stat.S_IXUSR)
        kwargs = {}
        if session_mode is not None:
            kwargs["session_mode"] = session_mode
        exit_code, run_root = MODULE.orchestrate(
            repo_root=repo_root,
            runs_root=runs_root,
            codex_bin=str(fake_codex),
            reviewer_home=reviewer_home,
            executor_home=executor_home,
            run_id="test-run",
            timeout_seconds=10,
            **kwargs,
        )
        return exit_code, run_root, fake_codex

    def test_profile_metadata_exposes_only_selected_config_fields(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            home = Path(temporary_directory)
            (home / "config.toml").write_text(
                'model = "test-model"\n'
                'model_reasoning_effort = "high"\n'
                'api_key = "must-not-appear"\n',
                encoding="utf-8",
            )
            (home / "auth.json").write_text("must-not-be-read", encoding="utf-8")

            metadata = MODULE.profile_config_metadata(home)
            self.assertEqual(metadata["model"], "test-model")
            self.assertEqual(metadata["model_reasoning_effort"], "high")
            self.assertNotIn("must-not-appear", json.dumps(metadata))
            self.assertNotIn("must-not-be-read", json.dumps(metadata))

    def test_frozen_experiment_enforces_control_then_treatment(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            experiment_file = root / "experiment.json"
            frozen = {"git_head": "abc123", "runtime_sha256": "def456"}

            control, control_index = MODULE.prepare_experiment(
                experiment_file=experiment_file,
                experiment_id="p4a-test",
                session_mode=MODULE.CONTROL_MODE,
                run_id="control",
                runs_root=root,
                frozen_context=frozen,
            )
            self.assertEqual(control_index, 0)
            self.assertEqual(control["run_order_index"], 1)

            document = json.loads(experiment_file.read_text())
            document["runs"][0]["status"] = "completed"
            experiment_file.write_text(json.dumps(document), encoding="utf-8")
            treatment, treatment_index = MODULE.prepare_experiment(
                experiment_file=experiment_file,
                experiment_id="p4a-test",
                session_mode=MODULE.TREATMENT_MODE,
                run_id="treatment",
                runs_root=root,
                frozen_context=frozen,
            )
            self.assertEqual(treatment_index, 1)
            self.assertEqual(treatment["run_order_index"], 2)

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

    def test_ambiguous_usage_events_are_unavailable_not_last_event_wins(self):
        events = b'\n'.join(
            [
                b'{"type":"turn.completed","usage":{"input_tokens":80,"cached_input_tokens":20}}',
                b'{"type":"turn.completed","usage":{"input_tokens":100,"cached_input_tokens":25}}',
            ]
        )
        metadata = MODULE.extract_event_metadata(events)
        self.assertIsNone(metadata["input_tokens"])
        self.assertIsNone(metadata["cached_input_tokens"])
        self.assertIsNone(metadata["uncached_input_tokens"])
        self.assertIsNone(metadata["cache_hit_ratio"])
        self.assertEqual(metadata["event_parse"]["usage_events"], 2)
        self.assertEqual(metadata["event_parse"]["ambiguous_usage_events"], 1)

    def test_impossible_cache_relationship_is_unavailable_not_negative(self):
        events = b'{"type":"turn.completed","usage":{"input_tokens":80,"cached_input_tokens":100,"output_tokens":12}}'
        metadata = MODULE.extract_event_metadata(events)
        self.assertIsNone(metadata["input_tokens"])
        self.assertIsNone(metadata["cached_input_tokens"])
        self.assertIsNone(metadata["uncached_input_tokens"])
        self.assertIsNone(metadata["cache_hit_ratio"])
        self.assertEqual(metadata["output_tokens"], 12)
        self.assertEqual(metadata["event_parse"]["invalid_cached_input_relationships"], 1)

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

    def test_fresh_bootstrap_contains_complete_governance_bytes_and_metadata(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            exit_code, run_root, _ = self.run_fake_loop(root)

            self.assertEqual(exit_code, 0)
            repo_root = root / "repo"
            manifest = json.loads((run_root / "manifest.json").read_text())
            turn1 = manifest["turns"][0]
            context = turn1["authoritative_context"]
            prompt = (run_root / turn1["prompt_path"]).read_bytes()
            self.assertEqual(context["injection_mode"], "full-bootstrap")
            self.assertEqual(context["injected_files"], ["static", "runtime"])
            self.assertTrue(context["validation"]["prompt_bytes_verified"])
            self.assertTrue(context["validation"]["source_bytes_verified"])

            for name, filename in (
                ("static", "miniloop_static.md"),
                ("runtime", "miniloop_runtime.md"),
            ):
                source = (repo_root / "1PCloop/docs" / filename).read_bytes()
                offset = context["document_prompt_offsets"][name]
                self.assertEqual(prompt[offset : offset + len(source)], source)
                self.assertEqual(context[name]["bytes"], len(source))
                self.assertEqual(context[name]["lines"], MODULE.count_lines(source))
                self.assertEqual(
                    context[name]["sha256"], hashlib.sha256(source).hexdigest()
                )

    def test_governance_growth_is_bootstrapped_without_a_line_limit(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            _, _, _ = self.run_fake_loop(root)
            repo_root = root / "repo"
            runtime_path = repo_root / "1PCloop/docs/miniloop_runtime.md"
            growth = b"".join(
                f"growth-line-{number:04d}\n".encode("ascii")
                for number in range(1000)
            )
            runtime_path.write_bytes(runtime_path.read_bytes() + growth)

            snapshot = MODULE.read_authoritative_snapshot(repo_root)
            authoritative, _ = MODULE.build_authoritative_prompt(
                role_prompt=b"role\n",
                current=snapshot,
                session_known=None,
                fresh_reason="growth-test",
            )
            MODULE.validate_authoritative_prompt(authoritative)
            offset = authoritative.document_offsets["runtime"]
            self.assertEqual(
                authoritative.prompt[
                    offset : offset + len(snapshot.runtime.content)
                ],
                snapshot.runtime.content,
            )
            self.assertTrue(snapshot.runtime.content.endswith(growth))
            self.assertEqual(
                authoritative.evidence["runtime"]["bytes"],
                len(snapshot.runtime.content),
            )

    def test_runtime_change_refreshes_same_reviewer_thread(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            exit_code, run_root, _ = self.run_fake_loop(
                root,
                binary_name="runtime-change-codex",
                session_mode=MODULE.TREATMENT_MODE,
            )

            self.assertEqual(exit_code, 0)
            manifest = json.loads((run_root / "manifest.json").read_text())
            turn1, _, turn3 = manifest["turns"]
            context = turn3["authoritative_context"]
            self.assertEqual(context["injection_mode"], "runtime-refresh")
            self.assertEqual(context["injected_files"], ["runtime"])
            self.assertTrue(context["refresh_required"])
            self.assertTrue(context["refresh_performed"])
            self.assertEqual(turn3["session_mode"], MODULE.RESUME)
            self.assertTrue(turn3["resume_relationship_verified"])
            self.assertNotEqual(
                turn1["authoritative_context"]["runtime"]["sha256"],
                context["runtime"]["sha256"],
            )
            runtime = (
                root / "repo/1PCloop/docs/miniloop_runtime.md"
            ).read_bytes()
            prompt = (run_root / turn3["prompt_path"]).read_bytes()
            offset = context["document_prompt_offsets"]["runtime"]
            self.assertEqual(prompt[offset : offset + len(runtime)], runtime)

    def test_static_change_rolls_over_and_fully_rebootstraps(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            exit_code, run_root, _ = self.run_fake_loop(
                root,
                binary_name="static-change-codex",
                session_mode=MODULE.TREATMENT_MODE,
            )

            self.assertEqual(exit_code, 0)
            manifest = json.loads((run_root / "manifest.json").read_text())
            turn3 = manifest["turns"][2]
            context = turn3["authoritative_context"]
            self.assertEqual(
                context["injection_mode"], "full-rebootstrap-static-change"
            )
            self.assertEqual(context["injected_files"], ["static", "runtime"])
            self.assertTrue(context["rollover_required"])
            self.assertTrue(context["rollover_performed"])
            self.assertEqual(turn3["session_mode"], MODULE.NEW_PERSISTENT)
            self.assertNotIn("resume", turn3["command"])
            self.assertIsNone(turn3["resume_target_thread_id"])

    def test_missing_governance_file_fails_before_another_codex_call(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            _, _, fake_codex = self.run_fake_loop(root)
            calls_path = fake_codex.with_suffix(".calls")
            initial_calls = calls_path.read_text().splitlines()
            (root / "repo/1PCloop/docs/miniloop_runtime.md").unlink()

            exit_code, run_root = MODULE.orchestrate(
                repo_root=root / "repo",
                runs_root=root / "missing-runs",
                codex_bin=str(fake_codex),
                reviewer_home=root / "reviewer-home",
                executor_home=root / "executor-home",
                run_id="missing-governance",
                timeout_seconds=10,
            )
            manifest = json.loads((run_root / "manifest.json").read_text())
            self.assertEqual(exit_code, 1)
            self.assertEqual(manifest["status"], "failed")
            self.assertIn("required governance file is missing", manifest["failure"])
            self.assertEqual(calls_path.read_text().splitlines(), initial_calls)

    def test_bootstrap_prompt_mismatch_fails_before_codex_launch(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            _, _, fake_codex = self.run_fake_loop(root)
            repo_root = root / "repo"
            snapshot = MODULE.read_authoritative_snapshot(repo_root)
            authoritative, _ = MODULE.build_authoritative_prompt(
                role_prompt=b"role\n",
                current=snapshot,
                session_known=None,
                fresh_reason="mismatch-test",
            )
            tampered_prompt = bytearray(authoritative.prompt)
            tampered_prompt[authoritative.document_offsets["static"]] ^= 1
            tampered = MODULE.AuthoritativePrompt(
                prompt=bytes(tampered_prompt),
                payload=authoritative.payload,
                payload_offset=authoritative.payload_offset,
                evidence=authoritative.evidence,
                snapshot=authoritative.snapshot,
                document_offsets=authoritative.document_offsets,
            )
            calls_path = fake_codex.with_suffix(".calls")
            call_count = len(calls_path.read_text().splitlines())
            run_root = root / "mismatch-run"
            run_root.mkdir()

            result = MODULE.run_turn(
                run_root=run_root,
                repo_root=repo_root,
                codex_bin=str(fake_codex),
                timeout_seconds=10,
                number=1,
                role="reviewer",
                codex_home=root / "reviewer-home",
                prompt=tampered.prompt,
                authoritative_context=tampered,
            )
            self.assertFalse(result.success)
            self.assertIn("validation failed", result.process["failure"])
            self.assertFalse(
                result.process["authoritative_context"]["validation"][
                    "prompt_bytes_verified"
                ]
            )
            self.assertEqual(len(calls_path.read_text().splitlines()), call_count)

    def test_complete_three_turn_run_with_fake_codex(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            exit_code, run_root, _ = self.run_fake_loop(root)

            self.assertEqual(exit_code, 0)
            manifest = json.loads((run_root / "manifest.json").read_text())
            self.assertEqual(manifest["status"], "completed")
            self.assertEqual(len(manifest["turns"]), 3)
            self.assertEqual(manifest["session_mode"], MODULE.CONTROL_MODE)
            self.assertTrue(
                all(
                    turn["session_mode"] == MODULE.FRESH_EPHEMERAL
                    and "--ephemeral" in turn["command"]
                    and "resume" not in turn["command"]
                    for turn in manifest["turns"]
                )
            )
            self.assertEqual(
                manifest["turns"][0]["authoritative_context"]["injection_mode"],
                "full-bootstrap",
            )
            self.assertIsNone(manifest["turns"][1]["authoritative_context"])
            self.assertEqual(
                manifest["turns"][2]["authoritative_context"]["injection_mode"],
                "full-bootstrap",
            )
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

    def test_treatment_command_construction_and_resume_relationship(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            exit_code, run_root, _ = self.run_fake_loop(
                root, session_mode=MODULE.TREATMENT_MODE
            )

            self.assertEqual(exit_code, 0)
            manifest = json.loads((run_root / "manifest.json").read_text())
            turn1, turn2, turn3 = manifest["turns"]
            self.assertEqual(turn1["session_mode"], MODULE.NEW_PERSISTENT)
            self.assertNotIn("--ephemeral", turn1["command"])
            self.assertEqual(turn1["created_thread_id"], "fake-thread-id")
            self.assertEqual(turn2["session_mode"], MODULE.FRESH_EPHEMERAL)
            self.assertIn("--ephemeral", turn2["command"])
            self.assertEqual(turn3["session_mode"], MODULE.RESUME)
            self.assertNotIn("--ephemeral", turn3["command"])
            resume_index = turn3["command"].index("resume")
            self.assertEqual(
                turn3["command"][resume_index + 1], turn1["created_thread_id"]
            )
            self.assertEqual(
                turn3["resume_target_thread_id"], "fake-thread-id"
            )
            self.assertEqual(
                turn3["observed_resume_thread_id"], "fake-thread-id"
            )
            self.assertTrue(turn3["resume_relationship_verified"])
            context1 = turn1["authoritative_context"]
            context3 = turn3["authoritative_context"]
            self.assertEqual(context1["injection_mode"], "full-bootstrap")
            self.assertEqual(context1["injected_files"], ["static", "runtime"])
            self.assertEqual(context3["injection_mode"], "resume-unchanged")
            self.assertEqual(context3["injected_files"], [])
            self.assertFalse(context3["refresh_required"])
            self.assertFalse(context3["refresh_performed"])
            self.assertEqual(
                context3["session_known_hashes"], context3["current_hashes"]
            )
            self.assertTrue(
                all(item["preserved_verbatim"] for item in manifest["transports"])
            )

    def test_treatment_missing_created_thread_id_fails_closed(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            exit_code, run_root, _ = self.run_fake_loop(
                root,
                binary_name="missing-thread-codex",
                session_mode=MODULE.TREATMENT_MODE,
            )

            self.assertEqual(exit_code, 1)
            manifest = json.loads((run_root / "manifest.json").read_text())
            self.assertEqual(manifest["status"], "failed")
            self.assertEqual(len(manifest["turns"]), 1)
            self.assertIsNone(manifest["turns"][0]["created_thread_id"])

    def test_resume_process_failure_does_not_fallback_to_fresh(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            exit_code, run_root, fake_codex = self.run_fake_loop(
                root,
                binary_name="resume-failure-codex",
                session_mode=MODULE.TREATMENT_MODE,
            )

            self.assertEqual(exit_code, 1)
            manifest = json.loads((run_root / "manifest.json").read_text())
            self.assertEqual(manifest["status"], "failed")
            self.assertEqual(len(manifest["turns"]), 3)
            self.assertEqual(manifest["turns"][2]["exit_code"], 7)
            calls = [json.loads(line) for line in fake_codex.with_suffix(".calls").read_text().splitlines()]
            self.assertEqual(len(calls), 3)
            self.assertEqual(sum("resume" in call for call in calls), 1)

    def test_resume_thread_mismatch_fails_closed(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            exit_code, run_root, _ = self.run_fake_loop(
                root,
                binary_name="resume-mismatch-codex",
                session_mode=MODULE.TREATMENT_MODE,
            )

            self.assertEqual(exit_code, 1)
            manifest = json.loads((run_root / "manifest.json").read_text())
            turn3 = manifest["turns"][2]
            self.assertEqual(turn3["resume_target_thread_id"], "fake-thread-id")
            self.assertEqual(turn3["observed_resume_thread_id"], "wrong-thread-id")
            self.assertFalse(turn3["resume_relationship_verified"])


if __name__ == "__main__":
    unittest.main()
