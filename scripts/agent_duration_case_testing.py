"""Shared calibration assertions for independently implemented duration families."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import tempfile
from typing import Any
import unittest

from agent_contracts import load_json
from agent_duration_fixtures import (
    _install_known_good_for_test,
    _install_mutant_for_test,
    _recipe_for_case,
    build_fixture,
    evaluate_fixture,
)
from agent_duration_study import validate_case_catalog_record


FIXED_CALIBRATION_TIME = datetime(2026, 8, 27, 12, 0, tzinfo=timezone.utc)


def assert_family_calibrated(
    testcase: unittest.TestCase,
    catalog_path: Path,
) -> None:
    """Validate and calibrate every case/mutant in one standalone family fragment."""

    catalog = load_json(catalog_path)
    testcase.assertIsInstance(catalog, dict)
    validate_case_catalog_record(catalog)
    entries: list[dict[str, Any]] = catalog["entries"]
    testcase.assertEqual(len(entries), 3)
    testcase.assertEqual({entry["case"]["size"] for entry in entries}, {"S", "M", "L"})
    testcase.assertEqual(len({entry["case"]["family"] for entry in entries}), 1)

    with tempfile.TemporaryDirectory(prefix="duration-family-calibration-") as raw:
        root = Path(raw)
        for entry in entries:
            case_id = entry["case"]["case_id"]
            recipe_id = entry["fixture"]["recipe_id"]
            recipe = _recipe_for_case(case_id, recipe_id)
            testcase.assertEqual(recipe.get("case_id"), case_id)

            fixture_dir = root / f"good-{case_id.lower()}"
            manifest = build_fixture(
                case_id,
                fixture_dir,
                catalog_path=catalog_path,
                fixture_id=f"calibration-{case_id.lower()}",
                now=FIXED_CALIBRATION_TIME,
            )
            testcase.assertEqual(manifest["initial_oracle"]["observed"], "fail")
            workspace = fixture_dir / "workspace"
            _install_known_good_for_test(case_id, workspace)
            good = evaluate_fixture(fixture_dir)
            testcase.assertEqual(good["status"], "pass", good)
            testcase.assertEqual(good["score"]["ratio"], 1.0)

            mutants = recipe.get("mutants", {})
            testcase.assertIsInstance(mutants, dict)
            testcase.assertGreaterEqual(len(mutants), 1)
            for mutant_id in sorted(mutants):
                mutant_dir = root / f"mutant-{case_id.lower()}-{mutant_id}"
                build_fixture(
                    case_id,
                    mutant_dir,
                    catalog_path=catalog_path,
                    fixture_id=f"mutant-{case_id.lower()}-{mutant_id}",
                    now=FIXED_CALIBRATION_TIME,
                )
                expected = _install_mutant_for_test(
                    case_id,
                    mutant_id,
                    mutant_dir / "workspace",
                )
                result = evaluate_fixture(mutant_dir)
                testcase.assertEqual(result["status"], "fail", (case_id, mutant_id, result))
                failed = set(result["score"]["failed_check_ids"])
                testcase.assertTrue(
                    set(expected).issubset(failed),
                    (case_id, mutant_id, expected, sorted(failed)),
                )


__all__ = ["assert_family_calibrated"]
