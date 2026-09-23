"""Pinned Codex transport and model-free sandbox probe for the synthesis pilot."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import uuid

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / 'feedback'))
import public_checks as public
runner = public.runner


class Transport(public.Docker):
    def __init__(self, workspace, release, config, auth=None, fake=None):
        name = 'consultation-pilot-' + uuid.uuid4().hex
        args = ['docker', 'create', '--name', name, '--privileged', '--init',
                '--label', 'dev.agentctl.benchmark=true', '--label', 'dev.agentctl.study=consultation-synthesis-v1',
                '--mount', f'type=bind,src={workspace},dst=/workspace',
                '--mount', f'type=bind,src={release},dst=/public-checks,readonly',
                '-e', 'MIRA_COMPANION_ENABLED=0', '-e', 'PYTHONDONTWRITEBYTECODE=1',
                '-e', 'DEVCONTAINER_AI_CLI_CHANNEL=stable', '-e', 'DEVCONTAINER_CODEX_DANGEROUS_DEFAULT=0']
        if auth is not None:
            args += ['--mount', f'type=bind,src={auth},dst=/home/devuser/.codex/auth.json,readonly']
        if fake is not None:
            args += ['--mount', f'type=bind,src={fake},dst=/calibration,readonly']
        args += ['--entrypoint', '/usr/bin/sleep', config['image'], 'infinity']
        container = subprocess.check_output(args, text=True, timeout=30).strip()
        try:
            super().__init__(container, workspace, release, {'network_access': False})
        except Exception:
            subprocess.run(['docker', 'rm', '-f', container], capture_output=True, timeout=30)
            raise
        self.expected_cli_version = config['cli_version']
        self.workspace = workspace
        self.stop_seconds = config['stop_seconds']
        self.fake = fake is not None
        self.prompt_directory = None

    def environment(self):
        value = super().environment()
        # Docker can reorder distinct --env entries between otherwise equal creates.
        # Duplicate keys are ambiguous and must not be normalized away.
        environment = value['config'].get('Env', [])
        names = [entry.split('=', 1)[0] for entry in environment]
        if len(names) != len(set(names)):
            raise ValueError('duplicate environment variable names')
        value['config']['Env'] = sorted(environment)
        return value

    def argv(self, manifest, seconds):
        original = super().argv(manifest, seconds)
        actual = manifest['phases'][0]['prompt'].encode()
        if self.fake:
            original = ['docker', 'exec', '-i', self.identity, 'python3', '-B', '/calibration/provider.py']
        path = self.prompt_directory / 'actual-prompt.private.txt'
        path.write_bytes(actual)
        path.chmod(0o600)
        spec = self.prompt_directory / 'relay.private.json'
        runner.campaign.save(spec, {'terminal_prompt_sha256': hashlib.sha256(runner.prompt_for(manifest, 0)).hexdigest(),
            'actual_prompt': str(path), 'actual_prompt_sha256': hashlib.sha256(actual).hexdigest(), 'argv': original})
        return [sys.executable, str(HERE / 'prompt_relay.py'), str(spec)]

    def probe(self):
        self.start()
        try:
            argv = self.check_argv({'argv': ['python3', '/public-checks/capability.py']})
            value = public.bounded(argv, 30, 32768, [])
            runner.campaign.save(self.release.parent / (self.identity + '-probe.private.json'), value)
            if value['exit_code'] != 0 or value['reason'] is not None:
                raise ValueError('sandbox capability unavailable; see private probe log')
            return value
        finally:
            self.stop_bounded(self.stop_seconds)
            self.stopped()
