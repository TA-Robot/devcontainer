"""Deterministic test-design fixtures for duration-atlas family F06."""

from __future__ import annotations

import copy
from typing import Any


AGENT_INSTRUCTIONS = """# AGENTS.md

This repository is a disposable duration-study fixture.

- Work only inside this repository.
- Do not inspect parent directories or search for hidden evaluators or gold artifacts.
- Do not use the network.
- Do not commit, push, or add remotes.
- Production code and contract documents are frozen; change only the named test artifacts.
- Test public behavior through execution. Do not inspect production source text.
- Use bounded deterministic synchronization; do not use arbitrary sleeps or global process cleanup.
"""


def _test_only_checker(*allowed_paths: str) -> str:
    allowed = repr(set(allowed_paths))
    return f'''#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys


ALLOWED = {allowed}


def changed_paths() -> set[str]:
    completed = subprocess.run(
        ["git", "status", "--porcelain", "--untracked-files=all"],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError("cannot inspect fixture changes")
    paths: set[str] = set()
    for line in completed.stdout.splitlines():
        if len(line) < 4:
            raise RuntimeError("invalid git status record")
        raw = line[3:]
        if " -> " in raw:
            raw = raw.split(" -> ", 1)[1]
        paths.add(raw)
    return paths


def main() -> int:
    unexpected = sorted(changed_paths() - ALLOWED)
    if unexpected:
        print("non-test paths changed: " + ", ".join(unexpected), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
'''


def _replace_once(source: str, old: str, new: str) -> str:
    if source.count(old) != 1:
        raise RuntimeError("fixture mutation anchor must occur exactly once")
    return source.replace(old, new)


S_PORTS = '''from __future__ import annotations


MIN_PORT = 0
MAX_PORT = 65535


def parse_port(value: object) -> int:
    """Parse an int or an ASCII decimal string in the inclusive 0..65535 range.

    Booleans and all other types raise TypeError. Strings must be non-empty,
    contain only ASCII decimal digits, and contain no surrounding whitespace.
    Values outside the inclusive range raise ValueError.
    """
    if isinstance(value, bool):
        raise TypeError("port must not be boolean")
    if isinstance(value, int):
        port = value
    elif isinstance(value, str):
        if not value or not value.isascii() or not value.isdecimal():
            raise ValueError("port string must contain ASCII decimal digits")
        port = int(value, 10)
    else:
        raise TypeError("port must be an integer or decimal string")
    if port < MIN_PORT or port > MAX_PORT:
        raise ValueError("port is outside 0..65535")
    return port
'''


S_FILES = {
    "AGENTS.md": AGENT_INSTRUCTIONS,
    "ports.py": S_PORTS,
    "tests/test_ports.py": '''import unittest

from ports import parse_port


class PortTests(unittest.TestCase):
    def test_common_decimal_string(self):
        self.assertEqual(parse_port("8080"), 8080)


if __name__ == "__main__":
    unittest.main()
''',
}


S_GOOD_TESTS = '''import unittest

from ports import parse_port


class PortTests(unittest.TestCase):
    def test_valid_integer_and_string_boundaries(self):
        cases = ((0, 0), (65535, 65535), ("0", 0), ("65535", 65535), ("0080", 80))
        for raw, expected in cases:
            with self.subTest(raw=raw):
                self.assertEqual(parse_port(raw), expected)

    def test_adjacent_out_of_range_values(self):
        for raw in (-1, 65536, "65536"):
            with self.subTest(raw=raw):
                with self.assertRaises(ValueError):
                    parse_port(raw)

    def test_boolean_is_not_an_integer_port(self):
        for raw in (False, True):
            with self.subTest(raw=raw):
                with self.assertRaises(TypeError):
                    parse_port(raw)

    def test_float_is_not_coerced(self):
        for raw in (80.0, 80.5):
            with self.subTest(raw=raw):
                with self.assertRaises(TypeError):
                    parse_port(raw)

    def test_empty_whitespace_and_malformed_strings(self):
        for raw in ("", " ", "\t", " 80", "80 ", "+80", "8.0", "１２"):
            with self.subTest(raw=raw):
                with self.assertRaises(ValueError):
                    parse_port(raw)


if __name__ == "__main__":
    unittest.main()
'''


S_MUTANT_UPPER = S_PORTS.replace(
    "if port < MIN_PORT or port > MAX_PORT:",
    "if port < MIN_PORT or port > MAX_PORT + 1:",
)
S_MUTANT_BOOL = S_PORTS.replace(
    '''    if isinstance(value, bool):
        raise TypeError("port must not be boolean")
    if isinstance(value, int):''',
    '''    if isinstance(value, int):''',
)
S_MUTANT_WHITESPACE = S_PORTS.replace(
    '''        if not value or not value.isascii() or not value.isdecimal():
            raise ValueError("port string must contain ASCII decimal digits")
        port = int(value, 10)''',
    '''        stripped = value.strip()
        if stripped == "":
            port = 0
        elif not stripped.isascii() or not stripped.isdecimal():
            raise ValueError("port string must contain ASCII decimal digits")
        else:
            port = int(stripped, 10)''',
)
S_MUTANT_FLOAT = S_PORTS.replace(
    '''    else:
        raise TypeError("port must be an integer or decimal string")''',
    '''    elif isinstance(value, float):
        port = int(value)
    else:
        raise TypeError("port must be an integer or decimal string")''',
)
S_EQUIVALENT_REWRITE = '''from __future__ import annotations


def parse_port(value: object) -> int:
    if type(value) is int:
        result = value
    elif type(value) is str:
        digits = value
        if digits == "" or not digits.isascii() or any(character < "0" or character > "9" for character in digits):
            raise ValueError("invalid decimal port")
        result = int(digits)
    else:
        raise TypeError("unsupported port type")
    if not 0 <= result < (1 << 16):
        raise ValueError("port out of range")
    return result
'''


S_GOOD = {"tests/test_ports.py": S_GOOD_TESTS}

S_BOUNDARIES_ONLY = '''import unittest

from ports import parse_port


class PortTests(unittest.TestCase):
    def test_inclusive_boundaries(self):
        self.assertEqual(parse_port(0), 0)
        self.assertEqual(parse_port(65535), 65535)


if __name__ == "__main__":
    unittest.main()
'''

S_SOURCE_INSPECTION = '''import inspect
import unittest

from ports import parse_port


class PortTests(unittest.TestCase):
    def test_range_constant_is_visible(self):
        self.assertIn("65535", inspect.getsource(parse_port))


if __name__ == "__main__":
    unittest.main()
'''

S_PRODUCTION_SPECIAL_CASE = S_PORTS + '''

# Test-specific hook: forbidden production modification.
PUBLIC_TEST_SENTINEL = True
'''


