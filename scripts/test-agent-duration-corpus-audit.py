#!/usr/bin/env python3

from __future__ import annotations

from pathlib import Path
import sys
import unittest
from typing import Any, Mapping, Sequence


SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from agent_duration_corpus_audit import (  # noqa: E402
    AuditSafetyError,
    EvaluationOutcome,
    audit_catalog,
)


def fake_entry(case_id: str, family: str) -> dict[str, Any]:
    return {
        "case": {
            "case_id": case_id,
            "family": family,
            "capsule_digest": "sha256:" + "0" * 64,
        },
        "fixture": {
            "case_id": case_id,
            "recipe_id": f"recipe-{case_id.lower()}",
            "capsule_path": f"capsules/{case_id.lower()}.md",
        },
    }


def fake_catalog(*entries: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "catalog_id": "fake-corpus",
        "revision": 1,
        "published_at": "2026-08-27T00:00:00Z",
        "entries": list(entries),
    }


class FakeRunner:
    def __init__(
        self,
        *,
        stale_cases: set[str] | None = None,
        survivor_cases: set[str] | None = None,
        broken_good_cases: set[str] | None = None,
        valid_alternative_cases: set[str] | None = None,
    ) -> None:
        self.stale_cases = stale_cases or set()
        self.survivor_cases = survivor_cases or set()
        self.broken_good_cases = broken_good_cases or set()
        self.valid_alternative_cases = valid_alternative_cases or set()
        self.calls: list[tuple[str, str]] = []
        self._builds: dict[str, int] = {}

    def _case_id(self, entry: Mapping[str, Any]) -> str:
        return entry["case"]["case_id"]

    def capsule_digest_matches(self, entry: Mapping[str, Any]) -> bool:
        case_id = self._case_id(entry)
        self.calls.append(("digest", case_id))
        return case_id not in self.stale_cases

    def declared_mutants(
        self, entry: Mapping[str, Any]
    ) -> Mapping[str, Sequence[str]]:
        case_id = self._case_id(entry)
        self.calls.append(("recipe", case_id))
        return {"declared-mutant": ("hidden-contract",)}

    def declared_valid_alternatives(
        self, entry: Mapping[str, Any]
    ) -> Sequence[str]:
        return (
            ("independent-valid",)
            if self._case_id(entry) in self.valid_alternative_cases
            else ()
        )

    def build(self, entry: Mapping[str, Any]) -> dict[str, Any]:
        case_id = self._case_id(entry)
        self.calls.append(("build", case_id))
        count = self._builds.get(case_id, 0) + 1
        self._builds[case_id] = count
        return {
            "case_id": case_id,
            "variant": "initial",
            "snapshot": f"snapshot-{case_id}",
            "build": count,
        }

    def initial_failed(self, artifact: dict[str, Any]) -> bool:
        return True

    def install_known_good(
        self, entry: Mapping[str, Any], artifact: dict[str, Any]
    ) -> None:
        artifact["variant"] = "good"

    def install_mutant(
        self,
        entry: Mapping[str, Any],
        mutant_id: str,
        artifact: dict[str, Any],
    ) -> None:
        artifact["variant"] = "mutant"

    def install_valid_alternative(
        self,
        entry: Mapping[str, Any],
        alternative_id: str,
        artifact: dict[str, Any],
    ) -> None:
        artifact["variant"] = "valid-alternative"

    def evaluate(self, artifact: dict[str, Any]) -> EvaluationOutcome:
        case_id = artifact["case_id"]
        self.calls.append(("evaluate", case_id))
        if artifact["variant"] == "good":
            status = "fail" if case_id in self.broken_good_cases else "pass"
            return EvaluationOutcome(status, frozenset())
        if artifact["variant"] == "valid-alternative":
            return EvaluationOutcome("pass", frozenset())
        if case_id in self.survivor_cases:
            return EvaluationOutcome("pass", frozenset())
        return EvaluationOutcome("fail", frozenset({"hidden-contract"}))

    def snapshot_key(self, artifact: dict[str, Any]) -> Any:
        return artifact["snapshot"]


