#!/usr/bin/env python3

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import unittest


ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts/benchmark-isolated-runtime-pilot.py"
SPEC = importlib.util.spec_from_file_location("isolated_runtime_benchmark", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
benchmark = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = benchmark
SPEC.loader.exec_module(benchmark)


class IsolatedRuntimeBenchmarkTests(unittest.TestCase):
    def test_percentile_and_summary_keep_failed_samples(self) -> None:
        self.assertEqual(benchmark.percentile([30.0, 10.0, 20.0], 0.5), 20.0)
        summary = benchmark.summarize_samples(
            [
                {
                    "status": "passed",
                    "daemon_ready_ms": 10.0,
                    "clone_ready_ms": 20.0,
                    "completion_ms": 30.0,
                    "teardown_ms": 5.0,
                    "docker_state_bytes": 100,
                    "container_writable_layer_bytes": 200,
                    "evidence_bytes": 300,
                },
                {"status": "failed", "error": "fixture"},
            ]
        )
        self.assertEqual(summary["status"], "failed")
        self.assertEqual(summary["passed"], 1)
        self.assertEqual(summary["failed"], 1)
        self.assertEqual(len(summary["samples"]), 2)

    def test_docker_agent_probe_uses_plugin_inventory_not_unknown_command_help(self) -> None:
        missing = benchmark.probe_docker_agent({"plugins": []})
        self.assertEqual(missing["status"], "unavailable")

        present = benchmark.probe_docker_agent(
            {
                "plugins": [
                    {
                        "Name": "agent",
                        "Version": "v1.2.3",
                        "Path": "/fixture/docker-agent",
                    }
                ]
            }
        )
        self.assertEqual(present["status"], "available_unmeasured")
        self.assertFalse(present["model_request_performed"])

    def test_fixture_uses_narrow_bundle_transport_and_scoped_cleanup(self) -> None:
        fixture = benchmark.PRIVATE_DIND_FIXTURE
        self.assertIn("/run/agentctl/input.bundle", fixture)
        self.assertIn("result.bundle", fixture)
        self.assertIn("dev.agentctl.benchmark=true", fixture)
        self.assertNotIn("docker system prune", fixture)
        self.assertNotIn("/workspace", fixture)

    def test_probe_only_cli_never_runs_a_runtime(self) -> None:
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "--probe-only", "--repetitions", "1"],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["candidates"]["private_dind"]["status"], "not_run")
        self.assertIn(
            payload["candidates"]["docker_sandboxes"]["status"],
            {"unavailable", "available_unmeasured", "unhealthy"},
        )
        self.assertFalse(payload["decision"]["stable_isolated_adapter_enabled"])


if __name__ == "__main__":
    unittest.main()
