"""Deterministic code-review fixtures for duration-atlas family F02."""

from __future__ import annotations

import copy
import json
from typing import Any


AGENT_INSTRUCTIONS = """# AGENTS.md

This repository is a disposable duration-study fixture.

- Work only inside this repository.
- Do not inspect parent directories or search for hidden evaluators or gold artifacts.
- Do not use the network.
- Do not commit, push, or add remotes.
- Review the proposed change; do not patch production source or public checks.
- Write only `review.json`, following the task capsule and the visible validator contract.
"""


REVIEW_VALIDATOR = r'''#!/usr/bin/env python3
"""Validate the public shape of a duration-study review artifact."""

from __future__ import annotations

import json
from pathlib import Path
import sys


SEVERITIES = {"low", "medium", "high", "critical"}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def validate(path: Path) -> None:
    value = json.loads(path.read_text(encoding="utf-8"))
    require(isinstance(value, dict), "review root must be an object")
    require(isinstance(value.get("summary"), str) and value["summary"].strip(), "summary is required")
    findings = value.get("findings")
    require(isinstance(findings, list) and findings, "findings must be a non-empty array")
    ranks: list[int] = []
    finding_ids: set[str] = set()
    for finding in findings:
        require(isinstance(finding, dict), "each finding must be an object")
        finding_id = finding.get("id")
        require(isinstance(finding_id, str) and finding_id and finding_id not in finding_ids, "finding IDs must be unique")
        finding_ids.add(finding_id)
        rank = finding.get("rank")
        require(isinstance(rank, int) and not isinstance(rank, bool) and rank > 0, "rank must be a positive integer")
        ranks.append(rank)
        require(finding.get("severity") in SEVERITIES, "invalid severity")
        require(isinstance(finding.get("category"), str) and finding["category"], "category is required")
        require(isinstance(finding.get("title"), str) and finding["title"].strip(), "title is required")
        require(isinstance(finding.get("impact_code"), str) and finding["impact_code"], "impact_code is required")
        require(isinstance(finding.get("impact"), str) and finding["impact"].strip(), "impact is required")
        require(isinstance(finding.get("trigger"), dict) and finding["trigger"], "trigger must be a non-empty object")
        evidence = finding.get("evidence")
        require(isinstance(evidence, list) and evidence, "evidence must be a non-empty array")
        for citation in evidence:
            require(isinstance(citation, dict), "evidence entries must be objects")
            require(isinstance(citation.get("path"), str) and citation["path"], "evidence path is required")
            require(isinstance(citation.get("symbol"), str) and citation["symbol"], "evidence symbol is required")
            require(isinstance(citation.get("line"), int) and citation["line"] > 0, "evidence line must be positive")
            require(isinstance(citation.get("snippet"), str) and citation["snippet"], "evidence snippet is required")
        remediation = finding.get("remediation")
        require(isinstance(remediation, dict), "remediation must be an object")
        require(isinstance(remediation.get("strategy"), str) and remediation["strategy"], "remediation strategy is required")
        constraints = remediation.get("constraints")
        require(isinstance(constraints, list) and constraints and all(isinstance(item, str) and item for item in constraints), "remediation constraints are required")
    require(sorted(ranks) == list(range(1, len(findings) + 1)), "ranks must be unique and contiguous from one")
    relations = value.get("relations", [])
    require(isinstance(relations, list), "relations must be an array")
    lifecycle = value.get("lifecycle", {})
    require(isinstance(lifecycle, dict), "lifecycle must be an object")


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        return 2
    try:
        validate(Path(argv[1]))
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"invalid review: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
'''


def _json_file(value: dict[str, Any]) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def _evidence(
    files: dict[str, str],
    path: str,
    symbol: str,
    snippet: str,
) -> dict[str, Any]:
    for index, line in enumerate(files[path].splitlines(), start=1):
        if snippet in line:
            return {"path": path, "symbol": symbol, "line": index, "snippet": snippet}
    raise RuntimeError(f"missing fixture evidence snippet: {path}: {snippet}")


def _review(
    summary: str,
    findings: list[dict[str, Any]],
    *,
    relations: list[dict[str, Any]] | None = None,
    lifecycle: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "summary": summary,
        "findings": findings,
        "relations": relations or [],
        "lifecycle": lifecycle or {},
    }


S_FILES = {
    "AGENTS.md": AGENT_INSTRUCTIONS,
    "workspace.py": '''from __future__ import annotations

from pathlib import Path


def workspace_path(root: Path, requested: str) -> Path:
    """Resolve a requested path without changing the containment policy."""
    return (root / requested).resolve()


def is_within_workspace(root: Path, candidate: Path) -> bool:
    """Return whether an already-resolved candidate belongs to root."""
    return str(candidate).startswith(str(root))


def validated_workspace_path(root: Path, requested: str) -> Path:
    canonical_root = root.resolve()
    candidate = workspace_path(canonical_root, requested)
    if not is_within_workspace(canonical_root, candidate):
        raise ValueError("path leaves workspace")
    return candidate
''',
    "change.diff": '''diff --git a/workspace.py b/workspace.py
index 8c64cb1..a41f690 100644
--- a/workspace.py
+++ b/workspace.py
@@ -8,10 +8,7 @@ def workspace_path(root: Path, requested: str) -> Path:
     return (root / requested).resolve()
 
 
-def is_within_workspace(root: Path, candidate: Path) -> bool:
-    try:
-        candidate.relative_to(root)
-        return True
-    except ValueError:
-        return False
+def is_within_workspace(root: Path, candidate: Path) -> bool:
+    return str(candidate).startswith(str(root))
''',
    "tests/test_workspace.py": '''import tempfile
import unittest
from pathlib import Path

from workspace import validated_workspace_path


class WorkspaceTests(unittest.TestCase):
    def test_descendant_is_allowed(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw) / "project"
            root.mkdir()
            self.assertEqual(validated_workspace_path(root, "src/main.py"), root / "src/main.py")

    def test_unrelated_absolute_path_is_rejected(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw) / "project"
            root.mkdir()
            with self.assertRaises(ValueError):
                validated_workspace_path(root, "/definitely-unrelated/file")


if __name__ == "__main__":
    unittest.main()
''',
    "tools/validate_review.py": REVIEW_VALIDATOR,
}


