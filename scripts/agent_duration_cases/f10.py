"""Deterministic performance/resource diagnosis fixtures for family F10."""

from __future__ import annotations

import copy
import hashlib
import json
from typing import Any


AGENT_INSTRUCTIONS = """# AGENTS.md

This repository is a disposable duration-study fixture.

- Work only inside this repository and do not use the network.
- Do not inspect parent directories, hidden evaluators, gold artifacts, or credentials.
- Do not commit, push, add remotes, or access real Docker/provider services.
- Modify only the task-named diagnosis/instrumentation artifacts.
- Do not change source, tests, launchers, validators, or contract files.
- Base conclusions on deterministic counters, traces, and fake resource signals.
- Treat local elapsed timings as diagnostic only; never make universal speed claims.
"""


def _json_file(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def _compact_digest(value: Any) -> str:
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def _line_evidence(files: dict[str, str], path: str, symbol: str, snippet: str) -> dict[str, Any]:
    for number, line in enumerate(files[path].splitlines(), start=1):
        if snippet in line:
            return {"path": path, "symbol": symbol, "line": number, "snippet": snippet}
    raise RuntimeError(f"missing evidence anchor: {path}: {snippet}")


S_REPORT = '''from __future__ import annotations

import json
from typing import Any


def canonical_json(value: dict[str, Any], counters: dict[str, int]) -> bytes:
    counters["canonical_json_calls"] += 1
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    counters["canonical_json_bytes"] += len(encoded)
    return encoded


def render_report(value: dict[str, Any], fields: list[str]) -> tuple[dict[str, str], dict[str, int]]:
    counters = {
        "canonical_json_calls": 0,
        "canonical_json_bytes": 0,
        "sort_calls": 0,
        "sort_items": 0,
    }
    counters["sort_calls"] += 1
    counters["sort_items"] += len(fields)
    ordered_fields = sorted(fields)
    output: dict[str, str] = {}
    for field in ordered_fields:
        output[field] = canonical_json(value, counters).decode("utf-8")
    return output, counters
'''


def _s_observation() -> dict[str, Any]:
    encoded = json.dumps(
        {"active": True, "job": "fixture", "values": [1, 2, 3]},
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    runs = []
    for field_count in (8, 64, 512):
        runs.append(
            {
                "field_count": field_count,
                "counters": {
                    "canonical_json_calls": field_count,
                    "canonical_json_bytes": field_count * len(encoded),
                    "sort_calls": 1,
                    "sort_items": field_count,
                },
                "output_fields": field_count,
                "output_value_digest": "sha256:" + hashlib.sha256(encoded).hexdigest(),
                "virtual_work_units": field_count * len(encoded) + field_count,
            }
        )
    return {
        "schema_version": 1,
        "command": "python3 bench.py --json",
        "counter_clock": "deterministic-work-units",
        "elapsed_time_role": "diagnostic-not-portable-gold",
        "runs": runs,
    }


S_OBSERVATION = _s_observation()


S_BENCH = '''from __future__ import annotations

import argparse
import hashlib
import json

from report import render_report


def observation() -> dict[str, object]:
    payload = {"active": True, "job": "fixture", "values": [1, 2, 3]}
    runs: list[dict[str, object]] = []
    for field_count in (8, 64, 512):
        fields = [f"field-{index:04d}" for index in range(field_count)]
        output, counters = render_report(payload, fields)
        first_value = next(iter(output.values())).encode("utf-8")
        runs.append(
            {
                "field_count": field_count,
                "counters": counters,
                "output_fields": len(output),
                "output_value_digest": "sha256:" + hashlib.sha256(first_value).hexdigest(),
                "virtual_work_units": counters["canonical_json_bytes"] + counters["sort_items"],
            }
        )
    return {
        "schema_version": 1,
        "command": "python3 bench.py --json",
        "counter_clock": "deterministic-work-units",
        "elapsed_time_role": "diagnostic-not-portable-gold",
        "runs": runs,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true", required=True)
    parser.parse_args()
    print(json.dumps(observation(), sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
'''


S_TESTS = '''import json
import unittest

from report import render_report


class ReportTests(unittest.TestCase):
    def test_report_values_are_canonical_and_fields_sorted(self):
        output, counters = render_report({"b": 2, "a": 1}, ["z", "a"])
        self.assertEqual(list(output), ["a", "z"])
        self.assertEqual(set(output.values()), {'{"a":1,"b":2}'})
        self.assertEqual(counters["canonical_json_calls"], 2)


if __name__ == "__main__":
    unittest.main()
'''


S_VALIDATOR = r'''#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys


def digest(value: object) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def main(argv: list[str]) -> int:
    if len(argv) != 3:
        return 2
    try:
        report = json.loads(Path(argv[1]).read_text(encoding="utf-8"))
        observed = json.loads(Path(argv[2]).read_text(encoding="utf-8"))
        require(report.get("schema_version") == 1, "report schema_version must be one")
        require(report.get("observation_digest") == digest(observed), "observation digest mismatch")
        require(report.get("command") == observed.get("command"), "command mismatch")
        runs = observed.get("runs")
        require(isinstance(runs, list) and len(runs) >= 3, "at least three runs are required")
        require(isinstance(report.get("diagnosis"), dict), "diagnosis is required")
        require(isinstance(report.get("optimization"), dict), "optimization is required")
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"invalid performance report: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
'''


S_FILES = {
    "AGENTS.md": AGENT_INSTRUCTIONS,
    "report.py": S_REPORT,
    "bench.py": S_BENCH,
    "tests/test_report.py": S_TESTS,
    "tools/validate_performance.py": S_VALIDATOR,
}


S_GOOD_REPORT = {
    "schema_version": 1,
    "command": "python3 bench.py --json",
    "observation_digest": _compact_digest(S_OBSERVATION),
    "observations": S_OBSERVATION["runs"],
    "diagnosis": {
        "primary": {
            "candidate": "repeated-canonical-json",
            "source": _line_evidence(S_FILES, "report.py", "render_report", "output[field] = canonical_json(value, counters)"),
            "relation": "one-call-per-output-field",
            "counter": "canonical_json_calls",
        },
        "candidates": [
            {"candidate": "repeated-canonical-json", "scales_with": "field_count", "observed_calls": [8, 64, 512], "primary": True},
            {"candidate": "field-sort", "scales_with": "one-sort-per-run", "observed_calls": [1, 1, 1], "primary": False},
        ],
    },
    "optimization": {
        "strategy": "cache-canonical-bytes-once-per-input-object",
        "condition": "only-after-output-equivalence-tests-pass",
        "preserves": ["canonical-json-bytes", "field-order", "output-field-count"],
        "portable_speedup_claim": None,
    },
    "claim_scope": {
        "environment": "fixture-local",
        "elapsed_time": "not-used-as-portable-gold",
        "generalization": "none",
    },
}

S_GOOD = {"performance.json": _json_file(S_GOOD_REPORT)}

S_SORT_BLAME = copy.deepcopy(S_GOOD_REPORT)
S_SORT_BLAME["diagnosis"]["primary"] = {
    "candidate": "field-sort",
    "source": _line_evidence(S_FILES, "report.py", "render_report", "ordered_fields = sorted(fields)"),
    "relation": "one-profile-snapshot",
    "counter": "sort_calls",
}
S_SORT_BLAME["diagnosis"]["candidates"][0]["primary"] = False
S_SORT_BLAME["diagnosis"]["candidates"][1]["primary"] = True

S_ELAPSED_ONLY = {
    "schema_version": 1,
    "command": "python3 bench.py --json",
    "observation_digest": _compact_digest(S_OBSERVATION),
    "observations": [{"elapsed_ms": 1.2}],
    "diagnosis": {"primary": {"candidate": "field-sort"}},
    "optimization": {"strategy": "optimize-fastest-line"},
}

S_GLOBAL_SPEEDUP = copy.deepcopy(S_GOOD_REPORT)
S_GLOBAL_SPEEDUP["optimization"]["portable_speedup_claim"] = "always-90-percent-faster"
S_GLOBAL_SPEEDUP["claim_scope"]["generalization"] = "all-machines"

S_REMOVE_CANONICAL = copy.deepcopy(S_GOOD_REPORT)
S_REMOVE_CANONICAL["optimization"]["strategy"] = "remove-canonical-json"
S_REMOVE_CANONICAL["optimization"]["preserves"] = ["field-order"]


S_HIDDEN_TEMPLATE = r'''from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import unittest


WORKSPACE = Path(os.environ["DURATION_FIXTURE_WORKSPACE"])
EXPECTED = __EXPECTED__
ALLOWED = {"performance.json"}


def compact_digest(value: object) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def load_report() -> dict:
    return json.loads((WORKSPACE / "performance.json").read_text(encoding="utf-8"))


def rerun() -> dict:
    completed = subprocess.run(
        [sys.executable, "bench.py", "--json"],
        cwd=WORKSPACE,
        env={
            "PATH": os.environ.get("PATH", "/usr/local/bin:/usr/bin:/bin"),
            "HOME": "/nonexistent",
            "PYTHONDONTWRITEBYTECODE": "1",
            "PYTHONPATH": str(WORKSPACE),
        },
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=10,
        check=False,
    )
    if completed.returncode != 0:
        raise AssertionError(completed.stderr)
    return json.loads(completed.stdout)


def assert_scope(testcase: unittest.TestCase) -> None:
    completed = subprocess.run(
        ["git", "status", "--porcelain", "--untracked-files=all"],
        cwd=WORKSPACE,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    testcase.assertEqual(completed.returncode, 0)
    changed = {line[3:].split(" -> ")[-1] for line in completed.stdout.splitlines() if len(line) >= 4}
    testcase.assertTrue(changed.issubset(ALLOWED), changed)
    for raw_path, expected in EXPECTED.items():
        testcase.assertEqual((WORKSPACE / raw_path).read_bytes(), expected.encode("utf-8"), raw_path)


def evidence_resolves(evidence: dict) -> bool:
    path = WORKSPACE / evidence.get("path", "")
    if not path.is_file():
        return False
    lines = path.read_text(encoding="utf-8").splitlines()
    line = evidence.get("line")
    snippet = evidence.get("snippet")
    symbol = evidence.get("symbol")
    return isinstance(line, int) and 1 <= line <= len(lines) and isinstance(snippet, str) and snippet in lines[line - 1] and isinstance(symbol, str) and symbol in path.read_text(encoding="utf-8")


class HiddenSmallPerformanceTests(unittest.TestCase):
    def setUp(self):
        assert_scope(self)

    def test_repro_command(self):
        report = load_report()
        observed = rerun()
        self.assertEqual(report.get("command"), observed.get("command"))
        self.assertEqual(report.get("observation_digest"), compact_digest(observed))
        self.assertEqual(report.get("observations"), observed.get("runs"))

    def test_scaling_evidence(self):
        runs = rerun()["runs"]
        self.assertEqual([run["field_count"] for run in runs], [8, 64, 512])
        self.assertEqual([run["counters"]["canonical_json_calls"] for run in runs], [8, 64, 512])
        self.assertEqual([run["counters"]["sort_calls"] for run in runs], [1, 1, 1])
        self.assertEqual(load_report().get("observations"), runs)

    def test_root_cause(self):
        report = load_report()
        primary = report.get("diagnosis", {}).get("primary", {})
        self.assertEqual(primary.get("candidate"), "repeated-canonical-json")
        self.assertEqual(primary.get("relation"), "one-call-per-output-field")
        self.assertEqual(primary.get("counter"), "canonical_json_calls")
        self.assertTrue(evidence_resolves(primary.get("source", {})))

    def test_distractor_rejected(self):
        candidates = {item.get("candidate"): item for item in load_report().get("diagnosis", {}).get("candidates", [])}
        self.assertEqual(candidates["repeated-canonical-json"].get("observed_calls"), [8, 64, 512])
        self.assertIs(candidates["repeated-canonical-json"].get("primary"), True)
        self.assertEqual(candidates["field-sort"].get("observed_calls"), [1, 1, 1])
        self.assertIs(candidates["field-sort"].get("primary"), False)

    def test_claim_bounded(self):
        report = load_report()
        optimization = report.get("optimization", {})
        self.assertEqual(optimization.get("strategy"), "cache-canonical-bytes-once-per-input-object")
        self.assertEqual(optimization.get("condition"), "only-after-output-equivalence-tests-pass")
        self.assertTrue({"canonical-json-bytes", "field-order", "output-field-count"}.issubset(set(optimization.get("preserves", []))))
        self.assertIsNone(optimization.get("portable_speedup_claim"))
        self.assertEqual(report.get("claim_scope", {}).get("generalization"), "none")


if __name__ == "__main__":
    unittest.main()
'''

S_HIDDEN = S_HIDDEN_TEMPLATE.replace(
    "__EXPECTED__",
    repr(
        {
            "report.py": S_REPORT,
            "bench.py": S_BENCH,
            "tests/test_report.py": S_TESTS,
            "tools/validate_performance.py": S_VALIDATOR,
        }
    ),
)


M_LEDGER_LINES = (
    '{"kind":"start","value":1}',
    '{"kind":"data","value":2}',
    '{"kind":"data","value":3}',
    '{"kind":"finish","value":4}',
)
M_LEDGER_TEXT = "\n".join(M_LEDGER_LINES) + "\n"


M_READER = '''from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable


def read_lines(path: Path, recorder: Any | None = None) -> Iterable[str]:
    content = path.read_text(encoding="utf-8")
    lines = content.splitlines()
    if recorder is not None:
        recorder.add("open_calls", 1)
        recorder.add("bytes_read", len(content.encode("utf-8")))
        return recorder.observe_lines(iter(lines))
    return iter(lines)
'''

M_DECODE = '''from __future__ import annotations

import json
from typing import Any


def decode_line(raw: str, recorder: Any | None = None) -> dict[str, object]:
    if recorder is not None:
        recorder.add("decode_calls", 1)
    value = json.loads(raw)
    if not isinstance(value, dict):
        raise ValueError("ledger line must be an object")
    return value
'''

M_CACHE = '''from __future__ import annotations

from pathlib import Path
from typing import Any


class SummaryCache:
    def __init__(self) -> None:
        self._values: dict[int, dict[str, object]] = {}

    def _key(self, path: Path) -> int:
        return id(path)

    def get(self, path: Path, recorder: Any | None = None) -> dict[str, object] | None:
        value = self._values.get(self._key(path))
        if recorder is not None:
            recorder.add("cache_hits" if value is not None else "cache_misses", 1)
        return value

    def put(self, path: Path, value: dict[str, object]) -> None:
        self._values[self._key(path)] = value
'''

M_SUMMARIZER = '''from __future__ import annotations

from pathlib import Path
from typing import Any

from .cache import SummaryCache
from .decode import decode_line
from .reader import read_lines


def summarize(path: Path, cache: SummaryCache, recorder: Any | None = None) -> dict[str, object]:
    if recorder is not None:
        recorder.add("query_calls", 1)
    cached = cache.get(path, recorder)
    if cached is not None:
        return cached
    counts: dict[str, int] = {}
    total = 0
    for raw in read_lines(path, recorder):
        decode_line(raw, recorder)
        event = decode_line(raw, recorder)
        kind = str(event["kind"])
        counts[kind] = counts.get(kind, 0) + 1
        total += int(event["value"])
    result: dict[str, object] = {"counts": counts, "total": total}
    cache.put(path, result)
    return result
'''

M_INSTRUMENTATION_SKELETON = '''from __future__ import annotations

from collections.abc import Iterable, Iterator


class Recorder:
    """Instrumentation extension point to complete for the experiment."""

    def add(self, name: str, amount: int) -> None:
        pass

    def observe_lines(self, lines: Iterable[str]) -> Iterator[str]:
        return iter(lines)

    def snapshot(self) -> dict[str, int]:
        return {}
'''

M_INSTRUMENTATION_GOOD = '''from __future__ import annotations

from collections.abc import Iterable, Iterator


class Recorder:
    def __init__(self) -> None:
        self._counts = {
            "query_calls": 0,
            "open_calls": 0,
            "bytes_read": 0,
            "line_observations": 0,
            "decode_calls": 0,
            "cache_hits": 0,
            "cache_misses": 0,
        }

    def add(self, name: str, amount: int) -> None:
        if name not in self._counts or not isinstance(amount, int) or amount < 0:
            raise ValueError("invalid instrumentation counter")
        self._counts[name] += amount

    def observe_lines(self, lines: Iterable[str]) -> Iterator[str]:
        for line in lines:
            self._counts["line_observations"] += 1
            yield line

    def snapshot(self) -> dict[str, int]:
        return dict(self._counts)
'''


M_BENCH = '''from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
from typing import Any

from events.cache import SummaryCache
from events.summarizer import summarize


LEDGER = ''' + repr(M_LEDGER_TEXT) + '''


def load_recorder(path: Path):
    spec = importlib.util.spec_from_file_location("fixture_instrumentation", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load instrumentation")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.Recorder


def result_digest(value: object) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def run_stratum(name: str, ledger: Path, queries: int, reuse_path: bool, recorder_type) -> dict[str, object]:
    recorder = recorder_type()
    cache = SummaryCache()
    if reuse_path:
        shared = Path(str(ledger))
        paths = [shared] * queries
    else:
        paths = [Path(str(ledger)) for _ in range(queries)]
    outputs = [summarize(path, cache, recorder) for path in paths]
    counters = recorder.snapshot()
    return {
        "stratum": name,
        "queries": queries,
        "logical_path_variants": len({str(path) for path in paths}),
        "path_object_count": len({id(path) for path in paths}),
        "counters": counters,
        "phase_work_units": {
            "io": counters.get("bytes_read", 0),
            "decode": counters.get("decode_calls", 0),
            "cache": counters.get("cache_hits", 0) + counters.get("cache_misses", 0),
        },
        "summary_digest": result_digest(outputs[-1]),
        "all_outputs_equivalent": all(item == outputs[0] for item in outputs),
    }


def observation(instrumentation_path: Path) -> dict[str, object]:
    recorder_type = load_recorder(instrumentation_path)
    with tempfile.TemporaryDirectory(prefix="event-bench-") as raw:
        ledger = Path(raw) / "events.jsonl"
        ledger.write_text(LEDGER, encoding="utf-8")
        before = hashlib.sha256(ledger.read_bytes()).hexdigest()
        blocks = []
        for block_id, order in (("cold-then-warm", ("cold", "warm-distinct")), ("warm-then-cold", ("warm-distinct", "cold"))):
            strata = []
            for name in order:
                if name == "cold":
                    strata.append(run_stratum(name, ledger, 1, False, recorder_type))
                else:
                    strata.append(run_stratum(name, ledger, 4, False, recorder_type))
            blocks.append({"block_id": block_id, "order": list(order), "strata": strata})
        identity_control = run_stratum("identity-reuse-control", ledger, 4, True, recorder_type)
        after = hashlib.sha256(ledger.read_bytes()).hexdigest()
    return {
        "schema_version": 1,
        "command": "python3 bench.py --instrument instrumentation.py --output observations.json",
        "environment": "local-deterministic-ledger",
        "line_count": 4,
        "ledger_bytes": len(LEDGER.encode("utf-8")),
        "ledger_digest_before": "sha256:" + before,
        "ledger_digest_after": "sha256:" + after,
        "blocks": blocks,
        "identity_control": identity_control,
        "timing_role": "diagnostic-only-not-gold",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--instrument", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    value = observation(args.instrument)
    args.output.write_text(json.dumps(value, sort_keys=True, separators=(",", ":")) + "\\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
'''


M_TESTS = '''import tempfile
import unittest
from pathlib import Path

from events.cache import SummaryCache
from events.summarizer import summarize


class SummarizerTests(unittest.TestCase):
    def test_summary_is_correct_and_ledger_unchanged(self):
        with tempfile.TemporaryDirectory() as raw:
            ledger = Path(raw) / "events.jsonl"
            content = ''' + repr(M_LEDGER_TEXT) + '''
            ledger.write_text(content, encoding="utf-8")
            result = summarize(ledger, SummaryCache())
            self.assertEqual(result, {"counts": {"start": 1, "data": 2, "finish": 1}, "total": 10})
            self.assertEqual(ledger.read_text(encoding="utf-8"), content)


if __name__ == "__main__":
    unittest.main()
'''


def _m_counts(queries: int, identity_reuse: bool) -> dict[str, int]:
    misses = 1 if identity_reuse else queries
    hits = queries - misses
    return {
        "query_calls": queries,
        "open_calls": misses,
        "bytes_read": misses * len(M_LEDGER_TEXT.encode("utf-8")),
        "line_observations": misses * len(M_LEDGER_LINES),
        "decode_calls": misses * len(M_LEDGER_LINES) * 2,
        "cache_hits": hits,
        "cache_misses": misses,
    }


M_SUMMARY = {"counts": {"start": 1, "data": 2, "finish": 1}, "total": 10}
M_SUMMARY_DIGEST = _compact_digest(M_SUMMARY)


def _m_stratum(name: str, queries: int, identity: bool) -> dict[str, Any]:
    counters = _m_counts(queries, identity)
    return {
        "stratum": name,
        "queries": queries,
        "logical_path_variants": 1,
        "path_object_count": 1 if identity else queries,
        "counters": counters,
        "phase_work_units": {
            "io": counters["bytes_read"],
            "decode": counters["decode_calls"],
            "cache": counters["cache_hits"] + counters["cache_misses"],
        },
        "summary_digest": M_SUMMARY_DIGEST,
        "all_outputs_equivalent": True,
    }


M_EXPECTED_OBSERVATION = {
    "schema_version": 1,
    "command": "python3 bench.py --instrument instrumentation.py --output observations.json",
    "environment": "local-deterministic-ledger",
    "line_count": 4,
    "ledger_bytes": len(M_LEDGER_TEXT.encode("utf-8")),
    "ledger_digest_before": "sha256:" + hashlib.sha256(M_LEDGER_TEXT.encode("utf-8")).hexdigest(),
    "ledger_digest_after": "sha256:" + hashlib.sha256(M_LEDGER_TEXT.encode("utf-8")).hexdigest(),
    "blocks": [
        {"block_id": "cold-then-warm", "order": ["cold", "warm-distinct"], "strata": [_m_stratum("cold", 1, False), _m_stratum("warm-distinct", 4, False)]},
        {"block_id": "warm-then-cold", "order": ["warm-distinct", "cold"], "strata": [_m_stratum("warm-distinct", 4, False), _m_stratum("cold", 1, False)]},
    ],
    "identity_control": _m_stratum("identity-reuse-control", 4, True),
    "timing_role": "diagnostic-only-not-gold",
}


M_VALIDATOR = r'''#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys


def digest(value: object) -> str:
    return "sha256:" + hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def main(argv: list[str]) -> int:
    if len(argv) != 3:
        return 2
    try:
        report = json.loads(Path(argv[1]).read_text(encoding="utf-8"))
        observed = json.loads(Path(argv[2]).read_text(encoding="utf-8"))
        require(report.get("schema_version") == 1, "invalid report schema")
        require(report.get("observation_digest") == digest(observed), "observation mismatch")
        require(report.get("observations") == observed, "raw observations must be embedded")
        require(len(observed.get("blocks", [])) >= 2, "rotated blocks required")
        require(isinstance(report.get("diagnosis"), dict), "diagnosis required")
        require(isinstance(report.get("distribution"), dict), "distribution required")
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"invalid performance report: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
'''


M_FILES = {
    "AGENTS.md": AGENT_INSTRUCTIONS,
    "events/__init__.py": '"""Event summarizer fixture."""\n',
    "events/reader.py": M_READER,
    "events/decode.py": M_DECODE,
    "events/cache.py": M_CACHE,
    "events/summarizer.py": M_SUMMARIZER,
    "bench.py": M_BENCH,
    "instrumentation.py": M_INSTRUMENTATION_SKELETON,
    "tests/test_summarizer.py": M_TESTS,
    "tools/validate_performance.py": M_VALIDATOR,
}


M_GOOD_REPORT = {
    "schema_version": 1,
    "command": M_EXPECTED_OBSERVATION["command"],
    "observation_digest": _compact_digest(M_EXPECTED_OBSERVATION),
    "observations": M_EXPECTED_OBSERVATION,
    "diagnosis": {
        "conditional_primary": {
            "workload": "warm-repeated-distinct-path-objects",
            "candidate": "identity-keyed-cache-miss",
            "source": _line_evidence(M_FILES, "events/cache.py", "SummaryCache._key", "return id(path)"),
            "effect": {"misses": 4, "hits": 0, "avoidable_opens": 3, "avoidable_decodes": 24},
        },
        "cold_secondary": [
            {"candidate": "reopen-per-miss", "counter": "open_calls", "cold_value": 1},
            {"candidate": "duplicate-decode", "counter": "decode_calls", "cold_value": 8, "expected_single_decode": 4},
        ],
        "universal_bottleneck": None,
    },
    "distribution": {
        "run_count": 2,
        "block_ids": ["cold-then-warm", "warm-then-cold"],
        "orders": [["cold", "warm-distinct"], ["warm-distinct", "cold"]],
        "pooled_cold_warm": False,
        "timing_role": "local-diagnostic-only",
    },
    "equivalence": {
        "summary_digest": M_SUMMARY_DIGEST,
        "ledger_unchanged": True,
        "all_outputs_equivalent": True,
    },
    "claim_scope": "fixture-workloads-only",
}

M_GOOD = {
    "instrumentation.py": M_INSTRUMENTATION_GOOD,
    "performance.json": _json_file(M_GOOD_REPORT),
}

M_ONE_WARM = copy.deepcopy(M_GOOD_REPORT)
M_ONE_WARM["distribution"] = {
    "run_count": 1,
    "block_ids": ["warm-only"],
    "orders": [["warm-distinct"]],
    "pooled_cold_warm": True,
    "timing_role": "universal",
}
M_ONE_WARM["diagnosis"]["universal_bottleneck"] = "identity-keyed-cache-miss"

M_TIMING_ONLY_INSTRUMENTATION = '''from __future__ import annotations

class Recorder:
    def __init__(self):
        self.duration_units = 0
    def add(self, name, amount):
        self.duration_units += 1
    def observe_lines(self, lines):
        return iter(lines)
    def snapshot(self):
        return {"duration_units": self.duration_units}
'''

M_DECODE_VICTORY = copy.deepcopy(M_GOOD_REPORT)
M_DECODE_VICTORY["diagnosis"]["conditional_primary"]["candidate"] = "duplicate-decode"
M_DECODE_VICTORY["diagnosis"]["conditional_primary"]["effect"] = {"decodes_removed": 4}
M_DECODE_VICTORY["diagnosis"]["universal_bottleneck"] = "duplicate-decode"

M_CONSUMING_INSTRUMENTATION = '''from __future__ import annotations

class Recorder:
    def __init__(self):
        self._counts = {"query_calls": 0, "open_calls": 0, "bytes_read": 0, "line_observations": 0, "decode_calls": 0, "cache_hits": 0, "cache_misses": 0}
    def add(self, name, amount):
        self._counts[name] += amount
    def observe_lines(self, lines):
        for _ in lines:
            self._counts["line_observations"] += 1
        return lines
    def snapshot(self):
        return dict(self._counts)
'''

M_POOLED = copy.deepcopy(M_GOOD_REPORT)
M_POOLED["distribution"]["pooled_cold_warm"] = True
M_POOLED["distribution"]["orders"] = [["pooled"]]


M_HIDDEN_TEMPLATE = r'''from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


WORKSPACE = Path(os.environ["DURATION_FIXTURE_WORKSPACE"])
EXPECTED = __EXPECTED__
ALLOWED = {"instrumentation.py", "performance.json"}


def digest(value: object) -> str:
    return "sha256:" + hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def load_report() -> dict:
    return json.loads((WORKSPACE / "performance.json").read_text(encoding="utf-8"))


def rerun() -> dict:
    with tempfile.TemporaryDirectory(prefix="f10-m-observed-") as raw:
        output = Path(raw) / "observations.json"
        completed = subprocess.run(
            [sys.executable, "bench.py", "--instrument", "instrumentation.py", "--output", str(output)],
            cwd=WORKSPACE,
            env={"PATH": os.environ.get("PATH", "/usr/local/bin:/usr/bin:/bin"), "HOME": "/nonexistent", "PYTHONDONTWRITEBYTECODE": "1", "PYTHONPATH": str(WORKSPACE)},
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=15,
            check=False,
        )
        if completed.returncode != 0:
            raise AssertionError(completed.stderr)
        return json.loads(output.read_text(encoding="utf-8"))


def assert_scope(testcase: unittest.TestCase) -> None:
    completed = subprocess.run(["git", "status", "--porcelain", "--untracked-files=all"], cwd=WORKSPACE, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    testcase.assertEqual(completed.returncode, 0)
    changed = {line[3:].split(" -> ")[-1] for line in completed.stdout.splitlines() if len(line) >= 4}
    testcase.assertTrue(changed.issubset(ALLOWED), changed)
    for raw_path, expected in EXPECTED.items():
        testcase.assertEqual((WORKSPACE / raw_path).read_bytes(), expected.encode("utf-8"), raw_path)


def strata(observed: dict, name: str) -> list[dict]:
    return [item for block in observed["blocks"] for item in block["strata"] if item["stratum"] == name]


class HiddenMediumPerformanceTests(unittest.TestCase):
    def setUp(self):
        assert_scope(self)

    def test_instrumentation_consistency(self):
        observed = rerun()
        for item in [*strata(observed, "cold"), *strata(observed, "warm-distinct"), observed["identity_control"]]:
            counters = item["counters"]
            self.assertEqual(counters["cache_hits"] + counters["cache_misses"], item["queries"])
            self.assertEqual(counters["open_calls"], counters["cache_misses"])
            self.assertEqual(counters["bytes_read"], counters["open_calls"] * observed["ledger_bytes"])
            self.assertEqual(counters["line_observations"], counters["open_calls"] * observed["line_count"])
            self.assertEqual(counters["decode_calls"], counters["line_observations"] * 2)
            self.assertEqual(item["phase_work_units"], {"io": counters["bytes_read"], "decode": counters["decode_calls"], "cache": item["queries"]})
        self.assertEqual(load_report().get("observation_digest"), digest(observed))

    def test_cold_warm_separation(self):
        observed = rerun()
        self.assertEqual([block["block_id"] for block in observed["blocks"]], ["cold-then-warm", "warm-then-cold"])
        self.assertEqual([block["order"] for block in observed["blocks"]], [["cold", "warm-distinct"], ["warm-distinct", "cold"]])
        distribution = load_report().get("distribution", {})
        self.assertEqual(distribution.get("run_count"), 2)
        self.assertIs(distribution.get("pooled_cold_warm"), False)

    def test_cache_diagnosis(self):
        observed = rerun()
        warm = strata(observed, "warm-distinct")[0]["counters"]
        control = observed["identity_control"]["counters"]
        self.assertEqual((warm["cache_misses"], warm["cache_hits"]), (4, 0))
        self.assertEqual((control["cache_misses"], control["cache_hits"]), (1, 3))
        cause = load_report().get("diagnosis", {}).get("conditional_primary", {})
        self.assertEqual(cause.get("workload"), "warm-repeated-distinct-path-objects")
        self.assertEqual(cause.get("candidate"), "identity-keyed-cache-miss")
        self.assertEqual(cause.get("effect"), {"misses": 4, "hits": 0, "avoidable_opens": 3, "avoidable_decodes": 24})
        self.assertIsNone(load_report().get("diagnosis", {}).get("universal_bottleneck"))

    def test_secondary_costs(self):
        observed = rerun()
        cold = strata(observed, "cold")[0]["counters"]
        self.assertEqual((cold["open_calls"], cold["decode_calls"]), (1, 8))
        candidates = {item["candidate"]: item for item in load_report().get("diagnosis", {}).get("cold_secondary", [])}
        self.assertEqual(candidates["reopen-per-miss"].get("cold_value"), 1)
        self.assertEqual(candidates["duplicate-decode"].get("cold_value"), 8)
        self.assertEqual(candidates["duplicate-decode"].get("expected_single_decode"), 4)

    def test_distribution(self):
        report = load_report()
        observed = rerun()
        self.assertEqual(report.get("observations"), observed)
        self.assertEqual(report.get("distribution", {}).get("block_ids"), ["cold-then-warm", "warm-then-cold"])
        self.assertEqual(report.get("distribution", {}).get("timing_role"), "local-diagnostic-only")

    def test_output_equivalence(self):
        observed = rerun()
        self.assertEqual(observed["ledger_digest_before"], observed["ledger_digest_after"])
        every = [item for block in observed["blocks"] for item in block["strata"]] + [observed["identity_control"]]
        self.assertTrue(all(item["all_outputs_equivalent"] for item in every))
        self.assertEqual({item["summary_digest"] for item in every}, {load_report()["equivalence"]["summary_digest"]})
        self.assertIs(load_report()["equivalence"].get("ledger_unchanged"), True)


if __name__ == "__main__":
    unittest.main()
'''

M_HIDDEN = M_HIDDEN_TEMPLATE.replace(
    "__EXPECTED__",
    repr(
        {
            "events/__init__.py": M_FILES["events/__init__.py"],
            "events/reader.py": M_READER,
            "events/decode.py": M_DECODE,
            "events/cache.py": M_CACHE,
            "events/summarizer.py": M_SUMMARIZER,
            "bench.py": M_BENCH,
            "tests/test_summarizer.py": M_TESTS,
            "tools/validate_performance.py": M_VALIDATOR,
        }
    ),
)


L_STAGES = ("queue", "image_probe", "worker_setup", "provider_wait", "validation", "cleanup")


def _l_simulate(width: int, *, jobs: int = 4, probe_lock: bool = True, timeout_job: int | None = None) -> dict[str, Any]:
    slots = [0] * width
    probe_free = 0
    events: list[dict[str, Any]] = []
    outcomes: dict[str, str] = {}
    for index in range(1, jobs + 1):
        job_id = f"job-{index}"
        slot = min(range(width), key=lambda item: (slots[item], item))
        admitted = slots[slot]
        probe_start = max(admitted, probe_free) if probe_lock else admitted
        probe_end = probe_start + 3
        if probe_lock:
            probe_free = probe_end
        setup_end = probe_end + 1
        provider_end = setup_end + (5 if timeout_job == index else 10)
        validation_end = provider_end + (0 if timeout_job == index else 2)
        cleanup_end = validation_end + 1
        outcome = "timeout" if timeout_job == index else "complete"
        outcomes[job_id] = outcome
        intervals = (
            ("queue", 0, probe_start, "complete"),
            ("image_probe", probe_start, probe_end, "complete"),
            ("worker_setup", probe_end, setup_end, "complete"),
            ("provider_wait", setup_end, provider_end, outcome),
            ("validation", provider_end, validation_end, "skipped" if outcome == "timeout" else "complete"),
            ("cleanup", validation_end, cleanup_end, "complete"),
        )
        for stage, start, end, status in intervals:
            events.append({"job_id": job_id, "stage": stage, "start": start, "end": end, "status": status})
        slots[slot] = cleanup_end
    return {
        "events": events,
        "outcomes": outcomes,
        "resource_signals": {
            "configured_width": width,
            "job_count": jobs,
            "probe_lock_acquisitions": jobs if probe_lock else 0,
            "provider_requests": jobs,
            "real_docker_calls": 0,
            "real_provider_calls": 0,
        },
    }


def _interval_union(intervals: list[tuple[int, int]]) -> int:
    merged: list[list[int]] = []
    for start, end in sorted(intervals):
        if not merged or start > merged[-1][1]:
            merged.append([start, end])
        else:
            merged[-1][1] = max(merged[-1][1], end)
    return sum(end - start for start, end in merged)


def _l_analyze(raw: dict[str, Any]) -> dict[str, Any]:
    events = []
    for item in raw["events"]:
        event = dict(item)
        event["correlation_id"] = f"{item['job_id']}:{item['stage']}"
        events.append(event)
    jobs = sorted(raw["outcomes"])
    worker_intervals = []
    stage_totals = {stage: 0 for stage in L_STAGES}
    queue_durations = []
    for job_id in jobs:
        job_events = [event for event in events if event["job_id"] == job_id]
        for event in job_events:
            stage_totals[event["stage"]] += event["end"] - event["start"]
        queue = next(event for event in job_events if event["stage"] == "queue")
        image = next(event for event in job_events if event["stage"] == "image_probe")
        cleanup = next(event for event in job_events if event["stage"] == "cleanup")
        queue_durations.append(queue["end"] - queue["start"])
        worker_intervals.append((image["start"], cleanup["end"]))
    outcomes = {
        "complete": sum(value == "complete" for value in raw["outcomes"].values()),
        "timeout": sum(value == "timeout" for value in raw["outcomes"].values()),
        "failure": sum(value == "failure" for value in raw["outcomes"].values()),
    }
    return {
        "events": events,
        "metrics": {
            "user_wall": max(event["end"] for event in events),
            "worker_span": max(end for _, end in worker_intervals) - min(start for start, _ in worker_intervals),
            "worker_union": _interval_union(worker_intervals),
            "aggregate_worker": sum(end - start for start, end in worker_intervals),
            "stage_totals": stage_totals,
            "queue_durations": queue_durations,
            "queue_tail": max(queue_durations),
            "outcomes": outcomes,
            "resource_signals": raw["resource_signals"],
        },
    }


def _l_run(run_id: str, width: int, *, probe_lock: bool = True, timeout_job: int | None = None) -> dict[str, Any]:
    analyzed = _l_analyze(_l_simulate(width, probe_lock=probe_lock, timeout_job=timeout_job))
    return {
        "run_id": run_id,
        "config": {"width": width, "jobs": 4, "probe_lock": probe_lock, "timeout_job": timeout_job},
        **analyzed,
    }


L_EXPECTED_DATASET = {
    "schema_version": 1,
    "manifest": {
        "blocks": [
            {"block_id": "ascending", "order": [1, 2, 4], "run_ids": ["ascending-w1", "ascending-w2", "ascending-w4"]},
            {"block_id": "descending", "order": [4, 2, 1], "run_ids": ["descending-w4", "descending-w2", "descending-w1"]},
        ],
        "counterfactual_run_id": "counterfactual-w4-no-lock",
        "censored_run_id": "censored-w2",
        "environment": "deterministic-simulator-no-docker-provider",
    },
    "runs": {},
}
for _run_id, _width in (
    ("ascending-w1", 1),
    ("ascending-w2", 2),
    ("ascending-w4", 4),
    ("descending-w4", 4),
    ("descending-w2", 2),
    ("descending-w1", 1),
):
    L_EXPECTED_DATASET["runs"][_run_id] = _l_run(_run_id, _width)
L_EXPECTED_DATASET["runs"]["counterfactual-w4-no-lock"] = _l_run("counterfactual-w4-no-lock", 4, probe_lock=False)
L_EXPECTED_DATASET["runs"]["censored-w2"] = _l_run("censored-w2", 2, timeout_job=2)


L_LEDGER = '''from __future__ import annotations


STAGES = ("queue", "image_probe", "worker_setup", "provider_wait", "validation", "cleanup")


def event(job_id: str, stage: str, start: int, end: int, status: str) -> dict[str, object]:
    if stage not in STAGES or start < 0 or end < start:
        raise ValueError("invalid simulator event")
    return {"job_id": job_id, "stage": stage, "start": start, "end": end, "status": status}
'''


L_SIMULATOR = '''from __future__ import annotations

from .ledger import event


def simulate(width: int, jobs: int = 4, probe_lock: bool = True, timeout_job: int | None = None) -> dict[str, object]:
    if width < 1 or jobs < 1:
        raise ValueError("width and jobs must be positive")
    slots = [0] * width
    probe_free = 0
    events: list[dict[str, object]] = []
    outcomes: dict[str, str] = {}
    for index in range(1, jobs + 1):
        job_id = f"job-{index}"
        slot = min(range(width), key=lambda item: (slots[item], item))
        admitted = slots[slot]
        probe_start = max(admitted, probe_free) if probe_lock else admitted
        probe_end = probe_start + 3
        if probe_lock:
            probe_free = probe_end
        setup_end = probe_end + 1
        provider_end = setup_end + (5 if timeout_job == index else 10)
        validation_end = provider_end + (0 if timeout_job == index else 2)
        cleanup_end = validation_end + 1
        outcome = "timeout" if timeout_job == index else "complete"
        outcomes[job_id] = outcome
        for values in (
            ("queue", 0, probe_start, "complete"),
            ("image_probe", probe_start, probe_end, "complete"),
            ("worker_setup", probe_end, setup_end, "complete"),
            ("provider_wait", setup_end, provider_end, outcome),
            ("validation", provider_end, validation_end, "skipped" if outcome == "timeout" else "complete"),
            ("cleanup", validation_end, cleanup_end, "complete"),
        ):
            events.append(event(job_id, *values))
        slots[slot] = cleanup_end
    return {
        "events": events,
        "outcomes": outcomes,
        "resource_signals": {
            "configured_width": width,
            "job_count": jobs,
            "probe_lock_acquisitions": jobs if probe_lock else 0,
            "provider_requests": jobs,
            "real_docker_calls": 0,
            "real_provider_calls": 0,
        },
    }
'''


L_INSTRUMENTATION_SKELETON = '''from __future__ import annotations


def analyze(raw: dict[str, object]) -> dict[str, object]:
    """Complete correlated event and resource accounting for the experiment."""
    return {"events": raw["events"], "metrics": {}}
'''


L_INSTRUMENTATION_GOOD = '''from __future__ import annotations


STAGES = ("queue", "image_probe", "worker_setup", "provider_wait", "validation", "cleanup")


def interval_union(intervals: list[tuple[int, int]]) -> int:
    merged: list[list[int]] = []
    for start, end in sorted(intervals):
        if not merged or start > merged[-1][1]:
            merged.append([start, end])
        else:
            merged[-1][1] = max(merged[-1][1], end)
    return sum(end - start for start, end in merged)


def analyze(raw: dict[str, object]) -> dict[str, object]:
    events = []
    for item in raw["events"]:
        enriched = dict(item)
        enriched["correlation_id"] = f"{item['job_id']}:{item['stage']}"
        events.append(enriched)
    outcomes_by_job = raw["outcomes"]
    jobs = sorted(outcomes_by_job)
    stage_totals = {stage: 0 for stage in STAGES}
    queue_durations: list[int] = []
    worker_intervals: list[tuple[int, int]] = []
    for job_id in jobs:
        job_events = [event for event in events if event["job_id"] == job_id]
        for event in job_events:
            stage_totals[event["stage"]] += event["end"] - event["start"]
        queue = next(event for event in job_events if event["stage"] == "queue")
        image = next(event for event in job_events if event["stage"] == "image_probe")
        cleanup = next(event for event in job_events if event["stage"] == "cleanup")
        queue_durations.append(queue["end"] - queue["start"])
        worker_intervals.append((image["start"], cleanup["end"]))
    outcomes = {
        "complete": sum(value == "complete" for value in outcomes_by_job.values()),
        "timeout": sum(value == "timeout" for value in outcomes_by_job.values()),
        "failure": sum(value == "failure" for value in outcomes_by_job.values()),
    }
    return {
        "events": events,
        "metrics": {
            "user_wall": max(event["end"] for event in events),
            "worker_span": max(end for _, end in worker_intervals) - min(start for start, _ in worker_intervals),
            "worker_union": interval_union(worker_intervals),
            "aggregate_worker": sum(end - start for start, end in worker_intervals),
            "stage_totals": stage_totals,
            "queue_durations": queue_durations,
            "queue_tail": max(queue_durations),
            "outcomes": outcomes,
            "resource_signals": raw["resource_signals"],
        },
    }
'''


L_RUNNER = '''from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path

from .simulator import simulate


def load_analyzer(path: Path):
    spec = importlib.util.spec_from_file_location("fixture_stage_instrumentation", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load instrumentation")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.analyze


def run_record(run_id: str, width: int, analyze, probe_lock: bool = True, timeout_job: int | None = None) -> dict[str, object]:
    return {
        "run_id": run_id,
        "config": {"width": width, "jobs": 4, "probe_lock": probe_lock, "timeout_job": timeout_job},
        **analyze(simulate(width, jobs=4, probe_lock=probe_lock, timeout_job=timeout_job)),
    }


def dataset(instrumentation: Path) -> dict[str, object]:
    analyze = load_analyzer(instrumentation)
    runs = {}
    for run_id, width in (
        ("ascending-w1", 1), ("ascending-w2", 2), ("ascending-w4", 4),
        ("descending-w4", 4), ("descending-w2", 2), ("descending-w1", 1),
    ):
        runs[run_id] = run_record(run_id, width, analyze)
    runs["counterfactual-w4-no-lock"] = run_record("counterfactual-w4-no-lock", 4, analyze, probe_lock=False)
    runs["censored-w2"] = run_record("censored-w2", 2, analyze, timeout_job=2)
    return {
        "schema_version": 1,
        "manifest": {
            "blocks": [
                {"block_id": "ascending", "order": [1, 2, 4], "run_ids": ["ascending-w1", "ascending-w2", "ascending-w4"]},
                {"block_id": "descending", "order": [4, 2, 1], "run_ids": ["descending-w4", "descending-w2", "descending-w1"]},
            ],
            "counterfactual_run_id": "counterfactual-w4-no-lock",
            "censored_run_id": "censored-w2",
            "environment": "deterministic-simulator-no-docker-provider",
        },
        "runs": runs,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--matrix", choices=("visible",), required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--instrument", type=Path, default=Path("instrumentation.py"))
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    value = dataset(args.instrument)
    (args.output / "dataset.json").write_text(json.dumps(value, sort_keys=True, separators=(",", ":")) + "\\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
'''


L_BATCH = '''#!/usr/bin/env bash
set -euo pipefail
exec python3 -m fabric.runner "$@"
'''


L_TESTS = '''import unittest

from fabric.simulator import simulate


class SimulatorTests(unittest.TestCase):
    def test_all_jobs_have_ordered_stages_and_no_real_resources(self):
        result = simulate(2, jobs=4)
        self.assertEqual(set(result["outcomes"].values()), {"complete"})
        self.assertEqual(result["resource_signals"]["real_docker_calls"], 0)
        self.assertEqual(result["resource_signals"]["real_provider_calls"], 0)
        for event in result["events"]:
            self.assertLessEqual(event["start"], event["end"])


if __name__ == "__main__":
    unittest.main()
'''


L_VALIDATOR = r'''#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys


def digest(value: object) -> str:
    return "sha256:" + hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def main(argv: list[str]) -> int:
    if len(argv) != 3:
        return 2
    try:
        report = json.loads(Path(argv[1]).read_text(encoding="utf-8"))
        dataset = json.loads((Path(argv[2]) / "dataset.json").read_text(encoding="utf-8"))
        require(report.get("schema_version") == 1, "invalid report schema")
        require(report.get("observation_digest") == digest(dataset), "dataset mismatch")
        require(report.get("observations") == dataset, "raw dataset must be embedded")
        require(isinstance(report.get("bottleneck_model"), dict), "bottleneck model required")
        require(isinstance(report.get("accounting"), dict), "accounting contract required")
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"invalid performance report: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
'''


L_FILES = {
    "AGENTS.md": AGENT_INSTRUCTIONS,
    "fabric/__init__.py": '"""Deterministic job-fabric simulator."""\n',
    "fabric/ledger.py": L_LEDGER,
    "fabric/simulator.py": L_SIMULATOR,
    "fabric/runner.py": L_RUNNER,
    "bin/run-batch": L_BATCH,
    "instrumentation.py": L_INSTRUMENTATION_SKELETON,
    "tests/test_simulator.py": L_TESTS,
    "tools/validate_performance.py": L_VALIDATOR,
}


_locked_w4 = L_EXPECTED_DATASET["runs"]["ascending-w4"]["metrics"]
_unlocked_w4 = L_EXPECTED_DATASET["runs"]["counterfactual-w4-no-lock"]["metrics"]
L_GOOD_REPORT = {
    "schema_version": 1,
    "command": "bash bin/run-batch --matrix visible --output observations",
    "observation_digest": _compact_digest(L_EXPECTED_DATASET),
    "observations": L_EXPECTED_DATASET,
    "accounting": {
        "user_wall": "max-event-end-from-batch-zero",
        "worker_span": "last-worker-end-minus-first-worker-start",
        "worker_union": "union-of-worker-active-intervals",
        "aggregate_worker": "sum-of-worker-active-intervals",
        "critical_path_claim": "not-reconstructed",
        "parallel_metrics_interchangeable": False,
    },
    "bottleneck_model": {
        "width_tail_cause": {
            "candidate": "global-image-probe-lock",
            "condition": "multiple-workers-admitted-together",
            "locked_width4_queue_tail": _locked_w4["queue_tail"],
            "unlocked_width4_queue_tail": _unlocked_w4["queue_tail"],
            "locked_user_wall": _locked_w4["user_wall"],
            "unlocked_user_wall": _unlocked_w4["user_wall"],
        },
        "per_job_active_dominant": {
            "stage": "provider_wait",
            "duration_per_complete_job": 10,
            "not_width_tail_cause": True,
        },
    },
    "distribution": {
        "blocks": ["ascending", "descending"],
        "widths": [1, 2, 4],
        "pooled": False,
        "queue_tail_by_run": {run_id: run["metrics"]["queue_tail"] for run_id, run in L_EXPECTED_DATASET["runs"].items()},
    },
    "censoring": {
        "censored_run_id": "censored-w2",
        "outcomes": L_EXPECTED_DATASET["runs"]["censored-w2"]["metrics"]["outcomes"],
        "resource_inventory_complete": True,
        "hidden_failures": False,
    },
    "claim_scope": {
        "environment": "deterministic-simulator",
        "real_docker_latency": False,
        "real_provider_latency": False,
        "production_generalization": "none",
    },
}

L_GOOD = {
    "instrumentation.py": L_INSTRUMENTATION_GOOD,
    "performance.json": _json_file(L_GOOD_REPORT),
}

L_SUM_AS_WALL = copy.deepcopy(L_GOOD_REPORT)
L_SUM_AS_WALL["accounting"]["user_wall"] = "sum-of-all-stage-durations"
L_SUM_AS_WALL["accounting"]["critical_path_claim"] = "aggregate-worker-is-critical-path"
L_SUM_AS_WALL["accounting"]["parallel_metrics_interchangeable"] = True

L_WIDTH1_PROVIDER = copy.deepcopy(L_GOOD_REPORT)
L_WIDTH1_PROVIDER["distribution"]["widths"] = [1]
L_WIDTH1_PROVIDER["distribution"]["pooled"] = True
L_WIDTH1_PROVIDER["bottleneck_model"]["width_tail_cause"]["candidate"] = "provider_wait"
L_WIDTH1_PROVIDER["bottleneck_model"]["per_job_active_dominant"]["not_width_tail_cause"] = False

L_HIDE_TIMEOUT = copy.deepcopy(L_GOOD_REPORT)
L_HIDE_TIMEOUT["censoring"]["outcomes"] = {"complete": 4, "timeout": 0, "failure": 0}
L_HIDE_TIMEOUT["censoring"]["hidden_failures"] = True
L_HIDE_TIMEOUT["censoring"]["resource_inventory_complete"] = False

L_AGGREGATE_PROOF = copy.deepcopy(L_GOOD_REPORT)
L_AGGREGATE_PROOF["accounting"]["user_wall"] = "aggregate-worker"
L_AGGREGATE_PROOF["accounting"]["critical_path_claim"] = "aggregate-proves-user-wait"

L_REAL_WORLD_CLAIM = copy.deepcopy(L_GOOD_REPORT)
L_REAL_WORLD_CLAIM["claim_scope"] = {
    "environment": "real-production",
    "real_docker_latency": True,
    "real_provider_latency": True,
    "production_generalization": "universal",
}

L_TIMING_ONLY_INSTRUMENTATION = '''from __future__ import annotations

def analyze(raw):
    return {"events": raw["events"], "metrics": {"elapsed_ms": 1.0}}
'''


L_HIDDEN_TEMPLATE = r'''from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest


WORKSPACE = Path(os.environ["DURATION_FIXTURE_WORKSPACE"])
EXPECTED = __EXPECTED__
ALLOWED = {"instrumentation.py", "performance.json"}
STAGES = ("queue", "image_probe", "worker_setup", "provider_wait", "validation", "cleanup")


def digest(value: object) -> str:
    return "sha256:" + hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def load_report() -> dict:
    return json.loads((WORKSPACE / "performance.json").read_text(encoding="utf-8"))


def rerun() -> dict:
    with tempfile.TemporaryDirectory(prefix="f10-l-observed-") as raw:
        output = Path(raw) / "observations"
        completed = subprocess.run(
            ["bash", "bin/run-batch", "--matrix", "visible", "--output", str(output)],
            cwd=WORKSPACE,
            env={"PATH": os.environ.get("PATH", "/usr/local/bin:/usr/bin:/bin"), "HOME": "/nonexistent", "PYTHONDONTWRITEBYTECODE": "1", "PYTHONPATH": str(WORKSPACE)},
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=15,
            check=False,
        )
        if completed.returncode != 0:
            raise AssertionError(completed.stderr)
        return json.loads((output / "dataset.json").read_text(encoding="utf-8"))


def assert_scope(testcase: unittest.TestCase) -> None:
    completed = subprocess.run(["git", "status", "--porcelain", "--untracked-files=all"], cwd=WORKSPACE, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    testcase.assertEqual(completed.returncode, 0)
    changed = {line[3:].split(" -> ")[-1] for line in completed.stdout.splitlines() if len(line) >= 4}
    testcase.assertTrue(changed.issubset(ALLOWED), changed)
    for raw_path, expected in EXPECTED.items():
        testcase.assertEqual((WORKSPACE / raw_path).read_bytes(), expected.encode("utf-8"), raw_path)


def recompute(run: dict) -> dict:
    events = run["events"]
    jobs = sorted({event["job_id"] for event in events})
    intervals = []
    totals = {stage: 0 for stage in STAGES}
    queues = []
    for job in jobs:
        items = [event for event in events if event["job_id"] == job]
        image = next(event for event in items if event["stage"] == "image_probe")
        cleanup = next(event for event in items if event["stage"] == "cleanup")
        queue = next(event for event in items if event["stage"] == "queue")
        intervals.append((image["start"], cleanup["end"]))
        queues.append(queue["end"] - queue["start"])
        for event in items:
            totals[event["stage"]] += event["end"] - event["start"]
    merged = []
    for start, end in sorted(intervals):
        if not merged or start > merged[-1][1]:
            merged.append([start, end])
        else:
            merged[-1][1] = max(merged[-1][1], end)
    return {
        "user_wall": max(event["end"] for event in events),
        "worker_span": max(end for _, end in intervals) - min(start for start, _ in intervals),
        "worker_union": sum(end - start for start, end in merged),
        "aggregate_worker": sum(end - start for start, end in intervals),
        "stage_totals": totals,
        "queue_durations": queues,
        "queue_tail": max(queues),
    }


class HiddenLargePerformanceTests(unittest.TestCase):
    def setUp(self):
        assert_scope(self)

    def test_stage_correlation(self):
        dataset = rerun()
        for run in dataset["runs"].values():
            jobs = sorted({event["job_id"] for event in run["events"]})
            for job in jobs:
                events = [event for event in run["events"] if event["job_id"] == job]
                self.assertEqual([event["stage"] for event in events], list(STAGES))
                self.assertEqual([event["correlation_id"] for event in events], [f"{job}:{stage}" for stage in STAGES])
                self.assertTrue(all(left["end"] <= right["start"] for left, right in zip(events, events[1:])))

    def test_time_accounting(self):
        dataset = rerun()
        for run in dataset["runs"].values():
            calculated = recompute(run)
            for key, value in calculated.items():
                self.assertEqual(run["metrics"][key], value)
        accounting = load_report().get("accounting", {})
        self.assertEqual(accounting.get("user_wall"), "max-event-end-from-batch-zero")
        self.assertEqual(accounting.get("worker_union"), "union-of-worker-active-intervals")
        self.assertEqual(accounting.get("aggregate_worker"), "sum-of-worker-active-intervals")
        self.assertEqual(accounting.get("critical_path_claim"), "not-reconstructed")
        self.assertIs(accounting.get("parallel_metrics_interchangeable"), False)

    def test_width_curve(self):
        dataset = rerun()
        blocks = dataset["manifest"]["blocks"]
        self.assertEqual([block["order"] for block in blocks], [[1, 2, 4], [4, 2, 1]])
        report = load_report().get("distribution", {})
        self.assertEqual(report.get("widths"), [1, 2, 4])
        self.assertEqual(report.get("blocks"), ["ascending", "descending"])
        self.assertIs(report.get("pooled"), False)
        self.assertEqual(load_report().get("observation_digest"), digest(dataset))

    def test_probe_lock_cause(self):
        dataset = rerun()
        locked = dataset["runs"]["ascending-w4"]["metrics"]
        unlocked = dataset["runs"][dataset["manifest"]["counterfactual_run_id"]]["metrics"]
        self.assertGreater(locked["queue_tail"], unlocked["queue_tail"])
        self.assertGreater(locked["user_wall"], unlocked["user_wall"])
        cause = load_report().get("bottleneck_model", {}).get("width_tail_cause", {})
        self.assertEqual(cause.get("candidate"), "global-image-probe-lock")
        self.assertEqual(cause.get("locked_width4_queue_tail"), locked["queue_tail"])
        self.assertEqual(cause.get("unlocked_width4_queue_tail"), unlocked["queue_tail"])

    def test_provider_distinction(self):
        dataset = rerun()
        locked_run = dataset["runs"]["ascending-w4"]
        locked = locked_run["metrics"]
        self.assertEqual(locked["stage_totals"]["provider_wait"], 40)
        for job_id in sorted({event["job_id"] for event in locked_run["events"]}):
            job_events = [
                event for event in locked_run["events"] if event["job_id"] == job_id
            ]
            self.assertTrue(all(event["status"] == "complete" for event in job_events))
            durations = {
                event["stage"]: event["end"] - event["start"]
                for event in job_events
                if event["stage"] != "queue"
            }
            provider_duration = durations.pop("provider_wait")
            self.assertGreater(provider_duration, max(durations.values()))
        model = load_report().get("bottleneck_model", {}).get("per_job_active_dominant", {})
        self.assertEqual(model.get("stage"), "provider_wait")
        self.assertEqual(model.get("duration_per_complete_job"), 10)
        self.assertIs(model.get("not_width_tail_cause"), True)

    def test_censoring_resource(self):
        dataset = rerun()
        run = dataset["runs"][dataset["manifest"]["censored_run_id"]]
        self.assertEqual(run["metrics"]["outcomes"], {"complete": 3, "timeout": 1, "failure": 0})
        signals = run["metrics"]["resource_signals"]
        self.assertEqual((signals["real_docker_calls"], signals["real_provider_calls"]), (0, 0))
        censoring = load_report().get("censoring", {})
        self.assertEqual(censoring.get("outcomes"), run["metrics"]["outcomes"])
        self.assertIs(censoring.get("resource_inventory_complete"), True)
        self.assertIs(censoring.get("hidden_failures"), False)

    def test_claim_bounded(self):
        scope = load_report().get("claim_scope", {})
        self.assertEqual(scope.get("environment"), "deterministic-simulator")
        self.assertIs(scope.get("real_docker_latency"), False)
        self.assertIs(scope.get("real_provider_latency"), False)
        self.assertEqual(scope.get("production_generalization"), "none")


if __name__ == "__main__":
    unittest.main()
'''

L_HIDDEN = L_HIDDEN_TEMPLATE.replace(
    "__EXPECTED__",
    repr(
        {
            "fabric/__init__.py": L_FILES["fabric/__init__.py"],
            "fabric/ledger.py": L_LEDGER,
            "fabric/simulator.py": L_SIMULATOR,
            "fabric/runner.py": L_RUNNER,
            "bin/run-batch": L_BATCH,
            "tests/test_simulator.py": L_TESTS,
            "tools/validate_performance.py": L_VALIDATOR,
        }
    ),
)


RECIPES: dict[str, dict[str, Any]] = {
    "f10-s-python-canonical-json-perf-v1": {
        "case_id": "F10-S-PY-001",
        "files": S_FILES,
        "hidden": S_HIDDEN,
        "good": S_GOOD,
        "executable": [],
        "mutants": {
            "sort-from-one-snapshot": {
                "files": {"performance.json": _json_file(S_SORT_BLAME)},
                "expected_failed_check_ids": ["perf-root-cause", "perf-distractor-rejected"],
            },
            "elapsed-only": {
                "files": {"performance.json": _json_file(S_ELAPSED_ONLY)},
                "expected_failed_check_ids": ["perf-scaling-evidence"],
            },
            "global-speedup": {
                "files": {"performance.json": _json_file(S_GLOBAL_SPEEDUP)},
                "expected_failed_check_ids": ["perf-claim-bounded"],
            },
            "remove-canonical-output": {
                "files": {"performance.json": _json_file(S_REMOVE_CANONICAL)},
                "expected_failed_check_ids": ["perf-claim-bounded"],
            },
            "production-edit": {
                "files": {"performance.json": _json_file(S_GOOD_REPORT), "report.py": S_REPORT + "\n# forbidden edit\n"},
                "expected_failed_check_ids": ["perf-repro-command"],
            },
            "validator-edit": {
                "files": {"performance.json": _json_file(S_GOOD_REPORT), "tools/validate_performance.py": "raise SystemExit(0)\n"},
                "expected_failed_check_ids": ["perf-repro-command"],
            },
            "outside-contract": {
                "files": {"performance.json": _json_file(S_GOOD_REPORT), "notes.txt": "extra artifact\n"},
                "expected_failed_check_ids": ["perf-repro-command"],
            },
        },
    },
    "f10-m-event-cache-performance-v1": {
        "case_id": "F10-M-PY-001",
        "files": M_FILES,
        "hidden": M_HIDDEN,
        "good": M_GOOD,
        "executable": [],
        "mutants": {
            "one-warm-universal": {
                "files": {"instrumentation.py": M_INSTRUMENTATION_GOOD, "performance.json": _json_file(M_ONE_WARM)},
                "expected_failed_check_ids": ["perf-cold-warm-separation", "perf-distribution"],
            },
            "timing-only": {
                "files": {"instrumentation.py": M_TIMING_ONLY_INSTRUMENTATION, "performance.json": _json_file(M_GOOD_REPORT)},
                "expected_failed_check_ids": ["perf-instrumentation-consistency"],
            },
            "decode-victory": {
                "files": {"instrumentation.py": M_INSTRUMENTATION_GOOD, "performance.json": _json_file(M_DECODE_VICTORY)},
                "expected_failed_check_ids": ["perf-cache-diagnosis"],
            },
            "consuming-instrumentation": {
                "files": {"instrumentation.py": M_CONSUMING_INSTRUMENTATION, "performance.json": _json_file(M_GOOD_REPORT)},
                "expected_failed_check_ids": ["perf-output-equivalence"],
            },
            "pooled-cold-warm": {
                "files": {"instrumentation.py": M_INSTRUMENTATION_GOOD, "performance.json": _json_file(M_POOLED)},
                "expected_failed_check_ids": ["perf-cold-warm-separation"],
            },
            "source-edit": {
                "files": {**M_GOOD, "events/cache.py": M_CACHE + "\n# forbidden edit\n"},
                "expected_failed_check_ids": ["perf-instrumentation-consistency"],
            },
            "validator-edit": {
                "files": {**M_GOOD, "tools/validate_performance.py": "raise SystemExit(0)\n"},
                "expected_failed_check_ids": ["perf-instrumentation-consistency"],
            },
            "outside-contract": {
                "files": {**M_GOOD, "analysis.tmp": "unexpected\n"},
                "expected_failed_check_ids": ["perf-instrumentation-consistency"],
            },
        },
    },
    "f10-l-job-fabric-performance-v1": {
        "case_id": "F10-L-PYBASH-001",
        "files": L_FILES,
        "hidden": L_HIDDEN,
        "good": L_GOOD,
        "executable": ["bin/run-batch"],
        "mutants": {
            "sum-as-wall": {
                "files": {"instrumentation.py": L_INSTRUMENTATION_GOOD, "performance.json": _json_file(L_SUM_AS_WALL)},
                "expected_failed_check_ids": ["perf-time-accounting"],
            },
            "width-one-provider-blame": {
                "files": {"instrumentation.py": L_INSTRUMENTATION_GOOD, "performance.json": _json_file(L_WIDTH1_PROVIDER)},
                "expected_failed_check_ids": ["perf-width-curve", "perf-probe-lock-cause", "perf-provider-distinction"],
            },
            "hide-timeout": {
                "files": {"instrumentation.py": L_INSTRUMENTATION_GOOD, "performance.json": _json_file(L_HIDE_TIMEOUT)},
                "expected_failed_check_ids": ["perf-censoring-resource"],
            },
            "aggregate-proves-wait": {
                "files": {"instrumentation.py": L_INSTRUMENTATION_GOOD, "performance.json": _json_file(L_AGGREGATE_PROOF)},
                "expected_failed_check_ids": ["perf-time-accounting"],
            },
            "real-world-generalization": {
                "files": {"instrumentation.py": L_INSTRUMENTATION_GOOD, "performance.json": _json_file(L_REAL_WORLD_CLAIM)},
                "expected_failed_check_ids": ["perf-claim-bounded"],
            },
            "timing-only": {
                "files": {"instrumentation.py": L_TIMING_ONLY_INSTRUMENTATION, "performance.json": _json_file(L_GOOD_REPORT)},
                "expected_failed_check_ids": ["perf-stage-correlation"],
            },
            "source-edit": {
                "files": {**L_GOOD, "fabric/simulator.py": L_SIMULATOR + "\n# forbidden edit\n"},
                "expected_failed_check_ids": ["perf-stage-correlation"],
            },
            "test-edit": {
                "files": {**L_GOOD, "tests/test_simulator.py": "import unittest\n"},
                "expected_failed_check_ids": ["perf-stage-correlation"],
            },
            "validator-edit": {
                "files": {**L_GOOD, "tools/validate_performance.py": "raise SystemExit(0)\n"},
                "expected_failed_check_ids": ["perf-stage-correlation"],
            },
            "outside-contract": {
                "files": {**L_GOOD, "observations/manual.json": "{}\n"},
                "expected_failed_check_ids": ["perf-stage-correlation"],
            },
        },
    },
}


__all__ = ["RECIPES"]
