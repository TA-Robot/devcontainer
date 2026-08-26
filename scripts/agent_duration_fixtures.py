#!/usr/bin/env python3
"""Build isolated disposable repositories for duration-study calibration cases."""

from __future__ import annotations

import copy
import json
import math
import os
from pathlib import Path
import re
import subprocess
import time
from datetime import datetime, timezone
from typing import Any

from agent_contracts import load_json
from agent_duration_study import (
    DurationStudyError,
    ROOT,
    atomic_write_json,
    canonical_json_digest,
    content_digest,
    utc_timestamp,
    validate_case_catalog_record,
    validate_fixture_record,
)


DEFAULT_CATALOG = ROOT / "experiments" / "multi-agent-duration" / "catalog" / "cases.json"
FIXTURE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
FIXED_GIT_DATE = "2026-01-01T00:00:00Z"
AGENT_INSTRUCTIONS = """# AGENTS.md

This repository is a disposable duration-study fixture.

- Work only inside this repository.
- Do not inspect parent directories or search for hidden evaluators or gold artifacts.
- Do not use the network.
- Do not commit, push, or add remotes.
- Follow the task capsule supplied by the harness and run the listed local checks.
"""


S_FILES = {
    "AGENTS.md": AGENT_INSTRUCTIONS,
    "tag_normalizer.py": '''"""Small dependency-free tag normalization."""


def normalize_tag(value: str) -> str:
    return value.strip().lower().replace(" ", "-")
''',
    "tests/test_tag_normalizer.py": '''import unittest

from tag_normalizer import normalize_tag


class TagNormalizerTests(unittest.TestCase):
    def test_trims_and_lowercases_a_simple_value(self):
        self.assertEqual(normalize_tag("  Release Candidate  "), "release-candidate")

    def test_collapses_mixed_separators(self):
        self.assertEqual(normalize_tag("API__  Client"), "api-client")


if __name__ == "__main__":
    unittest.main()
''',
}

S_GOOD = {
    "tag_normalizer.py": '''"""Small dependency-free tag normalization."""


def normalize_tag(value: str) -> str:
    if not isinstance(value, str):
        raise TypeError("tag must be a string")
    output: list[str] = []
    separator_pending = False
    for character in value.strip():
        if character in " _-\\t":
            separator_pending = bool(output)
            continue
        if character.isascii() and character.isalnum():
            if separator_pending and output:
                output.append("-")
            output.append(character.lower())
            separator_pending = False
    result = "".join(output)
    if not result or len(result) > 32:
        raise ValueError("normalized tag must contain 1 to 32 characters")
    return result
''',
}

S_HIDDEN = '''import unittest

from tag_normalizer import normalize_tag


class HiddenTagNormalizerTests(unittest.TestCase):
    def test_separator_runs_and_unsupported_characters(self):
        self.assertEqual(normalize_tag(" A___--\\tB! "), "a-b")

    def test_ascii_contract(self):
        self.assertEqual(normalize_tag("RÉSUMÉ-42"), "rsum-42")

    def test_empty_and_length_bounds(self):
        for value in ("___", "!!!", "éé"):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    normalize_tag(value)
        with self.assertRaises(ValueError):
            normalize_tag("a" * 33)


if __name__ == "__main__":
    unittest.main()
'''


M_FILES = {
    "AGENTS.md": AGENT_INSTRUCTIONS,
    "kvtool/__init__.py": '"""A tiny JSON-backed key/value CLI."""\n',
    "kvtool/store.py": '''from __future__ import annotations

import json
from pathlib import Path


def load_store(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict) or not all(
        isinstance(key, str) and isinstance(item, str) for key, item in value.items()
    ):
        raise ValueError("store must be a JSON object of string values")
    return value


def set_value(path: Path, key: str, value: str) -> None:
    raise NotImplementedError("set persistence is not implemented")
''',
    "kvtool/cli.py": '''from __future__ import annotations

import argparse
from pathlib import Path

from .store import load_store, set_value


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--store", type=Path, required=True)
    commands = parser.add_subparsers(dest="command", required=True)
    get_command = commands.add_parser("get")
    get_command.add_argument("key")
    set_command = commands.add_parser("set")
    set_command.add_argument("key")
    set_command.add_argument("value")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "get":
        values = load_store(args.store)
        if args.key not in values:
            return 3
        print(values[args.key])
        return 0
    set_value(args.store, args.key, args.value)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
''',
    "USAGE.md": '''# kvtool

Read a value with `python3 -m kvtool.cli --store PATH get KEY`.
''',
    "tests/test_store.py": '''import tempfile
import unittest
from pathlib import Path

from kvtool.store import load_store, set_value


class StoreTests(unittest.TestCase):
    def test_missing_store_is_empty(self):
        with tempfile.TemporaryDirectory() as raw:
            self.assertEqual(load_store(Path(raw) / "store.json"), {})

    def test_set_preserves_existing_keys(self):
        with tempfile.TemporaryDirectory() as raw:
            path = Path(raw) / "store.json"
            path.write_text('{"first":"one"}', encoding="utf-8")
            set_value(path, "second", "two")
            self.assertEqual(load_store(path), {"first": "one", "second": "two"})


if __name__ == "__main__":
    unittest.main()
''',
}

