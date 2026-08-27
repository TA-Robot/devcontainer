"""Devcontainer-operations duration fixtures with deterministic local lifecycles."""

from __future__ import annotations

import hashlib
from textwrap import dedent, indent
from typing import Any


AGENT_INSTRUCTIONS = """# AGENTS.md

This repository is a disposable duration-study fixture.

- Work only inside this repository and process-owned temporary directories.
- Do not inspect parent directories or search for hidden/gold artifacts.
- Do not use the network, host Docker, a shared Docker socket, credentials, or remotes.
- Do not commit, push, or modify Git metadata.
- Preserve tests and validators; change only paths authorized by the task capsule.
- Never perform broad workspace, volume, home, or metadata deletion.
- Run every validation command listed in the task capsule.
"""


def _overlay(base: dict[str, str], changes: dict[str, str]) -> dict[str, str]:
    return {**base, **changes}


def _hidden_source(
    class_name: str,
    files: dict[str, str],
    mutable_paths: set[str],
    class_body: str,
) -> str:
    protected = {
        path: hashlib.sha256(content.encode("utf-8")).hexdigest()
        for path, content in sorted(files.items())
        if path not in mutable_paths
    }
    header = f'''#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


WORKSPACE = Path(os.environ["DURATION_FIXTURE_WORKSPACE"])
PROTECTED_DIGESTS = {protected!r}
MUTABLE_PATHS = {sorted(mutable_paths)!r}


def assert_fixture_integrity(testcase):
    for raw_path, expected in PROTECTED_DIGESTS.items():
        path = WORKSPACE / raw_path
        testcase.assertTrue(path.is_file(), f"fixture file removed: {{raw_path}}")
        testcase.assertEqual(
            hashlib.sha256(path.read_bytes()).hexdigest(),
            expected,
            f"fixture file modified: {{raw_path}}",
        )
    completed = subprocess.run(
        ["git", "status", "--porcelain=v1", "--untracked-files=all"],
        cwd=WORKSPACE,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    testcase.assertEqual(completed.returncode, 0, completed.stderr)
    for line in completed.stdout.splitlines():
        testcase.assertGreaterEqual(len(line), 4)
        testcase.assertIn(line[3:], MUTABLE_PATHS, f"contract-external change: {{line}}")
        testcase.assertFalse(line.startswith("D ") or line.startswith(" D"), line)


def run_command(arguments, *, environment=None):
    selected = dict(os.environ)
    selected["PYTHONPATH"] = str(WORKSPACE)
    if environment:
        selected.update(environment)
    return subprocess.run(
        arguments,
        cwd=WORKSPACE,
        env=selected,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def canonical_bytes(value):
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\\n").encode("utf-8")


class {class_name}(unittest.TestCase):
'''
    footer = '''

if __name__ == "__main__":
    unittest.main()
'''
    return header + indent(dedent(class_body).strip(), "    ") + "\n" + footer


# ---------------------------------------------------------------------------
# S: one missing case terminator

S_FILES = {
    "AGENTS.md": AGENT_INSTRUCTIONS,
    "sync-version.sh": '''#!/usr/bin/env bash
set -euo pipefail

mode="${1:?mode is required}"
host_version="${2:-}"
container_version="${3:-}"
default_version="${4:-stable}"

case "$mode" in
    host)
        selected="$host_version"
    container)
        selected="$container_version"
        ;;
    auto)
        if [[ -n "$host_version" ]]; then
            selected="$host_version"
        elif [[ -n "$container_version" ]]; then
            selected="$container_version"
        else
            selected="$default_version"
        fi
        ;;
    *)
        printf 'unsupported mode: %s\n' "$mode" >&2
        exit 2
        ;;
esac

printf '%s\n' "$selected"
''',
    "tests/smoke.sh": '''#!/usr/bin/env bash
set -euo pipefail
root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
script="$root/sync-version.sh"
[[ "$(bash "$script" host host-1 container-2 default-3)" == "host-1" ]]
[[ "$(bash "$script" container host-1 container-2 default-3)" == "container-2" ]]
[[ "$(bash "$script" auto host-1 container-2 default-3)" == "host-1" ]]
[[ "$(bash "$script" auto '' container-2 default-3)" == "container-2" ]]
[[ "$(bash "$script" auto '' '' default-3)" == "default-3" ]]
''',
}

S_GOOD_SCRIPT = S_FILES["sync-version.sh"].replace(
    '    container)\n',
    '        ;;\n    container)\n',
    1,
)

S_BAD_IF_REWRITE = '''#!/usr/bin/env bash
set -euo pipefail
mode="${1:?mode is required}"
host_version="${2:-}"
container_version="${3:-}"
default_version="${4:-stable}"
if [[ "$mode" == host ]]; then
    selected="$host_version"
elif [[ "$mode" == container ]]; then
    selected="$container_version"
elif [[ "$mode" == auto ]]; then
    if [[ -n "$host_version" ]]; then selected="$host_version"
    elif [[ -n "$container_version" ]]; then selected="$container_version"
    else selected="$default_version"; fi
else
    printf 'unsupported mode: %s\n' "$mode" >&2
    exit 2
fi
printf '%s\n' "$selected"
'''

S_BAD_WRONG_ARM = S_FILES["sync-version.sh"].replace(
    '        ;;\n    auto)',
    '        ;;\n        ;;\n    auto)',
    1,
)

S_BAD_PRECEDENCE = S_GOOD_SCRIPT.replace(
    '''        if [[ -n "$host_version" ]]; then
            selected="$host_version"
        elif [[ -n "$container_version" ]]; then
            selected="$container_version"
''',
    '''        if [[ -n "$container_version" ]]; then
            selected="$container_version"
        elif [[ -n "$host_version" ]]; then
            selected="$host_version"
''',
)

S_HIDDEN = _hidden_source(
    "HiddenSmallOperationsTests",
    S_FILES,
    {"sync-version.sh"},
    f'''
def test_static_pass(self):
    assert_fixture_integrity(self)
    result = run_command(["bash", "-n", "sync-version.sh"])
    self.assertEqual(result.returncode, 0, result.stderr)

def test_behavior_matrix(self):
    assert_fixture_integrity(self)
    matrix = [
        (["host", "host-1", "container-2", "default-3"], "host-1\\n"),
        (["container", "host-1", "container-2", "default-3"], "container-2\\n"),
        (["auto", "host-1", "container-2", "default-3"], "host-1\\n"),
        (["auto", "", "container-2", "default-3"], "container-2\\n"),
        (["auto", "", "", "default-3"], "default-3\\n"),
    ]
    for arguments, expected in matrix:
        with self.subTest(arguments=arguments):
            result = run_command(["bash", "sync-version.sh", *arguments])
            self.assertEqual((result.returncode, result.stdout), (0, expected), result.stderr)

def test_minimal_diff(self):
    assert_fixture_integrity(self)
    actual = (WORKSPACE / "sync-version.sh").read_text(encoding="utf-8")
    self.assertEqual(actual, {S_GOOD_SCRIPT!r})
''',
)


# ---------------------------------------------------------------------------
# M: host metadata normalization and restart-safe ready marker

