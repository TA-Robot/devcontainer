#!/usr/bin/env python3

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


SCRIPT_DIR = Path(__file__).resolve().parent
CLI = SCRIPT_DIR / "run-agent-duration-collaboration"
sys.path.insert(0, str(SCRIPT_DIR))

from agent_duration_collaboration import (  # noqa: E402
    AdapterResult,
    CollaborationExecutionError,
    CollaborationManifestError,
    DialogueMetrics,
    FakeExecutionAdapter,
    MAX_DEADLINE_MS_HARD_GUARD,
    MAX_EXCHANGES_HARD_GUARD,
    MAX_PARTICIPANTS_HARD_GUARD,
    MAX_STEP_TIMEOUT_MS_HARD_GUARD,
    MAX_STEPS_HARD_GUARD,
    SynthesisMetrics,
    manifest_summary,
    parse_manifest,
    run_collaboration,
)
from agent_contracts import load_json, validate  # noqa: E402
from agent_duration_study import FakeClock  # noqa: E402


COLLABORATION_SCHEMA = (
    SCRIPT_DIR.parent
    / "experiments/multi-agent-duration/schemas/collaboration.schema.json"
)


def participant(participant_id: str, role: str) -> dict[str, object]:
    return {
        "participant_id": participant_id,
        "role": role,
        "adapter_id": "fixture",
    }


def step(
    step_id: str,
    kind: str,
    relation_role: str,
    participant_id: str,
    depends_on: list[str],
    *,
    exchange_id: str | None = None,
    parent_exchange_id: str | None = None,
) -> dict[str, object]:
    value: dict[str, object] = {
        "step_id": step_id,
        "kind": kind,
        "relation_role": relation_role,
        "participant_id": participant_id,
        "depends_on": depends_on,
        "task_ref": f"capsule-{step_id}",
    }
    if exchange_id is not None:
        value["exchange_id"] = exchange_id
    if parent_exchange_id is not None:
        value["parent_exchange_id"] = parent_exchange_id
    return value


def relation_manifest(relation: str) -> dict[str, object]:
    if relation == "bounded-delegation":
        participants = [participant("primary", "orchestrator"), participant("worker-a", "worker")]
        steps = [
            step("delegate-a", "worker", "delegate", "worker-a", []),
            step("synthesis", "synthesis", "synthesis", "primary", ["delegate-a"]),
        ]
        max_exchanges = 0
        concurrency = 2
    elif relation == "parallel-shards":
        participants = [
            participant("primary", "orchestrator"),
            participant("worker-a", "worker"),
            participant("worker-b", "worker"),
        ]
        steps = [
            step("shard-a", "worker", "shard", "worker-a", []),
            step("shard-b", "worker", "shard", "worker-b", []),
            step("synthesis", "synthesis", "synthesis", "primary", ["shard-a", "shard-b"]),
        ]
        max_exchanges = 0
        concurrency = 2
    elif relation == "independent-candidates":
        participants = [
            participant("primary", "selector"),
            participant("candidate-a", "candidate"),
            participant("candidate-b", "candidate"),
        ]
        steps = [
            step("candidate-a", "worker", "candidate", "candidate-a", []),
            step("candidate-b", "worker", "candidate", "candidate-b", []),
            step(
                "synthesis",
                "synthesis",
                "synthesis",
                "primary",
                ["candidate-a", "candidate-b"],
            ),
        ]
        max_exchanges = 0
        concurrency = 2
    elif relation == "maker-verifier":
        participants = [
            participant("primary", "orchestrator"),
            participant("maker", "maker"),
            participant("verifier", "verifier"),
        ]
        steps = [
            step("make", "worker", "maker", "maker", []),
            step("verify", "worker", "verifier", "verifier", ["make"]),
            step("synthesis", "synthesis", "synthesis", "primary", ["verify"]),
        ]
        max_exchanges = 0
        concurrency = 2
    elif relation == "evidence-dialogue":
        participants = [
            participant("primary", "orchestrator"),
            participant("proposer", "proposer"),
            participant("critic", "critic"),
        ]
        steps = [
            step(
                "dialogue-a",
                "dialogue",
                "dialogue",
                "proposer",
                [],
                exchange_id="exchange-a",
            ),
            step(
                "dialogue-b",
                "dialogue",
                "dialogue",
                "critic",
                ["dialogue-a"],
                exchange_id="exchange-b",
                parent_exchange_id="exchange-a",
            ),
            step("synthesis", "synthesis", "synthesis", "primary", ["dialogue-b"]),
        ]
        max_exchanges = 4
        concurrency = 2
    elif relation == "staged-pipeline":
        participants = [
            participant("primary", "orchestrator"),
            participant("researcher", "researcher"),
            participant("implementer", "implementer"),
        ]
        steps = [
            step("research", "worker", "stage", "researcher", []),
            step("implement", "worker", "stage", "implementer", ["research"]),
            step("synthesis", "synthesis", "synthesis", "primary", ["implement"]),
        ]
        max_exchanges = 0
        concurrency = 2
    else:
        raise AssertionError(relation)

    return {
        "schema_version": 1,
        "batch_id": f"batch-{relation}",
        "configuration_id": f"config-{relation}",
        "relation": relation,
        "participant_plan": {
            "plan_id": f"plan-{relation}",
            "independence_policy": "manifest-declared",
            "nested_delegation": "disabled",
            "participants": participants,
        },
        "steps": steps,
        "limits": {
            "max_participants": len(participants),
            "max_exchanges": max_exchanges,
            "deadline_ms": 1_000,
            "per_step_timeout_ms": 200,
            "max_concurrency": concurrency,
        },
        "failure_policy": {
            "mode": "continue-independent",
            "on_dependency_failure": "skip",
            "retry_policy": "none",
        },
    }