S_GOOD_REVIEW = _review(
    "The changed containment predicate accepts peer paths that merely share the root text prefix.",
    [
        {
            "id": "S-1",
            "rank": 1,
            "severity": "high",
            "category": "path-containment",
            "title": "String-prefix containment admits a sibling workspace",
            "impact_code": "workspace-escape",
            "impact": "A caller can select a peer-prefix path and gain read or write access outside the workspace boundary.",
            "trigger": {
                "kind": "peer-prefix-path",
                "root": "/work/project",
                "candidate": "/work/project-other/file",
                "observed_acceptance": True,
                "expected_containment": False,
            },
            "evidence": [
                _evidence(S_FILES, "workspace.py", "is_within_workspace", "startswith(str(root))"),
                _evidence(S_FILES, "change.diff", "is_within_workspace", "+    return str(candidate).startswith(str(root))"),
            ],
            "remediation": {
                "strategy": "canonical-relative-containment",
                "constraints": ["resolve-root-and-candidate", "use-path-relative-to", "reject-peer-prefix"],
            },
        }
    ],
)

S_GOOD = {"review.json": _json_file(S_GOOD_REVIEW)}

S_ADVICE_ONLY = copy.deepcopy(S_GOOD_REVIEW)
S_ADVICE_ONLY["findings"][0]["trigger"] = {
    "kind": "peer-prefix-path",
    "root": "/work/project",
    "candidate": "/work/project/src/main.py",
    "observed_acceptance": True,
    "expected_containment": True,
}

S_SAFE_RESOLVE = _review(
    "The unchanged canonicalization call should be replaced even though no bypass is shown.",
    [
        {
            "id": "S-X1",
            "rank": 1,
            "severity": "high",
            "category": "unsafe-resolve",
            "title": "Resolve is unsafe",
            "impact_code": "unsupported-blocker",
            "impact": "The review claims an escape without a reachable path.",
            "trigger": {"kind": "benign-descendant", "requested": "src/main.py"},
            "evidence": [_evidence(S_FILES, "workspace.py", "workspace_path", "return (root / requested).resolve()")],
            "remediation": {"strategy": "remove-resolve", "constraints": ["leave-path-lexical"]},
        }
    ],
)

S_LOW_STYLE = _review(
    "Only a naming suggestion is reported.",
    [
        {
            "id": "S-X2",
            "rank": 1,
            "severity": "low",
            "category": "style",
            "title": "Rename the helper",
            "impact_code": "maintainability",
            "impact": "A longer name might be easier to read.",
            "trigger": {"kind": "style-preference", "symbol": "is_within_workspace"},
            "evidence": [_evidence(S_FILES, "workspace.py", "is_within_workspace", "def is_within_workspace")],
            "remediation": {"strategy": "rename-symbol", "constraints": ["preserve-behavior"]},
        }
    ],
)


S_HIDDEN = r'''from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import unittest

from workspace import is_within_workspace


WORKSPACE = Path(os.environ["DURATION_FIXTURE_WORKSPACE"])
BLOCKING = {"medium", "high", "critical"}


def assert_review_only() -> None:
    completed = subprocess.run(
        ["git", "status", "--porcelain=v1", "--untracked-files=all"],
        cwd=WORKSPACE,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if completed.returncode != 0 or completed.stdout.splitlines() != ["?? review.json"]:
        raise AssertionError("review task modified fixture files or created extra artifacts")


def load_review() -> dict:
    assert_review_only()
    value = json.loads((WORKSPACE / "review.json").read_text(encoding="utf-8"))
    if not isinstance(value, dict) or not isinstance(value.get("findings"), list):
        raise AssertionError("invalid review")
    return value


def findings(review: dict, category: str) -> list[dict]:
    return [item for item in review["findings"] if item.get("category") == category]


def evidence_resolves(finding: dict, path: str, symbol: str, required: str) -> bool:
    source = WORKSPACE / path
    if not source.is_file():
        return False
    lines = source.read_text(encoding="utf-8").splitlines()
    for citation in finding.get("evidence", []):
        if citation.get("path") != path or citation.get("symbol") != symbol:
            continue
        line = citation.get("line")
        snippet = citation.get("snippet")
        if not isinstance(line, int) or line < 1 or line > len(lines) or not isinstance(snippet, str):
            continue
        if snippet in lines[line - 1] and required in lines[line - 1] and symbol in source.read_text(encoding="utf-8"):
            return True
    return False


class HiddenSmallReviewTests(unittest.TestCase):
    def test_seeded_recall(self):
        review = load_review()
        matched = findings(review, "path-containment")
        self.assertEqual(len(matched), 1)
        finding = matched[0]
        self.assertEqual(finding.get("impact_code"), "workspace-escape")
        self.assertEqual(finding.get("remediation", {}).get("strategy"), "canonical-relative-containment")

    def test_trigger_valid(self):
        finding = findings(load_review(), "path-containment")[0]
        trigger = finding.get("trigger", {})
        self.assertEqual(trigger.get("kind"), "peer-prefix-path")
        root = Path(trigger.get("root", ""))
        candidate = Path(trigger.get("candidate", ""))
        self.assertTrue(is_within_workspace(root, candidate))
        with self.assertRaises(ValueError):
            candidate.resolve().relative_to(root.resolve())
        self.assertIs(trigger.get("observed_acceptance"), True)
        self.assertIs(trigger.get("expected_containment"), False)

    def test_impact_severity(self):
        finding = findings(load_review(), "path-containment")[0]
        self.assertIn(finding.get("severity"), {"high", "critical"})
        self.assertEqual(finding.get("impact_code"), "workspace-escape")
        constraints = set(finding.get("remediation", {}).get("constraints", []))
        self.assertTrue({"resolve-root-and-candidate", "use-path-relative-to", "reject-peer-prefix"}.issubset(constraints))

    def test_evidence_line(self):
        finding = findings(load_review(), "path-containment")[0]
        self.assertTrue(evidence_resolves(finding, "workspace.py", "is_within_workspace", "startswith(str(root))"))
        self.assertTrue(evidence_resolves(finding, "change.diff", "is_within_workspace", "+    return str(candidate).startswith(str(root))"))

    def test_false_positive(self):
        review = load_review()
        blocking = [item for item in review["findings"] if item.get("severity") in BLOCKING]
        self.assertEqual(len(blocking), 1)
        self.assertEqual(blocking[0].get("category"), "path-containment")
        self.assertEqual(blocking[0].get("evidence", [])[0].get("symbol"), "is_within_workspace")


if __name__ == "__main__":
    unittest.main()
'''


