"""Independent staged observations; execute only inside a disposable evaluator."""
from __future__ import annotations
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import shlex
import signal
import stat
import subprocess
import sys
import time

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
from evaluate_execution import CASES as CORE_CASES, observe_case, require
from staged_fixture import StagedFixture, wait_for


def decoded(result):
    try:
        value = json.loads(result.stdout)
    except (ValueError, TypeError):
        raise AssertionError('required JSON observation is absent')
    require(isinstance(value, dict), 'observation is not an object')
    return value


def completed(f, result, status):
    value = decoded(result)
    require(type(value.get('schema_version')) is int and value['schema_version'] == 1, 'invalid schema version')
    require(value.get('job_id') == f.job['job_id'], 'wrong job identity')
    require(value.get('attempt_id') == f.attempt['attempt_id'], 'wrong attempt identity')
    require(value.get('head_sha') == f.attempt['head_sha'], 'wrong submitted HEAD')
    require(value.get('status') == status, f'expected {status}, got {value.get("status")}')
    require((result.returncode == 0) == (status == 'passed'), 'exit status disagrees with verification')
    checks = value.get('checks')
    require(isinstance(checks, list) and all(isinstance(c, dict) for c in checks), 'invalid checks')
    require([c.get('command') for c in checks] == f.commands, 'original acceptance order not preserved')
    for row in checks:
        require(isinstance(row.get('status'), str), 'missing command status')
        require(row.get('exit_code') is None or type(row['exit_code']) is int, 'invalid exit code')
        seconds = row.get('elapsed_seconds')
        require(type(seconds) in (int, float) and math.isfinite(seconds) and seconds >= 0, 'invalid elapsed time')
        require(all(isinstance(row.get(k), str) for k in ('stdout_tail', 'stderr_tail')), 'missing output tails')
        require(sum(len(row[k].encode('utf-8')) for k in ('stdout_tail', 'stderr_tail')) <= 65536, 'retained output exceeds cap')
    return value


def query(f):
    result = f.invoke('job', 'checks', f.job['job_id'], '--json')
    require(result.returncode == 0, 'cannot inspect verification evidence')
    value = decoded(result)
    require(type(value.get('schema_version')) is int and value['schema_version'] == 1, 'invalid query schema')
    require(value.get('job_id') == f.job['job_id'], 'wrong query job')
    require(type(value.get('fresh')) is bool, 'freshness must be explicit')
    require(isinstance(value.get('stale_reasons'), list), 'staleness reasons missing')
    return value


def gated(f, passed):
    before = decoded(f.invoke('job', 'show', f.job['job_id'], '--json'))
    result = f.invoke('job', 'validate', f.job['job_id'], '--require-checks', '--json')
    require((result.returncode == 0) == passed, 'independent validation gate disagrees with evidence')
    if not passed:
        after = decoded(f.invoke('job', 'show', f.job['job_id'], '--json'))
        require(after['state'] == before['state'] and
                [a['state'] for a in after['attempts']] == [a['state'] for a in before['attempts']],
                'rejected independent validation changed job or attempt state')
    return result


def fresh(value, expected):
    require(value['fresh'] is expected, 'incorrect evidence freshness')
    if not expected:
        require(bool(value['stale_reasons']), 'stale or absent evidence lacks diagnosis')
    else:
        require(value['latest'] is not None and value['latest']['status'] == 'passed', 'fresh passing report missing')
        require(bool(value['latest'].get('verification_id')), 'verification identity missing')


def write(path):
    return 'printf executed > ' + shlex.quote(str(path))


def run_program(f, source):
    path = f.root / ('program-' + str(len(list(f.root.glob('program-*')))) + '.py')
    path.write_text(source)
    return shlex.join([sys.executable, str(path)])


def invalid_limits(f):
    witness = f.root / 'executed'
    f.create([write(witness)])
    for value in ('0', '-1', 'nan', 'inf', '-inf'):
        result = f.check(value)
        require(result.returncode != 0 and not witness.exists(), 'invalid deadline allowed execution')


