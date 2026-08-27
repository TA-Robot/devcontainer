"""Deterministic failing-test-diagnosis duration-study fixtures."""

from __future__ import annotations

import json
from typing import Any


AGENT_INSTRUCTIONS = """# AGENTS.md

This repository is a disposable duration-study fixture.

- Work only inside this repository.
- Do not inspect parent directories or search for hidden evaluators or gold artifacts.
- Do not use the network.
- Do not commit, push, or add remotes.
- Follow the task capsule supplied by the harness and run the listed local checks.
"""


def _document(value: dict[str, Any]) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


CONFIRM_SEEDED_FAILURE = r'''#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import subprocess
import sys


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--test", required=True)
    parser.add_argument("--signature", required=True)
    args = parser.parse_args()
    workspace = Path(__file__).resolve().parents[1]
    completed = subprocess.run(
        [sys.executable, "-m", "unittest", args.test, "-v"],
        cwd=workspace,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=10,
        check=False,
    )
    output = completed.stdout
    if completed.returncode == 0:
        print("expected the seeded test to fail", file=sys.stderr)
        return 1
    if args.signature not in output:
        print("seeded failure did not contain the requested signature", file=sys.stderr)
        return 1
    print(f"confirmed seeded failure: {args.signature}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
'''


S_VALIDATE_DIAGNOSIS = r'''#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
import sys


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: validate_diagnosis.py PATH", file=sys.stderr)
        return 2
    path = Path(sys.argv[1])
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"invalid diagnosis artifact: {exc}", file=sys.stderr)
        return 1
    if not isinstance(value, dict):
        print("diagnosis must be a JSON object", file=sys.stderr)
        return 1
    root = value.get("root_cause")
    reproducer = value.get("reproducer")
    evidence = value.get("evidence")
    regressions = value.get("regression_tests")
    if not isinstance(root, dict) or not all(
        isinstance(root.get(key), str) and root[key]
        for key in ("path", "symbol", "expression", "cause")
    ):
        print("root_cause requires path, symbol, expression, and cause strings", file=sys.stderr)
        return 1
    if not isinstance(reproducer, dict):
        return 1
    command = reproducer.get("command")
    if not isinstance(command, list) or not command or not all(
        isinstance(item, str) and item for item in command
    ):
        print("reproducer.command must be a non-empty argv array", file=sys.stderr)
        return 1
    if not isinstance(reproducer.get("input"), dict):
        return 1
    if "expected" not in reproducer or "observed" not in reproducer:
        return 1
    if not isinstance(evidence, list) or not evidence or not all(
        isinstance(item, dict) and item for item in evidence
    ):
        return 1
    if not isinstance(regressions, list) or len(regressions) < 2 or not all(
        isinstance(item, dict)
        and isinstance(item.get("scenario"), str)
        and isinstance(item.get("input"), dict)
        and "expected" in item
        for item in regressions
    ):
        return 1
    print("diagnosis artifact is structurally valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
'''


M_VALIDATE_DIAGNOSIS = r'''#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
import sys


def nonempty_object(value: object, keys: tuple[str, ...]) -> bool:
    return isinstance(value, dict) and all(key in value for key in keys)


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: validate_diagnosis.py PATH", file=sys.stderr)
        return 2
    try:
        value = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"invalid diagnosis artifact: {exc}", file=sys.stderr)
        return 1
    if not isinstance(value, dict):
        return 1
    root = value.get("root_cause")
    if not nonempty_object(root, ("path", "symbol", "field", "transition", "cause")):
        return 1
    reproducer = value.get("reproducer")
    if not nonempty_object(reproducer, ("fresh", "reload")):
        return 1
    for name in ("fresh", "reload"):
        item = reproducer[name]
        if not nonempty_object(item, ("command", "observed")):
            return 1
        if not isinstance(item["command"], list) or not all(
            isinstance(argument, str) and argument for argument in item["command"]
        ):
            return 1
        if not isinstance(item["observed"], dict):
            return 1
    if not isinstance(value.get("evidence"), list) or not value["evidence"]:
        return 1
    if not isinstance(value.get("causal_chain"), list) or not value["causal_chain"]:
        return 1
    regressions = value.get("regression_tests")
    if not isinstance(regressions, list) or not regressions or not all(
        nonempty_object(item, ("layer", "target", "assertion")) for item in regressions
    ):
        return 1
    if not nonempty_object(value.get("distractor"), ("claim", "ruled_out", "command", "observed")):
        return 1
    print("diagnosis artifact is structurally valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
'''


L_VALIDATE_DIAGNOSIS = r'''#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
import sys


def nonempty_object(value: object, keys: tuple[str, ...]) -> bool:
    return isinstance(value, dict) and all(key in value for key in keys)


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: validate_diagnosis.py PATH", file=sys.stderr)
        return 2
    try:
        value = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"invalid diagnosis artifact: {exc}", file=sys.stderr)
        return 1
    if not isinstance(value, dict):
        return 1
    root = value.get("root_cause")
    if not nonempty_object(root, ("path", "symbol", "event_order", "vulnerable_window")):
        return 1
    if not isinstance(root["event_order"], list) or not root["event_order"]:
        return 1
    reproducer = value.get("reproducer")
    if not nonempty_object(
        reproducer,
        ("command", "expected_exit_code", "signature", "barrier_event"),
    ):
        return 1
    if not isinstance(reproducer["command"], list) or not all(
        isinstance(argument, str) and argument for argument in reproducer["command"]
    ):
        return 1
    if not isinstance(value.get("evidence"), list) or len(value["evidence"]) < 2:
        return 1
    if not isinstance(value.get("regression_tests"), list) or not value["regression_tests"]:
        return 1
    if not nonempty_object(
        value.get("regression"),
        ("path", "phases", "timeout_seconds", "cleanup_scope"),
    ):
        return 1
    if not nonempty_object(
        value.get("semantics"),
        ("delivery_guarantee", "exactly_once_guaranteed", "mitigation_boundary"),
    ):
        return 1
    print("diagnosis artifact is structurally valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
'''


