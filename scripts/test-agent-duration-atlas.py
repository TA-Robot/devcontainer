#!/usr/bin/env python3

from __future__ import annotations

import copy
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


SCRIPT_DIR = Path(__file__).resolve().parent
CLI = SCRIPT_DIR / "build-agent-duration-atlas"
sys.path.insert(0, str(SCRIPT_DIR))

from agent_duration_atlas import (  # noqa: E402
    AtlasError,
    atomic_write_atlas,
    build_atlas,
    encode_atlas,
    load_run_records_bounded,
    validate_atlas,
)
from agent_duration_study import build_fake_run, canonical_json_digest  # noqa: E402


def clone_run(record: dict[str, object], run_id: str, *, block_id: str | None = None) -> dict[str, object]:
    cloned = copy.deepcopy(record)
    cloned["run_id"] = run_id
    if block_id is not None:
        cloned["block_id"] = block_id
    return cloned


def change_image(record: dict[str, object], digit: str) -> None:
    digest = f"sha256:{digit * 64}"
    record["environment"]["image_digest"] = digest  # type: ignore[index]
    record["diagnostics"]["provider"]["sandbox_preflight"]["image_digest"] = digest  # type: ignore[index]
    evaluator = record["diagnostics"]["evaluator"]  # type: ignore[index]
    if evaluator["image_digest"] is not None:
        evaluator["image_digest"] = digest
    for participant in record["participants"]:  # type: ignore[index]
        runtime = participant["runtime_identity"]
        if "image_digest" in runtime:
            runtime["image_digest"] = digest


def quality_fail_run(record: dict[str, object], run_id: str) -> dict[str, object]:
    failed = clone_run(record, run_id)
    outcome = failed["outcome"]  # type: ignore[index]
    outcome.update(
        {
            "online_acceptance": "fail",
            "quality_pass": False,
            "quality_basis": "online-fail",
            "failure_class": "online-validation-failed",
        }
    )
    evaluator = failed["diagnostics"]["evaluator"]  # type: ignore[index]
    evaluator["status"] = "fail"
    evaluator["checks"][0].update({"status": "fail", "exit_code": 1})
    return failed