M_NORMALIZER = '''normalize_version_file() {
    local source="$1"
    local -a lines=()
    mapfile -t lines < "$source"
    [[ "${#lines[@]}" -eq 1 ]] || return 2
    local value="${lines[0]}"
    value="${value%$'\\r'}"
    while [[ "$value" == *' ' || "$value" == *$'\\t' ]]; do
        value="${value%?}"
    done
    [[ "$value" =~ ^[A-Za-z0-9][A-Za-z0-9._-]*$ ]] || return 2
    printf '%s\\n' "$value"
}
'''

M_BAD_NORMALIZER = '''normalize_version_file() {
    local source="$1"
    local value
    value="$(tr -d '\\r\\n ' < "$source")"
    [[ "$value" =~ ^[A-Za-z0-9][A-Za-z0-9._-]*$ ]] || return 2
    printf '%s\\n' "$value"
}
'''

M_INITIALIZE_BASE = '''#!/usr/bin/env bash
set -euo pipefail
source_file="${1:?source file is required}"
metadata_file="${2:?metadata file is required}"
mkdir -p "$(dirname "$metadata_file")"
cp "$source_file" "$metadata_file"
'''

M_INSTALLER = '''#!/usr/bin/env bash
set -euo pipefail
desired="${1:?desired version is required}"
installed_file="${2:?installed file is required}"
ledger="${3:?ledger is required}"
mkdir -p "$(dirname "$installed_file")" "$(dirname "$ledger")"
printf 'attempt:%s\n' "$desired" >> "$ledger"
if [[ -n "${INSTALL_FAIL_FLAG:-}" && -f "$INSTALL_FAIL_FLAG" ]]; then
    rm -f -- "$INSTALL_FAIL_FLAG"
    exit 23
fi
written="$desired"
if [[ "${INSTALL_WRONG_VERSION:-0}" == 1 ]]; then
    written="wrong-version"
fi
temporary="${installed_file}.tmp.$$"
trap 'rm -f -- "$temporary"' EXIT
printf '%s\n' "$written" > "$temporary"
mv -f -- "$temporary" "$installed_file"
trap - EXIT
'''

M_POST_BASE = '''#!/usr/bin/env bash
set -euo pipefail
host_metadata="${1:?host metadata is required}"
installed_file="${2:?installed file is required}"
ready_file="${3:?ready file is required}"
ledger="${4:?ledger is required}"
if [[ -f "$ready_file" ]]; then
    exit 0
fi
desired="$(cat "$host_metadata")"
mkdir -p "$(dirname "$ready_file")"
printf '%s\n' "$desired" > "$ready_file"
"$(dirname "${BASH_SOURCE[0]}")/install-cli" "$desired" "$installed_file" "$ledger"
'''

M_GOOD_INITIALIZE = '''#!/usr/bin/env bash
set -euo pipefail
''' + M_NORMALIZER + '''
source_file="${1:?source file is required}"
metadata_file="${2:?metadata file is required}"
canonical="$(normalize_version_file "$source_file")" || {
    printf 'invalid host version metadata\n' >&2
    exit 2
}
mkdir -p "$(dirname "$metadata_file")"
temporary="${metadata_file}.tmp.$$"
trap 'rm -f -- "$temporary"' EXIT
printf '%s\n' "$canonical" > "$temporary"
mv -f -- "$temporary" "$metadata_file"
trap - EXIT
'''

M_GOOD_POST = '''#!/usr/bin/env bash
set -euo pipefail
''' + M_NORMALIZER + '''
host_metadata="${1:?host metadata is required}"
installed_file="${2:?installed file is required}"
ready_file="${3:?ready file is required}"
ledger="${4:?ledger is required}"
desired="$(normalize_version_file "$host_metadata")" || {
    printf 'invalid host version metadata\n' >&2
    exit 2
}
installed=""
if [[ -f "$installed_file" ]]; then
    installed="$(normalize_version_file "$installed_file")" || installed=""
fi
ready=""
if [[ -f "$ready_file" ]]; then
    ready="$(normalize_version_file "$ready_file")" || ready=""
fi
if [[ "$installed" == "$desired" && "$ready" == "$desired" ]]; then
    exit 0
fi
if [[ "$installed" != "$desired" ]]; then
    "$(dirname "${BASH_SOURCE[0]}")/install-cli" "$desired" "$installed_file" "$ledger"
fi
verified="$(normalize_version_file "$installed_file")" || {
    printf 'installed version is invalid\n' >&2
    exit 3
}
[[ "$verified" == "$desired" ]] || {
    printf 'installed version does not match requested version\n' >&2
    exit 3
}
mkdir -p "$(dirname "$ready_file")"
temporary="${ready_file}.tmp.$$"
trap 'rm -f -- "$temporary"' EXIT
printf '%s\n' "$verified" > "$temporary"
mv -f -- "$temporary" "$ready_file"
trap - EXIT
'''

M_LIFECYCLE_TEST = '''#!/usr/bin/env bash
set -euo pipefail
root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
temporary="$(mktemp -d)"
trap 'rm -rf -- "$temporary"' EXIT
raw="$temporary/raw-version"
metadata="$temporary/persistent/host.version"
installed="$temporary/persistent/installed.version"
ready="$temporary/persistent/ready.version"
ledger="$temporary/persistent/install.log"
printf '1.2.3  \r\n' > "$raw"
bash "$root/initialize-host.sh" "$raw" "$metadata"
bash "$root/post-start.sh" "$metadata" "$installed" "$ready" "$ledger"
[[ "$(cat "$ready")" == "1.2.3" ]]
[[ "$(wc -l < "$ledger")" -eq 1 ]]
bash "$root/post-start.sh" "$metadata" "$installed" "$ready" "$ledger"
[[ "$(wc -l < "$ledger")" -eq 1 ]]
printf '2.0.0\r\n' > "$raw"
bash "$root/initialize-host.sh" "$raw" "$metadata"
fail_flag="$temporary/fail-once"
: > "$fail_flag"
set +e
INSTALL_FAIL_FLAG="$fail_flag" bash "$root/post-start.sh" "$metadata" "$installed" "$ready" "$ledger"
status=$?
set -e
[[ "$status" -eq 23 ]]
[[ "$(cat "$ready")" == "1.2.3" ]]
bash "$root/post-start.sh" "$metadata" "$installed" "$ready" "$ledger"
[[ "$(cat "$ready")" == "2.0.0" ]]
[[ "$(wc -l < "$ledger")" -eq 3 ]]
bash "$root/post-start.sh" "$metadata" "$installed" "$ready" "$ledger"
[[ "$(wc -l < "$ledger")" -eq 3 ]]
'''

M_FILES = {
    "AGENTS.md": AGENT_INSTRUCTIONS,
    "initialize-host.sh": M_INITIALIZE_BASE,
    "post-start.sh": M_POST_BASE,
    "install-cli": M_INSTALLER,
    "tests/lifecycle.sh": M_LIFECYCLE_TEST,
}

