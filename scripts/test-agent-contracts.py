#!/usr/bin/env python3

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(SCRIPT_DIR))

from agent_contracts import ContractValidationError, load_json, validate  # noqa: E402
from importlib.util import module_from_spec, spec_from_file_location  # noqa: E402


def load_template_validator():
    path = SCRIPT_DIR / "validate-agent-contracts.py"
    spec = spec_from_file_location("validate_agent_contracts", path)
    assert spec is not None and spec.loader is not None
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


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