def cwd(f, variant):
    witness = f.root / 'executed'
    directory = 'nested' if variant == 'valid' else 'absent'
    if variant in ('symlink', 'escape'):
        directory = 'linked'
        target = 'nested'
        if variant == 'escape':
            target = f.root / 'outside'
            target.mkdir()
        (f.workspace / directory).symlink_to(target, target_is_directory=True)
        f.git('add', directory, workspace=f.workspace)
        f.git('commit', '-qm', 'symlink directory fixture', workspace=f.workspace)
    entries = [{'kind': 'command', 'value': write(witness)},
               {'kind': 'command', 'value': 'pwd', 'cwd': directory}]
    f.create(entries)
    result = f.check()
    if variant == 'valid':
        value = completed(f, result, 'passed')
        require(witness.exists(), 'positive cwd sequence never executed')
        require(value['checks'][1]['stdout_tail'].strip() == str(f.work / 'nested'), 'check ran in wrong cwd')
        require(Path(value['checks'][1].get('cwd', '')).resolve() == f.work / 'nested', 'working directory not reported')
    else:
        require(result.returncode != 0 and not witness.exists(), 'unsafe cwd was not rejected before the sequence')


def precondition(f, variant):
    witness = f.root / 'executed'
    f.create([write(witness)], run=variant != 'no-attempt')
    if variant == 'dirty':
        (f.work / 'tracked.txt').write_text('user change\n')
    elif variant == 'hidden-dirty':
        f.git('update-index', '--skip-worktree', 'tracked.txt')
        (f.work / 'tracked.txt').write_text('hidden change\n')
    elif variant == 'wrong-head':
        f.git('commit', '--allow-empty', '-qm', 'unexpected commit')
    result = f.check()
    require(result.returncode != 0 and not witness.exists(), 'unsafe delivery was accepted or executed')
    if variant in ('dirty', 'hidden-dirty'):
        require('change' in (f.work / 'tracked.txt').read_text(), 'checker repaired user changes automatically')


def active_attempt(f):
    marker = f.root / 'provider-started'
    release = f.root / 'provider-release'
    pause = f"\nimport time\npathlib.Path({str(marker)!r}).write_text('started')\nwhile not pathlib.Path({str(release)!r}).exists(): time.sleep(.02)\n"
    f.provider.write_text(f.provider.read_text().replace("(root/'delivery.txt')", pause + "(root/'delivery.txt')", 1))
    witness = f.root / 'executed'
    f.create([write(witness)], run=False)
    process = f.start('job', 'run', f.job['job_id'], '--provider', 'codex', '--json')
    wait_for(marker.exists, process=process)
    result = f.check()
    require(result.returncode != 0 and not witness.exists(), 'checker ran against an active delivery')
    release.touch()
    require(f.wait(process).returncode == 0, 'fake provider did not finish after release')


def deadline(f):
    first = f.root / 'first'
    stamp = f.root / 'sequence-start'
    first_command = run_program(f, f"from pathlib import Path\nimport time\np=Path({str(stamp.with_suffix('.tmp'))!r})\np.write_text(str(time.monotonic()));p.replace({str(stamp)!r})\ntime.sleep(1)\nPath({str(first)!r}).write_text('executed')\n")
    worker = f.worker()
    f.create([first_command, shlex.join([sys.executable, str(worker)])])
    process = f.start('job', 'check', f.job['job_id'], '--timeout', '1.5', '--json')
    wait_for(stamp.exists, seconds=20, process=process)
    started = float(stamp.read_text())
    wait_for(lambda: (f.root / 'starts').exists(), seconds=2, process=process)
    wait_for(lambda: not f.worker_alive(), seconds=3)
    elapsed = time.monotonic() - started
    result = f.wait(process)
    value = completed(f, result, 'timed-out')
    require(first.exists() and (f.root / 'starts').exists(), 'deadline fixture did not reach both commands')
    require(value['checks'][0]['exit_code'] == 0, 'first command incorrectly timed out')
    require(elapsed < 2.3, 'whole-sequence deadline was restarted or ignored')


def bounded_output(f):
    command = run_program(f, "import sys\nfor _ in range(8192): sys.stdout.write('x'*1024)\nsys.stdout.flush()\nfor _ in range(8192): sys.stderr.write('y'*1024)\nsys.stderr.write('\\nAPI_KEY=fixture-stream-secret\\nEND-STDERR\\n')\nsys.stderr.flush()\nprint('END-STDOUT')\n")
    f.create([command])
    value = completed(f, f.check(10), 'passed')
    row = value['checks'][0]
    require('END-STDOUT' in row['stdout_tail'] and 'END-STDERR' in row['stderr_tail'], 'useful final output missing')
    require('fixture-stream-secret' not in row['stdout_tail'] + row['stderr_tail'], 'synthetic secret leaked')
    require(not any(p.stat().st_size > 2 * 1024 * 1024 for p in f.state.rglob('*') if p.is_file()), 'unbounded raw output persisted')


