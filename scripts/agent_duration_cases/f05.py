"""Behavior-preserving refactor and migration duration fixtures."""

from __future__ import annotations

import hashlib
from textwrap import dedent, indent
from typing import Any


AGENT_INSTRUCTIONS = """# AGENTS.md

This repository is a disposable duration-study fixture.

- Work only inside this repository.
- Do not inspect parent directories or search for hidden evaluators or gold artifacts.
- Do not use the network.
- Preserve existing tests and validation tools; add focused tests only when useful.
- Do not commit, push, add remotes, or modify Git metadata.
- Follow the task capsule supplied by the harness and run every listed local check.
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

import ast
import hashlib
import importlib
import inspect
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import warnings


WORKSPACE = Path(os.environ["DURATION_FIXTURE_WORKSPACE"])
PROTECTED_DIGESTS = {protected!r}
MUTABLE_PATHS = {sorted(mutable_paths)!r}


def assert_fixture_integrity(testcase):
    for raw_path, expected in PROTECTED_DIGESTS.items():
        path = WORKSPACE / raw_path
        testcase.assertTrue(path.is_file(), f"fixture file was removed: {{raw_path}}")
        testcase.assertEqual(
            hashlib.sha256(path.read_bytes()).hexdigest(),
            expected,
            f"fixture file was modified: {{raw_path}}",
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
        raw_path = line[3:]
        if " -> " in raw_path:
            raw_path = raw_path.split(" -> ", 1)[1]
        testcase.assertTrue(
            raw_path in MUTABLE_PATHS
            or (line.startswith("?? ") and raw_path.startswith("tests/test_") and raw_path.endswith(".py")),
            f"unexpected fixture change: {{line}}",
        )


def capture(callable_value, argument):
    try:
        return ("return", callable_value(argument))
    except Exception as exc:
        return ("raise", type(exc).__name__, str(exc))


def run_command(*arguments):
    environment = dict(os.environ)
    environment["PYTHONPATH"] = str(WORKSPACE)
    return subprocess.run(
        list(arguments),
        cwd=WORKSPACE,
        env=environment,
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
# S: local helper extraction

S_FILES = {
    "AGENTS.md": AGENT_INSTRUCTIONS,
    "events.py": '''from __future__ import annotations


__all__ = ["emit_event", "tag_event"]


def emit_event(name: str) -> str:
    if not isinstance(name, str):
        raise TypeError("event name must be a string")
    normalized = "-".join(name.strip().lower().replace("_", " ").replace("-", " ").split())
    if not normalized:
        raise ValueError("event name must not be empty")
    if len(normalized) > 12:
        raise ValueError("event name too long")
    return "event:" + normalized


def tag_event(name: str) -> str:
    normalized = "-".join(name.strip().lower().replace("_", " ").replace("-", " ").split())
    candidate = "tag:" + normalized
    if candidate == "tag:":
        raise ValueError("tag name must not be empty")
    if len(candidate) > 16:
        raise ValueError("tag name too long")
    return candidate
''',
    "tests/test_events.py": '''import unittest

from events import emit_event, tag_event


class EventTests(unittest.TestCase):
    def test_normal_outputs(self):
        self.assertEqual(emit_event(" Ready__Event "), "event:ready-event")
        self.assertEqual(tag_event(" Ready__Event "), "tag:ready-event")

    def test_public_validation_stays_distinct(self):
        with self.assertRaisesRegex(TypeError, "event name must be a string"):
            emit_event(None)
        with self.assertRaises(AttributeError):
            tag_event(None)


if __name__ == "__main__":
    unittest.main()
''',
    "tools/compare_behavior.py": '''#!/usr/bin/env python3
from __future__ import annotations

from events import emit_event, tag_event


def capture(callable_value, argument):
    try:
        return ("return", callable_value(argument))
    except Exception as exc:
        return ("raise", type(exc).__name__, str(exc))


EXPECTED = {
    ("emit", " Ready__Event "): ("return", "event:ready-event"),
    ("tag", " Ready__Event "): ("return", "tag:ready-event"),
    ("emit", ""): ("raise", "ValueError", "event name must not be empty"),
    ("tag", ""): ("raise", "ValueError", "tag name must not be empty"),
    ("emit", None): ("raise", "TypeError", "event name must be a string"),
    ("tag", None): ("raise", "AttributeError", "'NoneType' object has no attribute 'strip'"),
}


def main() -> int:
    functions = {"emit": emit_event, "tag": tag_event}
    for (name, value), expected in EXPECTED.items():
        actual = capture(functions[name], value)
        if actual != expected:
            raise SystemExit(f"behavior mismatch for {name}/{value!r}: {actual!r}")
    print("frozen behavior matrix matches")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
''',
}

S_GOOD_EVENTS = '''from __future__ import annotations


__all__ = ["emit_event", "tag_event"]


def _normalize_event_name(value: str) -> str:
    return "-".join(value.strip().lower().replace("_", " ").replace("-", " ").split())


def emit_event(name: str) -> str:
    if not isinstance(name, str):
        raise TypeError("event name must be a string")
    normalized = _normalize_event_name(name)
    if not normalized:
        raise ValueError("event name must not be empty")
    if len(normalized) > 12:
        raise ValueError("event name too long")
    return "event:" + normalized


def tag_event(name: str) -> str:
    normalized = _normalize_event_name(name)
    candidate = "tag:" + normalized
    if candidate == "tag:":
        raise ValueError("tag name must not be empty")
    if len(candidate) > 16:
        raise ValueError("tag name too long")
    return candidate
'''

S_BAD_PREFIX_FIRST = '''from __future__ import annotations


__all__ = ["emit_event", "tag_event"]


def _normalize_event_name(value: str, prefix: str) -> str:
    if not isinstance(value, str):
        raise TypeError("event name must be a string")
    normalized = "-".join(value.strip().lower().replace("_", " ").replace("-", " ").split())
    candidate = prefix + normalized
    if not normalized:
        raise ValueError(prefix[:-1] + " name must not be empty")
    if len(candidate) > (18 if prefix == "event:" else 16):
        raise ValueError(prefix[:-1] + " name too long")
    return candidate


def emit_event(name: str) -> str:
    return _normalize_event_name(name, "event:")


def tag_event(name: str) -> str:
    return _normalize_event_name(name, "tag:")
'''

S_BAD_DUPLICATE_HELPERS = '''from __future__ import annotations


__all__ = ["emit_event", "tag_event"]


def _normalize_emit_name(value: str) -> str:
    return "-".join(value.strip().lower().replace("_", " ").replace("-", " ").split())


def _normalize_tag_name(value: str) -> str:
    return "-".join(value.strip().lower().replace("_", " ").replace("-", " ").split())


def emit_event(name: str) -> str:
    if not isinstance(name, str):
        raise TypeError("event name must be a string")
    normalized = _normalize_emit_name(name)
    if not normalized:
        raise ValueError("event name must not be empty")
    if len(normalized) > 12:
        raise ValueError("event name too long")
    return "event:" + normalized


def tag_event(name: str) -> str:
    normalized = _normalize_tag_name(name)
    candidate = "tag:" + normalized
    if candidate == "tag:":
        raise ValueError("tag name must not be empty")
    if len(candidate) > 16:
        raise ValueError("tag name too long")
    return candidate
'''

S_BAD_PUBLIC_HELPER = S_GOOD_EVENTS.replace(
    '__all__ = ["emit_event", "tag_event"]',
    '__all__ = ["emit_event", "tag_event", "_normalize_event_name"]',
)

S_HIDDEN = _hidden_source(
    "HiddenSmallRefactorTests",
    S_FILES,
    {"events.py"},
    '''
def test_equivalence_output(self):
    assert_fixture_integrity(self)
    import events
    matrix = {
        " Ready Event ": ("event:ready-event", "tag:ready-event"),
        "API__Client": ("event:api-client", "tag:api-client"),
        "a---b": ("event:a-b", "tag:a-b"),
        "ÉX": ("event:éx", "tag:éx"),
        "a" * 12: ("event:" + "a" * 12, "tag:" + "a" * 12),
    }
    for value, expected in matrix.items():
        with self.subTest(value=value):
            self.assertEqual((events.emit_event(value), events.tag_event(value)), expected)

def test_equivalence_errors(self):
    assert_fixture_integrity(self)
    import events
    matrix = [
        (events.emit_event, None, ("raise", "TypeError", "event name must be a string")),
        (events.tag_event, None, ("raise", "AttributeError", "'NoneType' object has no attribute 'strip'")),
        (events.emit_event, "", ("raise", "ValueError", "event name must not be empty")),
        (events.tag_event, "", ("raise", "ValueError", "tag name must not be empty")),
        (events.emit_event, "a" * 13, ("raise", "ValueError", "event name too long")),
        (events.tag_event, "a" * 13, ("raise", "ValueError", "tag name too long")),
    ]
    for function, value, expected in matrix:
        with self.subTest(function=function.__name__, value=value):
            self.assertEqual(capture(function, value), expected)

def test_helper_shared(self):
    assert_fixture_integrity(self)
    tree = ast.parse((WORKSPACE / "events.py").read_text(encoding="utf-8"))
    definitions = {node.name: node for node in tree.body if isinstance(node, ast.FunctionDef)}
    caller_names = {}
    for public_name in ("emit_event", "tag_event"):
        caller_names[public_name] = {
            node.func.id
            for node in ast.walk(definitions[public_name])
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
        }
    shared_private = {
        name
        for name in caller_names["emit_event"] & caller_names["tag_event"]
        if name in definitions and name.startswith("_")
    }
    self.assertEqual(len(shared_private), 1)

def test_api_stable(self):
    assert_fixture_integrity(self)
    import events
    self.assertEqual(events.__all__, ["emit_event", "tag_event"])
    self.assertEqual(list(inspect.signature(events.emit_event).parameters), ["name"])
    self.assertEqual(list(inspect.signature(events.tag_event).parameters), ["name"])
    self.assertEqual(
        {name for name in vars(events) if not name.startswith("_")},
        {"annotations", "emit_event", "tag_event"},
    )
''',
)


# ---------------------------------------------------------------------------
# M: module function to injected codec

M_FILES = {
    "AGENTS.md": AGENT_INSTRUCTIONS,
    "events/__init__.py": '''from .codec import EventCodec, SchemaPolicy, encode_event

__all__ = ["encode_event", "EventCodec", "SchemaPolicy"]
''',
    "events/codec.py": '''from __future__ import annotations

from dataclasses import dataclass
import json
from typing import Any


@dataclass(frozen=True)
class SchemaPolicy:
    version: int = 1


def encode_event(event: dict[str, Any]) -> bytes:
    if not isinstance(event, dict):
        raise TypeError("event must be a dict")
    if not all(isinstance(key, str) for key in event):
        raise ValueError("event keys must be strings")
    document = {"event": event, "schema": 1}
    return json.dumps(document, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


class EventCodec:
    def __init__(self, policy: SchemaPolicy) -> None:
        self.policy = policy

    def encode(self, event: dict[str, Any]) -> bytes:
        raise NotImplementedError("EventCodec migration is incomplete")
''',
    "events/compat.py": '''from __future__ import annotations

from typing import Any

from .codec import EventCodec, SchemaPolicy


def encode_event(event: dict[str, Any]) -> bytes:
    return EventCodec(SchemaPolicy()).encode(event)
''',
    "producer.py": '''from events.codec import encode_event


class Producer:
    def produce(self, event):
        return encode_event(event)
''',
    "ledger.py": '''from events.codec import encode_event


class Ledger:
    def append(self, event):
        return encode_event(event)
''',
    "replay.py": '''from events.codec import encode_event


class Replay:
    def serialize(self, event):
        return encode_event(event)
''',
    "plugins.py": '''import importlib


PLUGIN_REGISTRY = {"event-codec": "events.codec:encode_event"}


def resolve_plugin(name):
    module_name, symbol = PLUGIN_REGISTRY[name].split(":", 1)
    return getattr(importlib.import_module(module_name), symbol)
''',
    "tests/test_codec_migration.py": '''import json
import unittest
import warnings

from events import EventCodec, SchemaPolicy, encode_event
from ledger import Ledger
from producer import Producer
from replay import Replay


class CodecMigrationTests(unittest.TestCase):
    def test_injected_codec_is_shared_by_components(self):
        codec = EventCodec(SchemaPolicy(version=3))
        components = [Producer(codec), Ledger(codec), Replay(codec)]
        for component in components:
            self.assertIs(component.codec, codec)
        outputs = [
            components[0].produce({"id": "one"}),
            components[1].append({"id": "two"}),
            components[2].serialize({"id": "three"}),
        ]
        self.assertTrue(all(json.loads(item)["schema"] == 3 for item in outputs))

    def test_compatibility_export_warns_once(self):
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            encoded = encode_event({"z": 1, "a": 2})
        self.assertEqual(encoded, b'{"event":{"a":2,"z":1},"schema":1}')
        self.assertEqual([item.category for item in caught], [DeprecationWarning])


if __name__ == "__main__":
    unittest.main()
''',
    "tools/check_callers.py": '''#!/usr/bin/env python3
from __future__ import annotations

import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
CALLERS = ["producer.py", "ledger.py", "replay.py"]


def main() -> int:
    for raw_path in CALLERS:
        tree = ast.parse((ROOT / raw_path).read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module == "events.codec":
                if any(alias.name == "encode_event" for alias in node.names):
                    raise SystemExit(f"old codec function remains in {raw_path}")
        source = (ROOT / raw_path).read_text(encoding="utf-8")
        if ".codec.encode(" not in source:
            raise SystemExit(f"injected codec is not used in {raw_path}")
    plugin = (ROOT / "plugins.py").read_text(encoding="utf-8")
    if '"events.codec:EventCodec"' not in plugin or "events.codec:encode_event" in plugin:
        raise SystemExit("reflective codec registry was not migrated")
    print("caller inventory is migrated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
''',
}

M_GOOD_CODEC = '''from __future__ import annotations

from dataclasses import dataclass
import json
from typing import Any


__all__ = ["EventCodec", "SchemaPolicy"]


@dataclass(frozen=True)
class SchemaPolicy:
    version: int = 1

    def __post_init__(self) -> None:
        if not isinstance(self.version, int) or self.version < 1:
            raise ValueError("schema version must be a positive integer")


class EventCodec:
    def __init__(self, policy: SchemaPolicy) -> None:
        self.policy = policy

    def encode(self, event: dict[str, Any]) -> bytes:
        if not isinstance(event, dict):
            raise TypeError("event must be a dict")
        if not all(isinstance(key, str) for key in event):
            raise ValueError("event keys must be strings")
        document = {"event": event, "schema": self.policy.version}
        return json.dumps(
            document,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
'''

M_GOOD_COMPAT = '''from __future__ import annotations

from typing import Any
import warnings

from .codec import EventCodec, SchemaPolicy


__all__ = ["encode_event"]
_COMPAT_CODEC = EventCodec(SchemaPolicy(version=1))


def encode_event(event: dict[str, Any]) -> bytes:
    warnings.warn(
        "encode_event is deprecated; inject EventCodec instead",
        DeprecationWarning,
        stacklevel=2,
    )
    return _COMPAT_CODEC.encode(event)
'''

M_GOOD_INIT = '''from .codec import EventCodec, SchemaPolicy
from .compat import encode_event

__all__ = ["EventCodec", "SchemaPolicy", "encode_event"]
'''

M_COMPONENTS = {
    "producer.py": '''from events.codec import EventCodec


class Producer:
    def __init__(self, codec: EventCodec) -> None:
        self.codec = codec

    def produce(self, event):
        return self.codec.encode(event)
''',
    "ledger.py": '''from events.codec import EventCodec


class Ledger:
    def __init__(self, codec: EventCodec) -> None:
        self.codec = codec

    def append(self, event):
        return self.codec.encode(event)
''',
    "replay.py": '''from events.codec import EventCodec


class Replay:
    def __init__(self, codec: EventCodec) -> None:
        self.codec = codec

    def serialize(self, event):
        return self.codec.encode(event)
''',
}

M_GOOD_PLUGINS = '''import importlib


PLUGIN_REGISTRY = {"event-codec": "events.codec:EventCodec"}


def resolve_plugin(name):
    module_name, symbol = PLUGIN_REGISTRY[name].split(":", 1)
    return getattr(importlib.import_module(module_name), symbol)


def build_plugin(name, policy):
    return resolve_plugin(name)(policy)
'''

M_GOOD = {
    "events/__init__.py": M_GOOD_INIT,
    "events/codec.py": M_GOOD_CODEC,
    "events/compat.py": M_GOOD_COMPAT,
    **M_COMPONENTS,
    "plugins.py": M_GOOD_PLUGINS,
}

M_BAD_PER_CALL_COMPONENTS = {
    path: source.replace(
        "return self.codec.encode(event)",
        "return EventCodec(self.codec.policy).encode(event)",
    )
    for path, source in M_COMPONENTS.items()
}

M_BAD_REFLECTIVE = M_GOOD_PLUGINS.replace(
    '"events.codec:EventCodec"',
    '"events.codec:encode_event"',
)

M_BAD_COMPAT_BYTES = M_GOOD_COMPAT.replace(
    "return _COMPAT_CODEC.encode(event)",
    '''if not isinstance(event, dict):
        raise TypeError("event must be a dict")
    return (json.dumps({"schema": 1, "event": event}, sort_keys=True) + "\\n").encode("utf-8")''',
).replace("import warnings", "import warnings\nimport json")

M_BAD_NESTED_WARNING_CODEC = M_GOOD_CODEC.replace(
    "    def encode(self, event: dict[str, Any]) -> bytes:\n",
    '''    def encode(self, event: dict[str, Any]) -> bytes:
        warnings.warn("nested encode is deprecated", DeprecationWarning, stacklevel=2)
''',
).replace("import json", "import json\nimport warnings")

M_HIDDEN = _hidden_source(
    "HiddenMediumMigrationTests",
    M_FILES,
    {
        "events/__init__.py",
        "events/codec.py",
        "events/compat.py",
        "producer.py",
        "ledger.py",
        "replay.py",
        "plugins.py",
    },
    '''
def test_all_callers(self):
    assert_fixture_integrity(self)
    for raw_path in ("producer.py", "ledger.py", "replay.py"):
        tree = ast.parse((WORKSPACE / raw_path).read_text(encoding="utf-8"))
        imports_old = [
            node
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom)
            and node.module in {"events", "events.codec", "events.compat"}
            and any(alias.name == "encode_event" for alias in node.names)
        ]
        self.assertEqual(imports_old, [], raw_path)
        self.assertIn(".codec.encode(", (WORKSPACE / raw_path).read_text(encoding="utf-8"))
    import plugins
    from events.codec import EventCodec, SchemaPolicy
    self.assertEqual(plugins.PLUGIN_REGISTRY, {"event-codec": "events.codec:EventCodec"})
    policy = SchemaPolicy(version=6)
    plugin = plugins.build_plugin("event-codec", policy)
    self.assertIsInstance(plugin, EventCodec)
    self.assertIs(plugin.policy, policy)

def test_policy_lifecycle(self):
    assert_fixture_integrity(self)
    from events.codec import EventCodec, SchemaPolicy
    from producer import Producer
    from ledger import Ledger
    from replay import Replay
    policy = SchemaPolicy(version=7)
    codec = EventCodec(policy)
    components = [Producer(codec), Ledger(codec), Replay(codec)]
    self.assertTrue(all(component.codec is codec for component in components))
    outputs = [
        components[0].produce({"id": "one"}),
        components[0].produce({"id": "two"}),
        components[1].append({"id": "three"}),
        components[2].serialize({"id": "four"}),
    ]
    self.assertEqual([json.loads(item)["schema"] for item in outputs], [7, 7, 7, 7])
    for raw_path in ("producer.py", "ledger.py", "replay.py"):
        tree = ast.parse((WORKSPACE / raw_path).read_text(encoding="utf-8"))
        methods = [node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef) and node.name != "__init__"]
        for method in methods:
            constructors = [
                node for node in ast.walk(method)
                if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "EventCodec"
            ]
            self.assertEqual(constructors, [], raw_path)

def test_compat_bytes(self):
    assert_fixture_integrity(self)
    from events.compat import encode_event
    normal = [
        ({"z": 1, "a": 2}, b'{"event":{"a":2,"z":1},"schema":1}'),
        ({"message": "é"}, b'{"event":{"message":"\\xc3\\xa9"},"schema":1}'),
        ({}, b'{"event":{},"schema":1}'),
    ]
    for value, expected in normal:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            self.assertEqual(encode_event(value), expected)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        self.assertEqual(capture(encode_event, []), ("raise", "TypeError", "event must be a dict"))
        self.assertEqual(capture(encode_event, {1: "bad"}), ("raise", "ValueError", "event keys must be strings"))

def test_warning_once(self):
    assert_fixture_integrity(self)
    from events.compat import encode_event
    from events.codec import EventCodec, SchemaPolicy
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        encode_event({"outer": {"nested": True}})
    self.assertEqual(len(caught), 1)
    self.assertIs(caught[0].category, DeprecationWarning)
    self.assertIn("inject EventCodec", str(caught[0].message))
    with warnings.catch_warnings(record=True) as direct:
        warnings.simplefilter("always")
        EventCodec(SchemaPolicy(version=2)).encode({"direct": True})
    self.assertEqual(direct, [])

def test_api_surface(self):
    assert_fixture_integrity(self)
    import events
    import events.codec as codec
    import events.compat as compat
    self.assertEqual(events.__all__, ["EventCodec", "SchemaPolicy", "encode_event"])
    self.assertEqual(codec.__all__, ["EventCodec", "SchemaPolicy"])
    self.assertEqual(compat.__all__, ["encode_event"])
    self.assertFalse(hasattr(codec, "encode_event"))
    self.assertEqual(list(inspect.signature(compat.encode_event).parameters), ["event"])
    self.assertEqual(list(inspect.signature(codec.EventCodec).parameters), ["policy"])
''',
)


# ---------------------------------------------------------------------------
# L: backend and persistent schema migration

L_FILES = {
    "AGENTS.md": AGENT_INSTRUCTIONS,
    "jobs/__init__.py": '"""Versioned job ledger."""\n',
    "jobs/backend.py": '''from __future__ import annotations

from typing import Any, Protocol


class JobBackend(Protocol):
    @property
    def backend_name(self) -> str: ...
    def load(self) -> dict[str, Any]: ...
    def load_journal(self) -> dict[str, Any] | None: ...
    def stage_migration(self, source: dict[str, Any], candidate: dict[str, Any]) -> None: ...
    def commit(self, state: dict[str, Any]) -> None: ...
    def clear_journal(self) -> None: ...


class MemoryBackend:
    def __init__(self, initial: dict[str, Any] | None = None) -> None:
        self.state = initial or {"version": 1, "jobs": []}

    @property
    def backend_name(self) -> str:
        return "memory"

    def load(self) -> dict[str, Any]:
        raise NotImplementedError

    def load_journal(self) -> dict[str, Any] | None:
        return None

    def stage_migration(self, source: dict[str, Any], candidate: dict[str, Any]) -> None:
        raise NotImplementedError

    def commit(self, state: dict[str, Any]) -> None:
        self.state = state

    def clear_journal(self) -> None:
        pass
''',
    "jobs/file_backend.py": '''from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class FileBackend:
    def __init__(self, path: Path) -> None:
        self.path = path

    @property
    def backend_name(self) -> str:
        return "file"

    def load(self) -> dict[str, Any]:
        return json.loads(self.path.read_text(encoding="utf-8"))

    def load_journal(self) -> dict[str, Any] | None:
        return None

    def stage_migration(self, source: dict[str, Any], candidate: dict[str, Any]) -> None:
        pass

    def commit(self, state: dict[str, Any]) -> None:
        self.path.write_text(json.dumps(state) + "\\n", encoding="utf-8")

    def clear_journal(self) -> None:
        pass
''',
    "jobs/migrate.py": '''from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .backend import JobBackend


class MigrationInterrupted(RuntimeError):
    pass


def to_v2(state: dict[str, Any]) -> dict[str, Any]:
    return {
        "version": 2,
        "items": {
            item["id"]: {"payload": item["payload"], "status": "done" if item.get("done") else "pending"}
            for item in state.get("jobs", [])
        },
    }


def migrate_backend(backend: JobBackend, fail_at: str | None = None) -> dict[str, Any]:
    state = backend.load()
    state["version"] = 2
    backend.commit(state)
    converted = to_v2(state)
    backend.commit(converted)
    return converted


def export_v1(backend: JobBackend, destination: Path) -> dict[str, Any]:
    state = backend.load()
    state["version"] = 1
    backend.commit(state)
    destination.write_text(json.dumps(state) + "\\n", encoding="utf-8")
    return state
''',
    "jobs/cli.py": '''from __future__ import annotations

import argparse
from pathlib import Path

from .file_backend import FileBackend
from .migrate import migrate_backend


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--state", type=Path, required=True)
    parser.add_argument("command", choices=["list", "migrate"])
    args = parser.parse_args(argv)
    backend = FileBackend(args.state)
    if args.command == "migrate":
        migrate_backend(backend)
    else:
        state = backend.load()
        for item in state.get("jobs", []):
            print(item["id"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
''',
    "bin/jobctl": '''#!/usr/bin/env bash
set -euo pipefail
repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHONPATH="$repo_root${PYTHONPATH:+:$PYTHONPATH}" python3 -m jobs.cli "$1"
''',
    "MIGRATION.md": '''# Job ledger migration

The ledger will eventually move to schema v2. Back up the state before experimenting.
''',
    "tests/test_migration.py": '''import json
import tempfile
import unittest
from pathlib import Path

from jobs.backend import MemoryBackend
from jobs.file_backend import FileBackend
from jobs.migrate import MigrationInterrupted, export_v1, migrate_backend


V1 = {
    "version": 1,
    "jobs": [
        {"id": "a", "payload": "first", "done": False},
        {"id": "b", "payload": "second", "done": True},
    ],
}


class MigrationTests(unittest.TestCase):
    def test_memory_backend_migrates(self):
        backend = MemoryBackend(V1)
        migrated = migrate_backend(backend)
        self.assertEqual(migrated["version"], 2)
        self.assertEqual(sorted(migrated["items"]), ["a", "b"])

    def test_interrupted_file_migration_resumes(self):
        with tempfile.TemporaryDirectory() as raw:
            path = Path(raw) / "jobs.json"
            path.write_text(json.dumps(V1), encoding="utf-8")
            backend = FileBackend(path)
            with self.assertRaises(MigrationInterrupted):
                migrate_backend(backend, fail_at="after-journal")
            migrated = migrate_backend(FileBackend(path))
            self.assertEqual(migrated["version"], 2)

    def test_rollback_export_is_non_destructive(self):
        with tempfile.TemporaryDirectory() as raw:
            path = Path(raw) / "jobs.json"
            output = Path(raw) / "rollback.json"
            path.write_text(json.dumps(V1), encoding="utf-8")
            migrate_backend(FileBackend(path))
            before = path.read_bytes()
            exported = export_v1(FileBackend(path), output)
            self.assertEqual(path.read_bytes(), before)
            self.assertEqual(exported["version"], 1)


if __name__ == "__main__":
    unittest.main()
''',
    "tests/migration-lifecycle.sh": '''#!/usr/bin/env bash
set -euo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
temporary="$(mktemp -d)"
trap 'rm -rf -- "$temporary"' EXIT
state="$temporary/jobs.json"
rollback="$temporary/rollback.json"
printf '%s\n' '{"jobs":[{"done":false,"id":"b","payload":"second"},{"done":false,"id":"a","payload":"first"}],"version":1}' > "$state"
set +e
"$root/bin/jobctl" --backend file --state "$state" migrate --fail-at after-journal
status=$?
set -e
test "$status" -eq 75
"$root/bin/jobctl" --backend file --state "$state" migrate
test "$("$root/bin/jobctl" --backend file --state "$state" list)" = $'a\nb'
"$root/bin/jobctl" --backend file --state "$state" rollback-export --output "$rollback"
python3 - "$state" "$rollback" <<'PY'
import json
from pathlib import Path
import sys

current = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
rollback = json.loads(Path(sys.argv[2]).read_text(encoding="utf-8"))
assert current["version"] == 2
assert rollback["version"] == 1
assert [item["id"] for item in rollback["jobs"]] == ["a", "b"]
PY
''',
    "tools/check_docs.py": '''#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile


START = "<!-- migration-contract"
END = "-->"


def load_manifest(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    if START not in text:
        raise ValueError("migration contract manifest is missing")
    body = text.split(START, 1)[1].split(END, 1)[0]
    value = json.loads(body)
    if not isinstance(value, dict):
        raise ValueError("migration contract must be an object")
    return value


def main() -> int:
    if len(sys.argv) != 2:
        raise SystemExit("usage: check_docs.py MIGRATION.md")
    root = Path.cwd()
    manifest = load_manifest(root / sys.argv[1])
    expected_names = ["migrate", "resume", "rollback"]
    commands = manifest.get("commands")
    if not isinstance(commands, list) or [item.get("name") for item in commands] != expected_names:
        raise SystemExit("documented command manifest is incomplete")
    with tempfile.TemporaryDirectory(prefix="job-migration-doc-") as raw:
        directory = Path(raw)
        state = directory / "jobs.json"
        rollback = directory / "rollback.json"
        state.write_text('{"jobs":[{"done":false,"id":"doc","payload":"value"}],"version":1}\\n', encoding="utf-8")
        values = {"{state}": str(state), "{rollback}": str(rollback)}
        for item in commands:
            argv = [values.get(part, part) for part in item.get("argv", [])]
            completed = subprocess.run(argv, cwd=root, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
            if completed.returncode != 0:
                raise SystemExit(f"documented command failed: {item.get('name')}: {completed.stderr}")
        if json.loads(state.read_text(encoding="utf-8"))["version"] != 2:
            raise SystemExit("documented migration did not commit v2")
        if json.loads(rollback.read_text(encoding="utf-8"))["version"] != 1:
            raise SystemExit("documented rollback did not export v1")
    print("operator command manifest replays successfully")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
''',
}

L_GOOD_BACKEND = '''from __future__ import annotations

import copy
from typing import Any, Protocol


class JobBackend(Protocol):
    @property
    def backend_name(self) -> str: ...
    def load(self) -> dict[str, Any]: ...
    def load_journal(self) -> dict[str, Any] | None: ...
    def stage_migration(self, source: dict[str, Any], candidate: dict[str, Any]) -> None: ...
    def commit(self, state: dict[str, Any]) -> None: ...
    def clear_journal(self) -> None: ...


class MemoryBackend:
    def __init__(self, initial: dict[str, Any] | None = None) -> None:
        self._state = copy.deepcopy(initial or {"version": 1, "jobs": []})
        self._journal: dict[str, Any] | None = None

    @property
    def backend_name(self) -> str:
        return "memory"

    def load(self) -> dict[str, Any]:
        return copy.deepcopy(self._state)

    def load_journal(self) -> dict[str, Any] | None:
        return copy.deepcopy(self._journal)

    def stage_migration(self, source: dict[str, Any], candidate: dict[str, Any]) -> None:
        from .migrate import state_digest
        self._journal = {"source_digest": state_digest(source), "candidate": copy.deepcopy(candidate)}

    def commit(self, state: dict[str, Any]) -> None:
        self._state = copy.deepcopy(state)

    def clear_journal(self) -> None:
        self._journal = None
'''

L_GOOD_FILE_BACKEND = '''from __future__ import annotations

import json
import os
from pathlib import Path
import tempfile
from typing import Any


def canonical_bytes(value: dict[str, Any]) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\\n").encode("utf-8")


def atomic_write(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, raw_temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary = Path(raw_temporary)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(canonical_bytes(value))
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass


class FileBackend:
    def __init__(self, path: Path) -> None:
        self._path = path
        self._journal_path = path.with_name(path.name + ".migration-journal")

    @property
    def backend_name(self) -> str:
        return "file"

    def load(self) -> dict[str, Any]:
        value = json.loads(self._path.read_text(encoding="utf-8"))
        if not isinstance(value, dict) or value.get("version") not in {1, 2}:
            raise ValueError("unsupported job state")
        return value

    def load_journal(self) -> dict[str, Any] | None:
        if not self._journal_path.exists():
            return None
        value = json.loads(self._journal_path.read_text(encoding="utf-8"))
        if not isinstance(value, dict):
            raise ValueError("invalid migration journal")
        return value

    def stage_migration(self, source: dict[str, Any], candidate: dict[str, Any]) -> None:
        from .migrate import state_digest
        atomic_write(
            self._journal_path,
            {"source_digest": state_digest(source), "candidate": candidate},
        )

    def commit(self, state: dict[str, Any]) -> None:
        atomic_write(self._path, state)

    def clear_journal(self) -> None:
        self._journal_path.unlink(missing_ok=True)
'''

L_GOOD_MIGRATE = '''from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import tempfile
from typing import Any

from .backend import JobBackend


class MigrationInterrupted(RuntimeError):
    pass


def canonical_bytes(value: dict[str, Any]) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\\n").encode("utf-8")


def state_digest(value: dict[str, Any]) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def _validate_v1(state: dict[str, Any]) -> None:
    if state.get("version") != 1 or not isinstance(state.get("jobs"), list):
        raise ValueError("invalid v1 job state")
    ids = []
    for item in state["jobs"]:
        if not isinstance(item, dict) or not isinstance(item.get("id"), str):
            raise ValueError("invalid v1 job")
        if not isinstance(item.get("payload"), str) or not isinstance(item.get("done"), bool):
            raise ValueError("invalid v1 job fields")
        ids.append(item["id"])
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate v1 job ID")


def _validate_v2(state: dict[str, Any]) -> None:
    if state.get("version") != 2 or not isinstance(state.get("items"), dict):
        raise ValueError("invalid v2 job state")
    for item_id, item in state["items"].items():
        if not isinstance(item_id, str) or not isinstance(item, dict):
            raise ValueError("invalid v2 job")
        if not isinstance(item.get("payload"), str) or item.get("status") not in {"pending", "done"}:
            raise ValueError("invalid v2 job fields")


def to_v2(state: dict[str, Any]) -> dict[str, Any]:
    _validate_v1(state)
    return {
        "version": 2,
        "items": {
            item["id"]: {
                "payload": item["payload"],
                "status": "done" if item["done"] else "pending",
            }
            for item in sorted(state["jobs"], key=lambda item: item["id"])
        },
    }


def to_v1(state: dict[str, Any]) -> dict[str, Any]:
    if state.get("version") == 1:
        _validate_v1(state)
        return state
    _validate_v2(state)
    return {
        "version": 1,
        "jobs": [
            {
                "id": item_id,
                "payload": item["payload"],
                "done": item["status"] == "done",
            }
            for item_id, item in sorted(state["items"].items())
        ],
    }


def migrate_backend(backend: JobBackend, fail_at: str | None = None) -> dict[str, Any]:
    current = backend.load()
    if current.get("version") == 2:
        _validate_v2(current)
        backend.clear_journal()
        return current
    _validate_v1(current)
    if fail_at == "before-journal":
        raise MigrationInterrupted("interrupted before journal")
    journal = backend.load_journal()
    if journal is None:
        candidate = to_v2(current)
        backend.stage_migration(current, candidate)
    else:
        if journal.get("source_digest") != state_digest(current):
            raise ValueError("migration journal does not match source")
        candidate = journal.get("candidate")
        if not isinstance(candidate, dict):
            raise ValueError("migration journal candidate is invalid")
        _validate_v2(candidate)
    if fail_at == "after-journal":
        raise MigrationInterrupted("interrupted after journal")
    backend.commit(candidate)
    if fail_at == "after-commit":
        raise MigrationInterrupted("interrupted after commit")
    backend.clear_journal()
    return candidate


def export_v1(backend: JobBackend, destination: Path) -> dict[str, Any]:
    exported = to_v1(backend.load())
    destination.parent.mkdir(parents=True, exist_ok=True)
    descriptor, raw_temporary = tempfile.mkstemp(prefix=f".{destination.name}.", dir=destination.parent)
    temporary = Path(raw_temporary)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(canonical_bytes(exported))
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, destination)
    finally:
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass
    return exported
'''

L_GOOD_CLI = '''from __future__ import annotations

import argparse
from pathlib import Path

from .backend import JobBackend, MemoryBackend
from .file_backend import FileBackend
from .migrate import MigrationInterrupted, export_v1, migrate_backend, to_v1


def build_backend(kind: str, state_path: Path) -> JobBackend:
    if kind == "file":
        return FileBackend(state_path)
    if kind == "memory":
        return MemoryBackend()
    raise ValueError(f"unsupported backend: {kind}")


def list_jobs(backend: JobBackend) -> list[str]:
    state = to_v1(backend.load())
    return sorted(item["id"] for item in state["jobs"])


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--backend", choices=["file", "memory"], required=True)
    parser.add_argument("--state", type=Path, required=True)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("list")
    migrate = commands.add_parser("migrate")
    migrate.add_argument("--fail-at", choices=["before-journal", "after-journal", "after-commit"])
    rollback = commands.add_parser("rollback-export")
    rollback.add_argument("--output", type=Path, required=True)
    commands.add_parser("backend")
    args = parser.parse_args(argv)
    backend = build_backend(args.backend, args.state)
    try:
        if args.command == "list":
            for item_id in list_jobs(backend):
                print(item_id)
        elif args.command == "migrate":
            migrate_backend(backend, fail_at=args.fail_at)
        elif args.command == "rollback-export":
            export_v1(backend, args.output)
        else:
            print(backend.backend_name)
        return 0
    except MigrationInterrupted:
        return 75
    except (OSError, ValueError):
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
'''

L_GOOD_WRAPPER = '''#!/usr/bin/env bash
set -euo pipefail
repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export PYTHONPATH="$repo_root${PYTHONPATH:+:$PYTHONPATH}"
exec python3 -m jobs.cli "$@"
'''

L_GOOD_DOC = '''# Job ledger backend and schema migration

The job-state operator owns migration, the pre-migration backup, and recovery. Preserve a copy at `STATE.pre-migration` before the first command. A committed v2 file is always complete; an interrupted journal is resumed by running the same migration command again. Rollback writes a separate v1 export and never replaces the v2 source.

<!-- migration-contract
{
  "owner": "job-state-operator",
  "backup": "{state}.pre-migration",
  "failure_recovery": {
    "before-journal": "rerun-migrate",
    "after-journal": "rerun-migrate",
    "after-commit": "rerun-migrate"
  },
  "commands": [
    {
      "name": "migrate",
      "argv": ["bin/jobctl", "--backend", "file", "--state", "{state}", "migrate"]
    },
    {
      "name": "resume",
      "argv": ["bin/jobctl", "--backend", "file", "--state", "{state}", "migrate"]
    },
    {
      "name": "rollback",
      "argv": ["bin/jobctl", "--backend", "file", "--state", "{state}", "rollback-export", "--output", "{rollback}"]
    }
  ]
}
-->

The `--backend file` selection is forwarded unchanged by `bin/jobctl`. Inspect and retain the migration journal after failure; do not delete the source, journal, or backup before a successful resume and rollback export.
'''

L_GOOD = {
    "jobs/backend.py": L_GOOD_BACKEND,
    "jobs/file_backend.py": L_GOOD_FILE_BACKEND,
    "jobs/migrate.py": L_GOOD_MIGRATE,
    "jobs/cli.py": L_GOOD_CLI,
    "bin/jobctl": L_GOOD_WRAPPER,
    "MIGRATION.md": L_GOOD_DOC,
}

L_BAD_EARLY_MARKER = L_GOOD_MIGRATE.replace(
    '''    if journal is None:
        candidate = to_v2(current)
        backend.stage_migration(current, candidate)
''',
    '''    if journal is None:
        backend.commit({"version": 2, "items": {}})
        candidate = to_v2(current)
        backend.stage_migration(current, candidate)
''',
)

L_BAD_LEAK_FILE = L_GOOD_FILE_BACKEND.replace("self._path", "self.path")
L_BAD_LEAK_CLI = L_GOOD_CLI.replace(
    '''def list_jobs(backend: JobBackend) -> list[str]:
    state = to_v1(backend.load())
''',
    '''def list_jobs(backend: JobBackend) -> list[str]:
    if backend.backend_name == "file":
        backend.path.read_bytes()
    state = to_v1(backend.load())
''',
)

L_BAD_DUPLICATE_RESUME = L_GOOD_MIGRATE.replace(
    '''        candidate = journal.get("candidate")
        if not isinstance(candidate, dict):
''',
    '''        candidate = journal.get("candidate")
        if isinstance(candidate, dict) and isinstance(candidate.get("items"), dict):
            for item_id, item in list(candidate["items"].items()):
                candidate["items"][item_id + "-resume"] = dict(item)
        if not isinstance(candidate, dict):
''',
)

L_BAD_DESTRUCTIVE_ROLLBACK = L_GOOD_MIGRATE.replace(
    '''def export_v1(backend: JobBackend, destination: Path) -> dict[str, Any]:
    exported = to_v1(backend.load())
''',
    '''def export_v1(backend: JobBackend, destination: Path) -> dict[str, Any]:
    exported = to_v1(backend.load())
    backend.commit(exported)
''',
)

L_BAD_WRAPPER = '''#!/usr/bin/env bash
set -euo pipefail
repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export PYTHONPATH="$repo_root${PYTHONPATH:+:$PYTHONPATH}"
if [[ "${1:-}" == "--backend" ]]; then
    shift 2
fi
exec python3 -m jobs.cli --backend file "$@"
'''

L_HIDDEN = _hidden_source(
    "HiddenLargeMigrationTests",
    L_FILES,
    {
        "jobs/backend.py",
        "jobs/file_backend.py",
        "jobs/migrate.py",
        "jobs/cli.py",
        "bin/jobctl",
        "MIGRATION.md",
    },
    '''
V1 = {
    "version": 1,
    "jobs": [
        {"id": "b", "payload": "second", "done": True},
        {"id": "a", "payload": "first", "done": False},
    ],
}
V1_CANONICAL = {
    "version": 1,
    "jobs": [
        {"id": "a", "payload": "first", "done": False},
        {"id": "b", "payload": "second", "done": True},
    ],
}
V2 = {
    "version": 2,
    "items": {
        "a": {"payload": "first", "status": "pending"},
        "b": {"payload": "second", "status": "done"},
    },
}

def write_v1(self, path):
    path.write_bytes(canonical_bytes(self.V1))

def assert_valid_committed(self, state):
    self.assertIn(state.get("version"), {1, 2})
    if state["version"] == 1:
        self.assertEqual(state, self.V1)
    else:
        self.assertEqual(state, self.V2)

def test_v1_compat(self):
    assert_fixture_integrity(self)
    from jobs.backend import MemoryBackend
    from jobs.cli import list_jobs
    from jobs.file_backend import FileBackend
    with tempfile.TemporaryDirectory() as raw:
        path = Path(raw) / "jobs.json"
        self.write_v1(path)
        self.assertEqual(FileBackend(path).load(), self.V1)
        self.assertEqual(list_jobs(FileBackend(path)), ["a", "b"])
        self.assertEqual(list_jobs(MemoryBackend(self.V1)), ["a", "b"])
        result = run_command(sys.executable, "-m", "jobs.cli", "--backend", "file", "--state", str(path), "list")
        self.assertEqual((result.returncode, result.stdout), (0, "a\\nb\\n"))

def test_backend_boundary(self):
    assert_fixture_integrity(self)
    for raw_path in ("jobs/cli.py", "jobs/migrate.py"):
        tree = ast.parse((WORKSPACE / raw_path).read_text(encoding="utf-8"))
        leaked = [
            node for node in ast.walk(tree)
            if isinstance(node, ast.Attribute) and node.attr in {"path", "_path", "_journal_path"}
        ]
        self.assertEqual(leaked, [], raw_path)
    with tempfile.TemporaryDirectory() as raw:
        state = Path(raw) / "unused.json"
        result = run_command(str(WORKSPACE / "bin/jobctl"), "--backend", "memory", "--state", str(state), "backend")
        self.assertEqual((result.returncode, result.stdout), (0, "memory\\n"))
        self.assertFalse(state.exists())

def test_atomic_order(self):
    assert_fixture_integrity(self)
    from jobs.file_backend import FileBackend
    from jobs.migrate import MigrationInterrupted, migrate_backend
    expected = {
        "before-journal": (self.V1, False),
        "after-journal": (self.V1, True),
        "after-commit": (self.V2, True),
    }
    with tempfile.TemporaryDirectory() as raw:
        for cut, (committed, journal_expected) in expected.items():
            with self.subTest(cut=cut):
                path = Path(raw) / f"{cut}.json"
                self.write_v1(path)
                backend = FileBackend(path)
                with self.assertRaises(MigrationInterrupted):
                    migrate_backend(backend, fail_at=cut)
                observed = json.loads(path.read_text(encoding="utf-8"))
                self.assert_valid_committed(observed)
                self.assertEqual(observed, committed)
                journal = path.with_name(path.name + ".migration-journal")
                self.assertEqual(journal.exists(), journal_expected)
                if journal.exists():
                    staged = json.loads(journal.read_text(encoding="utf-8"))
                    self.assertEqual(staged.get("candidate"), self.V2)

def test_resume(self):
    assert_fixture_integrity(self)
    with tempfile.TemporaryDirectory() as raw:
        for cut in ("before-journal", "after-journal", "after-commit"):
            with self.subTest(cut=cut):
                path = Path(raw) / f"resume-{cut}.json"
                self.write_v1(path)
                interrupted = run_command(
                    sys.executable, "-m", "jobs.cli", "--backend", "file", "--state", str(path),
                    "migrate", "--fail-at", cut,
                )
                self.assertEqual(interrupted.returncode, 75, interrupted.stderr)
                resumed = run_command(sys.executable, "-m", "jobs.cli", "--backend", "file", "--state", str(path), "migrate")
                self.assertEqual(resumed.returncode, 0, resumed.stderr)
                first = path.read_bytes()
                repeated = run_command(sys.executable, "-m", "jobs.cli", "--backend", "file", "--state", str(path), "migrate")
                self.assertEqual(repeated.returncode, 0, repeated.stderr)
                self.assertEqual(path.read_bytes(), first)
                self.assertEqual(json.loads(first), self.V2)
                self.assertFalse(path.with_name(path.name + ".migration-journal").exists())

def test_rollback(self):
    assert_fixture_integrity(self)
    from jobs.file_backend import FileBackend
    from jobs.migrate import export_v1, migrate_backend, to_v2
    with tempfile.TemporaryDirectory() as raw:
        path = Path(raw) / "jobs.json"
        rollback = Path(raw) / "rollback.json"
        self.write_v1(path)
        migrate_backend(FileBackend(path))
        source_before = path.read_bytes()
        exported = export_v1(FileBackend(path), rollback)
        self.assertEqual(path.read_bytes(), source_before)
        self.assertEqual(rollback.read_bytes(), canonical_bytes(exported))
        self.assertEqual(exported, self.V1_CANONICAL)
        self.assertEqual(to_v2(exported), self.V2)

def test_operations_doc(self):
    assert_fixture_integrity(self)
    from tools.check_docs import load_manifest
    manifest = load_manifest(WORKSPACE / "MIGRATION.md")
    self.assertEqual(manifest.get("owner"), "job-state-operator")
    self.assertEqual(manifest.get("backup"), "{state}.pre-migration")
    self.assertEqual(
        manifest.get("failure_recovery"),
        {
            "before-journal": "rerun-migrate",
            "after-journal": "rerun-migrate",
            "after-commit": "rerun-migrate",
        },
    )
    result = run_command(sys.executable, "tools/check_docs.py", "MIGRATION.md")
    self.assertEqual(result.returncode, 0, result.stderr)
''',
)


RECIPES: dict[str, dict[str, Any]] = {
    "f05-s-python-helper-refactor-v1": {
        "case_id": "F05-S-PY-001",
        "files": S_FILES,
        "hidden": S_HIDDEN,
        "good": {"events.py": S_GOOD_EVENTS},
        "executable": ["tools/compare_behavior.py"],
        "mutants": {
            "prefix-before-validation": {
                "files": {"events.py": S_BAD_PREFIX_FIRST},
                "expected_failed_check_ids": ["refactor-equivalence-errors"],
            },
            "duplicate-private-helpers": {
                "files": {"events.py": S_BAD_DUPLICATE_HELPERS},
                "expected_failed_check_ids": ["refactor-helper-shared"],
            },
            "public-helper-export": {
                "files": {"events.py": S_BAD_PUBLIC_HELPER},
                "expected_failed_check_ids": ["refactor-api-stable"],
            },
        },
    },
    "f05-m-python-codec-migration-v1": {
        "case_id": "F05-M-PY-001",
        "files": M_FILES,
        "hidden": M_HIDDEN,
        "good": M_GOOD,
        "executable": ["tools/check_callers.py"],
        "mutants": {
            "codec-per-call": {
                "files": _overlay(M_GOOD, M_BAD_PER_CALL_COMPONENTS),
                "expected_failed_check_ids": ["migration-policy-lifecycle"],
            },
            "reflective-caller-missed": {
                "files": _overlay(M_GOOD, {"plugins.py": M_BAD_REFLECTIVE}),
                "expected_failed_check_ids": ["migration-all-callers"],
            },
            "noncanonical-compat-bytes": {
                "files": _overlay(M_GOOD, {"events/compat.py": M_BAD_COMPAT_BYTES}),
                "expected_failed_check_ids": ["migration-compat-bytes"],
            },
            "nested-warning": {
                "files": _overlay(M_GOOD, {"events/codec.py": M_BAD_NESTED_WARNING_CODEC}),
                "expected_failed_check_ids": ["migration-warning-once"],
            },
        },
    },
    "f05-l-backend-schema-migration-v1": {
        "case_id": "F05-L-PYBASH-001",
        "files": L_FILES,
        "hidden": L_HIDDEN,
        "good": L_GOOD,
        "executable": ["bin/jobctl", "tests/migration-lifecycle.sh", "tools/check_docs.py"],
        "mutants": {
            "version-marker-first": {
                "files": _overlay(L_GOOD, {"jobs/migrate.py": L_BAD_EARLY_MARKER}),
                "expected_failed_check_ids": ["migration-atomic-order"],
            },
            "file-path-leak": {
                "files": _overlay(
                    L_GOOD,
                    {"jobs/file_backend.py": L_BAD_LEAK_FILE, "jobs/cli.py": L_BAD_LEAK_CLI},
                ),
                "expected_failed_check_ids": ["migration-backend-boundary"],
            },
            "duplicate-on-resume": {
                "files": _overlay(L_GOOD, {"jobs/migrate.py": L_BAD_DUPLICATE_RESUME}),
                "expected_failed_check_ids": ["migration-resume"],
            },
            "destructive-rollback": {
                "files": _overlay(L_GOOD, {"jobs/migrate.py": L_BAD_DESTRUCTIVE_ROLLBACK}),
                "expected_failed_check_ids": ["migration-rollback"],
            },
            "wrapper-drops-backend": {
                "files": _overlay(L_GOOD, {"bin/jobctl": L_BAD_WRAPPER}),
                "expected_failed_check_ids": ["migration-backend-boundary"],
                "executable": ["bin/jobctl"],
            },
        },
    },
}