S_FILES = {
    "AGENTS.md": AGENT_INSTRUCTIONS,
    "limits.py": r'''"""Parse retry and timeout limits from a JSON-like mapping."""


def parse_limits(raw: dict[str, object]) -> dict[str, int]:
    retries = raw.get("retries") or 3
    timeout_seconds = int(raw.get("timeout_seconds", 30))
    return {"retries": int(retries), "timeout_seconds": timeout_seconds}
''',
    "tests/__init__.py": "",
    "tests/test_limits.py": r'''import unittest

from limits import parse_limits


class LimitsTests(unittest.TestCase):
    def test_missing_retries_uses_default(self):
        self.assertEqual(parse_limits({})["retries"], 3)

    def test_explicit_zero_is_preserved(self):
        self.assertEqual(
            parse_limits({"retries": 0})["retries"],
            0,
            "explicit-zero must not be replaced by the default",
        )

    def test_timeout_string_is_converted(self):
        self.assertEqual(parse_limits({"timeout_seconds": "12"})["timeout_seconds"], 12)


if __name__ == "__main__":
    unittest.main()
''',
    "tools/confirm_seeded_failure.py": CONFIRM_SEEDED_FAILURE,
    "tools/validate_diagnosis.py": S_VALIDATE_DIAGNOSIS,
}


S_GOOD_DIAGNOSIS: dict[str, Any] = {
    "root_cause": {
        "path": "limits.py",
        "symbol": "parse_limits",
        "expression": 'raw.get("retries") or 3',
        "cause": "The truthiness fallback treats explicit zero as missing and selects the default.",
    },
    "reproducer": {
        "command": [
            "python3",
            "-c",
            "from limits import parse_limits; print(parse_limits({'retries': 0})['retries'])",
        ],
        "input": {"retries": 0},
        "expected": 0,
        "observed": 3,
    },
    "evidence": [
        {
            "path": "tests/test_limits.py",
            "test": "LimitsTests.test_explicit_zero_is_preserved",
            "signature": "explicit-zero",
            "expected": 0,
            "actual": 3,
        }
    ],
    "regression_tests": [
        {"scenario": "missing", "input": {}, "expected": 3},
        {"scenario": "explicit-zero", "input": {"retries": 0}, "expected": 0},
    ],
}


S_HIDDEN = r'''from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import unittest


WORKSPACE = Path(os.environ["DURATION_FIXTURE_WORKSPACE"])


def assert_artifacts_only() -> None:
    completed = subprocess.run(
        ["git", "status", "--porcelain=v1", "--untracked-files=all"],
        cwd=WORKSPACE,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if completed.returncode != 0 or set(completed.stdout.splitlines()) != {"?? diagnosis.json"}:
        raise AssertionError("diagnosis task modified fixture files or created extra artifacts")


def diagnosis() -> dict[str, object]:
    assert_artifacts_only()
    try:
        value = json.loads((WORKSPACE / "diagnosis.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return value if isinstance(value, dict) else {}


class HiddenZeroDiagnosisTests(unittest.TestCase):
    def test_root_cause(self):
        root = diagnosis().get("root_cause", {})
        self.assertIsInstance(root, dict)
        self.assertEqual(root.get("path"), "limits.py")
        self.assertEqual(root.get("symbol"), "parse_limits")
        expression = str(root.get("expression", "")).replace("'", '"')
        self.assertEqual(expression, 'raw.get("retries") or 3')
        cause = str(root.get("cause", "")).lower()
        self.assertTrue(any(term in cause for term in ("truthiness", "falsy", "boolean")))
        self.assertTrue(any(term in cause for term in ("explicit zero", "zero", " 0")))
        self.assertTrue(any(term in cause for term in ("missing", "absent", "default")))
        source = (WORKSPACE / "limits.py").read_text(encoding="utf-8")
        self.assertIn('raw.get("retries") or 3', source)

    def test_reproducer(self):
        reproducer = diagnosis().get("reproducer", {})
        self.assertIsInstance(reproducer, dict)
        self.assertEqual(reproducer.get("input"), {"retries": 0})
        self.assertEqual(reproducer.get("expected"), 0)
        self.assertEqual(reproducer.get("observed"), 3)
        command = reproducer.get("command")
        self.assertIsInstance(command, list)
        self.assertEqual(command[:2], ["python3", "-c"])
        self.assertEqual(len(command), 3)
        program = command[2]
        self.assertIsInstance(program, str)
        self.assertIn("parse_limits", program)
        self.assertIn("retries", program)
        self.assertIn("0", program)
        completed = subprocess.run(
            command,
            cwd=WORKSPACE,
            env={
                "PATH": os.environ.get("PATH", "/usr/local/bin:/usr/bin:/bin"),
                "PYTHONPATH": str(WORKSPACE),
                "PYTHONDONTWRITEBYTECODE": "1",
            },
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=5,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(completed.stdout.strip(), "3")

    def test_regression(self):
        proposals = diagnosis().get("regression_tests", [])
        self.assertIsInstance(proposals, list)
        by_scenario = {
            item.get("scenario"): item
            for item in proposals
            if isinstance(item, dict)
        }
        self.assertEqual(by_scenario.get("missing", {}).get("input"), {})
        self.assertEqual(by_scenario.get("missing", {}).get("expected"), 3)
        self.assertEqual(
            by_scenario.get("explicit-zero", {}).get("input"), {"retries": 0}
        )
        self.assertEqual(by_scenario.get("explicit-zero", {}).get("expected"), 0)

    def test_no_false_cause(self):
        root = diagnosis().get("root_cause", {})
        self.assertIsInstance(root, dict)
        blamed = " ".join(
            str(root.get(key, ""))
            for key in ("expression", "cause", "blamed_symbol", "blamed_expression")
        ).lower()
        self.assertNotIn("int()", blamed)
        self.assertNotIn("integer conversion", blamed)


if __name__ == "__main__":
    unittest.main()
'''