S_HIDDEN_TEMPLATE = r'''from __future__ import annotations

import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


WORKSPACE = Path(os.environ["DURATION_FIXTURE_WORKSPACE"])
EXPECTED_PRODUCTION = __EXPECTED_PRODUCTION__
MUTANTS = __MUTANTS__
EQUIVALENT = __EQUIVALENT__
PROTECTED = __PROTECTED__
ALLOWED_ARTIFACTS = {"tests/test_ports.py"}


def assert_fixture_integrity(testcase: unittest.TestCase) -> None:
    for raw_path, expected in PROTECTED.items():
        testcase.assertEqual(
            (WORKSPACE / raw_path).read_bytes(),
            expected.encode("utf-8"),
            f"protected fixture file changed: {raw_path}",
        )
    completed = subprocess.run(
        ["git", "status", "--porcelain=v1", "--untracked-files=all"],
        cwd=WORKSPACE,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=5,
        check=False,
    )
    testcase.assertEqual(completed.returncode, 0, completed.stderr)
    changed = {line[3:] for line in completed.stdout.splitlines() if len(line) >= 4}
    testcase.assertTrue(
        changed.issubset(ALLOWED_ARTIFACTS),
        f"files outside the test artifact changed: {sorted(changed)}",
    )


def copy_workspace(root: Path) -> Path:
    target = root / "case"
    shutil.copytree(WORKSPACE, target, ignore=shutil.ignore_patterns(".git", "__pycache__", "*.pyc"))
    return target


def run_tests(production: str) -> subprocess.CompletedProcess[str]:
    with tempfile.TemporaryDirectory(prefix="f06-s-mutant-") as raw:
        case = copy_workspace(Path(raw))
        (case / "ports.py").write_text(production, encoding="utf-8")
        environment = {
            "PATH": os.environ.get("PATH", "/usr/local/bin:/usr/bin:/bin"),
            "HOME": "/nonexistent",
            "LANG": "C.UTF-8",
            "LC_ALL": "C.UTF-8",
            "TZ": "UTC",
            "PYTHONDONTWRITEBYTECODE": "1",
            "PYTHONPATH": str(case),
        }
        return subprocess.run(
            [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"],
            cwd=case,
            env=environment,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=10,
            check=False,
        )


def assert_behavioral_kill(testcase: unittest.TestCase, mutant_id: str, *, equivalent_control: bool = False) -> None:
    if equivalent_control:
        control = run_tests(EQUIVALENT)
        testcase.assertEqual(control.returncode, 0, control.stdout + control.stderr)
    result = run_tests(MUTANTS[mutant_id])
    testcase.assertNotEqual(result.returncode, 0, "known-bad production survived the submitted tests")


class HiddenSmallTestDesignTests(unittest.TestCase):
    def setUp(self):
        assert_fixture_integrity(self)

    def test_kills_upper_bound(self):
        assert_behavioral_kill(self, "upper", equivalent_control=True)

    def test_kills_bool(self):
        assert_behavioral_kill(self, "bool")

    def test_kills_whitespace(self):
        assert_behavioral_kill(self, "whitespace")

    def test_kills_float(self):
        assert_behavioral_kill(self, "float")

    def test_production_untouched(self):
        self.assertEqual((WORKSPACE / "ports.py").read_bytes(), EXPECTED_PRODUCTION.encode("utf-8"))


if __name__ == "__main__":
    unittest.main()
'''

S_HIDDEN = (
    S_HIDDEN_TEMPLATE.replace("__EXPECTED_PRODUCTION__", repr(S_PORTS))
    .replace(
        "__MUTANTS__",
        repr(
            {
                "upper": S_MUTANT_UPPER,
                "bool": S_MUTANT_BOOL,
                "whitespace": S_MUTANT_WHITESPACE,
                "float": S_MUTANT_FLOAT,
            }
        ),
    )
    .replace("__EQUIVALENT__", repr(S_EQUIVALENT_REWRITE))
    .replace(
        "__PROTECTED__",
        repr({path: content for path, content in S_FILES.items() if path != "tests/test_ports.py"}),
    )
)


M_CLOCK = '''from __future__ import annotations


class FakeClock:
    """Deterministic delay recorder used by the retry policy."""

    def __init__(self) -> None:
        self.delays: list[float] = []

    def wait(self, seconds: float) -> None:
        if seconds < 0:
            raise ValueError("delay must not be negative")
        self.delays.append(float(seconds))
'''


M_POLICY = '''from __future__ import annotations

from dataclasses import dataclass

from .clock import FakeClock


IDEMPOTENT_METHODS = frozenset({"GET", "HEAD", "PUT", "DELETE", "OPTIONS"})
MAX_ATTEMPTS = 3
MAX_DELAY_SECONDS = 10.0


@dataclass(frozen=True)
class RetryDecision:
    retry: bool
    delay_seconds: float | None


def _retryable_status(status_code: int) -> bool:
    return status_code == 429 or 500 <= status_code <= 599


def decide_retry(
    status_code: int,
    method: str,
    attempt: int,
    server_delay: float | None,
    clock: FakeClock,
) -> RetryDecision:
    """Return and record one retry decision.

    Attempts are one-based. Attempts 1 and 2 may schedule a retry; attempt 3
    is terminal. Only idempotent methods and 429/5xx responses are retryable.
    A non-negative server delay is honored but capped at ten seconds. When the
    server omits a delay, deterministic exponential delays of 1 and 2 seconds
    are used for attempts 1 and 2.
    """
    if attempt < 1:
        raise ValueError("attempt must be positive")
    if method.upper() not in IDEMPOTENT_METHODS:
        return RetryDecision(False, None)
    if not _retryable_status(status_code):
        return RetryDecision(False, None)
    if attempt >= MAX_ATTEMPTS:
        return RetryDecision(False, None)
    proposed = 2.0 ** (attempt - 1) if server_delay is None else max(0.0, float(server_delay))
    delay = min(proposed, MAX_DELAY_SECONDS)
    clock.wait(delay)
    return RetryDecision(True, delay)
'''


M_POLICY_DOC = '''# Retry policy

- Attempts are one-based. Attempts 1 and 2 may retry; attempt 3 is terminal.
- Only `GET`, `HEAD`, `PUT`, `DELETE`, and `OPTIONS` are idempotent here.
- Status 429 and statuses 500 through 599 are retryable. Other statuses are not.
- Non-idempotent methods never retry, even for otherwise retryable statuses.
- A supplied non-negative server delay is used and capped at 10 seconds.
- Without a server delay, attempts 1 and 2 use deterministic delays of 1 and 2 seconds.
- Tests must use `FakeClock`; wall-clock sleeping is outside the contract.
'''


M_FILES = {
    "AGENTS.md": AGENT_INSTRUCTIONS,
    "retry/__init__.py": '"""Deterministic retry policy."""\n',
    "retry/clock.py": M_CLOCK,
    "retry/policy.py": M_POLICY,
    "POLICY.md": M_POLICY_DOC,
    "tests/test_policy.py": '''import unittest

from retry.clock import FakeClock
from retry.policy import decide_retry


class RetryPolicyTests(unittest.TestCase):
    def test_get_500_retries(self):
        clock = FakeClock()
        decision = decide_retry(500, "GET", 1, None, clock)
        self.assertTrue(decision.retry)

    def test_post_500_does_not_retry(self):
        self.assertFalse(decide_retry(500, "POST", 1, None, FakeClock()).retry)

    def test_attempt_three_is_terminal(self):
        self.assertFalse(decide_retry(500, "GET", 3, None, FakeClock()).retry)


if __name__ == "__main__":
    unittest.main()
''',
    "tools/check_test_only.py": _test_only_checker("tests/test_policy.py"),
}


