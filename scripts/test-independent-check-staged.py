"""Calibrate staged observers with executable, fixture-specific reference behavior.

This test double is not installed or copied into development candidates. It uses
real old jobs and real processes, but holds its reference evidence index in the
test process. Production durability still requires the actual candidate tests.
"""
import hashlib
import json
import math
import os
from pathlib import Path
import selectors
import signal
import subprocess
import sys
import tempfile
import time
import unittest
import uuid

ROOT = Path(__file__).resolve().parents[1]
sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT / 'experiments/development-harness/cycle-003/large-02'))
import evaluate_staged as E
from staged_fixture import StagedFixture


class ReferenceInterrupted(Exception):
    pass


def execute(spec):
    checks = []
    started = time.monotonic()
    status = 'passed'
    for command, cwd in zip(spec['commands'], spec['cwds']):
        row = {'command': command, 'cwd': cwd, 'status': 'unexecuted', 'exit_code': None,
               'elapsed_seconds': 0, 'stdout_tail': '', 'stderr_tail': ''}
        checks.append(row)
        if status != 'passed':
            continue
        process = subprocess.Popen(['/bin/sh', '-c', command], cwd=cwd, stdin=subprocess.DEVNULL,
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE, start_new_session=True)
        begin = time.monotonic(); tails = {0: bytearray(), 1: bytearray()}
        selector = selectors.DefaultSelector()
        selector.register(process.stdout, selectors.EVENT_READ, 0)
        selector.register(process.stderr, selectors.EVENT_READ, 1)
        try:
            deadline = (begin if spec.get('per_command') else started) + spec['seconds']
            while selector.get_map():
                if time.monotonic() >= deadline:
                    status = 'timed-out'
                    break
                for key, _ in selector.select(.02):
                    data = os.read(key.fileobj.fileno(), 65536)
                    if data:
                        tails[key.data].extend(data)
                        del tails[key.data][:-32768]
                    else:
                        selector.unregister(key.fileobj)
            if status == 'passed':
                process.wait(timeout=max(.01, deadline - time.monotonic()))
        except ReferenceInterrupted:
            status = 'interrupted'
        finally:
            if process.poll() is None:
                os.killpg(process.pid, signal.SIGKILL)
            process.wait(timeout=2)
            selector.close(); process.stdout.close(); process.stderr.close()
        row.update(exit_code=process.returncode, elapsed_seconds=time.monotonic() - begin,
                   stdout_tail=tails[0].decode(errors='replace').replace('fixture-stream-secret', '[REDACTED]'),
                   stderr_tail=tails[1].decode(errors='replace').replace('fixture-stream-secret', '[REDACTED]'))
        if status == 'passed' and process.returncode:
            status = 'failed'
        row['status'] = status
    return {'status': status if checks else 'no-checks', 'checks': checks}


def interrupted(_signal, _frame):
    # selectors handles InterruptedError internally; use a distinct exception.
    raise ReferenceInterrupted()


class Reference(StagedFixture):
    def __init__(self):
        super().__init__(ROOT, ROOT / 'project')
        self.records = []
        self.pending = None
        self.ignore_identity = False
        self.ignore_digest = False
        self.per_command = False

    def identity(self):
        inventory = {}
        for path in sorted(self.work.rglob('*')):
            relative = str(path.relative_to(self.work))
            if relative == '.git' or relative == 'cache' or relative.startswith('cache/'):
                continue
            if path.is_symlink():
                inventory[relative] = ['link', os.readlink(path)]
            elif path.is_file():
                inventory[relative] = [path.stat().st_mode, hashlib.sha256(path.read_bytes()).hexdigest()]
        index = Path(self.git('rev-parse', '--git-path', 'index'))
        return [self.git('rev-parse', 'HEAD'), inventory, hashlib.sha256(index.read_bytes()).hexdigest(),
                hashlib.sha256(Path(self.job['task_path']).read_bytes()).hexdigest(), self.attempt['attempt_id']]

    def spec(self, seconds):
        seconds = float(seconds)
        if not math.isfinite(seconds) or seconds <= 0 or self.attempt is None:
            raise ValueError('invalid precondition')
        if self.git('rev-parse', 'HEAD') != self.attempt['head_sha']:
            raise ValueError('wrong HEAD')
        if (self.work / 'tracked.txt').read_text() != 'original\n':
            raise ValueError('dirty fixture source')
        if self.git('status', '--porcelain', '--untracked-files=all'):
            raise ValueError('dirty source')
        task = json.loads(Path(self.job['task_path']).read_text())
        entries = [c for c in task['acceptance'] if c['kind'] == 'command']
        directories = []
        for entry in entries:
            path = self.work / entry.get('cwd', '.')
            if not path.is_dir() or path.resolve() != path or not path.resolve().is_relative_to(self.work):
                raise ValueError('invalid working directory')
            directories.append(str(path))
        return {'commands': [c['value'] for c in entries], 'cwds': directories,
                'seconds': seconds, 'per_command': self.per_command}

    def persist(self, observation, before):
        if observation['status'] == 'passed' and self.identity() != before:
            observation['status'] = 'source-changed'
        identifier = uuid.uuid4().hex
        path = self.state / ('reference-' + identifier + '.json')
        value = {'schema_version': 1, 'job_id': self.job['job_id'],
                 'attempt_id': self.attempt['attempt_id'], 'head_sha': self.attempt['head_sha'],
                 **observation, 'verification_id': identifier, 'report_path': str(path)}
        path.write_text(json.dumps(value)); path.chmod(0o600)
        self.records.append((path, hashlib.sha256(path.read_bytes()).hexdigest(), before))
        return subprocess.CompletedProcess([], 0 if value['status'] == 'passed' else 1, json.dumps(value), '')

    def view(self):
        current = bool(self.pending and self.pending[0].poll() is None)
        value, valid = None, False
        if self.records:
            path, digest, identity = self.records[-1]
            value = json.loads(path.read_text())
            valid = ((self.ignore_identity or self.identity() == identity) and
                     (self.ignore_digest or hashlib.sha256(path.read_bytes()).hexdigest() == digest) and
                     value['status'] == 'passed' and self.pending is None)
        return {'schema_version': 1, 'job_id': self.job['job_id'], 'latest': value,
                'fresh': valid, 'stale_reasons': [] if valid else ['absent, changed or incomplete'],
                'in_progress': current}

    def check(self, seconds=5):
        if self.pending and (self.pending[0].poll() is None or self.worker_alive()):
            return subprocess.CompletedProcess([], 1, '{}', '')
        self.pending = None
        try:
            spec = self.spec(seconds)
        except ValueError:
            return subprocess.CompletedProcess([], 1, '{}', '')
        before = self.identity()
        return self.persist(execute(spec), before)

    def invoke(self, *args, timeout=30):
        if args[:2] == ('job', 'checks'):
            return subprocess.CompletedProcess([], 0, json.dumps(self.view()), '')
        if args[:2] == ('job', 'validate') and '--require-checks' in args:
            if not self.view()['fresh']:
                return subprocess.CompletedProcess([], 1, '{}', '')
            args = tuple(x for x in args if x != '--require-checks')
        return super().invoke(*args, timeout=timeout)

    def start(self, *args):
        if args[:2] != ('job', 'check'):
            return super().start(*args)
        spec = self.spec(args[args.index('--timeout') + 1])
        path = self.root / 'reference-execution.json'; path.write_text(json.dumps(spec))
        number = len(self.processes)
        out = (self.root / f'helper-{number}.stdout').open('w+')
        err = (self.root / f'helper-{number}.stderr').open('w+')
        process = subprocess.Popen([sys.executable, str(Path(__file__).resolve()), '--execute-reference', str(path)],
                                   stdout=out, stderr=err, text=True, start_new_session=True)
        self.processes.append((process, out, err))
        self.pending = (process, self.identity())
        return process

    def wait(self, process, seconds=10):
        value = super().wait(process, seconds)
        if not self.pending or self.pending[0] is not process:
            return value
        before = self.pending[1]
        try:
            observation = json.loads(value.stdout)
        except ValueError:
            observation = {'status': 'interrupted', 'checks': []}
        self.pending = None
        return self.persist(observation, before)


