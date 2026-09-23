"""New fixed task adapters without modifying historical observers or protocols."""
import importlib.util
import json
from pathlib import Path
import subprocess
import time
import uuid


def catalog(task, legacy):
    if task != 'cli-sync-v1':
        return legacy.observer.catalog(task)
    path = Path(__file__).resolve().parents[1] / 'cycle-005/evaluate_sync.py'
    spec = importlib.util.spec_from_file_location('sync_task_oracle', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.catalog()


def evaluate_one(record, output, row, legacy):
    if record['config']['task'] != 'cli-sync-v1':
        return legacy.evaluate_one(record, output, row)
    config = record['config']
    folder = output / 'observations' / row['key']
    folder.mkdir(parents=True, mode=0o700)
    oracle = Path(__file__).resolve().parents[1] / 'cycle-005'
    name = 'sync-eval-' + uuid.uuid4().hex
    started = time.monotonic()
    try:
        subprocess.run(['docker', 'create', '--name', name, '--network', 'none', '--read-only',
            '--tmpfs', '/tmp:rw,exec,mode=1777', '-e', 'PYTHONDONTWRITEBYTECODE=1',
            '--mount', f'type=bind,src={oracle},dst=/oracle,readonly',
            '--mount', f'type=bind,src={row["source"]},dst=/candidate,readonly',
            '--mount', f'type=bind,src={folder},dst=/results', config['image'],
            'python3', '/oracle/evaluate_sync.py', '--candidate', '/candidate', '--output', '/results/result.json'],
            capture_output=True, check=True, timeout=30)
        context = json.loads(subprocess.check_output(['docker', 'inspect', name], text=True, timeout=10))[0]
        legacy.campaign.save(folder / 'context.json', {'image': context['Image'], 'mounts': context['Mounts'],
            'network': context['HostConfig']['NetworkMode'], 'read_only': context['HostConfig']['ReadonlyRootfs']})
        with (folder / 'observer.log').open('w') as stream:
            result = subprocess.run(['docker', 'start', '-a', name], stdout=stream, stderr=subprocess.STDOUT,
                timeout=max(.01, config['observer_seconds'] - (time.monotonic() - started)))
        value = legacy.campaign.read(folder / 'result.json') if result.returncode == 0 else None
        quality = legacy.grade(value, record['catalog'])
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        quality = {'accepted': None, 'measurement': 'unknown', 'reason': type(error).__name__, 'checks': []}
    finally:
        subprocess.run(['docker', 'rm', '-f', name], capture_output=True, timeout=30)
    response = {**row, 'quality': quality, 'observer_seconds': time.monotonic() - started}
    legacy.campaign.save(folder / 'observation.json', response)
    return response