MUTATIONS = {
    'bytes': "printf changed > tracked.txt",
    'mode': 'chmod +x tracked.txt',
    'index': 'git update-index --chmod=+x tracked.txt',
    'head': 'git -c commit.gpgSign=false -c core.hooksPath=/dev/null commit --allow-empty -qm changed',
    'untracked': 'printf changed > added-source.txt',
    'assume-unchanged': 'git update-index --assume-unchanged tracked.txt; printf changed > tracked.txt',
    'skip-worktree': 'git update-index --skip-worktree tracked.txt; printf changed > tracked.txt',
}


def mutation(f, variant):
    f.create([MUTATIONS[variant]])
    completed(f, f.check(), 'source-changed')
    if variant in ('bytes', 'assume-unchanged', 'skip-worktree'):
        require((f.work / 'tracked.txt').read_text() == 'changed', 'checker undid a source change')


def ignored_cache(f):
    f.create(['mkdir -p cache; printf cache > cache/test-data'])
    completed(f, f.check(), 'passed')
    require((f.work / 'cache/test-data').read_text() == 'cache', 'ignored test cache was not created')


def increment_command(f):
    return run_program(f, f"from pathlib import Path\np=Path({str(f.root / 'count')!r})\np.write_text(str(int(p.read_text())+1) if p.exists() else '1')\n")


def evidence(f):
    f.create([increment_command(f)])
    completed(f, f.check(), 'passed')
    value = query(f); fresh(value, True)
    again = query(f); fresh(again, True)
    require(value['latest']['verification_id'] == again['latest']['verification_id'], 'reading created new evidence')
    require((f.root / 'count').read_text() == '1', 'query reran a command')
    gated(f, True)
    require((f.root / 'count').read_text() == '1', 'validation reran a command')


def absent(f):
    f.create([increment_command(f)])
    value = query(f); fresh(value, False)
    require(value['latest'] is None, 'old jobs acquired fabricated evidence')
    gated(f, False)
    require(not (f.root / 'count').exists(), 'absence/query/validation executed a command')
    result = f.invoke('job', 'validate', f.job['job_id'], '--json')
    require(result.returncode == 0, 'legacy validation compatibility lost')


def stale(f, variant):
    f.create([increment_command(f)])
    completed(f, f.check(), 'passed')
    if variant == 'task':
        path = Path(f.job['task_path']); task = json.loads(path.read_text())
        task['objective'] += ' modified after verification'; path.write_text(json.dumps(task))
    else:
        subprocess.run(['/bin/sh', '-c', MUTATIONS[variant]], cwd=f.work, check=True, capture_output=True, timeout=10)
    value = query(f); fresh(value, False)
    gated(f, False)
    require((f.root / 'count').read_text() == '1', 'stale evidence triggered implicit execution')


def artifact(f, value):
    path = Path(value['latest'].get('report_path', ''))
    require(path.is_absolute() and path.is_file() and not path.is_symlink(), 'private JSON report artifact missing')
    require(path.resolve().is_relative_to(f.state.resolve()), 'report artifact escapes private state')
    require(path.stat().st_mode & 0o077 == 0, 'report artifact is not private')
    return path


def corruption(f):
    f.create(['printf ordinary'])
    completed(f, f.check(), 'passed')
    value = query(f); fresh(value, True)
    path = artifact(f, value); stored = json.loads(path.read_text())
    stored['checks'][0]['stdout_tail'] = 'tampered ordinary output'
    path.write_text(json.dumps(stored))
    result = f.invoke('job', 'checks', f.job['job_id'], '--json')
    if result.returncode == 0:
        fresh(decoded(result), False)
    gated(f, False)


def later_failure(f):
    flag = f.root / 'fail'
    f.create(['if test -e ' + shlex.quote(str(flag)) + '; then exit 17; fi; printf passed'])
    completed(f, f.check(), 'passed')
    first = query(f); fresh(first, True)
    path = artifact(f, first); original = path.read_bytes()
    flag.touch(); completed(f, f.check(), 'failed')
    last = query(f)
    require(last['latest']['status'] == 'failed', 'old pass hid the later failure')
    require(last['latest']['verification_id'] != first['latest']['verification_id'], 'new execution reused proof identity')
    require(path.read_bytes() == original, 'later failure rewrote earlier evidence')
    gated(f, False)


