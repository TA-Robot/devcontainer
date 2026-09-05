#!/usr/bin/env python3
"""Exercise an actual pre-verification database using archived code and fake providers."""
import importlib.util
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import tarfile
import tempfile

ROOT = Path(__file__).resolve().parents[3]
CURRENT = Path(os.environ.get("AGENTCTL_TEST_BIN", ROOT / "scripts/agentctl"))
ARCHIVE = Path(__file__).with_name("baseline-source.tar.gz")


def main():
    with tempfile.TemporaryDirectory(prefix="agentctl-verification-upgrade-") as directory:
        old = Path(directory)
        with tarfile.open(ARCHIVE) as archive:
            archive.extractall(old)
        spec = importlib.util.spec_from_file_location("old_job_tests", old / "scripts/test-agentctl-jobs.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        fixture = module.AgentctlJobTests("test_project_identity_is_stable_and_job_base_is_immutable")
        fixture.setUp()
        try:
            fixture.extra_environment["MIRA_COMPANION_ENABLED"] = "0"
            job = fixture.create()
            delivered = fixture.invoke("job", "run", job["job_id"], "--provider", "codex", "--json")
            assert delivered.returncode == 0, delivered.stderr
            job = json.loads(delivered.stdout)
            queued = fixture.create("queued.json")
            active = fixture.create("active.json")
            created = fixture.create("created.json")
            # Use the earlier runtime's real preparation/state machine, no supervisor/model.
            prepare = '''import sys
from agentctl_jobs import Store, StatePaths, prepare_attempt
with Store(StatePaths.from_value(sys.argv[1])) as store:
    prepare_attempt(store, sys.argv[2], "codex", queue_if_full=True)
'''
            environment = dict(os.environ, PYTHONPATH=str(old / "scripts"), MIRA_COMPANION_ENABLED="0")
            for identity, capacity in ((queued["job_id"], "0"), (active["job_id"], "2")):
                subprocess.run([sys.executable, "-c", prepare, str(fixture.state_dir), identity],
                               env=dict(environment, AGENTCTL_CAPACITY_WRITE=capacity), check=True,
                               capture_output=True, text=True, timeout=20)
            database = fixture.state_dir / "state.db"
            with sqlite3.connect(database) as connection:
                tables = [r[0] for r in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")]
                assert "command_verifications" not in tables
                assert "verification_tasks" not in tables
                before = {t: connection.execute(f'SELECT * FROM "{t}"').fetchall() for t in tables}
                states = dict(connection.execute("SELECT job_id, state FROM jobs"))
                assert states[queued["job_id"]] == "waiting_capacity", states
                assert states[active["job_id"]] == "ready", states
                assert connection.execute("SELECT COUNT(*) FROM leases WHERE released_at IS NULL").fetchone()[0]
            immutable_task = Path(job["task_path"]).read_bytes()
            result_path = Path(job["attempts"][-1]["result_path"])
            original_result = result_path.read_bytes()
            check_command = fixture.bin_dir / "fake-provider"
            marker = fixture.root / "check-count"
            check_command.write_text(f"#!/bin/sh\nprintf x >> '{marker}'\nprintf 'old job independently checked\\n'\n")
            check_command.chmod(0o755)
            environment["PATH"] = str(fixture.bin_dir) + os.pathsep + os.environ["PATH"]

            def current(*arguments):
                return subprocess.run([sys.executable, str(CURRENT), "--state-dir",
                                       str(fixture.state_dir), *arguments], env=environment,
                                      capture_output=True, text=True, timeout=30)

            for identity in (job["job_id"], queued["job_id"], active["job_id"], created["job_id"]):
                viewed = current("job", "checks", identity, "--json")
                assert viewed.returncode == 0, viewed.stderr
                view = json.loads(viewed.stdout)
                assert view["latest"] is None and not view["fresh"] and view["stale_reasons"], view
            denied = current("job", "validate", job["job_id"], "--require-checks", "--json")
            assert denied.returncode != 0, denied.stdout
            assert not marker.exists()
            with sqlite3.connect(database) as connection:
                after = {t: connection.execute(f'SELECT * FROM "{t}"').fetchall() for t in tables}
                assert after == before, "migration altered existing job/attempt/lease/queue/validation/event rows"
                assert connection.execute("SELECT COUNT(*) FROM command_verifications").fetchone()[0] == 0
                assert connection.execute("SELECT COUNT(*) FROM verification_tasks").fetchone()[0] == 4
            assert Path(job["task_path"]).read_bytes() == immutable_task
            assert result_path.read_bytes() == original_result
            # Repeat reads are a no-op, and additive schema-v2 remains old-client readable.
            shown = fixture.invoke("job", "show", job["job_id"], "--json")
            assert shown.returncode == 0, shown.stderr
            assert json.loads(shown.stdout)["state"] == "succeeded"
            checked = current("job", "check", job["job_id"], "--timeout", "5", "--json")
            assert checked.returncode == 0, checked.stderr
            report = json.loads(checked.stdout)
            assert report["checks"][0]["stdout_tail"] == "old job independently checked\n", report
            view = json.loads(current("job", "checks", job["job_id"], "--json").stdout)
            assert view["fresh"] and view["latest"] == report, view
            sealed = current("job", "validate", job["job_id"], "--require-checks", "--json")
            assert sealed.returncode == 0, sealed.stderr
            assert json.loads(sealed.stdout)["state"] == "validated"
            assert marker.read_text() == "x", "inspection/validation executed the command again"
            assert Path(job["task_path"]).read_bytes() == immutable_task
            assert result_path.read_bytes() == original_result
            print("PASS: actual old database upgraded; jobs/attempts/leases/queue retained, no historic evidence fabricated; explicit check and strict seal passed")
        finally:
            fixture.tearDown()


if __name__ == "__main__":
    main()
