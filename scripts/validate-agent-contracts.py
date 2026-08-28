#!/usr/bin/env python3
"""Validate native-agent templates and their provider-neutral envelopes."""

from __future__ import annotations

import argparse
import re
import sys
import tomllib
from pathlib import Path
from typing import Any

from agent_contracts import ContractValidationError, load_json, validate_file


EXPECTED_ROLE_MODES = {
    "researcher": ("read", "read-only", "plan"),
    "implementer": ("write", "workspace-write", "default"),
    "reviewer": ("read", "read-only", "plan"),
}


ADAPTIVE_GUIDANCE_REQUIREMENTS = {
    "AGENTS.md": (
        "binding constraint",
        "global default",
        "hard guard / cost cap / planning prior / hypothesis",
        "human review",
        "ユーザーへform",
    ),
    "docs/agents/collaboration-playbook.md": (
        "expected mechanism",
        "binding constraint",
        "derive participants",
        "human review",
        "parameter role",
        "invalidation evidence",
        "continue only while value changes",
        "lifecycle",
        "human input",
    ),
    "docs/agents/tickets/collaboration-plan.template.md": (
        "solo alternative",
        "expected mechanism",
        "binding constraint",
        "participant basis",
        "independence policy",
        "human review / synthesis budget",
        "invalidation evidence",
        "continuation evidence",
        "project-local learning",
        "do not ask the user",
    ),
}


UNSUPPORTED_GLOBAL_DEFAULTS = (
    re.compile(
        r"通常\s*\d+\s*(?:agents?|エージェント|participants?|rounds?|往復|回|variants?|案|candidates?)",
        re.IGNORECASE,
    ),
    re.compile(
        r"最大\s*\d+\s*(?:agents?|エージェント|participants?|rounds?|往復|回|variants?|案|candidates?)",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:normally|by\s+default|defaults?\s+to)\s*:?\s*\d+\s*(?:agents?|participants?|rounds?|exchanges?|variants?|candidates?)\b",
        re.IGNORECASE,
    ),
    re.compile(r"\b(?:blind\s+first\s+round|first[- ]round[- ]blind)\b", re.IGNORECASE),
)


def parse_frontmatter(path: Path) -> dict[str, str]:
    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0] != "---":
        raise ContractValidationError(f"missing YAML frontmatter: {path}")
    result: dict[str, str] = {}
    for line in lines[1:]:
        if line == "---":
            return result
        if not line or line.lstrip().startswith("#"):
            continue
        if ":" not in line or line.startswith((" ", "\t")):
            raise ContractValidationError(f"unsupported frontmatter line in {path}: {line!r}")
        key, value = line.split(":", 1)
        result[key.strip()] = value.strip()
    raise ContractValidationError(f"unterminated YAML frontmatter: {path}")


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ContractValidationError(message)


def validate_adaptive_guidance(path: Path, text: str, required_phrases: tuple[str, ...]) -> None:
    lowered = text.lower()
    for phrase in required_phrases:
        require(phrase.lower() in lowered, f"adaptive collaboration guidance missing {phrase!r}: {path}")
    for pattern in UNSUPPORTED_GLOBAL_DEFAULTS:
        match = pattern.search(text)
        if match:
            raise ContractValidationError(f"unsupported global collaboration default {match.group(0)!r}: {path}")


def validate_config(root: Path) -> dict[str, Any]:
    config_path = root / ".agent/config.json"
    config = load_json(config_path)
    require(isinstance(config, dict), f"config root must be an object: {config_path}")
    require(config.get("schema_version") == 1, "config schema_version must be 1")
    require(config.get("default_permission_profile") == "safe", "safe must be the default profile")
    require(config.get("integration", {}).get("single_writer") is True, "integration must be single-writer")
    require(config.get("integration", {}).get("workers_may_push") is False, "workers may not push")
    require(config.get("integration", {}).get("workers_may_merge") is False, "workers may not merge")
    require(set(config.get("roles", {})) == set(EXPECTED_ROLE_MODES), "role set must match native templates")
    for role, (lane, _, _) in EXPECTED_ROLE_MODES.items():
        role_config = config["roles"][role]
        require(role_config.get("default_lane") == lane, f"{role}: unexpected default lane")
        definition = root / role_config.get("definition", "")
        require(definition.is_file(), f"{role}: missing neutral role definition {definition}")
    return config


def validate_operating_docs(root: Path) -> None:
    required = (
        "docs/agents/runbook.md",
        "docs/agents/collaboration-playbook.md",
        "docs/agents/tickets/task-ticket.template.md",
        "docs/agents/tickets/collaboration-plan.template.md",
    )
    for relative in required:
        path = root / relative
        require(path.is_file(), f"missing operating document: {path}")
    agents_path = root / "AGENTS.md"
    agents = agents_path.read_text(encoding="utf-8")
    require(
        "docs/agents/collaboration-playbook.md" in agents,
        "AGENTS.md must reference the collaboration playbook",
    )
    for relative, phrases in ADAPTIVE_GUIDANCE_REQUIREMENTS.items():
        path = root / relative
        validate_adaptive_guidance(path, path.read_text(encoding="utf-8"), phrases)