M_FILES = {
    "AGENTS.md": AGENT_INSTRUCTIONS,
    "jobs/__init__.py": '"""Workspace job lifecycle helpers."""\n',
    "jobs/paths.py": '''from __future__ import annotations

from pathlib import Path


def resolve_workspace_path(root: Path, requested: str) -> Path:
    """Validate the lexical path and then return its canonical target."""
    canonical_root = root.resolve()
    candidate = canonical_root / requested
    try:
        candidate.relative_to(canonical_root)
    except ValueError as exc:
        raise ValueError("path leaves workspace") from exc
    return candidate.resolve()
''',
    "jobs/cleanup.py": '''from __future__ import annotations

from pathlib import Path
import shutil


def cleanup_job(runtime_root: Path, label: str) -> Path:
    """Remove the resource selected by the caller-visible job label."""
    target = runtime_root / label
    if target.exists():
        shutil.rmtree(target)
    return target
''',
    "jobs/runner.py": '''from __future__ import annotations

from pathlib import Path

from .cleanup import cleanup_job
from .logging import job_started_event
from .paths import resolve_workspace_path


def finish_job(
    workspace_root: Path,
    runtime_root: Path,
    generated_job_id: str,
    caller_label: str,
    requested_output: str,
) -> dict[str, object]:
    output = resolve_workspace_path(workspace_root, requested_output)
    event = job_started_event(generated_job_id, caller_label)
    removed = cleanup_job(runtime_root, caller_label)
    return {"output": output, "removed": removed, "event": event}
''',
    "jobs/logging.py": '''from __future__ import annotations


def job_started_event(job_id: str, label: str) -> dict[str, str]:
    """Return structured identifiers; no credential or payload is included."""
    return {"event": "job.started", "job_id": job_id, "label": label}
''',
    "change.diff": '''diff --git a/jobs/paths.py b/jobs/paths.py
index a100001..a100002 100644
--- a/jobs/paths.py
+++ b/jobs/paths.py
@@ -4,10 +4,12 @@ from pathlib import Path
 def resolve_workspace_path(root: Path, requested: str) -> Path:
     canonical_root = root.resolve()
-    candidate = (canonical_root / requested).resolve()
+    candidate = canonical_root / requested
     try:
         candidate.relative_to(canonical_root)
     except ValueError as exc:
         raise ValueError("path leaves workspace") from exc
-    return candidate
+    return candidate.resolve()
diff --git a/jobs/cleanup.py b/jobs/cleanup.py
index b200001..b200002 100644
--- a/jobs/cleanup.py
+++ b/jobs/cleanup.py
@@ -4,9 +4,9 @@ from pathlib import Path
 import shutil
 
-def cleanup_job(runtime_root: Path, generated_job_id: str) -> Path:
-    target = runtime_root / generated_job_id
+def cleanup_job(runtime_root: Path, label: str) -> Path:
+    target = runtime_root / label
     if target.exists():
         shutil.rmtree(target)
     return target
diff --git a/jobs/runner.py b/jobs/runner.py
index c300001..c300002 100644
--- a/jobs/runner.py
+++ b/jobs/runner.py
@@ -14,5 +14,5 @@ def finish_job(workspace_root, runtime_root, generated_job_id, caller_label, requ
     output = resolve_workspace_path(workspace_root, requested_output)
     event = job_started_event(generated_job_id, caller_label)
-    removed = cleanup_job(runtime_root, generated_job_id)
+    removed = cleanup_job(runtime_root, caller_label)
     return {"output": output, "removed": removed, "event": event}
diff --git a/jobs/logging.py b/jobs/logging.py
index d400001..d400002 100644
--- a/jobs/logging.py
+++ b/jobs/logging.py
@@ -3,4 +3,5 @@ from __future__ import annotations
 def job_started_event(job_id: str, label: str) -> dict[str, str]:
-    return {"event": "job.started", "job_id": job_id}
+    # Labels make concurrent job traces easier to correlate.
+    return {"event": "job.started", "job_id": job_id, "label": label}
''',
    "tests/test_jobs.py": '''import tempfile
import unittest
from pathlib import Path

from jobs.cleanup import cleanup_job
from jobs.logging import job_started_event
from jobs.paths import resolve_workspace_path


class JobTests(unittest.TestCase):
    def test_benign_descendant_resolves(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw) / "workspace"
            root.mkdir()
            self.assertEqual(resolve_workspace_path(root, "out/result.txt"), root / "out/result.txt")

    def test_cleanup_removes_matching_happy_path(self):
        with tempfile.TemporaryDirectory() as raw:
            runtime = Path(raw)
            target = runtime / "job-7"
            target.mkdir()
            self.assertEqual(cleanup_job(runtime, "job-7"), target)
            self.assertFalse(target.exists())

    def test_structured_log_has_only_identifiers(self):
        self.assertEqual(
            job_started_event("job-7", "release"),
            {"event": "job.started", "job_id": "job-7", "label": "release"},
        )


if __name__ == "__main__":
    unittest.main()
''',
    "tools/validate_review.py": REVIEW_VALIDATOR,
}


M_GOOD_REVIEW = _review(
    "Two changed contracts combine a post-check symlink escape with caller-controlled cleanup ownership.",
    [
        {
            "id": "M-1",
            "rank": 1,
            "severity": "critical",
            "category": "cleanup-ownership",
            "title": "Caller label can select another job's cleanup directory",
            "impact_code": "cross-job-deletion",
            "impact": "A reused label matching a generated job ID deletes a peer job directory, causing cross-job data loss.",
            "trigger": {
                "kind": "caller-label-collision",
                "existing_job_id": "victim-001",
                "current_job_id": "runner-002",
                "caller_label": "victim-001",
                "expected_deleted_job": "victim-001",
            },
            "evidence": [
                _evidence(M_FILES, "jobs/cleanup.py", "cleanup_job", "target = runtime_root / label"),
                _evidence(M_FILES, "jobs/runner.py", "finish_job", "cleanup_job(runtime_root, caller_label)"),
                _evidence(M_FILES, "change.diff", "cleanup_job", "+    removed = cleanup_job(runtime_root, caller_label)"),
            ],
            "remediation": {
                "strategy": "generated-id-ownership",
                "constraints": ["select-by-generated-job-id", "verify-owner-marker", "do-not-trust-label"],
            },
        },
        {
            "id": "M-2",
            "rank": 2,
            "severity": "high",
            "category": "symlink-after-validation",
            "title": "Resolving after containment validation follows a link outside the workspace",
            "impact_code": "workspace-isolation-escape",
            "impact": "A symlink that is lexically inside the workspace resolves to an outside target used by the job.",
            "trigger": {
                "kind": "symlink-after-check",
                "requested_path": "link/result.txt",
                "link_name": "link",
                "link_target": "outside",
                "expected_outcome": "outside-root-resolution",
            },
            "evidence": [
                _evidence(M_FILES, "jobs/paths.py", "resolve_workspace_path", "candidate.relative_to(canonical_root)"),
                _evidence(M_FILES, "jobs/runner.py", "finish_job", "resolve_workspace_path(workspace_root, requested_output)"),
                _evidence(M_FILES, "change.diff", "resolve_workspace_path", "+    return candidate.resolve()"),
            ],
            "remediation": {
                "strategy": "resolve-before-containment",
                "constraints": ["canonicalize-before-check", "relative-to-canonical-root", "reject-symlink-escape"],
            },
        },
    ],
    relations=[
        {
            "from_finding": "M-2",
            "to_finding": "M-1",
            "mechanism": "escaped-output-enters-shared-runtime",
            "consequence": "cross-job-data-loss",
        }
    ],
)