class RecordingAdapter:
    def __init__(
        self,
        *,
        fail_steps: set[str] | None = None,
        secret: str = "private-prompt-and-artifact-secret",
        yield_once: bool = False,
    ) -> None:
        self.fail_steps = fail_steps or set()
        self.secret = secret
        self.yield_once = yield_once
        self.calls: list[str] = []
        self.active = 0
        self.peak = 0
        self.active_by_participant: dict[str, int] = {}
        self.participant_peak: dict[str, int] = {}

    async def execute(self, request):
        import asyncio

        self.calls.append(request.step_id)
        self.active += 1
        self.peak = max(self.peak, self.active)
        active = self.active_by_participant.get(request.participant_id, 0) + 1
        self.active_by_participant[request.participant_id] = active
        self.participant_peak[request.participant_id] = max(
            self.participant_peak.get(request.participant_id, 0), active
        )
        try:
            if self.yield_once:
                await asyncio.sleep(0.01)
            if request.step_id in self.fail_steps:
                return AdapterResult(
                    status="failed",
                    terminal_reason="adapter-failure",
                    artifact_status="missing",
                )
            dialogue = None
            synthesis = None
            if request.step_kind == "dialogue":
                dialogue = DialogueMetrics(2, 1, 1, 1, 0, "evidence-added")
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
                private_artifact={"secret": self.secret, "step": request.step_id},
                dialogue_metrics=dialogue,
                synthesis_metrics=synthesis,
            )
        finally:
            self.active -= 1
            self.active_by_participant[request.participant_id] -= 1


class RaisingAdapter:
    def __init__(self, secret: str) -> None:
        self.secret = secret
        self.calls = 0

    async def execute(self, request):
        self.calls += 1
        raise RuntimeError(self.secret)


class HangingAdapter:
    def __init__(self) -> None:
        self.calls = 0
        self.cancelled = 0

    async def execute(self, request):
        import asyncio

        self.calls += 1
        try:
            await asyncio.sleep(60)
        except asyncio.CancelledError:
            self.cancelled += 1
            raise


class CancelledResultAdapter:
    async def execute(self, request):
        return AdapterResult(
            status="cancelled",
            terminal_reason="cancelled",
            artifact_status="missing",
        )