S_MUTANT_BLAME_INT = json.loads(json.dumps(S_GOOD_DIAGNOSIS))
S_MUTANT_BLAME_INT["root_cause"] = {
    "path": "limits.py",
    "symbol": "parse_limits",
    "expression": "int(retries)",
    "cause": "The int() integer conversion discards the explicit value.",
}

S_MUTANT_MISSING_ONLY = json.loads(json.dumps(S_GOOD_DIAGNOSIS))
S_MUTANT_MISSING_ONLY["regression_tests"] = [
    {"scenario": "missing", "input": {}, "expected": 3}
]

S_MUTANT_NO_REPRODUCER = json.loads(json.dumps(S_GOOD_DIAGNOSIS))
S_MUTANT_NO_REPRODUCER["reproducer"] = {
    "input": {"retries": 0},
    "expected": 0,
    "observed": 3,
}


M_FILES = {
    "AGENTS.md": AGENT_INSTRUCTIONS,
    "jobs/__init__.py": '"""Persisted job expiry example."""\n',
    "jobs/model.py": r'''from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass(frozen=True)
class Job:
    job_id: str
    expires_at: datetime


def dump_job(job: Job) -> dict[str, str]:
    expires_at = job.expires_at.astimezone(timezone.utc)
    return {
        "job_id": job.job_id,
        "expires_at": expires_at.isoformat().replace("+00:00", "Z"),
    }
''',
    "jobs/store.py": r'''from __future__ import annotations

from datetime import datetime
import json
from pathlib import Path

from .model import Job, dump_job


def save_job(path: Path, job: Job) -> None:
    path.write_text(
        json.dumps(dump_job(job), sort_keys=True, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )


def load_job(path: Path) -> Job:
    payload = json.loads(path.read_text(encoding="utf-8"))
    raw_expiry = payload["expires_at"]
    if raw_expiry.endswith("Z"):
        raw_expiry = raw_expiry[:-1]
    return Job(
        job_id=payload["job_id"],
        expires_at=datetime.fromisoformat(raw_expiry),
    )
''',
    "jobs/scheduler.py": r'''from __future__ import annotations

from datetime import datetime

from .model import Job


def should_retain(job: Job, now: datetime) -> bool:
    if job.expires_at.tzinfo is None:
        # Compatibility policy for legacy records whose timezone is unknown.
        return True
    return job.expires_at > now
''',
    "tests/__init__.py": "",
    "tests/test_expiry.py": r'''from datetime import datetime, timedelta, timezone
from pathlib import Path
import tempfile
import unittest

from jobs.model import Job
from jobs.scheduler import should_retain
from jobs.store import load_job, save_job


class ExpiryTests(unittest.TestCase):
    def test_fresh_expired_job_is_not_retained(self):
        now = datetime(2026, 8, 27, 12, 0, tzinfo=timezone.utc)
        job = Job("job-1", now - timedelta(seconds=1))
        self.assertFalse(should_retain(job, now))

    def test_expired_job_is_not_retained_after_reload(self):
        now = datetime(2026, 8, 27, 12, 0, tzinfo=timezone.utc)
        job = Job("job-1", now - timedelta(seconds=1))
        with tempfile.TemporaryDirectory() as raw:
            path = Path(raw) / "job.json"
            save_job(path, job)
            reloaded = load_job(path)
        self.assertFalse(
            should_retain(reloaded, now),
            "reload-retained: an expired persisted job was retained",
        )


if __name__ == "__main__":
    unittest.main()
''',
    "tools/observe_expiry.py": r'''#!/usr/bin/env python3
from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import tempfile

from jobs.model import Job
from jobs.scheduler import should_retain
from jobs.store import load_job, save_job


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("fresh", "reload"), required=True)
    args = parser.parse_args()
    now = datetime(2026, 8, 27, 12, 0, tzinfo=timezone.utc)
    job = Job("job-1", now - timedelta(seconds=1))
    observed = job
    if args.mode == "reload":
        with tempfile.TemporaryDirectory(prefix="expiry-observation-") as raw:
            path = Path(raw) / "job.json"
            save_job(path, job)
            observed = load_job(path)
    decision = "retained" if should_retain(observed, now) else "expired"
    tz_kind = "naive" if observed.expires_at.tzinfo is None else "aware"
    print(json.dumps({"mode": args.mode, "decision": decision, "tz_kind": tz_kind}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
''',
    "tools/confirm_seeded_failure.py": CONFIRM_SEEDED_FAILURE,
    "tools/validate_diagnosis.py": M_VALIDATE_DIAGNOSIS,
}