M_BAD_NORMALIZE_INITIALIZE = M_GOOD_INITIALIZE.replace(M_NORMALIZER, M_BAD_NORMALIZER)
M_BAD_NORMALIZE_POST = M_GOOD_POST.replace(M_NORMALIZER, M_BAD_NORMALIZER)

M_BAD_READY_FIRST = '''#!/usr/bin/env bash
set -euo pipefail
''' + M_NORMALIZER + '''
host_metadata="$1"; installed_file="$2"; ready_file="$3"; ledger="$4"
desired="$(normalize_version_file "$host_metadata")"
mkdir -p "$(dirname "$ready_file")"
printf '%s\n' "$desired" > "$ready_file"
"$(dirname "${BASH_SOURCE[0]}")/install-cli" "$desired" "$installed_file" "$ledger"
'''

M_BAD_ALWAYS_INSTALL = '''#!/usr/bin/env bash
set -euo pipefail
''' + M_NORMALIZER + '''
host_metadata="$1"; installed_file="$2"; ready_file="$3"; ledger="$4"
desired="$(normalize_version_file "$host_metadata")"
"$(dirname "${BASH_SOURCE[0]}")/install-cli" "$desired" "$installed_file" "$ledger"
verified="$(normalize_version_file "$installed_file")"
mkdir -p "$(dirname "$ready_file")"
printf '%s\n' "$verified" > "$ready_file"
'''

M_BAD_DELETE_STATE = '''#!/usr/bin/env bash
set -euo pipefail
''' + M_NORMALIZER + '''
host_metadata="$1"; installed_file="$2"; ready_file="$3"; ledger="$4"
desired="$(normalize_version_file "$host_metadata")"
if ! "$(dirname "${BASH_SOURCE[0]}")/install-cli" "$desired" "$installed_file" "$ledger"; then
    rm -f -- "$host_metadata" "$installed_file" "$ready_file" "$ledger" "$(dirname "$ready_file")/peer-sentinel"
    exit 23
fi
printf '%s\n' "$desired" > "$ready_file"
'''

M_HIDDEN = _hidden_source(
    "HiddenMediumOperationsTests",
    M_FILES,
    {"initialize-host.sh", "post-start.sh"},
    r'''
def test_version_normalization(self):
    assert_fixture_integrity(self)
    valid = [(b"1.2.3\r\n", "1.2.3\n"), (b"release-7   \r\n", "release-7\n"), (b"v_2\t\n", "v_2\n")]
    invalid = [b"one\ntwo\n", b" leading\n", b"bad value\n", b"\n", b"one\r\ntwo\r\n"]
    with tempfile.TemporaryDirectory() as raw:
        root = Path(raw)
        for index, (content, expected) in enumerate(valid):
            source = root / f"valid-{index}"
            output = root / f"metadata-{index}"
            source.write_bytes(content)
            result = run_command(["bash", "initialize-host.sh", str(source), str(output)])
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(output.read_text(encoding="utf-8"), expected)
        for index, content in enumerate(invalid):
            source = root / f"invalid-{index}"
            output = root / f"bad-metadata-{index}"
            source.write_bytes(content)
            result = run_command(["bash", "initialize-host.sh", str(source), str(output)])
            self.assertNotEqual(result.returncode, 0, content)
            self.assertFalse(output.exists())

def test_idempotent_install(self):
    assert_fixture_integrity(self)
    with tempfile.TemporaryDirectory() as raw:
        root = Path(raw); source = root / "raw"; metadata = root / "host"; installed = root / "installed"; ready = root / "ready"; ledger = root / "ledger"
        source.write_bytes(b"1.0.0\r\n")
        self.assertEqual(run_command(["bash", "initialize-host.sh", str(source), str(metadata)]).returncode, 0)
        command = ["bash", "post-start.sh", str(metadata), str(installed), str(ready), str(ledger)]
        self.assertEqual(run_command(command).returncode, 0)
        self.assertEqual(run_command(command).returncode, 0)
        self.assertEqual(ledger.read_text(encoding="utf-8").splitlines(), ["attempt:1.0.0"])
        source.write_text("2.0.0\n", encoding="utf-8")
        self.assertEqual(run_command(["bash", "initialize-host.sh", str(source), str(metadata)]).returncode, 0)
        self.assertEqual(run_command(command).returncode, 0)
        self.assertEqual(ledger.read_text(encoding="utf-8").splitlines(), ["attempt:1.0.0", "attempt:2.0.0"])

def test_ready_after_verify(self):
    assert_fixture_integrity(self)
    with tempfile.TemporaryDirectory() as raw:
        root = Path(raw); metadata = root / "host"; installed = root / "installed"; ready = root / "ready"; ledger = root / "ledger"; flag = root / "fail"
        metadata.write_text("3.0.0\n", encoding="utf-8"); flag.touch()
        command = ["bash", "post-start.sh", str(metadata), str(installed), str(ready), str(ledger)]
        result = run_command(command, environment={"INSTALL_FAIL_FLAG": str(flag)})
        self.assertEqual(result.returncode, 23)
        self.assertFalse(ready.exists())
        wrong = run_command(command, environment={"INSTALL_WRONG_VERSION": "1"})
        self.assertEqual(wrong.returncode, 3)
        self.assertFalse(ready.exists())

def test_restart_recovery(self):
    assert_fixture_integrity(self)
    with tempfile.TemporaryDirectory() as raw:
        root = Path(raw); metadata = root / "host"; installed = root / "installed"; ready = root / "ready"; ledger = root / "ledger"; flag = root / "fail"
        metadata.write_text("4.0.0\n", encoding="utf-8"); flag.touch()
        command = ["bash", "post-start.sh", str(metadata), str(installed), str(ready), str(ledger)]
        self.assertEqual(run_command(command, environment={"INSTALL_FAIL_FLAG": str(flag)}).returncode, 23)
        self.assertEqual(run_command(command).returncode, 0)
        first_ready = ready.read_bytes()
        self.assertEqual(run_command(command).returncode, 0)
        self.assertEqual(ready.read_bytes(), first_ready)
        self.assertEqual(ledger.read_text(encoding="utf-8").splitlines(), ["attempt:4.0.0", "attempt:4.0.0"])

def test_state_cleanup(self):
    assert_fixture_integrity(self)
    with tempfile.TemporaryDirectory() as raw:
        root = Path(raw); metadata = root / "host"; installed = root / "installed"; ready = root / "ready"; ledger = root / "ledger"; flag = root / "fail"; sentinel = root / "peer-sentinel"
        metadata.write_text("5.0.0\n", encoding="utf-8"); sentinel.write_text("keep\n", encoding="utf-8"); flag.touch()
        command = ["bash", "post-start.sh", str(metadata), str(installed), str(ready), str(ledger)]
        run_command(command, environment={"INSTALL_FAIL_FLAG": str(flag)})
        self.assertTrue(metadata.is_file()); self.assertTrue(sentinel.is_file())
        self.assertEqual(run_command(command).returncode, 0)
        self.assertEqual(list(root.glob("*.tmp.*")), [])
        self.assertEqual(sentinel.read_text(encoding="utf-8"), "keep\n")
''',
)


# ---------------------------------------------------------------------------
# L: simulated rebuild/reopen with persistent migration and versioned markers

