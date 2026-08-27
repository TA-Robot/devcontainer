"""Deterministic evidence-synthesis duration-study fixtures."""

from __future__ import annotations

import copy
import hashlib
import json
from statistics import median
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
        testcase.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), expected)
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
    testcase.assertTrue(changed.issubset(set(ALLOWED_ARTIFACTS)), sorted(changed))

'''
    return support + body


def _render_ledger(title: str, claims: list[dict[str, Any]], id_key: str = "input_id") -> str:
    lines = [
        f"# {title}",
        "",
        "The following ledger is the evidence-bounded synthesis. Narrative wording does not change its dispositions.",
        "",
        f"| {id_key} | disposition | canonical_claim | evidence | confidence |",
        "| --- | --- | --- | --- | --- |",
    ]
    for claim in claims:
        evidence = ",".join(claim.get("evidence", [])) or "-"
        lines.append(
            f"| {claim[id_key]} | {claim['disposition']} | {claim['canonical_claim']} | {evidence} | {claim.get('confidence', 'not-applicable')} |"
        )
    lines.append("")
    return "\n".join(lines)


S_VALIDATE = r'''#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
import sys


def table_rows(text: str) -> list[tuple[str, str, str, tuple[str, ...], str]]:
    rows = []
    for line in text.splitlines():
        if not line.startswith("| ") or line.startswith("| ---") or "input_id" in line:
            continue
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if len(cells) != 5:
            continue
        evidence = tuple() if cells[3] == "-" else tuple(cells[3].split(","))
        rows.append((cells[0], cells[1], cells[2], evidence, cells[4]))
    return rows


def main() -> int:
    if len(sys.argv) != 3:
        return 2
    try:
        value = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
        markdown = Path(sys.argv[2]).read_text(encoding="utf-8")
    except (OSError, json.JSONDecodeError):
        return 1
    if not isinstance(value, dict) or value.get("version") != 1:
        return 1
    claims = value.get("claims")
    if not isinstance(claims, list) or not claims:
        return 1
    required = {"input_id", "reviewer", "disposition", "canonical_claim", "evidence", "confidence", "note"}
    if any(not isinstance(item, dict) or not required.issubset(item) for item in claims):
        return 1
    structured = [
        (item["input_id"], item["disposition"], item["canonical_claim"], tuple(item["evidence"]), item["confidence"])
        for item in claims
    ]
    if table_rows(markdown) != structured:
        return 1
    if not isinstance(value.get("unknowns"), list) or not isinstance(value.get("recommendations"), list):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
'''


S_FILES = {
    "AGENTS.md": AGENT_INSTRUCTIONS,
    "analysis-a.md": r'''# Analysis A

- CLAIM A1: The wrapper forwards every argv item unchanged. Evidence: SRC-ARGV.
- CLAIM A2: `ALLOW_OUTSIDE=1` is active by default. Evidence: SRC-ENV.
- CLAIM A3: The wrapper logs the full command before execution. Evidence: SRC-INVOKE.
''',
    "analysis-b.md": r'''# Analysis B

