#!/usr/bin/env python3
"""Small dependency-free validator for the agent task/result contract.

This intentionally implements only the JSON Schema keywords used by the
checked-in v1 schemas. Unknown keywords are annotations, as allowed by JSON
Schema. Provider adapters can reuse this module until a full validator becomes
an explicit runtime dependency.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


class ContractValidationError(ValueError):
    """Raised when an instance does not satisfy the checked-in contract."""


def _type_matches(value: Any, expected: str) -> bool:
    if expected == "null":
        return value is None
    if expected == "boolean":
        return isinstance(value, bool)
    if expected == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if expected == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if expected == "string":
        return isinstance(value, str)
    if expected == "array":
        return isinstance(value, list)
    if expected == "object":
        return isinstance(value, dict)
    raise ContractValidationError(f"unsupported schema type: {expected!r}")


def _resolve_ref(root: dict[str, Any], ref: str) -> dict[str, Any]:
    if not ref.startswith("#/"):
        raise ContractValidationError(f"only local JSON pointers are supported: {ref}")
    node: Any = root
    for encoded_part in ref[2:].split("/"):
        part = encoded_part.replace("~1", "/").replace("~0", "~")
        if not isinstance(node, dict) or part not in node:
            raise ContractValidationError(f"unresolvable schema reference: {ref}")
        node = node[part]
    if not isinstance(node, dict):
        raise ContractValidationError(f"schema reference is not an object: {ref}")
    return node


def _is_valid(instance: Any, schema: dict[str, Any], root: dict[str, Any]) -> bool:
    try:
        validate(instance, schema, root=root)
    except ContractValidationError:
        return False
    return True


def validate(
    instance: Any,
    schema: dict[str, Any],
    *,
    root: dict[str, Any] | None = None,
    path: str = "$",
) -> None:
    """Validate one instance against the supported v1 JSON Schema subset."""

    root = schema if root is None else root

    if "$ref" in schema:
        validate(instance, _resolve_ref(root, schema["$ref"]), root=root, path=path)

    if "type" in schema:
        expected = schema["type"]
        expected_types = expected if isinstance(expected, list) else [expected]
        if not any(_type_matches(instance, item) for item in expected_types):
            raise ContractValidationError(
                f"{path}: expected type {' | '.join(expected_types)}, "
                f"got {type(instance).__name__}"
            )

    if "const" in schema and instance != schema["const"]:
        raise ContractValidationError(f"{path}: expected constant {schema['const']!r}")
    if "enum" in schema and instance not in schema["enum"]:
        raise ContractValidationError(f"{path}: value {instance!r} is not in enum")

    if isinstance(instance, str):
        if len(instance) < schema.get("minLength", 0):
            raise ContractValidationError(f"{path}: string is shorter than minLength")
        if "maxLength" in schema and len(instance) > schema["maxLength"]:
            raise ContractValidationError(f"{path}: string is longer than maxLength")
        if "pattern" in schema and re.search(schema["pattern"], instance) is None:
            raise ContractValidationError(f"{path}: string does not match required pattern")

    if isinstance(instance, list):
        if len(instance) < schema.get("minItems", 0):
            raise ContractValidationError(f"{path}: array has fewer than minItems")
        if "maxItems" in schema and len(instance) > schema["maxItems"]:
            raise ContractValidationError(f"{path}: array has more than maxItems")
        if schema.get("uniqueItems"):
            canonical = [json.dumps(item, sort_keys=True, separators=(",", ":")) for item in instance]
            if len(canonical) != len(set(canonical)):
                raise ContractValidationError(f"{path}: array items must be unique")
        if "items" in schema:
            for index, item in enumerate(instance):
                validate(item, schema["items"], root=root, path=f"{path}[{index}]")

    if isinstance(instance, dict):
        required = schema.get("required", [])
        for key in required:
            if key not in instance:
                raise ContractValidationError(f"{path}: missing required property {key!r}")
        properties = schema.get("properties", {})
        if schema.get("additionalProperties") is False:
            extras = sorted(set(instance) - set(properties))
            if extras:
                raise ContractValidationError(f"{path}: unexpected properties: {', '.join(extras)}")
        for key, child_schema in properties.items():
            if key in instance:
                validate(instance[key], child_schema, root=root, path=f"{path}.{key}")

    if "allOf" in schema:
        for child_schema in schema["allOf"]:
            validate(instance, child_schema, root=root, path=path)

    if "anyOf" in schema:
        matches = sum(_is_valid(instance, item, root) for item in schema["anyOf"])
        if matches == 0:
            raise ContractValidationError(f"{path}: no anyOf branch matched")

    if "oneOf" in schema:
        matches = sum(_is_valid(instance, item, root) for item in schema["oneOf"])
        if matches != 1:
            raise ContractValidationError(f"{path}: expected one oneOf match, got {matches}")

    if "if" in schema:
        branch = "then" if _is_valid(instance, schema["if"], root) else "else"
        if branch in schema:
            validate(instance, schema[branch], root=root, path=path)


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ContractValidationError(f"cannot load JSON {path}: {exc}") from exc


def validate_file(instance_path: Path, schema_path: Path) -> None:
    schema = load_json(schema_path)
    instance = load_json(instance_path)
    if not isinstance(schema, dict):
        raise ContractValidationError(f"schema root must be an object: {schema_path}")
    validate(instance, schema)
