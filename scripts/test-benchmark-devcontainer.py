#!/usr/bin/env python3

from __future__ import annotations

import importlib.util
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock
import subprocess


ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "benchmark-devcontainer.py"
SPEC = importlib.util.spec_from_file_location("benchmark_devcontainer", SCRIPT)
assert SPEC and SPEC.loader
benchmark = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = benchmark
SPEC.loader.exec_module(benchmark)


class BenchmarkDevcontainerTests(unittest.TestCase):
    def test_transient_probe_timeout_retries_without_restarting_container(self) -> None:
        ready = subprocess.CompletedProcess([], 0, '29.0\n', '')
        with mock.patch.object(benchmark, 'run', side_effect=[
                benchmark.BenchmarkCommandTimeout('temporary timeout'), ready]) as run, \
                mock.patch.object(benchmark.time, 'sleep'):
            self.assertEqual(benchmark.wait_for_nested_docker('docker', 'owned', 30), '29.0')
        self.assertEqual(run.call_count, 2)
        for call in run.call_args_list:
            self.assertEqual(call.args[0][:3], ['docker', 'exec', 'owned'])

    def test_probe_and_sleep_share_one_deadline(self) -> None:
        clock = [0.0]
        timeouts = []
        def timed_out(argv, *, timeout):
            timeouts.append(timeout)
            clock[0] += timeout
            raise benchmark.BenchmarkCommandTimeout('probe still blocked')
        def sleep(seconds):
            clock[0] += seconds
        with mock.patch.object(benchmark.time, 'monotonic', side_effect=lambda: clock[0]), \
                mock.patch.object(benchmark.time, 'sleep', side_effect=sleep), \
                mock.patch.object(benchmark, 'run', side_effect=timed_out):
            with self.assertRaisesRegex(benchmark.BenchmarkContainerError, 'probe still blocked'):
                benchmark.wait_for_nested_docker('docker', 'owned', 6)
        self.assertEqual(timeouts, [5, 0.5])
        self.assertEqual(clock[0], 6)

    def test_short_deadline_never_starts_five_second_probe(self) -> None:
        clock = [0.0]
        def timed_out(argv, *, timeout):
            self.assertEqual(timeout, 0.2)
            clock[0] += timeout
            raise benchmark.BenchmarkCommandTimeout('short deadline')
        with mock.patch.object(benchmark.time, 'monotonic', side_effect=lambda: clock[0]), \
                mock.patch.object(benchmark.time, 'sleep'), \
                mock.patch.object(benchmark, 'run', side_effect=timed_out) as run:
            with self.assertRaises(benchmark.BenchmarkContainerError):
                benchmark.wait_for_nested_docker('docker', 'owned', 0.2)
        self.assertEqual(run.call_count, 1)

    def test_nonzero_and_empty_success_are_not_readiness(self) -> None:
        results = [subprocess.CompletedProcess([], 1, '', 'starting'),
                   subprocess.CompletedProcess([], 0, '  ', ''),
                   subprocess.CompletedProcess([], 0, '29.0', '')]
        with mock.patch.object(benchmark, 'run', side_effect=results) as run, \
                mock.patch.object(benchmark.time, 'sleep'):
            self.assertEqual(benchmark.wait_for_nested_docker('docker', 'owned', 30), '29.0')
        self.assertEqual(run.call_count, 3)

    def test_missing_docker_is_not_retried_as_temporary_timeout(self) -> None:
        with mock.patch.object(benchmark, 'run', side_effect=benchmark.BenchmarkContainerError('missing docker')) as run:
            with self.assertRaisesRegex(benchmark.BenchmarkContainerError, 'missing docker'):
                benchmark.wait_for_nested_docker('docker', 'owned', 30)
        self.assertEqual(run.call_count, 1)

    def test_command_timeout_keeps_distinct_type_and_original_cause(self) -> None:
        cause = subprocess.TimeoutExpired(['docker'], 0.2)
        with mock.patch.object(benchmark.subprocess, 'run', side_effect=cause):
            with self.assertRaises(benchmark.BenchmarkCommandTimeout) as raised:
                benchmark.run(['docker'], timeout=0.2)
        self.assertIs(raised.exception.__cause__, cause)

    def test_start_command_isolated_nested_docker_and_forwards_no_secret_value(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            workspace = root / "workspace"
            home = root / "home"
            workspace.mkdir()
            home.mkdir()
            (home / ".codex").mkdir()
            (home / ".gitconfig").write_text("[user]\n", encoding="utf-8")
            secret = "must-not-appear-in-command"
            command = benchmark.build_start_command(
                docker="docker-fixture",
                name="benchmark-02",
                workspace=workspace,
                image="fixture:latest",
                host_home=home,
                environment={"OPENAI_API_KEY": secret},
            )
        rendered = " ".join(command)
        self.assertIn("type=volume,src=benchmark-02-docker,dst=/var/lib/docker", command)
        self.assertIn("type=volume,src=benchmark-02-agentctl,dst=/var/lib/agentctl", command)
        self.assertIn("type=volume,src=benchmark-02-mira,dst=/var/lib/mira-observations", command)
        self.assertIn("OPENAI_API_KEY", command)
        self.assertNotIn(secret, rendered)
        self.assertIn("readonly", rendered)

    def test_invalid_or_broad_names_are_rejected(self) -> None:
        for name in ("", ".hidden", "with/slash", "x" * 64):
            with self.subTest(name=name), self.assertRaises(benchmark.BenchmarkContainerError):
                benchmark.require_name(name)

    def test_missing_workspace_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(benchmark.BenchmarkContainerError):
                benchmark.require_workspace(Path(directory) / "missing")

    def test_stale_image_without_auth_contract_is_not_ready(self) -> None:
        summary = benchmark.summarize_doctor_payload(
            {
                "ok": True,
                "checks": [],
                "capabilities": {
                    "codex": {"available": True},
                    "claude": {"available": True},
                    "grok": {"available": True},
                },
            },
            0,
        )
        self.assertFalse(summary["ok"])
        self.assertFalse(summary["auth_contract_ready"])
        self.assertIn("provider.auth-contract", summary["failed_checks"])

    def test_target_project_without_devcontainer_lock_is_still_ready(self) -> None:
        summary = benchmark.summarize_doctor_payload(
            {
                "ok": False,
                "checks": [
                    {
                        "id": "toolchain.feature_lock",
                        "status": "fail",
                        "summary": "Dev Container Feature lockfile is missing",
                    }
                ],
                "capabilities": {
                    provider: {"auth": {"ready": True}}
                    for provider in ("codex", "claude", "grok")
                },
            },
            1,
        )
        self.assertTrue(summary["ok"])
        self.assertEqual(summary["failed_checks"], [])
        self.assertEqual(summary["not_applicable_checks"], ["toolchain.feature_lock"])

    def test_feature_lock_mismatch_remains_a_failure(self) -> None:
        summary = benchmark.summarize_doctor_payload(
            {
                "ok": False,
                "checks": [
                    {
                        "id": "toolchain.feature_lock",
                        "status": "fail",
                        "summary": "Dev Container Feature lock does not match",
                    }
                ],
                "capabilities": {
                    provider: {"auth": {"ready": True}}
                    for provider in ("codex", "claude", "grok")
                },
            },
            1,
        )
        self.assertFalse(summary["ok"])
        self.assertEqual(summary["failed_checks"], ["toolchain.feature_lock"])


if __name__ == "__main__":
    unittest.main()
