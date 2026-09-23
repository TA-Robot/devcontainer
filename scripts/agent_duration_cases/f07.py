"""Deterministic documentation/runbook duration-study fixtures."""

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
import unittest


WORKSPACE = Path(os.environ["DURATION_FIXTURE_WORKSPACE"])
PROTECTED_DIGESTS = {protected!r}
ALLOWED_ARTIFACTS = {sorted(editable_paths)!r}


def assert_fixture_integrity(testcase: unittest.TestCase) -> None:
    for raw_path, expected in PROTECTED_DIGESTS.items():
        path = WORKSPACE / raw_path
        testcase.assertTrue(path.is_file(), f"protected file is missing: {{raw_path}}")
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        testcase.assertEqual(actual, expected, f"protected file changed: {{raw_path}}")
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


S_AGENTCTL = r'''#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


def workspace_is_contained(current: Path, requested: Path) -> bool:
    try:
        requested.resolve().relative_to(current.resolve())
    except ValueError:
        return False
    return True


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="agentctl")
    commands = parser.add_subparsers(dest="command", required=True)
    doctor = commands.add_parser("doctor")
    doctor.add_argument("--json", action="store_true", dest="as_json")
    doctor.add_argument("--workspace", type=Path, default=Path("."))
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    current = Path.cwd()
    if not workspace_is_contained(current, args.workspace):
        print("workspace path must remain inside the current workspace", file=sys.stderr)
        return 2
    result = {"status": "ok", "workspace": str(args.workspace.resolve())}
    if args.as_json:
        print(json.dumps(result, sort_keys=True))
    else:
        print("doctor: ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
'''


S_TESTS = r'''from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]


class AgentctlTests(unittest.TestCase):
    def run_cli(self, *arguments: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(ROOT / "agentctl.py"), *arguments],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=5,
            check=False,
        )

    def test_doctor_json_and_workspace_are_subcommand_options(self):
        completed = self.run_cli("doctor", "--json", "--workspace", ".")
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(json.loads(completed.stdout)["status"], "ok")
        obsolete = self.run_cli("--workspace", ".", "doctor")
        self.assertNotEqual(obsolete.returncode, 0)

    def test_outside_workspace_is_rejected(self):
        with tempfile.TemporaryDirectory() as raw:
            completed = self.run_cli("doctor", "--json", "--workspace", raw)
        self.assertEqual(completed.returncode, 2)
        self.assertIn("inside the current workspace", completed.stderr)


if __name__ == "__main__":
    unittest.main()
'''


S_CHECK_DOCS = r'''#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
import re
import sys


FACT_BLOCK = re.compile(r"```doc-facts\s*\n(.*?)\n```", re.DOTALL)
LINK = re.compile(r"\[[^]]+\]\(([^)]+)\)")


def main() -> int:
    if len(sys.argv) != 2:
        return 2
    path = Path(sys.argv[1])
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        print(exc, file=sys.stderr)
        return 1
    commands = [line[2:].strip() for line in text.splitlines() if line.startswith("$ ")]
    if "agentctl doctor --json" not in commands:
        print("existing JSON doctor example is missing", file=sys.stderr)
        return 1
    if "agentctl doctor --json --workspace ." not in commands:
        print("replayable workspace doctor example is missing", file=sys.stderr)
        return 1
    if any(command.startswith("agentctl --workspace") for command in commands):
        print("obsolete option order remains", file=sys.stderr)
        return 1
    match = FACT_BLOCK.search(text)
    if match is None:
        print("doc-facts block is missing", file=sys.stderr)
        return 1
    try:
        manifest = json.loads(match.group(1))
    except json.JSONDecodeError as exc:
        print(exc, file=sys.stderr)
        return 1
    facts = manifest.get("facts") if isinstance(manifest, dict) else None
    if not isinstance(facts, list) or len(facts) != 1:
        return 1
    fact = facts[0]
    if not isinstance(fact, dict) or not all(
        key in fact for key in ("claim_id", "text", "source")
    ):
        return 1
    if fact["text"] not in text:
        print("fact text and prose are not synchronized", file=sys.stderr)
        return 1
    for target in LINK.findall(text):
        if target.startswith(("http://", "https://", "#")):
            continue
        link_path = (path.parent / target.split("#", 1)[0]).resolve()
        if not link_path.is_file():
            print(f"broken local link: {target}", file=sys.stderr)
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
'''


S_FILES = {
    "AGENTS.md": AGENT_INSTRUCTIONS,
    "agentctl.py": S_AGENTCTL,
    "README.md": r'''# agentctl

Use [the CLI parser](agentctl.py) as the command reference.

## Doctor

JSON output is available:

```console
$ agentctl doctor --json
```

The workspace form still uses the obsolete global-option order:

```console
$ agentctl --workspace . doctor
```
''',
    "tests/__init__.py": "",
    "tests/test_cli.py": S_TESTS,
    "tools/check_docs.py": S_CHECK_DOCS,
}


S_FACT_TEXT = (
    "`--workspace` must resolve inside the current workspace; paths outside "
    "that boundary are rejected."
)
S_GOOD_README = f'''# agentctl

Use [the CLI parser](agentctl.py) as the command reference.

## Doctor

JSON output is available:

```console
$ agentctl doctor --json
```

Pass a contained workspace after the `doctor` subcommand:

```console
$ agentctl doctor --json --workspace .
```

{S_FACT_TEXT}

```doc-facts
{{
  "facts": [
    {{
      "claim_id": "doctor-workspace-boundary",
      "source": {{
        "path": "agentctl.py",
        "symbols": ["build_parser", "workspace_is_contained"]
      }},
      "text": {json.dumps(S_FACT_TEXT)}
    }}
  ]
}}
```
'''


S_HIDDEN_BODY = r'''import ast
import re
import shlex


FACT_BLOCK = re.compile(r"```doc-facts\s*\n(.*?)\n```", re.DOTALL)
LINK = re.compile(r"\[[^]]+\]\(([^)]+)\)")


def read_doc() -> tuple[str, dict[str, object]]:
    text = (WORKSPACE / "README.md").read_text(encoding="utf-8")
    match = FACT_BLOCK.search(text)
    if match is None:
        return text, {}
    try:
        value = json.loads(match.group(1))
    except json.JSONDecodeError:
        value = {}
    return text, value if isinstance(value, dict) else {}


class HiddenDoctorDocTests(unittest.TestCase):
    def setUp(self):
        assert_fixture_integrity(self)

    def test_command_replay(self):
        text, _ = read_doc()
        commands = [line[2:].strip() for line in text.splitlines() if line.startswith("$ ")]
        command = "agentctl doctor --json --workspace ."
        self.assertIn(command, commands)
        argv = shlex.split(command)
        self.assertEqual(argv[0], "agentctl")
        completed = subprocess.run(
            [os.environ.get("PYTHON", "python3"), "agentctl.py", *argv[1:]],
            cwd=WORKSPACE,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=5,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        result = json.loads(completed.stdout)
        self.assertEqual(result.get("status"), "ok")
        self.assertEqual(Path(result["workspace"]), WORKSPACE.resolve())

    def test_constraint_accurate(self):
        text, manifest = read_doc()
        facts = manifest.get("facts", [])
        self.assertIsInstance(facts, list)
        self.assertEqual(len(facts), 1)
        fact = facts[0]
        self.assertIsInstance(fact.get("claim_id"), str)
        self.assertTrue(fact["claim_id"])
        claim = fact.get("text")
        self.assertIsInstance(claim, str)
        self.assertIn(claim, text)
        normalized = claim.lower()
        self.assertIn("--workspace", normalized)
        self.assertIn("current workspace", normalized)
        self.assertRegex(normalized, r"inside|within|contain")
        self.assertRegex(normalized, r"reject|error|fail")
        source = fact.get("source", {})
        self.assertEqual(source.get("path"), "agentctl.py")
        self.assertEqual(
            set(source.get("symbols", [])),
            {"build_parser", "workspace_is_contained"},
        )
        tree = ast.parse((WORKSPACE / source["path"]).read_text(encoding="utf-8"))
        symbols = {node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)}
        self.assertTrue(set(source["symbols"]).issubset(symbols))
        outside = subprocess.run(
            ["python3", "agentctl.py", "doctor", "--json", "--workspace", str(WORKSPACE.parent)],
            cwd=WORKSPACE,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=5,
            check=False,
        )
        self.assertEqual(outside.returncode, 2)
        self.assertNotIn("--allow-outside-workspace", text)

    def test_invalid_form_removed(self):
        text, _ = read_doc()
        self.assertNotRegex(text, r"agentctl\s+--workspace\s+\S+\s+doctor")

    def test_link_integrity(self):
        text, _ = read_doc()
        targets = LINK.findall(text)
        self.assertIn("agentctl.py", targets)
        for target in targets:
            if target.startswith(("http://", "https://", "#")):
                continue
            path = (WORKSPACE / target.split("#", 1)[0]).resolve()
            path.relative_to(WORKSPACE.resolve())
            self.assertTrue(path.is_file(), target)


if __name__ == "__main__":
    unittest.main()
'''


S_HIDDEN = _hidden_with_integrity(S_HIDDEN_BODY, S_FILES, {"README.md"})


S_MUTANT_ORDER_ONLY = r'''# agentctl

Use [the CLI parser](agentctl.py) as the command reference.

## Doctor

```console
$ agentctl doctor --json
$ agentctl doctor --json --workspace .
```
'''

S_MUTANT_PLACEHOLDER = S_GOOD_README.replace(
    "agentctl doctor --json --workspace .",
    "agentctl doctor --json --workspace <PATH>",
)

