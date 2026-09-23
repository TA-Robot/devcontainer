"""Repository-trace duration fixtures for the S, M, and L profiles."""

from __future__ import annotations

import hashlib
import json
from textwrap import dedent, indent
from typing import Any


AGENT_INSTRUCTIONS = """# AGENTS.md

This repository is a disposable duration-study fixture.

- Work only inside this repository.
- Do not inspect parent directories or search for hidden evaluators or gold artifacts.
- Do not use the network.
- Do not modify production code, tests, validation tools, or Git metadata.
- Create only the `trace.json` artifact requested by the task capsule.
- Do not commit, push, or add remotes.
- Run every validation command listed in the task capsule.
"""


TRACE_VALIDATOR = r'''#!/usr/bin/env python3
"""Public structural validation for a repository-trace artifact."""

from __future__ import annotations

import json
from pathlib import Path
import sys


def fail(message: str) -> int:
    print(f"invalid trace: {message}", file=sys.stderr)
    return 1


def main() -> int:
    if len(sys.argv) != 2:
        return fail("usage: validate_trace.py TRACE.json")
    root = Path.cwd().resolve()
    trace_path = (root / sys.argv[1]).resolve()
    try:
        trace_path.relative_to(root)
    except ValueError:
        return fail("artifact escapes the workspace")
    if not trace_path.is_file():
        return fail("artifact does not exist")
    try:
        trace = json.loads(trace_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        return fail(f"artifact is not valid UTF-8 JSON: {exc}")
    if not isinstance(trace, dict) or trace.get("trace_version") != 1:
        return fail("trace_version must be 1")
    nodes = trace.get("nodes")
    edges = trace.get("edges")
    if not isinstance(nodes, list) or not nodes:
        return fail("nodes must be a non-empty array")
    if not isinstance(edges, list) or not edges:
        return fail("edges must be a non-empty array")
    node_ids: set[str] = set()
    for node in nodes:
        if not isinstance(node, dict):
            return fail("each node must be an object")
        node_id = node.get("id")
        path = node.get("path")
        symbol = node.get("symbol")
        if not all(isinstance(value, str) and value for value in (node_id, path, symbol)):
            return fail("every node needs non-empty id, path, and symbol")
        if node_id in node_ids:
            return fail(f"duplicate node id: {node_id}")
        node_ids.add(node_id)
        evidence_path = (root / path).resolve()
        try:
            evidence_path.relative_to(root)
        except ValueError:
            return fail(f"evidence path escapes workspace: {path}")
        if not evidence_path.is_file():
            return fail(f"evidence path does not exist: {path}")
        try:
            source = evidence_path.read_text(encoding="utf-8")
        except (OSError, UnicodeError):
            return fail(f"evidence is not readable UTF-8: {path}")
        if symbol not in source:
            return fail(f"symbol is not present in evidence path: {path}:{symbol}")
        location = node.get("location")
        if location is not None and location not in {"host", "container", "extension"}:
            return fail(f"unsupported location label: {location}")
    for edge in edges:
        if not isinstance(edge, dict):
            return fail("each edge must be an object")
        start = edge.get("from")
        end = edge.get("to")
        if start not in node_ids or end not in node_ids:
            return fail("edge endpoint is not a declared node")
        for optional in ("artifact", "owner"):
            if optional in edge and not isinstance(edge[optional], str):
                return fail(f"edge {optional} must be a string")
    for field in ("contracts", "branches", "recoveries", "uncertainties"):
        if field in trace and not isinstance(trace[field], list):
            return fail(f"{field} must be an array")
    print("trace structure is valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
'''


def _json_file(value: Any) -> str:
    return json.dumps(value, indent=2, sort_keys=True) + "\n"