class CollaborationManifestTests(unittest.TestCase):
    def test_all_relation_fixtures_satisfy_machine_schema(self) -> None:
        schema = load_json(COLLABORATION_SCHEMA)
        for relation in (
            "bounded-delegation",
            "parallel-shards",
            "independent-candidates",
            "maker-verifier",
            "evidence-dialogue",
            "staged-pipeline",
        ):
            with self.subTest(relation=relation):
                validate(relation_manifest(relation), schema)

    def test_schema_resource_guards_match_control_plane(self) -> None:
        schema = load_json(COLLABORATION_SCHEMA)
        definitions = schema["$defs"]
        self.assertEqual(
            MAX_PARTICIPANTS_HARD_GUARD,
            definitions["participant_plan"]["properties"]["participants"]["maxItems"],
        )
        self.assertEqual(
            MAX_STEPS_HARD_GUARD,
            schema["properties"]["steps"]["maxItems"],
        )
        limits = definitions["limits"]["properties"]
        self.assertEqual(MAX_EXCHANGES_HARD_GUARD, limits["max_exchanges"]["maximum"])
        self.assertEqual(MAX_DEADLINE_MS_HARD_GUARD, limits["deadline_ms"]["maximum"])
        self.assertEqual(
            MAX_STEP_TIMEOUT_MS_HARD_GUARD,
            limits["per_step_timeout_ms"]["maximum"],
        )

    def test_all_six_relation_shapes_validate_without_fixed_global_count(self) -> None:
        for relation in (
            "bounded-delegation",
            "parallel-shards",
            "independent-candidates",
            "maker-verifier",
            "evidence-dialogue",
            "staged-pipeline",
        ):
            with self.subTest(relation=relation):
                manifest = parse_manifest(relation_manifest(relation))
                self.assertEqual(relation, manifest.relation)

    def test_unknown_dependency_is_rejected_before_execution(self) -> None:
        value = relation_manifest("bounded-delegation")
        value["steps"][0]["depends_on"] = ["missing"]  # type: ignore[index]
        with self.assertRaisesRegex(CollaborationManifestError, "unknown dependencies"):
            parse_manifest(value)

    def test_dependency_cycle_is_rejected_before_execution(self) -> None:
        value = relation_manifest("bounded-delegation")
        value["steps"][0]["depends_on"] = ["synthesis"]  # type: ignore[index]
        with self.assertRaisesRegex(CollaborationManifestError, "cycle"):
            parse_manifest(value)

    def test_deep_valid_dag_does_not_depend_on_python_recursion_limit(self) -> None:
        value = relation_manifest("bounded-delegation")
        delegate_count = 1_500
        delegates = []
        for index in range(delegate_count):
            step_id = f"delegate-{index:04d}"
            dependencies = [] if index == 0 else [f"delegate-{index - 1:04d}"]
            delegates.append(
                step(step_id, "worker", "delegate", "worker-a", dependencies)
            )
        value["steps"] = [
            *delegates,
            step(
                "synthesis",
                "synthesis",
                "synthesis",
                "primary",
                [delegates[-1]["step_id"]],
            ),
        ]
        value["limits"]["max_concurrency"] = 1  # type: ignore[index]
        manifest = parse_manifest(value)
        self.assertEqual(delegate_count + 1, len(manifest.steps))

    def test_duplicate_step_id_is_rejected(self) -> None:
        value = relation_manifest("parallel-shards")
        value["steps"][1]["step_id"] = "shard-a"  # type: ignore[index]
        with self.assertRaisesRegex(CollaborationManifestError, "step_id values must be unique"):
            parse_manifest(value)

    def test_participant_cap_is_enforced(self) -> None:
        value = relation_manifest("parallel-shards")
        value["limits"]["max_participants"] = 2  # type: ignore[index]
        with self.assertRaisesRegex(CollaborationManifestError, "planned participants exceed"):
            parse_manifest(value)

    def test_exchange_cap_is_enforced_without_default_exchange_count(self) -> None:
        value = relation_manifest("evidence-dialogue")
        value["limits"]["max_exchanges"] = 1  # type: ignore[index]
        with self.assertRaisesRegex(CollaborationManifestError, "planned dialogue exchanges exceed"):
            parse_manifest(value)

    def test_step_timeout_must_fit_batch_deadline(self) -> None:
        value = relation_manifest("bounded-delegation")
        value["limits"]["deadline_ms"] = 10  # type: ignore[index]
        value["limits"]["per_step_timeout_ms"] = 11  # type: ignore[index]
        with self.assertRaisesRegex(CollaborationManifestError, "must not exceed"):
            parse_manifest(value)

    def test_automatic_retry_policy_is_rejected(self) -> None:
        value = relation_manifest("bounded-delegation")
        value["failure_policy"]["retry_policy"] = "automatic"  # type: ignore[index]
        with self.assertRaisesRegex(CollaborationManifestError, "must be none"):
            parse_manifest(value)

    def test_prompt_or_other_unknown_manifest_key_is_rejected(self) -> None:
        value = relation_manifest("bounded-delegation")
        value["prompt"] = "do not persist me"
        with self.assertRaisesRegex(CollaborationManifestError, "unsupported keys: prompt"):
            parse_manifest(value)

    def test_parallel_relation_rejects_one_shard_disguised_as_parallel(self) -> None:
        value = relation_manifest("parallel-shards")
        value["steps"] = [value["steps"][0], value["steps"][2]]  # type: ignore[index]
        value["steps"][1]["depends_on"] = ["shard-a"]  # type: ignore[index]
        value["participant_plan"]["participants"] = [  # type: ignore[index]
            value["participant_plan"]["participants"][0],  # type: ignore[index]
            value["participant_plan"]["participants"][1],  # type: ignore[index]
        ]
        value["limits"]["max_participants"] = 2  # type: ignore[index]
        value["limits"]["max_concurrency"] = 2  # type: ignore[index]
        with self.assertRaisesRegex(CollaborationManifestError, "at least two"):
            parse_manifest(value)

    def test_parallel_shards_width_one_keeps_logical_shards_separate(self) -> None:
        value = relation_manifest("parallel-shards")
        value["steps"][1]["participant_id"] = "worker-a"  # type: ignore[index]
        value["participant_plan"]["participants"] = [  # type: ignore[index]
            value["participant_plan"]["participants"][0],  # type: ignore[index]
            value["participant_plan"]["participants"][1],  # type: ignore[index]
        ]
        value["limits"]["max_participants"] = 2  # type: ignore[index]
        value["limits"]["max_concurrency"] = 1  # type: ignore[index]
        adapter = RecordingAdapter(yield_once=True)
        result = run_collaboration(value, {"fixture": adapter})
        self.assertEqual("success", result["outcome"]["status"])
        self.assertEqual(1, result["configuration"]["peak_concurrent"])
        self.assertEqual(1, adapter.participant_peak["worker-a"])

    def test_schema_version_boolean_is_rejected(self) -> None:
        value = relation_manifest("bounded-delegation")
        value["schema_version"] = True
        with self.assertRaisesRegex(CollaborationManifestError, "schema_version"):
            parse_manifest(value)

    def test_dialogue_parent_must_be_a_dependency_ancestor(self) -> None:
        value = relation_manifest("evidence-dialogue")
        value["steps"][1]["depends_on"] = []  # type: ignore[index]
        with self.assertRaisesRegex(CollaborationManifestError, "dependency ancestor"):
            parse_manifest(value)

    def test_dialogue_requires_multiple_participants_and_linked_exchanges(self) -> None:
        value = relation_manifest("evidence-dialogue")
        value["steps"][1]["participant_id"] = "proposer"  # type: ignore[index]
        value["participant_plan"]["participants"] = [  # type: ignore[index]
            value["participant_plan"]["participants"][0],  # type: ignore[index]
            value["participant_plan"]["participants"][1],  # type: ignore[index]
        ]
        value["limits"]["max_participants"] = 2  # type: ignore[index]
        value["limits"]["max_concurrency"] = 2  # type: ignore[index]
        with self.assertRaisesRegex(CollaborationManifestError, "two dialogue participants"):
            parse_manifest(value)

        value = relation_manifest("evidence-dialogue")
        value["steps"][1]["depends_on"] = []  # type: ignore[index]
        value["steps"][1].pop("parent_exchange_id")  # type: ignore[index]
        value["steps"][2]["depends_on"] = [  # type: ignore[index]
            "dialogue-a",
            "dialogue-b",
        ]
        with self.assertRaisesRegex(CollaborationManifestError, "evidence dependency"):
            parse_manifest(value)

    def test_non_success_adapter_result_cannot_carry_private_valid_artifact(self) -> None:
        with self.assertRaisesRegex(ValueError, "must not expose"):
            AdapterResult(
                status="failed",
                terminal_reason="adapter-failure",
                artifact_status="valid",
                private_artifact="secret",
            )

    def test_summary_omits_task_references(self) -> None:
        value = relation_manifest("bounded-delegation")
        value["steps"][0]["task_ref"] = "secret-task-ref"  # type: ignore[index]
        summary = manifest_summary(parse_manifest(value))
        rendered = json.dumps(summary, sort_keys=True)
        self.assertNotIn("secret-task-ref", rendered)
        self.assertEqual("not-implemented", summary["boundary"]["provider_execution"])

    def test_adapter_cannot_put_arbitrary_text_in_dialogue_stop_reason(self) -> None:
        with self.assertRaisesRegex(ValueError, "content-free allowlisted"):
            DialogueMetrics(1, 1, 0, 0, 1, "private-provider-error-secret")