def retry(f):
    f.create(['printf passed'])
    completed(f, f.check(), 'passed')
    first = query(f); fresh(first, True)
    old_attempt = f.attempt['attempt_id']
    (f.work / 'tracked.txt').write_text('invalidated delivery')
    require(f.invoke('job', 'validate', f.job['job_id'], '--json').returncode != 0, 'legacy failure path missing')
    result = f.successful('job', 'run', f.job['job_id'], '--provider', 'codex', '--clean-retry', '--json')
    f.attempt = result['attempts'][-1]
    require(f.attempt['attempt_id'] != old_attempt, 'retry did not create a new attempt')
    gated(f, False)
    completed(f, f.check(), 'passed'); fresh(query(f), True); gated(f, True)


def prior_stage_proof(f):
    f.create([increment_command(f)])
    f.cli = f.creator_cli
    try:
        result = f.check()
        if result.returncode != 0:
            raise AssertionError('fixture prior-stage passing evidence unavailable')
        completed(f, result, 'passed')
        old = query(f); fresh(old, True)
        path = artifact(f, old); original = path.read_bytes()
    finally:
        f.cli = f.candidate_cli
    current = query(f); fresh(current, True)
    require(current['latest']['verification_id'] == old['latest']['verification_id'], 'migration replaced historic proof')
    require(path.read_bytes() == original, 'migration rewrote historic evidence')
    gated(f, True)
    require((f.root / 'count').read_text() == '1', 'migration reran the original command')


def concurrency(f, interruption=None):
    worker = f.worker(); release = f.root / 'release'
    release.touch(); f.create([shlex.join([sys.executable, str(worker)])])
    completed(f, f.check(), 'passed')
    first = query(f); fresh(first, True)
    release.unlink(); (f.root / 'starts').unlink()
    process = f.start('job', 'check', f.job['job_id'], '--timeout', '15', '--json')
    wait_for(lambda: (f.root / 'starts').exists(), process=process)
    value = query(f)
    require(value.get('in_progress') is True, 'active execution was not exposed')
    gated(f, False)
    if interruption:
        process.send_signal(interruption)
        try:
            stopped = f.wait(process)
        except subprocess.TimeoutExpired:
            raise AssertionError('interrupted checker did not stop within 10 seconds')
        require(stopped.returncode != 0, 'interrupted checker exited successfully')
        gated(f, False)
        if interruption == signal.SIGTERM:
            wait_for(lambda: not f.worker_alive(), seconds=2)
        else:
            # Simulate an operator establishing that orphaned execution stopped.
            f.stop_worker(); wait_for(lambda: not f.worker_alive(), seconds=2)
        release.touch()
        completed(f, f.check(), 'passed'); fresh(query(f), True)
    else:
        started = time.monotonic()
        second = f.check(2)
        require(second.returncode != 0 and time.monotonic() - started < 5, 'overlapping checker was not refused promptly')
        require((f.root / 'starts').read_text().splitlines() == ['started'], 'overlapping checker executed a command')
        release.touch(); completed(f, f.wait(process), 'passed')
        require(query(f).get('in_progress') is False, 'finished execution still claims ownership')


def cases():
    rows = [(name, 1, 'actual-execution', lambda f, n=name: observe_case(f, n)) for name in CORE_CASES]
    rows += [('invalid-deadlines', 1, 'bounded-execution', invalid_limits),
             ('active-attempt', 1, 'source-preconditions', active_attempt),
             ('whole-deadline-child-stop', 1, 'bounded-execution', deadline),
             ('bounded-output-redaction', 1, 'bounded-evidence', bounded_output),
             ('ignored-cache', 1, 'source-identity', ignored_cache)]
    rows += [(f'cwd-{v}', 1, 'working-directory', lambda f, v=v: cwd(f, v)) for v in ('valid', 'escape', 'symlink', 'missing')]
    rows += [(f'precondition-{v}', 1, 'source-preconditions', lambda f, v=v: precondition(f, v)) for v in ('no-attempt', 'dirty', 'hidden-dirty', 'wrong-head')]
    rows += [(f'mutation-{v}', 1, 'source-identity', lambda f, v=v: mutation(f, v)) for v in MUTATIONS]
    rows += [('fresh-read-only-gate', 2, 'evidence-freshness', evidence),
             ('legacy-absence', 2, 'migration', absent), ('report-corruption', 2, 'evidence-integrity', corruption),
             ('later-failure-retains-history', 2, 'evidence-integrity', later_failure),
             ('real-clean-retry', 2, 'migration', retry)]
    rows += [(f'stale-{v}', 2, 'evidence-freshness', lambda f, v=v: stale(f, v)) for v in (*MUTATIONS, 'task')]
    rows += [('exclusive-checker', 3, 'interruption-and-concurrency', concurrency),
             ('sigterm-and-recheck', 3, 'interruption-and-concurrency', lambda f: concurrency(f, signal.SIGTERM)),
             ('abrupt-death-and-recheck', 3, 'interruption-and-concurrency', lambda f: concurrency(f, signal.SIGKILL)),
             ('prior-stage-proof', 3, 'migration', prior_stage_proof)]
    return rows