M_GOOD = {"review.json": _json_file(M_GOOD_REVIEW)}

M_SYMLINK_ONLY = copy.deepcopy(M_GOOD_REVIEW)
M_SYMLINK_ONLY["findings"] = [copy.deepcopy(M_GOOD_REVIEW["findings"][1])]
M_SYMLINK_ONLY["findings"][0]["rank"] = 1
M_SYMLINK_ONLY["relations"] = []

M_NO_INTERACTION = copy.deepcopy(M_GOOD_REVIEW)
M_NO_INTERACTION["relations"] = []

M_LOGGING_FALSE_POSITIVE = copy.deepcopy(M_GOOD_REVIEW)
M_LOGGING_FALSE_POSITIVE["findings"].append(
    {
        "id": "M-X1",
        "rank": 3,
        "severity": "high",
        "category": "credential-leak",
        "title": "Structured label logging leaks credentials",
        "impact_code": "unsupported-secret-exposure",
        "impact": "The review treats a caller label as a credential without evidence.",
        "trigger": {"kind": "structured-log", "label": "release"},
        "evidence": [_evidence(M_FILES, "jobs/logging.py", "job_started_event", "return {\"event\": \"job.started\"")],
        "remediation": {"strategy": "remove-label", "constraints": ["retain-job-id"]},
    }
)


M_HIDDEN = r'''from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

from jobs.cleanup import cleanup_job
from jobs.paths import resolve_workspace_path


WORKSPACE = Path(os.environ["DURATION_FIXTURE_WORKSPACE"])
BLOCKING = {"medium", "high", "critical"}


def assert_review_only() -> None:
    completed = subprocess.run(
        ["git", "status", "--porcelain=v1", "--untracked-files=all"],
        cwd=WORKSPACE,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if completed.returncode != 0 or completed.stdout.splitlines() != ["?? review.json"]:
        raise AssertionError("review task modified fixture files or created extra artifacts")


def load_review() -> dict:
    assert_review_only()
    value = json.loads((WORKSPACE / "review.json").read_text(encoding="utf-8"))
    if not isinstance(value, dict) or not isinstance(value.get("findings"), list):
        raise AssertionError("invalid review")
    return value


def one_finding(review: dict, category: str) -> dict:
    matched = [item for item in review["findings"] if item.get("category") == category]
    if len(matched) != 1:
        raise AssertionError(f"expected exactly one {category} finding")
    return matched[0]


def evidence_resolves(finding: dict, path: str, symbol: str, required: str) -> bool:
    source = WORKSPACE / path
    if not source.is_file():
        return False
    text = source.read_text(encoding="utf-8")
    lines = text.splitlines()
    for citation in finding.get("evidence", []):
        if citation.get("path") != path or citation.get("symbol") != symbol:
            continue
        line = citation.get("line")
        snippet = citation.get("snippet")
        if isinstance(line, int) and 1 <= line <= len(lines) and isinstance(snippet, str):
            if snippet in lines[line - 1] and required in lines[line - 1] and symbol in text:
                return True
    return False


class HiddenMediumReviewTests(unittest.TestCase):
    def test_symlink_recall(self):
        finding = one_finding(load_review(), "symlink-after-validation")
        trigger = finding.get("trigger", {})
        self.assertEqual(trigger.get("kind"), "symlink-after-check")
        self.assertEqual(trigger.get("expected_outcome"), "outside-root-resolution")
        with tempfile.TemporaryDirectory() as raw:
            base = Path(raw)
            root = base / "workspace"
            outside = base / trigger.get("link_target", "")
            root.mkdir()
            outside.mkdir()
            (root / trigger.get("link_name", "")).symlink_to(outside, target_is_directory=True)
            resolved = resolve_workspace_path(root, trigger.get("requested_path", ""))
            resolved.relative_to(outside.resolve())
            with self.assertRaises(ValueError):
                resolved.relative_to(root.resolve())
        self.assertEqual(finding.get("impact_code"), "workspace-isolation-escape")

    def test_ownership_recall(self):
        finding = one_finding(load_review(), "cleanup-ownership")
        trigger = finding.get("trigger", {})
        self.assertEqual(trigger.get("kind"), "caller-label-collision")
        self.assertNotEqual(trigger.get("existing_job_id"), trigger.get("current_job_id"))
        self.assertEqual(trigger.get("caller_label"), trigger.get("existing_job_id"))
        with tempfile.TemporaryDirectory() as raw:
            runtime = Path(raw)
            victim = runtime / trigger["existing_job_id"]
            current = runtime / trigger["current_job_id"]
            victim.mkdir()
            current.mkdir()
            removed = cleanup_job(runtime, trigger["caller_label"])
            self.assertEqual(removed, victim)
            self.assertFalse(victim.exists())
            self.assertTrue(current.exists())
        self.assertEqual(finding.get("impact_code"), "cross-job-deletion")

    def test_interaction(self):
        review = load_review()
        symlink = one_finding(review, "symlink-after-validation")
        ownership = one_finding(review, "cleanup-ownership")
        expected = {
            "from_finding": symlink.get("id"),
            "to_finding": ownership.get("id"),
            "mechanism": "escaped-output-enters-shared-runtime",
            "consequence": "cross-job-data-loss",
        }
        self.assertIn(expected, review.get("relations", []))

    def test_ranking(self):
        review = load_review()
        ownership = one_finding(review, "cleanup-ownership")
        symlink = one_finding(review, "symlink-after-validation")
        self.assertEqual({ownership.get("rank"), symlink.get("rank")}, {1, 2})
        self.assertIn(ownership.get("severity"), {"high", "critical"})
        self.assertIn(symlink.get("severity"), {"high", "critical"})
        distractor_ranks = [item.get("rank") for item in review["findings"] if item.get("severity") not in BLOCKING]
        self.assertTrue(all(rank > 2 for rank in distractor_ranks))

    def test_evidence(self):
        review = load_review()
        symlink = one_finding(review, "symlink-after-validation")
        ownership = one_finding(review, "cleanup-ownership")
        self.assertTrue(evidence_resolves(symlink, "jobs/paths.py", "resolve_workspace_path", "candidate.relative_to(canonical_root)"))
        self.assertTrue(evidence_resolves(symlink, "jobs/runner.py", "finish_job", "resolve_workspace_path(workspace_root, requested_output)"))
        self.assertTrue(evidence_resolves(symlink, "change.diff", "resolve_workspace_path", "+    return candidate.resolve()"))
        self.assertTrue(evidence_resolves(ownership, "jobs/cleanup.py", "cleanup_job", "target = runtime_root / label"))
        self.assertTrue(evidence_resolves(ownership, "jobs/runner.py", "finish_job", "cleanup_job(runtime_root, caller_label)"))
        self.assertTrue(evidence_resolves(ownership, "change.diff", "cleanup_job", "+    removed = cleanup_job(runtime_root, caller_label)"))

    def test_false_positive(self):
        review = load_review()
        blocking = [item for item in review["findings"] if item.get("severity") in BLOCKING]
        self.assertEqual({item.get("category") for item in blocking}, {"symlink-after-validation", "cleanup-ownership"})
        for item in blocking:
            cited = {(citation.get("path"), citation.get("symbol")) for citation in item.get("evidence", [])}
            self.assertNotIn(("jobs/logging.py", "job_started_event"), cited)


if __name__ == "__main__":
    unittest.main()
'''