class AgentDurationAtlasTests(unittest.TestCase):
    def setUp(self) -> None:
        self.base = build_fake_run("solo-complete")

    def build(self, records: list[dict[str, object]], *, max_records: int | None = None) -> dict[str, object]:
        return build_atlas(  # type: ignore[arg-type]
            records,
            max_records=max_records or len(records),
            max_input_bytes=8 * 1024 * 1024,
            max_output_bytes=8 * 1024 * 1024,
        )

    def test_primary_stratum_prevents_identity_setting_runtime_and_image_mixing(self) -> None:
        applied = clone_run(self.base, "run-applied")

        requested_only = clone_run(self.base, "run-requested-only")
        setting = requested_only["participants"][0]["generation_settings"][0]  # type: ignore[index]
        setting["status"] = "unknown"
        setting.pop("applied_value")

        alias_only = clone_run(self.base, "run-alias-only")
        identity = alias_only["participants"][0]["model_identity"]  # type: ignore[index]
        identity["identity_confidence"] = "alias-only"
        identity.pop("resolved_id")

        other_cli = clone_run(self.base, "run-other-cli")
        other_cli["participants"][0]["runtime_identity"]["cli_version"] = "2"  # type: ignore[index]

        other_surface = clone_run(self.base, "run-other-surface")
        other_surface["participants"][0]["runtime_identity"]["execution_surface"] = "direct-provider"  # type: ignore[index]

        other_provider = clone_run(self.base, "run-other-provider")
        other_provider["participants"][0]["runtime_identity"]["provider"] = "codex"  # type: ignore[index]

        other_relation = clone_run(self.base, "run-other-relation")
        other_relation["configuration"]["relation"] = "maker-verifier"  # type: ignore[index]

        other_image = clone_run(self.base, "run-other-image")
        change_image(other_image, "9")

        other_environment = clone_run(self.base, "run-other-environment")
        other_environment["environment"]["session_context"] = "warm-task"  # type: ignore[index]

        other_requested_alias = clone_run(self.base, "run-other-requested-alias")
        other_requested_alias["participants"][0]["model_identity"]["requested_alias"] = "fixture-model-alias"  # type: ignore[index]

        other_applied_value = clone_run(self.base, "run-other-applied-value")
        applied_setting = other_applied_value["participants"][0]["generation_settings"][0]  # type: ignore[index]
        applied_setting["requested_value"] = "alternate"
        applied_setting["applied_value"] = "alternate"

        atlas = self.build(
            [
                applied,
                requested_only,
                alias_only,
                other_cli,
                other_surface,
                other_provider,
                other_relation,
                other_image,
                other_environment,
                other_requested_alias,
                other_applied_value,
            ]
        )
        self.assertEqual(atlas["counts"]["series"], 11)  # type: ignore[index]
        unknown_settings = [
            setting
            for series in atlas["series"]  # type: ignore[index]
            for participant in series["series_stratum"]["participants"]
            for setting in participant["generation_settings"]
            if setting["status"] == "unknown"
        ]
        self.assertEqual(len(unknown_settings), 1)
        self.assertNotIn("applied_value", unknown_settings[0])

    def test_case_revision_is_nested_without_flattening_between_cases(self) -> None:
        first = clone_run(self.base, "case-a-1", block_id="block-a")
        second = clone_run(self.base, "case-a-2", block_id="block-b")
        variant_one = clone_run(self.base, "case-b-1", block_id="block-a")
        variant_two = clone_run(self.base, "case-b-2", block_id="block-b")
        for record in (variant_one, variant_two):
            record["case"]["case_id"] = "F03-S-variant"  # type: ignore[index]
            record["case"]["revision"] = 2  # type: ignore[index]

        atlas = self.build([first, second, variant_one, variant_two])
        self.assertEqual(atlas["counts"], {
            "series": 1,
            "case_strata": 2,
            "samples": 4,
            "output_entities": 7,
        })
        series = atlas["series"][0]  # type: ignore[index]
        self.assertEqual(series["evidence_state"], "family-provisional")
        self.assertEqual(series["case_aware_summary_status"], "available")
        self.assertEqual(len(series["cases"]), 2)
        self.assertTrue(
            all(case["evidence_state"] == "same-case-repeat" for case in series["cases"])
        )
        pass_summary = next(
            item
            for item in series["case_aware_summaries"]
            if item["view_id"] == "quality-pass-user-result"
        )
        self.assertEqual(len(pass_summary["case_median_points_ms"]), 2)
        self.assertEqual(series["characterization"]["status"], "not-assessed")
        serialized = json.dumps(atlas, sort_keys=True)
        self.assertNotIn("family-characterized", serialized)
        self.assertNotIn("quantile", serialized)
        self.assertNotIn("prediction_band", serialized)

    def test_sparse_multiple_cases_do_not_get_case_aware_summary(self) -> None:
        case_a_one = clone_run(self.base, "case-a-1")
        case_a_two = clone_run(self.base, "case-a-2")
        case_b = clone_run(self.base, "case-b-1")
        case_b["case"]["case_id"] = "F03-S-sparse"  # type: ignore[index]
        case_b["case"]["revision"] = 2  # type: ignore[index]
        atlas = self.build([case_a_one, case_a_two, case_b])
        series = atlas["series"][0]  # type: ignore[index]
        self.assertEqual(series["case_aware_summary_status"], "insufficient-repeat-structure")
        self.assertEqual(series["case_aware_summaries"], [])

    def test_catalog_growth_is_sample_provenance_not_case_identity(self) -> None:
        earlier = clone_run(self.base, "catalog-earlier")
        current = clone_run(self.base, "catalog-current")
        earlier["case"]["catalog_digest"] = f"sha256:{'1' * 64}"  # type: ignore[index]
        current["case"]["catalog_digest"] = f"sha256:{'2' * 64}"  # type: ignore[index]
        earlier["snapshot"]["fixture_revision"] = "recipe-v1"  # type: ignore[index]
        current["snapshot"]["fixture_revision"] = "recipe-v2"  # type: ignore[index]

        atlas = self.build([earlier, current])
        self.assertEqual(1, atlas["counts"]["case_strata"])
        case = atlas["series"][0]["cases"][0]
        self.assertNotIn("catalog_digest", case["primary_stratum"]["case"])
        self.assertEqual(
            {f"sha256:{'1' * 64}", f"sha256:{'2' * 64}"},
            {sample["catalog_digest"] for sample in case["samples"]},
        )
        self.assertEqual(
            {"recipe-v1", "recipe-v2"},
            {sample["fixture_revision"] for sample in case["samples"]},
        )

    def test_single_observation_is_raw_point_and_missing_progress_is_not_imputed(self) -> None:
        single = self.build([self.base])
        case = single["series"][0]["cases"][0]  # type: ignore[index]
        self.assertEqual(case["evidence_state"], "single-observation")
        self.assertTrue(all(len(view["points"]) == 1 for view in case["duration_views"]))
        self.assertTrue(all("observed_range_ms" not in view for view in case["duration_views"]))

        missing = build_fake_run("missing-progress")
        missing_atlas = self.build([missing])
        missing_case = missing_atlas["series"][0]["cases"][0]  # type: ignore[index]
        sample = missing_case["samples"][0]
        self.assertEqual(sample["first_artifact"], {"resolution": "not-observed"})
        self.assertNotIn(
            "first-artifact-progress",
            [view["view_id"] for view in missing_case["duration_views"]],
        )

    def test_quality_populations_and_censoring_remain_explicit(self) -> None:
        passed = clone_run(self.base, "quality-pass")
        failed = quality_fail_run(self.base, "quality-fail")
        timeout = build_fake_run("timeout")
        timeout["run_id"] = "quality-unknown-timeout"
        atlas = self.build([passed, failed, timeout])
        samples = [
            sample
            for series in atlas["series"]  # type: ignore[index]
            for case in series["cases"]
            for sample in case["samples"]
        ]
        self.assertEqual(
            {sample["quality_population"] for sample in samples},
            {"quality-pass", "quality-fail", "quality-unknown"},
        )
        timeout_sample = next(sample for sample in samples if sample["run_id"] == "quality-unknown-timeout")
        self.assertEqual(timeout_sample["censoring"]["status"], "right-censored")
        self.assertIn("safety_cap_ms", timeout_sample["censoring"])
        failed_sample = next(sample for sample in samples if sample["run_id"] == "quality-fail")
        self.assertEqual(failed_sample["quality_evidence"]["evaluator_status"], "fail")
        self.assertEqual(
            failed_sample["quality_evidence"]["score"]["failed_check_ids"],
            ["fixture-online-v1"],
        )

    def test_source_digests_and_bytes_are_reproducible_for_input_order(self) -> None:
        one = clone_run(self.base, "repeat-one")
        two = clone_run(self.base, "repeat-two")
        forward = self.build([one, two])
        reverse = self.build([two, one])
        self.assertEqual(encode_atlas(forward), encode_atlas(reverse))
        source = forward["source"]
        expected = sorted(
            [
                {"run_id": record["run_id"], "run_digest": canonical_json_digest(record)}
                for record in (one, two)
            ],
            key=lambda item: item["run_id"],
        )
        self.assertEqual(source["runs"], expected)
        self.assertEqual(source["run_set_digest"], canonical_json_digest(expected))
        serialized = encode_atlas(forward).decode("utf-8")
        for forbidden in (
            "prompt_text",
            "raw_prompt",
            "transcript",
            "recommendation",
            "ranking",
            "selection_rule",
        ):
            self.assertNotIn(forbidden, serialized)

    def test_atomic_replace_never_exposes_partial_or_overwrites_before_cap_check(self) -> None:
        atlas = self.build([self.base])
        with tempfile.TemporaryDirectory(prefix="duration-atlas-atomic-") as raw_temp:
            output = Path(raw_temp) / "current.json"
            output.write_bytes(b"old-atlas\n")
            observed: list[bytes] = []

            def replace(source: Path, destination: Path) -> None:
                observed.append(destination.read_bytes())
                json.loads(source.read_text(encoding="utf-8"))
                os.replace(source, destination)

            atomic_write_atlas(
                output,
                atlas,
                max_output_bytes=8 * 1024 * 1024,
                replace=replace,
            )
            self.assertEqual(observed, [b"old-atlas\n"])
            self.assertEqual(json.loads(output.read_text(encoding="utf-8")), atlas)
            stable = output.read_bytes()
            with self.assertRaises(AtlasError):
                atomic_write_atlas(output, atlas, max_output_bytes=1)
            self.assertEqual(output.read_bytes(), stable)

    def test_input_caps_and_unknown_schema_fail_closed(self) -> None:
        unknown = clone_run(self.base, "unknown-schema")
        unknown["schema_version"] = 999
        with self.assertRaises(AtlasError):
            self.build([unknown])

        with tempfile.TemporaryDirectory(prefix="duration-atlas-input-") as raw_temp:
            path = Path(raw_temp) / "run.json"
            encoded = (json.dumps(self.base, sort_keys=True) + "\n").encode("utf-8")
            path.write_bytes(encoded)
            with self.assertRaises(AtlasError):
                load_run_records_bounded(
                    [path],
                    max_records=1,
                    max_input_bytes=len(encoded) - 1,
                )
            records, observed_bytes = load_run_records_bounded(
                [path],
                max_records=1,
                max_input_bytes=len(encoded),
            )
            self.assertEqual((len(records), observed_bytes), (1, len(encoded)))

        atlas = self.build([self.base])
        atlas["schema_version"] = 999
        with self.assertRaises(AtlasError):
            validate_atlas(atlas)

    def test_cli_requires_bound_and_writes_a_valid_atlas(self) -> None:
        with tempfile.TemporaryDirectory(prefix="duration-atlas-cli-") as raw_temp:
            directory = Path(raw_temp)
            run_path = directory / "run.json"
            output = directory / "atlas" / "current.json"
            run_path.write_text(
                json.dumps(self.base, ensure_ascii=False, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            missing_cap = subprocess.run(
                [sys.executable, str(CLI), str(run_path), "--output", str(output)],
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )
            self.assertEqual(missing_cap.returncode, 2)
            completed = subprocess.run(
                [
                    sys.executable,
                    str(CLI),
                    str(run_path),
                    "--output",
                    str(output),
                    "--max-records",
                    "1",
                ],
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            payload = json.loads(output.read_text(encoding="utf-8"))
            validate_atlas(payload)
            self.assertEqual(payload["counts"]["samples"], 1)


if __name__ == "__main__":
    unittest.main()