M_GOOD = {
    "kvtool/store.py": '''from __future__ import annotations

import json
import os
from pathlib import Path
import tempfile


def load_store(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict) or not all(
        isinstance(key, str) and isinstance(item, str) for key, item in value.items()
    ):
        raise ValueError("store must be a JSON object of string values")
    return value


def set_value(path: Path, key: str, value: str) -> None:
    if not key:
        raise ValueError("key must not be empty")
    values = load_store(path)
    values[key] = value
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(values, handle, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
            handle.write("\\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass
''',
    "kvtool/cli.py": '''from __future__ import annotations

import argparse
from pathlib import Path

from .store import load_store, set_value


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--store", type=Path, required=True)
    commands = parser.add_subparsers(dest="command", required=True)
    get_command = commands.add_parser("get")
    get_command.add_argument("key")
    set_command = commands.add_parser("set")
    set_command.add_argument("key")
    set_command.add_argument("value")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if not args.key:
        return 2
    try:
        if args.command == "get":
            values = load_store(args.store)
            if args.key not in values:
                return 3
            print(values[args.key])
            return 0
        set_value(args.store, args.key, args.value)
        return 0
    except ValueError:
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
''',
    "USAGE.md": '''# kvtool

```bash
python3 -m kvtool.cli --store PATH set KEY VALUE
python3 -m kvtool.cli --store PATH get KEY
```

A missing key exits 3. An empty key exits 2 without changing the store.
''',
}

M_HIDDEN = '''import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


WORKSPACE = Path(os.environ["DURATION_FIXTURE_WORKSPACE"])


def run_cli(*arguments: str) -> subprocess.CompletedProcess[str]:
    environment = dict(os.environ)
    environment["PYTHONPATH"] = str(WORKSPACE)
    return subprocess.run(
        [sys.executable, "-m", "kvtool.cli", *arguments],
        cwd=WORKSPACE,
        env=environment,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


class HiddenKvToolTests(unittest.TestCase):
    def test_cli_round_trip_and_sorted_storage(self):
        with tempfile.TemporaryDirectory() as raw:
            store = Path(raw) / "nested" / "values.json"
            self.assertEqual(run_cli("--store", str(store), "set", "z", "last").returncode, 0)
            self.assertEqual(run_cli("--store", str(store), "set", "a", "first").returncode, 0)
            result = run_cli("--store", str(store), "get", "a")
            self.assertEqual((result.returncode, result.stdout), (0, "first\\n"))
            self.assertEqual(store.read_text(encoding="utf-8"), '{"a":"first","z":"last"}\\n')

    def test_error_codes_do_not_corrupt_state(self):
        with tempfile.TemporaryDirectory() as raw:
            store = Path(raw) / "values.json"
            store.write_text('{"kept":"value"}\\n', encoding="utf-8")
            before = store.read_bytes()
            self.assertEqual(run_cli("--store", str(store), "set", "", "bad").returncode, 2)
            self.assertEqual(store.read_bytes(), before)
            self.assertEqual(run_cli("--store", str(store), "get", "missing").returncode, 3)


if __name__ == "__main__":
    unittest.main()
'''


