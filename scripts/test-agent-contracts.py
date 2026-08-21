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

    def test_template_provider_mappings_are_consistent(self) -> None:
        load_template_validator().validate_template(self.template)

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


if __name__ == "__main__":
    unittest.main()
