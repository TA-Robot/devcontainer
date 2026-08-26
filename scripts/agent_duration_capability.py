#!/usr/bin/env python3
"""Content-free passive capability probes for duration-study providers."""

from __future__ import annotations

import json
import math
import os
import re
import subprocess
import time
from datetime import datetime, timezone
from typing import Any

from agent_duration_study import DurationStudyError, utc_timestamp, validate_record


PROVIDERS = ("codex", "claude", "grok")
ANSI_ESCAPE = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]")
SEMVER = re.compile(r"(?<![0-9])([0-9]+\.[0-9]+\.[0-9]+(?:[-+][0-9A-Za-z.-]+)?)")
CAPABILITY_ID = re.compile(r"^[a-z0-9][a-z0-9._-]{0,127}$")
IMAGE_DIGEST = re.compile(r"^sha256:[0-9a-f]{64}$")


def _clean_output(value: str) -> str:
    return ANSI_ESCAPE.sub("", value).replace("\r\n", "\n")


def _version_from_output(value: str) -> str:
    match = SEMVER.search(value)
    return match.group(1) if match else "unknown"


def _run_command(
    binary: str,
    arguments: list[str],
    *,
    command_id: str,
    evidence_source: str,
    timeout_seconds: float,
) -> tuple[dict[str, Any], str]:
    started_ns = time.monotonic_ns()
    environment = dict(os.environ)
    environment.setdefault("NO_COLOR", "1")
    environment.setdefault("TERM", "dumb")
    try:
        completed = subprocess.run(
            [binary, *arguments],
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=timeout_seconds,
            env=environment,
        )
    except FileNotFoundError:
        duration_ms = round((time.monotonic_ns() - started_ns) / 1_000_000, 3)
        return (
            {
                "command_id": command_id,
                "status": "unavailable",
                "evidence_source": evidence_source,
                "duration_ms": duration_ms,
            },
            "",
        )
    except subprocess.TimeoutExpired:
        duration_ms = round((time.monotonic_ns() - started_ns) / 1_000_000, 3)
        return (
            {
                "command_id": command_id,
                "status": "timed-out",
                "evidence_source": evidence_source,
                "duration_ms": duration_ms,
            },
            "",
        )
    except OSError:
        duration_ms = round((time.monotonic_ns() - started_ns) / 1_000_000, 3)
        return (
            {
                "command_id": command_id,
                "status": "unavailable",
                "evidence_source": evidence_source,
                "duration_ms": duration_ms,
            },
            "",
        )

    duration_ms = round((time.monotonic_ns() - started_ns) / 1_000_000, 3)
    status = "observed" if completed.returncode == 0 else "failed"
    observation = {
        "command_id": command_id,
        "status": status,
        "evidence_source": evidence_source,
        "duration_ms": duration_ms,
        "exit_code": completed.returncode,
    }
    if status != "observed":
        return observation, ""
    return observation, _clean_output(f"{completed.stdout}\n{completed.stderr}")


def _catalog_entry(
    model_id: str,
    *,
    catalog_status: str,
    display_name: str | None = None,
    snapshot_hint: str | None = None,
    identity_confidence: str | None = None,
) -> dict[str, Any]:
    entry: dict[str, Any] = {
        "model_id": model_id,
        "catalog_status": catalog_status,
        "identity_confidence": identity_confidence
        or ("catalog-id-with-snapshot" if snapshot_hint else "catalog-id"),
    }
    if display_name:
        entry["display_name"] = display_name
    if snapshot_hint:
        entry["snapshot_hint"] = snapshot_hint
    return entry


def _parse_codex_catalog(
    raw: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], bool]:
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        return [], [], False
    models = payload.get("models") if isinstance(payload, dict) else None
    if not isinstance(models, list):
        return [], [], False

    inventory: list[dict[str, Any]] = []
    surfaces: list[dict[str, Any]] = []
    complete = True
    for item in models:
        if not isinstance(item, dict) or not isinstance(item.get("slug"), str):
            complete = False
            continue
        model_id = item["slug"].strip()
        if not model_id:
            complete = False
            continue
        display_name = item.get("display_name")
        if not isinstance(display_name, str) or not display_name.strip():
            display_name = None
        snapshot_hint = item.get("comp_hash")
        if not isinstance(snapshot_hint, str) or not snapshot_hint.strip():
            snapshot_hint = None
        inventory.append(
            _catalog_entry(
                model_id,
                display_name=display_name,
                snapshot_hint=snapshot_hint,
                catalog_status="hidden" if item.get("visibility") == "hide" else "available",
            )
        )

        advertised = item.get("supported_reasoning_levels")
        values: list[str] = []
        if isinstance(advertised, list):
            for level in advertised:
                effort = level.get("effort") if isinstance(level, dict) else None
                if isinstance(effort, str) and effort and effort not in values:
                    values.append(effort)
                else:
                    complete = False
        else:
            complete = False
        if values:
            surface: dict[str, Any] = {
                "namespace": "codex.reasoning",
                "key": "effort",
                "model_selector": model_id,
                "advertisement": "enumerated",
                "advertised_values": values,
                "evidence_source": "model-catalog",
                "application_observability": "not-observed",
            }
            default = item.get("default_reasoning_level")
            if isinstance(default, str) and default in values:
                surface["default_value"] = default
            elif default is not None:
                complete = False
            surfaces.append(surface)
    return inventory, surfaces, complete


