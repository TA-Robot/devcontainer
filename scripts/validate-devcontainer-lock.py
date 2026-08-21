#!/usr/bin/env python3
"""Validate that devcontainer.json Features are exactly covered by the lockfile."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys


SHA256 = re.compile(r"^sha256:[0-9a-f]{64}$")


def strip_jsonc(text: str) -> str:
    output: list[str] = []
    index = 0
    in_string = False
    escaped = False
    while index < len(text):
        char = text[index]
        next_char = text[index + 1] if index + 1 < len(text) else ""
        if in_string:
            output.append(char)
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            index += 1
            continue
        if char == '"':
            in_string = True
            output.append(char)
            index += 1
            continue
        if char == "/" and next_char == "/":
            index += 2
            while index < len(text) and text[index] not in "\r\n":
                index += 1
            continue
        if char == "/" and next_char == "*":
            index += 2
            while index + 1 < len(text) and text[index : index + 2] != "*/":
                index += 1
            index += 2
            continue
        output.append(char)
        index += 1

    without_comments = "".join(output)
    output = []
    index = 0
    in_string = False
    escaped = False
    while index < len(without_comments):
        char = without_comments[index]
        if in_string:
            output.append(char)
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            index += 1
            continue
        if char == '"':
            in_string = True
            output.append(char)
            index += 1
            continue
        if char == ",":
            lookahead = index + 1
            while lookahead < len(without_comments) and without_comments[lookahead].isspace():
                lookahead += 1
            if lookahead < len(without_comments) and without_comments[lookahead] in "}]":
                index += 1
                continue
        output.append(char)
        index += 1
    return "".join(output)


def validate(config_path: Path, lock_path: Path) -> list[str]:
    errors: list[str] = []
    try:
        config = json.loads(strip_jsonc(config_path.read_text(encoding="utf-8")))
    except (OSError, json.JSONDecodeError) as exc:
        return [f"cannot parse {config_path}: {exc}"]
    try:
        lock = json.loads(lock_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [f"cannot parse {lock_path}: {exc}"]

    configured_entries = config.get("features") or {}
    configured = set(configured_entries.keys())
    locked = lock.get("features")
    if not isinstance(locked, dict):
        return ["lockfile must contain an object at features"]
    locked_keys = set(locked.keys())
    for missing in sorted(configured - locked_keys):
        errors.append(f"configured Feature is missing from lockfile: {missing}")
    for extra in sorted(locked_keys - configured):
        errors.append(f"lockfile contains an unconfigured Feature: {extra}")

    for feature in sorted(configured & locked_keys):
        entry = locked[feature]
        if not isinstance(entry, dict):
            errors.append(f"lock entry is not an object: {feature}")
            continue
        version = entry.get("version")
        resolved = entry.get("resolved")
        integrity = entry.get("integrity")
        if not isinstance(version, str) or not version:
            errors.append(f"lock entry has no version: {feature}")
        if not isinstance(integrity, str) or not SHA256.fullmatch(integrity):
            errors.append(f"lock entry has invalid integrity digest: {feature}")
        if not isinstance(resolved, str) or "@sha256:" not in resolved:
            errors.append(f"lock entry is not digest-resolved: {feature}")
        elif isinstance(integrity, str) and resolved.rsplit("@", 1)[-1] != integrity:
            errors.append(f"resolved and integrity digests differ: {feature}")

    floating_values = {"latest", "current", "lts", "stable"}
    for feature, options in configured_entries.items():
        if not isinstance(options, dict):
            continue
        for option, value in options.items():
            if isinstance(value, str) and value.lower() in floating_values:
                errors.append(f"stable Feature option must not float: {feature} {option}={value}")

    docker_feature = next((name for name in configured if "docker-in-docker" in name), None)
    if docker_feature:
        docker_options = configured_entries.get(docker_feature) or {}
        if docker_options.get("dockerDashComposeVersion") != "none":
            errors.append("stable Docker Compose must use the separately pinned Dockerfile plugin")
        if docker_options.get("installDockerBuildx") is not False:
            errors.append("stable Docker Buildx must use the pinned Moby package, not a Feature download")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--lock", type=Path, required=True)
    args = parser.parse_args()
    errors = validate(args.config.resolve(), args.lock.resolve())
    if errors:
        for error in errors:
            print(f"error: {error}", file=sys.stderr)
        return 1
    print(f"ok - {args.lock} exactly locks configured Dev Container Features")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