M_FRESH_COMMAND = ["python3", "tools/observe_expiry.py", "--mode", "fresh"]
M_RELOAD_COMMAND = ["python3", "tools/observe_expiry.py", "--mode", "reload"]
M_GOOD_DIAGNOSIS: dict[str, Any] = {
    "root_cause": {
        "path": "jobs/store.py",
        "symbol": "load_job",
        "field": "expires_at",
        "transition": "UTC Z string -> timezone-naive datetime",
        "cause": "load_job strips the UTC Z suffix before datetime.fromisoformat, losing timezone awareness.",
    },
    "reproducer": {
        "fresh": {
            "command": M_FRESH_COMMAND,
            "observed": {"mode": "fresh", "decision": "expired", "tz_kind": "aware"},
        },
        "reload": {
            "command": M_RELOAD_COMMAND,
            "observed": {"mode": "reload", "decision": "retained", "tz_kind": "naive"},
        },
    },
    "evidence": [
        {
            "path": "jobs/store.py",
            "symbol": "load_job",
            "transition": "serialized expires_at ending in Z becomes a naive datetime",
        },
        {
            "path": "jobs/scheduler.py",
            "symbol": "should_retain",
            "transition": "a naive expires_at enters compatibility retention",
        },
    ],
    "causal_chain": [
        {
            "from": "jobs.model.dump_job",
            "to": "jobs.store.load_job",
            "transition": "aware datetime -> UTC Z string -> naive datetime",
        },
        {
            "from": "jobs.store.load_job",
            "to": "jobs.scheduler.should_retain",
            "transition": "naive datetime -> compatibility retention",
        },
    ],
    "regression_tests": [
        {
            "layer": "unit",
            "target": "jobs.store.load_job",
            "assertion": "a UTC Z timestamp reloads with non-null UTC-aware tzinfo",
        },
        {
            "layer": "integration",
            "target": "serialize-reload-expiry",
            "assertion": "an expired persisted job is not retained after reload",
        },
    ],
    "distractor": {
        "claim": "The scheduler expiry boundary is correct for an aware expired datetime.",
        "ruled_out": True,
        "command": M_FRESH_COMMAND,
        "observed": {"mode": "fresh", "decision": "expired", "tz_kind": "aware"},
    },
}


M_HIDDEN = r'''from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import unittest


WORKSPACE = Path(os.environ["DURATION_FIXTURE_WORKSPACE"])
EXPECTED_FRESH = {"mode": "fresh", "decision": "expired", "tz_kind": "aware"}
EXPECTED_RELOAD = {"mode": "reload", "decision": "retained", "tz_kind": "naive"}


def assert_artifacts_only() -> None:
    completed = subprocess.run(
        ["git", "status", "--porcelain=v1", "--untracked-files=all"],
        cwd=WORKSPACE,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if completed.returncode != 0 or set(completed.stdout.splitlines()) != {"?? diagnosis.json"}:
        raise AssertionError("diagnosis task modified fixture files or created extra artifacts")


def diagnosis() -> dict[str, object]:
    assert_artifacts_only()
    try:
        value = json.loads((WORKSPACE / "diagnosis.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return value if isinstance(value, dict) else {}


def run_observation(item: object, expected_mode: str) -> dict[str, object]:
    if not isinstance(item, dict):
        raise AssertionError("observation must be an object")
    command = item.get("command")
    expected_command = ["python3", "tools/observe_expiry.py", "--mode", expected_mode]
    if command != expected_command:
        raise AssertionError(f"unexpected observation command: {command!r}")
    completed = subprocess.run(
        command,
        cwd=WORKSPACE,
        env={
            "PATH": os.environ.get("PATH", "/usr/local/bin:/usr/bin:/bin"),
            "PYTHONPATH": str(WORKSPACE),
            "PYTHONDONTWRITEBYTECODE": "1",
            "TZ": "UTC",
        },
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=5,
        check=False,
    )
    if completed.returncode != 0:
        raise AssertionError(completed.stderr)
    observed = json.loads(completed.stdout)
    if item.get("observed") != observed:
        raise AssertionError("recorded observation does not match command output")
    return observed


class HiddenReloadDiagnosisTests(unittest.TestCase):
    def test_reload_contrast(self):
        reproducer = diagnosis().get("reproducer", {})
        self.assertIsInstance(reproducer, dict)
        self.assertEqual(run_observation(reproducer.get("fresh"), "fresh"), EXPECTED_FRESH)
        self.assertEqual(run_observation(reproducer.get("reload"), "reload"), EXPECTED_RELOAD)

    def test_timezone_cause(self):
        root = diagnosis().get("root_cause", {})
        self.assertIsInstance(root, dict)
        self.assertEqual(root.get("path"), "jobs/store.py")
        self.assertEqual(root.get("symbol"), "load_job")
        self.assertEqual(root.get("field"), "expires_at")
        transition = str(root.get("transition", "")).lower()
        self.assertIn("z", transition)
        self.assertTrue("naive" in transition or "tzinfo" in transition)
        cause = str(root.get("cause", "")).lower()
        self.assertTrue("strip" in cause or "remove" in cause)
        self.assertTrue(any(term in cause for term in ("timezone", "tzinfo", "aware")))

    def test_causal_chain(self):
        chain = diagnosis().get("causal_chain", [])
        self.assertIsInstance(chain, list)
        edges = [
            (item.get("from"), item.get("to"), str(item.get("transition", "")).lower())
            for item in chain
            if isinstance(item, dict)
        ]
        self.assertEqual(len(edges), 2)
        self.assertEqual(edges[0][0:2], ("jobs.model.dump_job", "jobs.store.load_job"))
        self.assertIn("naive", edges[0][2])
        self.assertEqual(
            edges[1][0:2],
            ("jobs.store.load_job", "jobs.scheduler.should_retain"),
        )
        self.assertIn("compatibility retention", edges[1][2])

    def test_regression_layers(self):
        proposals = diagnosis().get("regression_tests", [])
        self.assertIsInstance(proposals, list)
        by_layer = {
            item.get("layer"): item
            for item in proposals
            if isinstance(item, dict)
        }
        unit = by_layer.get("unit", {})
        integration = by_layer.get("integration", {})
        self.assertEqual(unit.get("target"), "jobs.store.load_job")
        unit_assertion = str(unit.get("assertion", "")).lower()
        self.assertTrue("tzinfo" in unit_assertion or "timezone-aware" in unit_assertion)
        self.assertEqual(integration.get("target"), "serialize-reload-expiry")
        integration_assertion = str(integration.get("assertion", "")).lower()
        self.assertIn("expired", integration_assertion)
        self.assertIn("not retained", integration_assertion)

    def test_distractor_rejected(self):
        distractor = diagnosis().get("distractor", {})
        self.assertIsInstance(distractor, dict)
        self.assertIs(distractor.get("ruled_out"), True)
        claim = str(distractor.get("claim", "")).lower()
        self.assertIn("scheduler", claim)
        self.assertTrue(any(term in claim for term in ("correct", "not causal", "ruled out", "unrelated")))
        observed = run_observation(
            {"command": distractor.get("command"), "observed": distractor.get("observed")},
            "fresh",
        )
        self.assertEqual(observed, EXPECTED_FRESH)
        root = diagnosis().get("root_cause", {})
        self.assertNotIn("threshold", str(root).lower())


if __name__ == "__main__":
    unittest.main()
'''


