"""Draft core execution probe; this is not the full sustained-task evaluator."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shlex
import subprocess
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
from fixture import Fixture


def require(value, message):
    if not value:
        raise AssertionError(message)


def report(result, fixture, commands):
    try:
        value = json.loads(result.stdout)
    except (ValueError, TypeError):
        raise AssertionError("required checker did not return a JSON observation")
    require(isinstance(value, dict), "checker observation is not an object")
    require(value.get("schema_version") == 1, "unsupported observation schema")
    require(value.get("job_id") == fixture.job["job_id"], "wrong job observed")
    require(value.get("attempt_id") == fixture.attempt["attempt_id"], "wrong attempt observed")
    checks = value.get("checks")
    require(isinstance(checks, list), "command observations missing")
    require(all(isinstance(c, dict) for c in checks), "invalid command observation")
    require([c.get("command") for c in checks] == commands, "original command order changed")
    return value


def observe_case(fixture, case, checker=None):
    """Assert effects independently of the candidate's success message."""
    first = fixture.root / "original-command-witness"
    extra = fixture.root / "result-only-witness"
    later = fixture.root / "later-command-witness"
    write = lambda path: "printf executed > " + shlex.quote(str(path))
    if case == "actual-success":
        commands = [write(first)]
        reported = []
    elif case == "false-success-and-stop":
        commands = [write(first) + "; exit 17", write(later)]
        reported = []
    elif case == "original-task-authority":
        commands = [write(first)]
        reported = [write(extra)]
    elif case == "manual-is-not-command-proof":
        commands, reported = [], []
    else:
        raise ValueError(case)
    fixture.create(commands, extra_reported=reported)
    require(not any(p.exists() for p in (first, extra, later)), "setup already executed checks")
    before = fixture.counter.read_text()
    invoke = checker or (lambda f, _: f.check())
    result = invoke(fixture, commands)
    require(fixture.counter.read_text() == before, "independent checking invoked a provider")
    value = report(result, fixture, commands)
    if case == "manual-is-not-command-proof":
        require(result.returncode != 0 and value.get("status") == "no-checks",
                "manual-only task became independent command success")
    else:
        require(first.is_file() and first.read_text() == "executed", "original command did not execute")
        if case == "false-success-and-stop":
            require(result.returncode != 0 and value.get("status") == "failed",
                    "a provider's false success overrode actual failure")
            require(value["checks"][0].get("exit_code") == 17, "actual exit code was not observed")
            require(not later.exists(), "sequence continued after a failed command")
            require(value["checks"][1].get("exit_code") is None,
                    "unexecuted later command has a fabricated exit code")
        else:
            require(result.returncode == 0 and value.get("status") == "passed",
                    "successful unchanged delivery was not accepted")
            require(value["checks"][0].get("exit_code") == 0, "actual success was not observed")
    require(not extra.exists(), "a command supplied only by the provider result executed")


CASES = (
    "actual-success", "false-success-and-stop", "original-task-authority",
    "manual-is-not-command-proof",
)


def evaluate(candidate, template):
    def hashes():
        return {str(p.relative_to(candidate)): hashlib.sha256(p.read_bytes()).hexdigest()
                for p in sorted((candidate / "scripts").rglob("*")) if p.is_file()}
    before = hashes()
    observations = []
    for case in CASES:
        fixture = None
        try:
            fixture = Fixture(candidate, template)
            # Fixture setup failures must not count as candidate rejection.
            try:
                observe_case(fixture, case)
                status, detail = "passed", None
            except AssertionError as error:
                if str(error).startswith("fixture CLI failed:"):
                    status, detail = "unknown", "actual-job setup failed"
                else:
                    status, detail = "failed", str(error)
        except (OSError, subprocess.SubprocessError) as error:
            status, detail = "unknown", type(error).__name__
        finally:
            if fixture:
                fixture.close()
        observations.append({"name": case, "status": status, "detail": detail})
    unchanged = hashes() == before
    return {"schema_version": 1, "scope": "phase-1-core-probe-only", "frozen": False,
            "checks": observations, "candidate_scripts_unchanged": unchanged,
            "evaluator_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            "fixture_sha256": hashlib.sha256(Path(__file__).with_name("fixture.py").read_bytes()).hexdigest(),
            "measurement_complete": unchanged and all(c["status"] != "unknown" for c in observations),
            "probe_passed": unchanged and all(c["status"] == "passed" for c in observations),
            "sustained_task_accepted": None}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--template", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = evaluate(args.candidate.resolve(), args.template.resolve())
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if result["measurement_complete"] else 2)