class AgentDurationCorpusAuditTests(unittest.TestCase):
    def setUp(self) -> None:
        self.catalog = fake_catalog(
            fake_entry("F01-S-FAKE-001", "family-one"),
            fake_entry("F02-S-FAKE-001", "family-two"),
        )

    def test_stale_digest_fails_without_building_fixture(self) -> None:
        runner = FakeRunner(stale_cases={"F01-S-FAKE-001"})
        result = audit_catalog(
            self.catalog,
            runner,
            case_ids=["F01-S-FAKE-001"],
            max_cases=1,
            failure_policy="continue",
        )
        self.assertEqual(result["status"], "fail")
        self.assertEqual(result["cases"][0]["checks"][0]["check_id"], "capsule-digest")
        self.assertEqual(result["cases"][0]["checks"][0]["status"], "fail")
        self.assertEqual(runner.calls, [("digest", "F01-S-FAKE-001")])

    def test_mutant_survivor_is_a_failed_case(self) -> None:
        runner = FakeRunner(survivor_cases={"F01-S-FAKE-001"})
        result = audit_catalog(
            self.catalog,
            runner,
            case_ids=["F01-S-FAKE-001"],
            max_cases=1,
            failure_policy="continue",
        )
        mutant = result["cases"][0]["mutants"][0]
        self.assertEqual((result["status"], mutant["status"]), ("fail", "fail"))
        self.assertEqual(mutant["checks"][0]["check_id"], "mutant-rejected")
        self.assertEqual(mutant["checks"][0]["status"], "fail")

    def test_safety_cap_is_checked_before_any_runner_call(self) -> None:
        runner = FakeRunner()
        with self.assertRaises(AuditSafetyError):
            audit_catalog(
                self.catalog,
                runner,
                max_cases=1,
                failure_policy="continue",
            )
        self.assertEqual(runner.calls, [])

    def test_declared_valid_alternative_must_full_pass(self) -> None:
        runner = FakeRunner(valid_alternative_cases={"F01-S-FAKE-001"})
        result = audit_catalog(
            self.catalog,
            runner,
            case_ids=["F01-S-FAKE-001"],
            max_cases=1,
            failure_policy="continue",
        )
        alternatives = result["cases"][0]["valid_alternatives"]
        self.assertEqual(len(alternatives), 1)
        self.assertEqual(alternatives[0]["alternative_id"], "independent-valid")
        self.assertEqual(alternatives[0]["status"], "pass")

    def test_continue_runs_later_cases_after_a_failure(self) -> None:
        runner = FakeRunner(broken_good_cases={"F01-S-FAKE-001"})
        result = audit_catalog(
            self.catalog,
            runner,
            max_cases=2,
            failure_policy="continue",
        )
        self.assertEqual([item["case_id"] for item in result["cases"]], [
            "F01-S-FAKE-001",
            "F02-S-FAKE-001",
        ])
        self.assertEqual([item["status"] for item in result["cases"]], ["fail", "pass"])

    def test_fail_fast_stops_before_the_later_case(self) -> None:
        runner = FakeRunner(broken_good_cases={"F01-S-FAKE-001"})
        result = audit_catalog(
            self.catalog,
            runner,
            max_cases=2,
            failure_policy="fail-fast",
        )
        self.assertEqual([item["case_id"] for item in result["cases"]], [
            "F01-S-FAKE-001",
        ])
        self.assertNotIn(("digest", "F02-S-FAKE-001"), runner.calls)
        self.assertEqual(result["cases"][0]["checks"][-1]["check_id"], "known-good-full-pass")

    def test_filters_are_intersected_and_summary_is_content_free(self) -> None:
        runner = FakeRunner()
        result = audit_catalog(
            self.catalog,
            runner,
            families=["family-two"],
            case_ids=["F02-S-FAKE-001"],
            max_cases=1,
            failure_policy="continue",
        )
        self.assertEqual(result["status"], "pass")
        self.assertEqual(result["cases"][0]["family"], "family-two")
        serialized = str(result)
        for forbidden in ("capsules/", "fixture-", "exception", "prompt", "stdout", "stderr"):
            self.assertNotIn(forbidden, serialized)


if __name__ == "__main__":
    unittest.main()
