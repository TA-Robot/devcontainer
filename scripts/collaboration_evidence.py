#!/usr/bin/env python3
"""Bounded, content-free summaries of Mira collaboration episodes."""

from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any, Iterable


REPORT_SCHEMA_VERSION = 1
MAX_ALLOWED_EPISODES = 4096
MAX_ALLOWED_GROUPS = 512
DEFAULT_MAX_OUTPUT_BYTES = 256 * 1024
MAX_ALLOWED_OUTPUT_BYTES = 1024 * 1024

SOURCES = {"agentctl", "codex", "claude", "grok"}
PROVIDERS = {"codex", "claude", "grok"}
TOPOLOGIES = {"solo-observed", "delegated", "managed-job"}
RELATIONS = {"solo", "delegate", "consult", "compete", "verify", "project-specific"}
LIFECYCLES = {"one-shot", "bounded-exchange", "event-triggered", "scheduled", "project-specific"}
MECHANISMS = {
    "latency-overlap",
    "context-partitioning",
    "coverage",
    "error-decorrelation",
    "empirical-selection",
    "evidence-producing-refinement",
    "temporal-sampling",
    "project-specific",
}
CONSTRAINTS = {
    "serialization",
    "human-review",
    "wall-clock",
    "quota",
    "agentctl-capacity",
    "integration",
    "context-coupling",
    "evaluator",
    "late-failure",
    "other",
    "unknown",
}
TERMINAL_OUTCOMES = {"success", "failure", "unknown"}
COMPLETIONS = {"observed-terminal", "superseded", "expired"}


class EvidenceReportError(ValueError):
    """Raised when report input or bounds are invalid."""


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _bounded_integer(value: Any) -> int | None:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        return None
    return value


def _enum(value: Any, allowed: set[str]) -> str:
    return value if isinstance(value, str) and value in allowed else "unknown"


def _mechanisms(value: Any) -> tuple[str, ...]:
    if not isinstance(value, list):
        return ()
    accepted = sorted(
        {
            item
            for item in value[:8]
            if isinstance(item, str) and item in MECHANISMS
        }
    )
    return tuple(accepted)


def _counter(value: Any, allowed: set[str]) -> dict[str, int]:
    if not isinstance(value, dict):
        return {}
    result: dict[str, int] = {}
    for key in sorted(allowed):
        count = _bounded_integer(value.get(key))
        if count is not None:
            result[key] = count
    return result


def _quantiles(values: Iterable[int]) -> dict[str, int] | None:
    ordered = sorted(values)
    if not ordered:
        return None
    middle = len(ordered) // 2
    median = (
        ordered[middle]
        if len(ordered) % 2
        else round((ordered[middle - 1] + ordered[middle]) / 2)
    )
    return {
        "observations": len(ordered),
        "min": ordered[0],
        "median": median,
        "max": ordered[-1],
    }


def _safe_episode(raw: Any) -> dict[str, Any] | None:
    if not isinstance(raw, dict) or raw.get("schemaVersion") != 1:
        return None
    duration = _bounded_integer(raw.get("durationMs"))
    if duration is None:
        return None
    delegation = raw.get("delegation") if isinstance(raw.get("delegation"), dict) else {}
    review = raw.get("reviewProxy") if isinstance(raw.get("reviewProxy"), dict) else {}
    rework = raw.get("reworkProxy") if isinstance(raw.get("reworkProxy"), dict) else {}
    coverage = raw.get("coverage") if isinstance(raw.get("coverage"), dict) else {}
    semantics = raw.get("semantics") if isinstance(raw.get("semantics"), dict) else {}
    correlation = semantics.get("correlation") if isinstance(semantics.get("correlation"), dict) else {}
    plan = correlation.get("plan")
    candidate = correlation.get("candidate")
    plan = plan if isinstance(plan, str) and len(plan) == 16 and all(c in "0123456789abcdef" for c in plan) else None
    candidate = candidate if isinstance(candidate, str) and len(candidate) == 16 and all(c in "0123456789abcdef" for c in candidate) else None
    return {
        "workspace": raw.get("workspace") if isinstance(raw.get("workspace"), str) else "unknown",
        "source": _enum(raw.get("source"), SOURCES),
        "provider": _enum(raw.get("provider"), PROVIDERS),
        "topology": _enum(raw.get("topology"), TOPOLOGIES),
        "terminalOutcome": _enum(raw.get("terminalOutcome"), TERMINAL_OUTCOMES),
        "completion": _enum(raw.get("completion"), COMPLETIONS),
        "durationMs": duration,
        "workerStarts": _bounded_integer(delegation.get("starts")),
        "peakWorkers": _bounded_integer(delegation.get("peakConcurrent")),
        "workerActiveMs": _bounded_integer(delegation.get("workerActiveMs")),
        "reviewAvailable": review.get("available") is True,
        "reviewElapsedMs": _bounded_integer(review.get("elapsedMs")),
        "testRecoveries": _bounded_integer(rework.get("testRecoveries")),
        "editAfterFailure": _bounded_integer(rework.get("editEventsAfterTestFailure")),
        "testOutcomes": _counter(raw.get("testOutcomes"), TERMINAL_OUTCOMES),
        "startObserved": coverage.get("startObserved") is True,
        "terminalObserved": coverage.get("terminalObserved") is True,
        "workerStartsObserved": coverage.get("workerStartsObserved") is True,
        "relation": _enum(semantics.get("relation"), RELATIONS),
        "lifecycle": _enum(semantics.get("lifecycle"), LIFECYCLES),
        "bindingConstraint": _enum(semantics.get("bindingConstraint"), CONSTRAINTS),
        "expectedMechanisms": _mechanisms(semantics.get("expectedMechanisms")),
        "annotationSource": "primary-plan" if semantics.get("annotationSource") == "primary-plan" else "none",
        "plan": plan,
        "candidate": candidate,
        "correlated": correlation.get("available") is True and plan is not None and candidate is not None,
    }