L_FILES = {
    "AGENTS.md": AGENT_INSTRUCTIONS,
    "bridge/__init__.py": '"""Provider event bridge."""\n',
    "bridge/store.py": '''from __future__ import annotations

import json
import os
from pathlib import Path
import re
import tempfile


MAX_EVENT_CHARS = 4096
TOKEN = re.compile(r"token=[A-Za-z0-9._-]+")


def redact(value: str) -> str:
    return TOKEN.sub("token=[redacted]", value)


def normalize(value: str) -> str:
    return "".join(value.splitlines())


def prepare_event(payload: str) -> str:
    redacted = redact(payload)
    normalized = normalize(redacted)
    return normalized[-MAX_EVENT_CHARS:]


def persist_event(path: Path, payload: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    state = {"event": prepare_event(payload), "status": "working"}
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


def main() -> int:
    import sys
    if len(sys.argv) != 3:
        return 2
    persist_event(Path(sys.argv[1]), sys.argv[2])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
''',
    "scripts/provider-wrapper": '''#!/usr/bin/env bash
set -euo pipefail

state_path="${1:?state path is required}"
payload="${2-}"
provider_status="${MIRA_PROVIDER_STATUS:-0}"

forward_event() {
    # Event persistence is fail-open so telemetry cannot replace the provider result.
    python3 -m bridge.store "$state_path" "$payload" || true
}

forward_event
exit "$provider_status"
''',
    "extension/world.js": '''"use strict";

function restoreWorld(persisted, nowMs) {
  const status = persisted.status || "idle";
  return {
    status,
    active: status === "working",
    ageMs: Math.max(0, nowMs - (persisted.updatedAtMs || 0)),
  };
}

module.exports = { restoreWorld };
''',
    "extension/style.css": '''/* Cosmetic layout change: it does not consume persisted event data. */
.mira-sprite {
  image-rendering: pixelated;
  inset-inline-end: 6px;
}
''',
    "scripts/cleanup.sh": '''#!/usr/bin/env bash
set -euo pipefail

cleanup_resources() {
    local resource_root="$1"
    local prefix="$2"
    local owner_id="$3"
    local candidate
    for candidate in "$resource_root"/"$prefix"*; do
        [[ -e "$candidate" ]] || continue
        rm -rf -- "$candidate"
    done
}

cleanup_resources "${1:?resource root is required}" "${2:?prefix is required}" "${3:?owner is required}"
''',
    "change.diff": '''diff --git a/scripts/provider-wrapper b/scripts/provider-wrapper
index 1000001..1000002 100755
--- a/scripts/provider-wrapper
+++ b/scripts/provider-wrapper
@@ -3,8 +3,14 @@ set -euo pipefail
 state_path="${1:?state path is required}"
-payload="${2:0:4096}"
+payload="${2-}"
 provider_status="${MIRA_PROVIDER_STATUS:-0}"
 
-python3 -m bridge.store "$state_path" "${payload//$'\\n'/ }" || true
+forward_event() {
+    # Event persistence is fail-open so telemetry cannot replace the provider result.
+    python3 -m bridge.store "$state_path" "$payload" || true
+}
+
+forward_event
 exit "$provider_status"
diff --git a/bridge/store.py b/bridge/store.py
index 2000001..2000002 100644
--- a/bridge/store.py
+++ b/bridge/store.py
@@ -14,8 +14,9 @@ def normalize(value: str) -> str:
     return "".join(value.splitlines())
 
 def prepare_event(payload: str) -> str:
-    normalized = normalize(payload)[:MAX_EVENT_CHARS]
-    return redact(normalized)
+    redacted = redact(payload)
+    normalized = normalize(redacted)
+    return normalized[-MAX_EVENT_CHARS:]
diff --git a/extension/world.js b/extension/world.js
index 3000001..3000002 100644
--- a/extension/world.js
+++ b/extension/world.js
@@ -2,8 +2,9 @@ "use strict";
 function restoreWorld(persisted, nowMs) {
-  const stale = nowMs - persisted.updatedAtMs > 300000;
-  const status = stale && persisted.status === "working" ? "idle" : persisted.status;
+  const status = persisted.status || "idle";
   return {
     status,
     active: status === "working",
+    ageMs: Math.max(0, nowMs - (persisted.updatedAtMs || 0)),
   };
 }
diff --git a/scripts/cleanup.sh b/scripts/cleanup.sh
index 4000001..4000002 100755
--- a/scripts/cleanup.sh
+++ b/scripts/cleanup.sh
@@ -6,8 +6,8 @@ cleanup_resources() {
     local prefix="$2"
     local owner_id="$3"
     local candidate
-    for candidate in "$resource_root"/"$prefix"; do
-        [[ "$(cat "$candidate/.owner")" == "$owner_id" ]] || continue
+    for candidate in "$resource_root"/"$prefix"*; do
+        [[ -e "$candidate" ]] || continue
         rm -rf -- "$candidate"
     done
 }
diff --git a/extension/style.css b/extension/style.css
index 5000001..5000002 100644
--- a/extension/style.css
+++ b/extension/style.css
@@ -1,4 +1,5 @@
+/* Cosmetic layout change: it does not consume persisted event data. */
 .mira-sprite {
   image-rendering: pixelated;
-  inset-inline-end: 4px;
+  inset-inline-end: 6px;
 }
''',
    "tests/test_store.py": '''import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from bridge.store import persist_event


WORKSPACE = Path(__file__).resolve().parents[1]


class StoreTests(unittest.TestCase):
    def test_single_line_token_is_redacted(self):
        with tempfile.TemporaryDirectory() as raw:
            path = Path(raw) / "state.json"
            persist_event(path, "phase=start token=fixture-token")
            self.assertEqual(json.loads(path.read_text(encoding="utf-8"))["event"], "phase=start token=[redacted]")

    def test_wrapper_preserves_provider_exit_status(self):
        with tempfile.TemporaryDirectory() as raw:
            path = Path(raw) / "state.json"
            environment = {
                "PATH": "/usr/local/bin:/usr/bin:/bin",
                "PYTHONPATH": str(WORKSPACE),
                "PYTHONDONTWRITEBYTECODE": "1",
                "MIRA_PROVIDER_STATUS": "7",
            }
            result = subprocess.run(
                [str(WORKSPACE / "scripts" / "provider-wrapper"), str(path), "phase=done"],
                cwd=WORKSPACE,
                env=environment,
                check=False,
            )
            self.assertEqual(result.returncode, 7)
            self.assertTrue(path.is_file())


if __name__ == "__main__":
    unittest.main()
''',
    "tests/replay-review-surface.sh": '''#!/usr/bin/env bash
set -euo pipefail

fixture_tmp="$(mktemp -d)"
trap 'rm -rf -- "$fixture_tmp"' EXIT
mkdir -p "$fixture_tmp/mira-job-7" "$fixture_tmp/other-job"
printf '%s\\n' owner-a >"$fixture_tmp/mira-job-7/.owner"
printf '%s\\n' owner-b >"$fixture_tmp/other-job/.owner"
scripts/cleanup.sh "$fixture_tmp" mira-job-7 owner-a
test ! -e "$fixture_tmp/mira-job-7"
test -d "$fixture_tmp/other-job"
''',
    "extension/test/world.test.js": '''"use strict";

const test = require("node:test");
const assert = require("node:assert/strict");
const { restoreWorld } = require("../world.js");

test("idle state remains inactive", () => {
  assert.deepEqual(restoreWorld({ status: "idle", updatedAtMs: 1000 }, 2000), {
    status: "idle",
    active: false,
    ageMs: 1000,
  });
});
''',
    "tools/validate_review.py": REVIEW_VALIDATOR,
}