L_FILES = {
    "AGENTS.md": AGENT_INSTRUCTIONS,
    "queue_store.py": '''from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class UnknownItem(KeyError):
    pass


def load_state(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"version": 1, "items": {}}
    state = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(state, dict) or state.get("version") != 1 or not isinstance(state.get("items"), dict):
        raise ValueError("invalid queue state")
    return state


def save_state(path: Path, state: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, sort_keys=True) + "\\n", encoding="utf-8")


def enqueue(path: Path, item_id: str, payload: str) -> None:
    state = load_state(path)
    state["items"][item_id] = {"payload": payload, "acknowledged": False, "ack_count": 0}
    save_state(path, state)


def acknowledge(path: Path, item_id: str) -> None:
    raise NotImplementedError("acknowledgement is not implemented")


def pending(path: Path) -> list[str]:
    state = load_state(path)
    return sorted(
        item_id for item_id, item in state["items"].items() if not item.get("acknowledged", False)
    )
''',
    "queue_cli.py": '''from __future__ import annotations

import argparse
from pathlib import Path

from queue_store import acknowledge, enqueue, pending


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--store", type=Path, required=True)
    commands = parser.add_subparsers(dest="command", required=True)
    enqueue_command = commands.add_parser("enqueue")
    enqueue_command.add_argument("item_id")
    enqueue_command.add_argument("payload")
    ack_command = commands.add_parser("ack")
    ack_command.add_argument("item_id")
    commands.add_parser("pending")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "enqueue":
        enqueue(args.store, args.item_id, args.payload)
    elif args.command == "ack":
        acknowledge(args.store, args.item_id)
    else:
        for item_id in pending(args.store):
            print(item_id)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
''',
    "bin/queuectl": '''#!/usr/bin/env bash
set -euo pipefail
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec python3 "$script_dir/../queue_cli.py" "$1"
''',
    "FORMAT.md": '''# Queue state format

Version 1 is a JSON object with `version: 1` and an `items` object. Each item stores a payload, an `acknowledged` boolean, and an `ack_count` integer.
''',
    "tests/test_queue_store.py": '''import tempfile
import unittest
from pathlib import Path

from queue_store import acknowledge, enqueue, pending


class QueueStoreTests(unittest.TestCase):
    def test_ack_removes_item_from_pending(self):
        with tempfile.TemporaryDirectory() as raw:
            path = Path(raw) / "queue.json"
            enqueue(path, "item-1", "payload")
            acknowledge(path, "item-1")
            self.assertEqual(pending(path), [])


if __name__ == "__main__":
    unittest.main()
''',
}

L_GOOD = {
    "queue_store.py": '''from __future__ import annotations

import json
import os
from pathlib import Path
import tempfile
from typing import Any


class UnknownItem(KeyError):
    pass


def load_state(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"version": 1, "items": {}}
    state = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(state, dict) or state.get("version") != 1 or not isinstance(state.get("items"), dict):
        raise ValueError("invalid queue state")
    for item_id, item in state["items"].items():
        if not isinstance(item_id, str) or not isinstance(item, dict):
            raise ValueError("invalid queue item")
        if not isinstance(item.get("payload"), str):
            raise ValueError("invalid queue payload")
        if not isinstance(item.get("acknowledged"), bool) or not isinstance(item.get("ack_count"), int):
            raise ValueError("invalid acknowledgement state")
    return state


def save_state(path: Path, state: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(state, handle, sort_keys=True, separators=(",", ":"))
            handle.write("\\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass


def enqueue(path: Path, item_id: str, payload: str) -> None:
    if not item_id:
        raise ValueError("item ID must not be empty")
    state = load_state(path)
    if item_id in state["items"]:
        raise ValueError("item already exists")
    state["items"][item_id] = {"payload": payload, "acknowledged": False, "ack_count": 0}
    save_state(path, state)


def acknowledge(path: Path, item_id: str) -> None:
    state = load_state(path)
    item = state["items"].get(item_id)
    if item is None:
        raise UnknownItem(item_id)
    if item["acknowledged"]:
        return
    item["acknowledged"] = True
    item["ack_count"] += 1
    save_state(path, state)


def pending(path: Path) -> list[str]:
    state = load_state(path)
    return sorted(
        item_id for item_id, item in state["items"].items() if not item["acknowledged"]
    )
''',
    "queue_cli.py": '''from __future__ import annotations

import argparse
import json
from pathlib import Path

from queue_store import UnknownItem, acknowledge, enqueue, pending


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--store", type=Path, required=True)
    commands = parser.add_subparsers(dest="command", required=True)
    enqueue_command = commands.add_parser("enqueue")
    enqueue_command.add_argument("item_id")
    enqueue_command.add_argument("payload")
    ack_command = commands.add_parser("ack")
    ack_command.add_argument("item_id")
    commands.add_parser("pending")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "enqueue":
            enqueue(args.store, args.item_id, args.payload)
        elif args.command == "ack":
            acknowledge(args.store, args.item_id)
        else:
            for item_id in pending(args.store):
                print(item_id)
        return 0
    except UnknownItem:
        return 4
    except (ValueError, json.JSONDecodeError):
        return 5


if __name__ == "__main__":
    raise SystemExit(main())
''',
    "bin/queuectl": '''#!/usr/bin/env bash
set -euo pipefail
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec python3 "$script_dir/../queue_cli.py" "$@"
''',
}