S_FALSE_BYPASS_TEXT = (
    "`--workspace` may point outside the current workspace when "
    "`--allow-outside-workspace` is supplied."
)
S_MUTANT_FALSE_BYPASS = S_GOOD_README.replace(S_FACT_TEXT, S_FALSE_BYPASS_TEXT)


M_STATE_DOCTOR = r'''#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path


EXIT_CORRUPT = 3
EXIT_MISSING = 4


def inspect_state(path: Path) -> tuple[int, dict[str, object]]:
    if not path.is_file():
        return EXIT_MISSING, {"status": "missing"}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return EXIT_CORRUPT, {"status": "corrupt", "reason": "invalid-json"}
    if not isinstance(value, dict) or value.get("version") != 1 or not isinstance(value.get("records"), list):
        return EXIT_CORRUPT, {"status": "corrupt", "reason": "invalid-schema"}
    return 0, {"status": "healthy", "records": len(value["records"])}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--state", type=Path, required=True)
    args = parser.parse_args()
    status, result = inspect_state(args.state)
    print(json.dumps(result, sort_keys=True))
    return status


if __name__ == "__main__":
    raise SystemExit(main())
'''


M_STATE_BACKUP = r'''#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import os
from pathlib import Path
import shutil
import tempfile


EXIT_INVALID_BACKUP = 5


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def create_backup(state: Path, backup: Path, digest_path: Path) -> int:
    if not state.is_file():
        return EXIT_INVALID_BACKUP
    shutil.copyfile(state, backup)
    digest_path.write_text(digest(backup) + "\n", encoding="utf-8")
    return 0


def preserve_evidence(state: Path, evidence: Path) -> int:
    if not state.is_file():
        return EXIT_INVALID_BACKUP
    shutil.copyfile(state, evidence)
    return 0


def verify_backup(backup: Path, digest_path: Path) -> int:
    if not backup.is_file() or not digest_path.is_file():
        return EXIT_INVALID_BACKUP
    expected = digest_path.read_text(encoding="utf-8").strip()
    if len(expected) != 64 or digest(backup) != expected:
        return EXIT_INVALID_BACKUP
    return 0


def restore_backup(backup: Path, digest_path: Path, state: Path) -> int:
    if verify_backup(backup, digest_path) != 0:
        return EXIT_INVALID_BACKUP
    state.parent.mkdir(parents=True, exist_ok=True)
    descriptor, raw_temporary = tempfile.mkstemp(prefix=f".{state.name}.", dir=state.parent)
    temporary = Path(raw_temporary)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(backup.read_bytes())
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, state)
    finally:
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    commands = parser.add_subparsers(dest="command", required=True)
    create = commands.add_parser("create")
    preserve = commands.add_parser("preserve")
    verify = commands.add_parser("verify")
    restore = commands.add_parser("restore")
    for command in (create, verify, restore):
        command.add_argument("--backup", type=Path, required=True)
        command.add_argument("--digest", type=Path, required=True)
    create.add_argument("--state", type=Path, required=True)
    preserve.add_argument("--state", type=Path, required=True)
    preserve.add_argument("--evidence", type=Path, required=True)
    restore.add_argument("--state", type=Path, required=True)
    args = parser.parse_args()
    if args.command == "create":
        return create_backup(args.state, args.backup, args.digest)
    if args.command == "preserve":
        return preserve_evidence(args.state, args.evidence)
    if args.command == "verify":
        return verify_backup(args.backup, args.digest)
    return restore_backup(args.backup, args.digest, args.state)


if __name__ == "__main__":
    raise SystemExit(main())
'''


M_SERVICE_CONTROL = r'''#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path


OWNED_SERVICE = "state-worker"


def healthy_state(path: Path) -> bool:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False
    return isinstance(value, dict) and value.get("version") == 1 and isinstance(value.get("records"), list)


def main() -> int:
    parser = argparse.ArgumentParser()
    commands = parser.add_subparsers(dest="command", required=True)
    restart = commands.add_parser("restart")
    health = commands.add_parser("health")
    for command in (restart, health):
        command.add_argument("--service", required=True)
        command.add_argument("--health", type=Path, required=True)
    restart.add_argument("--state", type=Path, required=True)
    args = parser.parse_args()
    if args.service != OWNED_SERVICE:
        return 6
    if args.command == "restart":
        if not healthy_state(args.state):
            return 7
        generation = 1
        if args.health.is_file():
            generation = json.loads(args.health.read_text(encoding="utf-8")).get("generation", 0) + 1
        args.health.write_text(
            json.dumps(
                {"generation": generation, "service": OWNED_SERVICE, "status": "healthy"},
                sort_keys=True,
                separators=(",", ":"),
            ) + "\n",
            encoding="utf-8",
        )
        return 0
    if not args.health.is_file():
        return 7
    value = json.loads(args.health.read_text(encoding="utf-8"))
    return 0 if value.get("service") == OWNED_SERVICE and value.get("status") == "healthy" else 7


if __name__ == "__main__":
    raise SystemExit(main())
'''


M_CHECK_RUNBOOK = r'''#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
import shlex
import sys


REQUIRED_STEPS = [
    "diagnose",
    "preserve-evidence",
    "verify-backup",
    "restore",
    "restart-owned-service",
    "verify-state",
    "verify-health",
]
ALLOWED_PROGRAMS = {"python3", "bin/state-backup", "bin/service-control"}


def main() -> int:
    if len(sys.argv) != 3:
        return 2
    markdown_path = Path(sys.argv[1])
    manifest_path = Path(sys.argv[2])
    try:
        markdown = markdown_path.read_text(encoding="utf-8")
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(exc, file=sys.stderr)
        return 1
    if not isinstance(manifest, dict) or manifest.get("version") != 1:
        return 1
    steps = manifest.get("steps")
    if not isinstance(steps, list):
        return 1
    ids = [step.get("id") for step in steps if isinstance(step, dict)]
    if ids != REQUIRED_STEPS:
        print("runbook steps do not match the required recovery lifecycle", file=sys.stderr)
        return 1
    commands = [line[2:].strip() for line in markdown.splitlines() if line.startswith("$ ")]
    expected_commands = []
    seen: set[str] = set()
    for step in steps:
        argv = step.get("argv")
        dependencies = step.get("depends_on")
        if not isinstance(argv, list) or not argv or not all(isinstance(item, str) for item in argv):
            return 1
        if argv[0] not in ALLOWED_PROGRAMS:
            print(f"unsupported runbook command: {argv[0]}", file=sys.stderr)
            return 1
        if not isinstance(dependencies, list) or any(item not in seen for item in dependencies):
            print("runbook dependency order is invalid", file=sys.stderr)
            return 1
        seen.add(step["id"])
        expected_commands.append(shlex.join(argv))
    if commands != expected_commands:
        print("Markdown commands and manifest argv differ", file=sys.stderr)
        return 1
    facts = manifest.get("facts")
    if not isinstance(facts, list) or len(facts) < 3:
        return 1
    branches = manifest.get("failure_branches")
    if not isinstance(branches, list) or {item.get("scenario") for item in branches if isinstance(item, dict)} != {"missing-backup", "invalid-backup"}:
        return 1
    if "docs/STATE.md#state-contract" not in markdown:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
'''