L_DEVCONTAINER = '''{
  "name": "operations-rebuild-fixture",
  "initializeCommand": "bash initialize-host.sh HOST_ROOT CLI_VERSION EXTENSION_VERSION",
  "postCreateCommand": "bash post-create.sh VOLUME_ROOT",
  "postStartCommand": "bash post-start.sh HOST_ROOT VOLUME_ROOT RUNTIME_ROOT",
  "fixtureLifecycle": {
    "usesHostDocker": false,
    "usesSharedDockerSocket": false,
    "stages": [
      {"id": "initialize-host", "owner": "host", "markerOwners": ["host-cli", "extension"]},
      {"id": "post-create", "owner": "container", "markerOwners": ["state-schema"]},
      {"id": "post-start", "owner": "container", "markerOwners": ["runtime-ready"]}
    ]
  }
}
'''

L_MIGRATE_BASE = '''#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path


def migrate(path: Path, fail_at: str | None) -> None:
    state = json.loads(path.read_text(encoding="utf-8"))
    state["version"] = 2
    path.write_text(json.dumps(state) + "\\n", encoding="utf-8")
    if fail_at == "after-stage":
        raise RuntimeError("forced interruption")
    state["items"] = {item["id"]: {"payload": item["payload"]} for item in state.pop("jobs", [])}
    path.write_text(json.dumps(state) + "\\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    commands = parser.add_subparsers(dest="command", required=True)
    migrate_command = commands.add_parser("migrate")
    migrate_command.add_argument("--state", type=Path, required=True)
    migrate_command.add_argument("--fail-at")
    args = parser.parse_args()
    try:
        migrate(args.state, args.fail_at)
        return 0
    except RuntimeError:
        return 75


if __name__ == "__main__":
    raise SystemExit(main())
'''

L_INITIALIZE_BASE = '''#!/usr/bin/env bash
set -euo pipefail
host_root="$1"; cli_version="$2"; extension_version="$3"
mkdir -p "$host_root/artifacts" "$host_root/markers"
printf 'cli=%s\n' "$cli_version" > "$host_root/markers/host-cli.marker"
printf 'extension=%s\n' "$extension_version" > "$host_root/markers/extension.marker"
printf '%s\n' "$cli_version" > "$host_root/artifacts/cli.version"
printf '%s\n' "$extension_version" > "$host_root/artifacts/extension.version"
'''

L_POST_CREATE_BASE = '''#!/usr/bin/env bash
set -euo pipefail
volume_root="$1"
fail_at="${2:-}"
if ! python3 "$(dirname "${BASH_SOURCE[0]}")/migrate_state.py" migrate --state "$volume_root/state.json" ${fail_at:+--fail-at "$fail_at"}; then
    rm -f -- "$volume_root/state.json"
    exit 75
fi
'''

L_POST_START_BASE = '''#!/usr/bin/env bash
set -euo pipefail
host_root="$1"; volume_root="$2"; runtime_root="$3"
[[ -f "$host_root/markers/host-cli.marker" ]]
[[ -f "$host_root/markers/extension.marker" ]]
[[ -f "$volume_root/state.json" ]]
mkdir -p "$runtime_root"
printf 'ready\n' > "$runtime_root/runtime.marker"
'''

L_GOOD_MIGRATE = '''#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import tempfile
from typing import Any


class MigrationInterrupted(RuntimeError):
    pass


def canonical_bytes(value: dict[str, Any]) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\\n").encode("utf-8")


def state_digest(value: dict[str, Any]) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def atomic_write(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, raw_temporary = tempfile.mkstemp(prefix=f".{path.name}.tmp.", dir=path.parent)
    temporary = Path(raw_temporary)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(canonical_bytes(value))
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def validate_v1(state: dict[str, Any]) -> None:
    if state.get("version") != 1 or not isinstance(state.get("jobs"), list):
        raise ValueError("invalid schema v1 state")
    ids = []
    for item in state["jobs"]:
        if not isinstance(item, dict) or not isinstance(item.get("id"), str) or not isinstance(item.get("payload"), str):
            raise ValueError("invalid schema v1 item")
        ids.append(item["id"])
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate schema v1 item")


def validate_v2(state: dict[str, Any]) -> None:
    if state.get("version") != 2 or not isinstance(state.get("items"), dict):
        raise ValueError("invalid schema v2 state")
    for item_id, item in state["items"].items():
        if not isinstance(item_id, str) or not isinstance(item, dict) or not isinstance(item.get("payload"), str):
            raise ValueError("invalid schema v2 item")


def to_v2(state: dict[str, Any]) -> dict[str, Any]:
    validate_v1(state)
    return {
        "version": 2,
        "items": {
            item["id"]: {"payload": item["payload"]}
            for item in sorted(state["jobs"], key=lambda item: item["id"])
        },
    }


def to_v1(state: dict[str, Any]) -> dict[str, Any]:
    if state.get("version") == 1:
        validate_v1(state)
        return state
    validate_v2(state)
    return {
        "version": 1,
        "jobs": [
            {"id": item_id, "payload": item["payload"]}
            for item_id, item in sorted(state["items"].items())
        ],
    }


def migrate(path: Path, fail_at: str | None = None) -> dict[str, Any]:
    journal_path = path.with_name(path.name + ".migration-journal")
    current = json.loads(path.read_text(encoding="utf-8"))
    if current.get("version") == 2:
        validate_v2(current)
        journal_path.unlink(missing_ok=True)
        return current
    validate_v1(current)
    if fail_at == "before-stage":
        raise MigrationInterrupted("interrupted before stage")
    if journal_path.exists():
        journal = json.loads(journal_path.read_text(encoding="utf-8"))
        if journal.get("source_digest") != state_digest(current):
            raise ValueError("migration journal source mismatch")
        candidate = journal.get("candidate")
        if not isinstance(candidate, dict):
            raise ValueError("invalid migration journal candidate")
        validate_v2(candidate)
    else:
        candidate = to_v2(current)
        atomic_write(journal_path, {"source_digest": state_digest(current), "candidate": candidate})
    if fail_at == "after-stage":
        raise MigrationInterrupted("interrupted after stage")
    atomic_write(path, candidate)
    if fail_at == "after-commit":
        raise MigrationInterrupted("interrupted after commit")
    journal_path.unlink(missing_ok=True)
    return candidate


def rollback_export(path: Path, output: Path) -> dict[str, Any]:
    source = json.loads(path.read_text(encoding="utf-8"))
    exported = to_v1(source)
    atomic_write(output, exported)
    return exported


def verify(path: Path) -> dict[str, Any]:
    state = json.loads(path.read_text(encoding="utf-8"))
    if state.get("version") == 1:
        validate_v1(state)
    else:
        validate_v2(state)
    return state


def main() -> int:
    parser = argparse.ArgumentParser()
    commands = parser.add_subparsers(dest="command", required=True)
    migrate_command = commands.add_parser("migrate")
    migrate_command.add_argument("--state", type=Path, required=True)
    migrate_command.add_argument("--fail-at", choices=["before-stage", "after-stage", "after-commit"])
    verify_command = commands.add_parser("verify")
    verify_command.add_argument("--state", type=Path, required=True)
    rollback_command = commands.add_parser("rollback")
    rollback_command.add_argument("--state", type=Path, required=True)
    rollback_command.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        if args.command == "migrate":
            migrate(args.state, args.fail_at)
        elif args.command == "verify":
            state = verify(args.state)
            print(f"schema-v{state['version']}")
        else:
            rollback_export(args.state, args.output)
        return 0
    except MigrationInterrupted:
        return 75
    except (OSError, ValueError, json.JSONDecodeError):
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
'''

