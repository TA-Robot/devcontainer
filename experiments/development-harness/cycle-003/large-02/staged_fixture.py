"""Owned real-job fixtures and finite subprocesses for staged acceptance."""
from __future__ import annotations
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

from fixture import Fixture


class StagedFixture(Fixture):
    def __init__(self, candidate, template, creator=None):
        super().__init__(creator or candidate, template)
        self.creator_cli = self.cli
        self.candidate_cli = candidate / 'scripts/agentctl'
        self.processes = []
        (self.workspace / '.gitignore').write_text('cache/\n')
        (self.workspace / 'nested').mkdir()
        (self.workspace / 'nested/kept.txt').write_text('nested\n')
        self.git('add', '.gitignore', 'nested', workspace=self.workspace)
        self.git('commit', '-qm', 'acceptance layout', workspace=self.workspace)

    def git(self, *args, workspace=None):
        return subprocess.check_output(['git', '-C', str(workspace or self.work), *args],
                                       text=True, stderr=subprocess.PIPE, timeout=15).strip()

    @property
    def work(self):
        return Path(self.attempt['workspace_path'])

    def create(self, commands, *, extra_reported=(), run=True):
        entries = [dict(c) if isinstance(c, dict) else {'kind': 'command', 'value': c} for c in commands]
        self.commands = [c['value'] for c in entries]
        task = {'schema_version': 1, 'objective': 'Deliver a fixture file.', 'role': 'implementer',
                'lane': 'write', 'permission_profile': 'safe', 'resource_class': 'write',
                'scope': {'allowed_paths': ['delivery.txt'], 'forbidden_paths': []},
                'acceptance': entries or [{'kind': 'manual', 'value': 'Review manually.'}],
                'constraints': ['Do not push or merge.'], 'dependency_job_ids': []}
        path = self.workspace / 'task.json'
        path.write_text(json.dumps(task))
        self.environment['CHECK_FIXTURE_REPORTED_COMMANDS'] = json.dumps([*self.commands, *extra_reported])
        self.job = self.successful('job', 'create', '--workspace', self.workspace, '--task', path, '--base', 'HEAD', '--json')
        if run:
            result = self.successful('job', 'run', self.job['job_id'], '--provider', 'codex', '--json')
            self.attempt = result['attempts'][-1]
        self.cli = self.candidate_cli
        return self.job

    def start(self, *args):
        number = len(self.processes)
        out = (self.root / f'observer-{number}.stdout').open('w+')
        err = (self.root / f'observer-{number}.stderr').open('w+')
        process = subprocess.Popen([sys.executable, str(self.cli), '--state-dir', str(self.state), *map(str, args)],
                                   env=self.environment, stdout=out, stderr=err, text=True, start_new_session=True)
        self.processes.append((process, out, err))
        return process

    def wait(self, process, seconds=10):
        process.wait(timeout=seconds)
        _, out, err = next(row for row in self.processes if row[0] is process)
        if any(os.fstat(stream.fileno()).st_size > 2 * 1024 * 1024 for stream in (out, err)):
            raise AssertionError('checker observation exceeded the 2 MiB observer output cap')
        out.flush(); err.flush(); out.seek(0); err.seek(0)
        return subprocess.CompletedProcess([], process.returncode, out.read(), err.read())

    def check(self, seconds=5):
        process = self.start('job', 'check', self.job['job_id'], '--timeout', str(seconds), '--json')
        try:
            return self.wait(process, seconds=20)
        except subprocess.TimeoutExpired:
            if process.poll() is None:
                os.killpg(process.pid, signal.SIGKILL)
            process.wait(timeout=5)
            raise AssertionError('checker did not return within the finite observer bound')

    def worker(self):
        script = self.root / 'owned-worker.py'
        script.write_text('''import json,os,pathlib,time
root=pathlib.Path(__file__).parent
identity={'pid':os.getpid(),'start':pathlib.Path('/proc/self/stat').read_text().split(') ',1)[1].split()[19]}
record=root/('worker-'+str(os.getpid())+'.json')
record.write_text(json.dumps(identity))
temporary=root/('identity-'+str(os.getpid())+'.tmp')
temporary.write_text(json.dumps(identity)); temporary.replace(root/'worker-identity.json')
with (root/'starts').open('a') as stream: stream.write('started\\n')
while not (root/'release').exists(): time.sleep(.02)
print('finished')
''')
        return script

    def worker_alive(self):
        path = self.root / 'worker-identity.json'
        if not path.exists():
            return False
        identity = json.loads(path.read_text())
        try:
            stat = Path(f"/proc/{identity['pid']}/stat").read_text().split(') ', 1)[1].split()
            return stat[19] == identity['start'] and stat[0] != 'Z'
        except FileNotFoundError:
            return False

    def stop_worker(self):
        for path in self.root.glob('worker-*.json'):
            identity = json.loads(path.read_text())
            try:
                value = Path(f"/proc/{identity['pid']}/stat").read_text().split(') ', 1)[1].split()
                # Match every owned worker's start identity, including a bad
                # overlapping check, rather than only the last writer's PID.
                if value[19] == identity['start'] and value[0] != 'Z':
                    os.kill(identity['pid'], signal.SIGKILL)
            except (FileNotFoundError, ProcessLookupError):
                pass

    def close(self):
        try:
            for process, out, err in self.processes:
                if process.poll() is None:
                    os.killpg(process.pid, signal.SIGKILL)
                process.wait(timeout=10)
                out.close(); err.close()
            self.stop_worker()
        finally:
            super().close()


def wait_for(predicate, seconds=5, process=None):
    end = time.monotonic() + seconds
    while time.monotonic() < end:
        if predicate():
            return
        if process is not None and process.poll() is not None:
            break
        time.sleep(.02)
    raise AssertionError('required execution event was not observed before the bound')