M_REPLAY_PY = r'''#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[1]
SCENARIOS = {"healthy", "corrupt", "missing-backup", "invalid-backup"}


def digest(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def substitute(argv: list[str], paths: dict[str, Path]) -> list[str]:
    return [str(paths.get(item[1:-1], item)) if item.startswith("{") and item.endswith("}") else item for item in argv]


def validate_command(argv: object) -> bool:
    if not isinstance(argv, list) or not argv or not all(isinstance(item, str) for item in argv):
        return False
    allowed = {
        ("python3", "tools/state-doctor.py"),
        ("bin/state-backup", "preserve"),
        ("bin/state-backup", "verify"),
        ("bin/state-backup", "restore"),
        ("bin/service-control", "restart"),
        ("bin/service-control", "health"),
    }
    return len(argv) >= 2 and tuple(argv[:2]) in allowed


def run(manifest: dict[str, object], scenario: str) -> dict[str, object]:
    steps = manifest.get("steps")
    if not isinstance(steps, list) or not all(isinstance(step, dict) for step in steps):
        raise ValueError("steps must be objects")
    if not all(validate_command(step.get("argv")) for step in steps):
        raise ValueError("manifest contains an unsupported command")
    branches = {
        item.get("scenario"): item
        for item in manifest.get("failure_branches", [])
        if isinstance(item, dict)
    }
    healthy = b'{"records":["alpha","beta"],"version":1}\n'
    corrupt = b'{not-json\n'
    with tempfile.TemporaryDirectory(prefix="f07-state-replay-") as raw:
        sandbox = Path(raw)
        paths = {
            "STATE": sandbox / "state.json",
            "BACKUP": sandbox / "state.backup.json",
            "DIGEST": sandbox / "state.backup.sha256",
            "EVIDENCE": sandbox / "state.corrupt.evidence",
            "HEALTH": sandbox / "state-worker.health.json",
        }
        initial = healthy if scenario == "healthy" else corrupt
        paths["STATE"].write_bytes(initial)
        if scenario != "missing-backup":
            backup_bytes = healthy if scenario != "invalid-backup" else b'{"records":[],"version":1}\n'
            paths["BACKUP"].write_bytes(backup_bytes)
            expected_digest = digest(healthy)
            paths["DIGEST"].write_text(expected_digest + "\n", encoding="utf-8")
        peer = sandbox / "peer-service.sentinel"
        peer.write_bytes(b"peer-alive\n")
        peer_before = digest(peer.read_bytes())
        state_before = digest(paths["STATE"].read_bytes())
        records: list[dict[str, object]] = []
        stopped_at = None
        completed_ids: set[str] = set()
        for step in steps:
            dependencies = step.get("depends_on")
            if not isinstance(dependencies, list) or any(item not in completed_ids for item in dependencies):
                raise ValueError("dependency is not satisfied")
            expected_map = step.get("expect")
            if not isinstance(expected_map, dict) or scenario not in expected_map:
                if scenario in {"missing-backup", "invalid-backup"} and stopped_at is not None:
                    break
                raise ValueError("scenario expectation is missing")
            argv = substitute(step["argv"], paths)
            environment = {
                "PATH": os.environ.get("PATH", "/usr/local/bin:/usr/bin:/bin"),
                "PYTHONDONTWRITEBYTECODE": "1",
                "PYTHONPATH": str(ROOT),
                "TZ": "UTC",
            }
            completed = subprocess.run(
                argv,
                cwd=ROOT,
                env=environment,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=5,
                check=False,
            )
            records.append({"id": step["id"], "exit": completed.returncode})
            if completed.returncode != expected_map[scenario]:
                raise RuntimeError(f"unexpected exit for {step['id']}")
            completed_ids.add(step["id"])
            if completed.returncode != 0 and scenario in {"missing-backup", "invalid-backup"} and step["id"] == "verify-backup":
                branch = branches.get(scenario, {})
                if branch.get("abort_after") != step["id"]:
                    raise RuntimeError("failure branch stopped at the wrong step")
                stopped_at = step["id"]
                break
        peer_after = digest(peer.read_bytes())
        evidence_digest = digest(paths["EVIDENCE"].read_bytes()) if paths["EVIDENCE"].is_file() else None
        state_after = digest(paths["STATE"].read_bytes())
        health = None
        if paths["HEALTH"].is_file():
            health = json.loads(paths["HEALTH"].read_text(encoding="utf-8"))
        if scenario in {"missing-backup", "invalid-backup"}:
            if stopped_at != "verify-backup" or state_after != state_before or evidence_digest != state_before or health is not None:
                raise RuntimeError("negative recovery branch changed protected state")
            status = "aborted-safe"
        else:
            state_value = json.loads(paths["STATE"].read_text(encoding="utf-8"))
            if state_value.get("version") != 1 or health is None or health.get("status") != "healthy":
                raise RuntimeError("recovery postcondition is incomplete")
            status = "recovered"
        if peer_before != peer_after:
            raise RuntimeError("peer service sentinel changed")
        return {
            "evidence_digest": evidence_digest,
            "health": health,
            "peer_after": peer_after,
            "peer_before": peer_before,
            "records": records,
            "state_after": state_after,
            "state_before": state_before,
            "status": status,
            "stopped_at": stopped_at,
        }


def main() -> int:
    if len(sys.argv) != 3 or sys.argv[2] not in SCENARIOS:
        return 2
    try:
        manifest = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
        result = run(manifest, sys.argv[2])
    except (OSError, ValueError, RuntimeError, json.JSONDecodeError, subprocess.TimeoutExpired) as exc:
        print(json.dumps({"status": "replay-error", "error": str(exc)}, sort_keys=True))
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
'''


M_FILES = {
    "AGENTS.md": AGENT_INSTRUCTIONS,
    "tools/state-doctor.py": M_STATE_DOCTOR,
    "bin/state-backup": M_STATE_BACKUP,
    "bin/service-control": M_SERVICE_CONTROL,
    "docs/STATE.md": r'''# State contract

## State contract

Version 1 state is a JSON object with a `records` array. `state-doctor.py`
returns 3 for corruption and does not modify the state file. Backup verification
returns 5 when the backup or digest is missing or mismatched. The only service
owned by this repository is `state-worker`.
''',
    "tools/check_runbook.py": M_CHECK_RUNBOOK,
    "tools/replay_runbook.py": M_REPLAY_PY,
    "tools/replay_runbook.sh": r'''#!/usr/bin/env bash
set -euo pipefail

if [[ "$#" -ne 2 ]]; then
  echo "usage: replay_runbook.sh MANIFEST SCENARIO" >&2
  exit 2
fi
exec python3 tools/replay_runbook.py "$1" "$2"
''',
}


M_GOOD_MANIFEST: dict[str, Any] = {
    "version": 1,
    "facts": [
        {
            "id": "doctor-corrupt-exit",
            "value": 3,
            "source": {"path": "tools/state-doctor.py", "symbol": "EXIT_CORRUPT"},
        },
        {
            "id": "invalid-backup-exit",
            "value": 5,
            "source": {"path": "bin/state-backup", "symbol": "EXIT_INVALID_BACKUP"},
        },
        {
            "id": "owned-service",
            "value": "state-worker",
            "source": {"path": "bin/service-control", "symbol": "OWNED_SERVICE"},
        },
        {
            "id": "atomic-restore",
            "value": "os.replace",
            "source": {"path": "bin/state-backup", "symbol": "restore_backup"},
        },
    ],
    "steps": [
        {
            "id": "diagnose",
            "phase": "diagnosis",
            "argv": ["python3", "tools/state-doctor.py", "--state", "{STATE}"],
            "depends_on": [],
            "expect": {"healthy": 0, "corrupt": 3, "missing-backup": 3, "invalid-backup": 3},
        },
        {
            "id": "preserve-evidence",
            "phase": "evidence",
            "argv": ["bin/state-backup", "preserve", "--state", "{STATE}", "--evidence", "{EVIDENCE}"],
            "depends_on": ["diagnose"],
            "expect": {"healthy": 0, "corrupt": 0, "missing-backup": 0, "invalid-backup": 0},
        },
        {
            "id": "verify-backup",
            "phase": "verification",
            "argv": ["bin/state-backup", "verify", "--backup", "{BACKUP}", "--digest", "{DIGEST}"],
            "depends_on": ["preserve-evidence"],
            "expect": {"healthy": 0, "corrupt": 0, "missing-backup": 5, "invalid-backup": 5},
        },
        {
            "id": "restore",
            "phase": "mutation",
            "argv": ["bin/state-backup", "restore", "--backup", "{BACKUP}", "--digest", "{DIGEST}", "--state", "{STATE}"],
            "depends_on": ["verify-backup"],
            "expect": {"healthy": 0, "corrupt": 0},
        },
        {
            "id": "restart-owned-service",
            "phase": "restart",
            "argv": ["bin/service-control", "restart", "--service", "state-worker", "--state", "{STATE}", "--health", "{HEALTH}"],
            "depends_on": ["restore"],
            "expect": {"healthy": 0, "corrupt": 0},
        },
        {
            "id": "verify-state",
            "phase": "postcondition",
            "argv": ["python3", "tools/state-doctor.py", "--state", "{STATE}"],
            "depends_on": ["restart-owned-service"],
            "expect": {"healthy": 0, "corrupt": 0},
        },
        {
            "id": "verify-health",
            "phase": "postcondition",
            "argv": ["bin/service-control", "health", "--service", "state-worker", "--health", "{HEALTH}"],
            "depends_on": ["verify-state"],
            "expect": {"healthy": 0, "corrupt": 0},
        },
    ],
    "failure_branches": [
        {
            "scenario": "missing-backup",
            "abort_after": "verify-backup",
            "preserve": ["{STATE}", "{EVIDENCE}"],
        },
        {
            "scenario": "invalid-backup",
            "abort_after": "verify-backup",
            "preserve": ["{STATE}", "{EVIDENCE}"],
        },
    ],
}


def _render_m_runbook(manifest: dict[str, Any]) -> str:
    lines = [
        "# State corruption recovery",
        "",
        "Use the [state contract](docs/STATE.md#state-contract) for exit codes and ownership.",
        "Diagnosis and evidence capture happen before any restore. A missing or invalid",
        "backup stops after verification; keep both `{STATE}` and `{EVIDENCE}` unchanged.",
        "The verified restore is atomic, and only `state-worker` is restarted before",
        "state and service health are checked.",
        "",
    ]
    for step in manifest["steps"]:
        lines.extend(
            [
                f"## {step['id']}",
                "",
                f"Phase: `{step['phase']}`.",
                "",
                "```console",
                "$ " + __import__("shlex").join(step["argv"]),
                "```",
                "",
            ]
        )
    lines.extend(
        [
            "## Failure branches",
            "",
            "For `missing-backup` and `invalid-backup`, exit 5 from `verify-backup`",
            "is a safe stop. Do not restore, restart, delete state, or discard evidence.",
            "",
        ]
    )
    return "\n".join(lines)


M_GOOD_RUNBOOK = _render_m_runbook(M_GOOD_MANIFEST)