def _hidden_source(
    class_name: str,
    files: dict[str, str],
    class_body: str,
) -> str:
    protected = {
        path: hashlib.sha256(content.encode("utf-8")).hexdigest()
        for path, content in sorted(files.items())
    }
    header = f'''#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
import unittest


WORKSPACE = Path(os.environ["DURATION_FIXTURE_WORKSPACE"])
PROTECTED_DIGESTS = {protected!r}


def load_trace(testcase):
    path = WORKSPACE / "trace.json"
    testcase.assertTrue(path.is_file(), "trace.json is required")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        testcase.fail(f"trace.json must be valid UTF-8 JSON: {{exc}}")
    testcase.assertIsInstance(value, dict)
    testcase.assertEqual(value.get("trace_version"), 1)
    return value


def assert_fixture_unchanged(testcase):
    for raw_path, expected in PROTECTED_DIGESTS.items():
        path = WORKSPACE / raw_path
        testcase.assertTrue(path.is_file(), f"fixture file was removed: {{raw_path}}")
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        testcase.assertEqual(actual, expected, f"fixture file was modified: {{raw_path}}")
    completed = subprocess.run(
        ["git", "status", "--porcelain=v1", "--untracked-files=all"],
        cwd=WORKSPACE,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    testcase.assertEqual(completed.returncode, 0, completed.stderr)
    testcase.assertEqual(completed.stdout.splitlines(), ["?? trace.json"])


def nodes(trace):
    value = trace.get("nodes")
    return value if isinstance(value, list) else []


def edges(trace):
    value = trace.get("edges")
    return value if isinstance(value, list) else []


def semantic_nodes(trace):
    result = {{}}
    for node in nodes(trace):
        if not isinstance(node, dict):
            continue
        path, symbol, node_id = node.get("path"), node.get("symbol"), node.get("id")
        if all(isinstance(item, str) for item in (path, symbol, node_id)):
            result.setdefault((path, symbol), []).append(node_id)
    return result


def edge_pairs(trace):
    return {{
        (edge.get("from"), edge.get("to"))
        for edge in edges(trace)
        if isinstance(edge, dict)
    }}


def assert_required_semantics(testcase, trace, required):
    found = semantic_nodes(trace)
    for item in required:
        testcase.assertEqual(len(found.get(tuple(item), [])), 1, f"missing or duplicate node: {{item}}")


def assert_semantic_chain(testcase, trace, chain):
    found = semantic_nodes(trace)
    pairs = edge_pairs(trace)
    ids = []
    for item in chain:
        matches = found.get(tuple(item), [])
        testcase.assertEqual(len(matches), 1, f"missing or duplicate chain node: {{item}}")
        ids.append(matches[0])
    for start, end in zip(ids, ids[1:]):
        testcase.assertIn((start, end), pairs, f"missing causal edge: {{start}} -> {{end}}")


def assert_evidence_integrity(testcase, trace, allowed_paths):
    assert_fixture_unchanged(testcase)
    found_nodes = nodes(trace)
    found_edges = edges(trace)
    testcase.assertTrue(found_nodes)
    testcase.assertTrue(found_edges)
    ids = []
    for node in found_nodes:
        testcase.assertIsInstance(node, dict)
        node_id = node.get("id")
        path = node.get("path")
        symbol = node.get("symbol")
        testcase.assertIsInstance(node_id, str)
        testcase.assertTrue(node_id)
        testcase.assertNotIn(node_id, ids)
        ids.append(node_id)
        testcase.assertIn(path, allowed_paths)
        testcase.assertIsInstance(symbol, str)
        testcase.assertTrue(symbol)
        source = (WORKSPACE / path).read_text(encoding="utf-8")
        testcase.assertIn(symbol, source, f"unresolved symbol: {{path}}:{{symbol}}")
    id_set = set(ids)
    adjacency = {{node_id: set() for node_id in ids}}
    for edge in found_edges:
        testcase.assertIsInstance(edge, dict)
        start, end = edge.get("from"), edge.get("to")
        testcase.assertIn(start, id_set)
        testcase.assertIn(end, id_set)
        adjacency[start].add(end)
        adjacency[end].add(start)
    seen = set()
    frontier = [ids[0]]
    while frontier:
        current = frontier.pop()
        if current in seen:
            continue
        seen.add(current)
        frontier.extend(adjacency[current] - seen)
    testcase.assertEqual(seen, id_set, "trace graph must be connected")


class {class_name}(unittest.TestCase):
'''
    footer = '''

if __name__ == "__main__":
    unittest.main()
'''
    return header + indent(dedent(class_body).strip(), "    ") + "\n" + footer


S_FILES = {
    "AGENTS.md": AGENT_INSTRUCTIONS,
    "syncctl/cli.py": '''from __future__ import annotations

import argparse
from pathlib import Path

from syncctl.paths import StateStore, normalize_state_dir, require_owner_marker


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="syncctl")
    parser.add_argument("--state-dir", type=Path, required=True)
    parser.add_argument("key")
    return parser


def run_sync(state_dir: Path, key: str) -> Path:
    normalized = normalize_state_dir(state_dir)
    owned = require_owner_marker(normalized)
    return StateStore(owned).path_for(key)


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    # argparse exposes the option as Namespace.state_dir.
    print(run_sync(args.state_dir, args.key))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
''',
    "syncctl/paths.py": '''from __future__ import annotations

from pathlib import Path


def normalize_state_dir(value: Path) -> Path:
    return value.expanduser().resolve(strict=False)


def require_owner_marker(state_dir: Path) -> Path:
    marker = state_dir / ".syncctl-owner"
    if marker.read_text(encoding="utf-8") != "syncctl\\n":
        raise ValueError("state directory is not owned by syncctl")
    return state_dir


class StateStore:
    def __init__(self, state_dir: Path) -> None:
        self.state_dir = state_dir

    def path_for(self, key: str) -> Path:
        if not key or "/" in key:
            raise ValueError("invalid state key")
        return self.state_dir / f"{key}.json"


def legacy_state_path(root: Path, key: str) -> Path:
    """Unused compatibility helper retained only for old on-disk layouts."""
    return root / "legacy-state" / key
''',
    "tests/test_cli.py": '''import tempfile
import unittest
from pathlib import Path

from syncctl.cli import build_parser, run_sync


class SyncCliTests(unittest.TestCase):
    def test_parser_and_owned_state_path(self):
        with tempfile.TemporaryDirectory() as raw:
            state_dir = Path(raw) / "state"
            state_dir.mkdir()
            (state_dir / ".syncctl-owner").write_text("syncctl\\n", encoding="utf-8")
            args = build_parser().parse_args(["--state-dir", str(state_dir), "jobs"])
            self.assertEqual(args.state_dir, state_dir)
            self.assertEqual(run_sync(args.state_dir, args.key), state_dir / "jobs.json")

    def test_rejects_unowned_directory(self):
        with tempfile.TemporaryDirectory() as raw:
            with self.assertRaises((FileNotFoundError, ValueError)):
                run_sync(Path(raw), "jobs")


if __name__ == "__main__":
    unittest.main()
''',
    "tools/validate_trace.py": TRACE_VALIDATOR,
}

S_REQUIRED = [
    ("syncctl/cli.py", "build_parser"),
    ("syncctl/cli.py", "Namespace.state_dir"),
    ("syncctl/cli.py", "run_sync"),
    ("syncctl/paths.py", "normalize_state_dir"),
    ("syncctl/paths.py", "require_owner_marker"),
    ("syncctl/paths.py", "StateStore"),
]

S_GOOD_TRACE = {
    "trace_version": 1,
    "nodes": [
        {"id": "parser-definition", "path": "syncctl/cli.py", "symbol": "build_parser"},
        {"id": "parsed-field", "path": "syncctl/cli.py", "symbol": "Namespace.state_dir"},
        {"id": "dispatch", "path": "syncctl/cli.py", "symbol": "run_sync"},
        {"id": "normalization", "path": "syncctl/paths.py", "symbol": "normalize_state_dir"},
        {"id": "owner-validation", "path": "syncctl/paths.py", "symbol": "require_owner_marker"},
        {"id": "consumer", "path": "syncctl/paths.py", "symbol": "StateStore"},
    ],
    "edges": [
        {"from": "parser-definition", "to": "parsed-field"},
        {"from": "parsed-field", "to": "dispatch"},
        {"from": "dispatch", "to": "normalization"},
        {"from": "normalization", "to": "owner-validation"},
        {"from": "owner-validation", "to": "consumer"},
    ],
    "uncertainties": [],
}

