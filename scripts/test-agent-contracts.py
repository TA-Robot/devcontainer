#!/usr/bin/env python3

from __future__ import annotations

import json
import re
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(SCRIPT_DIR))

from agent_contracts import ContractValidationError, load_json, validate, validate_file  # noqa: E402
from importlib.util import module_from_spec, spec_from_file_location  # noqa: E402


def load_template_validator():
    path = SCRIPT_DIR / "validate-agent-contracts.py"
    spec = spec_from_file_location("validate_agent_contracts", path)
    assert spec is not None and spec.loader is not None
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_collaboration_report_wrapper():
    path = (
        REPO_ROOT
        / "project/.codex/skills/review-collaboration-evidence/scripts/report_evidence.py"
    )
    spec = spec_from_file_location("collaboration_report_wrapper", path)
    assert spec is not None and spec.loader is not None
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class JsonObjectTests(unittest.TestCase):
    def test_load_json_rejects_duplicate_decoded_names_at_every_depth(self) -> None:
        objects = (
            '{"name": "first-secret", "name": "second-secret"}',
            '{"name": null, "name": null}',
            '{"name": false, "other": 0, "name": true}',
            r'{"name": 1, "\u006eame": 2}',
            r'{"\u006eame": 1, "n\u0061me": 2}',
            r'{"": 1, "": 2}',
            r'{"a/b": 1, "a\/b": 2}',
            r'{"é": 1, "\u00e9": 2}',
            r'{"😀": 1, "\ud83d\ude00": 2}',
        )
        with tempfile.TemporaryDirectory() as raw:
            path = Path(raw) / "duplicate.json"
            for obj in objects:
                for document in (obj, '{"outer": ' + obj + '}', '[{"outer": [' + obj + ']}]'):
                    with self.subTest(document=document):
                        path.write_text(document, encoding="utf-8")
                        before = path.read_bytes()
                        with self.assertRaises(ContractValidationError) as raised:
                            load_json(path)
                        diagnostic = str(raised.exception)
                        self.assertIn(str(path), diagnostic)
                        self.assertIn("duplicate", diagnostic)
                        self.assertIn("ambiguous", diagnostic)
                        self.assertNotIn("first-secret", diagnostic)
                        self.assertNotIn("second-secret", diagnostic)
                        self.assertNotIn(document, diagnostic)
                        self.assertEqual(before, path.read_bytes())

    def test_names_are_local_to_each_object_and_are_not_normalized(self) -> None:
        document = r'''{
            "left": {"name": 1}, "right": {"name": 2},
            "items": [{"name": 3}, {"name": 4}],
            "name": 5, "Name": 6, "é": 7, "e\u0301": 8,
            "\\u006eame": 9
        }'''
        with tempfile.TemporaryDirectory() as raw:
            path = Path(raw) / "distinct.json"
            path.write_text(document, encoding="utf-8")
            self.assertEqual(json.loads(document), load_json(path))
            self.assertEqual(document, path.read_text(encoding="utf-8"))

    def test_load_json_preserves_values_and_types(self) -> None:
        values = ({}, [], None, True, False, 0, 10**400, 1.0, -0.0, 5e-324, "text")
        with tempfile.TemporaryDirectory() as raw:
            path = Path(raw) / "ordinary.json"
            for value in values:
                for document, expected in (
                    (value, value), ([value], value), ({"value": value}, value),
                ):
                    with self.subTest(document=document):
                        source = json.dumps(document)
                        path.write_text(source, encoding="utf-8")
                        loaded = load_json(path)
                        self.assertIs(type(loaded), type(document))
                        self.assertEqual(document, loaded)
                        self.assertEqual(source, json.dumps(loaded))
                        if isinstance(document, list) and document:
                            loaded = loaded[0]
                        elif isinstance(document, dict) and document:
                            loaded = loaded["value"]
                        self.assertIs(type(loaded), type(expected))
                        self.assertEqual(source, path.read_text(encoding="utf-8"))

    def test_validate_file_rejects_duplicates_in_instance_and_schema(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            instance = Path(raw) / "instance.json"
            schema = Path(raw) / "schema.json"
            for invalid_path in (instance, schema):
                for document in (
                    '{"type": "string", "type": "object"}',
                    r'{"extra": [{"name": 1, "\u006eame": 2}]}',
                ):
                    with self.subTest(path=invalid_path.name, document=document):
                        instance.write_text("{}", encoding="utf-8")
                        schema.write_text("{}", encoding="utf-8")
                        invalid_path.write_text(document, encoding="utf-8")
                        before = (instance.read_bytes(), schema.read_bytes())
                        with self.assertRaises(ContractValidationError) as raised:
                            validate_file(instance, schema)
                        self.assertIn(str(invalid_path), str(raised.exception))
                        self.assertIn("duplicate", str(raised.exception))
                        self.assertEqual(before, (instance.read_bytes(), schema.read_bytes()))


class JsonNumberTests(unittest.TestCase):
    def test_load_json_rejects_non_finite_numbers(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            path = Path(raw) / "numbers.json"
            for token in ("NaN", "Infinity", "-Infinity", "1e309", "-1e309"):
                for document in (
                    token,
                    f'[{{"extra": [{token}]}}]',
                    f'{{"extra": {token}, "extra": 0}}',
                ):
                    with self.subTest(document=document):
                        path.write_text(document, encoding="utf-8")
                        with self.assertRaises(ContractValidationError) as raised:
                            load_json(path)
                        self.assertIn(str(path), str(raised.exception))
                        self.assertIn("non-finite", str(raised.exception))
                        self.assertIn(token, str(raised.exception))

    def test_validate_rejects_non_finite_numbers_in_unconstrained_values(self) -> None:
        for value in (float("nan"), float("inf"), float("-inf")):
            for instance, schemas, path in (
                (value, ({}, {"type": "number", "minimum": 0}), "$"),
                ([{"extra": [value]}], ({}, {"type": "array"}, {"items": {}}), "$[0].extra[0]"),
                (
                    {"extra": [{"value": value}]},
                    ({}, {"type": "object"}, {"properties": {"known": {"type": "string"}}}),
                    "$.extra[0].value",
                ),
            ):
                for schema in schemas:
                    with self.subTest(value=value, schema=schema, path=path):
                        with self.assertRaisesRegex(
                            ContractValidationError, re.escape(path) + ": .*non-finite"
                        ):
                            validate(instance, schema)

    def test_schema_branches_cannot_accept_non_finite_values(self) -> None:
        for schema in (
            {"$ref": "#/$defs/anything", "$defs": {"anything": {}}},
            {"allOf": [{}]},
            {"anyOf": [{"type": "string"}, {}]},
            {"oneOf": [{"type": "string"}, {}]},
            {"if": {"type": "number"}, "then": {}, "else": {}},
        ):
            with self.subTest(schema=schema):
                with self.assertRaisesRegex(
                    ContractValidationError, r"packet\.extra\[0\]: .*non-finite"
                ):
                    validate({"extra": [float("nan")]}, schema, root=schema, path="packet")

    def test_finite_numbers_large_integers_and_booleans_remain_supported(self) -> None:
        integers = (0, 1, -1, 10**400, -(10**400))
        numbers = (*integers, 0.0, -0.0, 1.25, -1.25, 1e308, -1e308, 5e-324)
        for value in numbers:
            with self.subTest(value=value):
                validate(value, {"type": "number"})
                validate([{"extra": value}], {})
        for value in integers:
            validate(value, {"type": "integer"})
        for value in (True, False):
            validate(value, {"type": "boolean", "minimum": 2})
            validate(value, {"type": ["number", "boolean"]})
            for numeric_type in ("number", "integer"):
                with self.subTest(value=value, numeric_type=numeric_type):
                    with self.assertRaisesRegex(ContractValidationError, "got bool"):
                        validate(value, {"type": numeric_type})
        with tempfile.TemporaryDirectory() as raw:
            path = Path(raw) / "finite.json"
            document = {"values": [*numbers, True, False, None, "NaN", "Infinity", "1e309"]}
            path.write_text(json.dumps(document, allow_nan=False), encoding="utf-8")
            loaded = load_json(path)
            self.assertEqual(document, loaded)
            self.assertIs(type(loaded["values"][3]), int)
            self.assertIs(type(loaded["values"][len(numbers)]), bool)
            validate(loaded, {})

    def test_load_json_preserves_syntax_and_io_diagnostics(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            path = Path(raw) / "invalid.json"
            with self.assertRaises(ContractValidationError) as raised:
                load_json(path)
            self.assertIn(str(path), str(raised.exception))
            self.assertIsInstance(raised.exception.__cause__, OSError)
            path.write_text('{"value": }', encoding="utf-8")
            with self.assertRaises(ContractValidationError) as raised:
                load_json(path)
            self.assertIn(str(path), str(raised.exception))
            self.assertIn("line 1 column", str(raised.exception))
            self.assertIsInstance(raised.exception.__cause__, json.JSONDecodeError)


class AgentContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.template = REPO_ROOT / "project"
        cls.fixtures = SCRIPT_DIR / "fixtures/agent-contracts"
        cls.task_schema = load_json(cls.template / ".agent/schemas/task.schema.json")
        cls.result_schema = load_json(cls.template / ".agent/schemas/result.schema.json")
        cls.decision_schema = load_json(cls.template / ".agent/schemas/collaboration-decision.schema.json")
        cls.outcome_schema = load_json(cls.template / ".agent/schemas/collaboration-outcome.schema.json")

    def test_template_provider_mappings_are_consistent(self) -> None:
        load_template_validator().validate_template(self.template)

    def test_collaboration_guidance_is_part_of_the_copy_source(self) -> None:
        validator = load_template_validator()
        validator.validate_operating_docs(self.template)
        playbook = self.template / "docs/agents/collaboration-playbook.md"
        template = self.template / "docs/agents/tickets/collaboration-plan.template.md"
        self.assertIn("Find the binding constraint", playbook.read_text(encoding="utf-8"))
        self.assertIn("human inputを要求しません", playbook.read_text(encoding="utf-8"))
        self.assertIn("human review / synthesis budget", template.read_text(encoding="utf-8"))
        self.assertIn("do not ask the user", template.read_text(encoding="utf-8"))

    def test_read_job_guidance_requires_clean_checkpoint_boundary(self) -> None:
        skill = (self.template / ".codex/skills/orchestrate-agent-collaboration/SKILL.md").read_text(
            encoding="utf-8"
        )
        playbook = (self.template / "docs/agents/collaboration-playbook.md").read_text(
            encoding="utf-8"
        )
        agents = (self.template / "AGENTS.md").read_text(encoding="utf-8")
        for text in (skill, playbook, agents):
            self.assertIn("clean", text)
            self.assertIn("checkpoint", text)
            self.assertIn("uncommitted diff", text)

    def test_native_full_history_fork_guidance_avoids_incompatible_override(self) -> None:
        skill = (
            self.template / ".codex/skills/orchestrate-agent-collaboration/SKILL.md"
        ).read_text(encoding="utf-8")
        playbook = (
            self.template / "docs/agents/collaboration-playbook.md"
        ).read_text(encoding="utf-8")
        for text in (skill, playbook):
            self.assertIn("full-history", text)
            self.assertIn("override", text)

    def test_read_lane_packets_and_checks_preserve_clean_result_contract(self) -> None:
        agents = (self.template / "AGENTS.md").read_text(encoding="utf-8")
        playbook = (
            self.template / "docs/agents/collaboration-playbook.md"
        ).read_text(encoding="utf-8")
        researcher = (
            self.template / ".agent/roles/researcher.md"
        ).read_text(encoding="utf-8")
        reviewer = (
            self.template / ".agent/roles/reviewer.md"
        ).read_text(encoding="utf-8")
        template = (REPO_ROOT / "AGENTS_TEMPLATE.md").read_text(encoding="utf-8")
        for text in (agents, playbook, template):
            self.assertIn(".git/agentctl-inputs", text)
        for text in (agents, playbook, researcher, reviewer, template):
            self.assertIn("py_compile", text)
            self.assertIn("checks", text)
        self.assertIn("exit_code: null", playbook)
        self.assertIn(
            "Commands actually executed",
            json.dumps(self.result_schema),
        )

    def test_collaboration_report_resolves_project_root_from_skill_directory(self) -> None:
        wrapper = load_collaboration_report_wrapper()
        with tempfile.TemporaryDirectory() as raw:
            project = Path(raw) / "target"
            skill_directory = project / ".codex/skills/review-collaboration-evidence"
            skill_directory.mkdir(parents=True)
            (project / ".agent").mkdir()
            (project / ".agent/config.json").write_text("{}\n", encoding="utf-8")
            with mock.patch.object(Path, "cwd", return_value=skill_directory):
                self.assertEqual(project.resolve(), wrapper.current_workspace())

    def test_collaboration_guidance_rejects_unsupported_global_defaults(self) -> None:
        validator = load_template_validator()
        path = self.template / "docs/agents/collaboration-playbook.md"
        for statement in (
            "deliberationは通常2 rounds",
            "最大3往復で停止する",
            "variants normally 2 candidates",
            "use a blind first round",
        ):
            with self.subTest(statement=statement):
                with self.assertRaises(ContractValidationError):
                    validator.validate_adaptive_guidance(path, statement, ())

    def test_valid_fixtures(self) -> None:
        validate(load_json(self.fixtures / "task.valid.json"), self.task_schema)
        validate(load_json(self.fixtures / "result.valid.json"), self.result_schema)

    def test_absolute_scope_is_rejected(self) -> None:
        with self.assertRaises(ContractValidationError):
            validate(load_json(self.fixtures / "task.absolute-path.invalid.json"), self.task_schema)

    def test_lane_rejects_incompatible_permission_profile(self) -> None:
        candidate = load_json(self.fixtures / "task.valid.json")
        candidate["permission_profile"] = "trusted-fast"
        with self.assertRaises(ContractValidationError):
            validate(candidate, self.task_schema)

    def test_queue_priority_is_optional_but_bounded(self) -> None:
        candidate = load_json(self.fixtures / "task.valid.json")
        validate(candidate, self.task_schema)
        for priority in ("interactive", "normal", "background"):
            with self.subTest(priority=priority):
                candidate["priority"] = priority
                validate(candidate, self.task_schema)
        candidate["priority"] = "urgent"
        with self.assertRaises(ContractValidationError):
            validate(candidate, self.task_schema)

    def test_task_collaboration_projection_is_optional_and_content_free(self) -> None:
        candidate = load_json(self.fixtures / "task.valid.json")
        candidate["collaboration"] = {
            "plan_id": "plan-001",
            "candidate_id": "delegate-tests",
            "decision_digest": "sha256:" + "1" * 64,
            "relation": "delegate",
            "lifecycle": "one-shot",
            "expected_mechanisms": ["latency-overlap", "context-partitioning"],
            "binding_constraint": "wall-clock",
            "annotation_source": "primary-plan",
        }
        validate(candidate, self.task_schema)

        candidate["collaboration"]["rationale"] = "free-form text must stay in the decision packet"
        with self.assertRaises(ContractValidationError):
            validate(candidate, self.task_schema)

    def test_task_collaboration_projection_rejects_unbounded_categories(self) -> None:
        candidate = load_json(self.fixtures / "task.valid.json")
        candidate["collaboration"] = {
            "plan_id": "plan-001",
            "candidate_id": "candidate-001",
            "decision_digest": "sha256:" + "2" * 64,
            "relation": "ask-a-friend-about-parser-details",
            "lifecycle": "one-shot",
            "expected_mechanisms": ["coverage"],
            "binding_constraint": "wall-clock",
            "annotation_source": "primary-plan",
        }
        with self.assertRaises(ContractValidationError):
            validate(candidate, self.task_schema)

    def test_collaboration_examples_validate(self) -> None:
        validate(
            load_json(self.template / ".agent/examples/collaboration-decision.example.json"),
            self.decision_schema,
        )
        validate(
            load_json(self.template / ".agent/examples/collaboration-outcome.example.json"),
            self.outcome_schema,
        )

    def test_outcome_requires_a_decision_digest(self) -> None:
        candidate = load_json(self.template / ".agent/examples/collaboration-outcome.example.json")
        candidate["decision_digest"] = "not-a-digest"
        with self.assertRaises(ContractValidationError):
            validate(candidate, self.outcome_schema)

    def test_completed_result_must_be_clean(self) -> None:
        with self.assertRaises(ContractValidationError):
            validate(load_json(self.fixtures / "result.dirty-completed.invalid.json"), self.result_schema)

    def test_ready_for_commit_requires_dirty_change(self) -> None:
        candidate = load_json(self.fixtures / "result.valid.json")
        candidate["status"] = "ready_for_commit"
        candidate["changed_paths"] = ["src/parser/index.js"]
        candidate["dirty_state"] = {
            "is_dirty": True,
            "paths": ["src/parser/index.js"],
        }
        validate(candidate, self.result_schema)

        candidate["changed_paths"] = []
        candidate["dirty_state"] = {"is_dirty": False, "paths": []}
        with self.assertRaises(ContractValidationError):
            validate(candidate, self.result_schema)

    def test_clean_result_cannot_list_dirty_paths(self) -> None:
        candidate = load_json(self.fixtures / "result.valid.json")
        candidate["dirty_state"]["paths"] = ["src/parser/index.js"]
        with self.assertRaises(ContractValidationError):
            validate(candidate, self.result_schema)

    def test_failed_and_blocked_results_require_reason(self) -> None:
        base = load_json(self.fixtures / "result.valid.json")
        for status in ("failed", "blocked"):
            with self.subTest(status=status):
                candidate = json.loads(json.dumps(base))
                candidate["status"] = status
                candidate["head_sha"] = None
                with self.assertRaises(ContractValidationError):
                    validate(candidate, self.result_schema)

    def test_passed_check_requires_zero_exit(self) -> None:
        candidate = load_json(self.fixtures / "result.valid.json")
        candidate["checks"] = [
            {
                "command": "false",
                "status": "passed",
                "exit_code": 1,
                "summary": "Impossible result",
            }
        ]
        with self.assertRaises(ContractValidationError):
            validate(candidate, self.result_schema)

    def test_dependency_free_validator_enforces_numeric_bounds(self) -> None:
        schema = {
            "type": "number",
            "minimum": 1,
            "maximum": 3,
            "exclusiveMinimum": 0,
            "exclusiveMaximum": 4,
        }
        validate(1, schema)
        validate(3.0, schema)
        for value in (0, 4):
            with self.subTest(value=value):
                with self.assertRaises(ContractValidationError):
                    validate(value, schema)


if __name__ == "__main__":
    unittest.main()
