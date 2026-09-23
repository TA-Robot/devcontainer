#!/usr/bin/env python3
"""Create real phase-2 states with its archived runtime; inspect with current CLI."""
import importlib.util
import json
import os
from pathlib import Path
import signal
import sqlite3
import subprocess
import sys
import tarfile
import tempfile
import time

ROOT = Path(__file__).resolve().parents[3]
CURRENT = Path(os.environ.get("AGENTCTL_TEST_BIN", ROOT / "scripts/agentctl"))


def main():
    with tempfile.TemporaryDirectory(prefix="agentctl-phase2-upgrade-") as directory:
        old = Path(directory)
        with tarfile.open(Path(__file__).with_name("phase-2-source.tar.gz")) as archive:
            archive.extractall(old)
        spec = importlib.util.spec_from_file_location("phase2_job_tests", old / "scripts/test-agentctl-jobs.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        fixture = module.AgentctlJobTests("test_checks_persist_pass_and_strict_validation_never_executes")
        fixture.setUp()
        try:
            passed, _ = fixture.check_fixture(["printf phase2-pass"])
            passed_report = fixture.check_report(passed)
            failed, _ = fixture.check_fixture(["exit 7"])
            failed_report = fixture.check_report(failed)
            absent, _ = fixture.check_fixture(["true"])
            gate, marker = fixture.root / "gate", fixture.root / "group"
            gate.touch()
            crashed, _ = fixture.check_fixture([
                f"if test -f '{gate}'; then echo $$ > '{marker}'; sleep 30 & wait; fi"])
            checker = fixture.popen("job", "check", crashed["job_id"], "--json")
            group = None
            try:
                deadline = time.monotonic() + 8
                while (not marker.exists() or not marker.stat().st_size) and time.monotonic() < deadline:
                    time.sleep(0.01)
                assert marker.exists(), "old checker did not launch"
                group = int(marker.read_text())
                checker.kill()
                checker.wait(timeout=3)
            finally:
                if group is not None:
                    os.killpg(group, signal.SIGKILL)
                if checker.poll() is None:
                    checker.kill()
                checker.communicate(timeout=5)
            gate.unlink()
            old_incomplete = fixture.checks_view(crashed)["latest"]
            assert old_incomplete["status"] == "incomplete"
            database = fixture.state_dir / "state.db"

            def rows():
                with sqlite3.connect(database) as connection:
                    tables = [r[0] for r in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")]
                    return {t: connection.execute(f'SELECT * FROM "{t}"').fetchall() for t in tables}

            before = rows()
            artifacts = {p: p.read_bytes() for p in fixture.state_dir.rglob("*.json")}

            def current(*arguments):
                return subprocess.run([sys.executable, str(CURRENT), "--state-dir", str(fixture.state_dir),
                                       *arguments], capture_output=True, text=True, timeout=15,
                                      env=dict(os.environ, MIRA_COMPANION_ENABLED="0"))

            for job, expected in ((passed, passed_report), (failed, failed_report),
                                  (absent, None), (crashed, old_incomplete)):
                result = current("job", "checks", job["job_id"], "--json")
                assert result.returncode == 0, result.stderr
                view = json.loads(result.stdout)
                assert view["latest"] == expected, view
                assert view["in_progress"] is False, view
                assert view["fresh"] == (job in (passed, failed)), view
            for job in (failed, absent, crashed):
                denied = current("job", "validate", job["job_id"], "--require-checks", "--json")
                assert denied.returncode != 0, denied.stdout
            assert rows() == before, "reading/rejecting changed earlier database records"
            assert all(p.read_bytes() == raw for p, raw in artifacts.items())
            # Phase-2 completed evidence remains usable; no historic execution invented.
            sealed = current("job", "validate", passed["job_id"], "--require-checks", "--json")
            assert sealed.returncode == 0, sealed.stderr
            assert json.loads(sealed.stdout)["validation"]["verification_id"] == passed_report["verification_id"]
            old_view = fixture.invoke("job", "show", passed["job_id"], "--json")
            assert json.loads(old_view.stdout)["state"] == "validated"
            denied = current("job", "check", crashed["job_id"], "--json")
            assert denied.returncode != 0 and "--recover-incomplete" in denied.stderr
            recovered = current("job", "check", crashed["job_id"], "--recover-incomplete", "--json")
            assert recovered.returncode == 0, recovered.stderr
            report = json.loads(recovered.stdout)
            assert report["verification_id"] != old_incomplete["verification_id"]
            with sqlite3.connect(database) as connection:
                assert connection.execute("SELECT count(*) FROM command_verifications").fetchone()[0] == 4
                assert connection.execute("SELECT status FROM command_verifications WHERE verification_id = ?",
                                          (old_incomplete["verification_id"],)).fetchone()[0] == "incomplete"
            print("PASS: actual phase-2 passing/failed/absent/interrupted states retained; no fabricated evidence; explicit recovery and strict seal")
        finally:
            fixture.tearDown()


if __name__ == "__main__":
    main()
