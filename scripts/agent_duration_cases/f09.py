"""Deterministic security/isolation duration-study fixtures."""

from __future__ import annotations

import copy
import hashlib
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


def _document(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def _hidden_with_integrity(
    body: str,
    files: dict[str, str],
    editable_paths: set[str],
) -> str:
    protected = {
        path: hashlib.sha256(content.encode("utf-8")).hexdigest()
        for path, content in files.items()
        if path not in editable_paths
    }
    support = f'''from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest


WORKSPACE = Path(os.environ["DURATION_FIXTURE_WORKSPACE"])
PROTECTED_DIGESTS = {protected!r}
ALLOWED_ARTIFACTS = {sorted(editable_paths)!r}


def assert_fixture_integrity(testcase: unittest.TestCase) -> None:
    for raw_path, expected in PROTECTED_DIGESTS.items():
        path = WORKSPACE / raw_path
        testcase.assertTrue(path.is_file(), f"protected file is missing: {{raw_path}}")
        testcase.assertEqual(
            hashlib.sha256(path.read_bytes()).hexdigest(),
            expected,
            f"protected file changed: {{raw_path}}",
        )
    completed = subprocess.run(
        ["git", "status", "--porcelain", "--untracked-files=all"],
        cwd=WORKSPACE,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=5,
        check=False,
    )
    testcase.assertEqual(completed.returncode, 0, completed.stderr)
    changed = {{line[3:] for line in completed.stdout.splitlines() if len(line) >= 4}}
    testcase.assertTrue(
        changed.issubset(set(ALLOWED_ARTIFACTS)),
        f"files outside the artifact contract changed: {{sorted(changed)}}",
    )

'''
    return support + body


S_NAMES = r'''from __future__ import annotations


def validate_name(raw_name: str) -> str:
    if not raw_name or raw_name.startswith("."):
        raise ValueError("name must be non-empty and must not start with a dot")
    if "/" in raw_name or "\\" in raw_name or raw_name in {".", ".."}:
        raise ValueError("name must be one path segment")
    return raw_name
'''


S_WORKSPACE = r'''from __future__ import annotations

from pathlib import Path
from urllib.parse import unquote

from names import validate_name


def create_workspace(root: Path, raw_name: str) -> Path:
    validate_name(raw_name)
    decoded_name = unquote(raw_name)
    target = root / decoded_name
    target.mkdir(parents=True, exist_ok=True)
    return target
'''


S_TESTS = r'''from pathlib import Path
import tempfile
import unittest

from names import validate_name
from workspace import create_workspace


class NameTests(unittest.TestCase):
    def test_benign_name_creates_one_segment(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            target = create_workspace(root, "peer-one")
            self.assertEqual(target.relative_to(root).parts, ("peer-one",))

    def test_raw_separator_is_rejected(self):
        with self.assertRaises(ValueError):
            validate_name("peer/escape")

    def test_double_encoding_is_not_decoded_twice(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            target = create_workspace(root, "peer%252fescape")
            self.assertEqual(target.relative_to(root).parts, ("peer%2fescape",))


if __name__ == "__main__":
    unittest.main()
'''


S_CHECK_REGRESSION = r'''#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("script", type=Path)
    parser.add_argument("--expected", required=True)
    args = parser.parse_args()
    if args.expected != "encoded-separator-escape" or not args.script.is_file():
        return 2
    with tempfile.TemporaryDirectory(prefix="f09-s-probe-") as raw:
        root = Path(raw)
        environment = {
            "PATH": os.environ.get("PATH", "/usr/local/bin:/usr/bin:/bin"),
            "PYTHONPATH": str(Path.cwd()),
            "PYTHONDONTWRITEBYTECODE": "1",
            "SECURITY_PROBE_ROOT": str(root),
            "TZ": "UTC",
        }
        completed = subprocess.run(
            [sys.executable, str(args.script)],
            cwd=Path.cwd(),
            env=environment,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=8,
            check=False,
        )
        if completed.returncode != 1:
            print("raw regression must fail with 1 when the seeded vulnerability is observed", file=sys.stderr)
            return 1
        try:
            observation = json.loads(completed.stdout.splitlines()[-1])
        except (IndexError, json.JSONDecodeError):
            return 1
        expected = {
            "event": "encoded-separator-escape",
            "payload": "peer%2fescape",
            "relative_segments": ["peer", "escape"],
            "violates_one_segment": True,
        }
        if observation != expected:
            return 1
        if not (root / "peer" / "escape").is_dir():
            print("regression did not reach the caller filesystem boundary", file=sys.stderr)
            return 1
    print("confirmed expected encoded-separator escape")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
'''


S_VALIDATE_FINDING = r'''#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
import sys


def main() -> int:
    if len(sys.argv) != 2:
        return 2
    try:
        value = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return 1
    if not isinstance(value, dict) or value.get("version") != 1:
        return 1
    finding = value.get("finding")
    if not isinstance(finding, dict):
        return 1
    required = {
        "payload",
        "raw_representation",
        "decoded_representation",
        "observed_segments",
        "data_flow",
        "impact_scope",
        "arbitrary_parent_traversal_proven",
        "remediation_invariant",
        "double_decode_claimed",
    }
    if not required.issubset(finding):
        return 1
    if not isinstance(finding["data_flow"], list) or not isinstance(finding["observed_segments"], list):
        return 1
    if value.get("regression") != "security_regression.py":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
'''


S_FILES = {
    "AGENTS.md": AGENT_INSTRUCTIONS,
    "names.py": S_NAMES,
    "workspace.py": S_WORKSPACE,
    "tests/test_names.py": S_TESTS,
    "tools/check_security_regression.py": S_CHECK_REGRESSION,
    "tools/validate_finding.py": S_VALIDATE_FINDING,
}


S_GOOD_REGRESSION = r'''from __future__ import annotations

import json
import os
from pathlib import Path

from workspace import create_workspace


def main() -> int:
    root = Path(os.environ["SECURITY_PROBE_ROOT"])
    payload = "peer%2fescape"
    target = create_workspace(root, payload)
    segments = list(target.relative_to(root).parts)
    observation = {
        "event": "encoded-separator-escape",
        "payload": payload,
        "relative_segments": segments,
        "violates_one_segment": len(segments) != 1,
    }
    print(json.dumps(observation, sort_keys=True))
    return 1 if observation["violates_one_segment"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
'''


S_GOOD_FINDING: dict[str, Any] = {
    "version": 1,
    "finding": {
        "payload": "peer%2fescape",
        "raw_representation": "peer%2fescape passes one-segment raw validation",
        "decoded_representation": "peer/escape",
        "observed_segments": ["peer", "escape"],
        "data_flow": ["validate raw name", "percent-decode once", "join decoded path"],
        "impact_scope": "creates a nested path inside the fixture root and violates the one-segment contract",
        "arbitrary_parent_traversal_proven": False,
        "remediation_invariant": "percent-decode exactly once, then validate the canonical value as one segment before path join",
        "double_decode_claimed": False,
    },
    "regression": "security_regression.py",
}


S_HIDDEN_BODY = r'''import ast


def finding() -> dict[str, object]:
    try:
        value = json.loads((WORKSPACE / "finding.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    item = value.get("finding", {}) if isinstance(value, dict) else {}
    return item if isinstance(item, dict) else {}


def run_raw() -> tuple[subprocess.CompletedProcess[str], dict[str, object], Path, tempfile.TemporaryDirectory[str]]:
    temporary = tempfile.TemporaryDirectory(prefix="f09-s-hidden-")
    root = Path(temporary.name)
    completed = subprocess.run(
        ["python3", "security_regression.py"],
        cwd=WORKSPACE,
        env={
            "PATH": os.environ.get("PATH", "/usr/local/bin:/usr/bin:/bin"),
            "PYTHONPATH": str(WORKSPACE),
            "PYTHONDONTWRITEBYTECODE": "1",
            "SECURITY_PROBE_ROOT": str(root),
        },
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=8,
        check=False,
    )
    try:
        observed = json.loads(completed.stdout.splitlines()[-1])
    except (IndexError, json.JSONDecodeError):
        observed = {}
    return completed, observed, root, temporary


class HiddenNameBypassTests(unittest.TestCase):
    def setUp(self):
        assert_fixture_integrity(self)

    def test_bypass_recall(self):
        item = finding()
        self.assertEqual(item.get("payload"), "peer%2fescape")
        self.assertEqual(item.get("decoded_representation"), "peer/escape")
        self.assertEqual(item.get("observed_segments"), ["peer", "escape"])
        completed, observed, root, temporary = run_raw()
        try:
            self.assertEqual(completed.returncode, 1)
            self.assertEqual(observed.get("event"), "encoded-separator-escape")
            self.assertTrue((root / "peer" / "escape").is_dir())
        finally:
            temporary.cleanup()

    def test_negative_test(self):
        tree = ast.parse((WORKSPACE / "security_regression.py").read_text(encoding="utf-8"))
        aliases = {
            alias.asname or alias.name
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom) and node.module == "workspace"
            for alias in node.names
            if alias.name == "create_workspace"
        }
        self.assertTrue(aliases, "regression must import the real workspace caller")
        self.assertTrue(
            any(
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Name)
                and node.func.id in aliases
                for node in ast.walk(tree)
            ),
            "regression must execute the real workspace caller",
        )
        completed = subprocess.run(
            ["python3", "tools/check_security_regression.py", "security_regression.py", "--expected", "encoded-separator-escape"],
            cwd=WORKSPACE,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=10,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)

    def test_root_order(self):
        flow = finding().get("data_flow")
        self.assertIsInstance(flow, list)
        self.assertEqual(len(flow), 3)
        normalized_flow = [str(item).lower() for item in flow]
        self.assertTrue("raw" in normalized_flow[0] and "valid" in normalized_flow[0])
        self.assertTrue("decode" in normalized_flow[1] and "once" in normalized_flow[1])
        self.assertTrue("join" in normalized_flow[2] and "path" in normalized_flow[2])
        invariant = str(finding().get("remediation_invariant", "")).lower()
        decode_at = invariant.find("decode")
        validate_at = invariant.find("valid")
        join_at = invariant.find("join")
        self.assertTrue(0 <= decode_at < validate_at < join_at)
        self.assertIn("once", invariant)
        self.assertIn("segment", invariant)

    def test_impact_scope(self):
        item = finding()
        scope = str(item.get("impact_scope", "")).lower()
        self.assertIn("nested path", scope)
        self.assertIn("fixture root", scope)
        self.assertIn("one-segment contract", scope)
        self.assertIs(item.get("arbitrary_parent_traversal_proven"), False)

    def test_no_double_decode(self):
        item = finding()
        self.assertIs(item.get("double_decode_claimed"), False)
        self.assertNotIn("%252f", str(item).lower())
        completed = subprocess.run(
            ["python3", "-c", "from urllib.parse import unquote; print(unquote('peer%252fescape'))"],
            cwd=WORKSPACE,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=5,
            check=False,
        )
        self.assertEqual(completed.stdout.strip(), "peer%2fescape")


if __name__ == "__main__":
    unittest.main()
'''


S_HIDDEN = _hidden_with_integrity(
    S_HIDDEN_BODY,
    S_FILES,
    {"security_regression.py", "finding.json"},
)


S_MUTANT_RAW_FINDING = copy.deepcopy(S_GOOD_FINDING)
S_MUTANT_RAW_FINDING["finding"]["payload"] = "../escape"
S_MUTANT_RAW_FINDING["finding"]["raw_representation"] = "raw parent traversal"
S_MUTANT_RAW_REGRESSION = S_GOOD_REGRESSION.replace("peer%2fescape", "../escape")

S_MUTANT_VALIDATOR_ONLY = r'''from __future__ import annotations

import json

from names import validate_name


def main() -> int:
    payload = "peer%2fescape"
    validate_name(payload)
    print(json.dumps({
        "event": "encoded-separator-escape",
        "payload": payload,
        "relative_segments": ["peer", "escape"],
        "violates_one_segment": True,
    }, sort_keys=True))
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
'''

S_MUTANT_DOUBLE_FINDING = copy.deepcopy(S_GOOD_FINDING)
S_MUTANT_DOUBLE_FINDING["finding"]["double_decode_claimed"] = True
S_MUTANT_DOUBLE_FINDING["finding"]["payload"] = "peer%252fescape"

S_MUTANT_UNBOUNDED_FINDING = copy.deepcopy(S_GOOD_FINDING)
S_MUTANT_UNBOUNDED_FINDING["finding"]["impact_scope"] = "arbitrary parent traversal and full filesystem escape"
S_MUTANT_UNBOUNDED_FINDING["finding"]["arbitrary_parent_traversal_proven"] = True


M_PATHS = r'''#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path


def resolve_task_path(workspace: Path, relative: str) -> Path:
    root = workspace.absolute()
    candidate = (root / relative).absolute()
    if os.path.commonpath([str(root), str(candidate)]) != str(root):
        raise ValueError("task path is outside the lexical workspace")
    return candidate.resolve()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--relative", required=True)
    args = parser.parse_args()
    try:
        resolved = resolve_task_path(args.root, args.relative)
        content = resolved.read_text(encoding="utf-8").strip()
    except (OSError, ValueError) as exc:
        print(str(exc))
        return 4
    print(json.dumps({"content": content, "resolved": str(resolved), "root": str(args.root.resolve())}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
'''


M_RUN_TASK = r'''#!/usr/bin/env bash
set -euo pipefail

if [[ "$#" -ne 2 ]]; then
  echo "usage: run-task EXPECTED_WORKSPACE RELATIVE_PATH" >&2
  exit 2
fi
expected_workspace=$1
relative_path=$2
task_workspace=${TASK_WORKSPACE:-$expected_workspace}
exec python3 isolation/paths.py --root "$task_workspace" --relative "$relative_path"
'''


M_TESTS = r'''from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

from isolation.paths import resolve_task_path


ROOT = Path(__file__).resolve().parents[1]


class IsolationTests(unittest.TestCase):
    def test_direct_descendant_is_allowed(self):
        with tempfile.TemporaryDirectory() as raw:
            workspace = Path(raw)
            target = workspace / "inside.txt"
            target.write_text("inside\n", encoding="utf-8")
            self.assertEqual(resolve_task_path(workspace, "inside.txt"), target.resolve())

    def test_internal_symlink_is_allowed(self):
        with tempfile.TemporaryDirectory() as raw:
            workspace = Path(raw)
            internal = workspace / "internal"
            internal.mkdir()
            target = internal / "inside.txt"
            target.write_text("inside\n", encoding="utf-8")
            (workspace / "link").symlink_to(internal, target_is_directory=True)
            self.assertEqual(resolve_task_path(workspace, "link/inside.txt"), target.resolve())

    def test_explicit_launcher_workspace_reaches_descendant(self):
        with tempfile.TemporaryDirectory() as raw:
            workspace = Path(raw)
            (workspace / "inside.txt").write_text("inside\n", encoding="utf-8")
            environment = dict(os.environ)
            environment.pop("TASK_WORKSPACE", None)
            completed = subprocess.run(
                ["bash", "bin/run-task", str(workspace), "inside.txt"],
                cwd=ROOT,
                env=environment,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=5,
                check=False,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertEqual(json.loads(completed.stdout)["content"], "inside")


if __name__ == "__main__":
    unittest.main()
'''


M_CHECK_REGRESSION = r'''#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("script", type=Path)
    parser.add_argument("--expected", required=True)
    args = parser.parse_args()
    expected = set(args.expected.split(","))
    if expected != {"symlink", "env-root"} or not args.script.is_file():
        return 2
    with tempfile.TemporaryDirectory(prefix="f09-m-probe-") as raw:
        root = Path(raw)
        completed = subprocess.run(
            [sys.executable, str(args.script)],
            cwd=Path.cwd(),
            env={
                "PATH": os.environ.get("PATH", "/usr/local/bin:/usr/bin:/bin"),
                "PYTHONPATH": str(Path.cwd()),
                "PYTHONDONTWRITEBYTECODE": "1",
                "SECURITY_PROBE_ROOT": str(root),
                "TZ": "UTC",
            },
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=12,
            check=False,
        )
        if completed.returncode != 1:
            print("raw regression must fail with 1 after both expected escapes", file=sys.stderr)
            return 1
        try:
            observation = json.loads(completed.stdout.splitlines()[-1])
        except (IndexError, json.JSONDecodeError):
            return 1
        if set(observation.get("observed", [])) != expected:
            return 1
        if observation.get("valid_descendant") is not True or observation.get("safe_internal_symlink") is not True:
            return 1
        if observation.get("requires_privilege") is not False:
            return 1
        if not (root / "trusted" / "external-link").is_symlink():
            return 1
        if not (root / "trusted" / "internal-link").is_symlink():
            return 1
        if not (root / "outside" / "secret.txt").is_file():
            return 1
    print("confirmed symlink and inherited-root escapes with positive controls")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
'''


M_VALIDATE_REVIEW = r'''#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
import sys


def main() -> int:
    if len(sys.argv) != 2:
        return 2
    try:
        value = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return 1
    if not isinstance(value, dict) or value.get("version") != 1:
        return 1
    findings = value.get("findings")
    if not isinstance(findings, list):
        return 1
    kinds = {item.get("kind") for item in findings if isinstance(item, dict)}
    if not kinds.issubset({"symlink", "env-root"}) or not kinds:
        return 1
    for finding in findings:
        if not isinstance(finding, dict) or not all(
            key in finding for key in ("kind", "trigger", "observation", "trust_boundary", "mitigation_invariants")
        ):
            return 1
    composition = value.get("composition")
    positives = value.get("positive_matrix")
    if not isinstance(composition, dict) or not isinstance(positives, dict):
        return 1
    if not isinstance(composition.get("required_controls"), list):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
'''


M_FILES = {
    "AGENTS.md": AGENT_INSTRUCTIONS,
    "isolation/__init__.py": "",
    "isolation/paths.py": M_PATHS,
    "bin/run-task": M_RUN_TASK,
    "tests/test_isolation.py": M_TESTS,
    "security_regression.py": r'''raise SystemExit("TODO: add composed isolation regression")
''',
    "tools/check_security_regression.py": M_CHECK_REGRESSION,
    "tools/validate_security_review.py": M_VALIDATE_REVIEW,
}


M_GOOD_REGRESSION = r'''from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess

from isolation.paths import resolve_task_path


ROOT = Path(__file__).resolve().parent


def main() -> int:
    probe = Path(os.environ["SECURITY_PROBE_ROOT"])
    trusted = probe / "trusted"
    outside = probe / "outside"
    internal = trusted / "internal"
    trusted.mkdir()
    outside.mkdir()
    internal.mkdir()
    (trusted / "direct.txt").write_text("direct\n", encoding="utf-8")
    (outside / "secret.txt").write_text("outside-sentinel\n", encoding="utf-8")
    (internal / "inside.txt").write_text("inside-sentinel\n", encoding="utf-8")
    (trusted / "external-link").symlink_to(outside, target_is_directory=True)
    (trusted / "internal-link").symlink_to(internal, target_is_directory=True)

    escaped = resolve_task_path(trusted, "external-link/secret.txt")
    symlink_escape = outside.resolve() in escaped.parents and escaped.read_text(encoding="utf-8").strip() == "outside-sentinel"

    environment = dict(os.environ)
    environment["TASK_WORKSPACE"] = str(outside)
    launched = subprocess.run(
        ["bash", "bin/run-task", str(trusted), "secret.txt"],
        cwd=ROOT,
        env=environment,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=5,
        check=False,
    )
    launched_value = json.loads(launched.stdout) if launched.returncode == 0 else {}
    env_escape = launched_value.get("content") == "outside-sentinel" and Path(launched_value.get("root", "")) == outside.resolve()

    valid_descendant = resolve_task_path(trusted, "direct.txt").read_text(encoding="utf-8").strip() == "direct"
    safe_internal = resolve_task_path(trusted, "internal-link/inside.txt").read_text(encoding="utf-8").strip() == "inside-sentinel"
    observed = sorted(
        name
        for name, present in (("symlink", symlink_escape), ("env-root", env_escape))
        if present
    )
    result = {
        "env_root": {"reached_sentinel": env_escape},
        "observed": observed,
        "requires_privilege": False,
        "safe_internal_symlink": safe_internal,
        "symlink": {"resolved_outside": symlink_escape},
        "valid_descendant": valid_descendant,
    }
    print(json.dumps(result, sort_keys=True))
    return 1 if set(observed) == {"symlink", "env-root"} and valid_descendant and safe_internal else 0


if __name__ == "__main__":
    raise SystemExit(main())
'''


M_GOOD_REVIEW: dict[str, Any] = {
    "version": 1,
    "findings": [
        {
            "kind": "symlink",
            "trigger": "an in-workspace symlink points to a file outside the trusted root",
            "observation": "lexical containment passes before resolve_task_path resolves the external target",
            "trust_boundary": "candidate path after filesystem resolution",
            "mitigation_invariants": [
                "resolve the candidate before containment authorization",
                "require the resolved candidate to remain beneath the trusted root",
            ],
        },
        {
            "kind": "env-root",
            "trigger": "inherited TASK_WORKSPACE names an outside directory",
            "observation": "bin/run-task replaces its explicit expected root before the resolver runs",
            "trust_boundary": "launcher root provenance",
            "mitigation_invariants": [
                "derive the trusted root from the explicit launcher contract",
                "reject inherited root overrides that do not match the trusted root",
            ],
        },
    ],
    "composition": {
        "distinct_boundaries": ["launcher root provenance", "resolved candidate containment"],
        "single_control_bypasses": [
            "post-resolution containment cannot repair an attacker-selected trusted root",
            "trusted root provenance does not stop a symlink resolving outside that root",
        ],
        "required_controls": ["trusted root provenance", "post-resolution containment"],
    },
    "positive_matrix": {
        "explicit_workspace_is_safe": True,
        "requires_privilege": False,
        "safe_internal_symlink_allowed": True,
        "valid_descendant_allowed": True,
    },
}


M_HIDDEN_BODY = r'''import ast


def review() -> dict[str, object]:
    try:
        value = json.loads((WORKSPACE / "security-review.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return value if isinstance(value, dict) else {}


def run_raw() -> dict[str, object]:
    with tempfile.TemporaryDirectory(prefix="f09-m-hidden-") as raw:
        completed = subprocess.run(
            ["python3", "security_regression.py"],
            cwd=WORKSPACE,
            env={
                "PATH": os.environ.get("PATH", "/usr/local/bin:/usr/bin:/bin"),
                "PYTHONPATH": str(WORKSPACE),
                "PYTHONDONTWRITEBYTECODE": "1",
                "SECURITY_PROBE_ROOT": raw,
                "TZ": "UTC",
            },
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=12,
            check=False,
        )
        if completed.returncode != 1:
            raise AssertionError(completed.stdout + completed.stderr)
        return json.loads(completed.stdout.splitlines()[-1])


def findings() -> dict[str, dict[str, object]]:
    items = review().get("findings", [])
    return {item.get("kind"): item for item in items if isinstance(item, dict)}


class HiddenWorkspaceIsolationTests(unittest.TestCase):
    def setUp(self):
        assert_fixture_integrity(self)

    def test_symlink_exploit(self):
        observed = run_raw()
        self.assertIn("symlink", observed.get("observed", []))
        self.assertIs(observed.get("symlink", {}).get("resolved_outside"), True)
        finding = findings().get("symlink", {})
        boundary = str(finding.get("trust_boundary", "")).lower()
        self.assertIn("resol", boundary)
        self.assertTrue("candidate" in boundary or "path" in boundary)
        invariants = " ".join(finding.get("mitigation_invariants", [])).lower()
        self.assertIn("resol", invariants)
        self.assertIn("trusted root", invariants)
        self.assertRegex(invariants, r"beneath|inside|within|contain")

    def test_env_root_exploit(self):
        observed = run_raw()
        self.assertIn("env-root", observed.get("observed", []))
        self.assertIs(observed.get("env_root", {}).get("reached_sentinel"), True)
        finding = findings().get("env-root", {})
        boundary = str(finding.get("trust_boundary", "")).lower()
        for term in ("launcher", "root", "provenance"):
            self.assertIn(term, boundary)
        self.assertIn("TASK_WORKSPACE", str(finding.get("trigger", "")))

    def test_composition(self):
        composition = review().get("composition", {})
        boundaries = " ".join(composition.get("distinct_boundaries", [])).lower()
        controls = " ".join(composition.get("required_controls", [])).lower()
        for term in ("launcher", "root", "provenance", "resol", "contain"):
            self.assertIn(term, boundaries)
        for term in ("trusted root", "provenance", "resol", "contain"):
            self.assertIn(term, controls)
        bypasses = composition.get("single_control_bypasses", [])
        self.assertTrue(any("attacker-selected trusted root" in item for item in bypasses))
        self.assertTrue(any("symlink" in item and "outside" in item for item in bypasses))

    def test_negative_tests(self):
        source = (WORKSPACE / "security_regression.py").read_text(encoding="utf-8")
        tree = ast.parse(source)
        aliases = {
            alias.asname or alias.name
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom) and node.module == "isolation.paths"
            for alias in node.names
            if alias.name == "resolve_task_path"
        }
        calls = [
            node
            for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id in aliases
        ]
        self.assertGreaterEqual(len(calls), 2, "regression must execute the real resolver controls")
        self.assertIn("bin/run-task", source)
        observed = run_raw()
        self.assertIs(observed.get("valid_descendant"), True)
        self.assertIs(observed.get("safe_internal_symlink"), True)
        self.assertIs(observed.get("requires_privilege"), False)
        matrix = review().get("positive_matrix", {})
        self.assertIsInstance(matrix, dict)
        normalized = {str(key).lower().replace("-", "_"): value for key, value in matrix.items()}
        self.assertTrue(any("explicit" in key and "workspace" in key and value is True for key, value in normalized.items()))
        self.assertTrue(any("privilege" in key and value is False for key, value in normalized.items()))
        self.assertTrue(any("internal" in key and "symlink" in key and value is True for key, value in normalized.items()))
        self.assertTrue(any("descendant" in key and value is True for key, value in normalized.items()))

    def test_mitigation_invariants(self):
        required = review().get("composition", {}).get("required_controls", [])
        normalized = " ".join(required).lower()
        for term in ("trusted root", "provenance", "resol", "contain"):
            self.assertIn(term, normalized)
        self.assertEqual(set(findings()), {"symlink", "env-root"})

    def test_no_false_positive(self):
        matrix = review().get("positive_matrix", {})
        normalized = {str(key).lower().replace("-", "_"): value for key, value in matrix.items()}
        self.assertTrue(any("explicit" in key and "workspace" in key and value is True for key, value in normalized.items()))
        self.assertTrue(any("internal" in key and "symlink" in key and value is True for key, value in normalized.items()))
        self.assertNotIn("explicit-workspace", findings())


if __name__ == "__main__":
    unittest.main()
'''


M_HIDDEN = _hidden_with_integrity(
    M_HIDDEN_BODY,
    M_FILES,
    {"security-review.json", "security_regression.py"},
)


M_MUTANT_SYMLINK_REVIEW = copy.deepcopy(M_GOOD_REVIEW)
M_MUTANT_SYMLINK_REVIEW["findings"] = [M_MUTANT_SYMLINK_REVIEW["findings"][0]]
M_MUTANT_SYMLINK_REVIEW["composition"]["required_controls"] = ["post-resolution containment"]
M_MUTANT_SYMLINK_REGRESSION = M_GOOD_REGRESSION.replace(
    '("symlink", symlink_escape), ("env-root", env_escape)',
    '("symlink", symlink_escape), ("env-root", False)',
)

M_MUTANT_ENV_REVIEW = copy.deepcopy(M_GOOD_REVIEW)
M_MUTANT_ENV_REVIEW["findings"] = [M_MUTANT_ENV_REVIEW["findings"][1]]
M_MUTANT_ENV_REVIEW["composition"]["required_controls"] = ["trusted root provenance"]
M_MUTANT_ENV_REGRESSION = M_GOOD_REGRESSION.replace(
    '("symlink", symlink_escape), ("env-root", env_escape)',
    '("symlink", False), ("env-root", env_escape)',
)

M_MUTANT_REJECT_SYMLINK_REVIEW = copy.deepcopy(M_GOOD_REVIEW)
M_MUTANT_REJECT_SYMLINK_REVIEW["positive_matrix"]["safe_internal_symlink_allowed"] = False
M_MUTANT_REJECT_SYMLINK_REGRESSION = M_GOOD_REGRESSION.replace(
    "safe_internal = resolve_task_path(trusted, \"internal-link/inside.txt\").read_text(encoding=\"utf-8\").strip() == \"inside-sentinel\"",
    "safe_internal = False",
)

M_MUTANT_PRIVILEGE_REVIEW = copy.deepcopy(M_GOOD_REVIEW)
M_MUTANT_PRIVILEGE_REVIEW["positive_matrix"]["requires_privilege"] = True


L_WORKTREES = r'''from __future__ import annotations

from pathlib import Path
import re
from typing import Callable


NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")


def create_worktree(
    root: Path,
    name: str,
    owner_token: str,
    interleave: Callable[[Path], None] | None = None,
) -> Path:
    if NAME.fullmatch(name) is None:
        raise ValueError("invalid worktree name")
    path = root / name
    path.mkdir()
    (path / ".owner").write_text(owner_token + "\n", encoding="utf-8")
    if interleave is not None:
        interleave(path)
    if (path / ".owner").read_text(encoding="utf-8").strip() != owner_token:
        raise ValueError("owner marker mismatch")
    return path.resolve()
'''


L_CONTAINER_RUN = r'''#!/usr/bin/env bash
set -euo pipefail

if [[ "$#" -ne 1 ]]; then
  echo "usage: container-run WORKSPACE" >&2
  exit 2
fi
workspace=$1
mount_spec="type=bind,src=$workspace,dst=/workspace"
printf '%s\n' 'docker' 'run' '--mount' "$mount_spec" 'fixture-agent:locked'
'''


L_CREDENTIALS = r'''from __future__ import annotations


def project_credential(provider: str, scope: str, token: str) -> dict[str, str]:
    del provider, scope
    return {"token": token}


def accepted_for(projected: dict[str, str], provider: str, scope: str) -> bool:
    del provider, scope
    return bool(projected.get("token"))
'''


L_CLEANUP = r'''from __future__ import annotations


def cleanup_authorized(
    observed_name: str,
    observed_pid: int,
    expected_name: str,
    expected_pid: int,
) -> bool:
    return observed_name == expected_name and observed_pid == expected_pid
'''


L_TESTS = r'''from pathlib import Path
import subprocess
import tempfile
import unittest

from orchestrator.cleanup import cleanup_authorized
from orchestrator.credentials import accepted_for, project_credential
from orchestrator.worktrees import create_worktree


class BenignBoundaryTests(unittest.TestCase):
    def test_owned_worktree_is_created(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            self.assertEqual(create_worktree(root, "worker-1", "owner-a"), (root / "worker-1").resolve())

    def test_simple_bind_is_one_mount_argument(self):
        completed = subprocess.run(
            ["bash", "bin/container-run", "/tmp/workspace-safe"],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=5,
            check=False,
        )
        self.assertEqual(completed.returncode, 0)
        self.assertIn("type=bind,src=/tmp/workspace-safe,dst=/workspace", completed.stdout.splitlines())

    def test_same_scope_credential_is_usable(self):
        projected = project_credential("provider-a", "project-a/agent-a", "fixture-token")
        self.assertTrue(accepted_for(projected, "provider-a", "project-a/agent-a"))

    def test_owned_cleanup_observation_is_accepted(self):
        self.assertTrue(cleanup_authorized("worker-1", 4101, "worker-1", 4101))


if __name__ == "__main__":
    unittest.main()
'''


L_ATTACK_SIMULATOR = r'''#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import shutil
import subprocess
import tempfile

from orchestrator.cleanup import cleanup_authorized
from orchestrator.credentials import accepted_for, project_credential
from orchestrator.worktrees import create_worktree


REQUIRED = {
    "worktree-marker-race": "marker-replacement",
    "bind-option-injection": "bind-comma-newline",
    "credential-scope-loss": "cross-provider-reuse",
    "cleanup-owner-confusion": "pid-name-reuse",
}


def raw_attacks() -> dict[str, object]:
    with tempfile.TemporaryDirectory(prefix="f09-threat-attacks-") as raw:
        root = Path(raw)
        worktrees = root / "worktrees"
        worktrees.mkdir()
        peer = root / "peer-worktree"
        peer.mkdir()
        (peer / ".owner").write_text("predictable-owner\n", encoding="utf-8")

        def replace_with_peer(path: Path) -> None:
            shutil.rmtree(path)
            path.symlink_to(peer, target_is_directory=True)

        selected = create_worktree(worktrees, "worker-1", "predictable-owner", replace_with_peer)
        worktree_escape = selected == peer.resolve()

        injected_path = str(root / "workspace,readonly") + "\n--privileged"
        bind = subprocess.run(
            ["bash", "bin/container-run", injected_path],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=5,
            check=False,
        )
        bind_escape = bind.returncode == 0 and ",readonly" in bind.stdout and any(
            line.startswith("--privileged") for line in bind.stdout.splitlines()
        )

        projected = project_credential("provider-a", "project-a/agent-a", "fixture-token")
        credential_escape = accepted_for(projected, "provider-b", "project-b/agent-b") and set(projected) == {"token"}

        cleanup_escape = cleanup_authorized("worker-1", 4101, "worker-1", 4101)
        observations = {
            "bind-option-injection": {"observed": bind_escape, "scenario": "bind-comma-newline"},
            "cleanup-owner-confusion": {"observed": cleanup_escape, "scenario": "pid-name-reuse"},
            "credential-scope-loss": {"observed": credential_escape, "scenario": "cross-provider-reuse"},
            "worktree-marker-race": {"observed": worktree_escape, "scenario": "marker-replacement"},
        }
        return {"all_observed": all(item["observed"] for item in observations.values()), "observations": observations}


def validate_model(model_path: Path, observation_path: Path) -> int:
    model = json.loads(model_path.read_text(encoding="utf-8"))
    observed = json.loads(observation_path.read_text(encoding="utf-8"))
    threats = {item.get("kind"): item for item in model.get("threats", []) if isinstance(item, dict)}
    if set(threats) != set(REQUIRED) or observed.get("all_observed") is not True:
        return 1
    for kind, scenario in REQUIRED.items():
        if observed.get("observations", {}).get(kind) != {"observed": True, "scenario": scenario}:
            return 1
        evidence = threats[kind].get("evidence", {})
        if evidence.get("scenario") != scenario or evidence.get("observed") is not True:
            return 1
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw", action="store_true")
    parser.add_argument("--validate-model", type=Path)
    parser.add_argument("--observation", type=Path)
    args = parser.parse_args()
    if args.raw:
        value = raw_attacks()
        print(json.dumps(value, sort_keys=True))
        return 1 if value["all_observed"] else 0
    if args.validate_model is None or args.observation is None:
        return 2
    return validate_model(args.validate_model, args.observation)


if __name__ == "__main__":
    raise SystemExit(main())
'''


L_RUN_ATTACKS = r'''#!/usr/bin/env bash
set -euo pipefail

if [[ "$#" -ne 1 ]]; then
  echo "usage: run-visible-attacks.sh MODEL" >&2
  exit 2
fi
observation=$(mktemp "${TMPDIR:-/tmp}/f09-visible-attacks.XXXXXX")
cleanup() {
  rm -f -- "$observation"
}
trap cleanup EXIT
set +e
python3 scenarios/attack_simulator.py --raw >"$observation"
status=$?
set -e
if [[ "$status" -ne 1 ]]; then
  echo "raw attack simulator did not observe the exact seeded vulnerabilities" >&2
  exit 1
fi
python3 scenarios/attack_simulator.py --validate-model "$1" --observation "$observation"
'''


L_VALIDATE_MODEL = r'''#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
import sys


REQUIRED_KINDS = {
    "worktree-marker-race",
    "bind-option-injection",
    "credential-scope-loss",
    "cleanup-owner-confusion",
}
REQUIRED_TOPOLOGY = {"assets", "actors", "boundaries", "phases", "owners"}


def main() -> int:
    if len(sys.argv) != 3:
        return 2
    try:
        model = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
        markdown = Path(sys.argv[2]).read_text(encoding="utf-8")
    except (OSError, json.JSONDecodeError):
        return 1
    if not isinstance(model, dict) or model.get("version") != 1:
        return 1
    topology = model.get("topology")
    if not isinstance(topology, dict) or not REQUIRED_TOPOLOGY.issubset(topology):
        return 1
    threats = model.get("threats")
    if not isinstance(threats, list):
        return 1
    kinds = {item.get("kind") for item in threats if isinstance(item, dict)}
    if kinds != REQUIRED_KINDS:
        return 1
    for threat in threats:
        required = {"kind", "boundary", "phase", "owner", "preconditions", "evidence", "impact", "controls", "negative_test", "detection", "containment", "recovery", "residual_risk"}
        if not required.issubset(threat):
            return 1
        controls = threat["controls"]
        if not isinstance(controls, dict) or not isinstance(controls.get("preventive"), list) or not isinstance(controls.get("detective"), list):
            return 1
        if f"## {threat['kind']}" not in markdown:
            return 1
        if threat["evidence"].get("scenario") not in markdown:
            return 1
    if not isinstance(model.get("control_counterexamples"), list) or not model["control_counterexamples"]:
        return 1
    if not isinstance(model.get("unknowns"), list) or not model["unknowns"]:
        return 1
    if "## Topology" not in markdown or "## Unknowns" not in markdown:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
'''


L_FILES = {
    "AGENTS.md": AGENT_INSTRUCTIONS,
    "orchestrator/__init__.py": "",
    "orchestrator/worktrees.py": L_WORKTREES,
    "orchestrator/credentials.py": L_CREDENTIALS,
    "orchestrator/cleanup.py": L_CLEANUP,
    "bin/container-run": L_CONTAINER_RUN,
    "scenarios/ATTACKS.md": r'''# Visible attack contract

| Threat kind | Scenario | Safe observation |
| --- | --- | --- |
| worktree-marker-race | marker-replacement | a temporary worktree path resolves to a peer fixture |
| bind-option-injection | bind-comma-newline | comma/newline data changes the simulated mount option surface |
| credential-scope-loss | cross-provider-reuse | projected fixture token loses provider/project/agent scope |
| cleanup-owner-confusion | pid-name-reuse | a peer with reused PID/name is authorized without an owner token |
''',
    "scenarios/attack_simulator.py": L_ATTACK_SIMULATOR,
    "scenarios/run-visible-attacks.sh": L_RUN_ATTACKS,
    "tests/test_boundaries.py": L_TESTS,
    "tools/validate_threat_model.py": L_VALIDATE_MODEL,
}


L_TOPOLOGY = {
    "assets": ["worktree", "bind-mount", "provider-credential", "process-container-lifecycle"],
    "actors": ["orchestrator", "task-agent", "peer-agent", "provider"],
    "boundaries": ["git-worktree-ownership", "docker-bind-construction", "provider-credential-scope", "cleanup-ownership"],
    "phases": ["create", "launch", "project", "cleanup", "detect", "recover"],
    "owners": {
        "worktree": "orchestrator-worktree-owner",
        "bind-mount": "container-launcher-owner",
        "provider-credential": "credential-adapter-owner",
        "process-container-lifecycle": "cleanup-supervisor-owner",
        "recovery": "incident-commander",
    },
}


L_GOOD_MODEL: dict[str, Any] = {
    "version": 1,
    "topology": L_TOPOLOGY,
    "threats": [
        {
            "kind": "worktree-marker-race",
            "boundary": "git-worktree-ownership",
            "phase": "create",
            "owner": "orchestrator-worktree-owner",
            "preconditions": ["attacker can replace the just-created path", "owner marker value is reusable"],
            "evidence": {"scenario": "marker-replacement", "source_paths": ["orchestrator/worktrees.py", "scenarios/attack_simulator.py"], "observed": True},
            "impact": "peer worktree path is accepted as the requesting agent worktree",
            "controls": {
                "preventive": ["bind an unpredictable owner token in an external registry", "verify directory identity with dirfd and no-follow semantics before and after creation"],
                "detective": ["alert when marker inode or resolved worktree identity changes during creation"],
            },
            "negative_test": "interleave marker replacement and require peer path rejection while owned creation succeeds",
            "detection": "record owner-token, inode, and resolved-path transitions",
            "containment": "quarantine the disputed worktree without deleting the peer path",
            "recovery": {"owner": "incident-commander", "steps": ["stop the requesting job", "preserve markers and registry evidence", "recreate with a fresh token"]},
            "residual_risk": "filesystem/kernel race guarantees outside the simulator remain unknown",
        },
        {
            "kind": "bind-option-injection",
            "boundary": "docker-bind-construction",
            "phase": "launch",
            "owner": "container-launcher-owner",
            "preconditions": ["workspace path contains comma or newline", "launcher embeds it in Docker mount option text"],
            "evidence": {"scenario": "bind-comma-newline", "source_paths": ["bin/container-run", "scenarios/attack_simulator.py"], "observed": True},
            "impact": "path data changes the simulated Docker mount option surface",
            "controls": {
                "preventive": ["reject comma and newline in bind source before Docker argv construction", "validate a structured Docker mount argv instead of shell-escaped option text"],
                "detective": ["record normalized bind source and final mount fields before launch"],
            },
            "negative_test": "exercise comma/newline corpus and require rejection before simulated Docker invocation",
            "detection": "alert on unexpected mount fields or line count",
            "containment": "do not launch and preserve the rejected argv evidence",
            "recovery": {"owner": "incident-commander", "steps": ["invalidate the launch", "inspect mount evidence", "retry with an approved workspace path"]},
            "residual_risk": "real Docker parser behavior is not certified by the simulator",
        },
        {
            "kind": "credential-scope-loss",
            "boundary": "provider-credential-scope",
            "phase": "project",
            "owner": "credential-adapter-owner",
            "preconditions": ["projection drops provider/project/agent scope", "another provider accepts the remaining token field"],
            "evidence": {"scenario": "cross-provider-reuse", "source_paths": ["orchestrator/credentials.py", "scenarios/attack_simulator.py"], "observed": True},
            "impact": "a projected credential is reused across provider and agent scope",
            "controls": {
                "preventive": ["preserve provider, project, and agent scope metadata in projection", "issue least-privilege per-scope credentials"],
                "detective": ["compare requested provider/project/agent scope with projection metadata"],
            },
            "negative_test": "cross-provider and cross-agent reuse must fail while matching scope succeeds",
            "detection": "record content-free scope mismatch events",
            "containment": "stop projection and revoke the affected scope",
            "recovery": {"owner": "incident-commander", "steps": ["rotate the affected scoped credential", "revoke projected copies", "audit scope mismatch events"]},
            "residual_risk": "provider-side revocation timing remains unknown",
        },
        {
            "kind": "cleanup-owner-confusion",
            "boundary": "cleanup-ownership",
            "phase": "cleanup",
            "owner": "cleanup-supervisor-owner",
            "preconditions": ["peer reuses expected PID and name", "cleanup treats observations as authorization"],
            "evidence": {"scenario": "pid-name-reuse", "source_paths": ["orchestrator/cleanup.py", "scenarios/attack_simulator.py"], "observed": True},
            "impact": "cleanup authorizes deletion or termination of a peer resource",
            "controls": {
                "preventive": ["authorize cleanup with an unpredictable owner token plus immutable resource identity", "treat PID and name as observations and never authority"],
                "detective": ["alert when owner token, resource identity, PID, and name do not agree"],
            },
            "negative_test": "PID/name reuse with a different owner token must preserve the peer sentinel",
            "detection": "record cleanup authorization tuple and peer-preservation result",
            "containment": "skip ambiguous cleanup and isolate only registry-owned resources",
            "recovery": {"owner": "incident-commander", "steps": ["preserve peer sentinel", "reconcile registry ownership", "retry cleanup by owner token"]},
            "residual_risk": "host PID lifecycle behavior outside the simulator remains unknown",
        },
    ],
    "control_counterexamples": [
        {"single_control": "name validation", "bypass": "PID/name reuse still authorizes peer cleanup without an owner token"},
        {"single_control": "shell escaping", "bypass": "Docker mount comma grammar remains data-driven"},
        {"single_control": "token masking", "bypass": "masked values do not preserve provider/project/agent scope"},
        {"single_control": "read-only rootfs", "bypass": "a mounted host socket is still a host authority boundary"},
    ],
    "unknowns": [
        {"area": "host-kernel", "status": "unknown", "reason": "simulator does not certify kernel race or namespace guarantees"},
        {"area": "docker-daemon", "status": "unknown", "reason": "no daemon or host socket is used"},
        {"area": "provider", "status": "unknown", "reason": "provider revocation and acceptance are simulated"},
    ],
}


def _render_l_model(model: dict[str, Any]) -> str:
    lines = [
        "# Worktree/container threat model",
        "",
        "## Topology",
        "",
        "Assets, actors, boundaries, phases, and owners are defined in `threat-model.json`.",
        "",
    ]
    for threat in model["threats"]:
        lines.extend(
            [
                f"## {threat['kind']}",
                "",
                f"Boundary `{threat['boundary']}`; phase `{threat['phase']}`; owner `{threat['owner']}`.",
                f"Evidence scenario `{threat['evidence']['scenario']}` observes: {threat['impact']}.",
                "",
                "Preconditions: " + "; ".join(threat["preconditions"]) + ".",
                "Preventive controls: " + "; ".join(threat["controls"]["preventive"]) + ".",
                "Detective controls: " + "; ".join(threat["controls"]["detective"]) + ".",
                "Negative test: " + threat["negative_test"] + ".",
                "Detection: " + threat["detection"] + ".",
                "Containment: " + threat["containment"] + ".",
                f"Recovery owner `{threat['recovery']['owner']}`: " + "; ".join(threat["recovery"]["steps"]) + ".",
                "Residual risk: " + threat["residual_risk"] + ".",
                "",
            ]
        )
    lines.extend(["## Control counterexamples", ""])
    for item in model["control_counterexamples"]:
        lines.append(f"- `{item['single_control']}`: {item['bypass']}")
    lines.extend(["", "## Unknowns", ""])
    for item in model["unknowns"]:
        lines.append(f"- `{item['area']}` remains `{item['status']}`: {item['reason']}")
    lines.append("")
    return "\n".join(lines)


L_GOOD_MARKDOWN = _render_l_model(L_GOOD_MODEL)


L_HIDDEN_BODY = r'''def model() -> dict[str, object]:
    try:
        value = json.loads((WORKSPACE / "threat-model.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return value if isinstance(value, dict) else {}


def threats() -> dict[str, dict[str, object]]:
    items = model().get("threats", [])
    return {item.get("kind"): item for item in items if isinstance(item, dict)}


def raw_attacks() -> dict[str, object]:
    completed = subprocess.run(
        ["python3", "scenarios/attack_simulator.py", "--raw"],
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
        timeout=15,
        check=False,
    )
    if completed.returncode != 1:
        raise AssertionError(completed.stdout + completed.stderr)
    return json.loads(completed.stdout)


def controls(kind: str, control_type: str) -> list[str]:
    item = threats().get(kind, {})
    value = item.get("controls", {}).get(control_type, [])
    return value if isinstance(value, list) else []


class HiddenThreatModelTests(unittest.TestCase):
    def setUp(self):
        assert_fixture_integrity(self)

    def test_assets_boundaries(self):
        topology = model().get("topology", {})
        self.assertIsInstance(topology, dict)
        for key in ("assets", "actors", "boundaries", "phases", "owners"):
            self.assertIn(key, topology)
        joined_assets = " ".join(topology.get("assets", [])).lower()
        for term in ("worktree", "bind", "credential", "lifecycle"):
            self.assertIn(term, joined_assets)
        joined_actors = " ".join(topology.get("actors", [])).lower()
        for term in ("orchestrator", "task", "peer", "provider"):
            self.assertIn(term, joined_actors)
        boundaries = set(topology.get("boundaries", []))
        phases = set(topology.get("phases", []))
        owner_values = set(topology.get("owners", {}).values())
        items = threats()
        self.assertEqual(
            set(items),
            {"worktree-marker-race", "bind-option-injection", "credential-scope-loss", "cleanup-owner-confusion"},
        )
        for item in items.values():
            self.assertIn(item.get("boundary"), boundaries)
            self.assertIn(item.get("phase"), phases)
            self.assertIn(item.get("owner"), owner_values)
        self.assertIn("detect", phases)
        self.assertIn("recover", phases)

    def test_worktree_race(self):
        observed = raw_attacks()["observations"]["worktree-marker-race"]
        self.assertEqual(observed, {"observed": True, "scenario": "marker-replacement"})
        item = threats().get("worktree-marker-race", {})
        self.assertEqual(item.get("evidence", {}).get("scenario"), "marker-replacement")
        preventive = " ".join(controls("worktree-marker-race", "preventive")).lower()
        self.assertTrue("owner token" in preventive or "capability" in preventive)
        self.assertTrue(any(term in preventive for term in ("dirfd", "no-follow", "atomic", "rename")))
        self.assertTrue(any(term in preventive for term in ("before and after", "revalid", "post-create", "fence")))
        negative = str(item.get("negative_test", "")).lower()
        self.assertIn("peer", negative)
        self.assertTrue("reject" in negative or "preserv" in negative)

    def test_bind_injection(self):
        observed = raw_attacks()["observations"]["bind-option-injection"]
        self.assertEqual(observed, {"observed": True, "scenario": "bind-comma-newline"})
        preventive = " ".join(controls("bind-option-injection", "preventive")).lower()
        self.assertIn("comma", preventive)
        self.assertIn("newline", preventive)
        self.assertTrue(any(term in preventive for term in ("reject", "encode", "structured")))
        self.assertTrue(any(term in preventive for term in ("docker", "mount", "argv")))
        for raw_path in ("/tmp/safe,readonly", "/tmp/safe\n--privileged"):
            completed = subprocess.run(
                ["bash", "bin/container-run", raw_path],
                cwd=WORKSPACE,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=5,
                check=False,
            )
            self.assertEqual(completed.returncode, 0)
            self.assertTrue(
                ",readonly" in completed.stdout
                or any(line.startswith("--privileged") for line in completed.stdout.splitlines())
            )

    def test_credential_scope(self):
        observed = raw_attacks()["observations"]["credential-scope-loss"]
        self.assertEqual(observed, {"observed": True, "scenario": "cross-provider-reuse"})
        preventive = " ".join(controls("credential-scope-loss", "preventive")).lower()
        for term in ("provider", "project", "agent"):
            self.assertIn(term, preventive)
        self.assertTrue(any(term in preventive for term in ("least-privilege", "least privilege", "minimal", "scoped")))
        recovery = threats()["credential-scope-loss"].get("recovery", {})
        recovery_text = " ".join(recovery.get("steps", [])).lower()
        self.assertIn("rotate", recovery_text)
        self.assertIn("revoke", recovery_text)

    def test_cleanup_ownership(self):
        observed = raw_attacks()["observations"]["cleanup-owner-confusion"]
        self.assertEqual(observed, {"observed": True, "scenario": "pid-name-reuse"})
        preventive = " ".join(controls("cleanup-owner-confusion", "preventive")).lower()
        self.assertTrue("owner token" in preventive or "capability" in preventive)
        self.assertTrue(any(term in preventive for term in ("resource identity", "stable identity", "inode")))
        self.assertIn("pid", preventive)
        self.assertIn("name", preventive)
        self.assertTrue(any(term in preventive for term in ("never authority", "not authority", "observation")))
        negative = str(threats()["cleanup-owner-confusion"].get("negative_test", "")).lower()
        self.assertIn("peer sentinel", negative)
        self.assertIn("different owner token", negative)

    def test_detection_recovery(self):
        for kind, item in threats().items():
            with self.subTest(kind=kind):
                detective = item.get("controls", {}).get("detective", [])
                self.assertIsInstance(detective, list)
                self.assertTrue(all(isinstance(value, str) and value for value in detective))
                self.assertTrue(item.get("detection"))
                self.assertTrue(item.get("containment"))
                recovery = item.get("recovery", {})
                self.assertTrue(recovery.get("owner"))
                self.assertGreaterEqual(len(recovery.get("steps", [])), 2)
                self.assertIn(recovery.get("owner"), set(model()["topology"]["owners"].values()))
        markdown = (WORKSPACE / "THREAT-MODEL.md").read_text(encoding="utf-8")
        for kind in threats():
            self.assertIn(f"## {kind}", markdown)

    def test_control_counterexamples(self):
        items = model().get("control_counterexamples", [])
        self.assertIsInstance(items, list)
        text = "\n".join(str(item).lower() for item in items)
        for term in ("pid", "name", "comma", "provider", "project", "agent", "scope", "host socket"):
            self.assertIn(term, text)
        self.assertTrue("owner token" in text or "capability" in text)
        self.assertTrue("docker" in text or "mount" in text)
        self.assertTrue("read-only" in text or "rootfs" in text)

    def test_unknown_honesty(self):
        unknowns = model().get("unknowns", [])
        self.assertIsInstance(unknowns, list)
        by_area = {item.get("area"): item for item in unknowns if isinstance(item, dict)}
        self.assertEqual(set(by_area), {"host-kernel", "docker-daemon", "provider"})
        self.assertTrue(all(item.get("status") == "unknown" for item in by_area.values()))
        serialized = json.dumps(model(), sort_keys=True).lower()
        self.assertNotIn("read-only rootfs fully isolates", serialized)
        self.assertNotIn("host socket is fully isolated", serialized)
        self.assertNotIn("provider revocation is immediate", serialized)


if __name__ == "__main__":
    unittest.main()
'''


L_HIDDEN = _hidden_with_integrity(
    L_HIDDEN_BODY,
    L_FILES,
    {"THREAT-MODEL.md", "threat-model.json"},
)


L_MUTANT_CHECKLIST = copy.deepcopy(L_GOOD_MODEL)
for _l_threat in L_MUTANT_CHECKLIST["threats"]:
    _l_threat["preconditions"] = []
    _l_threat["negative_test"] = ""
    _l_threat["controls"]["detective"] = []
    _l_threat["detection"] = ""
    _l_threat["recovery"]["steps"] = []

L_MUTANT_CLEANUP = copy.deepcopy(L_GOOD_MODEL)
for _l_threat in L_MUTANT_CLEANUP["threats"]:
    if _l_threat["kind"] == "cleanup-owner-confusion":
        _l_threat["controls"]["preventive"] = ["validate the resource name and compare the observed PID"]
        _l_threat["negative_test"] = "matching PID and name authorize cleanup"

L_MUTANT_CREDENTIAL = copy.deepcopy(L_GOOD_MODEL)
for _l_threat in L_MUTANT_CREDENTIAL["threats"]:
    if _l_threat["kind"] == "credential-scope-loss":
        _l_threat["controls"]["preventive"] = ["mask token values in logs"]
        _l_threat["recovery"]["steps"] = ["mask the token", "retry projection"]

L_MUTANT_BIND = copy.deepcopy(L_GOOD_MODEL)
for _l_threat in L_MUTANT_BIND["threats"]:
    if _l_threat["kind"] == "bind-option-injection":
        _l_threat["controls"]["preventive"] = ["shell-escape the workspace string"]

L_MUTANT_GUARANTEE = copy.deepcopy(L_GOOD_MODEL)
for _l_unknown in L_MUTANT_GUARANTEE["unknowns"]:
    if _l_unknown["area"] == "docker-daemon":
        _l_unknown["status"] = "guaranteed"
        _l_unknown["reason"] = "read-only rootfs fully isolates a mounted host socket"

L_MUTANT_NO_RECOVERY = copy.deepcopy(L_GOOD_MODEL)
for _l_threat in L_MUTANT_NO_RECOVERY["threats"]:
    _l_threat["controls"]["detective"] = []
    _l_threat["detection"] = ""
    _l_threat["containment"] = ""
    _l_threat["recovery"]["steps"] = []


RECIPES: dict[str, dict[str, Any]] = {
    "f09-s-python-name-bypass-v1": {
        "case_id": "F09-S-PY-001",
        "files": S_FILES,
        "hidden": S_HIDDEN,
        "good": {
            "security_regression.py": S_GOOD_REGRESSION,
            "finding.json": _document(S_GOOD_FINDING),
        },
        "executable": [],
        "mutants": {
            "raw-parent-traversal": {
                "files": {
                    "security_regression.py": S_MUTANT_RAW_REGRESSION,
                    "finding.json": _document(S_MUTANT_RAW_FINDING),
                },
                "expected_failed_check_ids": ["security-bypass-recall", "security-negative-test"],
            },
            "validator-only-test": {
                "files": {
                    "security_regression.py": S_MUTANT_VALIDATOR_ONLY,
                    "finding.json": _document(S_GOOD_FINDING),
                },
                "expected_failed_check_ids": ["security-negative-test"],
            },
            "double-decode-claim": {
                "files": {
                    "security_regression.py": S_GOOD_REGRESSION,
                    "finding.json": _document(S_MUTANT_DOUBLE_FINDING),
                },
                "expected_failed_check_ids": ["security-no-double-decode"],
            },
            "unbounded-traversal-impact": {
                "files": {
                    "security_regression.py": S_GOOD_REGRESSION,
                    "finding.json": _document(S_MUTANT_UNBOUNDED_FINDING),
                },
                "expected_failed_check_ids": ["security-impact-scope"],
            },
        },
    },
    "f09-m-workspace-isolation-review-v1": {
        "case_id": "F09-M-PYBASH-001",
        "files": M_FILES,
        "hidden": M_HIDDEN,
        "good": {
            "security-review.json": _document(M_GOOD_REVIEW),
            "security_regression.py": M_GOOD_REGRESSION,
        },
        "executable": ["bin/run-task", "isolation/paths.py"],
        "mutants": {
            "symlink-only": {
                "files": {
                    "security-review.json": _document(M_MUTANT_SYMLINK_REVIEW),
                    "security_regression.py": M_MUTANT_SYMLINK_REGRESSION,
                },
                "expected_failed_check_ids": ["security-env-root-exploit", "security-composition", "security-mitigation-invariants"],
            },
            "environment-only": {
                "files": {
                    "security-review.json": _document(M_MUTANT_ENV_REVIEW),
                    "security_regression.py": M_MUTANT_ENV_REGRESSION,
                },
                "expected_failed_check_ids": ["security-symlink-exploit", "security-composition", "security-mitigation-invariants"],
            },
            "reject-all-symlinks": {
                "files": {
                    "security-review.json": _document(M_MUTANT_REJECT_SYMLINK_REVIEW),
                    "security_regression.py": M_MUTANT_REJECT_SYMLINK_REGRESSION,
                },
                "expected_failed_check_ids": ["security-negative-tests", "security-no-false-positive"],
            },
            "privileged-reproduction": {
                "files": {
                    "security-review.json": _document(M_MUTANT_PRIVILEGE_REVIEW),
                    "security_regression.py": M_GOOD_REGRESSION,
                },
                "expected_failed_check_ids": ["security-negative-tests"],
            },
        },
    },
    "f09-l-worktree-container-threat-model-v1": {
        "case_id": "F09-L-PYBASHDOCKER-001",
        "files": L_FILES,
        "hidden": L_HIDDEN,
        "good": {
            "THREAT-MODEL.md": L_GOOD_MARKDOWN,
            "threat-model.json": _document(L_GOOD_MODEL),
        },
        "executable": [
            "bin/container-run",
            "scenarios/attack_simulator.py",
            "scenarios/run-visible-attacks.sh",
        ],
        "mutants": {
            "threat-checklist-only": {
                "files": {
                    "THREAT-MODEL.md": _render_l_model(L_MUTANT_CHECKLIST),
                    "threat-model.json": _document(L_MUTANT_CHECKLIST),
                },
                "expected_failed_check_ids": ["threat-detection-recovery"],
            },
            "pid-name-cleanup-authority": {
                "files": {
                    "THREAT-MODEL.md": _render_l_model(L_MUTANT_CLEANUP),
                    "threat-model.json": _document(L_MUTANT_CLEANUP),
                },
                "expected_failed_check_ids": ["threat-cleanup-ownership"],
            },
            "masked-token-without-scope": {
                "files": {
                    "THREAT-MODEL.md": _render_l_model(L_MUTANT_CREDENTIAL),
                    "threat-model.json": _document(L_MUTANT_CREDENTIAL),
                },
                "expected_failed_check_ids": ["threat-credential-scope"],
            },
            "shell-escape-bind-control": {
                "files": {
                    "THREAT-MODEL.md": _render_l_model(L_MUTANT_BIND),
                    "threat-model.json": _document(L_MUTANT_BIND),
                },
                "expected_failed_check_ids": ["threat-bind-injection"],
            },
            "read-only-rootfs-guarantee": {
                "files": {
                    "THREAT-MODEL.md": _render_l_model(L_MUTANT_GUARANTEE),
                    "threat-model.json": _document(L_MUTANT_GUARANTEE),
                },
                "expected_failed_check_ids": ["threat-unknown-honesty"],
            },
            "prevention-without-recovery": {
                "files": {
                    "THREAT-MODEL.md": _render_l_model(L_MUTANT_NO_RECOVERY),
                    "threat-model.json": _document(L_MUTANT_NO_RECOVERY),
                },
                "expected_failed_check_ids": ["threat-detection-recovery"],
            },
        },
    },
}


__all__ = ["RECIPES"]