L_GOOD_REVIEW = _review(
    "Three lifecycle defects expose normalized secrets, resurrect stale activity, and delete peer resources.",
    [
        {
            "id": "L-1",
            "rank": 1,
            "severity": "critical",
            "category": "redaction-order",
            "title": "Unbounded multiline input is normalized only after redaction",
            "impact_code": "credential-fragment-persisted",
            "impact": "A newline-split token survives redaction, is joined during normalization, and is persisted after tail truncation.",
            "trigger": {
                "kind": "multiline-oversized-event",
                "prefix_count": 4090,
                "secret": "fixture-secret-42",
                "separator": "newline-after-token-equals",
                "expected_persisted_fragment": "token=fixture-secret-42",
            },
            "evidence": [
                _evidence(L_FILES, "scripts/provider-wrapper", "forward_event", "python3 -m bridge.store \"$state_path\" \"$payload\""),
                _evidence(L_FILES, "bridge/store.py", "prepare_event", "redacted = redact(payload)"),
                _evidence(L_FILES, "change.diff", "prepare_event", "+    redacted = redact(payload)"),
            ],
            "remediation": {
                "strategy": "bound-normalize-then-redact",
                "constraints": ["bound-wrapper-input", "normalize-before-redact", "preserve-provider-exit"],
            },
        },
        {
            "id": "L-2",
            "rank": 2,
            "severity": "critical",
            "category": "cleanup-owner-prefix",
            "title": "Prefix cleanup removes a peer resource without checking ownership",
            "impact_code": "peer-resource-deletion",
            "impact": "A resource whose name extends the requested prefix is deleted even when its owner marker belongs to another job.",
            "trigger": {
                "kind": "peer-prefix-resource",
                "requested_resource": "mira-job-1",
                "peer_resource": "mira-job-10",
                "prefix": "mira-job-1",
                "requested_owner": "owner-a",
                "peer_owner": "owner-b",
                "expected_peer_outcome": "deleted",
            },
            "evidence": [
                _evidence(L_FILES, "scripts/cleanup.sh", "cleanup_resources", 'for candidate in "$resource_root"/"$prefix"*'),
                _evidence(L_FILES, "change.diff", "cleanup_resources", '+    for candidate in "$resource_root"/"$prefix"*'),
            ],
            "remediation": {
                "strategy": "exact-resource-and-owner-match",
                "constraints": ["exact-resource-id", "verify-owner-marker", "preserve-best-effort-cleanup"],
            },
        },
        {
            "id": "L-3",
            "rank": 3,
            "severity": "high",
            "category": "stale-restart",
            "title": "Restart restores an expired working state as active",
            "impact_code": "stale-active-render",
            "impact": "A two-hour-old transient working state is rendered active after extension restart instead of expiring to idle.",
            "trigger": {
                "kind": "restart-with-stale-transient",
                "persisted_status": "working",
                "updated_at_ms": 0,
                "restart_at_ms": 7200000,
                "max_transient_age_ms": 300000,
                "expected_safe_status": "idle",
            },
            "evidence": [
                _evidence(L_FILES, "extension/world.js", "restoreWorld", 'active: status === "working"'),
                _evidence(L_FILES, "change.diff", "restoreWorld", '+  const status = persisted.status || "idle";'),
            ],
            "remediation": {
                "strategy": "expire-transient-on-restore",
                "constraints": ["age-check-on-restart", "working-expires-to-idle", "preserve-nontransient-state"],
            },
        },
    ],
    relations=[
        {"from_finding": "L-1", "to_finding": "L-3", "mechanism": "persisted-event-replayed-after-restart", "consequence": "unsafe-state-survives-process-boundary"},
        {"from_finding": "L-3", "to_finding": "L-2", "mechanism": "stale-lifecycle-loses-current-owner", "consequence": "peer-resource-deletion"},
    ],
    lifecycle={
        "stages": ["input", "persistence", "restart", "render", "cleanup", "ownership"],
        "coverage": [
            {"finding_id": "L-1", "boundaries": ["input", "persistence"]},
            {"finding_id": "L-3", "boundaries": ["restart", "render"]},
            {"finding_id": "L-2", "boundaries": ["cleanup", "ownership"]},
        ],
    },
)

L_GOOD = {"review.json": _json_file(L_GOOD_REVIEW)}