S_HIDDEN = _hidden_source(
    "HiddenSmallTraceTests",
    S_FILES,
    f'''
def test_required_nodes(self):
    trace = load_trace(self)
    assert_fixture_unchanged(self)
    assert_required_semantics(self, trace, {S_REQUIRED!r})

def test_required_edges(self):
    trace = load_trace(self)
    assert_fixture_unchanged(self)
    assert_semantic_chain(self, trace, {S_REQUIRED!r})

def test_evidence_exists(self):
    trace = load_trace(self)
    assert_evidence_integrity(
        self,
        trace,
        {{"syncctl/cli.py", "syncctl/paths.py"}},
    )

def test_no_distractor(self):
    trace = load_trace(self)
    assert_fixture_unchanged(self)
    encoded = json.dumps(trace, sort_keys=True).lower()
    self.assertNotIn("legacy_state_path", encoded)
    self.assertNotIn("legacy-state", encoded)
''',
)

S_JUMP_TRACE = {
    "trace_version": 1,
    "nodes": [S_GOOD_TRACE["nodes"][0], S_GOOD_TRACE["nodes"][-1]],
    "edges": [{"from": "parser-definition", "to": "consumer"}],
    "uncertainties": [],
}
S_LEGACY_TRACE = {
    "trace_version": 1,
    "nodes": [
        *S_GOOD_TRACE["nodes"][:3],
        {"id": "legacy", "path": "syncctl/paths.py", "symbol": "legacy_state_path"},
        S_GOOD_TRACE["nodes"][-1],
    ],
    "edges": [
        {"from": "parser-definition", "to": "parsed-field"},
        {"from": "parsed-field", "to": "dispatch"},
        {"from": "dispatch", "to": "legacy"},
        {"from": "legacy", "to": "consumer"},
    ],
    "uncertainties": [],
}


M_FILES = {
    "AGENTS.md": AGENT_INSTRUCTIONS,
    "bridge/adapter.py": '''from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class CanonicalEnvelope:
    schema_version: int
    category: str
    status: str
    task_id: str


def normalize_event(payload: Any) -> CanonicalEnvelope:
    if not isinstance(payload, dict) or payload.get("event") != "tool_end":
        raise ValueError("unsupported hook event")
    task_id = payload.get("task_id")
    if not isinstance(task_id, str) or not task_id:
        raise ValueError("tool_end requires task_id")
    return CanonicalEnvelope(1, "tool", "complete", task_id)
''',
    "bridge/reducer.py": '''from __future__ import annotations

from typing import Any

from .adapter import CanonicalEnvelope


def reduce_state(previous: dict[str, Any], envelope: CanonicalEnvelope) -> dict[str, Any]:
    return {
        "schema_version": envelope.schema_version,
        "category": envelope.category,
        "status": envelope.status,
        "task_id": envelope.task_id,
        "sequence": int(previous.get("sequence", 0)) + 1,
    }
''',
    "bridge/store.py": '''from __future__ import annotations

import json
import os
from pathlib import Path
import tempfile
from typing import Any


def read_last_good(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"schema_version": 1, "category": "system", "status": "idle", "task_id": "", "sequence": 0}
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("state must be an object")
    return value


def write_state_atomic(path: Path, state: dict[str, Any]) -> bool:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, raw_temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary = Path(raw_temporary)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(state, handle, sort_keys=True, separators=(",", ":"))
            handle.write("\\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
        return True
    except OSError:
        return False
    finally:
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass
''',
    "bridge/hook.py": '''from __future__ import annotations

from pathlib import Path
from typing import Any

from .adapter import normalize_event
from .reducer import reduce_state
from .store import read_last_good, write_state_atomic


def handle_hook(payload: Any, state_path: Path) -> dict[str, Any]:
    previous = read_last_good(state_path)
    try:
        envelope = normalize_event(payload)
    except ValueError:
        return {"branch": "malformed-input", "state": previous}
    candidate = reduce_state(previous, envelope)
    if not write_state_atomic(state_path, candidate):
        return {"branch": "atomic-write-failure", "state": previous}
    return {"branch": "stored", "state": candidate}
''',
    "bridge/telemetry.py": '''from pathlib import Path


def append_telemetry(ledger: Path, event_name: str) -> None:
    """An unrelated append-only metric; the renderer never reads this file."""
    with ledger.open("a", encoding="utf-8") as handle:
        handle.write(event_name + "\\n")
''',
    "schema/state-v1.json": '''{
  "type": "object",
  "required": ["schema_version", "category", "status", "task_id", "sequence"],
  "properties": {
    "schema_version": {"const": 1},
    "category": {"type": "string"},
    "status": {"type": "string"},
    "task_id": {"type": "string"},
    "sequence": {"type": "integer"}
  }
}
''',
    "media/state.js": '''"use strict";

function decodeState(raw) {
  const value = typeof raw === "string" ? JSON.parse(raw) : raw;
  const required = ["schema_version", "category", "status", "task_id", "sequence"];
  if (!value || value.schema_version !== 1 || required.some((field) => !(field in value))) {
    throw new Error("invalid companion state");
  }
  return value;
}

module.exports = { decodeState };
''',
    "media/world.js": '''"use strict";

const { decodeState } = require("./state.js");

function mapWorldState(state) {
  return state.category === "tool" && state.status === "complete" ? "celebrate" : "idle";
}

function renderWorld(raw) {
  const state = decodeState(raw);
  return { animation: mapWorldState(state), taskId: state.task_id };
}

module.exports = { mapWorldState, renderWorld };
''',
    "media/telemetry.js": '''"use strict";

function readTelemetryLedger(text) {
  return text.split("\\n").filter(Boolean).length;
}

module.exports = { readTelemetryLedger };
''',
    "tests/test_bridge.py": '''import tempfile
import unittest
from pathlib import Path
from unittest import mock

from bridge.hook import handle_hook


class BridgeTests(unittest.TestCase):
    def test_tool_end_is_normalized_and_stored(self):
        with tempfile.TemporaryDirectory() as raw:
            path = Path(raw) / "mira-state.json"
            result = handle_hook({"event": "tool_end", "task_id": "task-7"}, path)
            self.assertEqual(result["branch"], "stored")
            self.assertEqual(result["state"]["status"], "complete")
            self.assertEqual(result["state"]["category"], "tool")

    def test_malformed_input_preserves_last_good(self):
        with tempfile.TemporaryDirectory() as raw:
            path = Path(raw) / "mira-state.json"
            good = handle_hook({"event": "tool_end", "task_id": "kept"}, path)["state"]
            result = handle_hook({"event": "unknown"}, path)
            self.assertEqual(result, {"branch": "malformed-input", "state": good})

    def test_write_failure_preserves_last_good(self):
        with tempfile.TemporaryDirectory() as raw:
            path = Path(raw) / "mira-state.json"
            good = handle_hook({"event": "tool_end", "task_id": "kept"}, path)["state"]
            with mock.patch("bridge.hook.write_state_atomic", return_value=False):
                result = handle_hook({"event": "tool_end", "task_id": "new"}, path)
            self.assertEqual(result, {"branch": "atomic-write-failure", "state": good})


if __name__ == "__main__":
    unittest.main()
''',
    "media/test/world.test.js": '''"use strict";

const test = require("node:test");
const assert = require("node:assert/strict");
const { renderWorld } = require("../world.js");

test("tool completion maps to celebration", () => {
  const rendered = renderWorld(JSON.stringify({
    schema_version: 1,
    category: "tool",
    status: "complete",
    task_id: "task-7",
    sequence: 1,
  }));
  assert.deepEqual(rendered, { animation: "celebrate", taskId: "task-7" });
});
''',
    "tools/validate_trace.py": TRACE_VALIDATOR,
}

