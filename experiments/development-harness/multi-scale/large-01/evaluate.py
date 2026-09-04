#!/usr/bin/env python3
"""Independent CLI acceptance; run with immutable candidate source, no provider.

Every scenario observes target bytes/modes or externally visible behavior.
The candidate's JSON is an interface, never the quality oracle.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import stat
import subprocess
import tempfile
import time


def tree(root: Path) -> dict:
    result = {}
    for path in sorted(root.rglob('*')):
        relative = str(path.relative_to(root))
        mode = path.lstat().st_mode
        if stat.S_ISLNK(mode):
            result[relative] = ('link', os.readlink(path))
        elif stat.S_ISREG(mode):
            result[relative] = ('file', stat.S_IMODE(mode), hashlib.sha256(path.read_bytes()).hexdigest())
        elif stat.S_ISDIR(mode):
            result[relative] = ('directory', stat.S_IMODE(mode))
        else:
            result[relative] = ('special', mode)
    return result


def require(value, detail):
    if not value:
        raise AssertionError(detail)


class Scenario:
    def __init__(self, root, candidate):
        self.root = root
        self.candidate = candidate
        self.cli = candidate / 'scripts/manage-agent-project'
        self.source = root / 'source'
        self.target = root / 'target'
        self.source.mkdir()
        self.target.mkdir()
        (self.source / 'settings.txt').write_text('first=base\nmiddle=stable\nlast=base\n')
        (self.source / '.agent').mkdir()
        (self.source / '.agent/data.bin').write_bytes(b'\x00\xff\x80binary\n')
        (self.source / 'space 日本.txt').write_text('template text\n')
        script = self.source / 'run.sh'
        script.write_text('#!/bin/sh\nexit 0\n')
        script.chmod(0o755)
        (self.target / 'user-notes.txt').write_text('user content\n')
        self.counter = 0

    def call(self, *args, env=None, ok=True):
        require(self.cli.is_file(), 'required CLI is absent')
        require(os.access(self.cli, os.X_OK), 'CLI is not executable')
        process = subprocess.run([str(self.cli), *map(str, args), '--json'], cwd=self.root,
                                 env={**os.environ, 'PYTHONDONTWRITEBYTECODE': '1', **(env or {})},
                                 text=True, capture_output=True, timeout=20)
        if ok:
            require(process.returncode == 0, f'CLI failed: {process.stderr[-500:]}')
            return json.loads(process.stdout)
        return process

    def plan(self):
        before = tree(self.target)
        plan = self.call('plan', '--source', self.source, '--target', self.target)
        require(tree(self.target) == before, 'planning changed target state')
        require(plan.get('schema_version') == 1, 'plan schema missing')
        require(plan.get('status') in ('ready', 'conflict'), 'plan status invalid')
        actions = plan.get('actions')
        require(isinstance(actions, list) and all(isinstance(a, dict) for a in actions), 'actions absent')
        paths = [a.get('path') for a in actions]
        require(len(paths) == len(set(paths)), 'duplicate planned paths')
        self.counter += 1
        path = self.root / f'plan-{self.counter}.json'
        path.write_text(json.dumps(plan))
        return path

    def apply(self, plan=None, **kwargs):
        return self.call('apply', '--target', self.target, '--plan', plan or self.plan(), **kwargs)

    def install(self):
        result = self.apply()
        require(result.get('status') == 'applied', 'initial installation was not applied')
        require(isinstance(result.get('transaction_id'), str), 'transaction identity missing')
        require((self.target / '.agent-project').is_dir(), 'ownership metadata missing')
        for source in self.source.rglob('*'):
            if source.is_file():
                target = self.target / source.relative_to(self.source)
                require(target.read_bytes() == source.read_bytes(), 'installed bytes differ')
                require(stat.S_IMODE(target.stat().st_mode) == stat.S_IMODE(source.stat().st_mode), 'installed mode differs')
        require((self.target / 'user-notes.txt').read_text() == 'user content\n', 'unrelated file damaged')
        return result

    def rejected_unchanged(self, action):
        before = tree(self.target)
        response = action()
        require(response.returncode != 0, 'unsafe operation returned success')
        require(tree(self.target) == before, 'rejected operation modified target')


def install(s):
    s.install()


def noop(s):
    s.install()
    before = tree(s.target)
    result = s.apply()
    require(result.get('status') == 'noop', 'repeat installation is not a no-op')
    require(tree(s.target) == before, 'no-op rewrote target state')


def existing_conflict(s):
    (s.target / 'settings.txt').write_text('pre-existing user settings\n')
    plan = s.plan()
    s.rejected_unchanged(lambda: s.apply(plan, ok=False))


def identical_unmanaged(s):
    (s.target / 'settings.txt').write_bytes((s.source / 'settings.txt').read_bytes())
    plan = s.plan()
    s.rejected_unchanged(lambda: s.apply(plan, ok=False))


def upstream_update(s):
    s.install()
    (s.source / 'settings.txt').write_text('upstream replacement\n')
    s.apply()
    require((s.target / 'settings.txt').read_text() == 'upstream replacement\n', 'upstream update missing')


def local_preserved(s):
    s.install()
    (s.target / 'settings.txt').write_text('local customization\n')
    s.apply()
    require((s.target / 'settings.txt').read_text() == 'local customization\n', 'local customization lost')


def overlapping_conflict(s):
    s.install()
    (s.target / 'settings.txt').write_text('local=one\n')
    (s.source / 'settings.txt').write_text('upstream=two\n')
    plan = s.plan()
    s.rejected_unchanged(lambda: s.apply(plan, ok=False))


def deletion(s):
    s.install()
    (s.source / 'settings.txt').unlink()
    s.apply()
    require(not (s.target / 'settings.txt').exists(), 'managed deletion not applied')
    require((s.target / 'user-notes.txt').is_file(), 'unmanaged file removed')


def dirty_deletion(s):
    s.install()
    (s.target / 'settings.txt').write_text('local change\n')
    (s.source / 'settings.txt').unlink()
    plan = s.plan()
    s.rejected_unchanged(lambda: s.apply(plan, ok=False))


def stale_target(s):
    plan = s.plan()
    (s.target / 'settings.txt').write_text('created after planning\n')
    s.rejected_unchanged(lambda: s.apply(plan, ok=False))


def stale_source(s):
    plan = s.plan()
    (s.source / 'settings.txt').write_text('source changed after planning\n')
    s.rejected_unchanged(lambda: s.apply(plan, ok=False))


def plan_attack(s, kind):
    plan = s.plan()
    payload = json.loads(plan.read_text())
    if kind == 'duplicate':
        payload['actions'].append(dict(payload['actions'][0]))
    else:
        payload['actions'][0]['path'] = '../outside' if kind == 'traversal' else str(s.root / 'outside')
    outside = s.root / 'outside'
    outside.write_text('must survive\n')
    plan.write_text(json.dumps(payload))
    s.rejected_unchanged(lambda: s.apply(plan, ok=False))
    require(outside.read_text() == 'must survive\n', 'plan escaped target')


def symlink(s, where):
    outside = s.root / 'outside'
    outside.mkdir()
    (outside / 'sentinel').write_text('private\n')
    if where == 'source':
        (s.source / 'link').symlink_to(outside, target_is_directory=True)
    elif where == 'metadata':
        (s.target / '.agent-project').symlink_to(outside, target_is_directory=True)
    else:
        (s.target / '.agent').symlink_to(outside, target_is_directory=True)
    before = tree(s.target)
    response = s.call('plan', '--source', s.source, '--target', s.target, ok=False)
    if response.returncode == 0:
        plan = s.root / 'unsafe.json'
        plan.write_text(response.stdout)
        s.rejected_unchanged(lambda: s.apply(plan, ok=False))
    require(tree(s.target) == before, 'symlink refusal changed target')
    require(tree(outside) == {'sentinel': ('file', stat.S_IMODE((outside / 'sentinel').stat().st_mode), hashlib.sha256(b'private\n').hexdigest())}, 'outside symlink destination modified')


def status_readonly(s):
    s.install()
    before = tree(s.target)
    report = s.call('status', '--target', s.target)
    expected = sorted(str(p.relative_to(s.source)) for p in s.source.rglob('*') if p.is_file())
    require(report.get('managed_paths') == expected, 'managed inventory differs')
    require(tree(s.target) == before, 'status mutated state')


def reserved_source(s, reserved):
    (s.source / reserved).mkdir()
    (s.source / reserved / 'state').write_text('untrusted ownership\n')
    before = tree(s.target)
    response = s.call('plan', '--source', s.source, '--target', s.target, ok=False)
    if response.returncode == 0:
        plan = s.root / 'reserved.json'
        plan.write_text(response.stdout)
        s.rejected_unchanged(lambda: s.apply(plan, ok=False))
    require(tree(s.target) == before, 'reserved source modified target')


def native_template(s):
    import shutil
    shutil.rmtree(s.source)
    shutil.copytree(s.candidate / 'project', s.source)
    s.install()
    result = subprocess.run([os.environ.get('PYTHON', 'python3'),
                             str(s.candidate / 'scripts/validate-agent-contracts.py'),
                             '--template-root', str(s.target)],
                            env={**os.environ, 'PYTHONDONTWRITEBYTECODE': '1'},
                            cwd=s.candidate, text=True, capture_output=True, timeout=60)
    require(result.returncode == 0, f'installed native contract validation failed: {result.stderr[-500:]}')


def git_preserved(s):
    subprocess.run(['git', 'init', '-q', str(s.target)], check=True)
    before = tree(s.target / '.git')
    s.install()
    require(tree(s.target / '.git') == before, 'target Git metadata changed')


def text_merge(s):
    s.install()
    (s.target / 'settings.txt').write_text('first=local\nmiddle=stable\nlast=base\n')
    (s.source / 'settings.txt').write_text('first=base\nmiddle=stable\nlast=upstream\n')
    s.apply()
    require((s.target / 'settings.txt').read_text() == 'first=local\nmiddle=stable\nlast=upstream\n', 'non-overlapping changes not both retained')
    (s.source / 'settings.txt').write_text('first=base\nmiddle=new\nlast=upstream\n')
    s.apply()
    require((s.target / 'settings.txt').read_text() == 'first=local\nmiddle=new\nlast=upstream\n', 'third-version update lost local edit')


def binary_conflict(s):
    s.install()
    (s.target / '.agent/data.bin').write_bytes(b'\x00local')
    (s.source / '.agent/data.bin').write_bytes(b'\x00upstream')
    plan = s.plan()
    s.rejected_unchanged(lambda: s.apply(plan, ok=False))


def adoption(s, mismatch=False):
    import shutil
    shutil.copytree(s.source, s.target, dirs_exist_ok=True)
    if mismatch:
        (s.target / 'settings.txt').write_text('customized before adoption\n')
        s.rejected_unchanged(lambda: s.call('adopt', '--source', s.source, '--target', s.target, ok=False))
    else:
        s.call('adopt', '--source', s.source, '--target', s.target)
        require(s.call('adopt', '--source', s.source, '--target', s.target).get('status') == 'noop', 'repeat adoption not a no-op')
        (s.source / 'settings.txt').write_text('adopted upstream update\n')
        s.apply()
        require((s.target / 'settings.txt').read_text() == 'adopted upstream update\n', 'adopted file not updatable')


def unrelated_change(s):
    s.install()
    (s.source / 'settings.txt').write_text('upstream\n')
    plan = s.plan()
    (s.target / 'user-notes.txt').write_text('intervening unrelated edit\n')
    s.apply(plan)
    require((s.target / 'user-notes.txt').read_text() == 'intervening unrelated edit\n', 'unrelated edit lost')
    require((s.target / 'settings.txt').read_text() == 'upstream\n', 'safe update rejected')


def mode_stale(s):
    s.install()
    (s.source / 'run.sh').write_text('#!/bin/sh\nexit 1\n')
    plan = s.plan()
    (s.target / 'run.sh').chmod(0o644)
    s.rejected_unchanged(lambda: s.apply(plan, ok=False))


def crash_recover(s, local_after=False):
    s.install()
    original = {p: (s.target / p).read_bytes() for p in ('settings.txt', 'space 日本.txt')}
    for path in original:
        (s.source / path).write_text('updated in transaction\n')
    plan = s.plan()
    response = s.apply(plan, env={'AGENT_PROJECT_TEST_CRASH_AFTER_REPLACE': '1'}, ok=False)
    require(response.returncode == 99, 'crash failpoint did not terminate at requested boundary')
    require(any((s.target / p).read_bytes() != old for p, old in original.items()), 'crash occurred before any actual replacement')
    report = s.call('status', '--target', s.target)
    require(isinstance(report.get('pending_transaction'), str), 'pending transaction not visible')
    s.rejected_unchanged(lambda: s.apply(plan, ok=False))
    if local_after:
        changed = next(p for p, old in original.items() if (s.target / p).read_bytes() != old)
        (s.target / changed).write_text('user edit after crash\n')
        s.rejected_unchanged(lambda: s.call('recover', '--target', s.target, ok=False))
    else:
        (s.target / 'user-notes.txt').write_text('unrelated during outage\n')
        s.call('recover', '--target', s.target)
        require(all((s.target / p).read_bytes() == old for p, old in original.items()), 'recovery did not restore before-images')
        require(s.call('status', '--target', s.target).get('pending_transaction') is None, 'recovery still pending')
        require(s.call('recover', '--target', s.target).get('status') == 'noop', 'repeat recovery not a no-op')
        require((s.target / 'user-notes.txt').read_text() == 'unrelated during outage\n', 'recovery overwrote unrelated edit')
        s.apply()
        require(all((s.target / p).read_text() == 'updated in transaction\n' for p in original), 'normal update fails after recovery')


def rollback(s, local_after=False):
    s.install()
    original = (s.target / 'settings.txt').read_bytes()
    (s.source / 'settings.txt').write_text('upstream\n')
    (s.source / 'space 日本.txt').write_text('another upstream change\n')
    result = s.apply()
    transaction = result['transaction_id']
    if local_after:
        (s.target / 'space 日本.txt').write_text('user edit after update\n')
        s.rejected_unchanged(lambda: s.call('rollback', '--target', s.target, '--transaction', transaction, ok=False))
    else:
        s.call('rollback', '--target', s.target, '--transaction', transaction)
        require((s.target / 'settings.txt').read_bytes() == original, 'rollback did not restore previous data')
        require(s.call('rollback', '--target', s.target, '--transaction', transaction).get('status') == 'noop', 'repeat rollback not a no-op')


def corrupt_metadata(s):
    s.install()
    files = [p for p in (s.target / '.agent-project').rglob('*') if p.is_file() and not p.is_symlink()]
    require(files, 'persistent ownership state absent')
    for path in files:
        path.write_bytes(b'corrupt-state\x00')
    s.rejected_unchanged(lambda: s.call('plan', '--source', s.source, '--target', s.target, ok=False))


def stale_rollback(s):
    first = s.install()['transaction_id']
    (s.source / 'settings.txt').write_text('newer transaction\n')
    s.apply()
    s.rejected_unchanged(lambda: s.call('rollback', '--target', s.target, '--transaction', first, ok=False))
    for transaction in ('../outside', '/tmp/outside', 'unknown-id'):
        s.rejected_unchanged(lambda t=transaction: s.call('rollback', '--target', s.target, '--transaction', t, ok=False))


def concurrent_apply(s):
    plan = s.plan()
    argv = [str(s.cli), 'apply', '--target', str(s.target), '--plan', str(plan), '--json']
    processes = []
    try:
        for _ in range(2):
            processes.append(subprocess.Popen(argv, cwd=s.root, env={**os.environ, 'PYTHONDONTWRITEBYTECODE': '1'},
                                              stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True))
        results = []
        for process in processes:
            stdout, _ = process.communicate(timeout=20)
            if process.returncode == 0:
                results.append(json.loads(stdout))
        require(sum(r.get('status') == 'applied' for r in results) == 1, 'concurrent stale plans both applied or neither installed')
        for source in s.source.rglob('*'):
            if source.is_file():
                require((s.target / source.relative_to(s.source)).read_bytes() == source.read_bytes(), 'concurrent apply corrupted content')
        require(s.call('status', '--target', s.target).get('pending_transaction') is None, 'concurrent apply left incomplete state')
    finally:
        for process in processes:
            if process.poll() is None:
                process.kill()
            process.communicate()


def scenarios(phase):
    result = [('install-bytes-modes-dotpaths', install), ('repeat-noop', noop),
              ('existing-unmanaged-conflict', existing_conflict), ('identical-unmanaged-conflict', identical_unmanaged),
              ('upstream-update', upstream_update), ('local-preserved', local_preserved),
              ('overlapping-conflict', overlapping_conflict), ('managed-deletion', deletion),
              ('dirty-deletion-conflict', dirty_deletion), ('stale-target', stale_target),
              ('stale-source', stale_source), ('status-readonly', status_readonly),
              ('native-template-validation', native_template), ('target-git-preserved', git_preserved)]
    result += [(f'reserved-{name}', lambda s, n=name: reserved_source(s, n)) for name in ('.git', '.agent-project')]
    result += [(f'plan-{kind}', lambda s, k=kind: plan_attack(s, k)) for kind in ('traversal', 'absolute', 'duplicate')]
    result += [(f'symlink-{where}', lambda s, w=where: symlink(s, w)) for where in ('source', 'target', 'metadata')]
    if phase >= 2:
        result += [('text-merge-and-third-update', text_merge), ('binary-conflict', binary_conflict),
                   ('explicit-adoption', adoption), ('adoption-mismatch', lambda s: adoption(s, True)),
                   ('unrelated-edit-kept', unrelated_change), ('mode-precondition', mode_stale)]
    if phase >= 3:
        result += [('crash-recovery', crash_recover), ('post-crash-user-edit', lambda s: crash_recover(s, True)),
                   ('rollback', rollback), ('post-update-user-edit', lambda s: rollback(s, True)),
                   ('corrupt-ownership-metadata', corrupt_metadata), ('stale-and-unsafe-rollback', stale_rollback),
                   ('concurrent-apply', concurrent_apply)]
    return result


def evaluate(candidate, phase):
    initial = tree(candidate)
    checks = []
    for name, action in scenarios(phase):
        began = time.monotonic()
        with tempfile.TemporaryDirectory(prefix='project-lifecycle-acceptance-') as raw:
            try:
                action(Scenario(Path(raw), candidate))
                passed, detail = True, None
            except Exception as error:
                passed, detail = False, f'{type(error).__name__}: {error}'[-1000:]
        checks.append({'name': name, 'passed': passed, 'detail': detail,
                       'wall_seconds': round(time.monotonic() - began, 3)})
    unchanged = initial == tree(candidate)
    return {'schema_version': 1, 'phase': phase, 'source_unchanged': unchanged,
            'candidate_tree_sha256': hashlib.sha256(json.dumps(initial, sort_keys=True, separators=(',', ':')).encode()).hexdigest(),
            'evaluator_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            'semantic_checks_passed': sum(c['passed'] for c in checks), 'semantic_checks_total': len(checks),
            'semantic_checks_accepted': unchanged and all(c['passed'] for c in checks),
            'release_accepted': None, 'checks': checks}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--candidate', type=Path, required=True)
    parser.add_argument('--phase', type=int, choices=(1, 2, 3), required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = evaluate(args.candidate.resolve(), args.phase)
    args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + '\n')
    print(json.dumps({k: v for k, v in result.items() if k != 'checks'}, indent=2))
    return 0 if result['semantic_checks_accepted'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
