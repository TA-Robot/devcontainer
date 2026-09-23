"""Run a finite, credential-free native accounting probe in the pinned image."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
import uuid

HERE = Path(__file__).resolve().parent
SOLO = HERE.parent / 'dynamic_solo_v1'
sys.path.insert(0, str(SOLO))
import projection


def run(output, mode, *, start_seconds=75):
    if mode not in ('fork_none', 'fork_all', 'missing_usage', 'child_timeout'):
        raise ValueError('unsupported probe')
    if mode == 'child_timeout':
        start_seconds = min(start_seconds, 10)
    output = Path(output).resolve()
    output.mkdir(mode=0o700, parents=True, exist_ok=False)
    source = output / 'source'
    source.mkdir()
    for name in ('probe.py', 'accounting.py', 'run.py'):
        shutil.copyfile(HERE / name, source / name)
    policy = output / 'policy'
    policy.mkdir()
    config = json.loads((SOLO / 'policy.json').read_text())
    config['features.multi_agent'] = True
    (policy / 'policy.json').write_text(json.dumps(config))
    catalog = json.loads((SOLO / 'model-catalog.json').read_text())
    for model in catalog['models']:
        model['multi_agent_version'] = 'v2'
    (policy / 'model-catalog.json').write_text(json.dumps(catalog))
    (policy / 'mode.json').write_text(json.dumps({'mode': mode}))
    projection.prepare(output / 'public')
    work = output / 'work'
    work.mkdir()
    image = json.loads((SOLO / 'image.json').read_text())['image']
    name = 'native-accounting-probe-' + uuid.uuid4().hex
    result = {'mode': mode, 'image': image, 'container': name, 'removed': False, 'status': 'withhold',
              'source_sha256': {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in source.glob('*.py')},
              'input_sha256': {str(p.relative_to(output)): hashlib.sha256(p.read_bytes()).hexdigest()
                               for directory in (policy, output / 'public') for p in directory.iterdir()}}
    for directory in (source, policy, output / 'public'):
        for path in directory.iterdir():
            path.chmod(0o444)
    (output / 'start.json').write_text(json.dumps(result, indent=2) + '\n')
    args = ['docker', 'create', '-i', '--name', name, '--init', '--network', 'none', '--read-only',
            '--cap-drop', 'ALL', '--security-opt', 'no-new-privileges', '--security-opt', 'seccomp=unconfined',
            '--pids-limit', '256', '--memory', '2g', '--cpus', '1', '--user', f'{os.getuid()}:{os.getgid()}',
            '--log-driver', 'none', '--tmpfs', '/codex:rw,nosuid,nodev,size=64m,mode=1777',
            '--tmpfs', '/tmp:rw,nosuid,nodev,size=64m,mode=1777']
    for origin, dest, readonly in [(source, '/probe', True), (policy, '/policy', True),
                                   (output / 'public', '/public', True), (work, '/work', False)]:
        args += ['--mount', f'type=bind,src={origin},dst={dest}' + (',readonly' if readonly else '')]
    args += [image, 'python3', '/probe/probe.py']
    began = time.monotonic()
    try:
        subprocess.run(args, check=True, capture_output=True, timeout=15)
        process = subprocess.run(['docker', 'start', '-ai', name], capture_output=True, text=True, timeout=start_seconds)
        (output / 'stderr.txt').write_text(process.stderr)
        if process.returncode:
            raise ValueError('probe process failed')
        report = json.loads(process.stdout)
        (output / 'probe.json').write_text(json.dumps(report, indent=2) + '\n')
        result['probe'] = report
        accounting = report['accounting']
        expected = {k: sum(r['usage'][k] for r in report['requests'] if r['usage'])
                    for k in accounting['observed_usage']}
        result['provider_observed_usage'] = expected
        expected_status = 'withhold' if mode == 'missing_usage' else 'completed'
        observed_responses = {r['response_id']: (t['thread_id'], r['turn_id'], r['usage'])
                              for t in accounting['threads'] for r in t['responses']}
        expected_responses = {r['response_id']: (r['thread_id'], r['turn_id'], r['usage'])
                              for r in report['requests'] if r['usage']}
        if (report['exit_code'] != 0 or accounting['status'] != expected_status
                or accounting['observed_usage'] != expected or observed_responses != expected_responses
                or not report['child_public_check_valid'] or not report['child_network_denied']
                or len(accounting['threads']) != 2 or len(report['requests']) != 9
                or {t['thread_id'] for t in accounting['threads']} != {r['thread_id'] for r in report['requests']}
                or not all(r['shell_available'] and r['spawn_available'] for r in report['requests'])):
            raise ValueError('native accounting capability mismatch')
        result['status'] = 'passed'
    except (OSError, ValueError, KeyError, subprocess.SubprocessError) as exc:
        result['failure'] = str(exc)[:160]
    finally:
        result['child_running_observed'] = (work / 'child-running.txt').is_file()
        try:
            subprocess.run(['docker', 'rm', '-f', name], check=True, capture_output=True, timeout=15)
            result['removed'] = True
        except (OSError, subprocess.SubprocessError):
            result['status'] = 'withhold'
        result['elapsed_seconds'] = time.monotonic() - began
        (output / 'result.json').write_text(json.dumps(result, indent=2) + '\n')
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--mode', choices=('fork_none', 'fork_all', 'missing_usage', 'child_timeout'), required=True)
    args = parser.parse_args()
    value = run(args.output, args.mode)
    print(json.dumps(value))
    raise SystemExit(0 if value['status'] == 'passed' else 1)