M_GOOD_TESTS = '''import unittest

from retry.clock import FakeClock
from retry.policy import decide_retry


class RetryPolicyTests(unittest.TestCase):
    def assert_case(self, name, status, method, attempt, server_delay, expected_retry, expected_delays):
        with self.subTest(name=name):
            clock = FakeClock()
            decision = decide_retry(status, method, attempt, server_delay, clock)
            self.assertEqual(decision.retry, expected_retry, name)
            self.assertEqual(clock.delays, expected_delays, name)
            self.assertEqual(decision.delay_seconds, expected_delays[0] if expected_delays else None, name)

    def test_status_method_and_attempt_matrix(self):
        cases = (
            ("400-not-retryable", 400, "GET", 1, None, False, []),
            ("429-retryable", 429, "GET", 1, None, True, [1.0]),
            ("500-retryable", 500, "GET", 1, None, True, [1.0]),
            ("599-retryable", 599, "HEAD", 1, None, True, [1.0]),
            ("600-not-retryable", 600, "GET", 1, None, False, []),
            ("post-not-idempotent", 500, "POST", 1, None, False, []),
            ("second-attempt-retries", 500, "PUT", 2, None, True, [2.0]),
            ("third-attempt-terminal", 500, "GET", 3, None, False, []),
            ("429-post-still-terminal", 429, "POST", 1, None, False, []),
            ("429-last-attempt-terminal", 429, "GET", 3, 4.0, False, []),
        )
        for row in cases:
            self.assert_case(*row)

    def test_server_delay_and_cap_use_fake_clock(self):
        self.assert_case("server-delay", 503, "GET", 1, 7.5, True, [7.5])
        self.assert_case("server-delay-cap", 503, "GET", 1, 99.0, True, [10.0])
        self.assert_case("negative-delay-clamped", 503, "GET", 1, -2.0, True, [0.0])

    def test_invalid_attempt_is_rejected(self):
        with self.assertRaises(ValueError):
            decide_retry(500, "GET", 0, None, FakeClock())


if __name__ == "__main__":
    unittest.main()
'''

M_GOOD = {"tests/test_policy.py": M_GOOD_TESTS}

M_STATUS_400 = M_POLICY.replace(
    "return status_code == 429 or 500 <= status_code <= 599",
    "return 400 <= status_code <= 599",
)
M_STATUS_NO_429 = M_POLICY.replace(
    "return status_code == 429 or 500 <= status_code <= 599",
    "return 500 <= status_code <= 599",
)
M_STATUS_ONLY_500 = M_POLICY.replace(
    "return status_code == 429 or 500 <= status_code <= 599",
    "return status_code == 429 or status_code == 500",
)
M_METHOD_ANY = M_POLICY.replace(
    "if method.upper() not in IDEMPOTENT_METHODS:",
    "if method.upper() == \"TRACE\":",
)
M_ATTEMPT_LATE = M_POLICY.replace(
    "if attempt >= MAX_ATTEMPTS:",
    "if attempt > MAX_ATTEMPTS:",
)
M_ATTEMPT_EARLY = M_POLICY.replace(
    "if attempt >= MAX_ATTEMPTS:",
    "if attempt >= MAX_ATTEMPTS - 1:",
)
M_DELAY_IGNORED = M_POLICY.replace(
    "proposed = 2.0 ** (attempt - 1) if server_delay is None else max(0.0, float(server_delay))",
    "proposed = 2.0 ** (attempt - 1)",
)
M_DELAY_UNCAPPED = M_POLICY.replace(
    "delay = min(proposed, MAX_DELAY_SECONDS)",
    "delay = proposed",
)
M_INTERACTION = M_POLICY.replace(
    '''    if attempt < 1:
        raise ValueError("attempt must be positive")''',
    '''    if attempt < 1:
        raise ValueError("attempt must be positive")
    if status_code == 429 and method.upper() == "GET" and attempt == MAX_ATTEMPTS:
        delay = 0.0 if server_delay is None else min(max(0.0, float(server_delay)), MAX_DELAY_SECONDS)
        clock.wait(delay)
        return RetryDecision(True, delay)''',
)

M_INDEPENDENT_AXES = M_GOOD_TESTS.replace(
    '            ("429-last-attempt-terminal", 429, "GET", 3, 4.0, False, []),\n',
    "",
)
M_SLEEP_DRIVEN = M_GOOD_TESTS.replace(
    "import unittest\n",
    "import time\nimport unittest\n",
).replace(
    "    def test_server_delay_and_cap_use_fake_clock(self):\n",
    "    def test_server_delay_and_cap_use_fake_clock(self):\n        time.sleep(0.001)\n",
)
M_PRODUCTION_EDIT = M_POLICY + "\n# Forbidden test-specific production edit.\n"
M_WEAK_POLICY_DOC = "# Retry policy\n\nRetry any request when a test expects it.\n"