M_REQUIRED = [
    ("bridge/adapter.py", "normalize_event"),
    ("bridge/adapter.py", "CanonicalEnvelope"),
    ("bridge/reducer.py", "reduce_state"),
    ("bridge/store.py", "write_state_atomic"),
    ("schema/state-v1.json", '"category"'),
    ("media/state.js", "decodeState"),
    ("media/world.js", "mapWorldState"),
    ("media/world.js", "renderWorld"),
]

M_GOOD_TRACE = {
    "trace_version": 1,
    "nodes": [
        {"id": "adapter", "path": "bridge/adapter.py", "symbol": "normalize_event"},
        {"id": "envelope", "path": "bridge/adapter.py", "symbol": "CanonicalEnvelope"},
        {"id": "reducer", "path": "bridge/reducer.py", "symbol": "reduce_state"},
        {"id": "atomic-store", "path": "bridge/store.py", "symbol": "write_state_atomic"},
        {"id": "state-schema", "path": "schema/state-v1.json", "symbol": '"category"'},
        {"id": "state-decoder", "path": "media/state.js", "symbol": "decodeState"},
        {"id": "state-mapper", "path": "media/world.js", "symbol": "mapWorldState"},
        {"id": "renderer", "path": "media/world.js", "symbol": "renderWorld"},
    ],
    "edges": [
        {"from": "adapter", "to": "envelope"},
        {"from": "envelope", "to": "reducer"},
        {"from": "reducer", "to": "atomic-store"},
        {"from": "atomic-store", "to": "state-schema"},
        {"from": "state-schema", "to": "state-decoder"},
        {"from": "state-decoder", "to": "state-mapper"},
        {"from": "state-mapper", "to": "renderer"},
    ],
    "contracts": [
        {
            "id": "mira-state-v1",
            "producer": "atomic-store",
            "consumer": "state-decoder",
            "path": "schema/state-v1.json",
            "fields": ["schema_version", "category", "status", "task_id", "sequence"],
        }
    ],
    "branches": [
        {
            "id": "malformed-input",
            "from": "adapter",
            "outcome": "last-good-state-unchanged",
            "path": "bridge/hook.py",
            "symbol": "malformed-input",
        },
        {
            "id": "atomic-write-failure",
            "from": "atomic-store",
            "outcome": "last-good-state-retained",
            "path": "bridge/hook.py",
            "symbol": "atomic-write-failure",
        },
    ],
    "uncertainties": [],
}