def _flag_values(help_text: str, flag: str) -> tuple[bool, list[str]]:
    position = help_text.find(flag)
    if position < 0:
        return False, []
    fragment = help_text[position : position + 600]
    next_option = re.search(r"\n\s{2,}--[a-z]", fragment[1:])
    if next_option:
        fragment = fragment[: next_option.start() + 1]
    choices = re.search(r"\(([^()\n]+)\)", fragment)
    if not choices:
        return True, []
    values = [item.strip() for item in choices.group(1).split(",")]
    return True, [item for item in values if re.fullmatch(r"[A-Za-z0-9._-]+", item)]


def _parse_claude_help(raw: str) -> list[dict[str, Any]]:
    advertised, values = _flag_values(raw, "--effort <level>")
    if not advertised:
        return [
            {
                "namespace": "claude.reasoning",
                "key": "effort",
                "advertisement": "not-advertised",
                "evidence_source": "root-help",
                "application_observability": "not-observed",
            }
        ]
    surface: dict[str, Any] = {
        "namespace": "claude.reasoning",
        "key": "effort",
        "advertisement": "enumerated" if values else "flag-only",
        "evidence_source": "root-help",
        "application_observability": "not-observed",
    }
    if values:
        surface["advertised_values"] = values
    return [surface]


def _parse_grok_models(
    raw: str,
) -> tuple[list[dict[str, Any]], str | None, bool]:
    default_match = re.search(r"^Default model:\s*(\S+)\s*$", raw, re.MULTILINE)
    default_model = default_match.group(1) if default_match else None
    inventory: list[dict[str, Any]] = []
    for match in re.finditer(r"^\s*[*-]\s+(\S+?)(?:\s+\(default\))?\s*$", raw, re.MULTILINE):
        model_id = match.group(1)
        inventory.append(
            _catalog_entry(
                model_id,
                catalog_status=(
                    "advertised-default" if model_id == default_model else "available"
                ),
                identity_confidence="alias-only",
            )
        )
    complete = bool(inventory) and default_model is not None
    if default_model is not None and default_model not in {item["model_id"] for item in inventory}:
        complete = False
    return inventory, default_model, complete


def _parse_grok_help(raw: str) -> list[dict[str, Any]]:
    advertised = "--reasoning-effort <EFFORT>" in raw or "--effort <EFFORT>" in raw
    return [
        {
            "namespace": "grok.reasoning",
            "key": "effort",
            "advertisement": "flag-only" if advertised else "not-advertised",
            "evidence_source": "root-help",
            "application_observability": "not-observed",
        }
    ]


def _grok_build_identity(version_output: str) -> tuple[str | None, str | None]:
    build = re.search(r"\(([0-9a-f]{7,64})\)", version_output)
    channel = re.search(r"\[([a-z0-9._-]+)\]", version_output, re.IGNORECASE)
    return (
        build.group(1) if build else None,
        channel.group(1).lower() if channel else None,
    )


def _capability_id(provider: str, observed_at: str) -> str:
    compact_time = re.sub(r"[^0-9]", "", observed_at)
    return f"{provider}-passive-{compact_time}-{os.getpid()}"


