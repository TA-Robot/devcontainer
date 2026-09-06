"""A new task binding of the frozen serial pilot; no historical module globals are changed."""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import types
import uuid

import task

CONSULTATION = task.ROOT / 'experiments/development-harness/consultation'
sys.path.insert(0, str(CONSULTATION))
import codex_transport

KIND = 'queue-review-pilot-v1'
IMAGE = 'sha256:c7f904a12d7e7c63a2c7e46bc6654c8304b497a2836ecb08fb5bea0118f679ea'
PROBE = """import subprocess,tempfile
from pathlib import Path
root=Path('/workspace')
assert (root/'tools/check_queue.py').is_file()
subprocess.run(['git','status','--porcelain'],cwd=root,check=True)
with tempfile.TemporaryDirectory() as raw:
 p=Path(raw)/'probe';p.write_text('ok');assert p.read_text()=='ok'
print('CAPABILITY_OK')
"""


class Transport(codex_transport.Transport):
    def __init__(self, workspace, release, config, auth=None, fake=None):
        name = 'queue-review-participant-' + uuid.uuid4().hex
        args = ['docker', 'create', '--name', name, '--privileged', '--init',
                '--label', 'dev.agentctl.benchmark=true', '--label', 'dev.agentctl.study=' + KIND,
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
            codex_transport.public.Docker.__init__(self, container, workspace, release, {'network_access': False})
        except Exception:
            subprocess.run(['docker', 'rm', '-f', container], capture_output=True, timeout=30)
            raise
        self.expected_cli_version = config['cli_version']
        self.workspace, self.stop_seconds = workspace, config['stop_seconds']
        self.fake, self.prompt_directory = fake is not None, None


def binding(variant, image):
    if variant not in task.VARIANTS:
        raise ValueError('explicit scenario required')
    specification = importlib.util.spec_from_file_location('private_queue_pilot_binding', CONSULTATION / 'synthesis_pilot.py')
    engine = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(engine)

    def build(path):
        manifest = task.build(path, variant)
        manifest['initial_quality'] = task.evaluate(path / 'workspace', path, path / 'initial-evaluation', image)
        if manifest['initial_quality']['status'] == 'unknown':
            raise ValueError('initial behavior could not be measured')
        return manifest

    engine.task = types.SimpleNamespace(**{name: getattr(task, name) for name in
        ('ROOT', 'CAPSULE', 'CATALOG', 'inventory', 'validate_source', 'evaluate', 'prompt')}, build=build)
    engine.KIND, engine.PROBE = KIND, PROBE
    engine.codex_transport = types.SimpleNamespace(Transport=Transport)
    return engine


def live_config(variant):
    if variant not in ('repair', 'preserve'):
        raise ValueError('confirmation scenario is reserved for a later protocol')
    return {'kind': KIND, 'execution': 'live', 'variant': variant, 'model': 'gpt-6-astra', 'effort': 'high',
            'cli_version': '0.153.0', 'image': IMAGE,
            'order': ['solo', 'consult'] if variant == 'repair' else ['consult', 'solo'],
            'condition_seconds': 600, 'advisor_seconds': 120, 'advisor_minimum_seconds': 15,
            'minimum_seconds': 180, 'output_tokens': 12000, 'minimum_output_tokens': 1000,
            'stop_seconds': 10, 'capture_seconds': 30, 'capture_window_seconds': 10,
            'snapshot_bytes': 16777216, 'advice_bytes': 16384}


def run(config, output, *, auth=None, fake=None):
    engine = binding(config.get('variant'), config.get('image'))
    engine.validate(config)
    if config['execution'] == 'live':
        if config != live_config(config['variant']):
            raise ValueError('live configuration differs from fixed protocol')
        # A source-matched preflight is required, not a boolean supplied by a caller.
        from queue_calibration import verify_preflight
        verify_preflight()
        original_identity = engine.identity
        def identity_with_preflight():
            return {**original_identity(), **{str(task.HERE / name): hashlib.sha256((task.HERE / name).read_bytes()).hexdigest()
                for name in ('calibration.json', 'validation.json')}}
        engine.identity = identity_with_preflight
    result = engine.run(config, output, auth=auth, fake=fake)
    seal = json.loads((output / 'seal.json').read_text()) if (output / 'seal.json').exists() else {}
    summary = {'kind': KIND, 'variant': config['variant'], 'status': result['status'],
               'initial_quality': seal.get('fixture', {}).get('initial_quality'),
               'conditions': result['conditions'], 'all_writers_stopped': result['all_writers_stopped'],
               'general_effect_established': False, 'automatic_review_default': 'not-adopted',
               'semantic_review_adoption': 'unknown'}
    engine.runner.campaign.save(output / 'queue-summary.json', summary)
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--auth', type=Path)
    parser.add_argument('--fake-provider', type=Path)
    args = parser.parse_args()
    os.umask(0o077)
    result = run(json.loads(args.config.read_text()), args.output, auth=args.auth, fake=args.fake_provider)
    print(json.dumps({'status': result['status']}))
    raise SystemExit(result['status'] != 'completed')