M_MUTANT_THRESHOLD = json.loads(json.dumps(M_GOOD_DIAGNOSIS))
M_MUTANT_THRESHOLD["root_cause"] = {
    "path": "jobs/scheduler.py",
    "symbol": "should_retain",
    "field": "expires_at",
    "transition": "expiry threshold -> retained",
    "cause": "The scheduler threshold comparison is too strict.",
}
M_MUTANT_THRESHOLD["reproducer"] = {
    "fresh": M_GOOD_DIAGNOSIS["reproducer"]["fresh"]
}
M_MUTANT_THRESHOLD["causal_chain"] = [
    {
        "from": "jobs.scheduler.should_retain",
        "to": "jobs.scheduler.should_retain",
        "transition": "threshold -> retention",
    }
]
M_MUTANT_THRESHOLD["distractor"] = {
    "claim": "The scheduler expiry threshold is wrong.",
    "ruled_out": False,
    "command": M_FRESH_COMMAND,
    "observed": M_GOOD_DIAGNOSIS["reproducer"]["fresh"]["observed"],
}

M_MUTANT_DISCONNECTED = json.loads(json.dumps(M_GOOD_DIAGNOSIS))
M_MUTANT_DISCONNECTED["causal_chain"] = [
    {
        "from": "jobs.model.dump_job",
        "to": "jobs.store.load_job",
        "transition": "aware datetime -> UTC Z string -> naive datetime",
    }
]

M_MUTANT_INTEGRATION_ONLY = json.loads(json.dumps(M_GOOD_DIAGNOSIS))
M_MUTANT_INTEGRATION_ONLY["regression_tests"] = [
    {
        "layer": "integration",
        "target": "serialize-reload-expiry",
        "assertion": "an expired persisted job is not retained after reload",
    }
]


