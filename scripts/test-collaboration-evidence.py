#!/usr/bin/env python3

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from collaboration_evidence import EvidenceReportError, build_report  # noqa: E402


CLI = SCRIPT_DIR / "report-agent-collaboration-evidence"


def episode(**overrides: object) -> dict[str, object]:
    value: dict[str, object] = {
        "schemaVersion": 1,
        "id": "opaque-episode",
        "session": "opaque-session",
        "workspace": "0123456789abcdef",
        "source": "agentctl",
        "provider": "claude",
        "durationMs": 1000,
        "terminalOutcome": "success",
        "completion": "observed-terminal",
        "topology": "managed-job",
        "testOutcomes": {"success": 1, "failure": 0, "unknown": 0},
        "delegation": {"starts": 1, "peakConcurrent": 1, "workerActiveMs": 700},
        "reviewProxy": {"available": False, "elapsedMs": None},
        "reworkProxy": {"testRecoveries": 0, "editEventsAfterTestFailure": 0},
        "semantics": {
            "expectedMechanisms": ["coverage"],
            "bindingConstraint": "evaluator",
            "relation": "consult",
            "lifecycle": "bounded-exchange",
            "annotationSource": "primary-plan",
            "correlation": {
                "available": True,
                "plan": "1111111111111111",
                "candidate": "2222222222222222",
                "decisionDigest": "sha256:" + "a" * 64,
            },
        },
        "coverage": {"startObserved": True, "terminalObserved": True, "workerStartsObserved": True},
    }
    value.update(overrides)
    return value


class CollaborationEvidenceTests(unittest.TestCase):
    def test_empty_ledger_is_unmeasured(self) -> None:
        report = build_report({"schemaVersion": 1, "episodes": []})
        self.assertEqual(report["status"], "unmeasured")
        self.assertEqual(report["groups"], [])

    def test_report_groups_exact_semantics_and_describes_observed_time(self) -> None:
        report = build_report(
            {"schemaVersion": 1, "episodes": [episode(durationMs=1000), episode(durationMs=3000)]}
        )
        self.assertEqual(report["decisionCoverage"]["correlatedEpisodes"], 2)
        self.assertEqual(report["decisionCoverage"]["opaquePlans"], 1)
        group = report["groups"][0]
        self.assertEqual(group["dimensions"]["relation"], "consult")
        self.assertEqual(group["durationMs"], {"observations": 2, "min": 1000, "median": 2000, "max": 3000})
        self.assertEqual(group["terminalOutcomes"], {"success": 2})

    def test_untrusted_free_text_is_not_emitted(self) -> None:
        secret = "private-customer-semantic"
        malicious = episode(source=secret, provider=secret, topology=secret)
        malicious["semantics"] = {
            "relation": secret,
            "lifecycle": secret,
            "bindingConstraint": secret,
            "expectedMechanisms": [secret],
            "correlation": {"available": True, "plan": secret, "candidate": secret},
        }
        report = build_report({"schemaVersion": 1, "episodes": [malicious]})
        serialized = json.dumps(report)
        self.assertNotIn(secret, serialized)
        dimensions = report["groups"][0]["dimensions"]
        self.assertEqual(dimensions["source"], "unknown")
        self.assertEqual(dimensions["relation"], "unknown")

    def test_workspace_filter_does_not_echo_the_key(self) -> None:
        key = "0123456789abcdef"
        report = build_report({"episodes": [episode()]}, workspace=key)
        self.assertEqual(report["input"]["validEpisodes"], 1)
        self.assertNotIn(key, json.dumps(report))

    def test_episode_and_group_bounds_are_enforced(self) -> None:
        with self.assertRaises(EvidenceReportError):
            build_report({"episodes": []}, max_episodes=5000)
        ledger = {"episodes": [episode(durationMs=index) for index in range(1, 5)]}
        report = build_report(ledger, max_episodes=2)
        self.assertEqual(report["input"]["consideredEpisodes"], 2)

    def test_cli_missing_ledger_returns_unmeasured_json(self) -> None:
        with tempfile.TemporaryDirectory() as raw_temp:
            result = subprocess.run(
                [sys.executable, str(CLI), "--ledger", str(Path(raw_temp) / "missing.json")],
                text=True,
                capture_output=True,
                check=False,
            )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["status"], "unmeasured")

    def test_cli_markdown_contains_limits_not_episode_ids(self) -> None:
        with tempfile.TemporaryDirectory() as raw_temp:
            ledger = Path(raw_temp) / "ledger.json"
            ledger.write_text(json.dumps({"schemaVersion": 1, "episodes": [episode()]}), encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(CLI), "--ledger", str(ledger), "--format", "markdown"],
                text=True,
                capture_output=True,
                check=False,
            )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Interpretation limits", result.stdout)
        self.assertNotIn("opaque-episode", result.stdout)


if __name__ == "__main__":
    unittest.main()
