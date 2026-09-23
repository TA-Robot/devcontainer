"""Calibrated architecture-design fixtures for S, M, and L profiles."""

from __future__ import annotations

import hashlib
import json
from textwrap import dedent, indent
from typing import Any


AGENT_INSTRUCTIONS = """# AGENTS.md

This repository is a disposable duration-study fixture.

- Work only inside this repository and do not inspect parent directories.
- Do not search for hidden evaluators, gold artifacts, or other cases.
- Do not use the network, credentials, remotes, commits, or pushes.
- Source evidence IDs and vocabulary only from the visible fixture and task capsule.
- Create only the requested Markdown and JSON architecture artifacts.
- Do not modify source evidence, scenarios, tests, or validation tools.
- Run every validation command listed in the task capsule.
"""


def _json_file(value: Any) -> str:
    return json.dumps(value, indent=2, sort_keys=True) + "\n"


def _artifact_validator(required_keys: list[str]) -> str:
    return f'''#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
import re
import sys


REQUIRED_KEYS = {required_keys!r}
MARKER = re.compile(r"<!-- architecture-marker:([^>]+) -->")


def fail(message: str) -> int:
    print(f"invalid architecture artifact: {{message}}", file=sys.stderr)
    return 1


def main() -> int:
    if len(sys.argv) != 3:
        return fail("expected STRUCTURED.json DOCUMENT.md")
    structured_path = Path(sys.argv[1])
    document_path = Path(sys.argv[2])
    if not structured_path.is_file() or not document_path.is_file():
        return fail("both requested artifacts must exist")
    try:
        structured = json.loads(structured_path.read_text(encoding="utf-8"))
        document = document_path.read_text(encoding="utf-8")
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        return fail(f"artifacts are not valid UTF-8/JSON: {{exc}}")
    if not isinstance(structured, dict) or structured.get("schema_version") != 1:
        return fail("schema_version must be 1")
    for key in REQUIRED_KEYS:
        if key not in structured:
            return fail(f"missing required field: {{key}}")
    markers = structured.get("document_markers")
    if not isinstance(markers, list) or not markers or not all(
        isinstance(item, str) and item for item in markers
    ):
        return fail("document_markers must be a non-empty string array")
    if len(markers) != len(set(markers)):
        return fail("document_markers must be unique")
    observed = MARKER.findall(document)
    if len(observed) != len(set(observed)) or set(observed) != set(markers):
        return fail("Markdown and JSON marker sets differ")
    if len(document.strip()) < 200:
        return fail("Markdown decision record is incomplete")
    print("architecture artifacts are structurally valid and synchronized")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
'''