M_HIDDEN_BODY = r'''import ast
import shlex


def manifest() -> dict[str, object]:
    try:
        value = json.loads((WORKSPACE / "runbook.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return value if isinstance(value, dict) else {}


def replay(scenario: str) -> dict[str, object]:
    completed = subprocess.run(
        ["python3", "tools/replay_runbook.py", "runbook.json", scenario],
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
    if completed.returncode != 0:
        raise AssertionError(completed.stdout + completed.stderr)
    return json.loads(completed.stdout)


def source_symbols(path: str) -> tuple[dict[str, object], set[str]]:
    tree = ast.parse((WORKSPACE / path).read_text(encoding="utf-8"))
    constants: dict[str, object] = {}
    functions: set[str] = set()
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            functions.add(node.name)
        elif isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            try:
                constants[node.targets[0].id] = ast.literal_eval(node.value)
            except (ValueError, TypeError):
                pass
    return constants, functions


class HiddenStateRunbookTests(unittest.TestCase):
    def setUp(self):
        assert_fixture_integrity(self)

    def test_fact_accuracy(self):
        facts = manifest().get("facts", [])
        self.assertIsInstance(facts, list)
        self.assertEqual(len(facts), 4)
        by_source = {
            (item.get("source", {}).get("path"), item.get("source", {}).get("symbol")): item
            for item in facts
            if isinstance(item, dict) and isinstance(item.get("source"), dict)
        }
        expected = {
            ("tools/state-doctor.py", "EXIT_CORRUPT"): 3,
            ("bin/state-backup", "EXIT_INVALID_BACKUP"): 5,
            ("bin/service-control", "OWNED_SERVICE"): "state-worker",
            ("bin/state-backup", "restore_backup"): "os.replace",
        }
        self.assertEqual(set(by_source), set(expected))
        for (path, symbol), value in expected.items():
            fact = by_source[(path, symbol)]
            self.assertEqual(fact.get("value"), value)
            self.assertEqual(fact.get("source"), {"path": path, "symbol": symbol})
            constants, functions = source_symbols(path)
            if symbol == "restore_backup":
                self.assertIn(symbol, functions)
                function_source = (WORKSPACE / path).read_text(encoding="utf-8")
                self.assertIn("os.replace(temporary, state)", function_source)
            else:
                self.assertEqual(constants.get(symbol), value)

    def test_order_safety(self):
        steps = manifest().get("steps", [])
        self.assertIsInstance(steps, list)
        ids = [item.get("id") for item in steps if isinstance(item, dict)]
        self.assertEqual(
            ids,
            [
                "diagnose",
                "preserve-evidence",
                "verify-backup",
                "restore",
                "restart-owned-service",
                "verify-state",
                "verify-health",
            ],
        )
        positions = {step_id: index for index, step_id in enumerate(ids)}
        for step in steps:
            for dependency in step.get("depends_on", []):
                self.assertLess(positions[dependency], positions[step["id"]])
        commands = [step.get("argv", []) for step in steps]
        flattened = "\n".join(shlex.join(command) for command in commands if isinstance(command, list))
        self.assertNotRegex(flattened, r"(?:^|\s)(?:rm|unlink|restart-all)(?:\s|$)")

    def test_corrupt_recovery(self):
        result = replay("corrupt")
        self.assertEqual(result.get("status"), "recovered")
        self.assertEqual(result.get("health", {}).get("service"), "state-worker")
        self.assertEqual(result.get("health", {}).get("status"), "healthy")
        self.assertEqual(
            [item.get("id") for item in result.get("records", [])],
            [
                "diagnose",
                "preserve-evidence",
                "verify-backup",
                "restore",
                "restart-owned-service",
                "verify-state",
                "verify-health",
            ],
        )
        self.assertNotEqual(result.get("state_before"), result.get("state_after"))
        self.assertEqual(result.get("evidence_digest"), result.get("state_before"))

    def test_invalid_backup(self):
        for scenario in ("missing-backup", "invalid-backup"):
            with self.subTest(scenario=scenario):
                result = replay(scenario)
                self.assertEqual(result.get("status"), "aborted-safe")
                self.assertEqual(result.get("stopped_at"), "verify-backup")
                self.assertEqual(result.get("state_after"), result.get("state_before"))
                self.assertEqual(result.get("evidence_digest"), result.get("state_before"))
                self.assertIsNone(result.get("health"))

    def test_owned_restart(self):
        result = replay("healthy")
        self.assertEqual(result.get("peer_before"), result.get("peer_after"))
        self.assertEqual(result.get("health", {}).get("service"), "state-worker")
        steps = manifest().get("steps", [])
        restart = next(step for step in steps if step.get("id") == "restart-owned-service")
        self.assertEqual(
            restart.get("argv"),
            [
                "bin/service-control",
                "restart",
                "--service",
                "state-worker",
                "--state",
                "{STATE}",
                "--health",
                "{HEALTH}",
            ],
        )

    def test_doc_manifest_sync(self):
        markdown = (WORKSPACE / "RUNBOOK.md").read_text(encoding="utf-8")
        documented = [line[2:].strip() for line in markdown.splitlines() if line.startswith("$ ")]
        steps = manifest().get("steps", [])
        declared = [shlex.join(step.get("argv", [])) for step in steps if isinstance(step, dict)]
        self.assertEqual(documented, declared)
        self.assertIn("docs/STATE.md#state-contract", markdown)


if __name__ == "__main__":
    unittest.main()
'''


M_HIDDEN = _hidden_with_integrity(
    M_HIDDEN_BODY,
    M_FILES,
    {"RUNBOOK.md", "runbook.json"},
)


M_MUTANT_DESTRUCTIVE = copy.deepcopy(M_GOOD_MANIFEST)
M_MUTANT_DESTRUCTIVE["steps"].insert(
    0,
    {
        "id": "delete-state",
        "phase": "mutation",
        "argv": ["rm", "{STATE}"],
        "depends_on": [],
        "expect": {"healthy": 0, "corrupt": 0, "missing-backup": 0, "invalid-backup": 0},
    },
)

M_MUTANT_VERIFY_AFTER = copy.deepcopy(M_GOOD_MANIFEST)
_m_verify_steps = M_MUTANT_VERIFY_AFTER["steps"]
_m_verify = _m_verify_steps.pop(2)
_m_restore = _m_verify_steps[2]
_m_restore["depends_on"] = ["preserve-evidence"]
_m_verify["depends_on"] = ["restore"]
_m_verify_steps.insert(3, _m_verify)
_m_verify_steps[4]["depends_on"] = ["verify-backup"]

M_MUTANT_NO_HEALTH = copy.deepcopy(M_GOOD_MANIFEST)
M_MUTANT_NO_HEALTH["steps"] = [
    step for step in M_MUTANT_NO_HEALTH["steps"] if step["id"] != "verify-health"
]

M_MUTANT_PLACEHOLDER_RUNBOOK = M_GOOD_RUNBOOK.replace(
    "python3 tools/state-doctor.py --state '{STATE}'",
    "python3 tools/state-doctor.py --state '$STATE'",
    1,
)


L_BACKEND = r'''from __future__ import annotations


CURRENT_BACKEND = "legacy-json"
TARGET_BACKEND = "sqlite-v2"
COMPATIBILITY_MODE = "dual-read-write"
OWNERS = {
    "runtime": "runtime-backend",
    "migration": "migration-controller",
    "cleanup": "migration-controller",
    "recovery": "oncall-storage",
}
'''


L_MIGRATION = r'''from __future__ import annotations

import json
import os
from pathlib import Path
import tempfile

from .backend import CURRENT_BACKEND, TARGET_BACKEND


COMPAT_REMOVAL_EVIDENCE = (
    "two-successful-verifications",
    "rollback-drill",
    "zero-mixed-version-readers",
)


def initial_state() -> dict[str, object]:
    return {
        "active_backend": CURRENT_BACKEND,
        "compat_enabled": True,
        "legacy_records": ["alpha", "beta"],
        "mixed_version_readers": 1,
        "phase": "current",
        "rollback_drill": False,
        "target_records": [],
        "verification_runs": 0,
    }


def load_state(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("migration state must be an object")
    return value


def save_state(path: Path, value: dict[str, object]) -> None:
    descriptor, raw_temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary = Path(raw_temporary)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(value, handle, sort_keys=True, separators=(",", ":"))
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass


def prepare(path: Path) -> None:
    state = load_state(path)
    state["target_records"] = list(state["legacy_records"])
    state["phase"] = "dual-write"
    save_state(path, state)


def compat_read(path: Path) -> None:
    state = load_state(path)
    if not state["compat_enabled"] or state["legacy_records"] != state["target_records"]:
        raise ValueError("compatibility read is unavailable")


def verify(path: Path) -> None:
    state = load_state(path)
    if state["legacy_records"] != state["target_records"]:
        raise ValueError("backend records differ")
    state["verification_runs"] = int(state["verification_runs"]) + 1
    save_state(path, state)


def cutover(path: Path) -> None:
    state = load_state(path)
    if state["phase"] != "dual-write" or int(state["verification_runs"]) < 2:
        raise ValueError("cutover requires dual-write and two successful verifications")
    state["active_backend"] = TARGET_BACKEND
    state["phase"] = "cutover"
    save_state(path, state)


def abort(path: Path) -> None:
    state = load_state(path)
    state["active_backend"] = CURRENT_BACKEND
    state["phase"] = "aborted"
    save_state(path, state)


def export_rollback(path: Path, output: Path) -> None:
    if output.exists():
        raise ValueError("rollback export already exists")
    output.write_bytes(path.read_bytes())


def rollback(path: Path, exported: Path) -> None:
    exported_state = load_state(exported)
    if exported_state.get("active_backend") != TARGET_BACKEND:
        raise ValueError("rollback export does not describe the cutover state")
    state = load_state(path)
    state["active_backend"] = CURRENT_BACKEND
    state["phase"] = "rolled-back"
    save_state(path, state)


def record_rollback_drill(path: Path) -> None:
    state = load_state(path)
    state["rollback_drill"] = True
    save_state(path, state)


def mark_readers_upgraded(path: Path) -> None:
    state = load_state(path)
    state["mixed_version_readers"] = 0
    save_state(path, state)


def cleanup_compat(path: Path) -> None:
    state = load_state(path)
    if (
        state["active_backend"] != TARGET_BACKEND
        or int(state["verification_runs"]) < 2
        or state["rollback_drill"] is not True
        or int(state["mixed_version_readers"]) != 0
    ):
        raise ValueError("compatibility removal evidence is incomplete")
    state["compat_enabled"] = False
    state["phase"] = "compat-removed"
    save_state(path, state)
'''


