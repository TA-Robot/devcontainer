#!/usr/bin/env python3

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest import mock


SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from agent_duration_cases import (  # noqa: E402
    load_case_family_recipes,
    load_family_recipes,
)


class DurationCaseRegistryTests(unittest.TestCase):
    def test_case_loader_imports_only_requested_family(self) -> None:
        requested = mock.Mock(
            RECIPES={"f01-s-test-v1": {"case_id": "F01-S-PY-001"}}
        )
        with mock.patch(
            "agent_duration_cases.importlib.import_module", return_value=requested
        ) as importer:
            recipes = load_case_family_recipes("F01-S-PY-001")
        self.assertEqual(recipes, requested.RECIPES)
        importer.assert_called_once_with("agent_duration_cases.f01")

    def test_case_loader_rejects_recipe_owned_by_another_family(self) -> None:
        wrong_owner = mock.Mock(
            RECIPES={"f01-s-test-v1": {"case_id": "F02-S-PY-001"}}
        )
        with (
            mock.patch(
                "agent_duration_cases.importlib.import_module",
                return_value=wrong_owner,
            ),
            self.assertRaisesRegex(RuntimeError, "does not own recipe"),
        ):
            load_case_family_recipes("F01-S-PY-001")

    def test_registry_is_deterministic_and_well_formed_during_rollout(self) -> None:
        first = load_family_recipes()
        second = load_family_recipes()
        self.assertEqual(first, second)
        for recipe_id, recipe in first.items():
            self.assertRegex(recipe_id, r"^f[0-9]{2}-[sml]-[a-z0-9-]+-v[0-9]+$")
            self.assertRegex(recipe["case_id"], r"^F[0-9]{2}-(?:S|M|L)-")

    def test_duplicate_recipe_ids_fail_closed(self) -> None:
        first = mock.Mock(RECIPES={"same": {"case_id": "F01-S-PY-001"}})
        second = mock.Mock(RECIPES={"same": {"case_id": "F02-S-PY-001"}})
        discovered = [mock.Mock(name="f01"), mock.Mock(name="f02")]
        discovered[0].name = "f01"
        discovered[1].name = "f02"
        with (
            mock.patch("agent_duration_cases.pkgutil.iter_modules", return_value=discovered),
            mock.patch(
                "agent_duration_cases.importlib.import_module",
                side_effect=[first, second],
            ),
            self.assertRaisesRegex(RuntimeError, "duplicate duration recipe ID"),
        ):
            load_family_recipes()


if __name__ == "__main__":
    unittest.main()