def probe_capability(
    provider: str,
    *,
    binary: str | None = None,
    cli_source: str = "unknown",
    environment_kind: str = "unknown",
    image_digest: str | None = None,
    timeout_seconds: float = 15.0,
    offline_only: bool = False,
    capability_id: str | None = None,
    now: datetime | None = None,
) -> dict[str, Any]:
    """Observe provider CLI metadata without issuing a model-generation request."""

    if provider not in PROVIDERS:
        raise DurationStudyError(f"unsupported capability provider: {provider}")
    if not math.isfinite(timeout_seconds) or timeout_seconds <= 0 or timeout_seconds > 60:
        raise DurationStudyError("capability command timeout must be > 0 and <= 60 seconds")
    if cli_source not in {"container-image", "host-sync", "fixture", "unknown"}:
        raise DurationStudyError(f"unsupported CLI source: {cli_source}")
    if environment_kind not in {"host", "devcontainer", "fixture", "unknown"}:
        raise DurationStudyError(f"unsupported environment kind: {environment_kind}")
    if image_digest is not None and IMAGE_DIGEST.fullmatch(image_digest) is None:
        raise DurationStudyError("image digest must be a lowercase sha256 value")
    if capability_id is not None and CAPABILITY_ID.fullmatch(capability_id) is None:
        raise DurationStudyError("capability ID must match the capability schema ID format")
    if now is not None and now.tzinfo is None:
        raise DurationStudyError("capability observation time must be timezone-aware")

    observed_at = utc_timestamp(now or datetime.now(timezone.utc))
    executable = binary or provider
    commands: list[dict[str, Any]] = []
    version_command, version_output = _run_command(
        executable,
        ["--version"],
        command_id="version",
        evidence_source="version-output",
        timeout_seconds=timeout_seconds,
    )
    commands.append(version_command)
    help_command, help_output = _run_command(
        executable,
        ["--help"],
        command_id="root-help",
        evidence_source="root-help",
        timeout_seconds=timeout_seconds,
    )
    commands.append(help_command)

    inventory: list[dict[str, Any]] = []
    setting_surfaces: list[dict[str, Any]] = []
    model_inventory_coverage = "not-observed"
    setting_coverage = "not-observed"
    default_model: str | None = None
    metadata_scope = "not-requested"
    catalog_parsed = False

    if provider == "codex":
        catalog_arguments = ["debug", "models"]
        if offline_only:
            catalog_arguments.append("--bundled")
            metadata_scope = "bundled"
        else:
            metadata_scope = "provider-current"
        catalog_command, catalog_output = _run_command(
            executable,
            catalog_arguments,
            command_id="model-catalog",
            evidence_source="model-catalog-json",
            timeout_seconds=timeout_seconds,
        )
        commands.append(catalog_command)
        if catalog_command["status"] == "observed":
            inventory, setting_surfaces, catalog_parsed = _parse_codex_catalog(catalog_output)
            if inventory:
                model_inventory_coverage = "exact" if catalog_parsed else "partial"
            if setting_surfaces:
                setting_coverage = "exact" if catalog_parsed else "partial"
    elif provider == "claude":
        if help_command["status"] == "observed":
            setting_surfaces = _parse_claude_help(help_output)
            setting_coverage = "partial"
    else:
        if help_command["status"] == "observed":
            setting_surfaces = _parse_grok_help(help_output)
            setting_coverage = "partial"
        if not offline_only:
            metadata_scope = "provider-current"
            catalog_command, catalog_output = _run_command(
                executable,
                ["models"],
                command_id="model-catalog",
                evidence_source="model-list-text",
                timeout_seconds=timeout_seconds,
            )
            commands.append(catalog_command)
            if catalog_command["status"] == "observed":
                inventory, default_model, catalog_parsed = _parse_grok_models(catalog_output)
                if inventory:
                    model_inventory_coverage = "exact" if catalog_parsed else "partial"

    cli_version = _version_from_output(version_output)
    runtime: dict[str, Any] = {
        "provider": provider,
        "cli_name": provider,
        "cli_version": cli_version,
        "cli_source": cli_source,
        "execution_surface": "capability-probe",
        "environment_kind": environment_kind,
        "permission_mode": "unknown",
        "observed_at": observed_at,
    }
    if provider == "grok":
        build_hint, release_channel = _grok_build_identity(version_output)
        if build_hint:
            runtime["build_hint"] = build_hint
        if release_channel:
            runtime["release_channel"] = release_channel
    if image_digest is not None:
        runtime["image_digest"] = image_digest

    model_identity: dict[str, Any] = {
        "requested_source": "unknown",
        "identity_confidence": "default-unspecified",
    }
    if provider == "grok" and default_model:
        model_identity = {
            "requested_alias": default_model,
            "requested_source": "runtime-default",
            "identity_confidence": "alias-only",
        }

    limitations = {"no-generation-request", "setting-application-unobserved"}
    if default_model is None:
        limitations.add("model-default-unresolved")
    if not inventory:
        limitations.add("model-inventory-unobserved")
    if not catalog_parsed and provider in {"codex", "grok"} and not (
        provider == "grok" and offline_only
    ):
        limitations.add("model-catalog-unparsed")
    if any(item["status"] != "observed" for item in commands):
        limitations.add("partial-command-coverage")
    if any(item["advertisement"] == "flag-only" for item in setting_surfaces):
        limitations.add("setting-values-unadvertised")

    runtime_coverage = "exact" if cli_version != "unknown" else "not-observed"
    record = {
        "schema_version": 2,
        "capability_id": capability_id or _capability_id(provider, observed_at),
        "observed_at": observed_at,
        "probe": {
            "mode": "passive-cli",
            "generation_request_performed": False,
            "provider_metadata_request_attempted": metadata_scope == "provider-current",
            "metadata_scope": metadata_scope,
            "raw_output_persisted": False,
            "commands": commands,
        },
        "model_identity": model_identity,
        "model_inventory": inventory,
        "runtime_identity": runtime,
        "setting_surfaces": setting_surfaces,
        "setting_probes": [],
        "surfaces": {
            "progress_artifact": "unknown",
            "synthesis_envelope": "unknown",
            "permission_mode": "unknown",
        },
        "coverage": {
            "model_inventory": model_inventory_coverage,
            "setting_advertisement": setting_coverage,
            "setting_application": "not-observed",
            "runtime_identity": runtime_coverage,
            "limitations": sorted(limitations),
        },
    }
    validate_record("capability", record)
    return record