class StagedCalibrationTests(unittest.TestCase):
    def test_all_declared_observers_with_executable_reference(self):
        for name, _, _, action in E.cases():
            with self.subTest(case=name):
                f = Reference()
                try:
                    action(f)
                finally:
                    f.close()

    def test_stale_source_cannot_be_hidden_by_a_passing_report(self):
        f = Reference(); self.addCleanup(f.close)
        f.ignore_identity = True
        with self.assertRaisesRegex(AssertionError, 'freshness'):
            E.stale(f, 'bytes')

    def test_mutated_report_cannot_trust_its_own_success(self):
        f = Reference(); self.addCleanup(f.close)
        f.ignore_digest = True
        with self.assertRaisesRegex(AssertionError, 'freshness'):
            E.corruption(f)

    def test_deadline_reset_between_commands_is_detected(self):
        f = Reference(); self.addCleanup(f.close)
        f.per_command = True
        with self.assertRaisesRegex(AssertionError, 'deadline was restarted'):
            E.deadline(f)

    def test_selected_observations_cannot_claim_complete_phase(self):
        self.assertRaises(ValueError, E.evaluate, ROOT, ROOT / 'project', 1, ROOT, ['not-a-case'])

    def test_missing_interface_does_not_pass_negative_guards(self):
        with tempfile.TemporaryDirectory(prefix='checker-interface-calibration-') as temporary:
            root = Path(temporary); (root / 'scripts').mkdir()
            (root / 'scripts/agentctl').write_text("print('no checker')\n")
            result = E.evaluate(root, root, 3, root)
            self.assertTrue(result['measurement_complete'])
            self.assertFalse(result['behavioral_threshold'])
            self.assertFalse(result['check_interface_available'])
            self.assertEqual(len(result['checks']), 41)
            self.assertTrue(all(c['status'] == 'failed' for c in result['checks']))

    def test_source_inventory_observes_bytes_modes_and_symlinks(self):
        with tempfile.TemporaryDirectory(prefix='checker-inventory-calibration-') as temporary:
            root = Path(temporary); file = root / 'file'; file.write_text('first')
            a = E.inventory(root); file.write_text('second'); b = E.inventory(root)
            self.assertNotEqual(a, b)
            file.chmod(0o600); c = E.inventory(root)
            self.assertNotEqual(b, c)
            (root / 'link').symlink_to('file'); d = E.inventory(root)
            self.assertNotEqual(c, d)
            self.assertEqual(d['link'], ['link', 'file'])

    def test_prior_stage_proof_reference(self):
        f = Reference(); self.addCleanup(f.close)
        E.prior_stage_proof(f)


if __name__ == '__main__':
    if len(sys.argv) == 3 and sys.argv[1] == '--execute-reference':
        signal.signal(signal.SIGTERM, interrupted)
        value = execute(json.loads(Path(sys.argv[2]).read_text()))
        print(json.dumps(value))
        raise SystemExit(0 if value['status'] == 'passed' else 1)
    unittest.main()
