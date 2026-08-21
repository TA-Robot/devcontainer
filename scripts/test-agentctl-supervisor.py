#!/usr/bin/env python3

from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import signal
import sqlite3
import subprocess
import sys
import tempfile
import time
import unittest


ROOT = Path(__file__).resolve().parent.parent
AGENTCTL = ROOT / "scripts/agentctl"


FAKE_CODEX = r'''#!/usr/bin/env python3
import json
import os
from pathlib import Path
import subprocess
import sys
import time

mode = os.environ.get("FAKE_PROVIDER_MODE", "success")
if mode == "hang":
    time.sleep(60)
elif mode == "slow":
    time.sleep(0.7)

workspace = Path.cwd()
job_id = os.environ["AGENTCTL_JOB_ID"]
(workspace / "result.txt").write_text(
    f"job={job_id}\n"
    f"memory={os.environ.get('GROK_MEMORY', '')}\n",
    encoding="utf-8",
)
head = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
result = {
    "schema_version": 1,
    "job_id": job_id,
    "status": "ready_for_commit",
    "summary": "Detached synthetic provider result.",
    "head_sha": head,
    "changed_paths": ["result.txt"],
    "dirty_state": {"is_dirty": True, "paths": ["result.txt"]},
    "checks": [{
        "command": "fake-provider",
        "status": "passed",
        "exit_code": 0,
        "summary": "Synthetic check passed."
    }],
    "risks": [],
    "followups": []
}
arguments = sys.argv[1:]
if Path(sys.argv[0]).name == "fake-grok":
    print(json.dumps({"structuredOutput": result, "argv": arguments}))
else:
    index = arguments.index("--output-last-message")
    Path(arguments[index + 1]).write_text(json.dumps(result), encoding="utf-8")
    print(json.dumps({"argv": arguments}))
'''


def process_marker(pid: int) -> str | None:
    try:
        raw = Path(f"/proc/{pid}/stat").read_text(encoding="utf-8")
        fields = raw[raw.rfind(")") + 1 :].split()
        if fields[0] == "Z":
            return None
        return fields[19]
    except (OSError, IndexError):
        return None


def wait_process_gone(pid: int, marker: str, timeout: float = 5.0) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if process_marker(pid) != marker:
            return True
        time.sleep(0.05)
    return process_marker(pid) != marker


class AgentctlSupervisorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(prefix="agentctl-supervisor-")
        self.root = Path(self.temp.name)
        self.workspace = self.root / "workspace"
        self.workspace.mkdir()
        subprocess.run(["git", "init", "-q", str(self.workspace)], check=True)
        subprocess.run(
            ["git", "-C", str(self.workspace), "config", "user.email", "test@example.invalid"],
            check=True,
        )
        subprocess.run(
            ["git", "-C", str(self.workspace), "config", "user.name", "test"],
            check=True,
        )
        shutil.copytree(ROOT / "project/.agent", self.workspace / ".agent")
        shutil.copytree(ROOT / "project/.codex", self.workspace / ".codex")
        shutil.copy2(ROOT / "project/AGENTS.md", self.workspace / "AGENTS.md")
        (self.workspace / "tracked.txt").write_text("base\n", encoding="utf-8")
        subprocess.run(["git", "-C", str(self.workspace), "add", "."], check=True)
        subprocess.run(["git", "-C", str(self.workspace), "commit", "-qm", "base"], check=True)

        self.state_dir = self.root / "state"
        self.provider = self.root / "fake-codex"
        self.provider.write_text(FAKE_CODEX, encoding="utf-8")
        self.provider.chmod(0o755)
        self.grok = self.root / "fake-grok"
        self.grok.write_text(FAKE_CODEX, encoding="utf-8")
        self.grok.chmod(0o755)
        self.jobs: list[str] = []
        self.capacity_write = "2"
        self.capacity_integration = "1"

    def tearDown(self) -> None:
        for job_id in self.jobs:
            self.invoke("job", "cancel", job_id, mode="hang")
        socket_path = self.state_dir / "agentd.sock"
        if socket_path.exists():
            self.invoke("supervisor", "stop", mode="hang")
            deadline = time.monotonic() + 5
            while socket_path.exists() and time.monotonic() < deadline:
                time.sleep(0.05)
        self.temp.cleanup()

    def environment(self, mode: str) -> dict[str, str]:
        environment = os.environ.copy()
        environment.update(
            {
                "AGENTCTL_CODEX_BIN": str(self.provider),
                "AGENTCTL_CODEX_TRUSTED_BIN": str(self.provider),
                "AGENTCTL_GROK_BIN": str(self.grok),
                "AGENTCTL_GROK_TRUSTED_BIN": str(self.grok),
                "FAKE_PROVIDER_MODE": mode,
                "AGENTCTL_HEARTBEAT_SECONDS": "0.1",
                "AGENTCTL_ORPHAN_AFTER_SECONDS": "0.4",
                "AGENTCTL_CAPACITY_WRITE": self.capacity_write,
                "AGENTCTL_CAPACITY_INTEGRATION": self.capacity_integration,
                "MIRA_COMPANION_ENABLED": "0",
            }
        )
        return environment

    def invoke(self, *arguments: str, mode: str = "success") -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [
                sys.executable,
                str(AGENTCTL),
                "--state-dir",
                str(self.state_dir),
                *arguments,
            ],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=self.environment(mode),
            check=False,
            timeout=20,
        )

    def create(
        self,
        name: str,
        *,
        permission_profile: str = "safe",
        priority: str = "normal",
        resource_class: str = "write",
    ) -> str:
        task = {
            "schema_version": 1,
            "objective": "Create one deterministic detached result file.",
            "role": "implementer",
            "lane": "write",
            "permission_profile": permission_profile,
            "resource_class": resource_class,
            "priority": priority,
            "scope": {
                "allowed_paths": ["result.txt"],
                "forbidden_paths": [".devcontainer/"],
            },
            "acceptance": [{"kind": "command", "value": "fake-provider"}],
            "constraints": ["Do not push or merge."],
            "dependency_job_ids": [],
        }
        task_path = self.workspace / name
        task_path.write_text(json.dumps(task), encoding="utf-8")
        created = self.invoke(
            "job",
            "create",
            "--workspace",
            str(self.workspace),
            "--task",
            str(task_path),
            "--base",
            "HEAD",
            "--json",
        )
        self.assertEqual(created.returncode, 0, created.stdout + created.stderr)
        job_id = str(json.loads(created.stdout)["job_id"])
        self.jobs.append(job_id)
        return job_id

    def show(self, job_id: str) -> dict[str, object]:
        result = self.invoke("job", "show", job_id, "--json")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        return json.loads(result.stdout)

    def wait_state(self, job_id: str, expected: set[str], timeout: float = 10) -> dict[str, object]:
        deadline = time.monotonic() + timeout
        latest: dict[str, object] = {}
        while time.monotonic() < deadline:
            latest = self.show(job_id)
            if latest["state"] in expected:
                return latest
            time.sleep(0.05)
        self.fail(f"job did not reach {expected}: {latest}")

    def wait_running_identity(self, job_id: str, timeout: float = 10) -> dict[str, object]:
        deadline = time.monotonic() + timeout
        latest: dict[str, object] = {}
        while time.monotonic() < deadline:
            latest = self.show(job_id)
            attempts = latest.get("attempts", [])
            if (
                latest.get("state") == "running"
                and attempts
                and attempts[0].get("pid") is not None
                and attempts[0].get("process_started_at")
            ):
                return latest
            time.sleep(0.05)
        self.fail(f"job did not record a running process identity: {latest}")

    def test_detached_runner_survives_dispatch_client_and_heartbeats(self) -> None:
        job_id = self.create("detached.json")
        submitted = self.invoke(
            "job", "run", job_id, "--provider", "codex", "--detach", "--json", mode="slow"
        )
        self.assertEqual(submitted.returncode, 0, submitted.stdout + submitted.stderr)
        accepted = json.loads(submitted.stdout)
        self.assertEqual(accepted["state"], "accepted")
        self.assertRegex(accepted["runtime_id"], r"^runner:\d+:\d+$")

        completed = self.wait_state(job_id, {"succeeded"})
        attempt = completed["attempts"][0]
        self.assertEqual(attempt["state"], "succeeded")
        self.assertGreater(attempt["heartbeat_at"], attempt["started_at"])
        self.assertEqual((self.state_dir / "agentd.sock").stat().st_mode & 0o777, 0o600)
        self.assertEqual((self.state_dir / "agentd.json").stat().st_mode & 0o777, 0o600)
        self.assertEqual(Path(attempt["log_path"]).with_name("runner.log").stat().st_mode & 0o777, 0o600)

    def test_detached_grok_uses_the_same_supervised_execution_path(self) -> None:
        job_id = self.create("detached-grok.json")
        submitted = self.invoke(
            "job",
            "run",
            job_id,
            "--provider",
            "grok",
            "--detach",
            "--json",
            mode="slow",
        )
        self.assertEqual(submitted.returncode, 0, submitted.stdout + submitted.stderr)
        self.assertEqual(json.loads(submitted.stdout)["state"], "accepted")

        completed = self.wait_state(job_id, {"succeeded"})
        attempt = completed["attempts"][0]
        self.assertEqual(attempt["provider"], "grok")
        provider_log = json.loads(Path(attempt["log_path"]).read_text(encoding="utf-8"))
        arguments = provider_log["argv"]
        self.assertIn("--prompt-file", arguments)
        self.assertIn("/dev/stdin", arguments)
        self.assertIn("--no-subagents", arguments)
        self.assertIn("dontAsk", arguments)
        self.assertIn(
            "memory=0",
            (Path(attempt["workspace_path"]) / "result.txt").read_text(encoding="utf-8"),
        )

    def test_cancel_terminates_recorded_process_group(self) -> None:
        job_id = self.create("cancel.json")
        submitted = self.invoke(
            "job", "run", job_id, "--provider", "codex", "--detach", mode="hang"
        )
        self.assertEqual(submitted.returncode, 0, submitted.stdout + submitted.stderr)
        running = self.wait_running_identity(job_id)
        attempt = running["attempts"][0]
        provider_pid = int(attempt["pid"])
        provider_marker = str(attempt["process_started_at"])

        cancelled = self.invoke("job", "cancel", job_id, "--json", mode="hang")
        self.assertEqual(cancelled.returncode, 0, cancelled.stdout + cancelled.stderr)
        payload = json.loads(cancelled.stdout)
        self.assertEqual(payload["state"], "cancelled")
        self.assertEqual(payload["attempts"][0]["exit_reason"], "cancel_requested")
        self.assertTrue(wait_process_gone(provider_pid, provider_marker))
        process_leases = [lease for lease in payload["leases"] if lease["kind"] == "process"]
        self.assertTrue(process_leases)
        self.assertTrue(all(lease["released_at"] for lease in process_leases))
        retention = Path(attempt["log_path"]).with_name("log-retention.json")
        self.assertTrue(retention.is_file())

    def test_restart_reconciliation_marks_lost_execution_orphaned(self) -> None:
        job_id = self.create("orphan.json")
        submitted = self.invoke(
            "job", "run", job_id, "--provider", "codex", "--detach", mode="hang"
        )
        self.assertEqual(submitted.returncode, 0, submitted.stdout + submitted.stderr)
        running = self.wait_running_identity(job_id)
        attempt = running["attempts"][0]
        provider_pid = int(attempt["pid"])
        runtime_parts = str(attempt["runtime_id"]).split(":", 2)
        runner_pid = int(runtime_parts[1])

        status = self.invoke("supervisor", "status", "--json", mode="hang")
        supervisor_pid = int(json.loads(status.stdout)["pid"])
        supervisor_marker = process_marker(supervisor_pid)
        stopped = self.invoke("supervisor", "stop", mode="hang")
        self.assertEqual(stopped.returncode, 0, stopped.stdout + stopped.stderr)
        self.assertIsNotNone(supervisor_marker)
        self.assertTrue(wait_process_gone(supervisor_pid, str(supervisor_marker)))

        for pid in (runner_pid, provider_pid):
            try:
                os.killpg(pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
        time.sleep(0.6)

        reconciled = self.invoke("supervisor", "reconcile", "--json", mode="hang")
        self.assertEqual(reconciled.returncode, 0, reconciled.stdout + reconciled.stderr)
        orphaned = self.wait_state(job_id, {"orphaned"})
        self.assertEqual(orphaned["attempts"][0]["state"], "orphaned")
        self.assertEqual(orphaned["attempts"][0]["exit_reason"], "orphaned")
        retention = Path(attempt["log_path"]).with_name("log-retention.json")
        self.assertTrue(retention.is_file())

    def test_detached_dispatch_is_single_attempt_and_preserves_trusted_gate(self) -> None:
        job_id = self.create("single-dispatch.json")
        first = self.invoke(
            "job", "run", job_id, "--provider", "codex", "--detach", mode="hang"
        )
        self.assertEqual(first.returncode, 0, first.stdout + first.stderr)
        duplicate = self.invoke(
            "job", "run", job_id, "--provider", "codex", "--detach", mode="hang"
        )
        self.assertEqual(duplicate.returncode, 2)
        self.assertEqual(len(self.show(job_id)["attempts"]), 1)
        self.invoke("job", "cancel", job_id, mode="hang")

        trusted_id = self.create("trusted-detached.json", permission_profile="trusted-fast")
        denied = self.invoke(
            "job", "run", trusted_id, "--provider", "codex", "--detach"
        )
        self.assertEqual(denied.returncode, 2)
        self.assertIn("--allow-trusted-fast", denied.stderr)
        self.assertEqual(self.show(trusted_id)["attempts"], [])
        allowed = self.invoke(
            "job",
            "run",
            trusted_id,
            "--provider",
            "codex",
            "--detach",
            "--allow-trusted-fast",
        )
        self.assertEqual(allowed.returncode, 0, allowed.stdout + allowed.stderr)
        self.wait_state(trusted_id, {"succeeded"})

    def test_capacity_queue_promotes_after_the_active_lease_is_released(self) -> None:
        self.capacity_write = "1"
        active_id = self.create("capacity-active.json")
        queued_id = self.create("capacity-queued.json")

        active = self.invoke(
            "job", "run", active_id, "--provider", "codex", "--detach", mode="hang"
        )
        self.assertEqual(active.returncode, 0, active.stdout + active.stderr)
        self.wait_running_identity(active_id)

        queued = self.invoke(
            "job", "run", queued_id, "--provider", "codex", "--detach", "--json"
        )
        self.assertEqual(queued.returncode, 0, queued.stdout + queued.stderr)
        queue_result = json.loads(queued.stdout)
        self.assertEqual(queue_result["state"], "waiting_capacity")
        self.assertEqual(queue_result["queue"]["position"], 1)
        waiting = self.show(queued_id)
        self.assertEqual(waiting["state"], "waiting_capacity")
        self.assertEqual(waiting["attempts"], [])

        cancelled = self.invoke("job", "cancel", active_id, mode="hang")
        self.assertEqual(cancelled.returncode, 0, cancelled.stdout + cancelled.stderr)
        completed = self.wait_state(queued_id, {"succeeded"})
        self.assertEqual(len(completed["attempts"]), 1)
        capacity_leases = [
            lease for lease in completed["leases"] if lease["kind"] == "capacity"
        ]
        self.assertEqual(len(capacity_leases), 1)
        self.assertIsNotNone(capacity_leases[0]["released_at"])

    def test_priority_reorders_capacity_queue(self) -> None:
        self.capacity_write = "1"
        active_id = self.create("priority-active.json")
        background_id = self.create("priority-background.json", priority="background")
        interactive_id = self.create("priority-interactive.json", priority="interactive")

        self.assertEqual(
            self.invoke(
                "job", "run", active_id, "--provider", "codex", "--detach", mode="hang"
            ).returncode,
            0,
        )
        self.wait_running_identity(active_id)
        for job_id in (background_id, interactive_id):
            submitted = self.invoke(
                "job", "run", job_id, "--provider", "codex", "--detach", mode="hang"
            )
            self.assertEqual(submitted.returncode, 0, submitted.stdout + submitted.stderr)

        self.assertEqual(self.show(interactive_id)["queue"]["position"], 1)
        self.assertEqual(self.show(background_id)["queue"]["position"], 2)
        self.assertEqual(self.invoke("job", "cancel", active_id, mode="hang").returncode, 0)
        self.wait_running_identity(interactive_id)
        self.assertEqual(self.show(background_id)["state"], "waiting_capacity")
        self.assertEqual(
            self.invoke("job", "cancel", interactive_id, mode="hang").returncode, 0
        )
        self.wait_running_identity(background_id)

    def test_aging_promotes_an_old_background_job(self) -> None:
        self.capacity_write = "0"
        background_id = self.create("aging-background.json", priority="background")
        interactive_id = self.create("aging-interactive.json", priority="interactive")
        for job_id in (background_id, interactive_id):
            submitted = self.invoke(
                "job", "run", job_id, "--provider", "codex", "--detach", mode="hang"
            )
            self.assertEqual(submitted.returncode, 0, submitted.stdout + submitted.stderr)
        self.assertEqual(self.show(interactive_id)["queue"]["position"], 1)

        with sqlite3.connect(self.state_dir / "state.db") as connection:
            connection.execute(
                "UPDATE jobs SET queued_at = ? WHERE job_id = ?",
                ("2000-01-01T00:00:00.000Z", background_id),
            )
        aged = self.show(background_id)
        self.assertEqual(aged["queue"]["effective_priority"], "interactive")
        self.assertEqual(aged["queue"]["position"], 1)

    def test_durable_queue_requires_safe_resubmit_after_supervisor_restart(self) -> None:
        self.capacity_write = "0"
        job_id = self.create("restart-queued.json")
        queued = self.invoke(
            "job", "run", job_id, "--provider", "codex", "--detach", "--json"
        )
        self.assertEqual(queued.returncode, 0, queued.stdout + queued.stderr)
        self.assertEqual(json.loads(queued.stdout)["state"], "waiting_capacity")
        stopped = self.invoke("supervisor", "stop")
        self.assertEqual(stopped.returncode, 0, stopped.stdout + stopped.stderr)
        deadline = time.monotonic() + 5
        while (self.state_dir / "agentd.sock").exists() and time.monotonic() < deadline:
            time.sleep(0.05)

        self.capacity_write = "1"
        restarted = self.invoke("supervisor", "status", "--json")
        self.assertEqual(restarted.returncode, 0, restarted.stdout + restarted.stderr)
        status = json.loads(restarted.stdout)
        self.assertIn(job_id, status["awaiting_resubmit"])
        self.assertEqual(self.show(job_id)["state"], "waiting_capacity")

        resubmitted = self.invoke(
            "job", "run", job_id, "--provider", "codex", "--detach", "--json"
        )
        self.assertEqual(resubmitted.returncode, 0, resubmitted.stdout + resubmitted.stderr)
        self.assertEqual(json.loads(resubmitted.stdout)["state"], "accepted")
        self.wait_state(job_id, {"succeeded"})

    def test_queued_job_can_be_cancelled_without_creating_an_attempt(self) -> None:
        self.capacity_write = "0"
        job_id = self.create("cancel-queued.json")
        submitted = self.invoke(
            "job", "run", job_id, "--provider", "codex", "--detach", "--json"
        )
        self.assertEqual(submitted.returncode, 0, submitted.stdout + submitted.stderr)
        self.assertEqual(json.loads(submitted.stdout)["state"], "waiting_capacity")
        cancelled = self.invoke("job", "cancel", job_id, "--json")
        self.assertEqual(cancelled.returncode, 0, cancelled.stdout + cancelled.stderr)
        payload = json.loads(cancelled.stdout)
        self.assertEqual(payload["state"], "cancelled")
        self.assertEqual(payload["attempts"], [])

    def test_concurrent_integration_jobs_receive_distinct_capacity_and_ports(self) -> None:
        self.capacity_integration = "2"
        job_ids = [
            self.create(f"integration-{index}.json", resource_class="integration")
            for index in range(2)
        ]
        for job_id in job_ids:
            submitted = self.invoke(
                "job", "run", job_id, "--provider", "codex", "--detach", mode="hang"
            )
            self.assertEqual(submitted.returncode, 0, submitted.stdout + submitted.stderr)
        running = [self.wait_running_identity(job_id) for job_id in job_ids]
        active_ports = []
        capacity_values = []
        for payload in running:
            active_ports.extend(
                lease["value"]
                for lease in payload["leases"]
                if lease["kind"] == "port" and lease["released_at"] is None
            )
            capacity_values.extend(
                lease["value"]
                for lease in payload["leases"]
                if lease["kind"] == "capacity" and lease["released_at"] is None
            )
        self.assertEqual(len(set(active_ports)), 2)
        self.assertEqual(set(capacity_values), {"integration:1", "integration:2"})


if __name__ == "__main__":
    unittest.main()