L_GOOD_INITIALIZE = '''#!/usr/bin/env bash
set -euo pipefail
host_root="${1:?host root is required}"
cli_version="${2:?CLI version is required}"
extension_version="${3:?extension version is required}"
fail_at="${4:-}"
[[ "$cli_version" =~ ^[A-Za-z0-9][A-Za-z0-9._-]*$ ]]
[[ "$extension_version" =~ ^[A-Za-z0-9][A-Za-z0-9._-]*$ ]]
mkdir -p "$host_root/artifacts" "$host_root/markers"
ledger="$host_root/repair.log"

sync_component() {
    local name="$1" version="$2" cut="$3"
    local artifact="$host_root/artifacts/$name.version"
    local marker_name="$name"
    [[ "$name" == cli ]] && marker_name="host-cli"
    local marker="$host_root/markers/$marker_name.marker"
    local expected_marker="$marker_name=$version"
    local installed=""
    [[ -f "$artifact" ]] && installed="$(cat "$artifact")"
    if [[ "$installed" != "$version" ]]; then
        local artifact_tmp="${artifact}.tmp.$$"
        trap 'rm -f -- "$artifact_tmp"' RETURN
        printf '%s\n' "$version" > "$artifact_tmp"
        mv -f -- "$artifact_tmp" "$artifact"
        trap - RETURN
        printf 'install:%s:%s\n' "$marker_name" "$version" >> "$ledger"
    fi
    if [[ "$fail_at" == "$cut" ]]; then
        return 75
    fi
    [[ "$(cat "$artifact")" == "$version" ]]
    local current_marker=""
    [[ -f "$marker" ]] && current_marker="$(cat "$marker")"
    if [[ "$current_marker" != "$expected_marker" ]]; then
        local marker_tmp="${marker}.tmp.$$"
        trap 'rm -f -- "$marker_tmp"' RETURN
        printf '%s\n' "$expected_marker" > "$marker_tmp"
        mv -f -- "$marker_tmp" "$marker"
        trap - RETURN
        printf 'marker:%s:%s\n' "$marker_name" "$version" >> "$ledger"
    fi
}

sync_component cli "$cli_version" after-cli-artifact || exit $?
sync_component extension "$extension_version" after-extension-artifact || exit $?
'''

L_GOOD_POST_CREATE = '''#!/usr/bin/env bash
set -euo pipefail
volume_root="${1:?volume root is required}"
fail_at="${2:-}"
state="$volume_root/state.json"
[[ -f "$state" ]]
arguments=(migrate --state "$state")
[[ -n "$fail_at" ]] && arguments+=(--fail-at "$fail_at")
python3 "$(dirname "${BASH_SOURCE[0]}")/migrate_state.py" "${arguments[@]}"
'''

L_GOOD_POST_START = '''#!/usr/bin/env bash
set -euo pipefail
host_root="${1:?host root is required}"
volume_root="${2:?volume root is required}"
runtime_root="${3:?runtime root is required}"
state="$volume_root/state.json"
python3 "$(dirname "${BASH_SOURCE[0]}")/migrate_state.py" migrate --state "$state"
cli_version="$(cat "$host_root/artifacts/cli.version")"
extension_version="$(cat "$host_root/artifacts/extension.version")"
[[ "$(cat "$host_root/markers/host-cli.marker")" == "host-cli=$cli_version" ]] || exit 4
[[ "$(cat "$host_root/markers/extension.marker")" == "extension=$extension_version" ]] || exit 4
[[ "$(python3 "$(dirname "${BASH_SOURCE[0]}")/migrate_state.py" verify --state "$state")" == "schema-v2" ]]
mkdir -p "$runtime_root"
ready="runtime=schema-v2;cli=$cli_version;extension=$extension_version"
temporary="$runtime_root/runtime.marker.tmp.$$"
trap 'rm -f -- "$temporary"' EXIT
printf '%s\n' "$ready" > "$temporary"
mv -f -- "$temporary" "$runtime_root/runtime.marker"
trap - EXIT
'''

L_UNIT_TEST = r'''import json
import tempfile
import unittest
from pathlib import Path

from migrate_state import MigrationInterrupted, migrate, rollback_export


class StateMigrationTests(unittest.TestCase):
    def test_interrupted_stage_resumes(self):
        with tempfile.TemporaryDirectory() as raw:
            path = Path(raw) / "state.json"
            path.write_text('{"jobs":[{"id":"a","payload":"one"}],"version":1}\n', encoding="utf-8")
            with self.assertRaises(MigrationInterrupted):
                migrate(path, "after-stage")
            self.assertEqual(json.loads(path.read_text(encoding="utf-8"))["version"], 1)
            self.assertEqual(migrate(path)["version"], 2)

    def test_rollback_export_does_not_change_source(self):
        with tempfile.TemporaryDirectory() as raw:
            path = Path(raw) / "state.json"
            output = Path(raw) / "rollback.json"
            path.write_text('{"jobs":[{"id":"a","payload":"one"}],"version":1}\n', encoding="utf-8")
            migrate(path)
            before = path.read_bytes()
            rollback_export(path, output)
            self.assertEqual(path.read_bytes(), before)
            self.assertEqual(json.loads(output.read_text(encoding="utf-8"))["version"], 1)


if __name__ == "__main__":
    unittest.main()
'''

L_REBUILD_TEST = '''#!/usr/bin/env bash
set -euo pipefail
[[ "${1:-}" == "--scenario" && "${2:-}" == "visible-all" ]]
root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
temporary="$(mktemp -d)"
trap 'rm -rf -- "$temporary"' EXIT
host="$temporary/host"; volume="$temporary/volume"; runtime="$temporary/runtime"
mkdir -p "$host" "$volume" "$runtime"
printf 'keep\n' > "$host/peer-sentinel"
printf 'keep\n' > "$volume/peer-sentinel"
printf 'keep\n' > "$runtime/peer-sentinel"
printf '%s\n' '{"jobs":[{"id":"b","payload":"two"},{"id":"a","payload":"one"}],"version":1}' > "$volume/state.json"
bash "$root/initialize-host.sh" "$host" cli-2 extension-3
set +e
bash "$root/post-create.sh" "$volume" after-stage
status=$?
set -e
[[ "$status" -eq 75 ]]
bash "$root/initialize-host.sh" "$host" cli-2 extension-3
bash "$root/post-create.sh" "$volume"
bash "$root/post-start.sh" "$host" "$volume" "$runtime"
first_ready="$(cat "$runtime/runtime.marker")"
bash "$root/post-start.sh" "$host" "$volume" "$runtime"
[[ "$(cat "$runtime/runtime.marker")" == "$first_ready" ]]
printf 'ready\n' > "$host/markers/host-cli.marker"
printf 'ready\n' > "$host/markers/extension.marker"
bash "$root/initialize-host.sh" "$host" cli-2 extension-3
bash "$root/post-start.sh" "$host" "$volume" "$runtime"
[[ "$(cat "$host/peer-sentinel")" == keep ]]
[[ "$(cat "$volume/peer-sentinel")" == keep ]]
[[ "$(cat "$runtime/peer-sentinel")" == keep ]]
[[ ! -e "$volume/state.json.migration-journal" ]]
[[ -z "$(find "$temporary" -type f -name '*.tmp.*' -print -quit)" ]]
'''