L_BACKENDCTL = r'''#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.migration import (  # noqa: E402
    abort,
    cleanup_compat,
    compat_read,
    cutover,
    export_rollback,
    load_state,
    mark_readers_upgraded,
    prepare,
    record_rollback_drill,
    rollback,
    verify,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    commands = parser.add_subparsers(dest="command", required=True)
    names = (
        "status",
        "prepare",
        "compat-read",
        "verify",
        "cutover",
        "abort",
        "export-rollback",
        "rollback",
        "record-rollback-drill",
        "mark-readers-upgraded",
        "cleanup-compat",
    )
    parsers = {name: commands.add_parser(name) for name in names}
    for command in parsers.values():
        command.add_argument("--state", type=Path, required=True)
    parsers["export-rollback"].add_argument("--output", type=Path, required=True)
    parsers["rollback"].add_argument("--export", type=Path, required=True)
    args = parser.parse_args()
    try:
        if args.command == "status":
            state = load_state(args.state)
            print(json.dumps({"active_backend": state["active_backend"], "compat_enabled": state["compat_enabled"], "phase": state["phase"]}, sort_keys=True))
        elif args.command == "prepare":
            prepare(args.state)
        elif args.command == "compat-read":
            compat_read(args.state)
        elif args.command == "verify":
            verify(args.state)
        elif args.command == "cutover":
            cutover(args.state)
        elif args.command == "abort":
            abort(args.state)
        elif args.command == "export-rollback":
            export_rollback(args.state, args.output)
        elif args.command == "rollback":
            rollback(args.state, args.export)
        elif args.command == "record-rollback-drill":
            record_rollback_drill(args.state)
        elif args.command == "mark-readers-upgraded":
            mark_readers_upgraded(args.state)
        else:
            cleanup_compat(args.state)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(str(exc), file=sys.stderr)
        return 8
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
'''


L_CHECK_INDEX = r'''#!/usr/bin/env python3
from __future__ import annotations

import ast
import json
from pathlib import Path
import shlex
import sys


ALLOWED_PROGRAM = "bin/backendctl"
REQUIRED_SCENARIOS = {"upgrade", "mixed-version", "interrupted", "rollback", "cleanup"}


def anchors(text: str) -> set[str]:
    result: set[str] = set()
    for line in text.splitlines():
        if not line.startswith("#"):
            continue
        heading = line.lstrip("#").strip().lower()
        slug = "-".join("".join(character for character in word if character.isalnum()) for word in heading.split())
        result.add(slug)
    return result


def main() -> int:
    if len(sys.argv) != 2:
        return 2
    try:
        index = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(exc, file=sys.stderr)
        return 1
    if not isinstance(index, dict) or index.get("version") != 1:
        return 1
    documents = index.get("documents")
    facts = index.get("facts")
    commands = index.get("commands")
    scenarios = index.get("scenarios")
    if not all(isinstance(item, list) for item in (documents, facts, commands)) or not isinstance(scenarios, dict):
        return 1
    if {item.get("path") for item in documents if isinstance(item, dict)} != {"docs/ARCHITECTURE.md", "docs/MIGRATION.md", "docs/RECOVERY.md"}:
        return 1
    document_text: dict[str, str] = {}
    document_anchors: dict[str, set[str]] = {}
    for item in documents:
        path = Path(item["path"])
        if not path.is_file():
            return 1
        text = path.read_text(encoding="utf-8")
        document_text[item["path"]] = text
        document_anchors[item["path"]] = anchors(text)
        if not set(item.get("anchors", [])).issubset(document_anchors[item["path"]]):
            return 1
    command_ids: set[str] = set()
    documented: list[str] = []
    for path in sorted(document_text):
        documented.extend(line[2:].strip() for line in document_text[path].splitlines() if line.startswith("$ "))
    declared: list[str] = []
    for command in commands:
        if not isinstance(command, dict) or command.get("id") in command_ids:
            return 1
        command_ids.add(command["id"])
        argv = command.get("argv")
        if not isinstance(argv, list) or len(argv) < 3 or argv[0] != ALLOWED_PROGRAM:
            return 1
        if command.get("document") not in document_text or command.get("anchor") not in document_anchors[command["document"]]:
            return 1
        if not isinstance(command.get("depends_on"), list) or any(item not in command_ids for item in command["depends_on"]):
            return 1
        declared.append(shlex.join(argv))
    if sorted(documented) != sorted(declared):
        print("documented and indexed commands differ", file=sys.stderr)
        return 1
    if set(scenarios) != REQUIRED_SCENARIOS or any(
        not isinstance(items, list) or any(item not in command_ids for item in items)
        for items in scenarios.values()
    ):
        return 1
    for fact in facts:
        if not isinstance(fact, dict):
            return 1
        source = fact.get("source", {})
        if not isinstance(source, dict) or not Path(source.get("path", "")).is_file():
            return 1
        references = fact.get("documents")
        if not isinstance(references, list) or not references:
            return 1
        for reference in references:
            if reference.get("path") not in document_text or reference.get("anchor") not in document_anchors[reference["path"]]:
                return 1
    gate = index.get("removal_gate")
    if not isinstance(gate, dict) or not isinstance(gate.get("requires"), list):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
'''


L_CHECK_LINKS = r'''#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import re
import sys


LINK = re.compile(r"\[[^]]+\]\(([^)]+)\)")


def anchors(text: str) -> set[str]:
    result: set[str] = set()
    for line in text.splitlines():
        if line.startswith("#"):
            heading = line.lstrip("#").strip().lower()
            result.add("-".join("".join(c for c in word if c.isalnum()) for word in heading.split()))
    return result


def main() -> int:
    if len(sys.argv) != 2:
        return 2
    root = Path(sys.argv[1])
    if not root.is_dir():
        return 1
    for source in root.glob("*.md"):
        text = source.read_text(encoding="utf-8")
        for target in LINK.findall(text):
            if target.startswith(("http://", "https://")):
                continue
            raw_path, separator, anchor = target.partition("#")
            destination = source if not raw_path else source.parent / raw_path
            if not destination.is_file():
                print(f"broken link in {source}: {target}", file=sys.stderr)
                return 1
            if separator and anchor not in anchors(destination.read_text(encoding="utf-8")):
                print(f"broken anchor in {source}: {target}", file=sys.stderr)
                return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
'''


L_REPLAY_PY = r'''#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[1]
EXPECTED_SCENARIOS = {"upgrade", "mixed-version", "interrupted", "rollback", "cleanup"}


def digest(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def initial_state() -> dict[str, object]:
    return {
        "active_backend": "legacy-json",
        "compat_enabled": True,
        "legacy_records": ["alpha", "beta"],
        "mixed_version_readers": 1,
        "phase": "current",
        "rollback_drill": False,
        "target_records": [],
        "verification_runs": 0,
    }


def substitute(argv: list[str], state: Path, exported: Path) -> list[str]:
    values = {"{STATE}": str(state), "{EXPORT}": str(exported)}
    return [values.get(item, item) for item in argv]


def execute(command: dict[str, object], state: Path, exported: Path) -> None:
    argv = command.get("argv")
    if not isinstance(argv, list) or len(argv) < 3 or argv[0] != "bin/backendctl":
        raise ValueError("unsupported migration command")
    completed = subprocess.run(
        substitute(argv, state, exported),
        cwd=ROOT,
        env={
            "PATH": os.environ.get("PATH", "/usr/local/bin:/usr/bin:/bin"),
            "PYTHONPATH": str(ROOT),
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
        raise RuntimeError(f"{command.get('id')} failed: {completed.stderr.strip()}")


def replay_scenario(index: dict[str, object], scenario: str) -> dict[str, object]:
    commands = {item["id"]: item for item in index["commands"] if isinstance(item, dict)}
    command_ids = index["scenarios"][scenario]
    with tempfile.TemporaryDirectory(prefix=f"f07-migration-{scenario}-") as raw:
        root = Path(raw)
        state = root / "migration-state.json"
        exported = root / "rollback-export.json"
        state.write_text(json.dumps(initial_state(), sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
        legacy_before = digest(json.dumps(initial_state()["legacy_records"], separators=(",", ":")).encode("utf-8"))
        export_source_digest = None
        export_unchanged = None
        for command_id in command_ids:
            command = commands.get(command_id)
            if command is None:
                raise ValueError("scenario references an unknown command")
            if command_id == "export-rollback":
                before = state.read_bytes()
                execute(command, state, exported)
                export_source_digest = digest(before)
                export_unchanged = state.read_bytes() == before and exported.read_bytes() == before
            else:
                execute(command, state, exported)
        value = json.loads(state.read_text(encoding="utf-8"))
        legacy_after = digest(json.dumps(value["legacy_records"], separators=(",", ":")).encode("utf-8"))
        expected = {
            "upgrade": ("sqlite-v2", "cutover", True),
            "mixed-version": ("legacy-json", "dual-write", True),
            "interrupted": ("legacy-json", "aborted", True),
            "rollback": ("legacy-json", "rolled-back", True),
            "cleanup": ("sqlite-v2", "compat-removed", False),
        }[scenario]
        observed = (value["active_backend"], value["phase"], value["compat_enabled"])
        if observed != expected or legacy_before != legacy_after:
            raise RuntimeError(f"scenario postcondition mismatch: {scenario}")
        if scenario in {"mixed-version", "interrupted", "rollback"} and value["target_records"] != value["legacy_records"]:
            raise RuntimeError("compatibility or recovery lost a backend copy")
        if scenario == "rollback" and not export_unchanged:
            raise RuntimeError("rollback export was destructive or incomplete")
        return {
            "active_backend": value["active_backend"],
            "compat_enabled": value["compat_enabled"],
            "export_source_digest": export_source_digest,
            "export_unchanged": export_unchanged,
            "legacy_after": legacy_after,
            "legacy_before": legacy_before,
            "phase": value["phase"],
            "status": "pass",
        }


def early_removal_probe(index: dict[str, object]) -> dict[str, object]:
    commands = {item["id"]: item for item in index["commands"] if isinstance(item, dict)}
    with tempfile.TemporaryDirectory(prefix="f07-early-removal-") as raw:
        root = Path(raw)
        state = root / "migration-state.json"
        exported = root / "unused-export.json"
        state.write_text(json.dumps(initial_state(), sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
        for command_id in ("prepare", "verify-first", "verify-second", "cutover"):
            execute(commands[command_id], state, exported)
        before = state.read_bytes()
        command = commands["cleanup-compat"]
        completed = subprocess.run(
            substitute(command["argv"], state, exported),
            cwd=ROOT,
            env={"PATH": os.environ.get("PATH", "/usr/local/bin:/usr/bin:/bin"), "PYTHONPATH": str(ROOT), "PYTHONDONTWRITEBYTECODE": "1"},
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=5,
            check=False,
        )
        after = state.read_bytes()
        if completed.returncode != 8 or before != after:
            raise RuntimeError("early compatibility removal was not rejected safely")
        return {"exit": completed.returncode, "preserved": before == after, "status": "blocked"}


def main() -> int:
    if len(sys.argv) != 2:
        return 2
    try:
        index = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
        if set(index.get("scenarios", {})) != EXPECTED_SCENARIOS:
            raise ValueError("scenario set is incomplete")
        results = {name: replay_scenario(index, name) for name in sorted(EXPECTED_SCENARIOS)}
        results["early-removal"] = early_removal_probe(index)
    except (OSError, ValueError, RuntimeError, KeyError, json.JSONDecodeError, subprocess.TimeoutExpired) as exc:
        print(json.dumps({"status": "replay-error", "error": str(exc)}, sort_keys=True))
        return 1
    print(json.dumps({"scenarios": results, "status": "pass"}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
'''


