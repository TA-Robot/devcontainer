#!/usr/bin/env python3

from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile
import unittest


SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(SCRIPT_DIR))

from agent_contracts import load_json  # noqa: E402
from agent_duration_catalog import compose_catalog, replace_catalog  # noqa: E402
from agent_duration_study import DurationStudyError  # noqa: E402


class AgentDurationCatalogTests(unittest.TestCase):
    def make_fragment(self, directory: Path, filename: str = "f04.json") -> Path:
        catalog = load_json(
            ROOT / "experiments" / "multi-agent-duration" / "catalog" / "cases.json"
        )
        catalog["catalog_id"] = "duration-atlas-f04"
        path = directory / filename
        path.write_text(json.dumps(catalog), encoding="utf-8")
        return path

    def test_composes_one_declared_family_and_replaces_atomically(self) -> None:
        with tempfile.TemporaryDirectory(prefix="duration-catalog-") as raw:
            root = Path(raw)
            families = root / "families"
            families.mkdir()
            self.make_fragment(families)
            result = compose_catalog(
                family_directory=families,
                expected_family_codes={"f04"},
                revision=3,
                published_at="2026-08-27T00:00:00.000Z",
            )
            self.assertEqual(result["catalog_id"], "duration-atlas-calibration")
            self.assertEqual(result["revision"], 3)
            self.assertEqual(len(result["entries"]), 3)
            output = root / "cases.json"
            replace_catalog(output, result)
            self.assertEqual(load_json(output), result)

    def test_rejects_missing_and_misnamed_family_fragments(self) -> None:
        with tempfile.TemporaryDirectory(prefix="duration-catalog-bad-") as raw:
            families = Path(raw)
            self.make_fragment(families, "f03.json")
            with self.assertRaisesRegex(DurationStudyError, "catalog_id does not match"):
                compose_catalog(
                    family_directory=families,
                    expected_family_codes={"f03"},
                    revision=3,
                    published_at="2026-08-27T00:00:00.000Z",
                )
            with self.assertRaisesRegex(DurationStudyError, "fragment set mismatch"):
                compose_catalog(
                    family_directory=families,
                    expected_family_codes={"f01", "f03"},
                    revision=3,
                    published_at="2026-08-27T00:00:00.000Z",
                )


if __name__ == "__main__":
    unittest.main()