L_FILES = {
    "AGENTS.md": AGENT_INSTRUCTIONS,
    "journal.py": r'''from __future__ import annotations

import json
import os
from pathlib import Path
import tempfile


def read_offset(path: Path) -> int:
    if not path.exists():
        return 0
    value = json.loads(path.read_text(encoding="utf-8"))
    offset = value.get("offset")
    if not isinstance(offset, int) or offset < 0:
        raise ValueError("journal offset must be a non-negative integer")
    return offset


def write_offset(path: Path, offset: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, raw_temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary = Path(raw_temporary)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump({"offset": offset}, handle, sort_keys=True, separators=(",", ":"))
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
        directory_fd = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    finally:
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass
''',
    "worker.py": r'''from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import time

from journal import read_offset, write_offset


def append_external_effect(path: Path, event_id: str) -> None:
    with path.open("a", encoding="utf-8") as handle:
        handle.write(event_id + "\n")
        handle.flush()
        os.fsync(handle.fileno())


def signal_barrier(ready: Path, release: Path) -> None:
    with ready.open("w", encoding="utf-8") as handle:
        handle.write("external-effect\n")
        handle.flush()
    with release.open("r", encoding="utf-8") as handle:
        handle.readline()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--events", type=Path, required=True)
    parser.add_argument("--journal", type=Path, required=True)
    parser.add_argument("--effects", type=Path, required=True)
    parser.add_argument("--barrier-ready", type=Path)
    parser.add_argument("--barrier-release", type=Path)
    parser.add_argument("--delay-before-ack", type=float, default=0.0)
    args = parser.parse_args()
    if (args.barrier_ready is None) != (args.barrier_release is None):
        parser.error("both barrier paths are required together")
    events = json.loads(args.events.read_text(encoding="utf-8"))
    offset = read_offset(args.journal)
    if offset >= len(events):
        return 0
    event_id = events[offset]
    append_external_effect(args.effects, event_id)
    if args.barrier_ready is not None:
        signal_barrier(args.barrier_ready, args.barrier_release)
    elif args.delay_before_ack:
        time.sleep(args.delay_before_ack)
    write_offset(args.journal, offset + 1)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
''',
    "bin/restart-repro": r'''#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import selectors
import subprocess
import sys
import tempfile
import time

from journal import read_offset


ROOT = Path(__file__).resolve().parents[1]


def worker_command(root: Path, *extra: str) -> list[str]:
    return [
        sys.executable,
        str(ROOT / "worker.py"),
        "--events",
        str(root / "events.json"),
        "--journal",
        str(root / "journal.json"),
        "--effects",
        str(root / "effects.log"),
        *extra,
    ]


def terminate_owned(process: subprocess.Popen[str], timeout_seconds: float) -> None:
    process.terminate()
    try:
        process.wait(timeout=timeout_seconds)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=timeout_seconds)


def crash_with_barrier(root: Path, timeout_seconds: float) -> str:
    ready = root / "barrier-ready.fifo"
    release = root / "barrier-release.fifo"
    os.mkfifo(ready)
    os.mkfifo(release)
    ready_fd = os.open(ready, os.O_RDONLY | os.O_NONBLOCK)
    process = subprocess.Popen(
        worker_command(
            root,
            "--barrier-ready",
            str(ready),
            "--barrier-release",
            str(release),
        ),
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    try:
        selector = selectors.DefaultSelector()
        selector.register(ready_fd, selectors.EVENT_READ)
        if not selector.select(timeout_seconds):
            raise TimeoutError("worker did not reach external-effect barrier")
        payload = os.read(ready_fd, 4096).decode("utf-8").strip()
        if payload != "external-effect":
            raise RuntimeError(f"unexpected barrier event: {payload!r}")
        terminate_owned(process, timeout_seconds)
        return payload
    finally:
        os.close(ready_fd)
        if process.poll() is None:
            terminate_owned(process, timeout_seconds)


def crash_with_timing_guess(root: Path, timeout_seconds: float) -> str:
    process = subprocess.Popen(
        worker_command(root, "--delay-before-ack", "0.05"),
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    try:
        time.sleep(0.01)
        terminate_owned(process, timeout_seconds)
    finally:
        if process.poll() is None:
            terminate_owned(process, timeout_seconds)
    return "timing-guess"


def main() -> int:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--barrier", action="store_true")
    mode.add_argument("--racy", action="store_true")
    parser.add_argument("--timeout-seconds", type=float, default=3.0)
    args = parser.parse_args()
    if not 0 < args.timeout_seconds <= 10:
        parser.error("timeout must be within (0, 10]")
    try:
        with tempfile.TemporaryDirectory(prefix=f"f03-restart-{os.getpid()}-") as raw:
            root = Path(raw)
            (root / "events.json").write_text('["job-1"]\n', encoding="utf-8")
            barrier_event = (
                crash_with_barrier(root, args.timeout_seconds)
                if args.barrier
                else crash_with_timing_guess(root, args.timeout_seconds)
            )
            journal_before = read_offset(root / "journal.json")
            restarted = subprocess.run(
                worker_command(root),
                cwd=ROOT,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=args.timeout_seconds,
                check=False,
            )
            if restarted.returncode != 0:
                raise RuntimeError(f"restart failed: {restarted.stderr.strip()}")
            journal_after = read_offset(root / "journal.json")
            effects = (root / "effects.log").read_text(encoding="utf-8").splitlines()
            duplicate = effects == ["job-1", "job-1"]
            result = {
                "barrier_event": barrier_event,
                "effects": effects,
                "journal_after_restart": journal_after,
                "journal_before_restart": journal_before,
                "outcome": "duplicate-delivery" if duplicate else "no-duplicate",
                "phase": "crash-after-external-effect-before-durable-ack",
            }
            print(json.dumps(result, sort_keys=True))
            return 1 if duplicate else 0
    except (OSError, RuntimeError, TimeoutError, subprocess.TimeoutExpired) as exc:
        print(json.dumps({"outcome": "harness-error", "error": str(exc)}, sort_keys=True))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
''',
    "tests/__init__.py": "",
    "tests/test_lifecycle.py": r'''from pathlib import Path
import subprocess
import unittest


ROOT = Path(__file__).resolve().parents[1]


class LifecycleTests(unittest.TestCase):
    def test_restart_does_not_duplicate_delivery(self):
        completed = subprocess.run(
            [str(ROOT / "bin" / "restart-repro"), "--racy", "--timeout-seconds", "2"],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=5,
            check=False,
        )
        self.assertEqual(
            completed.returncode,
            0,
            "intermittent-duplicate-delivery: " + completed.stdout,
        )


if __name__ == "__main__":
    unittest.main()
''',
    "tools/validate_diagnosis.py": L_VALIDATE_DIAGNOSIS,
    "tools/check-regression.sh": r'''#!/usr/bin/env bash
set -euo pipefail

if [[ "$#" -ne 1 ]]; then
  echo "usage: check-regression.sh PATH" >&2
  exit 2
fi
candidate=$1
bash -n "$candidate"

for attempt in 1 2 3; do
  set +e
  output=$(timeout 12s bash "$candidate" 2>&1)
  status=$?
  set -e
  if [[ "$status" -ne 1 ]]; then
    echo "regression did not expose the seeded failure on attempt $attempt" >&2
    exit 1
  fi
  python3 - "$output" <<'PY'
import json
import sys

try:
    value = json.loads(sys.argv[1].splitlines()[-1])
except (IndexError, json.JSONDecodeError):
    raise SystemExit(1)
expected = {
    "barrier_event": "external-effect",
    "effects": ["job-1", "job-1"],
    "journal_after_restart": 1,
    "journal_before_restart": 0,
    "outcome": "duplicate-delivery",
    "phase": "crash-after-external-effect-before-durable-ack",
}
if value != expected:
    raise SystemExit(1)
PY
done

echo "confirmed deterministic crash/restart duplicate"
''',
}


L_GOOD_REGRESSION = r'''#!/usr/bin/env bash
set -euo pipefail

script_dir=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
cd "$script_dir"
timeout 8s bin/restart-repro --barrier --timeout-seconds 3
'''