class CollaborationExecutionTests(unittest.TestCase):
    def test_fake_run_captures_dispatch_stop_and_synthesis_events(self) -> None:
        value = relation_manifest("bounded-delegation")
        result = run_collaboration(
            value,
            {"fixture": FakeExecutionAdapter()},
            clock=FakeClock(),
        )
        self.assertEqual("success", result["outcome"]["status"])
        self.assertEqual(
            {"dispatch": 2, "worker-stop": 2, "synthesis": 1, "dialogue": 0},
            result["coverage"]["event_counts"],
        )
        self.assertTrue(result["coverage"]["dispatch_worker_stop_complete"])

    def test_private_artifact_and_task_ref_never_enter_analytics(self) -> None:
        secret = "TOP-SECRET-PROMPT-TRANSCRIPT-CREDENTIAL"
        value = relation_manifest("bounded-delegation")
        value["steps"][0]["task_ref"] = "opaque-secret-ref"  # type: ignore[index]
        adapter = RecordingAdapter(secret=secret)
        result = run_collaboration(value, {"fixture": adapter}, clock=FakeClock())
        rendered = json.dumps(result, sort_keys=True)
        self.assertNotIn(secret, rendered)
        self.assertNotIn("opaque-secret-ref", rendered)
        self.assertFalse(result["privacy"]["private_artifact_persisted"])
        self.assertFalse(result["privacy"]["prompt_persisted"])

    def test_adapter_exception_detail_is_collapsed(self) -> None:
        secret = "credential-path-and-provider-output-secret"
        adapter = RaisingAdapter(secret)
        value = relation_manifest("bounded-delegation")
        value["failure_policy"]["mode"] = "fail-fast"  # type: ignore[index]
        result = run_collaboration(value, {"fixture": adapter})
        self.assertEqual("failure", result["outcome"]["status"])
        self.assertNotIn(secret, json.dumps(result))
        self.assertEqual("adapter-error", result["steps"][0]["terminal_reason"])
        self.assertEqual(1, adapter.calls)

    def test_parallel_steps_obey_explicit_bounded_concurrency(self) -> None:
        value = relation_manifest("parallel-shards")
        value["limits"]["max_concurrency"] = 2  # type: ignore[index]
        adapter = RecordingAdapter(yield_once=True)
        result = run_collaboration(value, {"fixture": adapter})
        self.assertEqual(2, adapter.peak)
        self.assertEqual(2, result["configuration"]["peak_concurrent"])

    def test_same_participant_is_never_dispatched_concurrently(self) -> None:
        value = relation_manifest("maker-verifier")
        second = step("make-b", "worker", "maker", "maker", [])
        value["steps"].insert(1, second)  # type: ignore[union-attr]
        value["steps"][2]["depends_on"] = ["make", "make-b"]  # type: ignore[index]
        adapter = RecordingAdapter(yield_once=True)
        result = run_collaboration(value, {"fixture": adapter})
        self.assertEqual("success", result["outcome"]["status"])
        self.assertEqual(1, adapter.participant_peak["maker"])

    def test_continue_independent_runs_unaffected_branch_and_skips_dependent(self) -> None:
        value = relation_manifest("parallel-shards")
        adapter = RecordingAdapter(fail_steps={"shard-a"}, yield_once=True)
        result = run_collaboration(value, {"fixture": adapter})
        statuses = {item["step_id"]: item["status"] for item in result["steps"]}
        self.assertEqual("failed", statuses["shard-a"])
        self.assertEqual("succeeded", statuses["shard-b"])
        self.assertEqual("skipped", statuses["synthesis"])
        self.assertEqual(1, adapter.calls.count("shard-a"))
        self.assertEqual(1, adapter.calls.count("shard-b"))
        self.assertNotIn("synthesis", adapter.calls)

    def test_fail_fast_stops_new_dispatch_without_retry(self) -> None:
        value = relation_manifest("parallel-shards")
        value["limits"]["max_concurrency"] = 1  # type: ignore[index]
        value["failure_policy"]["mode"] = "fail-fast"  # type: ignore[index]
        adapter = RecordingAdapter(fail_steps={"shard-a"})
        result = run_collaboration(value, {"fixture": adapter})
        self.assertEqual(["shard-a"], adapter.calls)
        self.assertEqual("failure", result["outcome"]["status"])
        self.assertEqual("skipped", result["steps"][1]["status"])

    def test_per_step_timeout_cancels_adapter_once(self) -> None:
        value = relation_manifest("bounded-delegation")
        value["limits"]["per_step_timeout_ms"] = 5  # type: ignore[index]
        value["limits"]["deadline_ms"] = 100  # type: ignore[index]
        value["failure_policy"]["mode"] = "fail-fast"  # type: ignore[index]
        adapter = HangingAdapter()
        result = run_collaboration(value, {"fixture": adapter})
        self.assertEqual("timeout", result["outcome"]["status"])
        self.assertEqual("timed-out", result["steps"][0]["status"])
        self.assertEqual(1, adapter.calls)
        self.assertEqual(1, adapter.cancelled)

    def test_adapter_cancellation_is_not_mislabeled_as_fail_fast(self) -> None:
        value = relation_manifest("bounded-delegation")
        result = run_collaboration(value, {"fixture": CancelledResultAdapter()})
        self.assertEqual("cancelled", result["outcome"]["status"])
        self.assertEqual("adapter-cancelled", result["outcome"]["stop_reason"])

    def test_dialogue_events_are_content_free_count_envelopes(self) -> None:
        adapter = RecordingAdapter()
        result = run_collaboration(
            relation_manifest("evidence-dialogue"),
            {"fixture": adapter},
            clock=FakeClock(),
        )
        events = [item for item in result["events"] if item["event_type"] == "dialogue"]
        self.assertEqual(2, len(events))
        self.assertEqual(2, events[0]["claim_count"])
        self.assertEqual("exchange-a", events[1]["parent_exchange_id"])
        self.assertNotIn("content", events[0])

    def test_missing_adapter_is_rejected_before_any_dispatch(self) -> None:
        with self.assertRaisesRegex(CollaborationExecutionError, "missing execution adapters"):
            run_collaboration(relation_manifest("bounded-delegation"), {})

    def test_every_relation_completes_with_fake_adapter(self) -> None:
        for relation in (
            "bounded-delegation",
            "parallel-shards",
            "independent-candidates",
            "maker-verifier",
            "evidence-dialogue",
            "staged-pipeline",
        ):
            with self.subTest(relation=relation):
                result = run_collaboration(
                    relation_manifest(relation),
                    {"fixture": FakeExecutionAdapter()},
                    clock=FakeClock(),
                )
                self.assertEqual("success", result["outcome"]["status"])


class CollaborationCliTests(unittest.TestCase):
    def test_cli_validate_and_fake_run_emit_content_free_json(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            directory = Path(raw)
            manifest_path = directory / "manifest.json"
            manifest_path.write_text(
                json.dumps(relation_manifest("bounded-delegation")),
                encoding="utf-8",
            )
            validated = subprocess.run(
                [sys.executable, str(CLI), "validate", str(manifest_path)],
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )
            self.assertEqual(0, validated.returncode, validated.stderr)
            self.assertTrue(json.loads(validated.stdout)["valid"])

            executed = subprocess.run(
                [sys.executable, str(CLI), "run-fake", str(manifest_path)],
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )
            self.assertEqual(0, executed.returncode, executed.stderr)
            result = json.loads(executed.stdout)
            self.assertEqual("success", result["outcome"]["status"])
            self.assertEqual("not-implemented", result["boundary"]["provider_execution"])


if __name__ == "__main__":
    unittest.main()