def _group_summary(key: tuple[Any, ...], episodes: list[dict[str, Any]]) -> dict[str, Any]:
    outcomes = Counter(item["terminalOutcome"] for item in episodes)
    completions = Counter(item["completion"] for item in episodes)
    tests = Counter()
    for item in episodes:
        tests.update(item["testOutcomes"])
    review_durations = [
        item["reviewElapsedMs"]
        for item in episodes
        if item["reviewAvailable"] and item["reviewElapsedMs"] is not None
    ]
    source, provider, topology, relation, lifecycle, constraint, mechanisms = key
    return {
        "dimensions": {
            "source": source,
            "provider": provider,
            "topology": topology,
            "relation": relation,
            "lifecycle": lifecycle,
            "bindingConstraint": constraint,
            "expectedMechanisms": list(mechanisms),
        },
        "episodes": len(episodes),
        "terminalOutcomes": dict(sorted(outcomes.items())),
        "completions": dict(sorted(completions.items())),
        "durationMs": _quantiles(item["durationMs"] for item in episodes),
        "workerStarts": _quantiles(item["workerStarts"] for item in episodes if item["workerStarts"] is not None),
        "peakWorkers": _quantiles(item["peakWorkers"] for item in episodes if item["peakWorkers"] is not None),
        "workerActiveMs": _quantiles(item["workerActiveMs"] for item in episodes if item["workerActiveMs"] is not None),
        "reviewProxy": {
            "availableEpisodes": len(review_durations),
            "elapsedMs": _quantiles(review_durations),
        },
        "reworkProxy": {
            "testRecoveries": sum(item["testRecoveries"] or 0 for item in episodes),
            "editEventsAfterTestFailure": sum(item["editAfterFailure"] or 0 for item in episodes),
        },
        "testOutcomes": dict(sorted(tests.items())),
        "coverage": {
            "startObserved": sum(item["startObserved"] for item in episodes),
            "terminalObserved": sum(item["terminalObserved"] for item in episodes),
            "workerStartsObserved": sum(item["workerStartsObserved"] for item in episodes),
            "decisionCorrelated": sum(item["correlated"] for item in episodes),
        },
    }