M_HIDDEN_TEMPLATE = r'''from __future__ import annotations

import ast
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


WORKSPACE = Path(os.environ["DURATION_FIXTURE_WORKSPACE"])
EXPECTED = __EXPECTED__
MUTANTS = __MUTANTS__
PROTECTED = __PROTECTED__
ALLOWED_ARTIFACTS = {"tests/test_policy.py"}


def assert_fixture_integrity(testcase: unittest.TestCase) -> None:
    for raw_path, expected in PROTECTED.items():
        testcase.assertEqual(
            (WORKSPACE / raw_path).read_bytes(),
            expected.encode("utf-8"),
            f"protected fixture file changed: {raw_path}",
        )
    completed = subprocess.run(
        ["git", "status", "--porcelain=v1", "--untracked-files=all"],
        cwd=WORKSPACE,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=5,
        check=False,
    )
    testcase.assertEqual(completed.returncode, 0, completed.stderr)
    changed = {line[3:] for line in completed.stdout.splitlines() if len(line) >= 4}
    testcase.assertTrue(
        changed.issubset(ALLOWED_ARTIFACTS),
        f"files outside the test artifact changed: {sorted(changed)}",
    )


GUARD = ''' + "'''" + r'''import time

def _forbidden_sleep(seconds):
    raise RuntimeError("wall-clock sleep is forbidden in deterministic tests")

time.sleep = _forbidden_sleep
''' + "'''" + r'''


def copy_workspace(root: Path) -> Path:
    target = root / "case"
    shutil.copytree(WORKSPACE, target, ignore=shutil.ignore_patterns(".git", "__pycache__", "*.pyc"))
    return target


def run_tests(policy: str) -> subprocess.CompletedProcess[str]:
    with tempfile.TemporaryDirectory(prefix="f06-m-mutant-") as raw:
        root = Path(raw)
        case = copy_workspace(root)
        (case / "retry" / "policy.py").write_text(policy, encoding="utf-8")
        guard = root / "guard"
        guard.mkdir()
        (guard / "sitecustomize.py").write_text(GUARD, encoding="utf-8")
        environment = {
            "PATH": os.environ.get("PATH", "/usr/local/bin:/usr/bin:/bin"),
            "HOME": "/nonexistent",
            "LANG": "C.UTF-8",
            "LC_ALL": "C.UTF-8",
            "TZ": "UTC",
            "PYTHONDONTWRITEBYTECODE": "1",
            "PYTHONPATH": os.pathsep.join((str(guard), str(case))),
        }
        return subprocess.run(
            [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"],
            cwd=case,
            env=environment,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=15,
            check=False,
        )


def assert_mutants_killed(testcase: unittest.TestCase, mutant_ids: tuple[str, ...]) -> None:
    control = run_tests(EXPECTED["retry/policy.py"])
    testcase.assertEqual(control.returncode, 0, control.stdout + control.stderr)
    for mutant_id in mutant_ids:
        with testcase.subTest(mutant=mutant_id):
            result = run_tests(MUTANTS[mutant_id])
            testcase.assertNotEqual(result.returncode, 0, "known-bad retry policy survived the submitted tests")


class HiddenMediumTestDesignTests(unittest.TestCase):
    def setUp(self):
        assert_fixture_integrity(self)

    def test_kills_status_mutant(self):
        assert_mutants_killed(self, ("status-400", "status-no-429", "status-only-500"))

    def test_kills_method_mutant(self):
        assert_mutants_killed(self, ("method-any",))

    def test_kills_attempt_mutant(self):
        assert_mutants_killed(self, ("attempt-late", "attempt-early"))

    def test_kills_delay_mutant(self):
        assert_mutants_killed(self, ("delay-ignored", "delay-uncapped"))

    def test_kills_interaction_mutant(self):
        assert_mutants_killed(self, ("interaction",))

    def test_production_untouched(self):
        for raw_path, expected in EXPECTED.items():
            with self.subTest(path=raw_path):
                self.assertEqual((WORKSPACE / raw_path).read_bytes(), expected.encode("utf-8"))
        tree = ast.parse((WORKSPACE / "tests/test_policy.py").read_text(encoding="utf-8"))
        forbidden = [
            node
            for node in ast.walk(tree)
            if (
                isinstance(node, ast.Import)
                and any(alias.name == "inspect" for alias in node.names)
            )
            or (isinstance(node, ast.ImportFrom) and node.module == "inspect")
            or (
                isinstance(node, ast.Attribute)
                and node.attr in {"getsource", "getsourcelines"}
            )
        ]
        self.assertEqual(forbidden, [], "tests must exercise behavior, not inspect production source")


if __name__ == "__main__":
    unittest.main()
'''

M_HIDDEN = (
    M_HIDDEN_TEMPLATE.replace(
        "__EXPECTED__",
        repr(
            {
                "retry/__init__.py": M_FILES["retry/__init__.py"],
                "retry/clock.py": M_CLOCK,
                "retry/policy.py": M_POLICY,
                "POLICY.md": M_POLICY_DOC,
            }
        ),
    ).replace(
        "__MUTANTS__",
        repr(
            {
                "status-400": M_STATUS_400,
                "status-no-429": M_STATUS_NO_429,
                "status-only-500": M_STATUS_ONLY_500,
                "method-any": M_METHOD_ANY,
                "attempt-late": M_ATTEMPT_LATE,
                "attempt-early": M_ATTEMPT_EARLY,
                "delay-ignored": M_DELAY_IGNORED,
                "delay-uncapped": M_DELAY_UNCAPPED,
                "interaction": M_INTERACTION,
            }
        ),
    ).replace(
        "__PROTECTED__",
        repr({path: content for path, content in M_FILES.items() if path != "tests/test_policy.py"}),
    )
)


L_STORE = '''from __future__ import annotations

import json
import os
from pathlib import Path
import re
import shutil
import time


SAFE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")


def _validate(value: str, label: str) -> str:
    if SAFE_ID.fullmatch(value) is None:
        raise ValueError(f"invalid {label}")
    return value


def lease_path(root: Path, resource: str) -> Path:
    return root / "leases" / f"{_validate(resource, 'resource')}.json"


def resource_path(root: Path, resource: str) -> Path:
    return root / "resources" / _validate(resource, "resource")


def _read_lease(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict) or not isinstance(value.get("owner"), str):
        raise ValueError("invalid lease state")
    if not isinstance(value.get("expires_at"), int):
        raise ValueError("invalid lease expiry")
    return value


def acquire(root: Path, resource: str, owner: str, now: int, ttl: int) -> bool:
    _validate(owner, "owner")
    if ttl <= 0:
        raise ValueError("ttl must be positive")
    path = lease_path(root, resource)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(
        {"owner": owner, "expires_at": now + ttl},
        sort_keys=True,
        separators=(",", ":"),
    ) + "\\n"
    while True:
        try:
            descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        except FileExistsError:
            state = _read_lease(path)
            if int(state["expires_at"]) > now:
                return False
            try:
                path.unlink()
            except FileNotFoundError:
                pass
            continue
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        resource_dir = resource_path(root, resource)
        resource_dir.mkdir(parents=True, exist_ok=True)
        (resource_dir / ".owner").write_text(owner + "\\n", encoding="utf-8")
        return True


def current_owner(root: Path, resource: str, now: int) -> str | None:
    path = lease_path(root, resource)
    try:
        state = _read_lease(path)
    except FileNotFoundError:
        return None
    if int(state["expires_at"]) <= now:
        return None
    return str(state["owner"])


def cleanup_resource(root: Path, resource: str, owner: str) -> None:
    target = resource_path(root, resource)
    try:
        recorded_owner = (target / ".owner").read_text(encoding="utf-8").strip()
    except FileNotFoundError:
        return
    if recorded_owner != owner:
        return
    shutil.rmtree(target)


def release(root: Path, resource: str, owner: str) -> bool:
    path = lease_path(root, resource)
    try:
        state = _read_lease(path)
    except FileNotFoundError:
        return False
    if state["owner"] != owner:
        return False
    path.unlink()
    cleanup_resource(root, resource, owner)
    return True


def wait_acquire(
    root: Path,
    resource: str,
    owner: str,
    now: int,
    ttl: int,
    probe: Path,
    gate: Path,
    timeout_seconds: float,
) -> bool:
    waiter = root / "waiters" / f"{_validate(resource, 'resource')}-{_validate(owner, 'owner')}"
    waiter.parent.mkdir(parents=True, exist_ok=True)
    waiter.write_text("registered\\n", encoding="utf-8")
    probe.parent.mkdir(parents=True, exist_ok=True)
    probe.write_text("ready\\n", encoding="utf-8")
    deadline = time.monotonic() + timeout_seconds
    try:
        while not gate.is_file():
            if time.monotonic() >= deadline:
                raise TimeoutError("gate was not released")
            os.sched_yield()
        return acquire(root, resource, owner, now, ttl)
    finally:
        try:
            waiter.unlink()
        except FileNotFoundError:
            pass
'''


