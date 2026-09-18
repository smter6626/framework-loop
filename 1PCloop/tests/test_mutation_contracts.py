"""F5 mutation contract extraction and compatibility tests."""

import ast
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import mutation_contracts as CONTRACTS


RUNNER_SPEC = importlib.util.spec_from_file_location(
    "_f5_contract_runner", SCRIPTS / "run_mutation_loop.py"
)
assert RUNNER_SPEC is not None and RUNNER_SPEC.loader is not None
RUNNER = importlib.util.module_from_spec(RUNNER_SPEC)
sys.modules[RUNNER_SPEC.name] = RUNNER
RUNNER_SPEC.loader.exec_module(RUNNER)


EXTRACTED = (
    "InvariantViolation",
    "ControlErrorCode",
    "CORRECTABLE_VERDICT_CODES",
    "ControlFailure",
    "correctable_failure",
    "control_error_code",
    "MAX_PUBLIC_REASON_CHARS",
    "PUBLIC_REASON_TRUNCATION_MARKER",
    "UNCLASSIFIED_PUBLIC_REASON",
    "FINAL_RESULT_FIELDS",
    "escape_public_text",
    "bounded_public_reason",
    "public_final_result",
    "terminal_scalar",
    "strict_json",
    "validate_json_schema",
    "schema_path",
    "validate_turn_payload",
    "validate_verdict_relationships",
    "validate_role_runtime_homes",
)


