#!/usr/bin/env python3

from __future__ import annotations

import importlib.util
import os
from pathlib import Path
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "benchmark-devcontainer.py"
SPEC = importlib.util.spec_from_file_location("benchmark_devcontainer", SCRIPT)
assert SPEC and SPEC.loader
benchmark = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = benchmark
SPEC.loader.exec_module(benchmark)


class BenchmarkDevcontainerTests(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()