L_HIDDEN = '''import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest


WORKSPACE = Path(os.environ["DURATION_FIXTURE_WORKSPACE"])
QUEUECTL = WORKSPACE / "bin" / "queuectl"


def run_queue(store: Path, *arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [str(QUEUECTL), "--store", str(store), *arguments],
        cwd=WORKSPACE,
        env=dict(os.environ),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


class HiddenQueueLifecycleTests(unittest.TestCase):
    def test_fresh_process_restart_and_idempotent_ack(self):
        with tempfile.TemporaryDirectory() as raw:
            store = Path(raw) / "queue.json"
            self.assertEqual(run_queue(store, "enqueue", "b", "second").returncode, 0)
            self.assertEqual(run_queue(store, "enqueue", "a", "first").returncode, 0)
            pending = run_queue(store, "pending")
            self.assertEqual((pending.returncode, pending.stdout), (0, "a\\nb\\n"))
            self.assertEqual(run_queue(store, "ack", "a").returncode, 0)
            first_ack = store.read_bytes()
            self.assertEqual(run_queue(store, "ack", "a").returncode, 0)
            self.assertEqual(store.read_bytes(), first_ack)
            state = json.loads(store.read_text(encoding="utf-8"))
            self.assertEqual(state["items"]["a"]["ack_count"], 1)
            self.assertEqual(run_queue(store, "pending").stdout, "b\\n")

    def test_unknown_and_malformed_state_are_not_modified(self):
        with tempfile.TemporaryDirectory() as raw:
            store = Path(raw) / "queue.json"
            self.assertEqual(run_queue(store, "enqueue", "kept", "value").returncode, 0)
            before = store.read_bytes()
            self.assertEqual(run_queue(store, "ack", "missing").returncode, 4)
            self.assertEqual(store.read_bytes(), before)
            store.write_text("not-json\\n", encoding="utf-8")
            malformed = store.read_bytes()
            self.assertNotEqual(run_queue(store, "enqueue", "new", "value").returncode, 0)
            self.assertEqual(store.read_bytes(), malformed)


if __name__ == "__main__":
    unittest.main()
'''


RECIPES: dict[str, dict[str, Any]] = {
    "f04-s-python-normalizer-v1": {
        "case_id": "F04-S-PY-001",
        "files": S_FILES,
        "hidden": S_HIDDEN,
        "good": S_GOOD,
        "executable": [],
    },
    "f04-m-python-state-cli-v1": {
        "case_id": "F04-M-PY-001",
        "files": M_FILES,
        "hidden": M_HIDDEN,
        "good": M_GOOD,
        "executable": [],
    },
    "f04-l-python-bash-restart-v1": {
        "case_id": "F04-L-PYBASH-001",
        "files": L_FILES,
        "hidden": L_HIDDEN,
        "good": L_GOOD,
        "executable": ["bin/queuectl"],
    },
}


def _load_catalog(path: Path) -> dict[str, Any]:
    value = load_json(path)
    if not isinstance(value, dict):
        raise DurationStudyError("case catalog root must be an object")
    validate_case_catalog_record(value)
    return value


def _entry_for_case(catalog: dict[str, Any], case_id: str) -> dict[str, Any]:
    matches = [entry for entry in catalog["entries"] if entry["case"]["case_id"] == case_id]
    if len(matches) != 1:
        raise DurationStudyError(f"case catalog does not contain exactly one {case_id!r} entry")
    return matches[0]