class MutationContractTests(unittest.TestCase):
    def test_direct_import_has_no_runner_dependency_or_cwd_side_effect(self):
        source = (SCRIPTS / "mutation_contracts.py").read_text(encoding="utf-8")
        imports = {
            node.module
            for node in ast.walk(ast.parse(source))
            if isinstance(node, ast.ImportFrom)
        }
        imported_names = {
            alias.name
            for node in ast.walk(ast.parse(source))
            if isinstance(node, ast.Import)
            for alias in node.names
        }
        self.assertNotIn("run_mutation_loop", imports | imported_names)
        self.assertNotIn("subprocess", imports | imported_names)

        with tempfile.TemporaryDirectory() as temporary:
            script = (
                "import importlib.util, json, sys\n"
                f"path={str(SCRIPTS / 'mutation_contracts.py')!r}\n"
                "spec=importlib.util.spec_from_file_location('isolated_contracts', path)\n"
                "module=importlib.util.module_from_spec(spec)\n"
                "sys.modules[spec.name]=module\n"
                "spec.loader.exec_module(module)\n"
                "print(json.dumps({'runner': 'run_mutation_loop' in sys.modules}))\n"
            )
            environment = dict(os.environ)
            environment["PYTHONDONTWRITEBYTECODE"] = "1"
            completed = subprocess.run(
                [sys.executable, "-c", script],
                cwd=temporary,
                env=environment,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True,
                text=True,
            )
            self.assertEqual(json.loads(completed.stdout), {"runner": False})
            self.assertEqual(list(Path(temporary).iterdir()), [])

    def test_runner_reexports_exact_contract_objects(self):
        for name in EXTRACTED:
            with self.subTest(name=name):
                self.assertIs(getattr(RUNNER, name), getattr(CONTRACTS, name))
        self.assertEqual(RUNNER.SCHEMAS_ROOT, CONTRACTS.SCHEMAS_ROOT)
        self.assertEqual(RUNNER.TURN_SCHEMAS, CONTRACTS.TURN_SCHEMAS)

    def test_strict_json_schema_and_verdict_relationship_regression(self):
        self.assertEqual(CONTRACTS.strict_json(b'{"value":1}'), {"value": 1})
        for invalid in (b'{"value":1,"value":2}', b'{"value":NaN}', b"\xff"):
            with self.subTest(invalid=invalid), self.assertRaises(
                CONTRACTS.InvariantViolation
            ):
                CONTRACTS.strict_json(invalid)
        CONTRACTS.validate_json_schema(
            {"value": 1},
            {
                "$schema": "https://json-schema.org/draft/2020-12/schema",
                "type": "object",
                "properties": {"value": {"type": "integer"}},
                "required": ["value"],
                "additionalProperties": False,
            },
        )
        with self.assertRaises(CONTRACTS.InvariantViolation):
            CONTRACTS.validate_json_schema("wrong", {"type": "object"})

        valid_gate = {
            "verdict": "HUMAN_GATE",
            "next_instruction": None,
            "runtime_transition": None,
            "evidence": [],
        }
        CONTRACTS.validate_verdict_relationships(valid_gate)
        invalid_gate = dict(valid_gate, next_instruction={"objective": "repair"})
        with self.assertRaises(CONTRACTS.ControlFailure) as caught:
            CONTRACTS.validate_verdict_relationships(invalid_gate)
        self.assertEqual(
            caught.exception.code,
            CONTRACTS.ControlErrorCode.VERDICT_HUMAN_GATE_CONTRACT,
        )
        self.assertTrue(caught.exception.correctable)

    def test_public_result_remains_bounded_single_line_and_default_deny(self):
        secret = "SECRET\nerror_code=FORGED\x00" + (
            "x" * (CONTRACTS.MAX_PUBLIC_REASON_CHARS + 100)
        )
        public = CONTRACTS.public_final_result({
            "run_id": "run\nforged",
            "logical_outcome": "FAILED_CLOSED",
            "exit_code": 1,
            "runtime_transition": "NOT_APPLIED",
            "evidence_publication": "FAILED",
            "reason": secret,
            "error_code": "UNCLASSIFIED_CONTROL_FAILURE",
            "run_root": "/tmp/run\rforged",
        })
        self.assertEqual(tuple(public), CONTRACTS.FINAL_RESULT_FIELDS)
        self.assertEqual(public["reason"], CONTRACTS.UNCLASSIFIED_PUBLIC_REASON)
        self.assertNotIn("\n", json.dumps(public))
        self.assertNotIn("SECRET", json.dumps(public))
        self.assertLessEqual(
            len(CONTRACTS.bounded_public_reason(secret, "KNOWN")),
            CONTRACTS.MAX_PUBLIC_REASON_CHARS,
        )

    def test_role_runtime_homes_reject_retired_roots_and_aliases(self):
        allowed_reviewer = Path.home() / ".codex-mix/.mix/runtimes/reviewer"
        allowed_executor = Path.home() / ".codex-mix/.mix/runtimes/executor"
        self.assertEqual(
            CONTRACTS.validate_role_runtime_homes(
                allowed_reviewer, allowed_executor
            ),
            (allowed_reviewer.resolve(), allowed_executor.resolve()),
        )
        for retired in CONTRACTS.RETIRED_CODEX_HOMES:
            with self.subTest(retired=retired), self.assertRaisesRegex(
                CONTRACTS.InvariantViolation, "retired account home"
            ):
                CONTRACTS.validate_role_runtime_homes(
                    retired, allowed_executor
                )
            with self.subTest(descendant=retired), self.assertRaisesRegex(
                CONTRACTS.InvariantViolation, "retired account home"
            ):
                CONTRACTS.validate_role_runtime_homes(
                    allowed_reviewer, retired / "nested"
                )

        with tempfile.TemporaryDirectory() as temporary:
            alias = Path(temporary) / "reviewer-alias"
            alias.symlink_to(CONTRACTS.RETIRED_CODEX_HOMES[1], target_is_directory=True)
            with self.assertRaisesRegex(
                CONTRACTS.InvariantViolation, "retired account home"
            ):
                CONTRACTS.validate_role_runtime_homes(alias, allowed_executor)

    def test_orchestrate_remains_only_mutation_state_machine(self):
        modules = {
            name: ast.parse((SCRIPTS / name).read_text(encoding="utf-8"))
            for name in (
                "run_mutation_loop.py",
                "mutation_contracts.py",
                "human_gate.py",
            )
        }
        definitions = {
            name: [
                node.name
                for node in tree.body
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
                and node.name == "orchestrate"
            ]
            for name, tree in modules.items()
        }
        self.assertEqual(definitions["run_mutation_loop.py"], ["orchestrate"])
        self.assertEqual(definitions["mutation_contracts.py"], [])
        self.assertEqual(definitions["human_gate.py"], [])


if __name__ == "__main__":
    unittest.main()