L_FILES = {
    "AGENTS.md": AGENT_INSTRUCTIONS,
    "src/__init__.py": "",
    "src/backend.py": L_BACKEND,
    "src/migration.py": L_MIGRATION,
    "bin/backendctl": L_BACKENDCTL,
    "docs/ARCHITECTURE.md": r'''# Architecture

## Current and target

The service reads a direct JSON file as its permanent backend. A future backend
may be selected later.

## Ownership

Runtime code owns migration cleanup.
''',
    "docs/MIGRATION.md": r'''# Migration

## Staged rollout

Prepare the new backend and cut over immediately. The compatibility shim may be
removed as soon as the first process starts.
''',
    "tools/check_docs_index.py": L_CHECK_INDEX,
    "tools/check_links.py": L_CHECK_LINKS,
    "tools/replay_migration_docs.py": L_REPLAY_PY,
    "tools/replay_migration_docs.sh": r'''#!/usr/bin/env bash
set -euo pipefail

if [[ "$#" -ne 1 ]]; then
  echo "usage: replay_migration_docs.sh INDEX" >&2
  exit 2
fi
exec python3 tools/replay_migration_docs.py "$1"
''',
}


L_GOOD_INDEX: dict[str, Any] = {
    "version": 1,
    "documents": [
        {"path": "docs/ARCHITECTURE.md", "anchors": ["current-and-target", "compatibility-window", "ownership"]},
        {"path": "docs/MIGRATION.md", "anchors": ["staged-rollout", "interrupted-rollout", "compatibility-removal", "ownership"]},
        {"path": "docs/RECOVERY.md", "anchors": ["rollback-recovery", "ownership"]},
    ],
    "facts": [
        {
            "id": "current-backend",
            "value": "legacy-json",
            "source": {"path": "src/backend.py", "symbol": "CURRENT_BACKEND"},
            "documents": [
                {"path": "docs/ARCHITECTURE.md", "anchor": "current-and-target"},
                {"path": "docs/MIGRATION.md", "anchor": "staged-rollout"},
            ],
        },
        {
            "id": "target-backend",
            "value": "sqlite-v2",
            "source": {"path": "src/backend.py", "symbol": "TARGET_BACKEND"},
            "documents": [
                {"path": "docs/ARCHITECTURE.md", "anchor": "current-and-target"},
                {"path": "docs/MIGRATION.md", "anchor": "staged-rollout"},
                {"path": "docs/RECOVERY.md", "anchor": "rollback-recovery"},
            ],
        },
        {
            "id": "compatibility-mode",
            "value": "dual-read-write",
            "source": {"path": "src/backend.py", "symbol": "COMPATIBILITY_MODE"},
            "documents": [
                {"path": "docs/ARCHITECTURE.md", "anchor": "compatibility-window"},
                {"path": "docs/MIGRATION.md", "anchor": "staged-rollout"},
            ],
        },
    ],
    "owners": [
        {"responsibility": "runtime", "owner": "runtime-backend", "source": {"path": "src/backend.py", "symbol": "OWNERS"}},
        {"responsibility": "migration", "owner": "migration-controller", "source": {"path": "src/backend.py", "symbol": "OWNERS"}},
        {"responsibility": "cleanup", "owner": "migration-controller", "source": {"path": "src/backend.py", "symbol": "OWNERS"}},
        {"responsibility": "recovery", "owner": "oncall-storage", "source": {"path": "src/backend.py", "symbol": "OWNERS"}},
    ],
    "commands": [
        {"id": "status-current", "phase": "inspect", "argv": ["bin/backendctl", "status", "--state", "{STATE}"], "depends_on": [], "document": "docs/ARCHITECTURE.md", "anchor": "current-and-target"},
        {"id": "prepare", "phase": "prepare", "argv": ["bin/backendctl", "prepare", "--state", "{STATE}"], "depends_on": [], "document": "docs/MIGRATION.md", "anchor": "staged-rollout"},
        {"id": "compat-read", "phase": "compatibility", "argv": ["bin/backendctl", "compat-read", "--state", "{STATE}"], "depends_on": ["prepare"], "document": "docs/ARCHITECTURE.md", "anchor": "compatibility-window"},
        {"id": "verify-first", "phase": "verify", "argv": ["bin/backendctl", "verify", "--state", "{STATE}"], "depends_on": ["prepare"], "document": "docs/MIGRATION.md", "anchor": "staged-rollout"},
        {"id": "verify-second", "phase": "verify", "argv": ["bin/backendctl", "verify", "--state", "{STATE}"], "depends_on": ["verify-first"], "document": "docs/MIGRATION.md", "anchor": "staged-rollout"},
        {"id": "cutover", "phase": "cutover", "argv": ["bin/backendctl", "cutover", "--state", "{STATE}"], "depends_on": ["verify-second"], "document": "docs/MIGRATION.md", "anchor": "staged-rollout"},
        {"id": "abort", "phase": "abort", "argv": ["bin/backendctl", "abort", "--state", "{STATE}"], "depends_on": ["prepare"], "document": "docs/MIGRATION.md", "anchor": "interrupted-rollout"},
        {"id": "export-rollback", "phase": "export", "argv": ["bin/backendctl", "export-rollback", "--state", "{STATE}", "--output", "{EXPORT}"], "depends_on": ["cutover"], "document": "docs/RECOVERY.md", "anchor": "rollback-recovery"},
        {"id": "rollback", "phase": "rollback", "argv": ["bin/backendctl", "rollback", "--state", "{STATE}", "--export", "{EXPORT}"], "depends_on": ["export-rollback"], "document": "docs/RECOVERY.md", "anchor": "rollback-recovery"},
        {"id": "record-drill", "phase": "evidence", "argv": ["bin/backendctl", "record-rollback-drill", "--state", "{STATE}"], "depends_on": ["cutover"], "document": "docs/MIGRATION.md", "anchor": "compatibility-removal"},
        {"id": "readers-upgraded", "phase": "evidence", "argv": ["bin/backendctl", "mark-readers-upgraded", "--state", "{STATE}"], "depends_on": ["cutover"], "document": "docs/MIGRATION.md", "anchor": "compatibility-removal"},
        {"id": "cleanup-compat", "phase": "cleanup", "argv": ["bin/backendctl", "cleanup-compat", "--state", "{STATE}"], "depends_on": ["verify-second", "record-drill", "readers-upgraded"], "document": "docs/MIGRATION.md", "anchor": "compatibility-removal"},
    ],
    "scenarios": {
        "upgrade": ["status-current", "prepare", "verify-first", "verify-second", "cutover"],
        "mixed-version": ["prepare", "compat-read"],
        "interrupted": ["prepare", "abort"],
        "rollback": ["prepare", "verify-first", "verify-second", "cutover", "export-rollback", "rollback"],
        "cleanup": ["prepare", "verify-first", "verify-second", "cutover", "record-drill", "readers-upgraded", "cleanup-compat"],
    },
    "removal_gate": {
        "command_id": "cleanup-compat",
        "requires": ["two-successful-verifications", "rollback-drill", "zero-mixed-version-readers"],
        "source": {"path": "src/migration.py", "symbol": "COMPAT_REMOVAL_EVIDENCE"},
    },
}