def _safe_relative(raw_path: str) -> Path:
    path = Path(raw_path)
    if path.is_absolute() or ".." in path.parts:
        raise DurationStudyError(f"unsafe fixture recipe path: {raw_path}")
    return path


def _write_file(root: Path, raw_path: str, content: str, *, executable: bool = False) -> Path:
    relative = _safe_relative(raw_path)
    path = root / relative
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as handle:
        handle.write(content)
    path.chmod(0o700 if executable else 0o600)
    return path


def _workspace_inventory(workspace: Path) -> list[str]:
    return sorted(
        str(path.relative_to(workspace))
        for path in workspace.rglob("*")
        if path.is_file() and ".git" not in path.relative_to(workspace).parts
    )


def _workspace_tree_digest(workspace: Path, files: list[str]) -> str:
    pieces = bytearray()
    for raw_path in files:
        path = workspace / raw_path
        executable = bool(path.stat().st_mode & 0o111)
        encoded_path = raw_path.encode("utf-8")
        content = path.read_bytes()
        pieces.extend(len(encoded_path).to_bytes(8, "big"))
        pieces.extend(encoded_path)
        pieces.extend(b"x" if executable else b"-")
        pieces.extend(len(content).to_bytes(8, "big"))
        pieces.extend(content)
    return content_digest(bytes(pieces))


def _git_environment(control: Path) -> dict[str, str]:
    environment = dict(os.environ)
    environment.update(
        {
            "HOME": str(control / "git-home"),
            "GIT_CONFIG_GLOBAL": os.devnull,
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_AUTHOR_NAME": "Duration Fixture",
            "GIT_AUTHOR_EMAIL": "duration-fixture@example.invalid",
            "GIT_COMMITTER_NAME": "Duration Fixture",
            "GIT_COMMITTER_EMAIL": "duration-fixture@example.invalid",
            "GIT_AUTHOR_DATE": FIXED_GIT_DATE,
            "GIT_COMMITTER_DATE": FIXED_GIT_DATE,
        }
    )
    (control / "git-home").mkdir(mode=0o700)
    return environment