L_DOC_TOOL = r'''#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile


START = "<!-- recovery-contract"
END = "-->"


def load_manifest(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    if START not in text:
        raise ValueError("recovery contract is missing")
    value = json.loads(text.split(START, 1)[1].split(END, 1)[0])
    if not isinstance(value, dict):
        raise ValueError("recovery contract must be an object")
    return value


def main() -> int:
    if len(sys.argv) != 2:
        raise SystemExit("usage: check_recovery_docs.py RECOVERY.md")
    root = Path.cwd()
    manifest = load_manifest(root / sys.argv[1])
    if manifest.get("owners") != {
        "host-cli": "initialize-host",
        "extension": "initialize-host",
        "state-schema": "post-create",
        "runtime-ready": "post-start",
    }:
        raise SystemExit("recovery owners do not match lifecycle contract")
    commands = manifest.get("commands", [])
    if [item.get("name") for item in commands] != ["diagnose", "resume", "rollback-export", "reopen-host", "reopen-runtime"]:
        raise SystemExit("recovery command sequence is incomplete")
    with tempfile.TemporaryDirectory(prefix="recovery-doc-") as raw:
        temp = Path(raw); host = temp / "host"; volume = temp / "volume"; runtime = temp / "runtime"; output = temp / "rollback.json"
        host.mkdir(); volume.mkdir(); runtime.mkdir()
        (volume / "state.json").write_text('{"jobs":[{"id":"doc","payload":"value"}],"version":1}\n', encoding="utf-8")
        values = {
            "{host}": str(host), "{volume}": str(volume), "{runtime}": str(runtime),
            "{state}": str(volume / "state.json"), "{rollback}": str(output),
        }
        for item in commands:
            argv = [values.get(part, part) for part in item.get("argv", [])]
            result = subprocess.run(argv, cwd=root, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
            if result.returncode != 0:
                raise SystemExit(f"recovery command failed: {item.get('name')}: {result.stderr}")
        if json.loads((volume / "state.json").read_text(encoding="utf-8"))["version"] != 2:
            raise SystemExit("resume did not reach schema v2")
        if json.loads(output.read_text(encoding="utf-8"))["version"] != 1:
            raise SystemExit("rollback export is not schema v1")
    print("recovery commands replay successfully")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
'''

L_GOOD_DOC = '''# Simulated devcontainer recovery

The host owns CLI and extension artifacts plus their version-bound markers. `post-create` owns schema migration, and `post-start` owns runtime readiness. Preserve the original volume and peer sentinels; never delete the volume or workspace to recover.

<!-- recovery-contract
{
  "owners": {
    "host-cli": "initialize-host",
    "extension": "initialize-host",
    "state-schema": "post-create",
    "runtime-ready": "post-start"
  },
  "commands": [
    {"name": "diagnose", "argv": ["python3", "migrate_state.py", "verify", "--state", "{state}"]},
    {"name": "resume", "argv": ["bash", "post-create.sh", "{volume}"]},
    {"name": "rollback-export", "argv": ["python3", "migrate_state.py", "rollback", "--state", "{state}", "--output", "{rollback}"]},
    {"name": "reopen-host", "argv": ["bash", "initialize-host.sh", "{host}", "cli-2", "extension-3"]},
    {"name": "reopen-runtime", "argv": ["bash", "post-start.sh", "{host}", "{volume}", "{runtime}"]}
  ],
  "verification": ["schema-v2", "version-bound-markers", "peer-sentinels", "no-owned-temporaries"]
}
-->

Diagnosis first verifies the source schema. Resume reuses a validated staged candidate or builds one beside the source, then atomically commits version and data together. `rollback-export` writes a separate canonical v1 file and does not mutate v2. A complete reopen runs the host owner before container runtime verification. Finally verify the runtime marker, both version-bound host markers, retained peer sentinels, and an empty owned-temporary inventory.
'''

L_FILES = {
    "AGENTS.md": AGENT_INSTRUCTIONS,
    ".devcontainer/devcontainer.json": L_DEVCONTAINER,
    "initialize-host.sh": L_INITIALIZE_BASE,
    "post-create.sh": L_POST_CREATE_BASE,
    "post-start.sh": L_POST_START_BASE,
    "migrate_state.py": L_MIGRATE_BASE,
    "tests/test_migrate.py": L_UNIT_TEST,
    "tests/rebuild.sh": L_REBUILD_TEST,
    "tools/check_recovery_docs.py": L_DOC_TOOL,
}

L_GOOD = {
    "initialize-host.sh": L_GOOD_INITIALIZE,
    "post-create.sh": L_GOOD_POST_CREATE,
    "post-start.sh": L_GOOD_POST_START,
    "migrate_state.py": L_GOOD_MIGRATE,
    "RECOVERY.md": L_GOOD_DOC,
}

L_BAD_VERSION_FIRST = L_MIGRATE_BASE

L_BAD_DELETE_VOLUME = '''#!/usr/bin/env bash
set -euo pipefail
volume_root="$1"; fail_at="${2:-}"; state="$volume_root/state.json"
arguments=(migrate --state "$state")
[[ -n "$fail_at" ]] && arguments+=(--fail-at "$fail_at")
if ! python3 "$(dirname "${BASH_SOURCE[0]}")/migrate_state.py" "${arguments[@]}"; then
    rm -f -- "$state" "$state.migration-journal" "$volume_root/peer-sentinel"
    exit 75
fi
'''

L_BAD_BOOLEAN_MARKERS = L_GOOD_INITIALIZE.replace(
    '''        printf '%s\n' "$expected_marker" > "$marker_tmp"
''',
    '''        printf 'ready\n' > "$marker_tmp"
''',
)

L_BAD_TRUST_STALE = '''#!/usr/bin/env bash
set -euo pipefail
host_root="$1"; volume_root="$2"; runtime_root="$3"
python3 "$(dirname "${BASH_SOURCE[0]}")/migrate_state.py" migrate --state "$volume_root/state.json"
[[ -f "$host_root/markers/host-cli.marker" && -f "$host_root/markers/extension.marker" ]]
mkdir -p "$runtime_root"
printf 'ready\n' > "$runtime_root/runtime.marker"
'''

L_BAD_DOC = '''# Recovery by rebuilding

If anything is stale, delete local state and rebuild everything. Then reopen the container and hope the markers are refreshed. No separate export is necessary.
'''

