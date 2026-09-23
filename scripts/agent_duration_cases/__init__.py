"""Deterministic registry for independently owned duration-case recipe modules."""

from __future__ import annotations

import importlib
import pkgutil
import re
from typing import Any


FAMILY_MODULE = re.compile(r"^f[0-9]{2}$")
CASE_ID = re.compile(r"^(F[0-9]{2})-(?:S|M|L)-")


def _recipes_from_module(module_name: str) -> dict[str, dict[str, Any]]:
    module = importlib.import_module(f"{__name__}.{module_name}")
    family_recipes = getattr(module, "RECIPES", None)
    if not isinstance(family_recipes, dict) or not family_recipes:
        raise RuntimeError(f"duration case module {module_name} must export non-empty RECIPES")
    for recipe_id, recipe in family_recipes.items():
        if not isinstance(recipe_id, str) or not isinstance(recipe, dict):
            raise RuntimeError(f"duration case module {module_name} has invalid recipe entry")
        case_id = recipe.get("case_id")
        match = CASE_ID.match(case_id) if isinstance(case_id, str) else None
        if match is None or match.group(1).lower() != module_name:
            raise RuntimeError(
                f"duration case module {module_name} does not own recipe {recipe_id}"
            )
    return family_recipes


def load_case_family_recipes(case_id: str) -> dict[str, dict[str, Any]]:
    """Load only the family owning a requested case, isolating parallel partial work."""

    match = CASE_ID.match(case_id)
    if match is None:
        raise RuntimeError(f"duration case ID has no family prefix: {case_id}")
    module_name = match.group(1).lower()
    recipes = _recipes_from_module(module_name)
    matches = [recipe for recipe in recipes.values() if recipe.get("case_id") == case_id]
    if len(matches) != 1:
        raise RuntimeError(
            f"duration case module {module_name} does not own exactly one {case_id} recipe"
        )
    return recipes


def load_family_recipes() -> dict[str, dict[str, Any]]:
    """Load recipe dictionaries from fXX modules without a shared edit surface."""

    recipes: dict[str, dict[str, Any]] = {}
    module_names = sorted(
        item.name
        for item in pkgutil.iter_modules(__path__)
        if FAMILY_MODULE.fullmatch(item.name)
    )
    for module_name in module_names:
        family_recipes = _recipes_from_module(module_name)
        for recipe_id, recipe in family_recipes.items():
            if recipe_id in recipes:
                raise RuntimeError(f"duplicate duration recipe ID: {recipe_id}")
            recipes[recipe_id] = recipe
    return recipes


__all__ = ["load_case_family_recipes", "load_family_recipes"]