L_GOOD_DIAGNOSIS: dict[str, Any] = {
    "root_cause": {
        "path": "worker.py",
        "symbol": "main",
        "event_order": [
            "load-offset",
            "external-effect",
            "barrier",
            "durable-ack",
        ],
        "vulnerable_window": "after external-effect and before journal.write_offset makes the ack durable",
    },
    "reproducer": {
        "command": ["bash", "regression.sh"],
        "expected_exit_code": 1,
        "signature": "duplicate-delivery",
        "barrier_event": "external-effect",
    },
    "evidence": [
        {
            "phase": "before-restart",
            "journal_offset": 0,
            "effects": ["job-1"],
        },
        {
            "phase": "after-restart",
            "journal_offset": 1,
            "effects": ["job-1", "job-1"],
        },
    ],
    "regression_tests": [
        {
            "layer": "crash-restart",
            "assertion": "barrier forces termination after effect and restart replays retained offset",
        }
    ],
    "regression": {
        "path": "regression.sh",
        "phases": ["start", "barrier", "terminate-owned-worker", "restart", "assert-duplicate"],
        "timeout_seconds": 8,
        "cleanup_scope": "owned worker and process-owned temporary directory",
    },
    "semantics": {
        "delivery_guarantee": "at-least-once",
        "exactly_once_guaranteed": False,
        "mitigation_boundary": "consumer idempotency or a transactional external-effect-and-ack boundary",
    },
}


L_HIDDEN = r'''from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest


WORKSPACE = Path(os.environ["DURATION_FIXTURE_WORKSPACE"])
EXPECTED_RESULT = {
    "barrier_event": "external-effect",
    "effects": ["job-1", "job-1"],
    "journal_after_restart": 1,
    "journal_before_restart": 0,
    "outcome": "duplicate-delivery",
    "phase": "crash-after-external-effect-before-durable-ack",
}


def assert_artifacts_only() -> None:
    completed = subprocess.run(
        ["git", "status", "--porcelain=v1", "--untracked-files=all"],
        cwd=WORKSPACE,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    expected = {"?? diagnosis.json", "?? regression.sh"}
    if completed.returncode != 0 or set(completed.stdout.splitlines()) != expected:
        raise AssertionError("diagnosis task modified fixture files or created extra artifacts")


def diagnosis() -> dict[str, object]:
    assert_artifacts_only()
    try:
        value = json.loads((WORKSPACE / "diagnosis.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return value if isinstance(value, dict) else {}


def run_regression(*, temporary_parent: Path | None = None) -> dict[str, object]:
    assert_artifacts_only()
    environment = {
        "PATH": os.environ.get("PATH", "/usr/local/bin:/usr/bin:/bin"),
        "PYTHONPATH": str(WORKSPACE),
        "PYTHONDONTWRITEBYTECODE": "1",
        "TZ": "UTC",
    }
    if temporary_parent is not None:
        environment["TMPDIR"] = str(temporary_parent)
    completed = subprocess.run(
        ["bash", "regression.sh"],
        cwd=WORKSPACE,
        env=environment,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=12,
        check=False,
    )
    if completed.returncode != 1:
        raise AssertionError(
            f"regression must fail with 1 after exact duplicate; got {completed.returncode}: "
            f"{completed.stdout} {completed.stderr}"
        )
    try:
        return json.loads(completed.stdout.splitlines()[-1])
    except (IndexError, json.JSONDecodeError) as exc:
        raise AssertionError("regression did not emit structured evidence") from exc


class HiddenCrashRestartDiagnosisTests(unittest.TestCase):
    def test_deterministic_barrier(self):
        script = (WORKSPACE / "regression.sh").read_text(encoding="utf-8")
        self.assertIn("--barrier", script)
        self.assertNotRegex(script, r"sleep\s+0?\.0")
        first = run_regression()
        second = run_regression()
        self.assertEqual(first, EXPECTED_RESULT)
        self.assertEqual(second, EXPECTED_RESULT)

    def test_ordering_cause(self):
        root = diagnosis().get("root_cause", {})
        self.assertIsInstance(root, dict)
        self.assertEqual(root.get("path"), "worker.py")
        self.assertEqual(root.get("symbol"), "main")
        self.assertEqual(
            root.get("event_order"),
            ["load-offset", "external-effect", "barrier", "durable-ack"],
        )
        window = str(root.get("vulnerable_window", "")).lower()
        self.assertIn("after external-effect", window)
        self.assertIn("before journal.write_offset", window)

    def test_restart_state(self):
        evidence = diagnosis().get("evidence", [])
        self.assertIsInstance(evidence, list)
        by_phase = {
            item.get("phase"): item
            for item in evidence
            if isinstance(item, dict)
        }
        self.assertEqual(by_phase.get("before-restart", {}).get("journal_offset"), 0)
        self.assertEqual(by_phase.get("before-restart", {}).get("effects"), ["job-1"])
        self.assertEqual(by_phase.get("after-restart", {}).get("journal_offset"), 1)
        self.assertEqual(
            by_phase.get("after-restart", {}).get("effects"),
            ["job-1", "job-1"],
        )
        self.assertEqual(run_regression(), EXPECTED_RESULT)

    def test_regression_reliable(self):
        observations = [run_regression() for _ in range(3)]
        self.assertEqual(observations, [EXPECTED_RESULT] * 3)

    def test_cleanup_bounded(self):
        script = (WORKSPACE / "regression.sh").read_text(encoding="utf-8")
        harness = (WORKSPACE / "bin" / "restart-repro").read_text(encoding="utf-8")
        combined = script + "\n" + harness
        self.assertRegex(script, r"timeout\s+[0-9]+s")
        self.assertIn("TemporaryDirectory", harness)
        self.assertIn("terminate_owned(process", harness)
        self.assertNotIn("pkill", combined)
        self.assertNotIn("killall", combined)
        self.assertNotRegex(combined, r"rm\s+-rf\s+(?:--\s+)?/tmp")
        with tempfile.TemporaryDirectory(prefix="f03-cleanup-check-") as raw:
            temporary_parent = Path(raw)
            self.assertEqual(run_regression(temporary_parent=temporary_parent), EXPECTED_RESULT)
            self.assertEqual(list(temporary_parent.iterdir()), [])

    def test_semantics_honest(self):
        semantics = diagnosis().get("semantics", {})
        self.assertIsInstance(semantics, dict)
        self.assertEqual(semantics.get("delivery_guarantee"), "at-least-once")
        self.assertIs(semantics.get("exactly_once_guaranteed"), False)
        mitigation = str(semantics.get("mitigation_boundary", "")).lower().replace("-", " ")
        self.assertTrue("idempot" in mitigation or "transaction" in mitigation)
        self.assertIn("external effect", mitigation)


if __name__ == "__main__":
    unittest.main()
'''