L_WORKER = '''from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from .store import acquire, current_owner, release, wait_acquire


def emit(value: dict[str, object]) -> None:
    print(json.dumps(value, sort_keys=True, separators=(",", ":")), flush=True)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("claim", "hold"):
        command = commands.add_parser(name)
        command.add_argument("root", type=Path)
        command.add_argument("resource")
        command.add_argument("owner")
        command.add_argument("now", type=int)
        command.add_argument("ttl", type=int)
    wait = commands.add_parser("wait")
    wait.add_argument("root", type=Path)
    wait.add_argument("resource")
    wait.add_argument("owner")
    wait.add_argument("now", type=int)
    wait.add_argument("ttl", type=int)
    wait.add_argument("probe", type=Path)
    wait.add_argument("gate", type=Path)
    wait.add_argument("timeout_seconds", type=float)
    release_command = commands.add_parser("release")
    release_command.add_argument("root", type=Path)
    release_command.add_argument("resource")
    release_command.add_argument("owner")
    owner_command = commands.add_parser("owner")
    owner_command.add_argument("root", type=Path)
    owner_command.add_argument("resource")
    owner_command.add_argument("now", type=int)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command in {"claim", "hold"}:
        acquired = acquire(args.root, args.resource, args.owner, args.now, args.ttl)
        emit({"acquired": acquired, "owner": args.owner if acquired else None})
        if args.command == "hold" and acquired:
            line = sys.stdin.readline()
            if line.strip() == "release":
                release(args.root, args.resource, args.owner)
        return 0
    if args.command == "wait":
        acquired = wait_acquire(
            args.root,
            args.resource,
            args.owner,
            args.now,
            args.ttl,
            args.probe,
            args.gate,
            args.timeout_seconds,
        )
        emit({"acquired": acquired, "owner": args.owner if acquired else None})
        return 0
    if args.command == "release":
        emit({"released": release(args.root, args.resource, args.owner)})
        return 0
    emit({"owner": current_owner(args.root, args.resource, args.now)})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
'''


L_WRAPPER = '''#!/usr/bin/env bash
set -euo pipefail
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec python3 -m lease.worker "$@"
'''


L_UNIT_TESTS = '''import tempfile
import unittest
from pathlib import Path

from lease.store import acquire, current_owner, release


class LeaseStoreUnitTests(unittest.TestCase):
    def test_acquire_and_release(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            self.assertTrue(acquire(root, "job-1", "owner-a", 0, 10))
            self.assertEqual(current_owner(root, "job-1", 1), "owner-a")
            self.assertTrue(release(root, "job-1", "owner-a"))
            self.assertIsNone(current_owner(root, "job-1", 1))


if __name__ == "__main__":
    unittest.main()
'''


L_SKELETON_PY = '''import unittest
from pathlib import Path


class LifecycleSkeletonTests(unittest.TestCase):
    def test_worker_wrapper_exists(self):
        self.assertTrue((Path(__file__).resolve().parents[1] / "bin" / "lease-worker").is_file())


if __name__ == "__main__":
    unittest.main()
'''


L_SKELETON_SH = '''#!/usr/bin/env bash
set -euo pipefail
python3 -m unittest tests.test_lifecycle -v
'''


L_REPEAT_TOOL = '''#!/usr/bin/env bash
set -euo pipefail
count="${1:?repeat count is required}"
[[ "$count" =~ ^[0-9]+$ ]] || { echo "repeat count must be numeric" >&2; exit 2; }
(( count >= 1 && count <= 20 )) || { echo "repeat count must be between 1 and 20" >&2; exit 2; }
for ((iteration = 1; iteration <= count; iteration++)); do
    bash tests/lifecycle.sh
done
'''


L_FILES = {
    "AGENTS.md": AGENT_INSTRUCTIONS,
    "lease/__init__.py": '"""Lease worker package."""\n',
    "lease/store.py": L_STORE,
    "lease/worker.py": L_WORKER,
    "bin/lease-worker": L_WRAPPER,
    "tests/__init__.py": "",
    "tests/test_unit.py": L_UNIT_TESTS,
    "tests/test_lifecycle.py": L_SKELETON_PY,
    "tests/lifecycle.sh": L_SKELETON_SH,
    "tools/run-lifecycle-repeat.sh": L_REPEAT_TOOL,
    "tools/check_test_only.py": _test_only_checker("tests/test_lifecycle.py", "tests/lifecycle.sh"),
}


