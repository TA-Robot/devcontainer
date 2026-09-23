"""Actual jobs with a deliberately dishonest fake provider; never a live model."""
from __future__ import annotations
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

PROVIDER = r'''#!/usr/bin/env python3
import json,os,pathlib,subprocess,sys
sys.stdin.read()
root=pathlib.Path.cwd()
counter=pathlib.Path(os.environ['CHECK_FIXTURE_PROVIDER_COUNTER'])
counter.write_text(str(int(counter.read_text())+1))
(root/'delivery.txt').write_text('delivered\n')
head=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()
result={'schema_version':1,'job_id':os.environ['AGENTCTL_JOB_ID'],
        'status':'ready_for_commit','summary':'Fake provider claims every check passed.',
        'head_sha':head,'changed_paths':['delivery.txt'],
        'dirty_state':{'is_dirty':True,'paths':['delivery.txt']},
        'checks':[{'command':c,'status':'passed','exit_code':0,'summary':'Unexecuted claim'}
                  for c in json.loads(os.environ['CHECK_FIXTURE_REPORTED_COMMANDS'])],
        'risks':[],'followups':[],'artifacts':None,'blocked_reason':None,'error':None}
args=sys.argv[1:]
pathlib.Path(args[args.index('--output-last-message')+1]).write_text(json.dumps(result))
print(json.dumps({'fake_provider':True}))
'''


class Fixture:
    def __init__(self, candidate: Path, template: Path):
        self.temp = tempfile.TemporaryDirectory(prefix='independent-check-fixture-')
        self.root = Path(self.temp.name)
        self.workspace = self.root / 'workspace'
        self.workspace.mkdir()
        for name in ('.agent', '.codex', '.claude', '.grok'):
            shutil.copytree(template / name, self.workspace / name)
        for name in ('AGENTS.md', 'CLAUDE.md'):
            shutil.copy2(template / name, self.workspace / name)
        (self.workspace / 'tracked.txt').write_text('original\n')
        for args in (['init', '-q'], ['config', 'user.name', 'Fixture'],
                     ['config', 'user.email', 'fixture@example.invalid'], ['add', '.'],
                     ['commit', '-qm', 'fixture base']):
            subprocess.run(['git', '-C', str(self.workspace), *args], check=True, capture_output=True, timeout=20)
        self.cli = candidate / 'scripts/agentctl'
        self.state = self.root / 'state'
        self.provider = self.root / 'fake-provider'
        self.provider.write_text(PROVIDER)
        self.provider.chmod(0o755)
        self.counter = self.root / 'provider-count'
        self.counter.write_text('0')
        self.environment = {**os.environ, 'PYTHONDONTWRITEBYTECODE': '1',
                            'AGENTCTL_CODEX_BIN': str(self.provider),
                            'CHECK_FIXTURE_PROVIDER_COUNTER': str(self.counter),
                            'CHECK_FIXTURE_REPORTED_COMMANDS': '[]', 'MIRA_COMPANION_ENABLED': '0'}
        self.job = None
        self.attempt = None

    def close(self):
        self.temp.cleanup()

    def invoke(self, *args, timeout=30):
        return subprocess.run([sys.executable, str(self.cli), '--state-dir', str(self.state), *map(str, args)],
                              env=self.environment, text=True, capture_output=True, timeout=timeout)

    def successful(self, *args):
        result = self.invoke(*args)
        if result.returncode:
            raise AssertionError(f'fixture CLI failed: {result.stderr[-800:]}')
        return json.loads(result.stdout)

    def create(self, commands, *, extra_reported=()):
        task = {'schema_version': 1, 'objective': 'Deliver a fixture file.', 'role': 'implementer',
                'lane': 'write', 'permission_profile': 'safe', 'resource_class': 'write',
                'scope': {'allowed_paths': ['delivery.txt'], 'forbidden_paths': []},
                'acceptance': [{'kind': 'command', 'value': c} for c in commands]
                              or [{'kind': 'manual', 'value': 'Review the delivery manually.'}],
                'constraints': ['Do not push or merge.'], 'dependency_job_ids': []}
        path = self.workspace / 'task.json'
        path.write_text(json.dumps(task))
        self.environment['CHECK_FIXTURE_REPORTED_COMMANDS'] = json.dumps([*commands, *extra_reported])
        self.job = self.successful('job', 'create', '--workspace', self.workspace, '--task', path, '--base', 'HEAD', '--json')
        executed = self.successful('job', 'run', self.job['job_id'], '--provider', 'codex', '--json')
        self.attempt = executed['attempts'][-1]
        return self.job

    def check(self, seconds=5):
        return self.invoke('job', 'check', self.job['job_id'], '--timeout', str(seconds), '--json')
