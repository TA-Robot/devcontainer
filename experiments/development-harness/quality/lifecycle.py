#!/usr/bin/env python3
"""Requirement-level lifecycle quality observations, separate from cycle-002 scores.

Run against an immutable export in a credential-free evaluation container.
This covers concrete behavior, not overall usability or maintainability.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import runpy
import shutil
import stat
import subprocess
import tempfile
import time

SHARED_PATH = Path(__file__).resolve().parents[1] / 'multi-scale/large-01/evaluate.py'
SHARED = runpy.run_path(str(SHARED_PATH))
require, tree, Scenario = (SHARED[name] for name in ('require', 'tree', 'Scenario'))


def private_mode_adoption(s):
    shutil.copytree(s.source, s.target, dirs_exist_ok=True)
    local = s.target / 'settings.txt'
    local.chmod(0o600)
    before = tree(s.target)
    s.call('adopt', '--source', s.source, '--target', s.target)
    require({k: v for k, v in tree(s.target).items() if not k.startswith('.agent-project')}
            == before, 'adoption changed existing project bytes, modes or inventory')
    require(s.call('adopt', '--source', s.source, '--target', s.target).get('status') == 'noop',
            'repeated adoption was not a no-op')
    (s.source / 'settings.txt').write_text('updated upstream\n')
    s.apply()
    require(local.read_text() == 'updated upstream\n', 'adopted file did not update')
    require(stat.S_IMODE(local.stat().st_mode) == 0o600, 'update loosened local permissions')


def overlapping_roots(s):
    nested = s.source / 'nested'
    nested.mkdir()
    before = tree(s.root)
    for target in ('/', '//' + str(s.source).lstrip('/'), '//' + str(nested).lstrip('/')):
        # Plan only, never apply against the filesystem root.
        result = s.call('plan', '--source', s.source, '--target', target, ok=False)
        require(result.returncode != 0, 'planning accepted overlapping source and target roots')
        require(tree(s.root) == before, 'rejected plan changed project files')


def private_metadata_exclusion(s):
    env = {**os.environ, 'GIT_CONFIG_GLOBAL': '/dev/null', 'GIT_CONFIG_NOSYSTEM': '1'}
    subprocess.run(['git', 'init', '-q', str(s.target)], env=env, check=True,
                   capture_output=True, timeout=15)
    ignore = s.target / '.gitignore'
    ignore.write_text('user-owned-pattern\n')
    before_git = tree(s.target / '.git')
    s.install()
    require(ignore.read_text() == 'user-owned-pattern\n', 'project ignore rules changed')
    require(tree(s.target / '.git') == before_git, 'project Git metadata changed')
    output = subprocess.check_output(
        ['git', '-C', str(s.target), 'status', '--porcelain', '--untracked-files=all'],
        env=env, text=True, timeout=15)
    require(not any(row[3:].startswith('.agent-project/') for row in output.splitlines()),
            'private lifecycle data is visible in ordinary Git changes')
    require('settings.txt' in output, 'project files were hidden with private metadata')


SUPPLEMENTAL = {
    'private-mode-adoption': private_mode_adoption,
    'overlapping-roots': overlapping_roots,
    'private-metadata-exclusion': private_metadata_exclusion,
}

# Requirements are grouped by user outcome; more tests do not create more points.
# Guards are task-local adoption constraints, owned by the primary/integrator.
REQUIREMENTS = (
    ('installation', 'correctness', False,
     ('install-bytes-modes-dotpaths', 'native-template-validation')),
    ('read-only-and-repeatability', 'correctness', False,
     ('repeat-noop', 'status-readonly')),
    ('safe-updates', 'preservation', True,
     ('existing-unmanaged-conflict', 'identical-unmanaged-conflict', 'upstream-update',
      'local-preserved', 'overlapping-conflict', 'managed-deletion', 'dirty-deletion-conflict',
      'text-merge-and-third-update', 'binary-conflict', 'unrelated-edit-kept')),
    ('plan-preconditions', 'preservation', True,
     ('stale-target', 'stale-source', 'mode-precondition', 'plan-traversal',
      'plan-absolute', 'plan-duplicate')),
    ('path-boundaries', 'preservation', True,
     ('reserved-.git', 'reserved-.agent-project', 'symlink-source', 'symlink-target',
      'symlink-metadata', 'overlapping-roots')),
    ('matching-adoption', 'correctness', False,
     ('explicit-adoption', 'adoption-mismatch', 'private-mode-adoption')),
    ('recovery-and-rollback', 'resilience', True,
     ('crash-recovery', 'post-crash-user-edit', 'rollback', 'post-update-user-edit',
      'corrupt-ownership-metadata', 'stale-and-unsafe-rollback', 'concurrent-apply')),
    ('git-workflow', 'operability', False,
     ('target-git-preserved', 'private-metadata-exclusion')),
)


def summarize(checks):
    by_name = {check['name']: check for check in checks}
    if len(by_name) != len(checks):
        raise ValueError('duplicate observation identity')
    expected = {name for _, _, _, names in REQUIREMENTS for name in names}
    if set(by_name) - expected:
        raise ValueError('unmapped observation')
    rows = []
    for identifier, dimension, guard, names in REQUIREMENTS:
        states = [by_name.get(name, {}).get('status', 'unknown') for name in names]
        if any(state not in ('passed', 'failed', 'unknown') for state in states):
            raise ValueError('invalid observation status')
        status = 'failed' if 'failed' in states else 'unknown' if 'unknown' in states else 'passed'
        rows.append({'id': identifier, 'dimension': dimension, 'hard_guard': guard,
                     'status': status, 'observations': list(names)})
    return rows


def observe(name, action, candidate):
    started = time.monotonic()
    with tempfile.TemporaryDirectory(prefix='lifecycle-quality-') as raw:
        try:
            action(Scenario(Path(raw), candidate))
            status, detail = 'passed', None
        except AssertionError as error:
            status, detail = 'failed', str(error)[-1000:]
        except Exception as error:
            # Infrastructure/observer errors are not evidence of bad candidate quality.
            status, detail = 'unknown', f'{type(error).__name__}: {error}'[-1000:]
    return {'name': name, 'status': status, 'detail': detail,
            'evaluation_seconds': round(time.monotonic() - started, 3)}


def evaluate(candidate):
    before = tree(candidate)
    actions = dict(SHARED['scenarios'](3))
    actions.update(SUPPLEMENTAL)
    checks = [observe(name, action, candidate) for name, action in actions.items()]
    unchanged = before == tree(candidate)
    if not unchanged:
        for check in checks:
            check['status'] = 'unknown'
            check['detail'] = 'candidate source changed during evaluation'
    requirements = summarize(checks)
    return {
        'schema_version': 1, 'assessment': 'lifecycle-quality-v1',
        'purpose': 'new assessment calibration; not a replacement for cycle-002 fixed scores',
        'source_unchanged': unchanged,
        'candidate_tree_sha256': hashlib.sha256(json.dumps(before, sort_keys=True, separators=(',', ':')).encode()).hexdigest(),
        'evaluator_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'shared_evaluator_sha256': hashlib.sha256(SHARED_PATH.read_bytes()).hexdigest(),
        'measurement_complete': unchanged and all(c['status'] != 'unknown' for c in checks),
        'requirements': requirements, 'checks': checks,
        'unmeasured': ['guided first-use success and human effort',
                       'controlled follow-up development effort and maintainability',
                       'installed-image behavior; run release checks separately'],
        'overall_quality_score': None,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--candidate', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    candidate, output = args.candidate.resolve(), args.output.resolve()
    if output == candidate or candidate in output.parents:
        parser.error('output must be outside the immutable candidate')
    result = evaluate(candidate)
    output.write_text(json.dumps(result, indent=2, ensure_ascii=False, allow_nan=False) + '\n')
    print(json.dumps({k: result[k] for k in ('measurement_complete', 'requirements', 'unmeasured')}, indent=2))
    # Successful measurement may report candidate failures; never equate exit 0 to acceptance.
    return 0 if result['measurement_complete'] else 2


if __name__ == '__main__':
    raise SystemExit(main())