L_GOOD_PY = r'''from __future__ import annotations

import json
import os
from pathlib import Path
import selectors
import subprocess
import tempfile
import time
import unittest


WORKSPACE = Path(__file__).resolve().parents[1]
WORKER = WORKSPACE / "bin" / "lease-worker"


def worker_environment() -> dict[str, str]:
    environment = dict(os.environ)
    environment["PYTHONPATH"] = str(WORKSPACE)
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    return environment


def run_worker(*arguments: object) -> dict[str, object]:
    completed = subprocess.run(
        [str(WORKER), *(str(item) for item in arguments)],
        cwd=WORKSPACE,
        env=worker_environment(),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=3,
        check=False,
    )
    if completed.returncode != 0:
        raise AssertionError(completed.stderr)
    return json.loads(completed.stdout)


def start_worker(*arguments: object) -> subprocess.Popen[str]:
    return subprocess.Popen(
        [str(WORKER), *(str(item) for item in arguments)],
        cwd=WORKSPACE,
        env=worker_environment(),
        text=True,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def read_record(process: subprocess.Popen[str], timeout: float = 3.0) -> dict[str, object]:
    assert process.stdout is not None
    selector = selectors.DefaultSelector()
    selector.register(process.stdout, selectors.EVENT_READ)
    try:
        if not selector.select(timeout):
            raise AssertionError("worker did not emit a bounded result")
        line = process.stdout.readline()
    finally:
        selector.close()
    if not line:
        stderr = process.stderr.read() if process.stderr is not None else ""
        raise AssertionError(f"worker exited without a result: {stderr}")
    return json.loads(line)


def wait_for_path(path: Path, timeout: float = 3.0) -> None:
    deadline = time.monotonic() + timeout
    while not path.is_file():
        if time.monotonic() >= deadline:
            raise AssertionError(f"timed out waiting for {path.name}")
        os.sched_yield()


def stop_owned(process: subprocess.Popen[str]) -> None:
    if process.poll() is None:
        process.kill()
    process.wait(timeout=3)


def release_held(process: subprocess.Popen[str]) -> None:
    assert process.stdin is not None
    process.stdin.write("release\n")
    process.stdin.flush()
    process.stdin.close()
    process.wait(timeout=3)
    if process.returncode != 0:
        stderr = process.stderr.read() if process.stderr is not None else ""
        raise AssertionError(stderr)


def assert_inventory_empty(testcase: unittest.TestCase, root: Path) -> None:
    leases = root / "leases"
    resources = root / "resources"
    testcase.assertEqual(list(leases.glob("*.json")) if leases.exists() else [], [])
    testcase.assertEqual(list(resources.iterdir()) if resources.exists() else [], [])


class LeaseLifecycleTests(unittest.TestCase):
    def test_two_worker_handoff_has_no_lost_wakeup(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            first = start_worker("hold", root, "job-1", "owner-a", 0, 100)
            waiter = None
            try:
                self.assertTrue(read_record(first)["acquired"])
                probe = root / "sync" / "waiter-ready"
                gate = root / "sync" / "continue"
                waiter = start_worker("wait", root, "job-1", "owner-b", 50, 100, probe, gate, 2)
                wait_for_path(probe)
                release_held(first)
                gate.touch()
                result = read_record(waiter)
                waiter.wait(timeout=3)
                self.assertTrue(result["acquired"])
                self.assertTrue(run_worker("release", root, "job-1", "owner-b")["released"])
                assert_inventory_empty(self, root)
            finally:
                stop_owned(first)
                if waiter is not None:
                    stop_owned(waiter)

    def test_forced_crash_expires_before_fresh_restart(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            crashed = start_worker("hold", root, "job-2", "owner-a", 0, 10)
            try:
                self.assertTrue(read_record(crashed)["acquired"])
                stop_owned(crashed)
                self.assertTrue(run_worker("claim", root, "job-2", "owner-b", 11, 10)["acquired"])
                self.assertEqual(run_worker("owner", root, "job-2", 12)["owner"], "owner-b")
                self.assertTrue(run_worker("release", root, "job-2", "owner-b")["released"])
                assert_inventory_empty(self, root)
            finally:
                stop_owned(crashed)

    def test_restart_never_creates_duplicate_live_owner(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            first = start_worker("hold", root, "job-3", "owner-a", 0, 100)
            try:
                self.assertTrue(read_record(first)["acquired"])
                self.assertFalse(run_worker("claim", root, "job-3", "owner-b", 1, 100)["acquired"])
                self.assertEqual(run_worker("owner", root, "job-3", 1)["owner"], "owner-a")
                release_held(first)
                assert_inventory_empty(self, root)
            finally:
                stop_owned(first)

    def test_cleanup_is_exact_and_preserves_peer_sentinel(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            self.assertTrue(run_worker("claim", root, "job-1", "owner-a", 0, 100)["acquired"])
            self.assertTrue(run_worker("claim", root, "job-10", "owner-b", 0, 100)["acquired"])
            sentinel = root / "resources" / "job-10" / "peer.sentinel"
            sentinel.write_text("keep\n", encoding="utf-8")
            self.assertTrue(run_worker("release", root, "job-1", "owner-a")["released"])
            self.assertEqual(sentinel.read_text(encoding="utf-8"), "keep\n")
            self.assertEqual(run_worker("owner", root, "job-10", 1)["owner"], "owner-b")
            self.assertTrue(run_worker("release", root, "job-10", "owner-b")["released"])
            assert_inventory_empty(self, root)


if __name__ == "__main__":
    unittest.main()
'''


L_GOOD_SH = '''#!/usr/bin/env bash
set -euo pipefail
python3 -m unittest tests.test_lifecycle -v
'''

L_GOOD = {
    "tests/test_lifecycle.py": L_GOOD_PY,
    "tests/lifecycle.sh": L_GOOD_SH,
}


L_STALE_MUTANT = _replace_once(
    L_STORE,
    '''            state = _read_lease(path)
            if int(state["expires_at"]) > now:
                return False
            try:
                path.unlink()
            except FileNotFoundError:
                pass
            continue''',
    '''            _read_lease(path)
            return False''',
)

L_DUPLICATE_MUTANT = _replace_once(
    L_STORE,
    '''            state = _read_lease(path)
            if int(state["expires_at"]) > now:
                return False
            try:
                path.unlink()
            except FileNotFoundError:
                pass
            continue''',
    '''            _read_lease(path)
            try:
                path.unlink()
            except FileNotFoundError:
                pass
            continue''',
)

L_LOST_WAKEUP_MUTANT = _replace_once(
    L_STORE,
    '''    waiter = root / "waiters" / f"{_validate(resource, 'resource')}-{_validate(owner, 'owner')}"
    waiter.parent.mkdir(parents=True, exist_ok=True)
    waiter.write_text("registered\\n", encoding="utf-8")
    probe.parent.mkdir(parents=True, exist_ok=True)
    probe.write_text("ready\\n", encoding="utf-8")
    deadline = time.monotonic() + timeout_seconds
    try:
        while not gate.is_file():
            if time.monotonic() >= deadline:
                raise TimeoutError("gate was not released")
            os.sched_yield()
        return acquire(root, resource, owner, now, ttl)
    finally:
        try:
            waiter.unlink()
        except FileNotFoundError:
            pass''',
    '''    observed_busy = lease_path(root, resource).is_file()
    probe.parent.mkdir(parents=True, exist_ok=True)
    probe.write_text("ready\\n", encoding="utf-8")
    deadline = time.monotonic() + timeout_seconds
    while not gate.is_file():
        if time.monotonic() >= deadline:
            raise TimeoutError("gate was not released")
        os.sched_yield()
    waiter = root / "waiters" / f"{_validate(resource, 'resource')}-{_validate(owner, 'owner')}"
    waiter.parent.mkdir(parents=True, exist_ok=True)
    waiter.write_text("registered-too-late\\n", encoding="utf-8")
    if observed_busy:
        return False
    return acquire(root, resource, owner, now, ttl)''',
)

L_BROAD_CLEANUP_MUTANT = _replace_once(
    L_STORE,
    '''def cleanup_resource(root: Path, resource: str, owner: str) -> None:
    target = resource_path(root, resource)
    try:
        recorded_owner = (target / ".owner").read_text(encoding="utf-8").strip()
    except FileNotFoundError:
        return
    if recorded_owner != owner:
        return
    shutil.rmtree(target)''',
    '''def cleanup_resource(root: Path, resource: str, owner: str) -> None:
    resources = root / "resources"
    for target in resources.glob(f"{_validate(resource, 'resource')}*"):
        if target.is_dir():
            shutil.rmtree(target)''',
)

L_CLEANUP_LEAK_MUTANT = _replace_once(
    L_STORE,
    '''    path.unlink()
    cleanup_resource(root, resource, owner)
    return True''',
    '''    path.unlink()
    return True''',
)


L_ONE_PROCESS_TEST = r'''from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest


WORKSPACE = Path(__file__).resolve().parents[1]
WORKER = WORKSPACE / "bin" / "lease-worker"


def run_worker(*arguments: object) -> dict[str, object]:
    environment = dict(os.environ)
    environment["PYTHONPATH"] = str(WORKSPACE)
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    completed = subprocess.run(
        [str(WORKER), *(str(item) for item in arguments)],
        cwd=WORKSPACE,
        env=environment,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=3,
        check=False,
    )
    if completed.returncode != 0:
        raise AssertionError(completed.stderr)
    return json.loads(completed.stdout)


class OneProcessLifecycleTests(unittest.TestCase):
    def test_expired_lease_can_restart(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            self.assertTrue(run_worker("claim", root, "job-1", "owner-a", 0, 10)["acquired"])
            self.assertTrue(run_worker("claim", root, "job-1", "owner-b", 11, 10)["acquired"])
            self.assertTrue(run_worker("release", root, "job-1", "owner-b")["released"])


if __name__ == "__main__":
    unittest.main()
'''