def build_report(
    ledger: Any,
    *,
    max_episodes: int = 512,
    max_groups: int = 100,
    min_group_size: int = 1,
    workspace: str | None = None,
) -> dict[str, Any]:
    if not 1 <= max_episodes <= MAX_ALLOWED_EPISODES:
        raise EvidenceReportError(f"max_episodes must be within 1..{MAX_ALLOWED_EPISODES}")
    if not 1 <= max_groups <= MAX_ALLOWED_GROUPS:
        raise EvidenceReportError(f"max_groups must be within 1..{MAX_ALLOWED_GROUPS}")
    if not 1 <= min_group_size <= max_episodes:
        raise EvidenceReportError("min_group_size must be within 1..max_episodes")
    raw_episodes = ledger.get("episodes", []) if isinstance(ledger, dict) else []
    if not isinstance(raw_episodes, list):
        raw_episodes = []
    considered = raw_episodes[-max_episodes:]
    parsed = [_safe_episode(item) for item in considered]
    valid = [item for item in parsed if item is not None]
    if workspace is not None:
        valid = [item for item in valid if item["workspace"] == workspace]

    grouped: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
    for episode in valid:
        key = (
            episode["source"],
            episode["provider"],
            episode["topology"],
            episode["relation"],
            episode["lifecycle"],
            episode["bindingConstraint"],
            episode["expectedMechanisms"],
        )
        grouped[key].append(episode)
    eligible = [(key, items) for key, items in grouped.items() if len(items) >= min_group_size]
    eligible.sort(key=lambda item: (-len(item[1]), tuple(str(part) for part in item[0])))
    selected = eligible[:max_groups]

    correlated = [item for item in valid if item["correlated"]]
    status = "unmeasured" if not valid else "observed"
    limitations = [
        "Descriptive observations only; no causal effect, ranking, or routing recommendation is inferred.",
        "terminal success is not artifact correctness; reviewProxy is post-worker tail time, not human review time.",
        "Groups with different task fingerprints, execution surfaces, or coverage are not controlled comparisons.",
    ]
    if valid and not correlated:
        limitations.append("No episode has a machine-correlated collaboration decision; semantic dimensions remain unknown.")
    return {
        "schemaVersion": REPORT_SCHEMA_VERSION,
        "reportKind": "bounded-collaboration-evidence",
        "generatedAt": utc_now(),
        "status": status,
        "input": {
            "ledgerSchemaVersion": ledger.get("schemaVersion") if isinstance(ledger, dict) else None,
            "availableEpisodes": len(raw_episodes),
            "consideredEpisodes": len(considered),
            "validEpisodes": len(valid),
            "invalidEpisodes": sum(item is None for item in parsed),
            "workspaceFilterApplied": workspace is not None,
            "maxEpisodes": max_episodes,
        },
        "decisionCoverage": {
            "correlatedEpisodes": len(correlated),
            "opaquePlans": len({item["plan"] for item in correlated}),
            "opaqueCandidates": len({item["candidate"] for item in correlated}),
        },
        "groups": [_group_summary(key, items) for key, items in selected],
        "grouping": {
            "eligibleGroups": len(eligible),
            "returnedGroups": len(selected),
            "truncated": len(eligible) > len(selected),
            "minGroupSize": min_group_size,
        },
        "limitations": limitations,
    }


def load_ledger(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {"schemaVersion": None, "episodes": []}
    except (OSError, json.JSONDecodeError) as exc:
        raise EvidenceReportError(f"cannot read episode ledger: {exc}") from exc
    if not isinstance(value, dict):
        raise EvidenceReportError("episode ledger root must be an object")
    return value


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Collaboration evidence report",
        "",
        f"Status: `{report['status']}`",
        "",
        f"Observed {report['input']['validEpisodes']} valid episode(s); "
        f"{report['decisionCoverage']['correlatedEpisodes']} decision-correlated.",
        "",
    ]
    if report["groups"]:
        lines.extend([
            "| source | provider | topology | relation | lifecycle | episodes | duration ms (min / median / max) | outcome |",
            "|---|---|---|---|---|---:|---|---|",
        ])
        for group in report["groups"]:
            dimensions = group["dimensions"]
            duration = group["durationMs"]
            duration_text = f"{duration['min']} / {duration['median']} / {duration['max']}"
            outcome_text = ", ".join(f"{key}:{value}" for key, value in group["terminalOutcomes"].items())
            lines.append(
                f"| {dimensions['source']} | {dimensions['provider']} | {dimensions['topology']} | "
                f"{dimensions['relation']} | {dimensions['lifecycle']} | {group['episodes']} | "
                f"{duration_text} | {outcome_text} |"
            )
        lines.append("")
    else:
        lines.extend(["No valid episode groups were observed.", ""])
    lines.extend(["## Interpretation limits", ""])
    lines.extend(f"- {item}" for item in report["limitations"])
    lines.append("")
    return "\n".join(lines)


def bounded_output(text: str, max_output_bytes: int) -> str:
    if not 1024 <= max_output_bytes <= MAX_ALLOWED_OUTPUT_BYTES:
        raise EvidenceReportError(
            f"max_output_bytes must be within 1024..{MAX_ALLOWED_OUTPUT_BYTES}"
        )
    if len(text.encode("utf-8")) > max_output_bytes:
        raise EvidenceReportError(
            "report exceeds output cap; lower --max-groups or raise --max-output-bytes within the hard limit"
        )
    return text