- CLAIM B1: Backend argv forwarding is preserved. Evidence: SRC-ARGV.
- CLAIM B2: The wrapper always ignores `ALLOW_OUTSIDE`. Evidence: SRC-ENV.
- CLAIM B3: Environment values are redacted from wrapper logs. Evidence: SRC-INVOKE.
''',
    "sources/SRC-ARGV.txt": "EVIDENCE SRC-ARGV\nexec backend-command \"$@\"\n",
    "sources/SRC-ENV.txt": "EVIDENCE SRC-ENV\nif [[ -n \"${ALLOW_OUTSIDE:-}\" ]]; then flags+=(--allow-outside); fi\n",
    "sources/SRC-INVOKE.txt": "EVIDENCE SRC-INVOKE\nbackend-command is invoked directly; this snippet contains no logging behavior.\n",
    "tools/validate_synthesis.py": S_VALIDATE,
}


S_GOOD_CLAIMS: list[dict[str, Any]] = [
    {
        "input_id": "A1",
        "reviewer": "A",
        "disposition": "supported",
        "canonical_claim": "argv-forwarded",
        "evidence": ["SRC-ARGV"],
        "confidence": "high",
        "note": "The exec form forwards the argument vector.",
    },
    {
        "input_id": "A2",
        "reviewer": "A",
        "disposition": "corrected",
        "canonical_claim": "override-conditional-on-explicit-nonempty-env",
        "evidence": ["SRC-ENV"],
        "confidence": "high",
        "note": "The default-active blanket claim is contradicted by the branch condition.",
    },
    {
        "input_id": "A3",
        "reviewer": "A",
        "disposition": "unsupported",
        "canonical_claim": "logging-unknown",
        "evidence": [],
        "confidence": "unknown",
        "note": "Supplied snippets contain no logging evidence.",
    },
    {
        "input_id": "B1",
        "reviewer": "B",
        "disposition": "supported",
        "canonical_claim": "argv-forwarded",
        "evidence": ["SRC-ARGV"],
        "confidence": "high",
        "note": "This duplicates A1 with separate provenance.",
    },
    {
        "input_id": "B2",
        "reviewer": "B",
        "disposition": "corrected",
        "canonical_claim": "override-conditional-on-explicit-nonempty-env",
        "evidence": ["SRC-ENV"],
        "confidence": "high",
        "note": "The always-ignored blanket claim is contradicted by the branch condition.",
    },
    {
        "input_id": "B3",
        "reviewer": "B",
        "disposition": "unsupported",
        "canonical_claim": "logging-unknown",
        "evidence": [],
        "confidence": "unknown",
        "note": "Redaction behavior is not present in supplied evidence.",
    },
]


S_GOOD = {
    "version": 1,
    "claims": S_GOOD_CLAIMS,
    "unknowns": ["wrapper logging behavior"],
    "recommendations": [],
}
S_GOOD_MD = _render_ledger("Wrapper evidence synthesis", S_GOOD_CLAIMS)


S_HIDDEN_BODY = r'''def synthesis() -> dict[str, object]:
    try:
        value = json.loads((WORKSPACE / "synthesis.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return value if isinstance(value, dict) else {}


def claims() -> dict[str, dict[str, object]]:
    return {item.get("input_id"): item for item in synthesis().get("claims", []) if isinstance(item, dict)}


class HiddenWrapperSynthesisTests(unittest.TestCase):
    def setUp(self):
        assert_fixture_integrity(self)

    def test_claim_coverage(self):
        self.assertEqual(set(claims()), {"A1", "A2", "A3", "B1", "B2", "B3"})
        self.assertEqual({item.get("reviewer") for item in claims().values()}, {"A", "B"})

    def test_agreement(self):
        for claim_id in ("A1", "B1"):
            item = claims()[claim_id]
            self.assertEqual(item.get("disposition"), "supported")
            canonical = str(item.get("canonical_claim", "")).lower()
            self.assertIn("argv", canonical)
            self.assertIn("forward", canonical)
            self.assertEqual(item.get("evidence"), ["SRC-ARGV"])
        source = (WORKSPACE / "sources/SRC-ARGV.txt").read_text(encoding="utf-8")
        self.assertIn('exec backend-command "$@"', source)

    def test_conflict_adjudication(self):
        for claim_id in ("A2", "B2"):
            item = claims()[claim_id]
            self.assertEqual(item.get("disposition"), "corrected")
            canonical = str(item.get("canonical_claim", ""))
            self.assertIn("conditional", canonical)
            self.assertIn("explicit", canonical)
            self.assertEqual(item.get("evidence"), ["SRC-ENV"])
        source = (WORKSPACE / "sources/SRC-ENV.txt").read_text(encoding="utf-8")
        self.assertIn('${ALLOW_OUTSIDE:-}', source)
        self.assertIn("-n", source)

    def test_unsupported(self):
        for claim_id in ("A3", "B3"):
            item = claims()[claim_id]
            self.assertEqual(item.get("disposition"), "unsupported")
            self.assertEqual(item.get("evidence"), [])
            self.assertEqual(item.get("confidence"), "unknown")
        self.assertIn("wrapper logging behavior", synthesis().get("unknowns", []))
        self.assertEqual(synthesis().get("recommendations"), [])

    def test_doc_json_sync(self):
        completed = subprocess.run(
            ["python3", "tools/validate_synthesis.py", "synthesis.json", "SYNTHESIS.md"],
            cwd=WORKSPACE,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=8,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)


if __name__ == "__main__":
    unittest.main()
'''


S_HIDDEN = _hidden_with_integrity(
    S_HIDDEN_BODY,
    S_FILES,
    {"SYNTHESIS.md", "synthesis.json"},
)


S_MUTANT_A_WHOLESALE = copy.deepcopy(S_GOOD)
for _s_item in S_MUTANT_A_WHOLESALE["claims"]:
    if _s_item["input_id"] == "A2":
        _s_item["disposition"] = "supported"
        _s_item["canonical_claim"] = "override-active-by-default"
    if _s_item["input_id"] == "B2":
        _s_item["disposition"] = "rejected"

S_MUTANT_VAGUE = copy.deepcopy(S_GOOD)
for _s_item in S_MUTANT_VAGUE["claims"]:
    if _s_item["input_id"] in {"A2", "B2"}:
        _s_item["canonical_claim"] = "override-may-be-active"

S_MUTANT_LOGGING = copy.deepcopy(S_GOOD)
for _s_item in S_MUTANT_LOGGING["claims"]:
    if _s_item["input_id"] in {"A3", "B3"}:
        _s_item["disposition"] = "supported"
        _s_item["canonical_claim"] = "logging-redacts-environment"
        _s_item["evidence"] = ["SRC-INVOKE"]

S_MUTANT_RECOMMENDATION = copy.deepcopy(S_GOOD)
S_MUTANT_RECOMMENDATION["recommendations"] = ["migrate immediately to a different wrapper"]


M_PATH_GUARD = r'''from __future__ import annotations

from pathlib import Path
from typing import Callable


def authorize_path(
    root: Path,
    candidate: Path,
    interleave: Callable[[], None] | None = None,
) -> Path:
    resolved = candidate.resolve()
    try:
        resolved.relative_to(root.resolve())
    except ValueError as exc:
        raise PermissionError("candidate escapes root") from exc
    if interleave is not None:
        interleave()
    return candidate.resolve()
'''


M_REPLAY = r'''from __future__ import annotations

import json
from pathlib import Path
import shutil
import tempfile

from sources.path_guard import authorize_path


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="f12-race-") as raw:
        root = Path(raw)
        workspace = root / "workspace"
        safe = workspace / "candidate"
        outside = root / "outside"
        workspace.mkdir()
        safe.mkdir()
        outside.mkdir()

        def swap() -> None:
            shutil.rmtree(safe)
            safe.symlink_to(outside, target_is_directory=True)

        selected = authorize_path(workspace, safe, swap)
        result = {
            "evidence_id": "EXPLOIT-LINUX-RACE",
            "post_check_target_outside": selected == outside.resolve(),
            "platform": "linux-fixture",
        }
        print(json.dumps(result, sort_keys=True))
        return 0 if result["post_check_target_outside"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
'''


M_VALIDATE = r'''#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
import sys


def rows(text: str) -> list[tuple[str, str, tuple[str, ...], tuple[str, ...], str]]:
    result = []
    for line in text.splitlines():
        if not line.startswith("| ") or line.startswith("| ---") or "claim_id" in line:
            continue
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if len(cells) != 5:
            continue
        result.append((cells[0], cells[1], tuple(cells[2].split(",")), tuple() if cells[3] == "-" else tuple(cells[3].split(",")), cells[4]))
    return result


def main() -> int:
    if len(sys.argv) != 3:
        return 2
    try:
        value = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
        markdown = Path(sys.argv[2]).read_text(encoding="utf-8")
    except (OSError, json.JSONDecodeError):
        return 1
    if not isinstance(value, dict) or value.get("version") != 1:
        return 1
    claims = value.get("claims")
    if not isinstance(claims, list) or not claims:
        return 1
    required = {"claim_id", "canonical_claim", "input_claim_ids", "reviewers", "disposition", "evidence", "confidence", "statement", "missing_evidence"}
    if any(not isinstance(item, dict) or not required.issubset(item) for item in claims):
        return 1
    structured = [
        (item["claim_id"], item["disposition"], tuple(item["input_claim_ids"]), tuple(item["evidence"]), item["confidence"])
        for item in claims
    ]
    if rows(markdown) != structured:
        return 1
    if not isinstance(value.get("decision_boundary"), dict):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
'''


M_FILES = {
    "AGENTS.md": AGENT_INSTRUCTIONS,
    "reviews/review-a.md": r'''# Review A

- CLAIM A-RACE: The post-check symlink race remains exploitable. Evidence: EXPLOIT-LINUX-RACE.
- CLAIM A-CREDENTIAL: The escape grants critical provider credential access. Evidence: SOURCE-NO-CREDENTIAL.
''',
    "reviews/review-b.md": r'''# Review B

- CLAIM B-FIX: Canonicalization fully fixes all symlink races. Evidence: DIFF-CANONICALIZE.
''',
    "reviews/review-c.md": r'''# Review C

- CLAIM C-RACE: A path swap after the containment check still escapes. Evidence: EXPLOIT-LINUX-RACE.
- CLAIM C-JUNCTION: Windows junctions remain vulnerable. Evidence: NO-WINDOWS-EVIDENCE.
''',
    "change.diff": r'''diff --git a/path_guard.py b/path_guard.py
+ resolved = candidate.resolve()
+ resolved.relative_to(root.resolve())
  # candidate is used again after this check
''',
    "evidence/tests.json": _document(
        {
            "evidence_id": "TEST-MATRIX",
            "platform": "linux-fixture",
            "public_descendant": "pass",
            "preexisting_external_symlink": "rejected",
            "post_check_swap": "fail",
            "windows_junction": "not-run",
        }
    ),
    "evidence/index.json": _document(
        {
            "EXPLOIT-LINUX-RACE": "evidence/exploit.sh",
            "DIFF-CANONICALIZE": "change.diff",
            "TEST-MATRIX": "evidence/tests.json",
            "SOURCE-GUARD": "sources/path_guard.py",
            "SOURCE-NO-CREDENTIAL": "sources/credential_boundary.txt",
            "NO-WINDOWS-EVIDENCE": "evidence/tests.json#windows_junction:not-run",
        }
    ),
    "evidence/exploit.sh": r'''#!/usr/bin/env bash
set -euo pipefail
exec python3 sources/replay_exploit.py
''',
    "sources/__init__.py": "",
    "sources/path_guard.py": M_PATH_GUARD,
    "sources/replay_exploit.py": M_REPLAY,
    "sources/credential_boundary.txt": "EVIDENCE SOURCE-NO-CREDENTIAL\nThe path fixture mounts no credentials and models workspace paths only.\n",
    "tools/validate_adjudication.py": M_VALIDATE,
}


M_GOOD_CLAIMS: list[dict[str, Any]] = [
    {
        "claim_id": "race-present",
        "canonical_claim": "post-check path replacement escapes the Linux fixture root",
        "input_claim_ids": ["A-RACE", "C-RACE"],
        "reviewers": ["A", "C"],
        "disposition": "accepted",
        "evidence": ["EXPLOIT-LINUX-RACE", "SOURCE-GUARD", "TEST-MATRIX"],
        "confidence": "high",
        "statement": "The deterministic replay reaches an outside target after the earlier containment check.",
        "missing_evidence": [],
    },
    {
        "claim_id": "canonicalization-sufficient",
        "canonical_claim": "canonicalization alone closes all symlink races",
        "input_claim_ids": ["B-FIX"],
        "reviewers": ["B"],
        "disposition": "rejected",
        "evidence": ["DIFF-CANONICALIZE", "EXPLOIT-LINUX-RACE"],
        "confidence": "high",
        "statement": "The replay contradicts sufficiency because the candidate is swapped after the check.",
        "missing_evidence": [],
    },
    {
        "claim_id": "windows-junction",
        "canonical_claim": "Windows junction behavior under the patch",
        "input_claim_ids": ["C-JUNCTION"],
        "reviewers": ["C"],
        "disposition": "unknown",
        "evidence": ["NO-WINDOWS-EVIDENCE"],
        "confidence": "unknown",
        "statement": "The Linux-only fixture cannot adjudicate junction semantics.",
        "missing_evidence": ["Windows junction replay on a declared filesystem/runtime identity"],
    },
    {
        "claim_id": "credential-impact",
        "canonical_claim": "demonstrated impact is a workspace path escape without credential access evidence",
        "input_claim_ids": ["A-CREDENTIAL"],
        "reviewers": ["A"],
        "disposition": "narrowed",
        "evidence": ["EXPLOIT-LINUX-RACE", "SOURCE-NO-CREDENTIAL"],
        "confidence": "high",
        "statement": "The fixture proves path escape only and mounts no credentials.",
        "missing_evidence": [],
    },
]


def _render_m(claims: list[dict[str, Any]]) -> str:
    lines = [
        "# Isolation review adjudication",
        "",
        "| claim_id | disposition | input_claim_ids | evidence | confidence |",
        "| --- | --- | --- | --- | --- |",
    ]
    for item in claims:
        lines.append(
            f"| {item['claim_id']} | {item['disposition']} | {','.join(item['input_claim_ids'])} | {','.join(item['evidence']) or '-'} | {item['confidence']} |"
        )
    lines.extend(["", "Statements and missing-evidence boundaries are authoritative in `adjudication.json`.", ""])
    return "\n".join(lines)


M_GOOD = {
    "version": 1,
    "claims": M_GOOD_CLAIMS,
    "decision_boundary": {
        "platform": "linux-fixture",
        "supported_impact": "workspace path escape",
        "excluded_impact": "provider credential access",
        "unresolved": ["Windows junction semantics"],
    },
}
M_GOOD_MD = _render_m(M_GOOD_CLAIMS)


M_HIDDEN_BODY = r'''def adjudication() -> dict[str, object]:
    try:
        value = json.loads((WORKSPACE / "adjudication.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return value if isinstance(value, dict) else {}


def claims() -> dict[str, dict[str, object]]:
    return {item.get("claim_id"): item for item in adjudication().get("claims", []) if isinstance(item, dict)}


def claim_with_inputs(*input_ids: str) -> dict[str, object]:
    expected = set(input_ids)
    matches = [item for item in claims().values() if set(item.get("input_claim_ids", [])) == expected]
    if len(matches) != 1:
        raise AssertionError(f"expected one merged claim for {sorted(expected)}")
    return matches[0]


def exploit() -> dict[str, object]:
    completed = subprocess.run(
        ["bash", "evidence/exploit.sh"],
        cwd=WORKSPACE,
        env={"PATH": os.environ.get("PATH", "/usr/local/bin:/usr/bin:/bin"), "PYTHONPATH": str(WORKSPACE), "PYTHONDONTWRITEBYTECODE": "1"},
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=10,
        check=False,
    )
    if completed.returncode != 0:
        raise AssertionError(completed.stdout + completed.stderr)
    return json.loads(completed.stdout)


class HiddenAdjudicationTests(unittest.TestCase):
    def setUp(self):
        assert_fixture_integrity(self)

    def test_provenance(self):
        items = claims()
        self.assertEqual(len(items), 4)
        provenance = {claim for item in items.values() for claim in item.get("input_claim_ids", [])}
        self.assertEqual(provenance, {"A-RACE", "A-CREDENTIAL", "B-FIX", "C-RACE", "C-JUNCTION"})
        race = claim_with_inputs("A-RACE", "C-RACE")
        self.assertEqual(race.get("reviewers"), ["A", "C"])

    def test_race_accepted(self):
        item = claim_with_inputs("A-RACE", "C-RACE")
        self.assertEqual(item.get("disposition"), "accepted")
        self.assertIn("EXPLOIT-LINUX-RACE", item.get("evidence", []))
        self.assertIs(exploit().get("post_check_target_outside"), True)

    def test_fix_refuted(self):
        item = claim_with_inputs("B-FIX")
        self.assertEqual(item.get("disposition"), "rejected")
        self.assertEqual(set(item.get("evidence", [])), {"DIFF-CANONICALIZE", "EXPLOIT-LINUX-RACE"})
        self.assertIn("after the check", str(item.get("statement", "")))

    def test_platform_unknown(self):
        item = claim_with_inputs("C-JUNCTION")
        self.assertEqual(item.get("disposition"), "unknown")
        self.assertEqual(item.get("confidence"), "unknown")
        self.assertEqual(item.get("evidence"), ["NO-WINDOWS-EVIDENCE"])
        missing = " ".join(item.get("missing_evidence", [])).lower()
        self.assertIn("windows", missing)
        self.assertIn("junction", missing)
        self.assertTrue(any(term in missing for term in ("test", "replay", "runtime", "filesystem")))

    def test_severity_narrowed(self):
        item = claim_with_inputs("A-CREDENTIAL")
        self.assertEqual(item.get("disposition"), "narrowed")
        self.assertIn("workspace path escape", item.get("canonical_claim", ""))
        self.assertIn("without credential access", item.get("canonical_claim", ""))
        boundary = adjudication().get("decision_boundary", {})
        supported = str(boundary.get("supported_impact", "")).lower()
        excluded = str(boundary.get("excluded_impact", "")).lower()
        self.assertTrue(all(term in supported for term in ("workspace", "path", "escape")))
        self.assertTrue(all(term in excluded for term in ("credential", "access")))

    def test_entailment(self):
        evidence_index = json.loads((WORKSPACE / "evidence/index.json").read_text(encoding="utf-8"))
        for item in claims().values():
            for evidence_id in item.get("evidence", []):
                self.assertIn(evidence_id, evidence_index)
            if item.get("disposition") == "unknown":
                self.assertTrue(item.get("missing_evidence"))
            else:
                self.assertTrue(item.get("evidence"))

    def test_doc_json_sync(self):
        completed = subprocess.run(
            ["python3", "tools/validate_adjudication.py", "adjudication.json", "ADJUDICATION.md"],
            cwd=WORKSPACE,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=8,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)


if __name__ == "__main__":
    unittest.main()
'''


M_HIDDEN = _hidden_with_integrity(
    M_HIDDEN_BODY,
    M_FILES,
    {"ADJUDICATION.md", "adjudication.json"},
)


M_MUTANT_MAJORITY = copy.deepcopy(M_GOOD)
for _m_item in M_MUTANT_MAJORITY["claims"]:
    if _m_item["claim_id"] == "canonicalization-sufficient":
        _m_item["disposition"] = "accepted"

M_MUTANT_WINDOWS = copy.deepcopy(M_GOOD)
for _m_item in M_MUTANT_WINDOWS["claims"]:
    if _m_item["claim_id"] == "windows-junction":
        _m_item["disposition"] = "accepted"
        _m_item["confidence"] = "high"
        _m_item["missing_evidence"] = []

M_MUTANT_NO_PROVENANCE = copy.deepcopy(M_GOOD)
for _m_item in M_MUTANT_NO_PROVENANCE["claims"]:
    _m_item["input_claim_ids"] = [_m_item["input_claim_ids"][0]]
    _m_item["reviewers"] = [_m_item["reviewers"][0]]

M_MUTANT_CRITICAL = copy.deepcopy(M_GOOD)
for _m_item in M_MUTANT_CRITICAL["claims"]:
    if _m_item["claim_id"] == "credential-impact":
        _m_item["disposition"] = "accepted"
        _m_item["canonical_claim"] = "critical provider credential access"
M_MUTANT_CRITICAL["decision_boundary"]["supported_impact"] = "critical provider credential access"

M_MUTANT_NO_EVIDENCE = copy.deepcopy(M_GOOD)
for _m_item in M_MUTANT_NO_EVIDENCE["claims"]:
    _m_item["evidence"] = []


L_BENCHMARKS = {
    "series": [
        {"evidence_id": "BM-A-WARM", "proposal": "A", "workload": "warm", "samples_ms": [40, 42, 38], "censored": 0, "valid": True},
        {"evidence_id": "BM-A-COLD", "proposal": "A", "workload": "cold", "samples_ms": [180, 220, 200], "censored": 1, "valid": True},
        {"evidence_id": "BM-B-WARM", "proposal": "B", "workload": "warm", "samples_ms": [70, 72, 68], "censored": 0, "valid": True},
        {"evidence_id": "BM-B-COLD", "proposal": "B", "workload": "cold", "samples_ms": [90, 95, 100], "censored": 0, "valid": True},
        {"evidence_id": "BM-C-POOLED", "proposal": "C", "workload": "pooled-warm-cold", "samples_ms": [30, 300, 32, 290], "censored": 0, "valid": False, "exclusion_reason": "workload-mixed samples cannot support one throughput distribution"},
        {"evidence_id": "BM-D-WARM", "proposal": "D", "workload": "warm", "samples_ms": [85, 80, 90], "censored": 0, "valid": True},
        {"evidence_id": "BM-D-COLD", "proposal": "D", "workload": "cold", "samples_ms": [120, 125, 130], "censored": 0, "valid": True},
    ]
}


L_EVIDENCE_INDEX = {
    "BM-A-WARM": "evidence/benchmarks/raw.json#BM-A-WARM",
    "BM-A-COLD": "evidence/benchmarks/raw.json#BM-A-COLD",
    "BM-B-WARM": "evidence/benchmarks/raw.json#BM-B-WARM",
    "BM-B-COLD": "evidence/benchmarks/raw.json#BM-B-COLD",
    "BM-C-POOLED": "evidence/benchmarks/raw.json#BM-C-POOLED",
    "BM-D-WARM": "evidence/benchmarks/raw.json#BM-D-WARM",
    "BM-D-COLD": "evidence/benchmarks/raw.json#BM-D-COLD",
    "INC-A-CLEANUP": "evidence/incidents/incidents.json#INC-A-CLEANUP",
    "INC-D-RECOVERY": "evidence/incidents/incidents.json#INC-D-RECOVERY",
    "SEC-B-ISOLATION": "evidence/security/findings.json#SEC-B-ISOLATION",
    "SEC-A-BIND": "evidence/security/findings.json#SEC-A-BIND",
    "CON-MIGRATION": "constraints.json#CON-MIGRATION",
    "CON-OWNER": "constraints.json#CON-OWNER",
    "CON-ROLLBACK": "constraints.json#CON-ROLLBACK",
    "PROP-A": "proposals/A.md",
    "PROP-B": "proposals/B.md",
    "PROP-C": "proposals/C.md",
    "PROP-D": "proposals/D.md",
}


L_DECISION_CONTRACT_VALUE = {
    "schema_version": 2,
    "artifact": "decision-record.json",
    "claim_ids": [
        "A-WARM",
        "A-COLD",
        "B-ISOLATION",
        "B-MIGRATION",
        "C-THROUGHPUT",
        "D-MIGRATION",
        "D-RECOVERY",
        "CON-MIGRATION",
        "CON-OWNER",
        "CON-ROLLBACK",
    ],
    "proposal_options": ["A", "B", "C", "D"],
    "constraint_ids": ["CON-MIGRATION", "CON-OWNER", "CON-ROLLBACK"],
    "constraint_status_values": ["satisfied-by-stage-1", "gated"],
    "confidence_values": ["high", "medium", "low", "unknown"],
    "refresh_categories": ["identity", "window", "incident"],
    "required_claim_outcomes": {
        "D-RECOVERY": {
            "disposition": "unknown",
            "confidence": "unknown",
            "required_evidence": ["INC-D-RECOVERY"],
        }
    },
    "claim_condition_terms": {"A-WARM": "warm", "A-COLD": "cold"},
    "alternative_minimum_evidence": {
        "A": ["BM-A-COLD", "INC-A-CLEANUP"],
        "B": ["SEC-B-ISOLATION", "CON-MIGRATION"],
        "C": ["BM-C-POOLED"],
        "D": ["PROP-D", "INC-D-RECOVERY", "CON-OWNER"],
    },
    "decision_space": {
        "migration_bridge_option": "D",
        "permitted_target_options": ["A", "B"],
        "forbidden_selected_options": ["C"],
        "target_evidence": {
            "A": ["A-WARM", "A-COLD", "INC-A-CLEANUP", "SEC-A-BIND"],
            "B": ["B-ISOLATION", "SEC-B-ISOLATION"],
        },
    },
    "semantic_requirements": {
        "control_ids_are_author_chosen": True,
        "unknown_ids_are_author_chosen": True,
        "trigger_ids_are_author_chosen": True,
        "all_proposals_must_be_assessed": True,
        "selected_target_must_follow_the_migration_bridge": True,
    },
}

L_DECISION_CONTRACT = _document(L_DECISION_CONTRACT_VALUE)


L_VALIDATE = r'''#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
import re
import sys


DECISION = re.compile(r"<!-- decision-summary\s*(\{.*?\})\s*-->", re.DOTALL)


def rows(text: str) -> list[tuple[str, str, tuple[str, ...], str, str]]:
    result = []
    for line in text.splitlines():
        if not line.startswith("| ") or line.startswith("| ---") or "claim_id" in line:
            continue
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if len(cells) != 5:
            continue
        result.append((cells[0], cells[1], tuple() if cells[2] == "-" else tuple(cells[2].split(",")), cells[3], cells[4]))
    return result


def main() -> int:
    if len(sys.argv) != 3:
        return 2
    try:
        value = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
        markdown = Path(sys.argv[2]).read_text(encoding="utf-8")
        contract = json.loads(Path("decision-contract.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return 1
    if not isinstance(value, dict) or value.get("version") != 1:
        return 1
    claims = value.get("claims")
    if not isinstance(claims, list) or not claims:
        return 1
    required = {"claim_id", "provenance", "disposition", "evidence", "condition", "confidence"}
    if any(not isinstance(item, dict) or not required.issubset(item) for item in claims):
        return 1
    if {item.get("claim_id") for item in claims} != set(contract["claim_ids"]):
        return 1
    structured = [(item["claim_id"], item["disposition"], tuple(item["evidence"]), item["condition"], item["confidence"]) for item in claims]
    if rows(markdown) != structured:
        return 1
    match = DECISION.search(markdown)
    if match is None:
        return 1
    try:
        summary = json.loads(match.group(1))
    except json.JSONDecodeError:
        return 1
    decision = value.get("decision")
    if not isinstance(decision, dict):
        return 1
    expected = {
        "strategy": decision.get("strategy"),
        "phase_options": [phase.get("option") for phase in decision.get("phases", [])],
        "unknown_ids": [item.get("unknown_id") for item in value.get("unknowns", [])],
    }
    if summary != expected:
        return 1
    for key in ("metrics", "alternatives", "constraint_matrix", "unknowns", "refresh_plan"):
        if not isinstance(value.get(key), list):
            return 1
    phases = decision.get("phases", [])
    phase_options = [item.get("option") for item in phases if isinstance(item, dict)]
    decision_space = contract["decision_space"]
    if len(phase_options) < 2 or phase_options[0] != decision_space["migration_bridge_option"]:
        return 1
    if phase_options[-1] not in decision_space["permitted_target_options"]:
        return 1
    if any(item not in contract["proposal_options"] for item in phase_options):
        return 1
    if {item.get("option") for item in value["alternatives"] if isinstance(item, dict)} != set(contract["proposal_options"]):
        return 1
    if {item.get("constraint_id") for item in value["constraint_matrix"] if isinstance(item, dict)} != set(contract["constraint_ids"]):
        return 1
    if any(item.get("status") not in contract["constraint_status_values"] for item in value["constraint_matrix"] if isinstance(item, dict)):
        return 1
    alternatives = {item.get("option"): item for item in value["alternatives"] if isinstance(item, dict)}
    for option, required_evidence in contract["alternative_minimum_evidence"].items():
        if not set(required_evidence).issubset(set(alternatives[option].get("evidence", []))):
            return 1
    claims_by_id = {item.get("claim_id"): item for item in claims if isinstance(item, dict)}
    if any(item.get("confidence") not in contract["confidence_values"] for item in claims_by_id.values()):
        return 1
    for claim_id, requirement in contract["required_claim_outcomes"].items():
        claim = claims_by_id[claim_id]
        if claim.get("disposition") != requirement["disposition"] or claim.get("confidence") != requirement["confidence"]:
            return 1
        if not set(requirement["required_evidence"]).issubset(set(claim.get("evidence", []))):
            return 1
    for claim_id, term in contract["claim_condition_terms"].items():
        if term not in str(claims_by_id[claim_id].get("condition", "")).lower():
            return 1
    if {item.get("category") for item in value["refresh_plan"] if isinstance(item, dict)} != set(contract["refresh_categories"]):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
'''


L_RECOMPUTE = r'''#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
from statistics import median
import sys


def main() -> int:
    if len(sys.argv) != 3:
        return 2
    try:
        raw = json.loads((Path(sys.argv[1]) / "raw.json").read_text(encoding="utf-8"))
        record = json.loads(Path(sys.argv[2]).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return 1
    declared = {item.get("evidence_id"): item for item in record.get("metrics", []) if isinstance(item, dict)}
    series = raw.get("series", [])
    if set(declared) != {item.get("evidence_id") for item in series if isinstance(item, dict)}:
        return 1
    for item in series:
        observed = declared[item["evidence_id"]]
        if observed.get("proposal") != item["proposal"] or observed.get("workload") != item["workload"]:
            return 1
        if observed.get("sample_count") != len(item["samples_ms"]) or observed.get("censored") != item["censored"] or observed.get("valid") is not item["valid"]:
            return 1
        expected_median = median(item["samples_ms"]) if item["valid"] else None
        if observed.get("median_ms") != expected_median:
            return 1
        if not item["valid"] and observed.get("exclusion_reason") != item.get("exclusion_reason"):
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
'''


L_ENTAILMENT = r'''#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
import sys


def main() -> int:
    if len(sys.argv) != 2:
        return 2
    try:
        record = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
        evidence = json.loads(Path("evidence/index.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return 1
    claims = {item.get("claim_id"): item for item in record.get("claims", []) if isinstance(item, dict)}
    if not claims:
        return 1
    for item in claims.values():
        if any(evidence_id not in evidence for evidence_id in item.get("evidence", [])):
            return 1
        if item.get("disposition") == "unknown":
            if not item.get("missing_evidence"):
                return 1
        elif not item.get("evidence"):
            return 1
    decision = record.get("decision", {})
    dependencies = decision.get("depends_on", [])
    if not isinstance(dependencies, list) or any(item not in claims for item in dependencies):
        return 1
    phases = decision.get("phases", [])
    if not isinstance(phases, list) or not phases:
        return 1
    for phase in phases:
        if not phase.get("owner") or not phase.get("gates") or not phase.get("rollback_triggers"):
            return 1
    for alternative in record.get("alternatives", []):
        if any(item not in evidence for item in alternative.get("evidence", [])):
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
'''


L_FILES = {
    "AGENTS.md": AGENT_INSTRUCTIONS,
    "decision-contract.json": L_DECISION_CONTRACT,
    "proposals/A.md": "# Proposal A\n\nCLAIM A-WARM: lowest warm median. CLAIM A-COLD: acceptable cold behavior. Evidence BM-A-WARM, BM-A-COLD.\n",
    "proposals/B.md": "# Proposal B\n\nCLAIM B-ISOLATION: strongest supplied isolation. CLAIM B-MIGRATION: immediate migration is feasible. Evidence SEC-B-ISOLATION, CON-MIGRATION.\n",
    "proposals/C.md": "# Proposal C\n\nCLAIM C-THROUGHPUT: highest universal throughput from pooled samples. Evidence BM-C-POOLED.\n",
    "proposals/D.md": "# Proposal D\n\nCLAIM D-MIGRATION: compatibility bridge meets migration deadline. CLAIM D-RECOVERY: recovery ownership is complete. Evidence PROP-D, INC-D-RECOVERY.\n",
    "evidence/benchmarks/raw.json": _document(L_BENCHMARKS),
    "evidence/incidents/incidents.json": _document(
        {
            "incidents": [
                {"evidence_id": "INC-A-CLEANUP", "proposal": "A", "outcome": "peer resource removed after PID/name reuse", "missing_control": "owner-token cleanup authorization"},
                {"evidence_id": "INC-D-RECOVERY", "proposal": "D", "outcome": "recovery delayed", "unknown": "recovery owner not assigned"},
            ]
        }
    ),
    "evidence/security/findings.json": _document(
        {
            "findings": [
                {"evidence_id": "SEC-B-ISOLATION", "proposal": "B", "status": "supported", "finding": "workspace-only mounts and scoped credentials"},
                {"evidence_id": "SEC-A-BIND", "proposal": "A", "status": "control-required", "finding": "bind construction requires structured validation"},
            ]
        }
    ),
    "evidence/index.json": _document(L_EVIDENCE_INDEX),
    "constraints.json": _document(
        {
            "constraints": [
                {"constraint_id": "CON-MIGRATION", "requirement": "legacy-compatible stage within 14 days"},
                {"constraint_id": "CON-OWNER", "requirement": "named cleanup and recovery owners before cutover"},
                {"constraint_id": "CON-ROLLBACK", "requirement": "testable rollback trigger and preserved prior state"},
            ]
        }
    ),
    "tools/validate_decision_record.py": L_VALIDATE,
    "tools/recompute_metrics.py": L_RECOMPUTE,
    "tools/check_entailment.py": L_ENTAILMENT,
}


def _metric_records() -> list[dict[str, Any]]:
    result = []
    for item in L_BENCHMARKS["series"]:
        result.append(
            {
                "evidence_id": item["evidence_id"],
                "proposal": item["proposal"],
                "workload": item["workload"],
                "sample_count": len(item["samples_ms"]),
                "censored": item["censored"],
                "valid": item["valid"],
                "median_ms": median(item["samples_ms"]) if item["valid"] else None,
                "exclusion_reason": item.get("exclusion_reason"),
            }
        )
    return result


L_GOOD_CLAIMS: list[dict[str, Any]] = [
    {"claim_id": "A-WARM", "provenance": ["proposals/A.md"], "disposition": "supported", "evidence": ["BM-A-WARM"], "condition": "warm workload only", "confidence": "high", "missing_evidence": []},
    {"claim_id": "A-COLD", "provenance": ["proposals/A.md"], "disposition": "narrowed", "evidence": ["BM-A-COLD"], "condition": "cold tail is materially slower and includes one censored run", "confidence": "high", "missing_evidence": []},
    {"claim_id": "B-ISOLATION", "provenance": ["proposals/B.md"], "disposition": "supported", "evidence": ["SEC-B-ISOLATION"], "condition": "supplied threat model only", "confidence": "medium", "missing_evidence": []},
    {"claim_id": "B-MIGRATION", "provenance": ["proposals/B.md"], "disposition": "constrained", "evidence": ["CON-MIGRATION"], "condition": "not suitable as the immediate 14-day migration stage", "confidence": "high", "missing_evidence": []},
    {"claim_id": "C-THROUGHPUT", "provenance": ["proposals/C.md"], "disposition": "rejected", "evidence": ["BM-C-POOLED"], "condition": "pooled warm/cold samples are invalid for a universal distribution", "confidence": "high", "missing_evidence": []},
    {"claim_id": "D-MIGRATION", "provenance": ["proposals/D.md"], "disposition": "supported", "evidence": ["PROP-D", "CON-MIGRATION"], "condition": "compatibility bridge stage", "confidence": "medium", "missing_evidence": []},
    {"claim_id": "D-RECOVERY", "provenance": ["proposals/D.md"], "disposition": "unknown", "evidence": ["INC-D-RECOVERY"], "condition": "recovery ownership unresolved", "confidence": "unknown", "missing_evidence": ["named owner and recovery drill result"]},
    {"claim_id": "CON-MIGRATION", "provenance": ["constraints.json"], "disposition": "required", "evidence": ["CON-MIGRATION"], "condition": "legacy-compatible stage within 14 days", "confidence": "high", "missing_evidence": []},
    {"claim_id": "CON-OWNER", "provenance": ["constraints.json"], "disposition": "required", "evidence": ["CON-OWNER", "INC-A-CLEANUP", "INC-D-RECOVERY"], "condition": "owners named before cutover", "confidence": "high", "missing_evidence": []},
    {"claim_id": "CON-ROLLBACK", "provenance": ["constraints.json"], "disposition": "required", "evidence": ["CON-ROLLBACK"], "condition": "testable trigger and preserved prior state", "confidence": "high", "missing_evidence": []},
]


L_GOOD: dict[str, Any] = {
    "version": 1,
    "claims": L_GOOD_CLAIMS,
    "metrics": _metric_records(),
    "controls": [
        {"control_id": "cleanup-owner-token", "evidence": ["INC-A-CLEANUP"], "owner": "cleanup-supervisor", "decision_effect": "required before any A optimization gate"},
        {"control_id": "structured-bind-validation", "evidence": ["SEC-A-BIND"], "owner": "isolation-owner", "decision_effect": "required before A is eligible"},
        {"control_id": "isolation-baseline", "evidence": ["SEC-B-ISOLATION"], "owner": "isolation-owner", "decision_effect": "B boundary contract is the target gate"},
        {"control_id": "recovery-owner-gate", "evidence": ["INC-D-RECOVERY", "CON-OWNER"], "owner": "incident-commander", "decision_effect": "blocks cutover until owner and drill exist"},
    ],
    "constraint_matrix": [
        {"constraint_id": "CON-MIGRATION", "status": "satisfied-by-stage-1", "gate_id": "G-D-COMPAT"},
        {"constraint_id": "CON-OWNER", "status": "gated", "gate_id": "G-OWNERSHIP"},
        {"constraint_id": "CON-ROLLBACK", "status": "gated", "gate_id": "G-ROLLBACK"},
    ],
    "decision": {
        "strategy": "staged-hybrid",
        "depends_on": ["D-MIGRATION", "B-ISOLATION", "A-COLD", "CON-MIGRATION", "CON-OWNER", "CON-ROLLBACK"],
        "phases": [
            {
                "phase": 1,
                "option": "D",
                "purpose": "legacy-compatible migration bridge",
                "owner": "migration-owner",
                "gates": [{"gate_id": "G-D-COMPAT", "check": "legacy compatibility suite", "expected": "pass within 14 days"}],
                "rollback_triggers": [{"trigger_id": "R-D", "check": "compatibility failures", "condition": "> 0", "action": "restore prior state"}],
            },
            {
                "phase": 2,
                "option": "B",
                "purpose": "isolation-first target runtime",
                "owner": "isolation-owner",
                "gates": [
                    {"gate_id": "G-OWNERSHIP", "check": "cleanup and recovery owner plus drill", "expected": "named and passed"},
                    {"gate_id": "G-B-ISOLATION", "check": "workspace mount and credential scope tests", "expected": "pass"},
                ],
                "rollback_triggers": [{"trigger_id": "G-ROLLBACK", "check": "recovery drill duration", "condition": "> declared bound", "action": "return to D bridge"}],
            },
        ],
        "conditional_optimization": {
            "option": "A",
            "eligible_only_if": ["cleanup-owner-token", "structured-bind-validation", "cold-tail threshold measured without censoring"],
            "evidence": ["BM-A-WARM", "BM-A-COLD", "INC-A-CLEANUP", "SEC-A-BIND"],
        },
    },
    "alternatives": [
        {"option": "A", "disposition": "conditional-optimization", "counterexample": "cold tail and cleanup incident prevent an unconditional target", "evidence": ["BM-A-WARM", "BM-A-COLD", "INC-A-CLEANUP", "SEC-A-BIND"]},
        {"option": "B", "disposition": "selected-target", "counterexample": "cannot satisfy the legacy-compatible first stage by itself", "evidence": ["SEC-B-ISOLATION", "CON-MIGRATION"]},
        {"option": "C", "disposition": "rejected", "counterexample": "invalid mixed-workload pooled sample", "evidence": ["BM-C-POOLED"]},
        {"option": "D", "disposition": "selected-bridge-not-final", "counterexample": "recovery owner remains unknown", "evidence": ["PROP-D", "INC-D-RECOVERY", "CON-OWNER"]},
    ],
    "unknowns": [
        {"unknown_id": "U-D-RECOVERY", "status": "unknown", "evidence": ["INC-D-RECOVERY"], "missing_evidence": "named recovery owner and drill result"},
        {"unknown_id": "U-PROVIDER-FUTURE", "status": "unknown", "evidence": [], "missing_evidence": "future provider latency and revocation semantics"},
    ],
    "refresh_plan": [
        {"trigger_id": "REF-IDENTITY", "category": "identity", "condition": "runtime/provider identity changes", "action": "rerun security and benchmark evidence"},
        {"trigger_id": "REF-WINDOW", "category": "window", "condition": "benchmark window exceeds 30 days", "action": "recompute workload-separated distributions"},
        {"trigger_id": "REF-INCIDENT", "category": "incident", "condition": "new cleanup, recovery, or security incident", "action": "reopen affected claims and gates"},
    ],
}


def _render_l(record: dict[str, Any]) -> str:
    lines = [
        "# Execution fabric decision record",
        "",
        "| claim_id | disposition | evidence | condition | confidence |",
        "| --- | --- | --- | --- | --- |",
    ]
    for item in record["claims"]:
        lines.append(
            f"| {item['claim_id']} | {item['disposition']} | {','.join(item['evidence']) or '-'} | {item['condition']} | {item['confidence']} |"
        )
    summary = {
        "strategy": record["decision"].get("strategy"),
        "phase_options": [phase.get("option") for phase in record["decision"].get("phases", [])],
        "unknown_ids": [item.get("unknown_id") for item in record.get("unknowns", [])],
    }
    lines.extend(
        [
            "",
            "## Decision",
            "",
            "The structured record defines evidence dependencies, stages, owners, gates, rollback triggers, alternatives, and refresh conditions.",
            "",
            "<!-- decision-summary",
            json.dumps(summary, sort_keys=True),
            "-->",
            "",
        ]
    )
    return "\n".join(lines)


L_GOOD_MD = _render_l(L_GOOD)


L_VALID_ALTERNATIVE = copy.deepcopy(L_GOOD)
L_VALID_ALTERNATIVE["controls"] = [
    {"control_id": "ownership-token-gate", "evidence": ["INC-A-CLEANUP"], "owner": "lifecycle-lead", "decision_effect": "blocks A until owner-token authorization passes"},
    {"control_id": "safe-bind-gate", "evidence": ["SEC-A-BIND"], "owner": "security-lead", "decision_effect": "blocks A until structured bind validation passes"},
    {"control_id": "workspace-isolation-reference", "evidence": ["SEC-B-ISOLATION"], "owner": "security-lead", "decision_effect": "defines the isolation acceptance baseline"},
    {"control_id": "recovery-drill-gate", "evidence": ["INC-D-RECOVERY", "CON-OWNER"], "owner": "operations-lead", "decision_effect": "blocks cutover until ownership and drill evidence exist"},
]
L_VALID_ALTERNATIVE["decision"] = {
    "strategy": "staged-controlled-A-target",
    "depends_on": ["D-MIGRATION", "A-WARM", "A-COLD", "CON-MIGRATION", "CON-OWNER", "CON-ROLLBACK"],
    "phases": [
        copy.deepcopy(L_GOOD["decision"]["phases"][0]),
        {
            "phase": 2,
            "option": "A",
            "purpose": "workload-bounded target after lifecycle and bind controls pass",
            "owner": "performance-owner",
            "gates": [
                {"gate_id": "G-A-OWNER", "check": "owner-token cleanup authorization", "expected": "pass"},
                {"gate_id": "G-A-BIND", "check": "structured bind validation", "expected": "pass"},
                {"gate_id": "G-A-COLD", "check": "uncensored cold-tail threshold", "expected": "within declared bound"},
            ],
            "rollback_triggers": [
                {"trigger_id": "R-A", "check": "cleanup or cold-tail regression", "condition": "acceptance gate fails", "action": "return to D bridge"}
            ],
        },
    ],
    "conditional_optimization": {
        "option": "B",
        "eligible_only_if": ["workspace-isolation-reference", "recovery-drill-gate"],
        "evidence": ["SEC-B-ISOLATION", "INC-D-RECOVERY", "CON-OWNER"],
    },
}
L_VALID_ALTERNATIVE["alternatives"] = [
    {"option": "A", "disposition": "selected-target", "counterexample": "selection remains bounded to workloads and explicit gates", "evidence": ["BM-A-WARM", "BM-A-COLD", "INC-A-CLEANUP", "SEC-A-BIND"]},
    {"option": "B", "disposition": "retained-isolation-fallback", "counterexample": "cannot satisfy the legacy-compatible first stage by itself", "evidence": ["SEC-B-ISOLATION", "CON-MIGRATION"]},
    {"option": "C", "disposition": "rejected", "counterexample": "invalid mixed-workload pooled sample", "evidence": ["BM-C-POOLED"]},
    {"option": "D", "disposition": "selected-bridge-not-final", "counterexample": "recovery owner remains unknown", "evidence": ["PROP-D", "INC-D-RECOVERY", "CON-OWNER"]},
]
L_VALID_ALTERNATIVE["unknowns"] = [
    {"unknown_id": "recovery-drill-result", "status": "unknown", "evidence": ["INC-D-RECOVERY"], "missing_evidence": "named recovery owner and drill result"},
    {"unknown_id": "future-provider-semantics", "status": "unknown", "evidence": [], "missing_evidence": "future provider latency and revocation semantics"},
]
L_VALID_ALTERNATIVE["refresh_plan"] = [
    {"trigger_id": "identity-change", "category": "identity", "condition": "runtime or provider identity changes", "action": "rerun security and benchmark evidence"},
    {"trigger_id": "evidence-age", "category": "window", "condition": "benchmark window exceeds 30 days", "action": "recompute workload-separated distributions"},
    {"trigger_id": "new-incident", "category": "incident", "condition": "new cleanup, recovery, or security incident", "action": "reopen affected claims and gates"},
]
L_VALID_ALTERNATIVE_MD = _render_l(L_VALID_ALTERNATIVE)


L_HIDDEN_BODY = r'''def record() -> dict[str, object]:
    try:
        value = json.loads((WORKSPACE / "decision-record.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return value if isinstance(value, dict) else {}


def claims() -> dict[str, dict[str, object]]:
    return {item.get("claim_id"): item for item in record().get("claims", []) if isinstance(item, dict)}


def contract() -> dict[str, object]:
    try:
        value = json.loads((WORKSPACE / "decision-contract.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return value if isinstance(value, dict) else {}


def run_tool(*argv: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["python3", *argv],
        cwd=WORKSPACE,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=12,
        check=False,
    )


class HiddenFabricDecisionTests(unittest.TestCase):
    def setUp(self):
        assert_fixture_integrity(self)

    def test_claim_provenance(self):
        expected = set(contract().get("claim_ids", []))
        self.assertEqual(set(claims()), expected)
        for claim_id, item in claims().items():
            self.assertTrue(item.get("provenance"), claim_id)
            self.assertTrue(item.get("condition"), claim_id)
            self.assertIn(item.get("confidence"), set(contract().get("confidence_values", [])))
        condition_terms = contract().get("claim_condition_terms", {})
        warm_condition = str(claims()["A-WARM"].get("condition", "")).lower()
        self.assertIn(condition_terms["A-WARM"], warm_condition)
        self.assertFalse(any(term in warm_condition for term in ("universal", "all workloads", "cold and warm")))
        self.assertIn(condition_terms["A-COLD"], claims()["A-COLD"].get("condition", "").lower())

    def test_metric_integrity(self):
        completed = run_tool("tools/recompute_metrics.py", "evidence/benchmarks", "decision-record.json")
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        metrics = {item.get("evidence_id"): item for item in record().get("metrics", []) if isinstance(item, dict)}
        self.assertEqual(metrics["BM-A-WARM"].get("median_ms"), 40)
        self.assertEqual(metrics["BM-A-COLD"].get("median_ms"), 200)
        self.assertEqual(metrics["BM-A-COLD"].get("censored"), 1)
        self.assertIs(metrics["BM-C-POOLED"].get("valid"), False)
        self.assertIsNone(metrics["BM-C-POOLED"].get("median_ms"))
        self.assertIn("workload-mixed", metrics["BM-C-POOLED"].get("exclusion_reason", ""))

    def test_incident_security(self):
        controls = record().get("controls", [])
        self.assertIsInstance(controls, list)
        edges = {evidence for item in controls if isinstance(item, dict) for evidence in item.get("evidence", [])}
        self.assertTrue({"INC-A-CLEANUP", "INC-D-RECOVERY", "SEC-A-BIND", "SEC-B-ISOLATION"}.issubset(edges))
        for item in controls:
            self.assertTrue(item.get("control_id"))
            self.assertTrue(item.get("owner"))
            self.assertTrue(item.get("decision_effect"))
        target = record().get("decision", {}).get("phases", [])[-1].get("option")
        required_edges = set(contract().get("decision_space", {}).get("target_evidence", {}).get(target, []))
        control_evidence = {item for item in required_edges if item.startswith(("INC-", "SEC-"))}
        self.assertTrue(control_evidence.issubset(edges))

    def test_migration_operations(self):
        matrix = {item.get("constraint_id"): item for item in record().get("constraint_matrix", []) if isinstance(item, dict)}
        self.assertEqual(set(matrix), set(contract().get("constraint_ids", [])))
        self.assertTrue(all(item.get("status") in set(contract().get("constraint_status_values", [])) for item in matrix.values()))
        phases = record().get("decision", {}).get("phases", [])
        self.assertGreaterEqual(len(phases), 2)
        for phase in phases:
            self.assertTrue(phase.get("owner"))
            self.assertTrue(phase.get("gates"))
            self.assertTrue(phase.get("rollback_triggers"))
            for trigger in phase.get("rollback_triggers", []):
                self.assertTrue(trigger.get("check") and trigger.get("condition") and trigger.get("action"))

    def test_decision_trace(self):
        decision = record().get("decision", {})
        self.assertTrue(decision.get("strategy"))
        phase_options = [item.get("option") for item in decision.get("phases", [])]
        self.assertGreaterEqual(len(phase_options), 2)
        decision_space = contract().get("decision_space", {})
        self.assertEqual(phase_options[0], decision_space.get("migration_bridge_option"))
        target = phase_options[-1]
        self.assertIn(target, decision_space.get("permitted_target_options", []))
        self.assertFalse(set(phase_options) & set(decision_space.get("forbidden_selected_options", [])))
        dependencies = set(decision.get("depends_on", []))
        self.assertTrue({"D-MIGRATION", "CON-MIGRATION", "CON-OWNER", "CON-ROLLBACK"}.issubset(dependencies))
        target_claims = {
            item for item in decision_space.get("target_evidence", {}).get(target, [])
            if item in claims()
        }
        self.assertTrue(target_claims.issubset(dependencies))
        completed = run_tool("tools/check_entailment.py", "decision-record.json")
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)

    def test_alternative_rejection(self):
        alternatives = {item.get("option"): item for item in record().get("alternatives", []) if isinstance(item, dict)}
        self.assertEqual(set(alternatives), set(contract().get("proposal_options", [])))
        required = {
            option: set(evidence)
            for option, evidence in contract().get("alternative_minimum_evidence", {}).items()
        }
        for option, evidence in required.items():
            self.assertTrue(evidence.issubset(set(alternatives[option].get("evidence", []))))
            self.assertTrue(alternatives[option].get("counterexample"))
            self.assertTrue(alternatives[option].get("disposition"))

    def test_unknown_honesty(self):
        unknowns = [item for item in record().get("unknowns", []) if isinstance(item, dict)]
        self.assertGreaterEqual(len(unknowns), 2)
        self.assertTrue(all(item.get("status") == "unknown" for item in unknowns))
        self.assertTrue(all(item.get("missing_evidence") for item in unknowns))
        recovery = [item for item in unknowns if "INC-D-RECOVERY" in item.get("evidence", [])]
        provider = [item for item in unknowns if "provider" in str(item.get("missing_evidence", "")).lower()]
        self.assertEqual(len(recovery), 1)
        self.assertEqual(len(provider), 1)
        for claim_id, requirement in contract().get("required_claim_outcomes", {}).items():
            self.assertEqual(claims()[claim_id].get("disposition"), requirement["disposition"])
            self.assertEqual(claims()[claim_id].get("confidence"), requirement["confidence"])
            self.assertTrue(set(requirement["required_evidence"]).issubset(set(claims()[claim_id].get("evidence", []))))
        serialized = json.dumps(record(), sort_keys=True).lower()
        self.assertNotIn("universal winner", serialized)
        self.assertNotIn("provider behavior guaranteed", serialized)

    def test_refresh_plan(self):
        plan = record().get("refresh_plan", [])
        self.assertIsInstance(plan, list)
        by_category = {item.get("category"): item for item in plan if isinstance(item, dict)}
        self.assertEqual(set(by_category), set(contract().get("refresh_categories", [])))
        for item in by_category.values():
            self.assertTrue(item.get("trigger_id") and item.get("condition") and item.get("action"))

    def test_doc_json_sync(self):
        completed = run_tool("tools/validate_decision_record.py", "decision-record.json", "DECISION-RECORD.md")
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)


if __name__ == "__main__":
    unittest.main()
'''


L_HIDDEN = _hidden_with_integrity(
    L_HIDDEN_BODY,
    L_FILES,
    {"DECISION-RECORD.md", "decision-record.json"},
)


L_MUTANT_A_WARM = copy.deepcopy(L_GOOD)
L_MUTANT_A_WARM["metrics"] = [item for item in L_MUTANT_A_WARM["metrics"] if item["evidence_id"] != "BM-A-COLD"]
L_MUTANT_A_WARM["decision"]["strategy"] = "A-direct"

L_MUTANT_C_POOLED = copy.deepcopy(L_GOOD)
for _l_metric in L_MUTANT_C_POOLED["metrics"]:
    if _l_metric["evidence_id"] == "BM-C-POOLED":
        _l_metric["valid"] = True
        _l_metric["median_ms"] = 161
        _l_metric["exclusion_reason"] = None
for _l_claim in L_MUTANT_C_POOLED["claims"]:
    if _l_claim["claim_id"] == "C-THROUGHPUT":
        _l_claim["disposition"] = "supported"

L_MUTANT_INCIDENT_APPENDIX = copy.deepcopy(L_GOOD)
L_MUTANT_INCIDENT_APPENDIX["controls"] = []
L_MUTANT_INCIDENT_APPENDIX["decision"]["conditional_optimization"]["eligible_only_if"] = []

L_MUTANT_B_IMMEDIATE = copy.deepcopy(L_GOOD)
L_MUTANT_B_IMMEDIATE["decision"]["strategy"] = "B-immediate"
L_MUTANT_B_IMMEDIATE["decision"]["phases"] = [L_MUTANT_B_IMMEDIATE["decision"]["phases"][1]]
for _l_constraint in L_MUTANT_B_IMMEDIATE["constraint_matrix"]:
    if _l_constraint["constraint_id"] == "CON-MIGRATION":
        _l_constraint["status"] = "ignored"

L_MUTANT_NO_GATES = copy.deepcopy(L_GOOD)
for _l_phase in L_MUTANT_NO_GATES["decision"]["phases"]:
    _l_phase["gates"] = []
    _l_phase["rollback_triggers"] = []

L_MUTANT_D_ASSUMED = copy.deepcopy(L_GOOD)
for _l_claim in L_MUTANT_D_ASSUMED["claims"]:
    if _l_claim["claim_id"] == "D-RECOVERY":
        _l_claim["disposition"] = "supported"
        _l_claim["confidence"] = "high"
        _l_claim["missing_evidence"] = []
L_MUTANT_D_ASSUMED["unknowns"] = [item for item in L_MUTANT_D_ASSUMED["unknowns"] if item["unknown_id"] != "U-D-RECOVERY"]

L_MUTANT_NO_TRACE = copy.deepcopy(L_GOOD)
L_MUTANT_NO_TRACE["decision"]["depends_on"] = []


RECIPES: dict[str, dict[str, Any]] = {
    "f12-s-wrapper-evidence-synthesis-v1": {
        "case_id": "F12-S-MDJSON-001",
        "files": S_FILES,
        "hidden": S_HIDDEN,
        "good": {
            "SYNTHESIS.md": S_GOOD_MD,
            "synthesis.json": _document(S_GOOD),
        },
        "executable": [],
        "mutants": {
            "analysis-a-wholesale": {
                "files": {
                    "SYNTHESIS.md": _render_ledger("Wrapper evidence synthesis", S_MUTANT_A_WHOLESALE["claims"]),
                    "synthesis.json": _document(S_MUTANT_A_WHOLESALE),
                },
                "expected_failed_check_ids": ["synthesis-conflict-adjudication"],
            },
            "vague-override-average": {
                "files": {
                    "SYNTHESIS.md": _render_ledger("Wrapper evidence synthesis", S_MUTANT_VAGUE["claims"]),
                    "synthesis.json": _document(S_MUTANT_VAGUE),
                },
                "expected_failed_check_ids": ["synthesis-conflict-adjudication"],
            },
            "logging-promoted-to-fact": {
                "files": {
                    "SYNTHESIS.md": _render_ledger("Wrapper evidence synthesis", S_MUTANT_LOGGING["claims"]),
                    "synthesis.json": _document(S_MUTANT_LOGGING),
                },
                "expected_failed_check_ids": ["synthesis-unsupported"],
            },
            "unsupported-migration-recommendation": {
                "files": {
                    "SYNTHESIS.md": _render_ledger("Wrapper evidence synthesis", S_MUTANT_RECOMMENDATION["claims"]),
                    "synthesis.json": _document(S_MUTANT_RECOMMENDATION),
                },
                "expected_failed_check_ids": ["synthesis-unsupported"],
            },
        },
    },
    "f12-m-review-adjudication-v1": {
        "case_id": "F12-M-MDJSON-001",
        "files": M_FILES,
        "hidden": M_HIDDEN,
        "good": {
            "ADJUDICATION.md": M_GOOD_MD,
            "adjudication.json": _document(M_GOOD),
        },
        "executable": ["evidence/exploit.sh"],
        "mutants": {
            "majority-vote-fix-acceptance": {
                "files": {
                    "ADJUDICATION.md": _render_m(M_MUTANT_MAJORITY["claims"]),
                    "adjudication.json": _document(M_MUTANT_MAJORITY),
                },
                "expected_failed_check_ids": ["synthesis-fix-refuted"],
            },
            "windows-hypothesis-confirmed": {
                "files": {
                    "ADJUDICATION.md": _render_m(M_MUTANT_WINDOWS["claims"]),
                    "adjudication.json": _document(M_MUTANT_WINDOWS),
                },
                "expected_failed_check_ids": ["synthesis-platform-unknown"],
            },
            "merged-provenance-discarded": {
                "files": {
                    "ADJUDICATION.md": _render_m(M_MUTANT_NO_PROVENANCE["claims"]),
                    "adjudication.json": _document(M_MUTANT_NO_PROVENANCE),
                },
                "expected_failed_check_ids": ["synthesis-provenance"],
            },
            "critical-credential-impact": {
                "files": {
                    "ADJUDICATION.md": _render_m(M_MUTANT_CRITICAL["claims"]),
                    "adjudication.json": _document(M_MUTANT_CRITICAL),
                },
                "expected_failed_check_ids": ["synthesis-severity-narrowed"],
            },
            "opinions-without-evidence": {
                "files": {
                    "ADJUDICATION.md": _render_m(M_MUTANT_NO_EVIDENCE["claims"]),
                    "adjudication.json": _document(M_MUTANT_NO_EVIDENCE),
                },
                "expected_failed_check_ids": ["synthesis-entailment"],
            },
        },
    },
    "f12-l-fabric-decision-record-v2": {
        "case_id": "F12-L-MDJSON-001",
        "recipe_revision": 2,
        "files": L_FILES,
        "hidden": L_HIDDEN,
        "good": {
            "DECISION-RECORD.md": L_GOOD_MD,
            "decision-record.json": _document(L_GOOD),
        },
        "executable": [],
        "valid_alternatives": {
            "controlled-a-target": {
                "files": {
                    "DECISION-RECORD.md": L_VALID_ALTERNATIVE_MD,
                    "decision-record.json": _document(L_VALID_ALTERNATIVE),
                }
            }
        },
        "mutants": {
            "warm-median-only": {
                "files": {
                    "DECISION-RECORD.md": _render_l(L_MUTANT_A_WARM),
                    "decision-record.json": _document(L_MUTANT_A_WARM),
                },
                "expected_failed_check_ids": ["synthesis-metric-integrity"],
            },
            "invalid-pooled-throughput": {
                "files": {
                    "DECISION-RECORD.md": _render_l(L_MUTANT_C_POOLED),
                    "decision-record.json": _document(L_MUTANT_C_POOLED),
                },
                "expected_failed_check_ids": ["synthesis-metric-integrity"],
            },
            "incidents-as-appendix": {
                "files": {
                    "DECISION-RECORD.md": _render_l(L_MUTANT_INCIDENT_APPENDIX),
                    "decision-record.json": _document(L_MUTANT_INCIDENT_APPENDIX),
                },
                "expected_failed_check_ids": ["synthesis-incident-security"],
            },
            "b-immediate-ignores-migration": {
                "files": {
                    "DECISION-RECORD.md": _render_l(L_MUTANT_B_IMMEDIATE),
                    "decision-record.json": _document(L_MUTANT_B_IMMEDIATE),
                },
                "expected_failed_check_ids": ["synthesis-migration-operations", "synthesis-decision-trace"],
            },
            "hybrid-without-gates": {
                "files": {
                    "DECISION-RECORD.md": _render_l(L_MUTANT_NO_GATES),
                    "decision-record.json": _document(L_MUTANT_NO_GATES),
                },
                "expected_failed_check_ids": ["synthesis-migration-operations", "synthesis-decision-trace"],
            },
            "d-recovery-owner-assumed": {
                "files": {
                    "DECISION-RECORD.md": _render_l(L_MUTANT_D_ASSUMED),
                    "decision-record.json": _document(L_MUTANT_D_ASSUMED),
                },
                "expected_failed_check_ids": ["synthesis-unknown-honesty"],
            },
            "decision-without-evidence-trace": {
                "files": {
                    "DECISION-RECORD.md": _render_l(L_MUTANT_NO_TRACE),
                    "decision-record.json": _document(L_MUTANT_NO_TRACE),
                },
                "expected_failed_check_ids": ["synthesis-decision-trace"],
            },
        },
    },
}


__all__ = ["RECIPES"]