L_OWNER_TABLE = '''| Responsibility | Owner |
| --- | --- |
| runtime | runtime-backend |
| migration | migration-controller |
| cleanup | migration-controller |
| recovery | oncall-storage |'''


def _l_commands(index: dict[str, Any], path: str, anchor: str) -> str:
    import shlex

    lines: list[str] = []
    for command in index["commands"]:
        if command["document"] == path and command["anchor"] == anchor:
            lines.extend(["```console", "$ " + shlex.join(command["argv"]), "```", ""])
    return "\n".join(lines).rstrip()


def _render_l_documents(index: dict[str, Any]) -> dict[str, str]:
    architecture = f'''# Architecture

## Current and target

The current default backend is `legacy-json`; the staged target is `sqlite-v2`.
The runtime remains on the current backend until the documented cutover gate.

{_l_commands(index, "docs/ARCHITECTURE.md", "current-and-target")}

See the [staged rollout](MIGRATION.md#staged-rollout) and
[rollback recovery](RECOVERY.md#rollback-recovery).

## Compatibility window

During migration the `dual-read-write` compatibility mode keeps legacy and
target records available to mixed-version readers. It remains enabled through
verification, cutover, and rollback readiness.

{_l_commands(index, "docs/ARCHITECTURE.md", "compatibility-window")}

## Ownership

{L_OWNER_TABLE}
'''
    migration = f'''# Migration

## Staged rollout

Migrate `legacy-json` to `sqlite-v2` with `dual-read-write` compatibility,
completing two successful verifications, and only then cutting over.

{_l_commands(index, "docs/MIGRATION.md", "staged-rollout")}

Architecture context is in [current and target](ARCHITECTURE.md#current-and-target).

## Interrupted rollout

Abort returns service to `legacy-json` while preserving the prepared target
copy for diagnosis. It does not delete either backend.

{_l_commands(index, "docs/MIGRATION.md", "interrupted-rollout")}

For a post-cutover reversal, use [rollback recovery](RECOVERY.md#rollback-recovery).

## Compatibility removal

Compatibility removal remains blocked until two successful verifications, a
rollback drill, and zero mixed-version readers are all recorded.

{_l_commands(index, "docs/MIGRATION.md", "compatibility-removal")}

## Ownership

{L_OWNER_TABLE}
'''
    recovery = f'''# Recovery

## Rollback recovery

Before rollback, export the complete `sqlite-v2` cutover state. The export is a
non-destructive evidence copy; rollback changes the active backend to
`legacy-json` while retaining both the target copy and export.

{_l_commands(index, "docs/RECOVERY.md", "rollback-recovery")}

Review [architecture ownership](ARCHITECTURE.md#ownership) and the
[staged rollout](MIGRATION.md#staged-rollout) before acting.

## Ownership

{L_OWNER_TABLE}
'''
    return {
        "docs/ARCHITECTURE.md": architecture,
        "docs/MIGRATION.md": migration,
        "docs/RECOVERY.md": recovery,
    }


L_GOOD_DOCS = _render_l_documents(L_GOOD_INDEX)


L_HIDDEN_BODY = r'''import ast
import shlex
from collections import Counter


def index() -> dict[str, object]:
    try:
        value = json.loads((WORKSPACE / "docs-index.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return value if isinstance(value, dict) else {}


def source_constants(path: str) -> dict[str, object]:
    tree = ast.parse((WORKSPACE / path).read_text(encoding="utf-8"))
    result: dict[str, object] = {}
    for node in tree.body:
        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            target = node.targets[0] if isinstance(node, ast.Assign) and len(node.targets) == 1 else getattr(node, "target", None)
            if not isinstance(target, ast.Name):
                continue
            try:
                result[target.id] = ast.literal_eval(node.value)
            except (ValueError, TypeError):
                pass
    return result


def replay() -> dict[str, object]:
    completed = subprocess.run(
        ["python3", "tools/replay_migration_docs.py", "docs-index.json"],
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
        timeout=25,
        check=False,
    )
    if completed.returncode != 0:
        raise AssertionError(completed.stdout + completed.stderr)
    return json.loads(completed.stdout)


def markdown_anchors(path: Path) -> set[str]:
    anchors: set[str] = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("#"):
            heading = line.lstrip("#").strip().lower()
            anchors.add("-".join("".join(c for c in word if c.isalnum()) for word in heading.split()))
    return anchors


class HiddenMigrationDocsTests(unittest.TestCase):
    def setUp(self):
        assert_fixture_integrity(self)

    def test_current_target_facts(self):
        facts = index().get("facts", [])
        self.assertIsInstance(facts, list)
        self.assertEqual(len(facts), 3)
        by_source = {
            (item.get("source", {}).get("path"), item.get("source", {}).get("symbol")): item
            for item in facts
            if isinstance(item, dict) and isinstance(item.get("source"), dict)
        }
        expected = {
            ("src/backend.py", "CURRENT_BACKEND"): "legacy-json",
            ("src/backend.py", "TARGET_BACKEND"): "sqlite-v2",
            ("src/backend.py", "COMPATIBILITY_MODE"): "dual-read-write",
        }
        self.assertEqual(set(by_source), set(expected))
        constants = source_constants("src/backend.py")
        for (source_path, symbol), value in expected.items():
            fact = by_source[(source_path, symbol)]
            self.assertEqual(fact.get("value"), value)
            self.assertEqual(fact.get("source"), {"path": source_path, "symbol": symbol})
            self.assertEqual(constants.get(symbol), value)
            references = fact.get("documents", [])
            self.assertTrue(references)
            for reference in references:
                path = WORKSPACE / reference["path"]
                self.assertIn(reference["anchor"], markdown_anchors(path))
                self.assertIn(value, path.read_text(encoding="utf-8"))
    def test_migration_order(self):
        value = index()
        commands = value.get("commands", [])
        self.assertIsInstance(commands, list)
        by_id = {item.get("id"): item for item in commands if isinstance(item, dict)}
        self.assertEqual(len(by_id), len(commands))
        expected_subcommands = Counter(
            {
                "status": 1,
                "prepare": 1,
                "compat-read": 1,
                "verify": 2,
                "cutover": 1,
                "abort": 1,
                "export-rollback": 1,
                "rollback": 1,
                "record-rollback-drill": 1,
                "mark-readers-upgraded": 1,
                "cleanup-compat": 1,
            }
        )
        expected_phases = {
            "status": "inspect",
            "prepare": "prepare",
            "compat-read": "compatibility",
            "verify": "verify",
            "cutover": "cutover",
            "abort": "abort",
            "export-rollback": "export",
            "rollback": "rollback",
            "record-rollback-drill": "evidence",
            "mark-readers-upgraded": "evidence",
            "cleanup-compat": "cleanup",
        }
        observed_subcommands = Counter()
        for command in commands:
            argv = command.get("argv", [])
            self.assertGreaterEqual(len(argv), 2)
            subcommand = argv[1]
            observed_subcommands[subcommand] += 1
            self.assertEqual(command.get("phase"), expected_phases[subcommand])
        self.assertEqual(observed_subcommands, expected_subcommands)
        scenarios = value.get("scenarios", {})
        scenario_commands = {
            name: [by_id[command_id]["argv"][1] for command_id in command_ids]
            for name, command_ids in scenarios.items()
        }
        self.assertEqual(
            scenario_commands,
            {
                "upgrade": ["status", "prepare", "verify", "verify", "cutover"],
                "mixed-version": ["prepare", "compat-read"],
                "interrupted": ["prepare", "abort"],
                "rollback": ["prepare", "verify", "verify", "cutover", "export-rollback", "rollback"],
                "cleanup": [
                    "prepare",
                    "verify",
                    "verify",
                    "cutover",
                    "record-rollback-drill",
                    "mark-readers-upgraded",
                    "cleanup-compat",
                ],
            },
        )
        results = replay()["scenarios"]
        self.assertEqual(results["upgrade"]["phase"], "cutover")
        self.assertEqual(results["mixed-version"]["phase"], "dual-write")
        self.assertEqual(results["interrupted"]["phase"], "aborted")

    def test_rollback_nondestructive(self):
        result = replay()["scenarios"]["rollback"]
        self.assertEqual(result.get("status"), "pass")
        self.assertEqual(result.get("active_backend"), "legacy-json")
        self.assertEqual(result.get("phase"), "rolled-back")
        self.assertIs(result.get("export_unchanged"), True)
        self.assertEqual(result.get("legacy_before"), result.get("legacy_after"))
        self.assertIsNotNone(result.get("export_source_digest"))

    def test_ownership_consistency(self):
        owners = index().get("owners", [])
        self.assertIsInstance(owners, list)
        matrix = {item.get("responsibility"): item.get("owner") for item in owners if isinstance(item, dict)}
        expected = {
            "runtime": "runtime-backend",
            "migration": "migration-controller",
            "cleanup": "migration-controller",
            "recovery": "oncall-storage",
        }
        self.assertEqual(matrix, expected)
        self.assertEqual(source_constants("src/backend.py").get("OWNERS"), expected)
        for raw_path in ("docs/ARCHITECTURE.md", "docs/MIGRATION.md", "docs/RECOVERY.md"):
            lines = (WORKSPACE / raw_path).read_text(encoding="utf-8").lower().splitlines()
            for responsibility, owner in expected.items():
                self.assertTrue(
                    any(responsibility in line and owner in line for line in lines),
                    f"{raw_path} does not associate {responsibility} with {owner}",
                )

    def test_command_replay(self):
        result = replay()
        self.assertEqual(result.get("status"), "pass")
        scenarios = result.get("scenarios", {})
        for scenario in ("upgrade", "mixed-version", "interrupted", "rollback", "cleanup"):
            self.assertEqual(scenarios.get(scenario, {}).get("status"), "pass")
        self.assertEqual(scenarios.get("cleanup", {}).get("compat_enabled"), False)

    def test_links_index(self):
        for command in (
            ["python3", "tools/check_docs_index.py", "docs-index.json"],
            ["python3", "tools/check_links.py", "docs"],
        ):
            completed = subprocess.run(
                command,
                cwd=WORKSPACE,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=8,
                check=False,
            )
            self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        documents = index().get("documents", [])
        self.assertEqual(
            {item.get("path") for item in documents if isinstance(item, dict)},
            {"docs/ARCHITECTURE.md", "docs/MIGRATION.md", "docs/RECOVERY.md"},
        )

    def test_no_early_removal(self):
        value = index()
        gate = value.get("removal_gate", {})
        commands = {
            item.get("id"): item for item in value.get("commands", []) if isinstance(item, dict)
        }
        command = commands.get(gate.get("command_id"), {})
        self.assertEqual(command.get("argv", [None, None])[1], "cleanup-compat")
        required_evidence = {
            "two-successful-verifications",
            "rollback-drill",
            "zero-mixed-version-readers",
        }
        self.assertEqual(set(gate.get("requires", [])), required_evidence)
        self.assertEqual(gate.get("source"), {"path": "src/migration.py", "symbol": "COMPAT_REMOVAL_EVIDENCE"})
        self.assertEqual(
            set(source_constants("src/migration.py").get("COMPAT_REMOVAL_EVIDENCE", ())),
            required_evidence,
        )
        result = replay()["scenarios"]["early-removal"]
        self.assertEqual(result, {"exit": 8, "preserved": True, "status": "blocked"})
        migration = (WORKSPACE / "docs/MIGRATION.md").read_text(encoding="utf-8").lower().replace("-", " ")
        for term in ("compatib", "remov", "two", "verif", "rollback", "drill", "zero", "mixed", "reader"):
            self.assertIn(term, migration)


if __name__ == "__main__":
    unittest.main()
'''