def _run_git(workspace: Path, environment: dict[str, str], *arguments: str) -> str:
    completed = subprocess.run(
        ["git", *arguments],
        cwd=workspace,
        env=environment,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if completed.returncode != 0:
        raise DurationStudyError(f"fixture git command failed: git {' '.join(arguments)}")
    return completed.stdout.strip()


def _run_check(
    check_id: str,
    argv: list[str],
    *,
    workspace: Path,
    environment: dict[str, str],
    timeout_seconds: float = 30,
) -> dict[str, Any]:
    started = time.monotonic_ns()
    try:
        completed = subprocess.run(
            argv,
            cwd=workspace,
            env=environment,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout_seconds,
            check=False,
        )
        exit_code = completed.returncode
    except subprocess.TimeoutExpired:
        exit_code = 124
    duration_ms = round((time.monotonic_ns() - started) / 1_000_000, 3)
    return {
        "check_id": check_id,
        "status": "pass" if exit_code == 0 else "fail",
        "exit_code": exit_code,
        "duration_ms": duration_ms,
    }


def _evaluate_paths(
    workspace: Path,
    hidden_evaluator: Path,
    workspace_commands: list[list[str]],
    online_evaluator_id: str,
) -> dict[str, Any]:
    environment = {
        "PATH": os.environ.get("PATH", "/usr/local/bin:/usr/bin:/bin"),
        "HOME": "/nonexistent",
        "LANG": "C.UTF-8",
        "LC_ALL": "C.UTF-8",
        "TZ": "UTC",
        "PYTHONDONTWRITEBYTECODE": "1",
        "PYTHONPATH": str(workspace),
        "DURATION_FIXTURE_WORKSPACE": str(workspace),
    }
    workspace_checks = [
        _run_check(
            f"workspace-{index + 1}",
            command,
            workspace=workspace,
            environment=environment,
        )
        for index, command in enumerate(workspace_commands)
    ]
    hidden_check = _run_check(
        online_evaluator_id,
        ["python3", str(hidden_evaluator)],
        workspace=workspace,
        environment=environment,
    )
    all_checks = [*workspace_checks, hidden_check]
    return {
        "status": "pass" if all(item["status"] == "pass" for item in all_checks) else "fail",
        "workspace_checks": workspace_checks,
        "hidden_check": hidden_check,
    }


def build_fixture(
    case_id: str,
    output_dir: Path,
    *,
    catalog_path: Path = DEFAULT_CATALOG,
    fixture_id: str | None = None,
    now: datetime | None = None,
) -> dict[str, Any]:
    catalog = _load_catalog(catalog_path)
    entry = _entry_for_case(catalog, case_id)
    case = entry["case"]
    contract = entry["fixture"]
    recipe = RECIPES.get(contract["recipe_id"])
    if recipe is None or recipe["case_id"] != case_id:
        raise DurationStudyError(f"fixture recipe is not registered for {case_id}")
    if contract["recipe_revision"] != 1:
        raise DurationStudyError(f"unsupported fixture recipe revision for {case_id}")

    observed_at = utc_timestamp(now or datetime.now(timezone.utc))
    chosen_fixture_id = fixture_id or (
        f"{case_id.lower()}-{re.sub(r'[^0-9]', '', observed_at)}-{os.getpid()}"
    )
    if FIXTURE_ID.fullmatch(chosen_fixture_id) is None:
        raise DurationStudyError("fixture ID does not match the fixture schema ID format")
    if output_dir.exists():
        raise DurationStudyError(f"refusing to overwrite fixture directory: {output_dir}")
    output_dir.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    output_dir.mkdir(mode=0o700)
    workspace = output_dir / "workspace"
    control = output_dir / "control"
    workspace.mkdir(mode=0o700)
    control.mkdir(mode=0o700)

    executable_paths = set(recipe["executable"])
    for raw_path, content in recipe["files"].items():
        _write_file(
            workspace,
            raw_path,
            content,
            executable=raw_path in executable_paths,
        )
    hidden_evaluator = _write_file(control, "hidden_tests.py", recipe["hidden"])

    workspace_files = _workspace_inventory(workspace)
    tree_digest = _workspace_tree_digest(workspace, workspace_files)
    git_environment = _git_environment(control)
    _run_git(
        workspace,
        git_environment,
        "init",
        "--quiet",
        "--initial-branch=main",
        "--template=",
    )
    _run_git(workspace, git_environment, "add", "--all")
    _run_git(workspace, git_environment, "commit", "--quiet", "-m", "fixture base")
    base_sha = _run_git(workspace, git_environment, "rev-parse", "HEAD")
    bundle = control / "base.bundle"
    _run_git(workspace, git_environment, "bundle", "create", str(bundle), "main")
    bundle.chmod(0o600)

    initial = _evaluate_paths(
        workspace,
        hidden_evaluator,
        copy.deepcopy(contract["workspace_validation_commands"]),
        contract["online_evaluator_id"],
    )
    if initial["status"] != "fail":
        raise DurationStudyError(f"seeded fixture unexpectedly passes before work: {case_id}")
    if _run_git(workspace, git_environment, "status", "--porcelain"):
        raise DurationStudyError("fixture validation modified the base workspace")

    manifest = {
        "schema_version": 1,
        "fixture_id": chosen_fixture_id,
        "created_at": observed_at,
        "case": {
            "case_id": case_id,
            "revision": case["revision"],
            "catalog_id": catalog["catalog_id"],
            "catalog_revision": catalog["revision"],
            "catalog_digest": canonical_json_digest(catalog),
            "capsule_digest": case["capsule_digest"],
            "recipe_id": contract["recipe_id"],
            "recipe_revision": contract["recipe_revision"],
        },
        "snapshot": {
            "base_sha": base_sha,
            "bundle_digest": content_digest(bundle.read_bytes()),
            "workspace_tree_digest": tree_digest,
            "instruction_set_digest": content_digest(
                (workspace / "AGENTS.md").read_bytes()
            ),
        },
        "execution_contract": {
            "lane": contract["lane"],
            "task_network_policy": contract["task_network_policy"],
            "isolation_required": contract["isolation_required"],
            "evaluator_isolation_required": contract["evaluator_isolation_required"],
            "gold_visibility": contract["gold_visibility"],
            "workspace_validation_commands": copy.deepcopy(
                contract["workspace_validation_commands"]
            ),
            "online_evaluator_id": contract["online_evaluator_id"],
        },
        "paths": {
            "workspace": "workspace",
            "bundle": "control/base.bundle",
            "hidden_evaluator": "control/hidden_tests.py",
        },
        "workspace_files": workspace_files,
        "initial_oracle": {
            "expected": "fail",
            "observed": initial["status"],
            "workspace_checks": initial["workspace_checks"],
            "hidden_check": initial["hidden_check"],
        },
    }
    validate_fixture_record(manifest)
    atomic_write_json(output_dir / "fixture.json", manifest)
    return manifest


def evaluate_fixture(fixture_dir: Path) -> dict[str, Any]:
    """Evaluate checked-in fixture calibration code in a sanitized host environment.

    Do not use this function for live agent artifacts. Their manifest requires a
    network-disabled, read-only evaluator container.
    """

    manifest_value = load_json(fixture_dir / "fixture.json")
    if not isinstance(manifest_value, dict):
        raise DurationStudyError("fixture manifest root must be an object")
    validate_fixture_record(manifest_value)
    workspace = fixture_dir / manifest_value["paths"]["workspace"]
    hidden_evaluator = fixture_dir / manifest_value["paths"]["hidden_evaluator"]
    if not workspace.is_dir() or not hidden_evaluator.is_file():
        raise DurationStudyError("fixture workspace or hidden evaluator is missing")
    return _evaluate_paths(
        workspace,
        hidden_evaluator,
        copy.deepcopy(
            manifest_value["execution_contract"]["workspace_validation_commands"]
        ),
        manifest_value["execution_contract"]["online_evaluator_id"],
    )


def _docker_image_digest(docker_bin: str, image: str) -> str:
    try:
        completed = subprocess.run(
            [docker_bin, "image", "inspect", "--format", "{{.Id}}", image],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=15,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise DurationStudyError("cannot inspect isolated evaluator image") from exc
    digest = completed.stdout.strip()
    if completed.returncode != 0 or re.fullmatch(r"sha256:[0-9a-f]{64}", digest) is None:
        raise DurationStudyError("isolated evaluator image is unavailable or has no exact digest")
    return digest


def _isolated_check(
    check_id: str,
    argv: list[str],
    *,
    docker_bin: str,
    image: str,
    fixture_id: str,
    workspace: Path,
    hidden_evaluator: Path | None,
    timeout_seconds: float,
) -> dict[str, Any]:
    container_name = f"mira-duration-eval-{os.getpid()}-{time.time_ns()}"
    command = [
        docker_bin,
        "run",
        "--rm",
        "--pull",
        "never",
        "--name",
        container_name,
        "--label",
        f"devcontainer.duration-study.fixture={fixture_id}",
        "--network",
        "none",
        "--read-only",
        "--cap-drop",
        "ALL",
        "--security-opt",
        "no-new-privileges",
        "--pids-limit",
        "128",
        "--memory",
        "512m",
        "--cpus",
        "1.0",
        "--ulimit",
        "nofile=256:256",
        "--tmpfs",
        "/tmp:rw,nosuid,nodev,noexec,size=64m,mode=1777",
        "--user",
        f"{os.getuid()}:{os.getgid()}",
        "--workdir",
        "/case",
        "--env",
        "HOME=/tmp",
        "--env",
        "LANG=C.UTF-8",
        "--env",
        "LC_ALL=C.UTF-8",
        "--env",
        "TZ=UTC",
        "--env",
        "PYTHONDONTWRITEBYTECODE=1",
        "--env",
        "PYTHONPATH=/case",
        "--env",
        "DURATION_FIXTURE_WORKSPACE=/case",
        "--mount",
        f"type=bind,src={workspace},dst=/case,readonly",
    ]
    if hidden_evaluator is not None:
        command.extend(
            [
                "--mount",
                f"type=bind,src={hidden_evaluator},dst=/harness/hidden_tests.py,readonly",
            ]
        )
    command.extend([image, *argv])
    started = time.monotonic_ns()
    try:
        completed = subprocess.run(
            command,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=timeout_seconds,
            check=False,
        )
        exit_code = completed.returncode
    except subprocess.TimeoutExpired:
        try:
            subprocess.run(
                [docker_bin, "rm", "--force", container_name],
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=10,
                check=False,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise DurationStudyError(
                f"isolated evaluator timed out and cleanup could not be issued: {container_name}"
            ) from exc
        exit_code = 124
    except OSError as exc:
        raise DurationStudyError("cannot start isolated evaluator container") from exc
    duration_ms = round((time.monotonic_ns() - started) / 1_000_000, 3)
    if exit_code == 125:
        raise DurationStudyError("isolated evaluator container failed before the check started")
    return {
        "check_id": check_id,
        "status": "pass" if exit_code == 0 else "fail",
        "exit_code": exit_code,
        "duration_ms": duration_ms,
    }


def evaluate_fixture_isolated(
    fixture_dir: Path,
    *,
    image: str,
    docker_bin: str = "docker",
    timeout_seconds: float = 30,
) -> dict[str, Any]:
    """Evaluate an agent artifact in a bounded network-disabled container."""

    if not image or len(image) > 512:
        raise DurationStudyError("isolated evaluator image reference is required")
    if not math.isfinite(timeout_seconds) or timeout_seconds <= 0 or timeout_seconds > 300:
        raise DurationStudyError("isolated evaluator timeout must be > 0 and <= 300 seconds")
    manifest_value = load_json(fixture_dir / "fixture.json")
    if not isinstance(manifest_value, dict):
        raise DurationStudyError("fixture manifest root must be an object")
    validate_fixture_record(manifest_value)
    contract = manifest_value["execution_contract"]
    if contract["evaluator_isolation_required"] != "network-disabled-read-only-container":
        raise DurationStudyError("fixture does not authorize the isolated evaluator profile")

    resolved_fixture = fixture_dir.resolve()
    workspace = (resolved_fixture / manifest_value["paths"]["workspace"]).resolve()
    hidden_evaluator = (
        resolved_fixture / manifest_value["paths"]["hidden_evaluator"]
    ).resolve()
    try:
        workspace.relative_to(resolved_fixture)
        hidden_evaluator.relative_to(resolved_fixture)
    except ValueError as exc:
        raise DurationStudyError("fixture evaluator path escapes its owned root") from exc
    if not workspace.is_dir() or not hidden_evaluator.is_file():
        raise DurationStudyError("fixture workspace or hidden evaluator is missing")
    if workspace == hidden_evaluator or workspace in hidden_evaluator.parents:
        raise DurationStudyError("hidden evaluator must remain outside the agent workspace")
    if any("," in str(path) or "\n" in str(path) for path in (workspace, hidden_evaluator)):
        raise DurationStudyError("fixture path cannot be encoded as a Docker bind mount")

    image_digest = _docker_image_digest(docker_bin, image)
    workspace_checks = [
        _isolated_check(
            f"workspace-{index + 1}",
            command,
            docker_bin=docker_bin,
            image=image,
            fixture_id=manifest_value["fixture_id"],
            workspace=workspace,
            hidden_evaluator=None,
            timeout_seconds=timeout_seconds,
        )
        for index, command in enumerate(contract["workspace_validation_commands"])
    ]
    hidden_check = _isolated_check(
        contract["online_evaluator_id"],
        ["python3", "/harness/hidden_tests.py"],
        docker_bin=docker_bin,
        image=image,
        fixture_id=manifest_value["fixture_id"],
        workspace=workspace,
        hidden_evaluator=hidden_evaluator,
        timeout_seconds=timeout_seconds,
    )
    checks = [*workspace_checks, hidden_check]
    return {
        "status": "pass" if all(item["status"] == "pass" for item in checks) else "fail",
        "fixture_id": manifest_value["fixture_id"],
        "case_id": manifest_value["case"]["case_id"],
        "evaluator_id": contract["online_evaluator_id"],
        "isolation": {
            "profile": "network-disabled-read-only-container",
            "image_reference": image,
            "image_digest": image_digest,
            "rootfs": "read-only",
            "workspace_mount": "read-only",
            "hidden_evaluator_mount": "read-only",
            "network": "none",
            "credential_mounts": False,
            "control_bundle_mounted": False,
        },
        "workspace_checks": workspace_checks,
        "hidden_check": hidden_check,
    }


def _install_known_good_for_test(case_id: str, workspace: Path) -> None:
    """Install the private known-good variant for evaluator calibration tests only."""

    recipe = next((item for item in RECIPES.values() if item["case_id"] == case_id), None)
    if recipe is None:
        raise DurationStudyError(f"unknown fixture case: {case_id}")
    for raw_path, content in recipe["good"].items():
        path = workspace / _safe_relative(raw_path)
        path.write_text(content, encoding="utf-8")
        path.chmod(0o700 if raw_path in set(recipe["executable"]) else 0o600)