def inventory(root):
    result = {}
    for current, directories, files in os.walk(root, followlinks=False):
        if Path(current) == root and '.git' in directories:
            directories.remove('.git')
        for name in directories + files:
            path = Path(current) / name; mode = path.lstat().st_mode
            key = str(path.relative_to(root))
            if stat.S_ISLNK(mode):
                result[key] = ['link', os.readlink(path)]
            elif stat.S_ISREG(mode):
                result[key] = ['file', stat.S_IMODE(mode), hashlib.sha256(path.read_bytes()).hexdigest()]
            elif stat.S_ISDIR(mode):
                result[key] = ['directory', stat.S_IMODE(mode)]
            else:
                raise ValueError('unsupported candidate entry')
    return result


def evaluate(candidate, template, phase, legacy, selected=None, previous=None):
    eligible = [r for r in cases() if r[1] <= phase]
    if selected and not set(selected).issubset({r[0] for r in eligible}):
        raise ValueError('unknown or unreleased selected case')
    before = inventory(candidate)
    probe = subprocess.run([sys.executable, str(candidate / 'scripts/agentctl'), 'job', 'check', '--help'],
                           text=True, capture_output=True, timeout=15)
    available = probe.returncode == 0 and '--timeout' in probe.stdout
    checks = []
    for name, stage, dimension, action in cases():
        if stage > phase or (selected and name not in selected):
            continue
        if not available:
            checks.append({'name': name, 'phase': stage, 'dimension': dimension, 'status': 'failed',
                           'detail': 'required check interface unavailable; no independent execution demonstrated'})
            continue
        f = None
        try:
            creator = legacy if name == 'legacy-absence' else previous if name == 'prior-stage-proof' else None
            if name == 'prior-stage-proof' and previous is None:
                raise AssertionError('fixture prior-stage source was not supplied')
            f = StagedFixture(candidate, template, creator=creator)
            action(f)
            status, detail = 'passed', None
        except AssertionError as error:
            status = 'unknown' if str(error).startswith(('fixture CLI failed:', 'fixture prior-stage')) else 'failed'
            detail = str(error)[:400]
        except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError) as error:
            status, detail = 'unknown', type(error).__name__
        finally:
            if f:
                f.close()
        checks.append({'name': name, 'phase': stage, 'dimension': dimension, 'status': status, 'detail': detail})
    unchanged = inventory(candidate) == before
    digest = hashlib.sha256(json.dumps(before, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    return {'schema_version': 1, 'phase': phase, 'checks': checks, 'check_interface_available': available,
            'candidate_entry_sha256': digest, 'candidate_source_unchanged': unchanged,
            'coverage': 'selected observations' if selected else 'all declared observations through this phase',
            'measurement_complete': unchanged and bool(checks) and all(c['status'] != 'unknown' for c in checks),
            'behavioral_threshold': None if selected else unchanged and bool(checks) and all(c['status'] == 'passed' for c in checks),
            'release_accepted': None, 'installed_distribution': 'separate actual-image check required'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--candidate', required=True, type=Path)
    parser.add_argument('--template', required=True, type=Path)
    parser.add_argument('--legacy', required=True, type=Path)
    parser.add_argument('--previous', type=Path, help='actual phase-2 source, required for the phase-3 migration observation')
    parser.add_argument('--phase', required=True, type=int, choices=(1, 2, 3))
    parser.add_argument('--case', action='append')
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    value = evaluate(args.candidate.resolve(), args.template.resolve(), args.phase, args.legacy.resolve(), args.case,
                     args.previous.resolve() if args.previous else None)
    args.output.write_text(json.dumps(value, indent=2) + '\n')
    print(json.dumps(value, indent=2))
    raise SystemExit(0 if value['measurement_complete'] else 2)