M_HIDDEN = _hidden_source(
    "HiddenMediumTraceTests",
    M_FILES,
    f'''
def test_success_chain(self):
    trace = load_trace(self)
    assert_fixture_unchanged(self)
    assert_required_semantics(self, trace, {M_REQUIRED!r})
    assert_semantic_chain(self, trace, {M_REQUIRED!r})

def test_schema_boundary(self):
    trace = load_trace(self)
    assert_fixture_unchanged(self)
    found = semantic_nodes(trace)
    store_id = found.get(("bridge/store.py", "write_state_atomic"), [])
    decoder_id = found.get(("media/state.js", "decodeState"), [])
    self.assertEqual(len(store_id), 1)
    self.assertEqual(len(decoder_id), 1)
    contracts = trace.get("contracts")
    self.assertIsInstance(contracts, list)
    matches = [item for item in contracts if isinstance(item, dict) and item.get("id") == "mira-state-v1"]
    self.assertEqual(len(matches), 1)
    contract = matches[0]
    self.assertEqual(contract.get("producer"), store_id[0])
    self.assertEqual(contract.get("consumer"), decoder_id[0])
    self.assertEqual(contract.get("path"), "schema/state-v1.json")
    self.assertEqual(
        set(contract.get("fields", [])),
        {{"schema_version", "category", "status", "task_id", "sequence"}},
    )

def test_fail_open_branches(self):
    trace = load_trace(self)
    assert_fixture_unchanged(self)
    found = semantic_nodes(trace)
    adapter_id = found.get(("bridge/adapter.py", "normalize_event"), [])
    store_id = found.get(("bridge/store.py", "write_state_atomic"), [])
    self.assertEqual(len(adapter_id), 1)
    self.assertEqual(len(store_id), 1)
    branches = trace.get("branches")
    self.assertIsInstance(branches, list)
    observed = {{
        (item.get("id"), item.get("from"), item.get("outcome"))
        for item in branches
        if isinstance(item, dict)
    }}
    self.assertIn(("malformed-input", adapter_id[0], "last-good-state-unchanged"), observed)
    self.assertIn(("atomic-write-failure", store_id[0], "last-good-state-retained"), observed)
    self.assertEqual(len({{item[0] for item in observed if item[0] in {{"malformed-input", "atomic-write-failure"}}}}), 2)

def test_no_telemetry_detour(self):
    trace = load_trace(self)
    assert_fixture_unchanged(self)
    encoded = json.dumps(trace, sort_keys=True).lower()
    self.assertNotIn("telemetry.py", encoded)
    self.assertNotIn("telemetry.js", encoded)
    self.assertNotIn("telemetry-ledger", encoded)

def test_evidence_integrity(self):
    trace = load_trace(self)
    assert_evidence_integrity(
        self,
        trace,
        {{"bridge/adapter.py", "bridge/reducer.py", "bridge/store.py", "schema/state-v1.json", "media/state.js", "media/world.js"}},
    )
    for branch in trace.get("branches", []):
        self.assertIn(branch.get("path"), {{"bridge/hook.py"}})
        self.assertIn(branch.get("symbol"), (WORKSPACE / branch["path"]).read_text(encoding="utf-8"))
''',
)

M_PYTHON_ONLY_TRACE = {
    **M_GOOD_TRACE,
    "nodes": M_GOOD_TRACE["nodes"][:5],
    "edges": M_GOOD_TRACE["edges"][:4],
    "contracts": [],
}
M_MERGED_BRANCH_TRACE = {
    **M_GOOD_TRACE,
    "branches": [
        {
            "id": "hook-error",
            "from": "adapter",
            "outcome": "last-good-state-unchanged",
            "path": "bridge/hook.py",
            "symbol": "malformed-input",
        }
    ],
}
M_TELEMETRY_TRACE = {
    **M_GOOD_TRACE,
    "nodes": [
        *M_GOOD_TRACE["nodes"][:-2],
        {"id": "telemetry", "path": "media/telemetry.js", "symbol": "readTelemetryLedger"},
        *M_GOOD_TRACE["nodes"][-2:],
    ],
    "edges": [
        *M_GOOD_TRACE["edges"][:5],
        {"from": "state-decoder", "to": "telemetry", "artifact": "telemetry-ledger"},
        {"from": "telemetry", "to": "state-mapper"},
        *M_GOOD_TRACE["edges"][-1:],
    ],
}