L_HIDDEN = _hidden_source(
    "HiddenLargeOperationsTests",
    L_FILES,
    {"initialize-host.sh", "post-create.sh", "post-start.sh", "migrate_state.py", "RECOVERY.md"},
    r'''
def test_lifecycle_ownership(self):
    assert_fixture_integrity(self)
    config = json.loads((WORKSPACE / ".devcontainer/devcontainer.json").read_text(encoding="utf-8"))["fixtureLifecycle"]
    self.assertIs(config.get("usesHostDocker"), False)
    self.assertIs(config.get("usesSharedDockerSocket"), False)
    self.assertEqual(
        [(item["id"], item["owner"], item["markerOwners"]) for item in config["stages"]],
        [
            ("initialize-host", "host", ["host-cli", "extension"]),
            ("post-create", "container", ["state-schema"]),
            ("post-start", "container", ["runtime-ready"]),
        ],
    )
    with tempfile.TemporaryDirectory() as raw:
        root = Path(raw); host = root / "host"; volume = root / "volume"; runtime = root / "runtime"
        host.mkdir(); volume.mkdir(); runtime.mkdir()
        (volume / "state.json").write_bytes(canonical_bytes({"version": 1, "jobs": [{"id": "a", "payload": "one"}]}))
        self.assertEqual(run_command(["bash", "initialize-host.sh", str(host), "cli-2", "extension-3"]).returncode, 0)
        self.assertEqual(run_command(["bash", "post-create.sh", str(volume)]).returncode, 0)
        self.assertEqual(run_command(["bash", "post-start.sh", str(host), str(volume), str(runtime)]).returncode, 0)
        self.assertEqual((host / "markers/host-cli.marker").read_text(), "host-cli=cli-2\n")
        self.assertEqual((host / "markers/extension.marker").read_text(), "extension=extension-3\n")
        self.assertIn("schema-v2", (runtime / "runtime.marker").read_text())

def test_migration_fault_cuts(self):
    assert_fixture_integrity(self)
    v1 = {"version": 1, "jobs": [{"id": "b", "payload": "two"}, {"id": "a", "payload": "one"}]}
    v2 = {"version": 2, "items": {"a": {"payload": "one"}, "b": {"payload": "two"}}}
    expected = {"before-stage": (v1, False), "after-stage": (v1, True), "after-commit": (v2, True)}
    with tempfile.TemporaryDirectory() as raw:
        root = Path(raw)
        for cut, (committed, journal_expected) in expected.items():
            with self.subTest(cut=cut):
                state = root / f"{cut}.json"; state.write_bytes(canonical_bytes(v1))
                result = run_command(["python3", "migrate_state.py", "migrate", "--state", str(state), "--fail-at", cut])
                self.assertEqual(result.returncode, 75, result.stderr)
                self.assertEqual(json.loads(state.read_text()), committed)
                self.assertEqual(state.with_name(state.name + ".migration-journal").exists(), journal_expected)
                verify = run_command(["python3", "migrate_state.py", "verify", "--state", str(state)])
                self.assertEqual(verify.returncode, 0, verify.stderr)

def test_reopen_resume(self):
    assert_fixture_integrity(self)
    v1 = {"version": 1, "jobs": [{"id": "a", "payload": "one"}]}
    with tempfile.TemporaryDirectory() as raw:
        root = Path(raw)
        for cut in ("before-stage", "after-stage", "after-commit"):
            with self.subTest(cut=cut):
                case = root / cut; host = case / "host"; volume = case / "volume"; runtime = case / "runtime"
                host.mkdir(parents=True); volume.mkdir(); runtime.mkdir()
                (volume / "state.json").write_bytes(canonical_bytes(v1))
                self.assertEqual(run_command(["bash", "initialize-host.sh", str(host), "cli-2", "extension-3"]).returncode, 0)
                interrupted = run_command(["bash", "post-create.sh", str(volume), cut])
                self.assertEqual(interrupted.returncode, 75, interrupted.stderr)
                self.assertEqual(run_command(["bash", "initialize-host.sh", str(host), "cli-2", "extension-3"]).returncode, 0)
                self.assertEqual(run_command(["bash", "post-create.sh", str(volume)]).returncode, 0)
                command = ["bash", "post-start.sh", str(host), str(volume), str(runtime)]
                self.assertEqual(run_command(command).returncode, 0)
                first = (runtime / "runtime.marker").read_bytes()
                ledger = (host / "repair.log").read_bytes()
                self.assertEqual(run_command(command).returncode, 0)
                self.assertEqual((runtime / "runtime.marker").read_bytes(), first)
                self.assertEqual((host / "repair.log").read_bytes(), ledger)
                self.assertEqual(json.loads((volume / "state.json").read_text())["version"], 2)

def test_marker_verification(self):
    assert_fixture_integrity(self)
    with tempfile.TemporaryDirectory() as raw:
        root = Path(raw); host = root / "host"; volume = root / "volume"; runtime = root / "runtime"
        host.mkdir(); volume.mkdir(); runtime.mkdir()
        (volume / "state.json").write_bytes(canonical_bytes({"version": 2, "items": {}}))
        self.assertEqual(run_command(["bash", "initialize-host.sh", str(host), "cli-2", "extension-3"]).returncode, 0)
        (host / "markers/host-cli.marker").write_text("ready\n", encoding="utf-8")
        (host / "markers/extension.marker").write_text("extension=stale\n", encoding="utf-8")
        start = ["bash", "post-start.sh", str(host), str(volume), str(runtime)]
        self.assertEqual(run_command(start).returncode, 4)
        before = (host / "repair.log").read_text().splitlines()
        self.assertEqual(run_command(["bash", "initialize-host.sh", str(host), "cli-2", "extension-3"]).returncode, 0)
        after = (host / "repair.log").read_text().splitlines()
        self.assertEqual(len(after) - len(before), 2)
        self.assertEqual(run_command(start).returncode, 0)
        self.assertEqual((host / "markers/host-cli.marker").read_text(), "host-cli=cli-2\n")
        self.assertEqual((host / "markers/extension.marker").read_text(), "extension=extension-3\n")

def test_rollback_export(self):
    assert_fixture_integrity(self)
    v1 = {"version": 1, "jobs": [{"id": "b", "payload": "two"}, {"id": "a", "payload": "one"}]}
    canonical_v1 = {"version": 1, "jobs": [{"id": "a", "payload": "one"}, {"id": "b", "payload": "two"}]}
    with tempfile.TemporaryDirectory() as raw:
        state = Path(raw) / "state.json"; output = Path(raw) / "rollback.json"
        state.write_bytes(canonical_bytes(v1))
        self.assertEqual(run_command(["python3", "migrate_state.py", "migrate", "--state", str(state)]).returncode, 0)
        before = state.read_bytes()
        result = run_command(["python3", "migrate_state.py", "rollback", "--state", str(state), "--output", str(output)])
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(state.read_bytes(), before)
        self.assertEqual(output.read_bytes(), canonical_bytes(canonical_v1))
        copy = Path(raw) / "copy.json"; copy.write_bytes(output.read_bytes())
        self.assertEqual(run_command(["python3", "migrate_state.py", "migrate", "--state", str(copy)]).returncode, 0)

def test_recovery_doc(self):
    assert_fixture_integrity(self)
    result = run_command(["python3", "tools/check_recovery_docs.py", "RECOVERY.md"])
    self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
    document = (WORKSPACE / "RECOVERY.md").read_text(encoding="utf-8").lower()
    self.assertIn("rollback-export", document)
    self.assertIn("volume", document)
    self.assertIn("workspace", document)
    self.assertTrue(any(term in document for term in ("never delete", "do not delete", "preserve")))
    self.assertIn("host", document)
    self.assertTrue("runtime" in document or "container" in document)
    self.assertRegex(document, r"host[^.\n]*(?:before|then)[^.\n]*(?:runtime|container)|(?:runtime|container)[^.\n]*after[^.\n]*host")
    self.assertNotRegex(document, r"(?:rm\s+-rf|delete[^.\n]*(?:volume|workspace)[^.\n]*rebuild)")

def test_residual_inventory(self):
    assert_fixture_integrity(self)
    with tempfile.TemporaryDirectory() as raw:
        root = Path(raw); host = root / "host"; volume = root / "volume"; runtime = root / "runtime"
        host.mkdir(); volume.mkdir(); runtime.mkdir()
        for directory in (host, volume, runtime):
            (directory / "peer-sentinel").write_text("keep\n", encoding="utf-8")
        (volume / "state.json").write_bytes(canonical_bytes({"version": 1, "jobs": [{"id": "a", "payload": "one"}]}))
        run_command(["bash", "initialize-host.sh", str(host), "cli-2", "extension-3"])
        run_command(["bash", "post-create.sh", str(volume), "after-stage"])
        self.assertEqual(run_command(["bash", "post-start.sh", str(host), str(volume), str(runtime)]).returncode, 0)
        for directory in (host, volume, runtime):
            self.assertEqual((directory / "peer-sentinel").read_text(), "keep\n")
        self.assertFalse((volume / "state.json.migration-journal").exists())
        self.assertEqual([path for path in root.rglob("*") if path.is_file() and ".tmp." in path.name], [])
''',
)