L_HIDDEN = _hidden_with_integrity(
    L_HIDDEN_BODY,
    L_FILES,
    {
        "docs/ARCHITECTURE.md",
        "docs/MIGRATION.md",
        "docs/RECOVERY.md",
        "docs-index.json",
    },
)


L_MUTANT_STALE_DOCS = copy.deepcopy(L_GOOD_DOCS)
L_MUTANT_STALE_DOCS["docs/ARCHITECTURE.md"] = L_MUTANT_STALE_DOCS[
    "docs/ARCHITECTURE.md"
].replace(
    "The current default backend is `legacy-json`; the staged target is `sqlite-v2`.",
    "The current default backend is direct-file; a target will be chosen later.",
)

L_MUTANT_DESTRUCTIVE_INDEX = copy.deepcopy(L_GOOD_INDEX)
for _l_command in L_MUTANT_DESTRUCTIVE_INDEX["commands"]:
    if _l_command["id"] == "export-rollback":
        _l_command["argv"] = ["rm", "{STATE}"]
L_MUTANT_DESTRUCTIVE_DOCS = _render_l_documents(L_MUTANT_DESTRUCTIVE_INDEX)

L_MUTANT_WRONG_PHASE_INDEX = copy.deepcopy(L_GOOD_INDEX)
for _l_command in L_MUTANT_WRONG_PHASE_INDEX["commands"]:
    if _l_command["id"] == "cutover":
        _l_command["phase"] = "prepare"
L_MUTANT_WRONG_PHASE_DOCS = _render_l_documents(L_MUTANT_WRONG_PHASE_INDEX)

L_MUTANT_EARLY_INDEX = copy.deepcopy(L_GOOD_INDEX)
L_MUTANT_EARLY_INDEX["removal_gate"]["requires"] = []
L_MUTANT_EARLY_DOCS = _render_l_documents(L_MUTANT_EARLY_INDEX)
L_MUTANT_EARLY_DOCS["docs/MIGRATION.md"] = L_MUTANT_EARLY_DOCS[
    "docs/MIGRATION.md"
].replace(
    "Compatibility removal remains blocked until two successful verifications, a\nrollback drill, and zero mixed-version readers are all recorded.",
    "Compatibility removal is complete immediately after cutover.",
)

L_MUTANT_OWNER_DOCS = copy.deepcopy(L_GOOD_DOCS)
L_MUTANT_OWNER_DOCS["docs/RECOVERY.md"] = L_MUTANT_OWNER_DOCS[
    "docs/RECOVERY.md"
].replace("| cleanup | migration-controller |", "| cleanup | runtime-backend |")


def _l_artifact_files(documents: dict[str, str], index_value: dict[str, Any]) -> dict[str, str]:
    return {**documents, "docs-index.json": _document(index_value)}


RECIPES: dict[str, dict[str, Any]] = {
    "f07-s-agentctl-doctor-doc-v1": {
        "case_id": "F07-S-MD-001",
        "files": S_FILES,
        "hidden": S_HIDDEN,
        "good": {"README.md": S_GOOD_README},
        "executable": ["agentctl.py"],
        "mutants": {
            "correct-order-without-constraint": {
                "files": {"README.md": S_MUTANT_ORDER_ONLY},
                "expected_failed_check_ids": ["doc-constraint-accurate"],
            },
            "nonreplayable-placeholder": {
                "files": {"README.md": S_MUTANT_PLACEHOLDER},
                "expected_failed_check_ids": ["doc-command-replay"],
            },
            "invented-outside-bypass": {
                "files": {"README.md": S_MUTANT_FALSE_BYPASS},
                "expected_failed_check_ids": ["doc-constraint-accurate"],
            },
        },
    },
    "f07-m-state-recovery-runbook-v1": {
        "case_id": "F07-M-MDBASH-001",
        "files": M_FILES,
        "hidden": M_HIDDEN,
        "good": {
            "RUNBOOK.md": M_GOOD_RUNBOOK,
            "runbook.json": _document(M_GOOD_MANIFEST),
        },
        "executable": [
            "bin/state-backup",
            "bin/service-control",
            "tools/state-doctor.py",
            "tools/replay_runbook.sh",
        ],
        "mutants": {
            "delete-and-restart-all-first": {
                "files": {
                    "RUNBOOK.md": _render_m_runbook(M_MUTANT_DESTRUCTIVE),
                    "runbook.json": _document(M_MUTANT_DESTRUCTIVE),
                },
                "expected_failed_check_ids": ["runbook-order-safety"],
            },
            "verify-after-restore": {
                "files": {
                    "RUNBOOK.md": _render_m_runbook(M_MUTANT_VERIFY_AFTER),
                    "runbook.json": _document(M_MUTANT_VERIFY_AFTER),
                },
                "expected_failed_check_ids": ["runbook-order-safety"],
            },
            "prose-manifest-placeholder-drift": {
                "files": {
                    "RUNBOOK.md": M_MUTANT_PLACEHOLDER_RUNBOOK,
                    "runbook.json": _document(M_GOOD_MANIFEST),
                },
                "expected_failed_check_ids": ["runbook-doc-manifest-sync"],
            },
            "restore-without-health-check": {
                "files": {
                    "RUNBOOK.md": _render_m_runbook(M_MUTANT_NO_HEALTH),
                    "runbook.json": _document(M_MUTANT_NO_HEALTH),
                },
                "expected_failed_check_ids": ["runbook-corrupt-recovery"],
            },
        },
    },
    "f07-l-backend-migration-docs-v1": {
        "case_id": "F07-L-MDPYBASH-001",
        "files": L_FILES,
        "hidden": L_HIDDEN,
        "good": _l_artifact_files(L_GOOD_DOCS, L_GOOD_INDEX),
        "executable": ["bin/backendctl", "tools/replay_migration_docs.sh"],
        "mutants": {
            "stale-architecture-default": {
                "files": _l_artifact_files(L_MUTANT_STALE_DOCS, L_GOOD_INDEX),
                "expected_failed_check_ids": ["docs-current-target-facts"],
            },
            "destructive-rollback-export": {
                "files": _l_artifact_files(L_MUTANT_DESTRUCTIVE_DOCS, L_MUTANT_DESTRUCTIVE_INDEX),
                "expected_failed_check_ids": ["docs-rollback-nondestructive"],
            },
            "cutover-assigned-to-prepare-phase": {
                "files": _l_artifact_files(L_MUTANT_WRONG_PHASE_DOCS, L_MUTANT_WRONG_PHASE_INDEX),
                "expected_failed_check_ids": ["docs-migration-order"],
            },
            "immediate-compatibility-removal": {
                "files": _l_artifact_files(L_MUTANT_EARLY_DOCS, L_MUTANT_EARLY_INDEX),
                "expected_failed_check_ids": ["docs-no-early-removal"],
            },
            "recovery-cleanup-owner-drift": {
                "files": _l_artifact_files(L_MUTANT_OWNER_DOCS, L_GOOD_INDEX),
                "expected_failed_check_ids": ["docs-ownership-consistency"],
            },
        },
    },
}


__all__ = ["RECIPES"]