L_FILES = {
    "AGENTS.md": AGENT_INSTRUCTIONS,
    ".devcontainer/devcontainer.json": '''{
  "name": "mira-lifecycle-fixture",
  "initializeCommand": "bash scripts/initialize-host.sh .provider-source .host-cache",
  "postStartCommand": "bash scripts/post-start.sh .host-cache .runtime",
  "remoteEnv": {
    "MIRA_STATE_PATH": "/workspace-state/mira-state.json"
  }
}
''',
    "scripts/initialize-host.sh": '''#!/usr/bin/env bash
set -euo pipefail

prepare_host_cache() {
    local source_dir="$1"
    local cache_dir="$2"
    if [[ ! -f "$source_dir/provider-cli" ]]; then
        echo "provider wrapper missing; rebuild host cache" >&2
        return 42
    fi
    mkdir -p "$cache_dir/bin"
    cp "$source_dir/provider-cli" "$cache_dir/bin/provider-cli"
    chmod 0755 "$cache_dir/bin/provider-cli"
    printf '{"provider":"fixture","version":"1"}\n' > "$cache_dir/versions.json"
}

if [[ "${BASH_SOURCE[0]}" == "$0" ]]; then
    prepare_host_cache "$1" "$2"
fi
''',
    "scripts/post-start.sh": '''#!/usr/bin/env bash
set -euo pipefail

install_runtime() {
    local cache_dir="$1"
    local runtime_dir="$2"
    if [[ ! -f "$cache_dir/bin/provider-cli" ]]; then
        echo "cached provider wrapper missing; run host initialize" >&2
        return 43
    fi
    mkdir -p "$runtime_dir/bin"
    cp "$cache_dir/bin/provider-cli" "$runtime_dir/bin/provider-cli"
    chmod 0755 "$runtime_dir/bin/provider-cli"
    python3 "$(dirname "${BASH_SOURCE[0]}")/agentctl.py" ready > "$runtime_dir/agentctl-ready.json"
}

if [[ "${BASH_SOURCE[0]}" == "$0" ]]; then
    install_runtime "$1" "$2"
fi
''',
    "scripts/agentctl.py": '''from __future__ import annotations

import argparse
import json
from typing import Any


def make_activity_envelope(provider: str, status: str, sequence: int) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "kind": "provider_activity",
        "provider": provider,
        "status": status,
        "sequence": sequence,
    }


def provider_activity(provider: str, status: str, sequence: int) -> str:
    return json.dumps(make_activity_envelope(provider, status, sequence), sort_keys=True)


def main() -> int:
    parser = argparse.ArgumentParser()
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("ready")
    event = commands.add_parser("event")
    event.add_argument("provider")
    event.add_argument("status")
    event.add_argument("sequence", type=int)
    args = parser.parse_args()
    if args.command == "ready":
        print(json.dumps({"agentctl": "ready"}, sort_keys=True))
    else:
        print(provider_activity(args.provider, args.status, args.sequence))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
''',
    "scripts/mira_hook.py": '''from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys
import tempfile
from typing import Any


EMPTY_STATE = {"schema_version": 1, "provider": "none", "status": "idle", "sequence": 0}


def read_companion_state(path: Path) -> dict[str, Any]:
    if not path.exists():
        return dict(EMPTY_STATE)
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return dict(EMPTY_STATE)
    return value if isinstance(value, dict) else dict(EMPTY_STATE)


def persist_companion_state(path: Path, envelope: dict[str, Any]) -> dict[str, Any]:
    previous = read_companion_state(path)
    if envelope.get("kind") != "provider_activity":
        return previous
    sequence = envelope.get("sequence")
    if not isinstance(sequence, int) or sequence <= int(previous.get("sequence", 0)):
        return previous
    candidate = {
        "schema_version": 1,
        "provider": str(envelope.get("provider", "unknown")),
        "status": str(envelope.get("status", "idle")),
        "sequence": sequence,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, raw_temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary = Path(raw_temporary)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(candidate, handle, sort_keys=True, separators=(",", ":"))
            handle.write("\\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass
    return candidate


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--state", type=Path, required=True)
    args = parser.parse_args()
    try:
        envelope = json.load(sys.stdin)
    except json.JSONDecodeError:
        return 2
    persist_companion_state(args.state, envelope)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
''',
    "scripts/second-agent": '''#!/usr/bin/env bash
set -euo pipefail
echo "legacy compatibility path is feature-frozen" >&2
exit 64
''',
    "extension/world.js": '''"use strict";

const fs = require("node:fs");

const EMPTY_STATE = { schema_version: 1, provider: "none", status: "idle", sequence: 0 };

function readCompanionState(path, lastGood = EMPTY_STATE) {
  try {
    const value = JSON.parse(fs.readFileSync(path, "utf8"));
    if (!value || value.schema_version !== 1 || !Number.isInteger(value.sequence)) {
      throw new Error("invalid companion state");
    }
    return value;
  } catch (_error) {
    return lastGood;
  }
}

function renderWorld(state) {
  return `${state.provider}:${state.status}:${state.sequence}`;
}

module.exports = { EMPTY_STATE, readCompanionState, renderWorld };
''',
    "tests/test_lifecycle.py": '''import tempfile
import unittest
from pathlib import Path

from scripts.agentctl import make_activity_envelope
from scripts.mira_hook import persist_companion_state


class LifecycleTests(unittest.TestCase):
    def test_provider_event_persists_companion_state(self):
        with tempfile.TemporaryDirectory() as raw:
            state = Path(raw) / "persistent" / "mira-state.json"
            envelope = make_activity_envelope("codex", "working", 2)
            observed = persist_companion_state(state, envelope)
            self.assertEqual(observed["provider"], "codex")
            self.assertEqual(observed["sequence"], 2)

    def test_stale_runtime_event_retains_last_good_state(self):
        with tempfile.TemporaryDirectory() as raw:
            state = Path(raw) / "mira-state.json"
            newest = persist_companion_state(state, make_activity_envelope("grok", "done", 8))
            stale = persist_companion_state(state, make_activity_envelope("codex", "working", 7))
            self.assertEqual(stale, newest)


if __name__ == "__main__":
    unittest.main()
''',
    "tests/lifecycle-smoke.sh": '''#!/usr/bin/env bash
set -euo pipefail

fixture_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
temporary="$(mktemp -d)"
trap 'rm -rf -- "$temporary"' EXIT
mkdir -p "$temporary/source"
printf '#!/usr/bin/env bash\nprintf "fixture-provider\\n"\n' > "$temporary/source/provider-cli"
chmod 0755 "$temporary/source/provider-cli"
bash "$fixture_root/scripts/initialize-host.sh" "$temporary/source" "$temporary/cache"
bash "$fixture_root/scripts/post-start.sh" "$temporary/cache" "$temporary/runtime"
test -f "$temporary/runtime/bin/provider-cli"
test -f "$temporary/runtime/agentctl-ready.json"
python3 "$fixture_root/scripts/agentctl.py" event codex working 3 > "$temporary/event.json"
python3 "$fixture_root/scripts/mira_hook.py" --state "$temporary/persistent/mira-state.json" < "$temporary/event.json"
python3 - "$temporary/persistent/mira-state.json" <<'PY'
import json
from pathlib import Path
import sys

state = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
assert state == {"provider": "codex", "schema_version": 1, "sequence": 3, "status": "working"}
PY
''',
    "extension/test/world.test.js": '''"use strict";

const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const os = require("node:os");
const path = require("node:path");
const { readCompanionState, renderWorld } = require("../world.js");

test("extension restart reloads persisted companion state", () => {
  const directory = fs.mkdtempSync(path.join(os.tmpdir(), "mira-world-"));
  try {
    const statePath = path.join(directory, "mira-state.json");
    fs.writeFileSync(statePath, JSON.stringify({schema_version: 1, provider: "codex", status: "done", sequence: 4}));
    const loaded = readCompanionState(statePath);
    assert.equal(renderWorld(loaded), "codex:done:4");
    fs.rmSync(statePath);
    assert.deepEqual(readCompanionState(statePath, loaded), loaded);
  } finally {
    fs.rmSync(directory, {recursive: true, force: true});
  }
});
''',
    "tools/validate_trace.py": TRACE_VALIDATOR,
}

L_REQUIRED = [
    (".devcontainer/devcontainer.json", '"initializeCommand"'),
    ("scripts/initialize-host.sh", "prepare_host_cache"),
    ("scripts/post-start.sh", "install_runtime"),
    ("scripts/agentctl.py", "provider_activity"),
    ("scripts/agentctl.py", "make_activity_envelope"),
    ("scripts/mira_hook.py", "persist_companion_state"),
    ("extension/world.js", "readCompanionState"),
    ("extension/world.js", "renderWorld"),
]