def validate_schemas_and_examples(root: Path, config: dict[str, Any]) -> None:
    contracts = config.get("contracts", {})
    required_contracts = {
        "task": ".agent/examples/task.example.json",
        "result": ".agent/examples/result.example.json",
        "collaboration_decision": ".agent/examples/collaboration-decision.example.json",
        "collaboration_outcome": ".agent/examples/collaboration-outcome.example.json",
    }
    require(
        set(required_contracts).issubset(contracts),
        "config must publish task, result, collaboration_decision, and collaboration_outcome contracts",
    )
    schema_paths: dict[str, Path] = {}
    for kind, example in required_contracts.items():
        path = root / contracts.get(kind, "")
        schema_paths[kind] = path
        schema = load_json(path)
        require(isinstance(schema, dict), f"{kind} schema root must be an object")
        require(schema.get("$schema") == "https://json-schema.org/draft/2020-12/schema", f"{kind}: wrong draft")
        require(schema.get("properties", {}).get("schema_version", {}).get("const") == 1, f"{kind}: version must be 1")
        validate_file(root / example, path)
    validate_file(root / ".agent/examples/provider-result.example.json", schema_paths["result"])


def validate_codex_templates(root: Path) -> None:
    with (root / ".codex/config.toml").open("rb") as handle:
        config = tomllib.load(handle)
    require(config.get("agents", {}).get("enabled") is True, "Codex native agents must be enabled")
    concurrency = config.get("agents", {}).get("max_concurrent_threads_per_session")
    require(isinstance(concurrency, int) and 1 <= concurrency <= 16, "Codex concurrency must be between 1 and 16")
    for role, (_, sandbox_mode, _) in EXPECTED_ROLE_MODES.items():
        path = root / f".codex/agents/{role}.toml"
        with path.open("rb") as handle:
            agent = tomllib.load(handle)
        require(agent.get("name") == role, f"Codex filename/name mismatch: {path}")
        require(bool(agent.get("description")), f"Codex description missing: {path}")
        require(bool(agent.get("developer_instructions")), f"Codex instructions missing: {path}")
        require(agent.get("sandbox_mode") == sandbox_mode, f"Codex {role}: wrong sandbox_mode")


def validate_claude_templates(root: Path) -> None:
    bridge = (root / "CLAUDE.md").read_text(encoding="utf-8").splitlines()
    require(bool(bridge) and bridge[0].strip() == "@AGENTS.md", "CLAUDE.md must import AGENTS.md first")
    for role, (_, _, permission_mode) in EXPECTED_ROLE_MODES.items():
        path = root / f".claude/agents/{role}.md"
        agent = parse_frontmatter(path)
        require(agent.get("name") == role, f"Claude filename/name mismatch: {path}")
        require(bool(agent.get("description")), f"Claude description missing: {path}")
        require(agent.get("permissionMode") == permission_mode, f"Claude {role}: wrong permissionMode")
        tools = {item.strip() for item in agent.get("tools", "").split(",")}
        require("Agent" not in tools, f"Claude {role}: nested Agent tool is not allowed")
        if role != "implementer":
            require(not ({"Edit", "Write", "NotebookEdit"} & tools), f"Claude {role}: write tool exposed")


def validate_grok_templates(root: Path) -> None:
    for role, (_, _, permission_mode) in EXPECTED_ROLE_MODES.items():
        path = root / f".grok/agents/{role}.md"
        agent = parse_frontmatter(path)
        require(agent.get("name") == role, f"Grok filename/name mismatch: {path}")
        require(bool(agent.get("description")), f"Grok description missing: {path}")
        require(agent.get("permissionMode") == permission_mode, f"Grok {role}: wrong permissionMode")
        tools = {item.strip() for item in agent.get("tools", "").split(",")}
        require("Agent" not in tools, f"Grok {role}: nested Agent tool is not allowed")
        if role != "implementer":
            require(not ({"Edit", "Write", "NotebookEdit"} & tools), f"Grok {role}: write tool exposed")


def validate_template(root: Path) -> None:
    config = validate_config(root)
    validate_operating_docs(root)
    validate_schemas_and_examples(root, config)
    validate_codex_templates(root)
    validate_claude_templates(root)
    validate_grok_templates(root)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--template-root", type=Path, default=Path("project"))
    parser.add_argument("--schema", type=Path)
    parser.add_argument("--instance", type=Path)
    args = parser.parse_args()
    try:
        if args.schema or args.instance:
            require(args.schema is not None and args.instance is not None, "--schema and --instance must be used together")
            validate_file(args.instance, args.schema)
        else:
            validate_template(args.template_root)
    except (ContractValidationError, OSError, tomllib.TOMLDecodeError) as exc:
        print(f"agent contract validation failed: {exc}", file=sys.stderr)
        return 1
    print("agent contract validation: ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
