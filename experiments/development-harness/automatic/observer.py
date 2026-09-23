#!/usr/bin/env python3
"""Versioned machine-only quality observations, including previously found defects."""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import shlex
import signal
import subprocess
import sys

HARNESS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HARNESS / 'cycle-003/large-02'))
import evaluate_staged as staged
sys.path.insert(0, str(HARNESS / 'continuation'))
import recovery


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def index_refresh(f):
    f.create(['touch -t 200001010000 tracked.txt; git update-index --refresh'])
    staged.completed(f, f.check(), 'passed')
    staged.fresh(staged.query(f), True)


def gc_ownership(f):
    worker = f.worker()
    release = f.root / 'release'
    release.touch()
    f.create([shlex.join([sys.executable, str(worker)])])
    f.successful('job', 'check', f.job['job_id'], '--json')
    f.successful('job', 'validate', f.job['job_id'], '--require-checks', '--json')
    (f.workspace / 'task.json').unlink()
    f.git('cherry-pick', f.attempt['head_sha'], workspace=f.workspace)
    f.successful('job', 'collect', f.job['job_id'], '--onto', 'HEAD', '--json')
    before = f.successful('gc', '--dry-run', '--job', f.job['job_id'], '--json')['jobs'][0]
    staged.require(before['eligible'], 'fixture GC eligibility not established')
    release.unlink()
    (f.root / 'starts').unlink()
    process = f.start('job', 'check', f.job['job_id'], '--timeout', '15', '--json')
    staged.wait_for(lambda: (f.root / 'starts').exists(), process=process)
    value = f.successful('gc', '--dry-run', '--job', f.job['job_id'], '--json')['jobs'][0]
    staged.require(not value['eligible'] and not value['candidate_actions'], 'GC includes active verification')
    release.touch()
    staged.completed(f, f.wait(process), 'passed')


def publication(f):
    f.create(['printf checked'])
    f.successful('job', 'check', f.job['job_id'], '--json')
    marker = f.root / 'signal-injected'
    driver = f.root / 'publication.py'
    driver.write_text(
        'import os,sys,signal,runpy\n'
        + f'sys.path.insert(0,{str(f.cli.parent)!r})\n'
        + 'import agentctl_jobs as jobs\noriginal=jobs.Store.__init__\n'
        + 'def instrument(self,*args,**kwargs):\n original(self,*args,**kwargs)\n sent=[False]\n'
        + ' def trace(statement):\n  sql=" ".join(statement.upper().split())\n'
        + '  if not sent[0] and sql.startswith(("UPDATE VERIFICATIONS ","UPDATE COMMAND_VERIFICATIONS ")) and "REPORT_DIGEST" in sql:\n'
        + f'   sent[0]=True\n   open({str(marker)!r},"w").write("injected")\n'
        + '   os.kill(os.getpid(),signal.SIGTERM)\n self.connection.set_trace_callback(trace)\n'
        + f'jobs.Store.__init__=instrument\nrunpy.run_path({str(f.cli)!r},run_name="__main__")\n')
    original = f.cli
    f.cli = driver
    try:
        result = f.invoke('job', 'check', f.job['job_id'], '--json')
    finally:
        f.cli = original
    staged.require(marker.exists(), 'publication boundary was not observed')
    staged.require(result.returncode != 0, 'interrupted publication accepted success')
    staged.gated(f, False)
    staged.fresh(staged.query(f), False)


def declared_recovery(f):
    # Fixed rule chosen before either run: select by exposed interface, never by
    # which retry happens to pass. Both procedures are allowed by the task.
    help_result = f.invoke('job', 'check', '--help')
    procedure = 'explicit' if '--recover-incomplete' in help_result.stdout else 'automatic'
    result = recovery.observe(f, procedure)
    if result['status'] == 'unknown':
        raise OSError(result.get('detail', 'recovery witness unavailable'))
    staged.require(result['status'] == 'passed', result.get('detail', 'recovery failed'))


def acceptance_cases():
    rows = ORIGINAL_CASES()
    rows = [(name, phase, dimension, declared_recovery if name == 'abrupt-death-and-recheck' else action)
            for name, phase, dimension, action in rows]
    return rows + [('git-stat-refresh', 1, 'source-identity', index_refresh),
                   ('gc-active-verification', 3, 'interruption-and-concurrency', gc_ownership),
                   ('publication-signal', 3, 'interruption-and-concurrency', publication)]


ORIGINAL_CASES = staged.cases


def small(candidate):
    evaluator = load('automatic_redaction', HARNESS / 'cycle-003/evaluate_redaction.py')
    result = evaluator.evaluate(candidate)
    redact = sys.modules['agentctl_jobs']._redact_log_text
    for name, raw, required in [
        ('long-integer', '{"n":' + '9' * 5000 + ',"api_key":"fixture-secret"}', '9' * 5000),
        ('surrogate-utf8', '{"message":"\\ud800 sk-proj-aaaaaaaaaaaaaaaaaaaa"}', None),
    ]:
        try:
            value, count = redact(raw)
            value.encode('utf-8')
            secret = 'fixture-secret' if name == 'long-integer' else 'sk-proj-aaaaaaaaaaaaaaaaaaaa'
            assert secret not in value and count > 0
            if required:
                assert required in value
            else:
                json.loads(value)
            status, detail = 'passed', None
        except Exception as error:
            status, detail = 'failed', type(error).__name__
        result['checks'].append({'name': name, 'dimension': 'secret-removal',
                                 'status': status, 'detail': detail})
    for check in result['checks']:
        check['phase'] = 1
    return result


def catalog(task):
    if task == 'duplicates-v1':
        return load('duplicates_catalog', HARNESS / 'cycle-004/duplicates.py').catalog()
    if task == 'acceptance-v2':
        return [{'name': name, 'phase': phase, 'dimension': dimension}
                for name, phase, dimension, _ in acceptance_cases()]
    if task == 'redaction-v2':
        evaluator = load('redaction_catalog', HARNESS / 'cycle-003/evaluate_redaction.py')
        rows = evaluator.observations(lambda text: (text, 0))
        return [{'name': row['name'], 'phase': 1, 'dimension': row['dimension']} for row in rows] + [
            {'name': name, 'phase': 1, 'dimension': 'secret-removal'}
            for name in ('long-integer', 'surrogate-utf8')]
    raise ValueError('unsupported automatic task')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--task', required=True, choices=('redaction-v2', 'acceptance-v2', 'duplicates-v1'))
    parser.add_argument('--candidate', required=True, type=Path)
    parser.add_argument('--legacy', type=Path)
    parser.add_argument('--previous', type=Path)
    parser.add_argument('--phase', required=True, type=int, choices=(1, 2, 3))
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    before = staged.inventory(args.candidate)
    if args.task == 'duplicates-v1':
        result = load('duplicates_observer', HARNESS / 'cycle-004/duplicates.py').evaluate(args.candidate)
    elif args.task == 'redaction-v2':
        result = small(args.candidate)
    else:
        if args.legacy is None:
            parser.error('acceptance-v2 requires legacy source')
        staged.cases = acceptance_cases
        result = staged.evaluate(args.candidate, args.legacy / 'project', args.phase,
                                 args.legacy, previous=args.previous)
    result['source_unchanged'] = before == staged.inventory(args.candidate)
    result['task'] = args.task
    result['accepted'] = result['source_unchanged'] and all(c['status'] == 'passed' for c in result['checks'])
    result['measurement_complete'] = result['source_unchanged'] and all(c['status'] != 'unknown' for c in result['checks'])
    result['release_accepted'] = None
    args.output.write_text(json.dumps(result, indent=2) + '\n')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