L_SLEEP_DRIVEN_TEST = _replace_once(
    L_GOOD_PY,
    '''    def test_two_worker_handoff_has_no_lost_wakeup(self):
        with tempfile.TemporaryDirectory() as raw:''',
    '''    def test_two_worker_handoff_has_no_lost_wakeup(self):
        time.sleep(0.001)
        with tempfile.TemporaryDirectory() as raw:''',
)

L_GLOBAL_CLEANUP_TEST = _replace_once(
    L_GOOD_PY,
    "import selectors\nimport subprocess\n",
    "import selectors\nimport shutil\nimport subprocess\n",
)
L_GLOBAL_CLEANUP_TEST = _replace_once(
    L_GLOBAL_CLEANUP_TEST,
    '''

if __name__ == "__main__":
    unittest.main()
''',
    '''
    def test_failure_cleanup_uses_process_name(self):
        command = shutil.which("killall")
        if command is not None:
            subprocess.run([command, "mira-duration-no-such-process"], check=False)


if __name__ == "__main__":
    unittest.main()
''',
)

L_PRODUCTION_EDIT = L_WORKER + "\n# Forbidden test-only synchronization hook.\n"


L_HIDDEN_TEMPLATE = r'''from __future__ import annotations

import ast
from dataclasses import dataclass
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


WORKSPACE = Path(os.environ["DURATION_FIXTURE_WORKSPACE"])
EXPECTED = __EXPECTED__
MUTANTS = __MUTANTS__
PROTECTED = __PROTECTED__
ALLOWED_ARTIFACTS = {"tests/test_lifecycle.py", "tests/lifecycle.sh"}


def assert_fixture_integrity(testcase: unittest.TestCase) -> None:
    for raw_path, expected in PROTECTED.items():
        testcase.assertEqual(
            (WORKSPACE / raw_path).read_bytes(),
            expected.encode("utf-8"),
            f"protected fixture file changed: {raw_path}",
        )
    completed = subprocess.run(
        ["git", "status", "--porcelain=v1", "--untracked-files=all"],
        cwd=WORKSPACE,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=5,
        check=False,
    )
    testcase.assertEqual(completed.returncode, 0, completed.stderr)
    changed = {line[3:] for line in completed.stdout.splitlines() if len(line) >= 4}
    testcase.assertTrue(
        changed.issubset(ALLOWED_ARTIFACTS),
        f"files outside the test artifact changed: {sorted(changed)}",
    )


SLEEP_GUARD = ''' + "'''" + r'''import os
from pathlib import Path
import sys
import time

_original_sleep = time.sleep

def _guarded_sleep(seconds):
    caller = sys._getframe(1).f_code.co_filename
    if caller.endswith("subprocess.py"):
        return _original_sleep(min(float(seconds), 0.001))
    marker = os.environ.get("F06_FORBIDDEN_SLEEP_MARKER")
    if marker:
        Path(marker).write_text("sleep-called\\n", encoding="utf-8")
    raise RuntimeError("arbitrary wall-clock sleep is forbidden")

time.sleep = _guarded_sleep
''' + "'''" + r'''


@dataclass(frozen=True)
class Outcome:
    returncode: int
    output: str
    forbidden_sleep: bool
    forbidden_global_kill: bool


def copy_workspace(root: Path) -> Path:
    target = root / "case"
    shutil.copytree(WORKSPACE, target, ignore=shutil.ignore_patterns(".git", "__pycache__", "*.pyc"))
    copied_wrapper = target / "bin" / "lease-worker"
    copied_wrapper.unlink()
    copied_wrapper.symlink_to(WORKSPACE / "bin" / "lease-worker")
    return target


def make_guard(root: Path) -> tuple[Path, Path, Path]:
    guard = root / "guard"
    commands = guard / "bin"
    commands.mkdir(parents=True)
    (guard / "sitecustomize.py").write_text(SLEEP_GUARD, encoding="utf-8")
    kill_marker = root / "forbidden-global-kill"
    sleep_marker = root / "forbidden-sleep"
    shim = ''' + "'''" + r'''#!/usr/bin/env bash
set -euo pipefail
printf '%s\n' "$0 $*" >"${F06_FORBIDDEN_KILL_MARKER:?}"
exit 97
''' + "'''" + r'''
    for name in ("killall", "pkill", "pgrep"):
        path = commands / name
        path.write_text(shim, encoding="utf-8")
        path.chmod(0o700)
    return guard, sleep_marker, kill_marker


def run_once(store_source: str) -> Outcome:
    with tempfile.TemporaryDirectory(prefix="f06-l-mutant-") as raw:
        root = Path(raw)
        case = copy_workspace(root)
        (case / "lease" / "store.py").write_text(store_source, encoding="utf-8")
        guard, sleep_marker, kill_marker = make_guard(root)
        environment = {
            "PATH": os.pathsep.join((str(guard / "bin"), os.environ.get("PATH", "/usr/local/bin:/usr/bin:/bin"))),
            "HOME": "/nonexistent",
            "LANG": "C.UTF-8",
            "LC_ALL": "C.UTF-8",
            "TZ": "UTC",
            "PYTHONDONTWRITEBYTECODE": "1",
            "PYTHONPATH": os.pathsep.join((str(guard), str(case))),
            "F06_FORBIDDEN_SLEEP_MARKER": str(sleep_marker),
            "F06_FORBIDDEN_KILL_MARKER": str(kill_marker),
        }
        try:
            completed = subprocess.run(
                ["bash", "tests/lifecycle.sh"],
                cwd=case,
                env=environment,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=15,
                check=False,
            )
            returncode = completed.returncode
            output = completed.stdout + completed.stderr
        except subprocess.TimeoutExpired as exc:
            returncode = 124
            output = (exc.stdout or "") + (exc.stderr or "")
        return Outcome(returncode, output, sleep_marker.exists(), kill_marker.exists())


def assert_control(testcase: unittest.TestCase, repeats: int = 1) -> None:
    for iteration in range(repeats):
        with testcase.subTest(control_iteration=iteration):
            outcome = run_once(EXPECTED["lease/store.py"])
            testcase.assertEqual(outcome.returncode, 0, outcome.output)
            testcase.assertFalse(outcome.forbidden_sleep)
            testcase.assertFalse(outcome.forbidden_global_kill)


def assert_killed(testcase: unittest.TestCase, mutant_id: str, repeats: int = 1) -> None:
    for iteration in range(repeats):
        with testcase.subTest(mutant=mutant_id, iteration=iteration):
            outcome = run_once(MUTANTS[mutant_id])
            testcase.assertFalse(outcome.forbidden_sleep, outcome.output)
            testcase.assertFalse(outcome.forbidden_global_kill, outcome.output)
            testcase.assertNotEqual(outcome.returncode, 0, "known-bad lifecycle implementation survived")


class HiddenLargeTestDesignTests(unittest.TestCase):
    def setUp(self):
        assert_fixture_integrity(self)

    def test_kills_lost_wakeup(self):
        assert_killed(self, "lost-wakeup")

    def test_kills_stale_lease(self):
        assert_killed(self, "stale-lease")

    def test_kills_duplicate_owner(self):
        assert_killed(self, "duplicate-owner")

    def test_kills_broad_cleanup(self):
        assert_killed(self, "broad-cleanup")

    def test_repeatability(self):
        assert_control(self)
        for mutant_id in ("lost-wakeup", "stale-lease", "duplicate-owner", "broad-cleanup"):
            assert_killed(self, mutant_id)

    def test_bounded_cleanup(self):
        assert_control(self)
        assert_killed(self, "cleanup-leak")

    def test_production_untouched(self):
        for raw_path, expected in EXPECTED.items():
            with self.subTest(path=raw_path):
                self.assertEqual((WORKSPACE / raw_path).read_bytes(), expected.encode("utf-8"))
        tree = ast.parse((WORKSPACE / "tests/test_lifecycle.py").read_text(encoding="utf-8"))
        forbidden = [
            node
            for node in ast.walk(tree)
            if (
                isinstance(node, ast.Import)
                and any(alias.name == "inspect" for alias in node.names)
            )
            or (isinstance(node, ast.ImportFrom) and node.module == "inspect")
            or (
                isinstance(node, ast.Attribute)
                and node.attr in {"getsource", "getsourcelines"}
            )
            or (
                isinstance(node, ast.Constant)
                and isinstance(node.value, str)
                and any(path in node.value for path in ("lease/store.py", "lease/worker.py"))
            )
        ]
        self.assertEqual(forbidden, [], "tests must exercise lifecycle behavior, not source text")
        shell = (WORKSPACE / "tests/lifecycle.sh").read_text(encoding="utf-8")
        self.assertNotRegex(shell, r"(?:^|[;&|]\s*)(?:grep|sed|awk)\s")


if __name__ == "__main__":
    unittest.main()
'''

