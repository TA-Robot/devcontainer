"""Deterministic registry for independently owned duration-case recipe modules."""

from __future__ import annotations

import importlib
import pkgutil
import re
from typing import Any


FAMILY_MODULE = re.compile(r"^f[0-9]{2}$")


def load_family_recipes() -> dict[str, dict[str, Any]]:
    """Load recipe dictionaries from fXX modules without a shared edit surface."""

    recipes: dict[str, dict[str, Any]] = {}
    module_names = sorted(
        item.name
        for item in pkgutil.iter_modules(__path__)
        if FAMILY_MODULE.fullmatch(item.name)
    )
    for module_name in module_names:
        module = importlib.import_module(f"{__name__}.{module_name}")
        family_recipes = getattr(module, "RECIPES", None)
        if not isinstance(family_recipes, dict) or not family_recipes:
            raise RuntimeError(f"duration case module {module_name} must export non-empty RECIPES")
        for recipe_id, recipe in family_recipes.items():
            if not isinstance(recipe_id, str) or not isinstance(recipe, dict):
                raise RuntimeError(f"duration case module {module_name} has invalid recipe entry")
            if recipe_id in recipes:
                raise RuntimeError(f"duplicate duration recipe ID: {recipe_id}")
            recipes[recipe_id] = recipe
    return recipes


__all__ = ["load_family_recipes"]
