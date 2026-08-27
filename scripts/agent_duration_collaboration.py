#!/usr/bin/env python3
"""Finite, provider-agnostic collaboration control-plane for duration studies.

This module deliberately stops at an injected async adapter boundary.  It does
not start a provider, create an ``agentctl`` job, retry a provider call, or
schedule recurring work.  A future adapter may map one dispatch to the existing
``agentctl`` create -> run -> validate lifecycle, but that adapter must retain
prompt/result content outside the analytics object returned here.

The manifest is an execution contract, not a routing recommendation.  Exact
participant and exchange counts are supplied by each manifest.  Constants named
``*_HARD_GUARD`` below only bound parser/runtime resource use; they are not
planning defaults.  The owner of this module should revise them only when the
control-plane resource envelope is intentionally expanded and re-tested.
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path
import re
import sys
from typing import Any, Mapping, Protocol, Sequence

from agent_duration_study import (
    EventClock,
    SystemClock,
    atomic_write_json,
    elapsed_ms,
    interval_union_ms,
)


SCHEMA_VERSION = 1
ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")

# This is the implemented v1 capability surface, not a claim that collaboration
# relations form a globally closed ontology.  A new relation requires an
# explicit validator/event contract revision rather than silent inference.
SUPPORTED_RELATIONS_V1 = {
    "bounded-delegation",
    "parallel-shards",
    "independent-candidates",
    "maker-verifier",
    "evidence-dialogue",
    "staged-pipeline",
}
STEP_KINDS = {"worker", "synthesis", "dialogue"}
FAILURE_MODES = {"fail-fast", "continue-independent"}
STEP_STATUSES = {"succeeded", "failed", "timed-out", "cancelled", "skipped"}
ARTIFACT_STATUSES = {"valid", "invalid", "missing", "not-applicable"}
ADAPTER_STATUSES = {"succeeded", "failed", "cancelled"}
ADAPTER_TERMINAL_REASONS = {
    "completed",
    "adapter-failure",
    "artifact-invalid",
    "blocked",
    "provider-refusal",
    "rate-limit",
    "cancelled",
}
DIALOGUE_STOP_REASONS = {
    "evidence-added",
    "claim-resolved",
    "no-new-evidence",
    "acceptance-reached",
    "safety-cap",
    "blocked",
    "fixture-complete",
    "unknown",
}

# Resource-abuse hard guards, not participant-count, exchange-count, or timeout
# recommendations.  Every effective value remains required in the manifest.
MAX_PARTICIPANTS_HARD_GUARD = 256
MAX_STEPS_HARD_GUARD = 4096
MAX_EXCHANGES_HARD_GUARD = 4096
MAX_DEADLINE_MS_HARD_GUARD = 7 * 24 * 60 * 60 * 1000
MAX_STEP_TIMEOUT_MS_HARD_GUARD = 24 * 60 * 60 * 1000

RELATION_ROLES = {
    "bounded-delegation": {"delegate", "synthesis"},
    "parallel-shards": {"shard", "synthesis"},
    "independent-candidates": {"candidate", "synthesis"},
    "maker-verifier": {"maker", "verifier", "synthesis"},
    "evidence-dialogue": {"dialogue", "synthesis"},
    "staged-pipeline": {"stage", "synthesis"},
}


class CollaborationManifestError(ValueError):
    """Raised before execution when a collaboration manifest is unsafe."""


class CollaborationExecutionError(RuntimeError):
    """Raised for control-plane failures rather than adapter task failures."""


@dataclass(frozen=True)
class Participant:
    participant_id: str
    role: str
    adapter_id: str


@dataclass(frozen=True)
class Step:
    step_id: str
    kind: str
    relation_role: str
    participant_id: str
    depends_on: tuple[str, ...]
    task_ref: str
    exchange_id: str | None = None
    parent_exchange_id: str | None = None


@dataclass(frozen=True)
class Limits:
    max_participants: int
    max_exchanges: int
    deadline_ms: int
    per_step_timeout_ms: int
    max_concurrency: int


@dataclass(frozen=True)
class FailurePolicy:
    mode: str
    on_dependency_failure: str
    retry_policy: str


@dataclass(frozen=True)
class CollaborationManifest:
    schema_version: int
    batch_id: str
    configuration_id: str
    relation: str
    participant_plan_id: str
    independence_policy: str
    nested_delegation: str
    participants: tuple[Participant, ...]
    steps: tuple[Step, ...]
    limits: Limits
    failure_policy: FailurePolicy
    manifest_digest: str

    @property
    def participants_by_id(self) -> dict[str, Participant]:
        return {item.participant_id: item for item in self.participants}

    @property
    def steps_by_id(self) -> dict[str, Step]:
        return {item.step_id: item for item in self.steps}


@dataclass(frozen=True)
class DependencyArtifact:
    """Private dependency value passed between adapters and never serialized."""

    step_id: str
    value: Any = field(repr=False, compare=False)


@dataclass(frozen=True)
class DispatchRequest:
    """One finite adapter invocation.

    ``task_ref`` is an opaque lookup key.  The adapter owns resolution of prompt
    or task content.  ``dependency_artifacts`` are process-private values and the
    runner drops them before producing analytics.
    """

    batch_id: str
    configuration_id: str
    relation: str
    step_id: str
    step_kind: str
    relation_role: str
    participant_id: str
    participant_role: str
    task_ref: str
    dependency_step_ids: tuple[str, ...]
    dependency_artifacts: tuple[DependencyArtifact, ...]
    timeout_ms: int


@dataclass(frozen=True)
class DialogueMetrics:
    claim_count: int
    evidence_count: int
    test_count: int
    state_change_count: int
    unresolved_crux_count: int
    stop_reason: str

    def __post_init__(self) -> None:
        for name in (
            "claim_count",
            "evidence_count",
            "test_count",
            "state_change_count",
            "unresolved_crux_count",
        ):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise ValueError(f"{name} must be a non-negative integer")
        if (
            not isinstance(self.stop_reason, str)
            or self.stop_reason not in DIALOGUE_STOP_REASONS
        ):
            raise ValueError(
                "dialogue_metrics.stop_reason must be a content-free allowlisted value"
            )


@dataclass(frozen=True)
class SynthesisMetrics:
    adopted_count: int
    rejected_count: int
    unresolved_count: int

    def __post_init__(self) -> None:
        for name in ("adopted_count", "rejected_count", "unresolved_count"):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise ValueError(f"{name} must be a non-negative integer")


@dataclass(frozen=True)
class AdapterResult:
    """Adapter terminal envelope; ``private_artifact`` is never analytic output."""

    status: str
    terminal_reason: str
    artifact_status: str
    private_artifact: Any = field(default=None, repr=False, compare=False)
    dialogue_metrics: DialogueMetrics | None = None
    synthesis_metrics: SynthesisMetrics | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.status, str) or self.status not in ADAPTER_STATUSES:
            raise ValueError(f"unsupported adapter status: {self.status!r}")
        if (
            not isinstance(self.terminal_reason, str)
            or self.terminal_reason not in ADAPTER_TERMINAL_REASONS
        ):
            raise ValueError(f"unsupported adapter terminal reason: {self.terminal_reason!r}")
        if (
            not isinstance(self.artifact_status, str)
            or self.artifact_status not in ARTIFACT_STATUSES
        ):
            raise ValueError(f"unsupported artifact status: {self.artifact_status!r}")
        if self.status == "succeeded":
            if self.terminal_reason != "completed":
                raise ValueError("successful adapter results must use completed")
            if self.artifact_status != "valid" or self.private_artifact is None:
                raise ValueError("successful adapter results require a private valid artifact")
        else:
            if self.terminal_reason == "completed":
                raise ValueError("only successful adapter results may use completed")
            if self.artifact_status == "valid" or self.private_artifact is not None:
                raise ValueError(
                    "non-success adapter results must not expose a valid private artifact"
                )
            if self.status == "cancelled" and self.terminal_reason != "cancelled":
                raise ValueError("cancelled adapter results must use cancelled")


class ExecutionAdapter(Protocol):
    """Injected provider/job boundary.

    Implementations must propagate cancellation and terminate owned provider/job
    work before returning from cancellation.  The in-process control-plane can
    signal cancellation but cannot safely kill a cancellation-hostile adapter.
    """

    async def execute(self, request: DispatchRequest) -> AdapterResult:
        """Execute exactly one request without an internal automatic retry."""


class FakeExecutionAdapter:
    """Deterministic non-provider adapter used for Wave 0 calibration and CLI smoke."""

    async def execute(self, request: DispatchRequest) -> AdapterResult:
        dialogue = None
        synthesis = None
        if request.step_kind == "dialogue":
            dialogue = DialogueMetrics(
                claim_count=1,
                evidence_count=1,
                test_count=0,
                state_change_count=1,
                unresolved_crux_count=0,
                stop_reason="fixture-complete",
            )
        elif request.step_kind == "synthesis":
            synthesis = SynthesisMetrics(
                adopted_count=len(request.dependency_step_ids),
                rejected_count=0,
                unresolved_count=0,
            )
        return AdapterResult(
            status="succeeded",
            terminal_reason="completed",
            artifact_status="valid",
            private_artifact=("fixture-artifact", request.step_id),
            dialogue_metrics=dialogue,
            synthesis_metrics=synthesis,
        )


def _expect_object(
    value: Any,
    path: str,
    *,
    required: set[str],
    optional: set[str] | None = None,
) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise CollaborationManifestError(f"{path} must be an object")
    allowed = required | (optional or set())
    missing = sorted(required - set(value))
    if missing:
        raise CollaborationManifestError(f"{path} is missing required keys: {', '.join(missing)}")
    unknown = sorted(set(value) - allowed)
    if unknown:
        raise CollaborationManifestError(f"{path} has unsupported keys: {', '.join(unknown)}")
    return value


def _require_id_value(value: Any, path: str) -> str:
    if not isinstance(value, str) or ID_PATTERN.fullmatch(value) is None:
        raise CollaborationManifestError(
            f"{path} must match {ID_PATTERN.pattern!r}"
        )
    return value


def _require_int(
    value: Any,
    path: str,
    *,
    minimum: int,
    maximum: int,
) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise CollaborationManifestError(f"{path} must be an integer")
    if not minimum <= value <= maximum:
        raise CollaborationManifestError(
            f"{path} must be between {minimum} and {maximum}, got {value}"
        )
    return value


def _canonical_digest(payload: Mapping[str, Any]) -> str:
    encoded = json.dumps(
        payload,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def _parse_participant(value: Any, index: int) -> Participant:
    path = f"participant_plan.participants[{index}]"
    item = _expect_object(
        value,
        path,
        required={"participant_id", "role", "adapter_id"},
    )
    return Participant(
        participant_id=_require_id_value(item["participant_id"], f"{path}.participant_id"),
        role=_require_id_value(item["role"], f"{path}.role"),
        adapter_id=_require_id_value(item["adapter_id"], f"{path}.adapter_id"),
    )


def _parse_step(value: Any, index: int) -> Step:
    path = f"steps[{index}]"
    item = _expect_object(
        value,
        path,
        required={
            "step_id",
            "kind",
            "relation_role",
            "participant_id",
            "depends_on",
            "task_ref",
        },
        optional={"exchange_id", "parent_exchange_id"},
    )
    kind = item["kind"]
    if not isinstance(kind, str) or kind not in STEP_KINDS:
        raise CollaborationManifestError(
            f"{path}.kind must be one of {sorted(STEP_KINDS)}"
        )
    raw_dependencies = item["depends_on"]
    if not isinstance(raw_dependencies, list):
        raise CollaborationManifestError(f"{path}.depends_on must be an array")
    dependencies = tuple(
        _require_id_value(value, f"{path}.depends_on[{dep_index}]")
        for dep_index, value in enumerate(raw_dependencies)
    )
    if len(set(dependencies)) != len(dependencies):
        raise CollaborationManifestError(f"{path}.depends_on contains duplicates")

    exchange_id = item.get("exchange_id")
    parent_exchange_id = item.get("parent_exchange_id")
    if kind == "dialogue":
        if exchange_id is None:
            raise CollaborationManifestError(f"{path}.exchange_id is required for dialogue")
        exchange_id = _require_id_value(exchange_id, f"{path}.exchange_id")
        if parent_exchange_id is not None:
            parent_exchange_id = _require_id_value(
                parent_exchange_id, f"{path}.parent_exchange_id"
            )
    elif exchange_id is not None or parent_exchange_id is not None:
        raise CollaborationManifestError(
            f"{path} exchange fields are only valid for dialogue steps"
        )

    return Step(
        step_id=_require_id_value(item["step_id"], f"{path}.step_id"),
        kind=kind,
        relation_role=_require_id_value(item["relation_role"], f"{path}.relation_role"),
        participant_id=_require_id_value(item["participant_id"], f"{path}.participant_id"),
        depends_on=dependencies,
        task_ref=_require_id_value(item["task_ref"], f"{path}.task_ref"),
        exchange_id=exchange_id,
        parent_exchange_id=parent_exchange_id,
    )


def _topological_order(steps: Sequence[Step]) -> tuple[str, ...]:
    by_id = {step.step_id: step for step in steps}
    dependent_ids: dict[str, list[str]] = {step.step_id: [] for step in steps}
    remaining_dependencies = {
        step.step_id: len(step.depends_on) for step in steps
    }
    for step in steps:
        for dependency_id in step.depends_on:
            dependent_ids[dependency_id].append(step.step_id)

    ready = [
        step.step_id for step in steps if remaining_dependencies[step.step_id] == 0
    ]
    order: list[str] = []
    ready_index = 0
    while ready_index < len(ready):
        step_id = ready[ready_index]
        ready_index += 1
        order.append(step_id)
        for dependent_id in dependent_ids[step_id]:
            remaining_dependencies[dependent_id] -= 1
            if remaining_dependencies[dependent_id] == 0:
                ready.append(dependent_id)

    if len(order) != len(by_id):
        cycle_member = next(
            step.step_id
            for step in steps
            if remaining_dependencies[step.step_id] > 0
        )
        raise CollaborationManifestError(
            f"step dependency cycle detected at {cycle_member}"
        )
    return tuple(order)


def _ancestor_index(
    steps: Sequence[Step],
) -> tuple[dict[str, int], dict[str, int]]:
    """Return compact transitive-ancestor bitsets without recursive traversal."""

    by_id = {step.step_id: step for step in steps}
    order = _topological_order(steps)
    bit_by_id = {step_id: 1 << index for index, step_id in enumerate(order)}
    ancestors_by_id: dict[str, int] = {}
    for step_id in order:
        mask = 0
        for dependency_id in by_id[step_id].depends_on:
            mask |= bit_by_id[dependency_id]
            mask |= ancestors_by_id[dependency_id]
        ancestors_by_id[step_id] = mask
    return bit_by_id, ancestors_by_id


def _is_ancestor(
    ancestor_id: str,
    descendant_id: str,
    bit_by_id: Mapping[str, int],
    ancestors_by_id: Mapping[str, int],
) -> bool:
    return bool(ancestors_by_id[descendant_id] & bit_by_id[ancestor_id])


def _require_covering_synthesis(
    work_steps: Sequence[Step],
    synthesis_steps: Sequence[Step],
    bit_by_id: Mapping[str, int],
    ancestors_by_id: Mapping[str, int],
    relation: str,
) -> Step:
    if not synthesis_steps:
        raise CollaborationManifestError(f"{relation} requires an explicit synthesis step")
    work_mask = 0
    for step in work_steps:
        work_mask |= bit_by_id[step.step_id]
    for synthesis in synthesis_steps:
        if ancestors_by_id[synthesis.step_id] & work_mask == work_mask:
            return synthesis
    raise CollaborationManifestError(
        f"{relation} requires a synthesis step downstream of every relation work step"
    )


def _validate_relation(manifest: CollaborationManifest) -> None:
    allowed_roles = RELATION_ROLES[manifest.relation]
    for step in manifest.steps:
        if step.relation_role not in allowed_roles:
            raise CollaborationManifestError(
                f"step {step.step_id} relation_role {step.relation_role!r} is invalid for "
                f"{manifest.relation}"
            )
        expected_kind = (
            "synthesis"
            if step.relation_role == "synthesis"
            else "dialogue"
            if step.relation_role == "dialogue"
            else "worker"
        )
        if step.kind != expected_kind:
            raise CollaborationManifestError(
                f"step {step.step_id} relation_role {step.relation_role!r} requires "
                f"kind {expected_kind!r}"
            )

    bit_by_id, ancestors_by_id = _ancestor_index(manifest.steps)
    participants = manifest.participants_by_id
    syntheses = [step for step in manifest.steps if step.relation_role == "synthesis"]

    if manifest.relation == "bounded-delegation":
        delegates = [step for step in manifest.steps if step.relation_role == "delegate"]
        if not delegates:
            raise CollaborationManifestError("bounded-delegation requires at least one delegate")
        synthesis = _require_covering_synthesis(
            delegates, syntheses, bit_by_id, ancestors_by_id, manifest.relation
        )
        if all(item.participant_id == synthesis.participant_id for item in delegates):
            raise CollaborationManifestError(
                "bounded-delegation requires a delegate participant distinct from synthesis"
            )

    elif manifest.relation in {"parallel-shards", "independent-candidates"}:
        role = "shard" if manifest.relation == "parallel-shards" else "candidate"
        work = [step for step in manifest.steps if step.relation_role == role]
        if len(work) < 2:
            raise CollaborationManifestError(
                f"{manifest.relation} requires at least two independently schedulable {role} steps"
            )
        for index, left in enumerate(work):
            for right in work[index + 1 :]:
                if (
                    _is_ancestor(
                        left.step_id, right.step_id, bit_by_id, ancestors_by_id
                    )
                    or _is_ancestor(
                        right.step_id, left.step_id, bit_by_id, ancestors_by_id
                    )
                ):
                    raise CollaborationManifestError(
                        f"{manifest.relation} {role} steps must not depend on one another"
                    )
        # Logical shard count and worker width are separate dimensions.  A width-1
        # parallel-shard observation may assign several independent shards to one
        # participant sequentially.  Independent candidates, in contrast, require
        # distinct context identities even when max_concurrency is one.
        if (
            manifest.relation == "independent-candidates"
            and len({step.participant_id for step in work}) != len(work)
        ):
            raise CollaborationManifestError(
                "independent-candidates requires a distinct participant per candidate step"
            )
        _require_covering_synthesis(
            work, syntheses, bit_by_id, ancestors_by_id, manifest.relation
        )

    elif manifest.relation == "maker-verifier":
        makers = [step for step in manifest.steps if step.relation_role == "maker"]
        verifiers = [step for step in manifest.steps if step.relation_role == "verifier"]
        if not makers or not verifiers:
            raise CollaborationManifestError("maker-verifier requires maker and verifier steps")
        maker_participants = {step.participant_id for step in makers}
        for verifier in verifiers:
            if not any(
                _is_ancestor(
                    maker.step_id, verifier.step_id, bit_by_id, ancestors_by_id
                )
                for maker in makers
            ):
                raise CollaborationManifestError(
                    f"verifier {verifier.step_id} must depend on maker evidence"
                )
            if verifier.participant_id in maker_participants:
                raise CollaborationManifestError(
                    f"verifier {verifier.step_id} must use a participant distinct from makers"
                )
        _require_covering_synthesis(
            [*makers, *verifiers], syntheses, bit_by_id, ancestors_by_id, manifest.relation
        )

    elif manifest.relation == "evidence-dialogue":
        dialogue = [step for step in manifest.steps if step.relation_role == "dialogue"]
        if len(dialogue) < 2:
            raise CollaborationManifestError(
                "evidence-dialogue requires at least two explicit exchanges"
            )
        if len({step.participant_id for step in dialogue}) < 2:
            raise CollaborationManifestError(
                "evidence-dialogue requires at least two dialogue participants"
            )
        if not any(
            _is_ancestor(
                left.step_id, right.step_id, bit_by_id, ancestors_by_id
            )
            or _is_ancestor(
                right.step_id, left.step_id, bit_by_id, ancestors_by_id
            )
            for index, left in enumerate(dialogue)
            for right in dialogue[index + 1 :]
        ):
            raise CollaborationManifestError(
                "evidence-dialogue requires an evidence dependency between exchanges"
            )
        _require_covering_synthesis(
            dialogue, syntheses, bit_by_id, ancestors_by_id, manifest.relation
        )

    elif manifest.relation == "staged-pipeline":
        stages = [step for step in manifest.steps if step.relation_role == "stage"]
        if len(stages) < 2:
            raise CollaborationManifestError("staged-pipeline requires at least two stages")
        handoff = any(
            left.participant_id != right.participant_id
            and (
                _is_ancestor(
                    left.step_id, right.step_id, bit_by_id, ancestors_by_id
                )
                or _is_ancestor(
                    right.step_id, left.step_id, bit_by_id, ancestors_by_id
                )
            )
            for index, left in enumerate(stages)
            for right in stages[index + 1 :]
        )
        if not handoff:
            raise CollaborationManifestError(
                "staged-pipeline requires a dependency handoff between distinct participants"
            )
        _require_covering_synthesis(
            stages, syntheses, bit_by_id, ancestors_by_id, manifest.relation
        )

    # A participant is a planned execution context, so accepting an unused one
    # would overstate participants_actual in the resulting timing stratum.
    used = {step.participant_id for step in manifest.steps}
    unused = sorted(set(participants) - used)
    if unused:
        raise CollaborationManifestError(
            "participant plan contains unused participants: " + ", ".join(unused)
        )


def parse_manifest(payload: Any) -> CollaborationManifest:
    """Validate and compile a manifest without dispatching any adapter."""

    root = _expect_object(
        payload,
        "manifest",
        required={
            "schema_version",
            "batch_id",
            "configuration_id",
            "relation",
            "participant_plan",
            "steps",
            "limits",
            "failure_policy",
        },
    )
    if (
        isinstance(root["schema_version"], bool)
        or not isinstance(root["schema_version"], int)
        or root["schema_version"] != SCHEMA_VERSION
    ):
        raise CollaborationManifestError(
            f"manifest.schema_version must be {SCHEMA_VERSION}"
        )
    relation = root["relation"]
    if not isinstance(relation, str) or relation not in SUPPORTED_RELATIONS_V1:
        raise CollaborationManifestError(
            "manifest.relation is not supported by the v1 control-plane; "
            f"supported values are {sorted(SUPPORTED_RELATIONS_V1)}"
        )

    plan = _expect_object(
        root["participant_plan"],
        "participant_plan",
        required={
            "plan_id",
            "independence_policy",
            "nested_delegation",
            "participants",
        },
    )
    if plan["nested_delegation"] != "disabled":
        raise CollaborationManifestError(
            "participant_plan.nested_delegation must be disabled in the initial controlled slice"
        )
    raw_participants = plan["participants"]
    if not isinstance(raw_participants, list) or not raw_participants:
        raise CollaborationManifestError(
            "participant_plan.participants must be a non-empty array"
        )
    if len(raw_participants) > MAX_PARTICIPANTS_HARD_GUARD:
        raise CollaborationManifestError(
            f"participant plan exceeds hard guard {MAX_PARTICIPANTS_HARD_GUARD}"
        )
    participants = tuple(
        _parse_participant(value, index) for index, value in enumerate(raw_participants)
    )
    participant_ids = [item.participant_id for item in participants]
    if len(set(participant_ids)) != len(participant_ids):
        raise CollaborationManifestError("participant_id values must be unique")

    raw_steps = root["steps"]
    if not isinstance(raw_steps, list) or not raw_steps:
        raise CollaborationManifestError("manifest.steps must be a non-empty array")
    if len(raw_steps) > MAX_STEPS_HARD_GUARD:
        raise CollaborationManifestError(f"step plan exceeds hard guard {MAX_STEPS_HARD_GUARD}")
    steps = tuple(_parse_step(value, index) for index, value in enumerate(raw_steps))
    step_ids = [step.step_id for step in steps]
    if len(set(step_ids)) != len(step_ids):
        raise CollaborationManifestError("step_id values must be unique")

    known_steps = set(step_ids)
    known_participants = set(participant_ids)
    for step in steps:
        if step.participant_id not in known_participants:
            raise CollaborationManifestError(
                f"step {step.step_id} references unknown participant {step.participant_id}"
            )
        unknown_dependencies = sorted(set(step.depends_on) - known_steps)
        if unknown_dependencies:
            raise CollaborationManifestError(
                f"step {step.step_id} has unknown dependencies: "
                + ", ".join(unknown_dependencies)
            )
    _topological_order(steps)

    dialogue_by_exchange: dict[str, Step] = {}
    for step in steps:
        if step.exchange_id is None:
            continue
        if step.exchange_id in dialogue_by_exchange:
            raise CollaborationManifestError(
                f"duplicate dialogue exchange_id: {step.exchange_id}"
            )
        dialogue_by_exchange[step.exchange_id] = step
    bit_by_id, ancestors_by_id = _ancestor_index(steps)
    for step in steps:
        if step.parent_exchange_id is None:
            continue
        parent = dialogue_by_exchange.get(step.parent_exchange_id)
        if parent is None:
            raise CollaborationManifestError(
                f"dialogue step {step.step_id} has unknown parent exchange "
                f"{step.parent_exchange_id}"
            )
        if not _is_ancestor(
            parent.step_id, step.step_id, bit_by_id, ancestors_by_id
        ):
            raise CollaborationManifestError(
                f"dialogue parent {parent.exchange_id} must be a dependency ancestor of "
                f"{step.exchange_id}"
            )

    raw_limits = _expect_object(
        root["limits"],
        "limits",
        required={
            "max_participants",
            "max_exchanges",
            "deadline_ms",
            "per_step_timeout_ms",
            "max_concurrency",
        },
    )
    limits = Limits(
        max_participants=_require_int(
            raw_limits["max_participants"],
            "limits.max_participants",
            minimum=1,
            maximum=MAX_PARTICIPANTS_HARD_GUARD,
        ),
        max_exchanges=_require_int(
            raw_limits["max_exchanges"],
            "limits.max_exchanges",
            minimum=0,
            maximum=MAX_EXCHANGES_HARD_GUARD,
        ),
        deadline_ms=_require_int(
            raw_limits["deadline_ms"],
            "limits.deadline_ms",
            minimum=1,
            maximum=MAX_DEADLINE_MS_HARD_GUARD,
        ),
        per_step_timeout_ms=_require_int(
            raw_limits["per_step_timeout_ms"],
            "limits.per_step_timeout_ms",
            minimum=1,
            maximum=MAX_STEP_TIMEOUT_MS_HARD_GUARD,
        ),
        max_concurrency=_require_int(
            raw_limits["max_concurrency"],
            "limits.max_concurrency",
            minimum=1,
            maximum=MAX_PARTICIPANTS_HARD_GUARD,
        ),
    )
    if len(participants) > limits.max_participants:
        raise CollaborationManifestError(
            "planned participants exceed limits.max_participants"
        )
    if limits.max_concurrency > limits.max_participants:
        raise CollaborationManifestError(
            "limits.max_concurrency must not exceed limits.max_participants"
        )
    if limits.max_concurrency > len(participants):
        raise CollaborationManifestError(
            "limits.max_concurrency must not exceed planned participants"
        )
    if limits.per_step_timeout_ms > limits.deadline_ms:
        raise CollaborationManifestError(
            "limits.per_step_timeout_ms must not exceed limits.deadline_ms"
        )
    dialogue_count = len(dialogue_by_exchange)
    if dialogue_count > limits.max_exchanges:
        raise CollaborationManifestError(
            "planned dialogue exchanges exceed limits.max_exchanges"
        )
    if relation != "evidence-dialogue" and limits.max_exchanges != 0:
        raise CollaborationManifestError(
            "non-dialogue relations must declare limits.max_exchanges as 0"
        )

    raw_failure = _expect_object(
        root["failure_policy"],
        "failure_policy",
        required={"mode", "on_dependency_failure", "retry_policy"},
    )
    if (
        not isinstance(raw_failure["mode"], str)
        or raw_failure["mode"] not in FAILURE_MODES
    ):
        raise CollaborationManifestError(
            f"failure_policy.mode must be one of {sorted(FAILURE_MODES)}"
        )
    if raw_failure["on_dependency_failure"] != "skip":
        raise CollaborationManifestError(
            "failure_policy.on_dependency_failure must be skip"
        )
    if raw_failure["retry_policy"] != "none":
        raise CollaborationManifestError(
            "failure_policy.retry_policy must be none; automatic retry is out of scope"
        )
    failure_policy = FailurePolicy(
        mode=raw_failure["mode"],
        on_dependency_failure="skip",
        retry_policy="none",
    )

    manifest = CollaborationManifest(
        schema_version=SCHEMA_VERSION,
        batch_id=_require_id_value(root["batch_id"], "manifest.batch_id"),
        configuration_id=_require_id_value(
            root["configuration_id"], "manifest.configuration_id"
        ),
        relation=relation,
        participant_plan_id=_require_id_value(plan["plan_id"], "participant_plan.plan_id"),
        independence_policy=_require_id_value(
            plan["independence_policy"], "participant_plan.independence_policy"
        ),
        nested_delegation="disabled",
        participants=participants,
        steps=steps,
        limits=limits,
        failure_policy=failure_policy,
        manifest_digest=_canonical_digest(root),
    )
    _validate_relation(manifest)
    return manifest


def manifest_summary(manifest: CollaborationManifest) -> dict[str, Any]:
    """Return a content-free preflight result without task references."""

    return {
        "schema_version": SCHEMA_VERSION,
        "valid": True,
        "batch_id": manifest.batch_id,
        "configuration_id": manifest.configuration_id,
        "relation": manifest.relation,
        "manifest_digest": manifest.manifest_digest,
        "participant_plan": manifest.participant_plan_id,
        "participants_planned": len(manifest.participants),
        "steps_planned": len(manifest.steps),
        "dialogue_exchanges_planned": sum(
            step.kind == "dialogue" for step in manifest.steps
        ),
        "limits": {
            "max_participants": manifest.limits.max_participants,
            "max_exchanges": manifest.limits.max_exchanges,
            "deadline_ms": manifest.limits.deadline_ms,
            "per_step_timeout_ms": manifest.limits.per_step_timeout_ms,
            "max_concurrency": manifest.limits.max_concurrency,
        },
        "failure_policy": {
            "mode": manifest.failure_policy.mode,
            "on_dependency_failure": manifest.failure_policy.on_dependency_failure,
            "retry_policy": manifest.failure_policy.retry_policy,
        },
        "boundary": {
            "adapter_protocol": "injected-async-v1",
            "provider_execution": "not-implemented",
            "agentctl_mapping": "adapter-owned-not-implemented",
            "recurring_scheduler": False,
        },
    }


class _EventRecorder:
    def __init__(self, clock: EventClock) -> None:
        self.clock = clock
        self.events: list[dict[str, Any]] = []
        self.last_monotonic_ns: int | None = None

    def point(self) -> dict[str, Any]:
        wall_time, monotonic_ns = self.clock.snapshot()
        if isinstance(monotonic_ns, bool) or not isinstance(monotonic_ns, int):
            raise CollaborationExecutionError("clock returned a non-integer monotonic value")
        if monotonic_ns < 0:
            raise CollaborationExecutionError("clock returned a negative monotonic value")
        if self.last_monotonic_ns is not None and monotonic_ns < self.last_monotonic_ns:
            raise CollaborationExecutionError("clock monotonicity violation")
        self.last_monotonic_ns = monotonic_ns
        return {"wall_time": wall_time, "monotonic_ns": monotonic_ns}

    def capture(self, event_type: str, step: Step, **fields: Any) -> dict[str, Any]:
        point = self.point()
        value = {
            "sequence": len(self.events) + 1,
            "event_type": event_type,
            "step_id": step.step_id,
            "step_kind": step.kind,
            "participant_id": step.participant_id,
            **point,
            **fields,
        }
        self.events.append(value)
        return value


@dataclass
class _StepTerminal:
    record: dict[str, Any]
    private_artifact: Any = field(default=None, repr=False)


class _Runner:
    def __init__(
        self,
        manifest: CollaborationManifest,
        adapters: Mapping[str, ExecutionAdapter],
        clock: EventClock,
    ) -> None:
        self.manifest = manifest
        self.adapters = adapters
        self.clock = clock
        self.recorder = _EventRecorder(clock)
        self.step_results: dict[str, _StepTerminal] = {}
        self.private_artifacts: dict[str, Any] = {}
        self.active_count = 0
        self.peak_concurrent = 0
        self.cancel_reasons: dict[str, str] = {}

    def preflight_adapters(self) -> None:
        needed = {participant.adapter_id for participant in self.manifest.participants}
        missing = sorted(adapter_id for adapter_id in needed if adapter_id not in self.adapters)
        if missing:
            raise CollaborationExecutionError(
                "missing execution adapters: " + ", ".join(missing)
            )
        invalid = sorted(
            adapter_id
            for adapter_id in needed
            if not callable(getattr(self.adapters[adapter_id], "execute", None))
        )
        if invalid:
            raise CollaborationExecutionError(
                "execution adapters do not implement execute: " + ", ".join(invalid)
            )

    async def invoke_step(self, step: Step, deadline_at: float) -> _StepTerminal:
        participant = self.manifest.participants_by_id[step.participant_id]
        adapter = self.adapters[participant.adapter_id]
        dispatch = self.recorder.capture("dispatch", step)
        self.active_count += 1
        self.peak_concurrent = max(self.peak_concurrent, self.active_count)

        loop = asyncio.get_running_loop()
        remaining_seconds = max(0.0, deadline_at - loop.time())
        step_seconds = self.manifest.limits.per_step_timeout_ms / 1000
        effective_seconds = min(step_seconds, remaining_seconds)
        effective_timeout_ms = max(1, int(effective_seconds * 1000))
        dependency_artifacts = tuple(
            DependencyArtifact(step_id=dependency_id, value=self.private_artifacts[dependency_id])
            for dependency_id in step.depends_on
        )
        request = DispatchRequest(
            batch_id=self.manifest.batch_id,
            configuration_id=self.manifest.configuration_id,
            relation=self.manifest.relation,
            step_id=step.step_id,
            step_kind=step.kind,
            relation_role=step.relation_role,
            participant_id=step.participant_id,
            participant_role=participant.role,
            task_ref=step.task_ref,
            dependency_step_ids=step.depends_on,
            dependency_artifacts=dependency_artifacts,
            timeout_ms=effective_timeout_ms,
        )

        result: AdapterResult | None = None
        status = "failed"
        terminal_reason = "adapter-error"
        artifact_status = "missing"
        try:
            if effective_seconds <= 0:
                status = "timed-out"
                terminal_reason = "deadline-cap"
            else:
                raw_result = await asyncio.wait_for(
                    adapter.execute(request), timeout=effective_seconds
                )
                result = self._normalize_adapter_result(step, raw_result)
                status = result.status
                terminal_reason = result.terminal_reason
                artifact_status = result.artifact_status
                if status == "succeeded":
                    self.private_artifacts[step.step_id] = result.private_artifact
        except asyncio.TimeoutError:
            status = "timed-out"
            terminal_reason = (
                "step-timeout"
                if step_seconds <= remaining_seconds
                else "deadline-cap"
            )
        except asyncio.CancelledError:
            status = "cancelled"
            terminal_reason = self.cancel_reasons.get(step.step_id, "cancelled")
        except Exception:
            # Exception class/message may contain paths, provider output, prompt
            # fragments, or credential detail.  It is intentionally collapsed.
            status = "failed"
            terminal_reason = "adapter-error"
        finally:
            self.active_count -= 1

        stop = self.recorder.capture(
            "worker-stop",
            step,
            status=status,
            terminal_reason=terminal_reason,
            artifact_status=artifact_status,
        )
        if result is not None and status == "succeeded" and step.kind == "synthesis":
            assert result.synthesis_metrics is not None
            metrics = result.synthesis_metrics
            self.recorder.capture(
                "synthesis",
                step,
                adopted_count=metrics.adopted_count,
                rejected_count=metrics.rejected_count,
                unresolved_count=metrics.unresolved_count,
            )
        if result is not None and status == "succeeded" and step.kind == "dialogue":
            assert result.dialogue_metrics is not None
            metrics = result.dialogue_metrics
            dialogue_fields: dict[str, Any] = {
                "exchange_id": step.exchange_id,
                "claim_count": metrics.claim_count,
                "evidence_count": metrics.evidence_count,
                "test_count": metrics.test_count,
                "state_change_count": metrics.state_change_count,
                "unresolved_crux_count": metrics.unresolved_crux_count,
                "stop_reason": metrics.stop_reason,
            }
            if step.parent_exchange_id is not None:
                dialogue_fields["parent_exchange_id"] = step.parent_exchange_id
            self.recorder.capture("dialogue", step, **dialogue_fields)

        record = {
            "step_id": step.step_id,
            "kind": step.kind,
            "relation_role": step.relation_role,
            "participant_id": step.participant_id,
            "dependency_step_ids": list(step.depends_on),
            "status": status,
            "terminal_reason": terminal_reason,
            "artifact_status": artifact_status,
            "started": {
                "wall_time": dispatch["wall_time"],
                "monotonic_ns": dispatch["monotonic_ns"],
            },
            "finished": {
                "wall_time": stop["wall_time"],
                "monotonic_ns": stop["monotonic_ns"],
            },
            "duration_ms": elapsed_ms(
                dispatch["monotonic_ns"], stop["monotonic_ns"], step.step_id
            ),
        }
        if step.exchange_id is not None:
            record["exchange_id"] = step.exchange_id
            if step.parent_exchange_id is not None:
                record["parent_exchange_id"] = step.parent_exchange_id
        return _StepTerminal(
            record=record,
            private_artifact=(result.private_artifact if result and status == "succeeded" else None),
        )

    @staticmethod
    def _normalize_adapter_result(step: Step, value: Any) -> AdapterResult:
        if not isinstance(value, AdapterResult):
            raise CollaborationExecutionError("adapter returned a non-contract result")
        if value.status != "succeeded":
            if value.dialogue_metrics is not None or value.synthesis_metrics is not None:
                raise CollaborationExecutionError(
                    "non-success adapter result must not emit semantic metrics"
                )
        elif step.kind == "dialogue":
            if value.dialogue_metrics is None or value.synthesis_metrics is not None:
                raise CollaborationExecutionError("dialogue adapter metrics mismatch")
        elif step.kind == "synthesis":
            if value.synthesis_metrics is None or value.dialogue_metrics is not None:
                raise CollaborationExecutionError("synthesis adapter metrics mismatch")
        elif value.dialogue_metrics is not None or value.synthesis_metrics is not None:
            raise CollaborationExecutionError("worker adapter must not emit semantic metrics")
        return value

    def skipped(self, step: Step, reason: str) -> _StepTerminal:
        return _StepTerminal(
            record={
                "step_id": step.step_id,
                "kind": step.kind,
                "relation_role": step.relation_role,
                "participant_id": step.participant_id,
                "dependency_step_ids": list(step.depends_on),
                "status": "skipped",
                "terminal_reason": reason,
                "artifact_status": "not-applicable",
            }
        )

    async def execute(self) -> dict[str, Any]:
        self.preflight_adapters()
        started = self.recorder.point()
        loop = asyncio.get_running_loop()
        deadline_at = loop.time() + self.manifest.limits.deadline_ms / 1000
        pending = {step.step_id for step in self.manifest.steps}
        active: dict[asyncio.Task[_StepTerminal], Step] = {}
        active_participants: set[str] = set()
        halt_dispatch = False

        while pending or active:
            progress = False

            for step in self.manifest.steps:
                if step.step_id not in pending:
                    continue
                dependencies = [self.step_results.get(value) for value in step.depends_on]
                if dependencies and all(value is not None for value in dependencies):
                    if any(value.record["status"] != "succeeded" for value in dependencies if value):
                        self.step_results[step.step_id] = self.skipped(
                            step, "dependency-failed"
                        )
                        pending.remove(step.step_id)
                        progress = True

            if halt_dispatch:
                for step in self.manifest.steps:
                    if step.step_id in pending:
                        self.step_results[step.step_id] = self.skipped(step, "fail-fast")
                        pending.remove(step.step_id)
                        progress = True

            available_slots = self.manifest.limits.max_concurrency - len(active)
            if not halt_dispatch and available_slots > 0:
                for step in self.manifest.steps:
                    if available_slots <= 0:
                        break
                    if step.step_id not in pending:
                        continue
                    if step.participant_id in active_participants:
                        continue
                    if not all(
                        dependency_id in self.step_results
                        and self.step_results[dependency_id].record["status"] == "succeeded"
                        for dependency_id in step.depends_on
                    ):
                        continue
                    if loop.time() >= deadline_at:
                        break
                    task = asyncio.create_task(self.invoke_step(step, deadline_at))
                    active[task] = step
                    active_participants.add(step.participant_id)
                    pending.remove(step.step_id)
                    available_slots -= 1
                    progress = True

            if not active:
                if pending and loop.time() >= deadline_at:
                    for step in self.manifest.steps:
                        if step.step_id in pending:
                            self.step_results[step.step_id] = self.skipped(
                                step, "deadline-cap"
                            )
                    pending.clear()
                    break
                if pending and not progress:
                    raise CollaborationExecutionError(
                        "validated DAG made no scheduling progress"
                    )
                continue

            remaining = max(0.0, deadline_at - loop.time())
            done, _ = await asyncio.wait(
                active,
                timeout=remaining,
                return_when=asyncio.FIRST_COMPLETED,
            )
            if not done:
                for task, step in active.items():
                    self.cancel_reasons[step.step_id] = "deadline-cap"
                    task.cancel()
                done = set(active)

            completed = await asyncio.gather(*done, return_exceptions=True)
            for task, value in zip(done, completed):
                step = active.pop(task)
                active_participants.remove(step.participant_id)
                if isinstance(value, BaseException):
                    # Internal exceptions are collapsed just like adapter errors.
                    terminal = self.skipped(step, "control-plane-failure")
                    terminal.record["status"] = "failed"
                    terminal.record["artifact_status"] = "missing"
                else:
                    terminal = value
                self.step_results[step.step_id] = terminal
                if (
                    terminal.record["status"] != "succeeded"
                    and self.manifest.failure_policy.mode == "fail-fast"
                ):
                    halt_dispatch = True

            if halt_dispatch and active:
                for task, step in active.items():
                    self.cancel_reasons[step.step_id] = "fail-fast"
                    task.cancel()

        finished = self.recorder.point()
        ordered_records = [
            self.step_results[step.step_id].record for step in self.manifest.steps
        ]
        statuses = [record["status"] for record in ordered_records]
        terminal_reasons = [record["terminal_reason"] for record in ordered_records]
        if "deadline-cap" in terminal_reasons or any(
            status == "timed-out" for status in statuses
        ):
            outcome_status = "timeout"
            stop_reason = (
                "deadline-cap"
                if "deadline-cap" in terminal_reasons
                else "step-timeout"
            )
        elif any(status == "failed" for status in statuses):
            outcome_status = "failure"
            stop_reason = "step-failure"
        elif any(status == "cancelled" for status in statuses):
            outcome_status = "cancelled"
            stop_reason = (
                "fail-fast"
                if "fail-fast" in terminal_reasons
                else "adapter-cancelled"
            )
        elif all(status == "succeeded" for status in statuses):
            outcome_status = "success"
            stop_reason = "completed"
        else:
            outcome_status = "failure"
            stop_reason = "incomplete-dependency-graph"

        intervals = [
            (record["started"]["monotonic_ns"], record["finished"]["monotonic_ns"])
            for record in ordered_records
            if "started" in record and "finished" in record
        ]
        aggregate_worker_ms = round(
            sum((finish - start) for start, finish in intervals) / 1_000_000,
            3,
        )
        event_counts = {
            event_type: sum(
                event["event_type"] == event_type for event in self.recorder.events
            )
            for event_type in ("dispatch", "worker-stop", "synthesis", "dialogue")
        }
        dispatched_participants = {
            record["participant_id"] for record in ordered_records if "started" in record
        }
        return {
            "schema_version": SCHEMA_VERSION,
            "batch_id": self.manifest.batch_id,
            "configuration_id": self.manifest.configuration_id,
            "relation": self.manifest.relation,
            "manifest_digest": self.manifest.manifest_digest,
            "configuration": {
                "participant_plan": self.manifest.participant_plan_id,
                "independence_policy": self.manifest.independence_policy,
                "nested_delegation": self.manifest.nested_delegation,
                "participants_planned": len(self.manifest.participants),
                "participants_dispatched": len(dispatched_participants),
                "steps_planned": len(self.manifest.steps),
                "steps_dispatched": len(intervals),
                "dialogue_exchanges_planned": sum(
                    step.kind == "dialogue" for step in self.manifest.steps
                ),
                "dialogue_exchanges_dispatched": sum(
                    record["kind"] == "dialogue" and "started" in record
                    for record in ordered_records
                ),
                "dialogue_exchanges_returned": event_counts["dialogue"],
                "peak_concurrent": self.peak_concurrent,
            },
            "limits": {
                "max_participants": self.manifest.limits.max_participants,
                "max_exchanges": self.manifest.limits.max_exchanges,
                "deadline_ms": self.manifest.limits.deadline_ms,
                "per_step_timeout_ms": self.manifest.limits.per_step_timeout_ms,
                "max_concurrency": self.manifest.limits.max_concurrency,
            },
            "failure_policy": {
                "mode": self.manifest.failure_policy.mode,
                "on_dependency_failure": self.manifest.failure_policy.on_dependency_failure,
                "retry_policy": self.manifest.failure_policy.retry_policy,
            },
            "started": started,
            "finished": finished,
            "durations_ms": {
                "terminal_wall": elapsed_ms(
                    started["monotonic_ns"], finished["monotonic_ns"], "terminal_wall"
                ),
                "aggregate_worker": aggregate_worker_ms,
                "worker_active_union": interval_union_ms(intervals),
            },
            "outcome": {"status": outcome_status, "stop_reason": stop_reason},
            "steps": ordered_records,
            "events": self.recorder.events,
            "coverage": {
                "event_counts": event_counts,
                "dispatch_worker_stop_complete": (
                    event_counts["dispatch"] == event_counts["worker-stop"]
                ),
                "run_record_resolution": "collaboration-event-result",
                "provider_connection": "adapter-protocol-only",
                "agentctl_correlation": "not-observed",
            },
            "privacy": {
                "prompt_persisted": False,
                "transcript_persisted": False,
                "credential_persisted": False,
                "task_ref_persisted": False,
                "private_artifact_persisted": False,
                "exception_detail_persisted": False,
            },
            "boundary": {
                "adapter_protocol": "injected-async-v1",
                "provider_execution": "not-implemented",
                "agentctl_mapping": "adapter-owned-not-implemented",
                "automatic_retry": False,
                "recurring_scheduler": False,
                "cancellation": "adapter-must-propagate",
            },
        }


async def run_collaboration_async(
    payload: Any,
    adapters: Mapping[str, ExecutionAdapter],
    *,
    clock: EventClock | None = None,
) -> dict[str, Any]:
    """Validate then execute one finite collaboration manifest."""

    manifest = payload if isinstance(payload, CollaborationManifest) else parse_manifest(payload)
    return await _Runner(manifest, adapters, clock or SystemClock()).execute()


def run_collaboration(
    payload: Any,
    adapters: Mapping[str, ExecutionAdapter],
    *,
    clock: EventClock | None = None,
) -> dict[str, Any]:
    """Synchronous entry point; async callers must use ``run_collaboration_async``."""

    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(run_collaboration_async(payload, adapters, clock=clock))
    raise CollaborationExecutionError(
        "run_collaboration cannot run inside an active event loop; use run_collaboration_async"
    )


def _load_manifest(path: Path) -> Any:
    try:
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle)
    except (OSError, json.JSONDecodeError) as exc:
        raise CollaborationManifestError(f"cannot load manifest {path}: {exc}") from exc


def _print_json(payload: Any) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate or fake-run one finite duration-study collaboration manifest."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    validate_parser = subparsers.add_parser("validate")
    validate_parser.add_argument("manifest", type=Path)
    fake_parser = subparsers.add_parser("run-fake")
    fake_parser.add_argument("manifest", type=Path)
    fake_parser.add_argument("--output", type=Path)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    try:
        payload = _load_manifest(args.manifest)
        manifest = parse_manifest(payload)
        if args.command == "validate":
            _print_json(manifest_summary(manifest))
            return 0
        adapter = FakeExecutionAdapter()
        adapters = {
            participant.adapter_id: adapter for participant in manifest.participants
        }
        result = run_collaboration(manifest, adapters)
        if args.output is None:
            _print_json(result)
        else:
            atomic_write_json(args.output.resolve(), result)
            _print_json(
                {
                    "schema_version": SCHEMA_VERSION,
                    "batch_id": manifest.batch_id,
                    "result_written": True,
                    "manifest_digest": manifest.manifest_digest,
                }
            )
        return 0
    except (CollaborationManifestError, CollaborationExecutionError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