RECIPES: dict[str, dict[str, Any]] = {
    "f11-s-bash-case-syntax-v1": {
        "case_id": "F11-S-BASH-001",
        "files": S_FILES,
        "hidden": S_HIDDEN,
        "good": {"sync-version.sh": S_GOOD_SCRIPT},
        "executable": ["sync-version.sh", "tests/smoke.sh"],
        "mutants": {
            "nested-if-rewrite": {
                "files": {"sync-version.sh": S_BAD_IF_REWRITE},
                "expected_failed_check_ids": ["ops-minimal-diff"],
                "executable": ["sync-version.sh"],
            },
            "terminator-on-wrong-arm": {
                "files": {"sync-version.sh": S_BAD_WRONG_ARM},
                "expected_failed_check_ids": ["ops-static-pass"],
                "executable": ["sync-version.sh"],
            },
            "changed-auto-precedence": {
                "files": {"sync-version.sh": S_BAD_PRECEDENCE},
                "expected_failed_check_ids": ["ops-behavior-matrix"],
                "executable": ["sync-version.sh"],
            },
        },
    },
    "f11-m-post-start-version-recovery-v1": {
        "case_id": "F11-M-BASH-001",
        "files": M_FILES,
        "hidden": M_HIDDEN,
        "good": {"initialize-host.sh": M_GOOD_INITIALIZE, "post-start.sh": M_GOOD_POST},
        "executable": ["initialize-host.sh", "post-start.sh", "install-cli", "tests/lifecycle.sh"],
        "mutants": {
            "overbroad-version-normalization": {
                "files": {"initialize-host.sh": M_BAD_NORMALIZE_INITIALIZE, "post-start.sh": M_BAD_NORMALIZE_POST},
                "expected_failed_check_ids": ["ops-version-normalization"],
                "executable": ["initialize-host.sh", "post-start.sh"],
            },
            "ready-before-install": {
                "files": {"initialize-host.sh": M_GOOD_INITIALIZE, "post-start.sh": M_BAD_READY_FIRST},
                "expected_failed_check_ids": ["ops-ready-after-verify"],
                "executable": ["initialize-host.sh", "post-start.sh"],
            },
            "always-reinstall": {
                "files": {"initialize-host.sh": M_GOOD_INITIALIZE, "post-start.sh": M_BAD_ALWAYS_INSTALL},
                "expected_failed_check_ids": ["ops-idempotent-install"],
                "executable": ["initialize-host.sh", "post-start.sh"],
            },
            "delete-persistent-state-on-failure": {
                "files": {"initialize-host.sh": M_GOOD_INITIALIZE, "post-start.sh": M_BAD_DELETE_STATE},
                "expected_failed_check_ids": ["ops-state-cleanup"],
                "executable": ["initialize-host.sh", "post-start.sh"],
            },
        },
    },
    "f11-l-devcontainer-rebuild-recovery-v1": {
        "case_id": "F11-L-BASHDOCKER-001",
        "files": L_FILES,
        "hidden": L_HIDDEN,
        "good": L_GOOD,
        "executable": [
            "initialize-host.sh",
            "post-create.sh",
            "post-start.sh",
            "migrate_state.py",
            "tests/rebuild.sh",
            "tools/check_recovery_docs.py",
        ],
        "mutants": {
            "version-marker-before-data": {
                "files": _overlay(L_GOOD, {"migrate_state.py": L_BAD_VERSION_FIRST}),
                "expected_failed_check_ids": ["ops-migration-fault-cuts"],
                "executable": ["initialize-host.sh", "post-create.sh", "post-start.sh", "migrate_state.py"],
            },
            "delete-volume-on-migration-failure": {
                "files": _overlay(L_GOOD, {"post-create.sh": L_BAD_DELETE_VOLUME}),
                "expected_failed_check_ids": ["ops-reopen-resume", "ops-residual-inventory"],
                "executable": ["initialize-host.sh", "post-create.sh", "post-start.sh", "migrate_state.py"],
            },
            "boolean-host-markers": {
                "files": _overlay(L_GOOD, {"initialize-host.sh": L_BAD_BOOLEAN_MARKERS}),
                "expected_failed_check_ids": ["ops-marker-verification"],
                "executable": ["initialize-host.sh", "post-create.sh", "post-start.sh", "migrate_state.py"],
            },
            "trust-stale-host-marker": {
                "files": _overlay(L_GOOD, {"post-start.sh": L_BAD_TRUST_STALE}),
                "expected_failed_check_ids": ["ops-marker-verification"],
                "executable": ["initialize-host.sh", "post-create.sh", "post-start.sh", "migrate_state.py"],
            },
            "rebuild-only-recovery-doc": {
                "files": _overlay(L_GOOD, {"RECOVERY.md": L_BAD_DOC}),
                "expected_failed_check_ids": ["ops-recovery-doc"],
                "executable": ["initialize-host.sh", "post-create.sh", "post-start.sh", "migrate_state.py"],
            },
        },
    },
}