L_GOOD_TRACE = {
    "trace_version": 1,
    "nodes": [
        {"id": "rebuild", "path": ".devcontainer/devcontainer.json", "symbol": '"initializeCommand"', "location": "host"},
        {"id": "host-initialize", "path": "scripts/initialize-host.sh", "symbol": "prepare_host_cache", "location": "host"},
        {"id": "container-start", "path": "scripts/post-start.sh", "symbol": "install_runtime", "location": "container"},
        {"id": "provider-event", "path": "scripts/agentctl.py", "symbol": "provider_activity", "location": "container"},
        {"id": "agentctl-envelope", "path": "scripts/agentctl.py", "symbol": "make_activity_envelope", "location": "container"},
        {"id": "hook-state", "path": "scripts/mira_hook.py", "symbol": "persist_companion_state", "location": "container"},
        {"id": "extension-read", "path": "extension/world.js", "symbol": "readCompanionState", "location": "extension"},
        {"id": "world-render", "path": "extension/world.js", "symbol": "renderWorld", "location": "extension"},
    ],
    "edges": [
        {"from": "rebuild", "to": "host-initialize", "artifact": "initializeCommand", "owner": "devcontainer-host"},
        {"from": "host-initialize", "to": "container-start", "artifact": "provider-wrapper-cache", "owner": "host-provisioner"},
        {"from": "container-start", "to": "provider-event", "artifact": "installed-provider-wrapper", "owner": "container-startup"},
        {"from": "provider-event", "to": "agentctl-envelope", "artifact": "provider-activity-event", "owner": "agentctl"},
        {"from": "agentctl-envelope", "to": "hook-state", "artifact": "activity-envelope-v1", "owner": "mira-hook"},
        {"from": "hook-state", "to": "extension-read", "artifact": "mira-state.json", "owner": "companion-state-bridge"},
        {"from": "extension-read", "to": "world-render", "artifact": "companion-state-v1", "owner": "mira-extension"},
    ],
    "recoveries": [
        {
            "id": "missing-wrapper",
            "owner": "container-startup",
            "recovery": "rebuild-host-cache",
            "retained_state": "existing-companion-state",
        },
        {
            "id": "stale-runtime-state",
            "owner": "mira-hook",
            "recovery": "replace-from-next-provider-event",
            "retained_state": "last-good-companion-state",
        },
        {
            "id": "extension-restart",
            "owner": "mira-extension",
            "recovery": "reload-persisted-companion-state",
            "retained_state": "mira-state.json",
        },
    ],
    "uncertainties": [],
}

L_HIDDEN = _hidden_source(
    "HiddenLargeTraceTests",
    L_FILES,
    f'''
def test_lifecycle_nodes(self):
    trace = load_trace(self)
    assert_fixture_unchanged(self)
    assert_required_semantics(self, trace, {L_REQUIRED!r})
    expected_locations = {{
        (".devcontainer/devcontainer.json", '"initializeCommand"'): "host",
        ("scripts/initialize-host.sh", "prepare_host_cache"): "host",
        ("scripts/post-start.sh", "install_runtime"): "container",
        ("scripts/agentctl.py", "provider_activity"): "container",
        ("scripts/agentctl.py", "make_activity_envelope"): "container",
        ("scripts/mira_hook.py", "persist_companion_state"): "container",
        ("extension/world.js", "readCompanionState"): "extension",
        ("extension/world.js", "renderWorld"): "extension",
    }}
    for node in nodes(trace):
        key = (node.get("path"), node.get("symbol")) if isinstance(node, dict) else None
        if key in expected_locations:
            self.assertEqual(node.get("location"), expected_locations[key])

def test_boundary_artifacts(self):
    trace = load_trace(self)
    assert_fixture_unchanged(self)
    id_to_semantic = {{
        node.get("id"): (node.get("path"), node.get("symbol"))
        for node in nodes(trace)
        if isinstance(node, dict)
    }}
    observed = {{
        (
            id_to_semantic.get(edge.get("from")),
            id_to_semantic.get(edge.get("to")),
            edge.get("artifact"),
            edge.get("owner"),
        )
        for edge in edges(trace)
        if isinstance(edge, dict)
    }}
    expected = {{
        ((".devcontainer/devcontainer.json", '"initializeCommand"'), ("scripts/initialize-host.sh", "prepare_host_cache"), "initializeCommand", "devcontainer-host"),
        (("scripts/initialize-host.sh", "prepare_host_cache"), ("scripts/post-start.sh", "install_runtime"), "provider-wrapper-cache", "host-provisioner"),
        (("scripts/post-start.sh", "install_runtime"), ("scripts/agentctl.py", "provider_activity"), "installed-provider-wrapper", "container-startup"),
        (("scripts/mira_hook.py", "persist_companion_state"), ("extension/world.js", "readCompanionState"), "mira-state.json", "companion-state-bridge"),
        (("extension/world.js", "readCompanionState"), ("extension/world.js", "renderWorld"), "companion-state-v1", "mira-extension"),
    }}
    self.assertTrue(expected.issubset(observed), expected - observed)
    for edge in edges(trace):
        self.assertIsInstance(edge.get("artifact"), str)
        self.assertTrue(edge["artifact"])
        self.assertIsInstance(edge.get("owner"), str)
        self.assertTrue(edge["owner"])

def test_runtime_chain(self):
    trace = load_trace(self)
    assert_fixture_unchanged(self)
    chain = {L_REQUIRED[3:]!r}
    assert_semantic_chain(self, trace, chain)

def test_recovery_ownership(self):
    trace = load_trace(self)
    assert_fixture_unchanged(self)
    recoveries = trace.get("recoveries")
    self.assertIsInstance(recoveries, list)
    observed = {{
        (item.get("id"), item.get("owner"), item.get("recovery"), item.get("retained_state"))
        for item in recoveries
        if isinstance(item, dict)
    }}
    expected = {{
        ("missing-wrapper", "container-startup", "rebuild-host-cache", "existing-companion-state"),
        ("stale-runtime-state", "mira-hook", "replace-from-next-provider-event", "last-good-companion-state"),
        ("extension-restart", "mira-extension", "reload-persisted-companion-state", "mira-state.json"),
    }}
    self.assertTrue(expected.issubset(observed), expected - observed)

def test_no_legacy_path(self):
    trace = load_trace(self)
    assert_fixture_unchanged(self)
    encoded = json.dumps(trace, sort_keys=True).lower()
    self.assertNotIn("second-agent", encoded)
    self.assertNotIn("legacy-wrapper", encoded)

def test_evidence_integrity(self):
    trace = load_trace(self)
    assert_evidence_integrity(
        self,
        trace,
        {{".devcontainer/devcontainer.json", "scripts/initialize-host.sh", "scripts/post-start.sh", "scripts/agentctl.py", "scripts/mira_hook.py", "extension/world.js"}},
    )
''',
)

