#!/usr/bin/env python3

from __future__ import annotations

import copy
from pathlib import Path
import sys
import unittest


SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(SCRIPT_DIR))

from agent_contracts import load_json  # noqa: E402
from agent_duration_validity import (  # noqa: E402
    DEFAULT_CATALOG,
    DEFAULT_VALIDITY,
    ValidityError,
    classify_observation,
    load_validated_validity,
    summarize_case_validity,
    validate_validity_record,
    validity_index,
)


class AgentDurationValidityTests(unittest.TestCase):
    def test_checked_in_audit_matches_current_catalog(self) -> None:
        record = load_validated_validity()
        index = validity_index(record)
        self.assertEqual(index[("F06-L-PYBASH-001", 1)]["design_status"], "conditional")
        self.assertEqual(index[("F06-L-PYBASH-001", 2)]["design_status"], "eligible")
        self.assertEqual(index[("F10-S-PY-001", 1)]["design_status"], "ineligible")
        self.assertEqual(index[("F10-S-PY-001", 2)]["design_status"], "ineligible")
        self.assertEqual(index[("F10-S-PY-001", 3)]["design_status"], "conditional")
        self.assertEqual(index[("F10-S-PY-001", 4)]["design_status"], "conditional")
        self.assertEqual(index[("F10-S-PY-001", 5)]["design_status"], "eligible")
        self.assertEqual(index[("F12-L-MDJSON-001", 1)]["design_status"], "ineligible")
        self.assertEqual(index[("F12-L-MDJSON-001", 2)]["design_status"], "ineligible")
        self.assertEqual(index[("F12-L-MDJSON-001", 3)]["solution_space_calibration"], "plural-gold")
        self.assertEqual(index[("F09-L-PYBASHDOCKER-001", 1)]["design_status"], "conditional")

    def test_rejects_catalog_digest_drift(self) -> None:
        record = load_json(DEFAULT_VALIDITY)
        catalog = load_json(DEFAULT_CATALOG)
        changed = copy.deepcopy(record)
        changed["catalog"]["digest"] = "sha256:" + "0" * 64
        with self.assertRaisesRegex(ValidityError, "digest"):
            validate_validity_record(changed, catalog=catalog)

    def test_failed_observation_needs_retained_artifact(self) -> None:
        record = load_validated_validity()
        entry = validity_index(record)[("F06-L-PYBASH-001", 2)]
        self.assertEqual(
            classify_observation(
                entry,
                quality_population="quality-fail",
                artifact_retention="content-free-only",
            ),
            {"status": "conditional", "reason": "task-artifact-not-retained"},
        )
        self.assertEqual(
            classify_observation(
                entry,
                quality_population="quality-fail",
                artifact_retention="task-artifacts",
                artifact_completeness="complete",
                artifact_available=True,
            )["status"],
            "eligible",
        )
        self.assertEqual(
            classify_observation(
                entry,
                quality_population="quality-fail",
                artifact_retention="task-artifacts",
                artifact_completeness="complete",
                artifact_available=False,
            ),
            {"status": "conditional", "reason": "task-artifact-missing"},
        )

    def test_ineligible_revision_is_excluded_even_with_artifact(self) -> None:
        record = load_validated_validity()
        entry = validity_index(record)[("F12-L-MDJSON-001", 1)]
        self.assertEqual(
            classify_observation(
                entry,
                quality_population="quality-fail",
                artifact_retention="task-artifacts",
            ),
            {"status": "excluded", "reason": "case-design-ineligible"},
        )

    def test_case_summary_surfaces_observation_gate_and_pending_comparison(self) -> None:
        validity = load_validated_validity()
        case = {
            "primary_stratum": {
                "case": {"case_id": "F06-L-PYBASH-001", "revision": 2}
            },
            "samples": [
                {
                    "run_id": "pass",
                    "quality_population": "quality-pass",
                    "outcome": {"artifact": "valid"},
                },
                {
                    "run_id": "fail",
                    "quality_population": "quality-fail",
                    "outcome": {"artifact": "valid"},
                },
            ],
        }
        summary = summarize_case_validity(case, validity)
        self.assertEqual(summary["effort_quality_use"], "conditional-only")
        self.assertIn("task-artifact-not-retained", summary["reason_codes"])

        case["samples"] = [
            {
                "run_id": "pass",
                "quality_population": "quality-pass",
                "outcome": {"artifact": "valid"},
            }
        ]
        summary = summarize_case_validity(case, validity)
        self.assertEqual(
            summary["effort_quality_use"],
            "eligible-pending-comparison-gates",
        )

    def test_conditional_design_without_quality_is_excluded(self) -> None:
        validity = load_validated_validity()
        case = {
            "primary_stratum": {
                "case": {"case_id": "F09-L-PYBASHDOCKER-001", "revision": 1}
            },
            "samples": [
                {
                    "run_id": "unknown",
                    "quality_population": "quality-unknown",
                    "outcome": {"artifact": "missing"},
                }
            ],
        }
        summary = summarize_case_validity(case, validity)
        self.assertEqual(summary["effort_quality_use"], "excluded")
        self.assertIn("quality-unobserved", summary["reason_codes"])


if __name__ == "__main__":
    unittest.main()