L_PYTHON_ONLY = copy.deepcopy(L_GOOD_REVIEW)
L_PYTHON_ONLY["findings"][0]["evidence"] = [
    citation for citation in L_PYTHON_ONLY["findings"][0]["evidence"] if citation["path"] != "scripts/provider-wrapper"
]

L_STALE_WITHOUT_RESTART = copy.deepcopy(L_GOOD_REVIEW)
L_STALE_WITHOUT_RESTART["findings"][2]["trigger"]["restart_at_ms"] = 1000

L_CLEANUP_WITHOUT_PEER = copy.deepcopy(L_GOOD_REVIEW)
L_CLEANUP_WITHOUT_PEER["findings"][1]["trigger"]["peer_resource"] = "other-job"

L_CSS_FALSE_POSITIVE = copy.deepcopy(L_GOOD_REVIEW)
L_CSS_FALSE_POSITIVE["findings"].append(
    {
        "id": "L-X1",
        "rank": 4,
        "severity": "high",
        "category": "css-lifecycle-blocker",
        "title": "Pixel rendering prevents safe cleanup",
        "impact_code": "unsupported-ui-blocker",
        "impact": "The review promotes a cosmetic inset change to a lifecycle blocker.",
        "trigger": {"kind": "css-position", "property": "inset-inline-end", "value": "6px"},
        "evidence": [_evidence(L_FILES, "extension/style.css", "mira-sprite", "inset-inline-end: 6px")],
        "remediation": {"strategy": "revert-css", "constraints": ["keep-four-pixels"]},
    }
)


L_HIDDEN = r'''from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

from bridge.store import persist_event


WORKSPACE = Path(os.environ["DURATION_FIXTURE_WORKSPACE"])
BLOCKING = {"medium", "high", "critical"}


def assert_review_only() -> None:
    completed = subprocess.run(
        ["git", "status", "--porcelain=v1", "--untracked-files=all"],
        cwd=WORKSPACE,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if completed.returncode != 0 or completed.stdout.splitlines() != ["?? review.json"]:
        raise AssertionError("review task modified fixture files or created extra artifacts")


def load_review() -> dict:
    assert_review_only()
    value = json.loads((WORKSPACE / "review.json").read_text(encoding="utf-8"))
    if not isinstance(value, dict) or not isinstance(value.get("findings"), list):
        raise AssertionError("invalid review")
    return value


def one_finding(review: dict, category: str) -> dict:
    matched = [item for item in review["findings"] if item.get("category") == category]
    if len(matched) != 1:
        raise AssertionError(f"expected exactly one {category} finding")
    return matched[0]


def evidence_resolves(finding: dict, path: str, symbol: str, required: str) -> bool:
    source = WORKSPACE / path
    if not source.is_file():
        return False
    text = source.read_text(encoding="utf-8")
    lines = text.splitlines()
    for citation in finding.get("evidence", []):
        if citation.get("path") != path or citation.get("symbol") != symbol:
            continue
        line = citation.get("line")
        snippet = citation.get("snippet")
        if isinstance(line, int) and 1 <= line <= len(lines) and isinstance(snippet, str):
            if snippet in lines[line - 1] and required in lines[line - 1] and symbol in text:
                return True
    return False


class HiddenLargeReviewTests(unittest.TestCase):
    def test_redaction_order(self):
        finding = one_finding(load_review(), "redaction-order")
        trigger = finding.get("trigger", {})
        self.assertEqual(trigger.get("kind"), "multiline-oversized-event")
        self.assertEqual(trigger.get("separator"), "newline-after-token-equals")
        prefix_count = trigger.get("prefix_count")
        secret = trigger.get("secret")
        self.assertIsInstance(prefix_count, int)
        self.assertGreater(prefix_count, 4000)
        self.assertIsInstance(secret, str)
        payload = "x" * prefix_count + "token=\n" + secret
        self.assertGreater(len(payload), 4096)
        with tempfile.TemporaryDirectory() as raw:
            path = Path(raw) / "state.json"
            persist_event(path, payload)
            persisted = json.loads(path.read_text(encoding="utf-8"))["event"]
        fragment = trigger.get("expected_persisted_fragment")
        self.assertEqual(fragment, "token=" + secret)
        self.assertIn(fragment, persisted)
        self.assertTrue(evidence_resolves(finding, "scripts/provider-wrapper", "forward_event", "python3 -m bridge.store"))
        constraints = set(finding.get("remediation", {}).get("constraints", []))
        self.assertTrue({"bound-wrapper-input", "normalize-before-redact", "preserve-provider-exit"}.issubset(constraints))

    def test_stale_restart(self):
        finding = one_finding(load_review(), "stale-restart")
        trigger = finding.get("trigger", {})
        self.assertEqual(trigger.get("kind"), "restart-with-stale-transient")
        age = trigger.get("restart_at_ms", 0) - trigger.get("updated_at_ms", 0)
        self.assertGreater(age, trigger.get("max_transient_age_ms", age))
        script = (
            "const world=require(process.argv[1]);"
            "const t=JSON.parse(process.argv[2]);"
            "console.log(JSON.stringify(world.restoreWorld({status:t.persisted_status,updatedAtMs:t.updated_at_ms},t.restart_at_ms)));"
        )
        completed = subprocess.run(
            ["node", "-e", script, str(WORKSPACE / "extension" / "world.js"), json.dumps(trigger)],
            cwd=WORKSPACE,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        restored = json.loads(completed.stdout)
        self.assertEqual((restored.get("status"), restored.get("active")), ("working", True))
        self.assertEqual(trigger.get("expected_safe_status"), "idle")
        self.assertEqual(finding.get("impact_code"), "stale-active-render")

    def test_cleanup_owner(self):
        finding = one_finding(load_review(), "cleanup-owner-prefix")
        trigger = finding.get("trigger", {})
        self.assertEqual(trigger.get("kind"), "peer-prefix-resource")
        self.assertNotEqual(trigger.get("requested_owner"), trigger.get("peer_owner"))
        self.assertTrue(trigger.get("peer_resource", "").startswith(trigger.get("prefix", "")))
        self.assertNotEqual(trigger.get("peer_resource"), trigger.get("requested_resource"))
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            requested = root / trigger["requested_resource"]
            peer = root / trigger["peer_resource"]
            requested.mkdir()
            peer.mkdir()
            (requested / ".owner").write_text(trigger["requested_owner"], encoding="utf-8")
            (peer / ".owner").write_text(trigger["peer_owner"], encoding="utf-8")
            completed = subprocess.run(
                [str(WORKSPACE / "scripts" / "cleanup.sh"), str(root), trigger["prefix"], trigger["requested_owner"]],
                cwd=WORKSPACE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )
            self.assertEqual(completed.returncode, 0)
            self.assertFalse(requested.exists())
            self.assertFalse(peer.exists())
        self.assertEqual(trigger.get("expected_peer_outcome"), "deleted")
        self.assertEqual(finding.get("impact_code"), "peer-resource-deletion")

    def test_lifecycle_model(self):
        review = load_review()
        redaction = one_finding(review, "redaction-order")
        stale = one_finding(review, "stale-restart")
        cleanup = one_finding(review, "cleanup-owner-prefix")
        lifecycle = review.get("lifecycle", {})
        self.assertEqual(
            lifecycle.get("stages"),
            ["input", "persistence", "restart", "render", "cleanup", "ownership"],
        )
        coverage = lifecycle.get("coverage", [])
        self.assertIn({"finding_id": redaction["id"], "boundaries": ["input", "persistence"]}, coverage)
        self.assertIn({"finding_id": stale["id"], "boundaries": ["restart", "render"]}, coverage)
        self.assertIn({"finding_id": cleanup["id"], "boundaries": ["cleanup", "ownership"]}, coverage)
        relations = review.get("relations", [])
        self.assertIn(
            {"from_finding": redaction["id"], "to_finding": stale["id"], "mechanism": "persisted-event-replayed-after-restart", "consequence": "unsafe-state-survives-process-boundary"},
            relations,
        )

    def test_ranking_impact(self):
        review = load_review()
        redaction = one_finding(review, "redaction-order")
        cleanup = one_finding(review, "cleanup-owner-prefix")
        stale = one_finding(review, "stale-restart")
        self.assertEqual({redaction.get("rank"), cleanup.get("rank"), stale.get("rank")}, {1, 2, 3})
        self.assertTrue(
            all(
                finding.get("severity") in {"high", "critical"}
                for finding in (redaction, cleanup, stale)
            )
        )
        self.assertEqual(
            {redaction.get("impact_code"), cleanup.get("impact_code"), stale.get("impact_code")},
            {"credential-fragment-persisted", "peer-resource-deletion", "stale-active-render"},
        )

    def test_evidence_integrity(self):
        review = load_review()
        redaction = one_finding(review, "redaction-order")
        cleanup = one_finding(review, "cleanup-owner-prefix")
        stale = one_finding(review, "stale-restart")
        self.assertTrue(evidence_resolves(redaction, "scripts/provider-wrapper", "forward_event", "python3 -m bridge.store"))
        self.assertTrue(evidence_resolves(redaction, "bridge/store.py", "prepare_event", "redacted = redact(payload)"))
        self.assertTrue(evidence_resolves(redaction, "change.diff", "prepare_event", "+    redacted = redact(payload)"))
        self.assertTrue(evidence_resolves(stale, "extension/world.js", "restoreWorld", 'active: status === "working"'))
        self.assertTrue(evidence_resolves(stale, "change.diff", "restoreWorld", '+  const status = persisted.status || "idle";'))
        self.assertTrue(evidence_resolves(cleanup, "scripts/cleanup.sh", "cleanup_resources", 'for candidate in "$resource_root"/"$prefix"*'))
        self.assertTrue(evidence_resolves(cleanup, "change.diff", "cleanup_resources", '+    for candidate in "$resource_root"/"$prefix"*'))

    def test_false_positive(self):
        review = load_review()
        blocking = [item for item in review["findings"] if item.get("severity") in BLOCKING]
        self.assertEqual(
            {item.get("category") for item in blocking},
            {"redaction-order", "stale-restart", "cleanup-owner-prefix"},
        )
        for finding in blocking:
            cited_paths = {citation.get("path") for citation in finding.get("evidence", [])}
            self.assertNotIn("extension/style.css", cited_paths)


if __name__ == "__main__":
    unittest.main()
'''