L_MUTANT_SLEEP_REGRESSION = r'''#!/usr/bin/env bash
set -euo pipefail

script_dir=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
cd "$script_dir"
sleep 0.01
timeout 8s bin/restart-repro --racy --timeout-seconds 3
'''

L_MUTANT_CORRUPTION = json.loads(json.dumps(L_GOOD_DIAGNOSIS))
L_MUTANT_CORRUPTION["root_cause"] = {
    "path": "journal.py",
    "symbol": "read_offset",
    "event_order": ["load-offset", "json-corruption", "replay"],
    "vulnerable_window": "malformed JSON corrupts the acknowledgement offset",
}

L_MUTANT_BROAD_CLEANUP_REGRESSION = r'''#!/usr/bin/env bash
set -euo pipefail

cleanup_all_workers() {
  pkill -f worker.py
  rm -rf /tmp/f03-*
}

script_dir=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
cd "$script_dir"
timeout 8s bin/restart-repro --barrier --timeout-seconds 3
'''

L_MUTANT_EXACTLY_ONCE = json.loads(json.dumps(L_GOOD_DIAGNOSIS))
L_MUTANT_EXACTLY_ONCE["semantics"] = {
    "delivery_guarantee": "exactly-once",
    "exactly_once_guaranteed": True,
    "mitigation_boundary": "the journal alone guarantees exactly-once delivery",
}


RECIPES: dict[str, dict[str, Any]] = {
    "f03-s-python-zero-diagnosis-v1": {
        "case_id": "F03-S-PY-001",
        "files": S_FILES,
        "hidden": S_HIDDEN,
        "good": {"diagnosis.json": _document(S_GOOD_DIAGNOSIS)},
        "executable": [],
        "mutants": {
            "blame-integer-conversion": {
                "files": {"diagnosis.json": _document(S_MUTANT_BLAME_INT)},
                "expected_failed_check_ids": [
                    "diagnosis-root-cause",
                    "diagnosis-no-false-cause",
                ],
            },
            "missing-only-regression": {
                "files": {"diagnosis.json": _document(S_MUTANT_MISSING_ONLY)},
                "expected_failed_check_ids": ["diagnosis-regression"],
            },
            "root-cause-without-command": {
                "files": {"diagnosis.json": _document(S_MUTANT_NO_REPRODUCER)},
                "expected_failed_check_ids": ["diagnosis-reproducer"],
            },
        },
    },
    "f03-m-python-reload-diagnosis-v1": {
        "case_id": "F03-M-PY-001",
        "files": M_FILES,
        "hidden": M_HIDDEN,
        "good": {"diagnosis.json": _document(M_GOOD_DIAGNOSIS)},
        "executable": [],
        "mutants": {
            "scheduler-threshold-without-reload": {
                "files": {"diagnosis.json": _document(M_MUTANT_THRESHOLD)},
                "expected_failed_check_ids": [
                    "diagnosis-reload-contrast",
                    "diagnosis-timezone-cause",
                    "diagnosis-causal-chain",
                    "diagnosis-distractor-rejected",
                ],
            },
            "timezone-without-causal-connection": {
                "files": {"diagnosis.json": _document(M_MUTANT_DISCONNECTED)},
                "expected_failed_check_ids": ["diagnosis-causal-chain"],
            },
            "integration-only-regression": {
                "files": {"diagnosis.json": _document(M_MUTANT_INTEGRATION_ONLY)},
                "expected_failed_check_ids": ["diagnosis-regression-layers"],
            },
        },
    },
    "f03-l-python-bash-crash-diagnosis-v1": {
        "case_id": "F03-L-PYBASH-001",
        "files": L_FILES,
        "hidden": L_HIDDEN,
        "good": {
            "diagnosis.json": _document(L_GOOD_DIAGNOSIS),
            "regression.sh": L_GOOD_REGRESSION,
        },
        "executable": ["bin/restart-repro", "regression.sh"],
        "mutants": {
            "timing-guess-reproducer": {
                "files": {
                    "diagnosis.json": _document(L_GOOD_DIAGNOSIS),
                    "regression.sh": L_MUTANT_SLEEP_REGRESSION,
                },
                "executable": ["regression.sh"],
                "expected_failed_check_ids": ["diagnosis-deterministic-barrier"],
            },
            "json-corruption-cause": {
                "files": {
                    "diagnosis.json": _document(L_MUTANT_CORRUPTION),
                    "regression.sh": L_GOOD_REGRESSION,
                },
                "executable": ["regression.sh"],
                "expected_failed_check_ids": ["diagnosis-ordering-cause"],
            },
            "broad-process-cleanup": {
                "files": {
                    "diagnosis.json": _document(L_GOOD_DIAGNOSIS),
                    "regression.sh": L_MUTANT_BROAD_CLEANUP_REGRESSION,
                },
                "executable": ["regression.sh"],
                "expected_failed_check_ids": ["diagnosis-cleanup-bounded"],
            },
            "unsupported-exactly-once": {
                "files": {
                    "diagnosis.json": _document(L_MUTANT_EXACTLY_ONCE),
                    "regression.sh": L_GOOD_REGRESSION,
                },
                "executable": ["regression.sh"],
                "expected_failed_check_ids": ["diagnosis-semantics-honest"],
            },
        },
    },
}


__all__ = ["RECIPES"]