L_RUNTIME_ONLY_TRACE = {
    **L_GOOD_TRACE,
    "nodes": L_GOOD_TRACE["nodes"][3:],
    "edges": L_GOOD_TRACE["edges"][3:],
}
L_UNLABELLED_TRACE = {
    **L_GOOD_TRACE,
    "edges": [
        {"from": edge["from"], "to": edge["to"]}
        for edge in L_GOOD_TRACE["edges"]
    ],
}
L_LEGACY_TRACE = {
    **L_GOOD_TRACE,
    "nodes": [
        *L_GOOD_TRACE["nodes"][:3],
        {"id": "legacy-wrapper", "path": "scripts/second-agent", "symbol": "legacy compatibility", "location": "container"},
        *L_GOOD_TRACE["nodes"][3:],
    ],
    "edges": [
        *L_GOOD_TRACE["edges"][:3],
        {"from": "provider-event", "to": "legacy-wrapper", "artifact": "provider-activity-event", "owner": "legacy-wrapper"},
        {"from": "legacy-wrapper", "to": "agentctl-envelope", "artifact": "legacy-event", "owner": "legacy-wrapper"},
        *L_GOOD_TRACE["edges"][4:],
    ],
}
L_VAGUE_RECOVERY_TRACE = {
    **L_GOOD_TRACE,
    "recoveries": [
        {"id": "missing-wrapper", "owner": "unknown", "recovery": "retry", "retained_state": "unknown"},
        {"id": "stale-runtime-state", "owner": "unknown", "recovery": "retry", "retained_state": "unknown"},
        {"id": "extension-restart", "owner": "unknown", "recovery": "retry", "retained_state": "unknown"},
    ],
}


RECIPES: dict[str, dict[str, Any]] = {
    "f01-s-python-flag-trace-v1": {
        "case_id": "F01-S-PY-001",
        "files": S_FILES,
        "hidden": S_HIDDEN,
        "good": {"trace.json": _json_file(S_GOOD_TRACE)},
        "executable": ["tools/validate_trace.py"],
        "mutants": {
            "jump-over-validation": {
                "files": {"trace.json": _json_file(S_JUMP_TRACE)},
                "expected_failed_check_ids": ["trace-required-nodes", "trace-required-edges"],
            },
            "legacy-name-follow": {
                "files": {"trace.json": _json_file(S_LEGACY_TRACE)},
                "expected_failed_check_ids": ["trace-no-distractor"],
            },
            "prose-only": {
                "files": {"trace.json": '"The flag goes from argparse to the state store."\n'},
                "expected_failed_check_ids": ["trace-required-nodes", "trace-required-edges"],
            },
        },
    },
    "f01-m-hook-state-render-trace-v1": {
        "case_id": "F01-M-PYJS-001",
        "files": M_FILES,
        "hidden": M_HIDDEN,
        "good": {"trace.json": _json_file(M_GOOD_TRACE)},
        "executable": ["tools/validate_trace.py"],
        "mutants": {
            "python-only": {
                "files": {"trace.json": _json_file(M_PYTHON_ONLY_TRACE)},
                "expected_failed_check_ids": ["trace-success-chain", "trace-schema-boundary"],
            },
            "merged-failure-branches": {
                "files": {"trace.json": _json_file(M_MERGED_BRANCH_TRACE)},
                "expected_failed_check_ids": ["trace-fail-open-branches"],
            },
            "telemetry-detour": {
                "files": {"trace.json": _json_file(M_TELEMETRY_TRACE)},
                "expected_failed_check_ids": ["trace-no-telemetry-detour"],
            },
        },
    },
    "f01-l-devcontainer-companion-trace-v1": {
        "case_id": "F01-L-PYBASHJS-001",
        "files": L_FILES,
        "hidden": L_HIDDEN,
        "good": {"trace.json": _json_file(L_GOOD_TRACE)},
        "executable": [
            "scripts/initialize-host.sh",
            "scripts/post-start.sh",
            "scripts/second-agent",
            "tests/lifecycle-smoke.sh",
            "tools/validate_trace.py",
        ],
        "mutants": {
            "runtime-only": {
                "files": {"trace.json": _json_file(L_RUNTIME_ONLY_TRACE)},
                "expected_failed_check_ids": ["trace-lifecycle-nodes"],
            },
            "unlabelled-boundaries": {
                "files": {"trace.json": _json_file(L_UNLABELLED_TRACE)},
                "expected_failed_check_ids": ["trace-boundary-artifacts"],
            },
            "legacy-wrapper-detour": {
                "files": {"trace.json": _json_file(L_LEGACY_TRACE)},
                "expected_failed_check_ids": ["trace-no-legacy-path"],
            },
            "vague-recovery": {
                "files": {"trace.json": _json_file(L_VAGUE_RECOVERY_TRACE)},
                "expected_failed_check_ids": ["trace-recovery-ownership"],
            },
        },
    },
}