RECIPES: dict[str, dict[str, Any]] = {
    "f02-s-python-path-review-v1": {
        "case_id": "F02-S-PY-001",
        "files": S_FILES,
        "hidden": S_HIDDEN,
        "good": S_GOOD,
        "executable": [],
        "mutants": {
            "advice-without-bypass": {
                "files": {"review.json": _json_file(S_ADVICE_ONLY)},
                "expected_failed_check_ids": ["review-trigger-valid"],
            },
            "safe-resolve-false-positive": {
                "files": {"review.json": _json_file(S_SAFE_RESOLVE)},
                "expected_failed_check_ids": ["review-seeded-recall", "review-false-positive"],
            },
            "style-only": {
                "files": {"review.json": _json_file(S_LOW_STYLE)},
                "expected_failed_check_ids": ["review-seeded-recall", "review-impact-severity"],
            },
        },
    },
    "f02-m-python-isolation-review-v1": {
        "case_id": "F02-M-PY-001",
        "files": M_FILES,
        "hidden": M_HIDDEN,
        "good": M_GOOD,
        "executable": [],
        "mutants": {
            "symlink-only": {
                "files": {"review.json": _json_file(M_SYMLINK_ONLY)},
                "expected_failed_check_ids": ["review-ownership-recall", "review-interaction"],
            },
            "two-findings-no-interaction": {
                "files": {"review.json": _json_file(M_NO_INTERACTION)},
                "expected_failed_check_ids": ["review-interaction"],
            },
            "logging-false-positive": {
                "files": {"review.json": _json_file(M_LOGGING_FALSE_POSITIVE)},
                "expected_failed_check_ids": ["review-false-positive"],
            },
        },
    },
    "f02-l-hook-lifecycle-review-v1": {
        "case_id": "F02-L-PYBASHJS-001",
        "files": L_FILES,
        "hidden": L_HIDDEN,
        "good": L_GOOD,
        "executable": ["scripts/provider-wrapper", "scripts/cleanup.sh", "tests/replay-review-surface.sh"],
        "mutants": {
            "python-only-redaction": {
                "files": {"review.json": _json_file(L_PYTHON_ONLY)},
                "expected_failed_check_ids": ["review-redaction-order", "review-evidence-integrity"],
            },
            "stale-without-restart": {
                "files": {"review.json": _json_file(L_STALE_WITHOUT_RESTART)},
                "expected_failed_check_ids": ["review-stale-restart"],
            },
            "cleanup-without-peer-prefix": {
                "files": {"review.json": _json_file(L_CLEANUP_WITHOUT_PEER)},
                "expected_failed_check_ids": ["review-cleanup-owner"],
            },
            "css-false-positive": {
                "files": {"review.json": _json_file(L_CSS_FALSE_POSITIVE)},
                "expected_failed_check_ids": ["review-false-positive"],
            },
        },
    },
}


__all__ = ["RECIPES"]