def _hidden_source(
    class_name: str,
    files: dict[str, str],
    artifact_paths: set[str],
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
import re
import subprocess
import sys
import unittest


WORKSPACE = Path(os.environ["DURATION_FIXTURE_WORKSPACE"])
PROTECTED_DIGESTS = {protected!r}
ARTIFACT_PATHS = {sorted(artifact_paths)!r}
MARKER = re.compile(r"<!-- architecture-marker:([^>]+) -->")


def load_json_artifact(testcase, raw_path):
    path = WORKSPACE / raw_path
    testcase.assertTrue(path.is_file(), f"missing artifact: {{raw_path}}")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        testcase.fail(f"invalid JSON artifact {{raw_path}}: {{exc}}")
    testcase.assertIsInstance(value, dict)
    testcase.assertEqual(value.get("schema_version"), 1)
    return value


def assert_fixture_integrity(testcase):
    for raw_path, expected in PROTECTED_DIGESTS.items():
        path = WORKSPACE / raw_path
        testcase.assertTrue(path.is_file(), f"fixture evidence removed: {{raw_path}}")
        testcase.assertEqual(
            hashlib.sha256(path.read_bytes()).hexdigest(),
            expected,
            f"fixture evidence modified: {{raw_path}}",
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
    testcase.assertEqual(
        {{line[3:] for line in completed.stdout.splitlines()}},
        set(ARTIFACT_PATHS),
        "only the requested architecture artifacts may change",
    )
    testcase.assertTrue(all(line.startswith("?? ") for line in completed.stdout.splitlines()))


def run_command(arguments):
    environment = dict(os.environ)
    environment["PYTHONPATH"] = str(WORKSPACE)
    return subprocess.run(
        arguments,
        cwd=WORKSPACE,
        env=environment,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def assert_source_reference(testcase, reference, allowed_paths):
    testcase.assertIsInstance(reference, dict)
    raw_path = reference.get("path")
    anchor = reference.get("anchor")
    testcase.assertIn(raw_path, allowed_paths)
    testcase.assertIsInstance(anchor, str)
    testcase.assertTrue(anchor)
    testcase.assertIn(anchor, (WORKSPACE / raw_path).read_text(encoding="utf-8"))


class {class_name}(unittest.TestCase):
'''
    footer = '''

if __name__ == "__main__":
    unittest.main()
'''
    return header + indent(dedent(class_body).strip(), "    ") + "\n" + footer


def _replace_json(value: dict[str, Any], **changes: Any) -> dict[str, Any]:
    return {**value, **changes}


# ---------------------------------------------------------------------------
# S: local configuration API decision

S_CONSTRAINTS = {
    "constraints": [
        {
            "id": "CFG-request-isolation",
            "requirement": "Each request starts without state retained by a prior request.",
            "required_semantic": "fresh-state-per-call",
            "evidence_anchor": "run_builder_leak",
        },
        {
            "id": "CFG-explicit-deletion",
            "requirement": "An override can remove a key while JSON null remains a valid value.",
            "required_semantic": "explicit-delete-sentinel",
            "evidence_anchor": "run_raw_merge_deletion",
        },
        {
            "id": "CFG-deterministic-result",
            "requirement": "The same base and override produce the same result without ambient state.",
            "required_semantic": "same-input-same-output",
            "evidence_anchor": "raw_merge",
        },
        {
            "id": "CFG-no-third-party-dependencies",
            "requirement": "The local API adds no third-party dependency.",
            "required_semantic": "stdlib-only",
            "evidence_anchor": "from __future__ import annotations",
        },
        {
            "id": "CFG-nested-values-opaque",
            "requirement": "Nested values are replaced as opaque values rather than recursively merged.",
            "required_semantic": "replace-not-recursive-merge",
            "evidence_anchor": "result.update",
        },
    ],
    "open_questions": [
        {
            "id": "CFG-delete-sentinel-typing",
            "question": "Which exported typing form should represent the deletion sentinel?",
        }
    ],
}

S_FILES = {
    "AGENTS.md": AGENT_INSTRUCTIONS,
    "options.md": '''# Configuration API options

## `pure-merge`

`merge(base, override)` returns a fresh mapping and has no retained request state. The raw sketch uses `dict.update`, so JSON null remains a value and there is no deletion operation unless a distinct sentinel is added. Nested values are replaced, not recursively merged.

## `config-builder`

`ConfigBuilder.add_layer(mapping).build()` makes future extension convenient, but the supplied shared caller reuses one builder between requests. The raw sketch retains every earlier layer unless callers remember to reset it.

A bounded variant may modify one option. Any selected variant must state request-isolation and deletion semantics explicitly. Option IDs and scenario IDs in the decision must use the spellings in this fixture.
''',
    "constraints.json": _json_file(S_CONSTRAINTS),
    "callers.py": '''from __future__ import annotations

import argparse
import json


def raw_merge(base: dict, override: dict) -> dict:
    result = dict(base)
    result.update(override)
    return result


class ConfigBuilder:
    def __init__(self) -> None:
        self.layers: list[dict] = []

    def add_layer(self, layer: dict) -> "ConfigBuilder":
        self.layers.append(dict(layer))
        return self

    def build(self) -> dict:
        result: dict = {}
        for layer in self.layers:
            result.update(layer)
        return result


def run_builder_leak() -> dict:
    shared = ConfigBuilder()
    shared.add_layer({"request": "one", "theme": "dark"}).build()
    observed = shared.add_layer({"request": "two", "region": "eu"}).build()
    return {
        "scenario_id": "builder-leak",
        "option_id": "config-builder",
        "violates": "CFG-request-isolation",
        "failure": "request-two-retains-request-one-theme",
        "observed": observed,
    }


def run_raw_merge_deletion() -> dict:
    observed = raw_merge({"token": "secret", "region": "us"}, {"token": None})
    return {
        "scenario_id": "raw-merge-deletion",
        "option_id": "pure-merge",
        "violates": "CFG-explicit-deletion",
        "failure": "token-remains-with-null-value",
        "observed": observed,
    }


SCENARIOS = {
    "builder-leak": run_builder_leak,
    "raw-merge-deletion": run_raw_merge_deletion,
}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--scenario", choices=sorted(SCENARIOS), required=True)
    args = parser.parse_args()
    print(json.dumps(SCENARIOS[args.scenario](), sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
''',
    "tests/test_callers.py": '''import unittest

from callers import run_builder_leak, run_raw_merge_deletion


class CallerEvidenceTests(unittest.TestCase):
    def test_builder_leak_is_reproducible(self):
        observed = run_builder_leak()
        self.assertEqual(observed["observed"]["theme"], "dark")
        self.assertEqual(observed["violates"], "CFG-request-isolation")

    def test_raw_merge_cannot_distinguish_delete_from_null(self):
        observed = run_raw_merge_deletion()
        self.assertIn("token", observed["observed"])
        self.assertIsNone(observed["observed"]["token"])


if __name__ == "__main__":
    unittest.main()
''',
    "tools/validate_decision.py": _artifact_validator(
        [
            "choice",
            "constraint_dispositions",
            "counterexamples",
            "claims",
            "unknowns",
            "document_markers",
        ]
    ),
}

S_GOOD_JSON = {
    "schema_version": 1,
    "choice": {
        "option_id": "pure-merge",
        "variant": "deletion-sentinel",
        "request_isolation": "fresh-state-per-call",
        "deletion": "explicit-delete-sentinel",
        "nested_values": "replace-not-recursive-merge",
    },
    "constraint_dispositions": [
        {
            "constraint_id": item["id"],
            "status": "satisfied",
            "semantic": item["required_semantic"],
            "evidence": {
                "path": "callers.py" if item["id"] != "CFG-no-third-party-dependencies" else "constraints.json",
                "anchor": item["evidence_anchor"] if item["id"] != "CFG-no-third-party-dependencies" else item["id"],
            },
        }
        for item in S_CONSTRAINTS["constraints"]
    ],
    "counterexamples": [
        {
            "option_id": "config-builder",
            "scenario_id": "builder-leak",
            "command": ["python3", "callers.py", "--scenario", "builder-leak"],
            "expected_violation": "CFG-request-isolation",
        },
        {
            "option_id": "pure-merge",
            "scenario_id": "raw-merge-deletion",
            "command": ["python3", "callers.py", "--scenario", "raw-merge-deletion"],
            "expected_violation": "CFG-explicit-deletion",
        },
    ],
    "claims": [
        {
            "id": "claim-request-isolation",
            "text": "A fresh pure call cannot retain a previous request layer.",
            "constraint_ids": ["CFG-request-isolation", "CFG-deterministic-result"],
            "evidence": {"path": "options.md", "anchor": "returns a fresh mapping"},
        },
        {
            "id": "claim-delete-sentinel",
            "text": "Deletion needs a sentinel distinct from JSON null.",
            "constraint_ids": ["CFG-explicit-deletion"],
            "evidence": {"path": "options.md", "anchor": "distinct sentinel"},
        },
    ],
    "unknowns": [
        {
            "id": "CFG-delete-sentinel-typing",
            "status": "open",
            "impact": "public typing form remains undecided",
        }
    ],
    "document_markers": [
        "choice:pure-merge",
        *[f"constraint:{item['id']}" for item in S_CONSTRAINTS["constraints"]],
        "counterexample:builder-leak",
        "counterexample:raw-merge-deletion",
        "claim:claim-request-isolation",
        "claim:claim-delete-sentinel",
        "unknown:CFG-delete-sentinel-typing",
    ],
}

S_GOOD_MD = '''# Configuration merge decision

<!-- architecture-marker:choice:pure-merge -->

Select the bounded `pure-merge` variant: each call creates fresh state, nested values are replaced, and an explicit deletion sentinel is distinct from JSON null. This satisfies request isolation without relying on caller reset discipline.

## Constraint dispositions

<!-- architecture-marker:constraint:CFG-request-isolation -->
<!-- architecture-marker:constraint:CFG-explicit-deletion -->
<!-- architecture-marker:constraint:CFG-deterministic-result -->
<!-- architecture-marker:constraint:CFG-no-third-party-dependencies -->
<!-- architecture-marker:constraint:CFG-nested-values-opaque -->

All five supplied constraints are dispositioned in `decision.json` with source anchors. The variant remains standard-library-only and preserves opaque nested replacement.

## Counterexamples and claims

<!-- architecture-marker:counterexample:builder-leak -->
`python3 callers.py --scenario builder-leak` demonstrates request-two retaining request-one state in the raw builder.

<!-- architecture-marker:counterexample:raw-merge-deletion -->
`python3 callers.py --scenario raw-merge-deletion` demonstrates that raw merge retains `token` with a null value rather than deleting it.

<!-- architecture-marker:claim:claim-request-isolation -->
A fresh pure call cannot retain a previous request layer.

<!-- architecture-marker:claim:claim-delete-sentinel -->
Deletion needs a sentinel distinct from JSON null.

## Open question

<!-- architecture-marker:unknown:CFG-delete-sentinel-typing -->
The fixture does not determine which exported typing form should represent the sentinel, so that remains open and decision-relevant.
'''

S_HIDDEN = _hidden_source(
    "HiddenSmallArchitectureTests",
    S_FILES,
    {"DECISION.md", "decision.json"},
    '''
def test_constraint_coverage(self):
    assert_fixture_integrity(self)
    decision = load_json_artifact(self, "decision.json")
    constraints = json.loads((WORKSPACE / "constraints.json").read_text(encoding="utf-8"))["constraints"]
    required = {item["id"]: item for item in constraints}
    dispositions = decision.get("constraint_dispositions")
    self.assertIsInstance(dispositions, list)
    observed = {item.get("constraint_id"): item for item in dispositions if isinstance(item, dict)}
    self.assertEqual(set(observed), set(required))
    for constraint_id, source in required.items():
        item = observed[constraint_id]
        self.assertEqual(item.get("semantic"), source["required_semantic"])
        self.assertEqual(item.get("status"), "satisfied")
        assert_source_reference(self, item.get("evidence"), {"callers.py", "options.md", "constraints.json"})

def test_counterexamples(self):
    assert_fixture_integrity(self)
    decision = load_json_artifact(self, "decision.json")
    counterexamples = decision.get("counterexamples")
    self.assertIsInstance(counterexamples, list)
    by_option = {item.get("option_id"): item for item in counterexamples if isinstance(item, dict)}
    self.assertEqual(set(by_option), {"pure-merge", "config-builder"})
    for option_id, item in by_option.items():
        command = item.get("command")
        self.assertIsInstance(command, list)
        self.assertEqual(
            command,
            ["python3", "callers.py", "--scenario", item.get("scenario_id")],
        )
        result = run_command(command)
        self.assertEqual(result.returncode, 0, result.stderr)
        observed = json.loads(result.stdout)
        self.assertEqual(observed.get("option_id"), option_id)
        self.assertEqual(observed.get("scenario_id"), item.get("scenario_id"))
        self.assertEqual(observed.get("violates"), item.get("expected_violation"))
        self.assertIn("failure", observed)

def test_selected_contract(self):
    assert_fixture_integrity(self)
    decision = load_json_artifact(self, "decision.json")
    choice = decision.get("choice")
    self.assertIsInstance(choice, dict)
    self.assertIn(choice.get("option_id"), {"pure-merge", "config-builder"})
    self.assertEqual(choice.get("request_isolation"), "fresh-state-per-call")
    self.assertEqual(choice.get("deletion"), "explicit-delete-sentinel")
    self.assertEqual(choice.get("nested_values"), "replace-not-recursive-merge")

def test_evidence_entailment(self):
    assert_fixture_integrity(self)
    decision = load_json_artifact(self, "decision.json")
    valid_constraints = {
        item["id"]
        for item in json.loads((WORKSPACE / "constraints.json").read_text(encoding="utf-8"))["constraints"]
    }
    claims = decision.get("claims")
    self.assertIsInstance(claims, list)
    self.assertTrue(claims)
    for claim in claims:
        self.assertTrue(set(claim.get("constraint_ids", [])).issubset(valid_constraints))
        self.assertTrue(claim.get("constraint_ids"))
        assert_source_reference(self, claim.get("evidence"), {"options.md", "callers.py", "constraints.json"})
    expected_unknowns = {
        item["id"]
        for item in json.loads((WORKSPACE / "constraints.json").read_text(encoding="utf-8"))["open_questions"]
    }
    unknowns = decision.get("unknowns", [])
    self.assertEqual({item.get("id") for item in unknowns}, expected_unknowns)
    self.assertTrue(
        all(
            item.get("status") in {"unknown", "open"}
            and (item.get("decision_impact") or item.get("impact"))
            for item in unknowns
        )
    )

def test_doc_json_sync(self):
    assert_fixture_integrity(self)
    decision = load_json_artifact(self, "decision.json")
    document = (WORKSPACE / "DECISION.md").read_text(encoding="utf-8")
    observed = MARKER.findall(document)
    derived = {
        f"choice:{decision.get('choice', {}).get('option_id')}",
        *{f"constraint:{item.get('constraint_id')}" for item in decision.get("constraint_dispositions", [])},
        *{f"counterexample:{item.get('scenario_id')}" for item in decision.get("counterexamples", [])},
        *{f"claim:{item.get('id')}" for item in decision.get("claims", [])},
        *{f"unknown:{item.get('id')}" for item in decision.get("unknowns", [])},
    }
    self.assertEqual(set(decision.get("document_markers", [])), derived)
    self.assertEqual(set(observed), derived)
    self.assertEqual(len(observed), len(set(observed)))
    for claim in decision.get("claims", []):
        self.assertIn(claim.get("text"), document)
''',
)

S_BAD_BUILDER = _replace_json(
    S_GOOD_JSON,
    choice={
        "option_id": "config-builder",
        "variant": "shared-builder",
        "request_isolation": "retained-layers",
        "deletion": "explicit-delete-sentinel",
        "nested_values": "replace-not-recursive-merge",
    },
)
S_BAD_NO_DELETE = _replace_json(
    S_GOOD_JSON,
    choice={
        "option_id": "pure-merge",
        "variant": "raw",
        "request_isolation": "fresh-state-per-call",
        "deletion": "null-value-only",
        "nested_values": "replace-not-recursive-merge",
    },
)
S_BAD_NO_COUNTEREXAMPLES = _replace_json(S_GOOD_JSON, counterexamples=[])
S_BAD_PERFORMANCE = _replace_json(
    S_GOOD_JSON,
    claims=[
        *S_GOOD_JSON["claims"],
        {
            "id": "claim-throughput",
            "text": "Pure merge meets an unmeasured throughput target.",
            "constraint_ids": ["CFG-throughput"],
            "evidence": {"path": "options.md", "anchor": "throughput benchmark"},
        },
    ],
)

S_MUTANT_MD = S_GOOD_MD


# ---------------------------------------------------------------------------
# M: scheduler, supervisor, and durable store responsibility split

M_MODEL = {
    "invariants": [
        {"id": "INV-at-least-once", "scenario_ids": ["restart-after-start", "timeout-retry"]},
        {"id": "INV-bounded-retry", "scenario_ids": ["timeout-retry", "retry-exhausted"]},
        {"id": "INV-durable-cancel", "scenario_ids": ["cancel-before-restart"]},
        {"id": "INV-single-process-owner", "scenario_ids": ["restart-after-start", "timeout-retry"]},
    ],
    "state_contract": [
        {"state_id": "job-intent", "durability": "durable", "required_owner": "store"},
        {"state_id": "attempt-budget", "durability": "durable", "required_owner": "store"},
        {"state_id": "cancel-intent", "durability": "durable", "required_owner": "store"},
        {"state_id": "process-handle", "durability": "ephemeral", "required_owner": "supervisor"},
        {"state_id": "heartbeat", "durability": "ephemeral", "required_owner": "supervisor"},
        {"state_id": "admission-cursor", "durability": "ephemeral", "required_owner": "scheduler"},
    ],
    "required_policies": {
        "retry_owner": "store",
        "cancellation_owner": "store",
        "process_owner": "supervisor",
        "admission_owner": "scheduler",
        "restart_action": "reconcile-durable-intent",
    },
    "scenarios": [
        {
            "id": "restart-after-start",
            "events": ["admit", "start", "supervisor-restart", "lease-expire"],
            "expected": {"outcome": "requeue", "attempt_delta": 1, "cancel_persisted": False},
        },
        {
            "id": "cancel-before-restart",
            "events": ["admit", "cancel", "supervisor-restart"],
            "expected": {"outcome": "terminal-cancelled", "attempt_delta": 0, "cancel_persisted": True},
        },
        {
            "id": "timeout-retry",
            "events": ["admit", "start", "timeout", "retry"],
            "expected": {"outcome": "requeue", "attempt_delta": 1, "cancel_persisted": False},
        },
        {
            "id": "retry-exhausted",
            "events": ["admit", "start", "timeout", "budget-exhausted"],
            "expected": {"outcome": "terminal-failed", "attempt_delta": 0, "cancel_persisted": False},
        },
    ],
    "migration_phases": ["inventory", "dual-read", "cutover", "rollback-window"],
    "required_signals": ["queue-depth", "process-heartbeat", "retry-budget", "cancel-lag"],
    "evidence_gaps": [
        {"id": "GAP-provider-idempotency", "question": "Can every provider operation be made idempotent?"},
        {"id": "GAP-heartbeat-threshold", "question": "Which timeout threshold fits natural workloads?"},
    ],
}

M_OPTIONS = {
    "options": [
        {
            "id": "scheduler-owns-retry",
            "summary": "Scheduler and supervisor independently decide retry.",
            "counterexample_scenario": "restart-after-start",
            "observed_failure": "duplicate-retry-decision-after-supervisor-restart",
        },
        {
            "id": "supervisor-owns-intent",
            "summary": "Cancellation exists only in supervisor process memory.",
            "counterexample_scenario": "cancel-before-restart",
            "observed_failure": "cancel-intent-lost-on-supervisor-restart",
        },
        {
            "id": "store-runs-processes",
            "summary": "The durable store also launches and monitors provider processes.",
            "counterexample_scenario": "timeout-retry",
            "observed_failure": "persistence-control-coupled-to-process-timeout",
        },
    ]
}

M_SIMULATOR = '''#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def load_json(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected object: {path}")
    return value


def validate_proposal(proposal: dict, scenario_id: str | None = None) -> list[str]:
    model = load_json(ROOT / "scenarios.json")
    errors: list[str] = []
    ownership = {
        item.get("state_id"): (item.get("owner"), item.get("durability"))
        for item in proposal.get("state_ownership", [])
        if isinstance(item, dict)
    }
    for contract in model["state_contract"]:
        expected = (contract["required_owner"], contract["durability"])
        if ownership.get(contract["state_id"]) != expected:
            errors.append(f"ownership mismatch: {contract['state_id']}")
    transitions = {
        item.get("scenario_id"): item.get("result")
        for item in proposal.get("transitions", [])
        if isinstance(item, dict)
    }
    scenarios = model["scenarios"]
    if scenario_id is not None:
        scenarios = [item for item in scenarios if item["id"] == scenario_id]
        if not scenarios:
            errors.append(f"unknown scenario: {scenario_id}")
    for scenario in scenarios:
        if transitions.get(scenario["id"]) != scenario["expected"]:
            errors.append(f"transition mismatch: {scenario['id']}")
    if proposal.get("policies") != model["required_policies"]:
        errors.append("responsibility policies do not match the declared contract")
    return errors


def reproduce_option(option_id: str, scenario_id: str) -> dict:
    options = load_json(ROOT / "options" / "catalog.json")["options"]
    matches = [item for item in options if item["id"] == option_id]
    if len(matches) != 1 or matches[0]["counterexample_scenario"] != scenario_id:
        raise ValueError("option/scenario counterexample link is not declared")
    item = matches[0]
    return {
        "option_id": option_id,
        "scenario_id": scenario_id,
        "observed_failure": item["observed_failure"],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--proposal", type=Path)
    parser.add_argument("--all-scenarios", action="store_true")
    parser.add_argument("--scenario")
    parser.add_argument("--option")
    args = parser.parse_args()
    if args.option:
        if not args.scenario:
            raise SystemExit("--option requires --scenario")
        print(json.dumps(reproduce_option(args.option, args.scenario), sort_keys=True, separators=(",", ":")))
        return 0
    if args.proposal is None:
        raise SystemExit("--proposal is required")
    proposal = load_json(args.proposal)
    errors = validate_proposal(proposal, None if args.all_scenarios else args.scenario)
    if errors:
        for error in errors:
            print(error)
        return 1
    print("proposal scenarios preserve the declared contracts")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
'''

M_FILES = {
    "AGENTS.md": AGENT_INSTRUCTIONS,
    "system.md": '''# Local job-system contract

Execution is at-least-once with a finite attempt budget. Cancellation intent must survive process restart. The scheduler admits durable work, the supervisor owns provider processes and heartbeats, and the store is durable but never launches processes. A restart reconciles durable intent before admitting another attempt.

All state, invariant, scenario, migration-phase, signal, and evidence-gap IDs are defined in `scenarios.json`. A proposal may choose a composed split rather than one raw option, but it must use those IDs and must not claim exactly-once behavior without idempotency evidence.
''',
    "options/catalog.json": _json_file(M_OPTIONS),
    "options/scheduler-owned.md": "# scheduler-owns-retry\n\nScheduler and supervisor independently decide retry, creating a restart race.\n",
    "options/supervisor-owned.md": "# supervisor-owns-intent\n\nCancellation remains only in supervisor memory.\n",
    "options/store-executes.md": "# store-runs-processes\n\nThe persistence component also launches provider processes.\n",
    "scenarios.json": _json_file(M_MODEL),
    "simulator.py": M_SIMULATOR,
    "tools/validate_proposal.py": _artifact_validator(
        [
            "selected_design",
            "invariants",
            "state_ownership",
            "policies",
            "transitions",
            "rejected_options",
            "migration",
            "observability",
            "guarantees",
            "unknowns",
            "document_markers",
        ]
    ),
}

M_GOOD_JSON = {
    "schema_version": 1,
    "selected_design": "durable-intent-process-supervision-split",
    "invariants": [
        {"id": item["id"], "test_scenarios": list(item["scenario_ids"])}
        for item in M_MODEL["invariants"]
    ],
    "state_ownership": [
        {
            "state_id": item["state_id"],
            "owner": item["required_owner"],
            "durability": item["durability"],
        }
        for item in M_MODEL["state_contract"]
    ],
    "policies": dict(M_MODEL["required_policies"]),
    "transitions": [
        {
            "scenario_id": item["id"],
            "events": list(item["events"]),
            "result": dict(item["expected"]),
        }
        for item in M_MODEL["scenarios"]
    ],
    "rejected_options": [
        {
            "option_id": item["id"],
            "counterexample_scenario": item["counterexample_scenario"],
            "expected_failure": item["observed_failure"],
            "command": [
                "python3",
                "simulator.py",
                "--option",
                item["id"],
                "--scenario",
                item["counterexample_scenario"],
            ],
        }
        for item in M_OPTIONS["options"]
    ],
    "migration": {
        "phases": list(M_MODEL["migration_phases"]),
        "rollback_until": "rollback-window",
    },
    "observability": [
        {"signal_id": signal, "owner": "store" if signal in {"queue-depth", "retry-budget", "cancel-lag"} else "supervisor"}
        for signal in M_MODEL["required_signals"]
    ],
    "guarantees": ["at-least-once", "bounded-retry"],
    "unknowns": [
        {"id": item["id"], "status": "unknown", "decision_impact": item["question"]}
        for item in M_MODEL["evidence_gaps"]
    ],
    "document_markers": [
        "design:durable-intent-process-supervision-split",
        *[f"invariant:{item['id']}" for item in M_MODEL["invariants"]],
        *[f"state:{item['state_id']}" for item in M_MODEL["state_contract"]],
        *[f"scenario:{item['id']}" for item in M_MODEL["scenarios"]],
        *[f"option:{item['id']}" for item in M_OPTIONS["options"]],
        *[f"phase:{item}" for item in M_MODEL["migration_phases"]],
        *[f"signal:{item}" for item in M_MODEL["required_signals"]],
        *[f"unknown:{item['id']}" for item in M_MODEL["evidence_gaps"]],
    ],
}

M_GOOD_MD = '''# Scheduler, supervisor, and store proposal

<!-- architecture-marker:design:durable-intent-process-supervision-split -->

Use a composed split: the store owns durable intent, budget, and cancellation; the scheduler admits from durable state; the supervisor alone owns processes and heartbeats. Restart begins with reconciliation.

## Invariants and state

<!-- architecture-marker:invariant:INV-at-least-once -->
<!-- architecture-marker:invariant:INV-bounded-retry -->
<!-- architecture-marker:invariant:INV-durable-cancel -->
<!-- architecture-marker:invariant:INV-single-process-owner -->
<!-- architecture-marker:state:job-intent -->
<!-- architecture-marker:state:attempt-budget -->
<!-- architecture-marker:state:cancel-intent -->
<!-- architecture-marker:state:process-handle -->
<!-- architecture-marker:state:heartbeat -->
<!-- architecture-marker:state:admission-cursor -->

The machine proposal assigns each declared datum exactly once and links every invariant to executable scenario evidence.

## Failure transitions

<!-- architecture-marker:scenario:restart-after-start -->
<!-- architecture-marker:scenario:cancel-before-restart -->
<!-- architecture-marker:scenario:timeout-retry -->
<!-- architecture-marker:scenario:retry-exhausted -->

Restart, cancellation, timeout, and retry exhaustion follow the results encoded in `scenarios.json` and are replayed by `simulator.py`.

## Rejected raw options

<!-- architecture-marker:option:scheduler-owns-retry -->
<!-- architecture-marker:option:supervisor-owns-intent -->
<!-- architecture-marker:option:store-runs-processes -->

Each rejection cites and executes the option/scenario pair declared by the fixture rather than a preference adjective.

## Migration and observability

<!-- architecture-marker:phase:inventory -->
<!-- architecture-marker:phase:dual-read -->
<!-- architecture-marker:phase:cutover -->
<!-- architecture-marker:phase:rollback-window -->
<!-- architecture-marker:signal:queue-depth -->
<!-- architecture-marker:signal:process-heartbeat -->
<!-- architecture-marker:signal:retry-budget -->
<!-- architecture-marker:signal:cancel-lag -->

Inventory precedes dual-read and cutover; the rollback window remains explicit. Signals separate durable queue/cancel/budget state from process heartbeat state.

## Unknowns

<!-- architecture-marker:unknown:GAP-provider-idempotency -->
<!-- architecture-marker:unknown:GAP-heartbeat-threshold -->

Provider idempotency and the correct heartbeat threshold remain unknown. Therefore the design claims at-least-once, not exactly-once execution.
'''

M_HIDDEN = _hidden_source(
    "HiddenMediumArchitectureTests",
    M_FILES,
    {"PROPOSAL.md", "proposal.json"},
    '''
def test_invariant_coverage(self):
    assert_fixture_integrity(self)
    proposal = load_json_artifact(self, "proposal.json")
    model = json.loads((WORKSPACE / "scenarios.json").read_text(encoding="utf-8"))
    expected = {item["id"]: set(item["scenario_ids"]) for item in model["invariants"]}
    observed = {
        item.get("id"): set(item.get("test_scenarios", []))
        for item in proposal.get("invariants", [])
        if isinstance(item, dict)
    }
    self.assertEqual(observed, expected)

def test_state_ownership(self):
    assert_fixture_integrity(self)
    proposal = load_json_artifact(self, "proposal.json")
    model = json.loads((WORKSPACE / "scenarios.json").read_text(encoding="utf-8"))
    expected = {
        item["state_id"]: (item["required_owner"], item["durability"])
        for item in model["state_contract"]
    }
    rows = proposal.get("state_ownership", [])
    observed = {}
    for item in rows:
        self.assertNotIn(item.get("state_id"), observed, "state has conflicting owners")
        observed[item.get("state_id")] = (item.get("owner"), item.get("durability"))
    self.assertEqual(observed, expected)
    self.assertEqual(proposal.get("policies"), model["required_policies"])

def test_failure_transitions(self):
    assert_fixture_integrity(self)
    result = run_command(["python3", "simulator.py", "--proposal", "proposal.json", "--all-scenarios"])
    self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
    proposal = load_json_artifact(self, "proposal.json")
    transitions = {item["scenario_id"]: item["result"] for item in proposal.get("transitions", [])}
    self.assertEqual(transitions["cancel-before-restart"]["cancel_persisted"], True)
    self.assertEqual(transitions["retry-exhausted"]["outcome"], "terminal-failed")

def test_option_counterexamples(self):
    assert_fixture_integrity(self)
    proposal = load_json_artifact(self, "proposal.json")
    catalog = json.loads((WORKSPACE / "options/catalog.json").read_text(encoding="utf-8"))["options"]
    expected = {item["id"]: item for item in catalog}
    observed = {item.get("option_id"): item for item in proposal.get("rejected_options", [])}
    self.assertEqual(set(observed), set(expected))
    for option_id, source in expected.items():
        item = observed[option_id]
        self.assertEqual(item.get("counterexample_scenario"), source["counterexample_scenario"])
        self.assertEqual(item.get("expected_failure"), source["observed_failure"])
        command = item.get("command")
        self.assertEqual(
            command,
            [
                "python3",
                "simulator.py",
                "--option",
                option_id,
                "--scenario",
                source["counterexample_scenario"],
            ],
        )
        result = run_command(command)
        self.assertEqual(result.returncode, 0, result.stderr)
        replay = json.loads(result.stdout)
        self.assertEqual(replay["observed_failure"], source["observed_failure"])

def test_migration_observability(self):
    assert_fixture_integrity(self)
    proposal = load_json_artifact(self, "proposal.json")
    model = json.loads((WORKSPACE / "scenarios.json").read_text(encoding="utf-8"))
    self.assertEqual(proposal.get("migration", {}).get("phases"), model["migration_phases"])
    self.assertEqual(proposal.get("migration", {}).get("rollback_until"), "rollback-window")
    observed = {item.get("signal_id") for item in proposal.get("observability", [])}
    self.assertEqual(observed, set(model["required_signals"]))
    self.assertTrue(all(item.get("owner") in {"store", "supervisor", "scheduler"} for item in proposal["observability"]))

def test_unknown_honesty(self):
    assert_fixture_integrity(self)
    proposal = load_json_artifact(self, "proposal.json")
    model = json.loads((WORKSPACE / "scenarios.json").read_text(encoding="utf-8"))
    expected = {item["id"] for item in model["evidence_gaps"]}
    unknowns = proposal.get("unknowns", [])
    self.assertEqual({item.get("id") for item in unknowns}, expected)
    self.assertTrue(all(item.get("status") == "unknown" and item.get("decision_impact") for item in unknowns))
    self.assertEqual(set(proposal.get("guarantees", [])), {"at-least-once", "bounded-retry"})
''',
)

M_BAD_RETRY_CONFLICT = _replace_json(
    M_GOOD_JSON,
    state_ownership=[
        *M_GOOD_JSON["state_ownership"],
        {"state_id": "attempt-budget", "owner": "scheduler", "durability": "ephemeral"},
    ],
)
M_BAD_CANCEL_MEMORY = _replace_json(
    M_GOOD_JSON,
    state_ownership=[
        {
            **item,
            **({"owner": "supervisor", "durability": "ephemeral"} if item["state_id"] == "cancel-intent" else {}),
        }
        for item in M_GOOD_JSON["state_ownership"]
    ],
)
M_BAD_NO_TRANSITIONS = _replace_json(M_GOOD_JSON, transitions=[])
M_BAD_EXACTLY_ONCE = _replace_json(M_GOOD_JSON, guarantees=["exactly-once", "bounded-retry"], unknowns=[])
M_BAD_PREFERENCE_REJECTIONS = _replace_json(
    M_GOOD_JSON,
    rejected_options=[
        {"option_id": item["id"], "reason": "less elegant"}
        for item in M_OPTIONS["options"]
    ],
)


# ---------------------------------------------------------------------------
# L: execution fabric, persistence, security, migration, and operations

L_FUNCTIONAL = {
    "requirements": [
        {
            "id": "FUNC-durable-job-intent",
            "statement": "Job intent, leases, and attempt budget survive worker and orchestrator restart.",
            "accepted_evidence_ids": ["INC-direct-crash-lost", "INC-stale-lease"],
        },
        {
            "id": "FUNC-at-least-once-bounded",
            "statement": "Execution is at-least-once with an explicit finite attempt budget.",
            "accepted_evidence_ids": ["INC-stale-lease"],
        },
        {
            "id": "FUNC-ui-fail-open",
            "statement": "Companion/UI loss never pauses, cancels, or completes a job.",
            "accepted_evidence_ids": ["INC-ui-disconnect"],
        },
        {
            "id": "FUNC-finite-job-lifecycle",
            "statement": "Every finite job reaches success, cancelled, failed, or exhausted terminal state.",
            "accepted_evidence_ids": ["INC-stale-lease", "INC-direct-crash-lost"],
        },
    ]
}

L_SECURITY = {
    "requirements": [
        {
            "id": "SEC-workspace-isolation",
            "boundary": "workspace-to-host",
            "required_control": "workspace-only-mount",
            "required_owner": "worker",
            "accepted_evidence_ids": ["INC-direct-crash-lost"],
        },
        {
            "id": "SEC-credential-scope",
            "boundary": "credential-broker-to-provider-adapter",
            "required_control": "scoped-revocable-handle",
            "required_owner": "credential-broker",
            "accepted_evidence_ids": ["INC-central-credential-scope"],
        },
        {
            "id": "SEC-docker-boundary",
            "boundary": "worker-to-docker-daemon",
            "required_control": "no-shared-docker-socket",
            "required_owner": "worker",
            "accepted_evidence_ids": ["INC-direct-crash-lost"],
        },
        {
            "id": "SEC-host-boundary",
            "boundary": "job-workspace-to-host-filesystem",
            "required_control": "no-host-filesystem-mount",
            "required_owner": "worker",
            "accepted_evidence_ids": ["INC-central-credential-scope"],
        },
    ]
}

L_OPERATIONS = {
    "requirements": [
        {
            "id": "OPS-cleanup-owner",
            "statement": "Durable cleanup intent and ephemeral cleanup execution each have one owner.",
            "accepted_evidence_ids": ["INC-direct-crash-lost"],
        },
        {
            "id": "OPS-migration-rollback",
            "statement": "Migration is staged, observable, abortable, resumable, and non-destructive.",
            "accepted_evidence_ids": ["INC-daemon-split-observability"],
        },
        {
            "id": "OPS-diagnostic-states",
            "statement": "Signals distinguish queue, provider, worker, validation, recovery, and migration state.",
            "accepted_evidence_ids": ["INC-daemon-split-observability", "INC-stale-lease"],
        },
        {
            "id": "OPS-credential-rotation",
            "statement": "Rotation revokes old handles while new jobs obtain current scoped handles.",
            "accepted_evidence_ids": ["INC-central-credential-scope"],
        },
    ]
}

L_MODEL = {
    "state_contract": [
        {"state_id": "job-intent", "owner": "job-store", "durability": "durable"},
        {"state_id": "lease", "owner": "job-store", "durability": "durable"},
        {"state_id": "attempt-budget", "owner": "job-store", "durability": "durable"},
        {"state_id": "event-ledger", "owner": "event-store", "durability": "durable"},
        {"state_id": "provider-process", "owner": "worker", "durability": "ephemeral"},
        {"state_id": "credential-material", "owner": "credential-broker", "durability": "durable-external"},
        {"state_id": "credential-handle", "owner": "provider-adapter", "durability": "ephemeral"},
        {"state_id": "cleanup-intent", "owner": "job-store", "durability": "durable"},
        {"state_id": "cleanup-process", "owner": "cleanup-supervisor", "durability": "ephemeral"},
        {"state_id": "ui-state", "owner": "companion-ui", "durability": "ephemeral"},
        {"state_id": "workspace", "owner": "worker", "durability": "ephemeral"},
    ],
    "required_roles": [
        "job-store",
        "event-store",
        "orchestrator",
        "worker",
        "provider-adapter",
        "credential-broker",
        "cleanup-supervisor",
        "companion-ui",
    ],
    "failure_policies": {
        "worker-crash": "expire-lease-and-requeue-with-budget",
        "stale-lease": "fence-stale-worker-and-requeue-with-budget",
        "provider-loss": "record-provider-failure-and-consume-budget",
        "ui-disconnect": "continue-job-from-durable-state",
        "credential-rotation": "revoke-old-handle-and-issue-current",
        "retry-exhausted": "terminal-failed",
    },
    "visible_scenarios": ["worker-crash", "stale-lease", "ui-disconnect"],
    "migration": {
        "phase_order": [
            "inventory",
            "dual-write",
            "dual-read-verify",
            "cutover",
            "rollback-window",
            "retire",
        ],
        "phase_contract": {
            "inventory": {"abort_action": "leave-legacy-active", "signal": "migration-inventory-count"},
            "dual-write": {"abort_action": "stop-new-writes-use-legacy", "signal": "dual-write-divergence"},
            "dual-read-verify": {"abort_action": "restore-legacy-read", "signal": "dual-read-mismatch"},
            "cutover": {"abort_action": "restore-legacy-read", "signal": "cutover-error-rate"},
            "rollback-window": {"abort_action": "export-and-restore-legacy", "signal": "rollback-readiness"},
            "retire": {"abort_action": "restore-from-backup", "signal": "legacy-retirement-status"},
        },
        "rollback": {
            "source": "legacy-ledger",
            "output": "rollback-export",
            "mutates_new_store": False,
            "resume_key": "migration-checkpoint",
        },
    },
    "observability": [
        {"category": "queue", "signal": "queue-depth", "owner": "job-store"},
        {"category": "provider", "signal": "provider-health", "owner": "provider-adapter"},
        {"category": "worker", "signal": "lease-heartbeat", "owner": "worker"},
        {"category": "validation", "signal": "validation-result", "owner": "orchestrator"},
        {"category": "recovery", "signal": "recovery-action", "owner": "cleanup-supervisor"},
        {"category": "migration", "signal": "migration-phase", "owner": "orchestrator"},
    ],
}

L_INCIDENTS = {
    "evidence": [
        {"id": "INC-direct-crash-lost", "finding": "Direct subprocess ownership lost job state and cleanup intent after orchestrator crash."},
        {"id": "INC-central-credential-scope", "finding": "Central queue prototype exposed all provider credentials to one persistence service."},
        {"id": "INC-daemon-split-observability", "finding": "Per-provider daemons produced incompatible lifecycle and migration signals."},
        {"id": "INC-ui-disconnect", "finding": "UI disconnect occurred while the provider job continued correctly."},
        {"id": "INC-stale-lease", "finding": "A stale worker reported after its lease was reassigned and required fencing."},
    ]
}

L_BENCHMARKS = {
    "evidence": [
        {"id": "BEN-direct-start-latency", "finding": "Direct subprocess had the lowest nominal start latency in a small local sample."}
    ],
    "evidence_gaps": [
        {"id": "GAP-provider-idempotency", "question": "Provider-side idempotency guarantees are unmeasured."},
        {"id": "GAP-backend-scale", "question": "Backend throughput and retention limits are unmeasured."},
    ],
}

L_PROPOSALS = {
    "options": [
        {
            "id": "direct-subprocess",
            "decisive_evidence_id": "INC-direct-crash-lost",
            "counterexample": "worker-crash",
        },
        {
            "id": "central-database-queue",
            "decisive_evidence_id": "INC-central-credential-scope",
            "counterexample": "credential-rotation",
        },
        {
            "id": "per-provider-daemons",
            "decisive_evidence_id": "INC-daemon-split-observability",
            "counterexample": "provider-loss",
        },
    ]
}

L_SIMULATOR = '''#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def load_json(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected object: {path}")
    return value


def evaluate(design: dict, scenario_set: str) -> list[str]:
    model = load_json(ROOT / "requirements" / "model.json")
    errors: list[str] = []
    ownership = {
        item.get("state_id"): (item.get("owner"), item.get("durability"))
        for item in design.get("state_ownership", [])
        if isinstance(item, dict)
    }
    expected_ownership = {
        item["state_id"]: (item["owner"], item["durability"])
        for item in model["state_contract"]
    }
    if ownership != expected_ownership:
        errors.append("state ownership does not match the declared contract")
    roles = [item.get("role") for item in design.get("topology", []) if isinstance(item, dict)]
    if set(roles) != set(model["required_roles"]) or len(roles) != len(set(roles)):
        errors.append("topology roles are missing or duplicated")
    policies = design.get("failure_policies", {})
    scenario_ids = model["visible_scenarios"] if scenario_set == "visible" else list(model["failure_policies"])
    for scenario_id in scenario_ids:
        if policies.get(scenario_id) != model["failure_policies"][scenario_id]:
            errors.append(f"failure policy mismatch: {scenario_id}")
    if any(value == "retry-unbounded" for value in policies.values()):
        errors.append("unbounded retry violates finite lifecycle")
    if policies.get("ui-disconnect") != "continue-job-from-durable-state":
        errors.append("UI is not fail-open")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--design", type=Path, required=True)
    parser.add_argument("--scenario-set", choices=["visible", "all"], required=True)
    args = parser.parse_args()
    errors = evaluate(load_json(args.design), args.scenario_set)
    if errors:
        for error in errors:
            print(error)
        return 1
    print("execution-fabric scenarios preserve declared ownership and lifecycle")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
'''

L_MIGRATION_REPLAY = '''#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("design", type=Path)
    parser.add_argument("scenario_set", choices=["visible", "calibration"])
    args = parser.parse_args()
    design = json.loads(args.design.read_text(encoding="utf-8"))
    model = json.loads((ROOT / "requirements" / "model.json").read_text(encoding="utf-8"))["migration"]
    migration = design.get("migration", {})
    phases = migration.get("phases", [])
    if [item.get("id") for item in phases] != model["phase_order"]:
        raise SystemExit("migration phase order mismatch")
    selected = phases if args.scenario_set == "calibration" else phases[:5]
    for phase in selected:
        contract = model["phase_contract"][phase["id"]]
        if phase.get("abort_action") != contract["abort_action"]:
            raise SystemExit(f"abort mismatch: {phase['id']}")
        if phase.get("signal") != contract["signal"]:
            raise SystemExit(f"signal mismatch: {phase['id']}")
        if phase.get("source_preserved") is not True:
            raise SystemExit(f"source is destructive: {phase['id']}")
    if migration.get("rollback") != model["rollback"]:
        raise SystemExit("rollback contract mismatch")
    print("migration cuts are abortable, resumable, and non-destructive")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
'''

L_FILES = {
    "AGENTS.md": AGENT_INSTRUCTIONS,
    "requirements/functional.json": _json_file(L_FUNCTIONAL),
    "requirements/security.json": _json_file(L_SECURITY),
    "requirements/operations.json": _json_file(L_OPERATIONS),
    "requirements/model.json": _json_file(L_MODEL),
    "proposals/catalog.json": _json_file(L_PROPOSALS),
    "proposals/direct-subprocess.md": "# direct-subprocess\n\nLowest local start latency, but no durable recovery owner.\n",
    "proposals/central-database-queue.md": "# central-database-queue\n\nDurable queue, but the prototype centralizes credential and cleanup authority.\n",
    "proposals/per-provider-daemons.md": "# per-provider-daemons\n\nProvider isolation, but lifecycle signals and migration behavior diverge.\n",
    "evidence/incidents.json": _json_file(L_INCIDENTS),
    "evidence/benchmarks.json": _json_file(L_BENCHMARKS),
    "tests/test_evidence.py": '''import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


class EvidenceFixtureTests(unittest.TestCase):
    def test_requirement_and_evidence_ids_are_unique(self):
        requirement_ids = []
        for name in ("functional", "security", "operations"):
            value = json.loads((ROOT / "requirements" / f"{name}.json").read_text(encoding="utf-8"))
            requirement_ids.extend(item["id"] for item in value["requirements"])
        self.assertEqual(len(requirement_ids), len(set(requirement_ids)))
        incidents = json.loads((ROOT / "evidence" / "incidents.json").read_text(encoding="utf-8"))
        evidence_ids = [item["id"] for item in incidents["evidence"]]
        self.assertEqual(len(evidence_ids), len(set(evidence_ids)))


if __name__ == "__main__":
    unittest.main()
''',
    "simulator.py": L_SIMULATOR,
    "tools/validate_design.py": _artifact_validator(
        [
            "selected_design",
            "requirement_dispositions",
            "topology",
            "state_ownership",
            "failure_policies",
            "migration",
            "security_controls",
            "observability",
            "alternatives",
            "claims",
            "unknowns",
            "document_markers",
        ]
    ),
    "tools/replay_migration.py": L_MIGRATION_REPLAY,
    "tools/replay_migration.sh": '''#!/usr/bin/env bash
set -euo pipefail
root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
exec python3 "$root/tools/replay_migration.py" "$1" "$2"
''',
}

L_ALL_REQUIREMENTS = [
    *L_FUNCTIONAL["requirements"],
    *L_SECURITY["requirements"],
    *L_OPERATIONS["requirements"],
]

L_GOOD_JSON = {
    "schema_version": 1,
    "selected_design": "finite-job-fabric",
    "requirement_dispositions": [
        {
            "requirement_id": item["id"],
            "status": "satisfied",
            "evidence_ids": list(item["accepted_evidence_ids"][:1]),
        }
        for item in L_ALL_REQUIREMENTS
    ],
    "topology": [
        {"component_id": f"component-{role}", "role": role, "bounded_lifecycle": role not in {"job-store", "event-store", "credential-broker"}}
        for role in L_MODEL["required_roles"]
    ],
    "state_ownership": [dict(item) for item in L_MODEL["state_contract"]],
    "failure_policies": dict(L_MODEL["failure_policies"]),
    "migration": {
        "phases": [
            {
                "id": phase_id,
                "abort_action": L_MODEL["migration"]["phase_contract"][phase_id]["abort_action"],
                "signal": L_MODEL["migration"]["phase_contract"][phase_id]["signal"],
                "source_preserved": True,
            }
            for phase_id in L_MODEL["migration"]["phase_order"]
        ],
        "rollback": dict(L_MODEL["migration"]["rollback"]),
    },
    "security_controls": [
        {
            "requirement_id": item["id"],
            "boundary": item["boundary"],
            "control": item["required_control"],
            "owner": item["required_owner"],
            "counterexample_evidence_id": item["accepted_evidence_ids"][0],
        }
        for item in L_SECURITY["requirements"]
    ],
    "observability": [dict(item) for item in L_MODEL["observability"]],
    "alternatives": [
        {
            "option_id": item["id"],
            "disposition": "rejected-as-standalone",
            "decisive_evidence_id": item["decisive_evidence_id"],
            "counterexample": item["counterexample"],
        }
        for item in L_PROPOSALS["options"]
    ],
    "claims": [
        {
            "id": "claim-at-least-once",
            "statement": "The fabric provides at-least-once execution with a finite budget.",
            "requirement_ids": ["FUNC-at-least-once-bounded", "FUNC-finite-job-lifecycle"],
            "evidence_ids": ["INC-stale-lease"],
        },
        {
            "id": "claim-ui-fail-open",
            "statement": "UI state is observational and cannot decide job correctness.",
            "requirement_ids": ["FUNC-ui-fail-open"],
            "evidence_ids": ["INC-ui-disconnect"],
        },
    ],
    "unknowns": [
        {"id": item["id"], "status": "unknown", "decision_impact": item["question"]}
        for item in L_BENCHMARKS["evidence_gaps"]
    ],
    "document_markers": [
        "design:finite-job-fabric",
        *[f"requirement:{item['id']}" for item in L_ALL_REQUIREMENTS],
        *[f"state:{item['state_id']}" for item in L_MODEL["state_contract"]],
        *[f"failure:{item}" for item in L_MODEL["failure_policies"]],
        *[f"migration:{item}" for item in L_MODEL["migration"]["phase_order"]],
        *[f"security:{item['id']}" for item in L_SECURITY["requirements"]],
        *[f"signal:{item['category']}" for item in L_MODEL["observability"]],
        *[f"alternative:{item['id']}" for item in L_PROPOSALS["options"]],
        "claim:claim-at-least-once",
        "claim:claim-ui-fail-open",
        *[f"unknown:{item['id']}" for item in L_BENCHMARKS["evidence_gaps"]],
    ],
}

L_GOOD_MD = '''# Execution fabric and persistence design

<!-- architecture-marker:design:finite-job-fabric -->

Select a finite job fabric that separates durable intent, leases, budgets, and events from bounded workers and provider adapters. The companion remains observational. Stores and the credential broker are services; every launched job, cleanup, and adapter action is finite and supervised.

## Requirement disposition

<!-- architecture-marker:requirement:FUNC-durable-job-intent -->
<!-- architecture-marker:requirement:FUNC-at-least-once-bounded -->
<!-- architecture-marker:requirement:FUNC-ui-fail-open -->
<!-- architecture-marker:requirement:FUNC-finite-job-lifecycle -->
<!-- architecture-marker:requirement:SEC-workspace-isolation -->
<!-- architecture-marker:requirement:SEC-credential-scope -->
<!-- architecture-marker:requirement:SEC-docker-boundary -->
<!-- architecture-marker:requirement:SEC-host-boundary -->
<!-- architecture-marker:requirement:OPS-cleanup-owner -->
<!-- architecture-marker:requirement:OPS-migration-rollback -->
<!-- architecture-marker:requirement:OPS-diagnostic-states -->
<!-- architecture-marker:requirement:OPS-credential-rotation -->

Every visible requirement has a supported disposition in `design.json`; incident IDs, rather than assumed production guarantees, provide the evidence links.

## State and ownership

<!-- architecture-marker:state:job-intent -->
<!-- architecture-marker:state:lease -->
<!-- architecture-marker:state:attempt-budget -->
<!-- architecture-marker:state:event-ledger -->
<!-- architecture-marker:state:provider-process -->
<!-- architecture-marker:state:credential-material -->
<!-- architecture-marker:state:credential-handle -->
<!-- architecture-marker:state:cleanup-intent -->
<!-- architecture-marker:state:cleanup-process -->
<!-- architecture-marker:state:ui-state -->
<!-- architecture-marker:state:workspace -->

The state table assigns one owner and durability class to each item. UI state never owns durable job intent; credential material remains with the broker and adapters receive revocable handles.

## Failure and recovery

<!-- architecture-marker:failure:worker-crash -->
<!-- architecture-marker:failure:stale-lease -->
<!-- architecture-marker:failure:provider-loss -->
<!-- architecture-marker:failure:ui-disconnect -->
<!-- architecture-marker:failure:credential-rotation -->
<!-- architecture-marker:failure:retry-exhausted -->

Crash and stale lease paths fence old ownership before bounded requeue. Provider loss consumes budget, exhaustion is terminal, credential rotation revokes the old handle, and UI disconnect leaves correctness unchanged.

## Migration and rollback

<!-- architecture-marker:migration:inventory -->
<!-- architecture-marker:migration:dual-write -->
<!-- architecture-marker:migration:dual-read-verify -->
<!-- architecture-marker:migration:cutover -->
<!-- architecture-marker:migration:rollback-window -->
<!-- architecture-marker:migration:retire -->

Each phase declares its abort action, diagnostic signal, and source preservation. Checkpoints support resume; rollback exports legacy state without mutating the new store, and backup remains available through retirement.

## Security boundaries

<!-- architecture-marker:security:SEC-workspace-isolation -->
<!-- architecture-marker:security:SEC-credential-scope -->
<!-- architecture-marker:security:SEC-docker-boundary -->
<!-- architecture-marker:security:SEC-host-boundary -->

Workspace-only mounts, no shared Docker socket, no host filesystem mount, and scoped revocable credential handles are enforceable controls owned by the roles named in the requirement files.

## Observability

<!-- architecture-marker:signal:queue -->
<!-- architecture-marker:signal:provider -->
<!-- architecture-marker:signal:worker -->
<!-- architecture-marker:signal:validation -->
<!-- architecture-marker:signal:recovery -->
<!-- architecture-marker:signal:migration -->

Signals distinguish queue, provider, worker, validation, recovery, and migration state so an operator can identify which owner must act.

## Alternatives and evidence

<!-- architecture-marker:alternative:direct-subprocess -->
<!-- architecture-marker:alternative:central-database-queue -->
<!-- architecture-marker:alternative:per-provider-daemons -->

The direct, central queue, and daemon options are rejected as standalone designs using their declared incident counterexamples. Nominal direct-start latency does not override crash evidence.

<!-- architecture-marker:claim:claim-at-least-once -->
<!-- architecture-marker:claim:claim-ui-fail-open -->

## Unknowns

<!-- architecture-marker:unknown:GAP-provider-idempotency -->
<!-- architecture-marker:unknown:GAP-backend-scale -->

Provider idempotency and backend scale remain unknown. The design therefore does not claim exactly-once execution, linearizability, or production capacity unsupported by fixture evidence.
'''

L_HIDDEN = _hidden_source(
    "HiddenLargeArchitectureTests",
    L_FILES,
    {"DESIGN.md", "design.json"},
    '''
def test_requirement_coverage(self):
    assert_fixture_integrity(self)
    design = load_json_artifact(self, "design.json")
    requirements = []
    for name in ("functional", "security", "operations"):
        requirements.extend(json.loads((WORKSPACE / "requirements" / f"{name}.json").read_text(encoding="utf-8"))["requirements"])
    expected = {item["id"]: item for item in requirements}
    observed = {item.get("requirement_id"): item for item in design.get("requirement_dispositions", [])}
    self.assertEqual(set(observed), set(expected))
    evidence = json.loads((WORKSPACE / "evidence/incidents.json").read_text(encoding="utf-8"))["evidence"]
    valid_evidence = {item["id"] for item in evidence}
    for requirement_id, source in expected.items():
        item = observed[requirement_id]
        self.assertEqual(item.get("status"), "satisfied")
        used = set(item.get("evidence_ids", []))
        self.assertTrue(used)
        self.assertTrue(used.issubset(set(source["accepted_evidence_ids"])))
        self.assertTrue(used.issubset(valid_evidence))

def test_topology_ownership(self):
    assert_fixture_integrity(self)
    design = load_json_artifact(self, "design.json")
    model = json.loads((WORKSPACE / "requirements/model.json").read_text(encoding="utf-8"))
    rows = design.get("state_ownership", [])
    observed = {}
    for item in rows:
        self.assertNotIn(item.get("state_id"), observed, "state has multiple owners")
        observed[item.get("state_id")] = (item.get("owner"), item.get("durability"))
    expected = {item["state_id"]: (item["owner"], item["durability"]) for item in model["state_contract"]}
    self.assertEqual(observed, expected)
    roles = [item.get("role") for item in design.get("topology", [])]
    self.assertEqual(set(roles), set(model["required_roles"]))
    self.assertEqual(len(roles), len(set(roles)))

def test_failure_recovery(self):
    assert_fixture_integrity(self)
    result = run_command(["python3", "simulator.py", "--design", "design.json", "--scenario-set", "all"])
    self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
    design = load_json_artifact(self, "design.json")
    policies = design.get("failure_policies", {})
    self.assertTrue(all("unbounded" not in str(value) for value in policies.values()))
    self.assertEqual(policies.get("ui-disconnect"), "continue-job-from-durable-state")
    self.assertEqual(policies.get("retry-exhausted"), "terminal-failed")

def test_migration_rollback(self):
    assert_fixture_integrity(self)
    result = run_command(["bash", "tools/replay_migration.sh", "design.json", "calibration"])
    self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
    design = load_json_artifact(self, "design.json")
    migration = design.get("migration", {})
    self.assertTrue(all(item.get("source_preserved") is True for item in migration.get("phases", [])))
    rollback = migration.get("rollback", {})
    self.assertIs(rollback.get("mutates_new_store"), False)
    self.assertTrue(rollback.get("resume_key"))

def test_security_boundaries(self):
    assert_fixture_integrity(self)
    design = load_json_artifact(self, "design.json")
    requirements = json.loads((WORKSPACE / "requirements/security.json").read_text(encoding="utf-8"))["requirements"]
    expected = {item["id"]: item for item in requirements}
    observed = {item.get("requirement_id"): item for item in design.get("security_controls", [])}
    self.assertEqual(set(observed), set(expected))
    for requirement_id, source in expected.items():
        item = observed[requirement_id]
        self.assertEqual(item.get("boundary"), source["boundary"])
        self.assertEqual(item.get("control"), source["required_control"])
        self.assertEqual(item.get("owner"), source["required_owner"])
        self.assertIn(item.get("counterexample_evidence_id"), source["accepted_evidence_ids"])

def test_observability(self):
    assert_fixture_integrity(self)
    design = load_json_artifact(self, "design.json")
    model = json.loads((WORKSPACE / "requirements/model.json").read_text(encoding="utf-8"))
    expected = {item["category"]: (item["signal"], item["owner"]) for item in model["observability"]}
    observed = {item.get("category"): (item.get("signal"), item.get("owner")) for item in design.get("observability", [])}
    self.assertEqual(observed, expected)

def test_alternative_counterexamples(self):
    assert_fixture_integrity(self)
    design = load_json_artifact(self, "design.json")
    catalog = json.loads((WORKSPACE / "proposals/catalog.json").read_text(encoding="utf-8"))["options"]
    expected = {item["id"]: item for item in catalog}
    observed = {item.get("option_id"): item for item in design.get("alternatives", [])}
    self.assertEqual(set(observed), set(expected))
    incident_ids = {item["id"] for item in json.loads((WORKSPACE / "evidence/incidents.json").read_text(encoding="utf-8"))["evidence"]}
    for option_id, source in expected.items():
        item = observed[option_id]
        self.assertIn(item.get("disposition"), {"rejected-as-standalone", "incorporated-with-mitigation"})
        self.assertEqual(item.get("decisive_evidence_id"), source["decisive_evidence_id"])
        self.assertIn(item.get("decisive_evidence_id"), incident_ids)
        self.assertEqual(item.get("counterexample"), source["counterexample"])

def test_unknown_honesty(self):
    assert_fixture_integrity(self)
    design = load_json_artifact(self, "design.json")
    benchmarks = json.loads((WORKSPACE / "evidence/benchmarks.json").read_text(encoding="utf-8"))
    expected = {item["id"] for item in benchmarks["evidence_gaps"]}
    unknowns = design.get("unknowns", [])
    self.assertEqual({item.get("id") for item in unknowns}, expected)
    self.assertTrue(all(item.get("status") == "unknown" and item.get("decision_impact") for item in unknowns))
    claims = design.get("claims", [])
    unsupported_topics = ("exactly-once", "lineariz", "production capacity", "throughput", "backend scale")
    uncertainty_cues = ("unknown", "unmeasured", "unsupported", "cannot", "does not", "not ")
    for claim in claims:
        statement = str(claim.get("statement", claim.get("text", ""))).lower()
        if any(topic in statement for topic in unsupported_topics):
            self.assertTrue(
                any(cue in statement for cue in uncertainty_cues),
                f"unsupported positive architecture claim: {statement}",
            )
    valid_requirements = {item["requirement_id"] for item in design.get("requirement_dispositions", [])}
    valid_evidence = {item["id"] for item in json.loads((WORKSPACE / "evidence/incidents.json").read_text(encoding="utf-8"))["evidence"]}
    for claim in claims:
        self.assertTrue(set(claim.get("requirement_ids", [])).issubset(valid_requirements))
        self.assertTrue(set(claim.get("evidence_ids", [])).issubset(valid_evidence))
''',
)

L_BAD_NO_MIGRATION = _replace_json(
    L_GOOD_JSON,
    migration={"phases": [], "rollback": {}},
)
L_BAD_UI_TRUTH = _replace_json(
    L_GOOD_JSON,
    state_ownership=[
        {**item, **({"owner": "companion-ui"} if item["state_id"] == "job-intent" else {})}
        for item in L_GOOD_JSON["state_ownership"]
    ],
    failure_policies={**L_GOOD_JSON["failure_policies"], "ui-disconnect": "pause-until-ui-returns"},
)
L_BAD_CENTRAL_CREDENTIAL = _replace_json(
    L_GOOD_JSON,
    state_ownership=[
        {**item, **({"owner": "job-store"} if item["state_id"] == "credential-material" else {})}
        for item in L_GOOD_JSON["state_ownership"]
    ],
    security_controls=[
        {
            **item,
            **({"control": "central-unscoped-credential-record", "owner": "job-store"} if item["requirement_id"] == "SEC-credential-scope" else {}),
        }
        for item in L_GOOD_JSON["security_controls"]
    ],
)
L_BAD_UNBOUNDED_RETRY = _replace_json(
    L_GOOD_JSON,
    failure_policies={**L_GOOD_JSON["failure_policies"], "provider-loss": "retry-unbounded"},
)
L_BAD_THROUGHPUT_SELECTION = _replace_json(
    L_GOOD_JSON,
    alternatives=[
        {
            "option_id": item["id"],
            "disposition": "rejected-as-standalone",
            "decisive_evidence_id": "BEN-direct-start-latency",
            "counterexample": "nominal-throughput-preference",
        }
        for item in L_PROPOSALS["options"]
    ],
)
L_BAD_CLOSED_UNKNOWNS = _replace_json(
    L_GOOD_JSON,
    unknowns=[],
    claims=[
        *L_GOOD_JSON["claims"],
        {
            "id": "claim-exactly-once",
            "statement": "All provider operations are exactly-once and the backend is linearizable.",
            "requirement_ids": ["FUNC-at-least-once-bounded"],
            "evidence_ids": [],
        },
    ],
)


RECIPES: dict[str, dict[str, Any]] = {
    "f08-s-config-api-design-v1": {
        "case_id": "F08-S-MDJSON-001",
        "files": S_FILES,
        "hidden": S_HIDDEN,
        "good": {"decision.json": _json_file(S_GOOD_JSON), "DECISION.md": S_GOOD_MD},
        "executable": ["tools/validate_decision.py"],
        "mutants": {
            "builder-ignores-leak": {
                "files": {"decision.json": _json_file(S_BAD_BUILDER), "DECISION.md": S_MUTANT_MD},
                "expected_failed_check_ids": ["design-selected-contract"],
            },
            "pure-merge-without-deletion": {
                "files": {"decision.json": _json_file(S_BAD_NO_DELETE), "DECISION.md": S_MUTANT_MD},
                "expected_failed_check_ids": ["design-selected-contract"],
            },
            "pros-cons-without-counterexamples": {
                "files": {"decision.json": _json_file(S_BAD_NO_COUNTEREXAMPLES), "DECISION.md": S_MUTANT_MD},
                "expected_failed_check_ids": ["design-counterexamples"],
            },
            "invented-performance-claim": {
                "files": {"decision.json": _json_file(S_BAD_PERFORMANCE), "DECISION.md": S_MUTANT_MD},
                "expected_failed_check_ids": ["design-evidence-entailment"],
            },
        },
    },
    "f08-m-job-responsibility-design-v1": {
        "case_id": "F08-M-MDJSON-001",
        "files": M_FILES,
        "hidden": M_HIDDEN,
        "good": {"proposal.json": _json_file(M_GOOD_JSON), "PROPOSAL.md": M_GOOD_MD},
        "executable": ["simulator.py", "tools/validate_proposal.py"],
        "mutants": {
            "retry-owner-conflict": {
                "files": {"proposal.json": _json_file(M_BAD_RETRY_CONFLICT), "PROPOSAL.md": M_GOOD_MD},
                "expected_failed_check_ids": ["design-state-ownership"],
            },
            "cancellation-in-memory": {
                "files": {"proposal.json": _json_file(M_BAD_CANCEL_MEMORY), "PROPOSAL.md": M_GOOD_MD},
                "expected_failed_check_ids": ["design-state-ownership"],
            },
            "diagram-without-transitions": {
                "files": {"proposal.json": _json_file(M_BAD_NO_TRANSITIONS), "PROPOSAL.md": M_GOOD_MD},
                "expected_failed_check_ids": ["design-failure-transitions"],
            },
            "unsupported-exactly-once": {
                "files": {"proposal.json": _json_file(M_BAD_EXACTLY_ONCE), "PROPOSAL.md": M_GOOD_MD},
                "expected_failed_check_ids": ["design-unknown-honesty"],
            },
            "preference-only-rejections": {
                "files": {"proposal.json": _json_file(M_BAD_PREFERENCE_REJECTIONS), "PROPOSAL.md": M_GOOD_MD},
                "expected_failed_check_ids": ["design-option-counterexamples"],
            },
        },
    },
    "f08-l-execution-fabric-design-v1": {
        "case_id": "F08-L-MDJSON-001",
        "files": L_FILES,
        "hidden": L_HIDDEN,
        "good": {"design.json": _json_file(L_GOOD_JSON), "DESIGN.md": L_GOOD_MD},
        "executable": [
            "simulator.py",
            "tools/validate_design.py",
            "tools/replay_migration.py",
            "tools/replay_migration.sh",
        ],
        "mutants": {
            "no-migration-rollback": {
                "files": {"design.json": _json_file(L_BAD_NO_MIGRATION), "DESIGN.md": L_GOOD_MD},
                "expected_failed_check_ids": ["design-migration-rollback"],
            },
            "ui-source-of-truth": {
                "files": {"design.json": _json_file(L_BAD_UI_TRUTH), "DESIGN.md": L_GOOD_MD},
                "expected_failed_check_ids": ["design-topology-ownership", "design-failure-recovery"],
            },
            "central-unscoped-credentials": {
                "files": {"design.json": _json_file(L_BAD_CENTRAL_CREDENTIAL), "DESIGN.md": L_GOOD_MD},
                "expected_failed_check_ids": ["design-topology-ownership", "design-security-boundaries"],
            },
            "unbounded-provider-retry": {
                "files": {"design.json": _json_file(L_BAD_UNBOUNDED_RETRY), "DESIGN.md": L_GOOD_MD},
                "expected_failed_check_ids": ["design-failure-recovery"],
            },
            "throughput-over-incidents": {
                "files": {"design.json": _json_file(L_BAD_THROUGHPUT_SELECTION), "DESIGN.md": L_GOOD_MD},
                "expected_failed_check_ids": ["design-alternative-counterexamples"],
            },
            "closed-provider-unknowns": {
                "files": {"design.json": _json_file(L_BAD_CLOSED_UNKNOWNS), "DESIGN.md": L_GOOD_MD},
                "expected_failed_check_ids": ["design-unknown-honesty"],
            },
        },
    },
}
