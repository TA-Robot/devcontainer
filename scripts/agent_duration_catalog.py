"""Compose the versioned aggregate duration catalog from exclusive family fragments."""

from __future__ import annotations

import json
import os
from pathlib import Path
import re
import tempfile
from typing import Any

from agent_contracts import load_json
from agent_duration_study import DurationStudyError, ROOT, validate_case_catalog_record


FAMILY_DIRECTORY = ROOT / "experiments" / "multi-agent-duration" / "catalog" / "families"
AGGREGATE_PATH = ROOT / "experiments" / "multi-agent-duration" / "catalog" / "cases.json"
FAMILY_FILE = re.compile(r"^(f[0-9]{2})\.json$")
ALL_FAMILY_CODES = {f"f{index:02d}" for index in range(1, 13)}


def _load_family_fragment(path: Path, family_code: str) -> dict[str, Any]:
    value = load_json(path)
    if not isinstance(value, dict):
        raise DurationStudyError(f"duration family fragment root must be an object: {path}")
    validate_case_catalog_record(value)
    if value["catalog_id"] != f"duration-atlas-{family_code}":
        raise DurationStudyError(f"duration family catalog_id does not match filename: {path}")
    entries = value["entries"]
    if len(entries) != 3 or {entry["case"]["size"] for entry in entries} != {"S", "M", "L"}:
        raise DurationStudyError(f"duration family fragment must contain exactly S/M/L: {path}")
    expected_prefix = family_code.upper()
    case_prefixes = {entry["case"]["case_id"][:3] for entry in entries}
    if case_prefixes != {expected_prefix}:
        raise DurationStudyError(f"duration family case ID prefix does not match filename: {path}")
    if len({entry["case"]["family"] for entry in entries}) != 1:
        raise DurationStudyError(f"duration family fragment mixes family enums: {path}")
    return value


def compose_catalog(
    *,
    family_directory: Path = FAMILY_DIRECTORY,
    expected_family_codes: set[str] = ALL_FAMILY_CODES,
    revision: int,
    published_at: str,
) -> dict[str, Any]:
    """Load, validate, and merge a complete declared set of family fragments."""

    discovered: dict[str, Path] = {}
    if not family_directory.is_dir():
        raise DurationStudyError(f"duration family directory is missing: {family_directory}")
    for path in family_directory.iterdir():
        match = FAMILY_FILE.fullmatch(path.name)
        if match is None:
            continue
        discovered[match.group(1)] = path
    if set(discovered) != expected_family_codes:
        missing = sorted(expected_family_codes - set(discovered))
        extra = sorted(set(discovered) - expected_family_codes)
        raise DurationStudyError(
            f"duration family fragment set mismatch: missing={missing}, extra={extra}"
        )
    entries: list[dict[str, Any]] = []
    for family_code in sorted(discovered):
        fragment = _load_family_fragment(discovered[family_code], family_code)
        entries.extend(fragment["entries"])
    entries.sort(key=lambda entry: entry["case"]["case_id"])
    aggregate = {
        "schema_version": 1,
        "catalog_id": "duration-atlas-calibration",
        "revision": revision,
        "published_at": published_at,
        "entries": entries,
    }
    validate_case_catalog_record(aggregate)
    return aggregate


def replace_catalog(path: Path, catalog: dict[str, Any]) -> None:
    """Atomically replace the generated aggregate; Git retains the previous revision."""

    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        os.fchmod(descriptor, 0o644)
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(catalog, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
        directory_descriptor = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory_descriptor)
        finally:
            os.close(directory_descriptor)
    finally:
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass


__all__ = [
    "AGGREGATE_PATH",
    "ALL_FAMILY_CODES",
    "FAMILY_DIRECTORY",
    "compose_catalog",
    "replace_catalog",
]
