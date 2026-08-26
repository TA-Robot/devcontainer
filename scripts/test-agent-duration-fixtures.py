#!/usr/bin/env python3

from __future__ import annotations

import copy
from datetime import datetime, timezone
import json
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parent
CLI = SCRIPT_DIR / "agent-duration-study"
CATALOG_PATH = ROOT / "experiments" / "multi-agent-duration" / "catalog" / "cases.json"
sys.path.insert(0, str(SCRIPT_DIR))

from agent_contracts import load_json  # noqa: E402
from agent_duration_fixtures import (  # noqa: E402
    _install_known_good_for_test,
    build_fixture,
    evaluate_fixture,
    evaluate_fixture_isolated,
)
from agent_duration_study import (  # noqa: E402
    DurationStudyError,
    canonical_json_digest,
    validate_case_catalog_record,
    validate_fixture_record,
)


class AgentDurationFixtureTests(unittest.TestCase):
    def make_fake_docker(self, directory: Path) -> tuple[Path, Path]:
        executable = directory / "fake-docker"
        call_log = directory / "fake-docker.calls"
        program = f'''#!/usr/bin/env python3
import json
from pathlib import Path
import sys

call_log = Path({str(call_log)!r})
with call_log.open("a", encoding="utf-8") as handle:
    handle.write(json.dumps(sys.argv[1:]) + "\\n")
if sys.argv[1:3] == ["image", "inspect"]:
    print("sha256:" + "a" * 64)
elif sys.argv[1:2] in (["run"], ["rm"]):
    raise SystemExit(0)
else:
    raise SystemExit(125)
'''
        executable.write_text(program, encoding="utf-8")
        executable.chmod(0o700)
        return executable, call_log

    def catalog(self) -> dict[str, object]:
        value = load_json(CATALOG_PATH)
        self.assertIsInstance(value, dict)
        return value

    def git(self, workspace: Path, *arguments: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["git", *arguments],
            cwd=workspace,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )

    def test_catalog_is_valid_structural_s_m_l_input(self) -> None:
        catalog = self.catalog()
        validate_case_catalog_record(catalog)
        entries = catalog["entries"]  # type: ignore[index]
        self.assertEqual([entry["case"]["size"] for entry in entries], ["S", "M", "L"])
        self.assertEqual(
            {entry["case"]["family"] for entry in entries},
            {"bounded-implementation"},
        )
        self.assertEqual(
            {entry["fixture"]["isolation_required"] for entry in entries},
            {"workspace-only-container-mount"},
        )
        self.assertRegex(canonical_json_digest(catalog), r"^sha256:[0-9a-f]{64}$")

    def test_catalog_rejects_digest_tampering_and_capsule_escape(self) -> None:
        catalog = self.catalog()
        bad_digest = copy.deepcopy(catalog)
        bad_digest["entries"][0]["case"]["capsule_digest"] = f"sha256:{'0' * 64}"
        with self.assertRaises(DurationStudyError):
            validate_case_catalog_record(bad_digest)

        escaped = copy.deepcopy(catalog)
        escaped["entries"][0]["fixture"]["capsule_path"] = "../gold.md"
        with self.assertRaises(DurationStudyError):
            validate_case_catalog_record(escaped)

        duplicate = copy.deepcopy(catalog)
        duplicate["entries"][1]["case"]["case_id"] = duplicate["entries"][0]["case"][
            "case_id"
        ]
        duplicate["entries"][1]["fixture"]["case_id"] = duplicate["entries"][0]["case"][
            "case_id"
        ]
        with self.assertRaises(DurationStudyError):
            validate_case_catalog_record(duplicate)

    def test_every_fixture_is_isolated_seeded_and_oracle_calibrated(self) -> None:
        catalog = self.catalog()
        fixed_now = datetime(2026, 8, 26, 13, 0, tzinfo=timezone.utc)
        with tempfile.TemporaryDirectory(prefix="duration-fixture-build-") as raw_temp:
            root = Path(raw_temp)
            for entry in catalog["entries"]:  # type: ignore[index]
                case_id = entry["case"]["case_id"]
                with self.subTest(case_id=case_id):
                    fixture_dir = root / case_id.lower()
                    manifest = build_fixture(
                        case_id,
                        fixture_dir,
                        fixture_id=f"fixture-{case_id.lower()}",
                        now=fixed_now,
                    )
                    validate_fixture_record(manifest)
                    self.assertEqual(manifest["initial_oracle"]["observed"], "fail")
                    self.assertEqual(stat.S_IMODE((fixture_dir / "fixture.json").stat().st_mode), 0o600)
                    self.assertEqual(
                        stat.S_IMODE((fixture_dir / "control" / "hidden_tests.py").stat().st_mode),
                        0o600,
                    )

                    workspace = fixture_dir / "workspace"
                    control = fixture_dir / "control"
                    self.assertNotIn(control, [workspace, *workspace.parents])
                    visible_names = {
                        str(path.relative_to(workspace))
                        for path in workspace.rglob("*")
                    }
                    self.assertFalse(
                        any(
                            marker in name.lower()
                            for name in visible_names
                            for marker in ("hidden", "gold", "capsule", "base.bundle")
                        )
                    )
                    self.assertEqual(
                        set(manifest["workspace_files"]),
                        {
                            name
                            for name in visible_names
                            if (workspace / name).is_file() and ".git" not in Path(name).parts
                        },
                    )

                    rev_count = self.git(workspace, "rev-list", "--all", "--count")
                    self.assertEqual((rev_count.returncode, rev_count.stdout.strip()), (0, "1"))
                    self.assertEqual(self.git(workspace, "remote").stdout, "")
                    self.assertEqual(self.git(workspace, "tag").stdout, "")
                    branches = self.git(workspace, "branch", "--format=%(refname:short)")
                    self.assertEqual(branches.stdout.splitlines(), ["main"])
                    self.assertEqual(self.git(workspace, "status", "--porcelain").stdout, "")
                    bundle = self.git(
                        workspace,
                        "bundle",
                        "verify",
                        str(control / "base.bundle"),
                    )
                    self.assertEqual(bundle.returncode, 0, bundle.stdout + bundle.stderr)

                    self.assertEqual(evaluate_fixture(fixture_dir)["status"], "fail")
                    _install_known_good_for_test(case_id, workspace)
                    passed = evaluate_fixture(fixture_dir)
                    self.assertEqual(passed["status"], "pass", passed)
                    self.assertTrue(
                        all(
                            item["status"] == "pass"
                            for item in [*passed["workspace_checks"], passed["hidden_check"]]
                        )
                    )

    def test_fixture_snapshot_is_reproducible(self) -> None:
        fixed_now = datetime(2026, 8, 26, 13, 30, tzinfo=timezone.utc)
        with tempfile.TemporaryDirectory(prefix="duration-fixture-repeat-") as raw_temp:
            root = Path(raw_temp)
            first = build_fixture(
                "F04-S-PY-001",
                root / "first",
                fixture_id="repeat-first",
                now=fixed_now,
            )
            second = build_fixture(
                "F04-S-PY-001",
                root / "second",
                fixture_id="repeat-second",
                now=fixed_now,
            )
            self.assertEqual(first["case"], second["case"])
            self.assertEqual(first["snapshot"], second["snapshot"])
            self.assertEqual(first["workspace_files"], second["workspace_files"])

    def test_fixture_manifest_rejects_oracle_leak_and_tampered_check(self) -> None:
        fixed_now = datetime(2026, 8, 26, 13, 45, tzinfo=timezone.utc)
        with tempfile.TemporaryDirectory(prefix="duration-fixture-contract-") as raw_temp:
            manifest = build_fixture(
                "F04-S-PY-001",
                Path(raw_temp) / "fixture",
                fixture_id="contract-fixture",
                now=fixed_now,
            )
            leaked = copy.deepcopy(manifest)
            leaked["paths"]["hidden_evaluator"] = "workspace/hidden_tests.py"
            with self.assertRaises(DurationStudyError):
                validate_fixture_record(leaked)

            tampered = copy.deepcopy(manifest)
            tampered["initial_oracle"]["hidden_check"]["status"] = "pass"
            with self.assertRaises(DurationStudyError):
                validate_fixture_record(tampered)

    def test_isolated_evaluator_builds_a_bounded_content_free_docker_surface(self) -> None:
        fixed_now = datetime(2026, 8, 26, 13, 50, tzinfo=timezone.utc)
        with tempfile.TemporaryDirectory(prefix="duration-fixture-docker-") as raw_temp:
            root = Path(raw_temp)
            fixture_dir = root / "fixture"
            build_fixture(
                "F04-S-PY-001",
                fixture_dir,
                fixture_id="isolated-fixture",
                now=fixed_now,
            )
            fake_docker, call_log = self.make_fake_docker(root)
            result = evaluate_fixture_isolated(
                fixture_dir,
                image="fixture-evaluator:locked",
                docker_bin=str(fake_docker),
                timeout_seconds=2,
            )
            self.assertEqual(result["status"], "pass")
            self.assertEqual(result["isolation"]["image_digest"], f"sha256:{'a' * 64}")
            self.assertFalse(result["isolation"]["credential_mounts"])
            self.assertFalse(result["isolation"]["control_bundle_mounted"])

            calls = [
                json.loads(line)
                for line in call_log.read_text(encoding="utf-8").splitlines()
            ]
            run_calls = [call for call in calls if call[0] == "run"]
            self.assertEqual(len(run_calls), 2)
            for call in run_calls:
                serialized = json.dumps(call)
                self.assertIn("--network", call)
                self.assertIn("none", call)
                self.assertIn("--read-only", call)
                self.assertIn("--cap-drop", call)
                self.assertIn("no-new-privileges", call)
                self.assertNotIn("base.bundle", serialized)
                self.assertNotRegex(serialized.lower(), r"token|credential|secret")
            self.assertNotIn("/harness/hidden_tests.py", json.dumps(run_calls[0]))
            self.assertIn("/harness/hidden_tests.py", json.dumps(run_calls[1]))

            with self.assertRaises(DurationStudyError):
                evaluate_fixture_isolated(
                    fixture_dir,
                    image="fixture-evaluator:locked",
                    docker_bin=str(fake_docker),
                    timeout_seconds=float("nan"),
                )

    def test_cli_build_validate_evaluate_and_no_overwrite(self) -> None:
        with tempfile.TemporaryDirectory(prefix="duration-fixture-cli-") as raw_temp:
            fixture_dir = Path(raw_temp) / "fixture"
            build = subprocess.run(
                [
                    str(CLI),
                    "build-fixture",
                    "--case-id",
                    "F04-S-PY-001",
                    "--fixture-id",
                    "cli-fixture-s",
                    "--output-dir",
                    str(fixture_dir),
                ],
                cwd=ROOT,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )
            self.assertEqual(build.returncode, 0, build.stdout + build.stderr)
            self.assertEqual(json.loads(build.stdout)["initial_oracle"], "fail")

            validate_manifest = subprocess.run(
                [
                    str(CLI),
                    "validate",
                    "--kind",
                    "fixture",
                    str(fixture_dir / "fixture.json"),
                ],
                cwd=ROOT,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )
            self.assertEqual(
                validate_manifest.returncode,
                0,
                validate_manifest.stdout + validate_manifest.stderr,
            )

            refused_oracle = subprocess.run(
                [str(CLI), "evaluate-fixture", str(fixture_dir)],
                cwd=ROOT,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )
            self.assertEqual(refused_oracle.returncode, 2)
            self.assertIn("live artifacts require", refused_oracle.stderr)

            failed_oracle = subprocess.run(
                [
                    str(CLI),
                    "evaluate-fixture",
                    str(fixture_dir),
                    "--trusted-calibration",
                ],
                cwd=ROOT,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )
            self.assertEqual(failed_oracle.returncode, 1)
            self.assertEqual(json.loads(failed_oracle.stdout)["status"], "fail")

            repeated = subprocess.run(
                [
                    str(CLI),
                    "build-fixture",
                    "--case-id",
                    "F04-S-PY-001",
                    "--fixture-id",
                    "cli-fixture-s",
                    "--output-dir",
                    str(fixture_dir),
                ],
                cwd=ROOT,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )
            self.assertEqual(repeated.returncode, 2)
            self.assertIn("refusing to overwrite fixture directory", repeated.stderr)


if __name__ == "__main__":
    unittest.main()