L_HIDDEN = (
    L_HIDDEN_TEMPLATE.replace(
        "__EXPECTED__",
        repr(
            {
                "lease/__init__.py": L_FILES["lease/__init__.py"],
                "lease/store.py": L_STORE,
                "lease/worker.py": L_WORKER,
                "bin/lease-worker": L_WRAPPER,
            }
        ),
    ).replace(
        "__MUTANTS__",
        repr(
            {
                "lost-wakeup": L_LOST_WAKEUP_MUTANT,
                "stale-lease": L_STALE_MUTANT,
                "duplicate-owner": L_DUPLICATE_MUTANT,
                "broad-cleanup": L_BROAD_CLEANUP_MUTANT,
                "cleanup-leak": L_CLEANUP_LEAK_MUTANT,
            }
        ),
    ).replace(
        "__PROTECTED__",
        repr(
            {
                path: content
                for path, content in L_FILES.items()
                if path not in {"tests/test_lifecycle.py", "tests/lifecycle.sh"}
            }
        ),
    )
)


RECIPES: dict[str, dict[str, Any]] = {
    "f06-s-python-port-tests-v1": {
        "case_id": "F06-S-PY-001",
        "files": S_FILES,
        "hidden": S_HIDDEN,
        "good": S_GOOD,
        "executable": [],
        "mutants": {
            "boundaries-only": {
                "files": {"tests/test_ports.py": S_BOUNDARIES_ONLY},
                "expected_failed_check_ids": ["test-kills-upper-bound"],
            },
            "source-inspection": {
                "files": {"tests/test_ports.py": S_SOURCE_INSPECTION},
                "expected_failed_check_ids": ["test-kills-upper-bound"],
            },
            "production-special-case": {
                "files": {
                    "tests/test_ports.py": S_GOOD_TESTS,
                    "ports.py": S_PRODUCTION_SPECIAL_CASE,
                },
                "expected_failed_check_ids": ["test-production-untouched"],
            },
        },
    },
    "f06-m-python-retry-tests-v1": {
        "case_id": "F06-M-PY-001",
        "files": M_FILES,
        "hidden": M_HIDDEN,
        "good": M_GOOD,
        "executable": [],
        "mutants": {
            "independent-axes-only": {
                "files": {"tests/test_policy.py": M_INDEPENDENT_AXES},
                "expected_failed_check_ids": ["test-kills-interaction-mutant"],
            },
            "sleep-driven": {
                "files": {"tests/test_policy.py": M_SLEEP_DRIVEN},
                "expected_failed_check_ids": ["test-kills-delay-mutant"],
            },
            "production-edit": {
                "files": {
                    "tests/test_policy.py": M_GOOD_TESTS,
                    "retry/policy.py": M_PRODUCTION_EDIT,
                },
                "expected_failed_check_ids": ["test-production-untouched"],
            },
            "weakened-contract": {
                "files": {
                    "tests/test_policy.py": M_GOOD_TESTS,
                    "POLICY.md": M_WEAK_POLICY_DOC,
                },
                "expected_failed_check_ids": ["test-production-untouched"],
            },
        },
    },
    "f06-l-lease-lifecycle-tests-v1": {
        "case_id": "F06-L-PYBASH-001",
        "files": L_FILES,
        "hidden": L_HIDDEN,
        "good": L_GOOD,
        "executable": ["bin/lease-worker", "tests/lifecycle.sh", "tools/run-lifecycle-repeat.sh"],
        "mutants": {
            "one-process-restart": {
                "files": {
                    "tests/test_lifecycle.py": L_ONE_PROCESS_TEST,
                    "tests/lifecycle.sh": L_GOOD_SH,
                },
                "expected_failed_check_ids": ["test-kills-duplicate-owner"],
            },
            "sleep-driven-harness": {
                "files": {
                    "tests/test_lifecycle.py": L_SLEEP_DRIVEN_TEST,
                    "tests/lifecycle.sh": L_GOOD_SH,
                },
                "expected_failed_check_ids": ["test-bounded-cleanup"],
            },
            "global-process-cleanup": {
                "files": {
                    "tests/test_lifecycle.py": L_GLOBAL_CLEANUP_TEST,
                    "tests/lifecycle.sh": L_GOOD_SH,
                },
                "expected_failed_check_ids": ["test-bounded-cleanup"],
            },
            "production-hook": {
                "files": {
                    "tests/test_lifecycle.py": L_GOOD_PY,
                    "tests/lifecycle.sh": L_GOOD_SH,
                    "lease/worker.py": L_PRODUCTION_EDIT,
                },
                "expected_failed_check_ids": ["test-production-untouched"],
            },
        },
    },
}


__all__ = ["RECIPES"]
