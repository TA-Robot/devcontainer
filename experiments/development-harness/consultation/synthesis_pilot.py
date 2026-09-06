"""Finite, sealed F12-L solo/advice pilot using the existing terminal and sandbox."""
import argparse
import copy
import hashlib
import json
import math
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time
import traceback

import codex_transport
import synthesis_task as task
import flow_v1 as prior
runner = codex_transport.runner
sys.path.insert(0, str(task.ROOT / 'scripts'))
from agent_duration_live import _validate_provider_credential_window

KIND = 'synthesis-consultation-pilot-v1'
ACTORS = ('solo-maker', 'consult-advisor', 'consult-maker')
PROBE = """import json,subprocess,tempfile
from pathlib import Path
root=Path('/workspace')
assert (root/'decision-contract.json').is_file()
subprocess.run(['git','status','--porcelain'],cwd=root,check=True)
with tempfile.TemporaryDirectory() as raw:
 p=Path(raw)/'probe';p.write_text('ok');assert p.read_text()=='ok'
print('CAPABILITY_OK')
"""


def validate(config):
    if config.get('kind') != KIND or config.get('execution') not in ('calibration', 'live'):
        raise ValueError('explicit version and execution mode required')
    if config.get('order') not in (['solo', 'consult'], ['consult', 'solo']):
        raise ValueError('explicit paired order required')
    if not re.fullmatch(r'sha256:[0-9a-f]{64}', config.get('image', '')):
        raise ValueError('pinned image required')
    for key in ('model', 'effort', 'cli_version'):
        if not isinstance(config.get(key), str) or not config[key].strip():
            raise ValueError('explicit provider settings required')
    for key in ('condition_seconds', 'advisor_seconds', 'advisor_minimum_seconds', 'minimum_seconds', 'stop_seconds',
                'capture_seconds', 'capture_window_seconds'):
        value = config.get(key)
        if type(value) not in (float, int) or not math.isfinite(value) or value <= 0:
            raise ValueError('invalid cap ' + key)
    for key in ('output_tokens', 'minimum_output_tokens', 'snapshot_bytes', 'advice_bytes'):
        if type(config.get(key)) is not int or config[key] <= 0:
            raise ValueError('invalid cap ' + key)
    if config['advice_bytes'] > 16384 or config['condition_seconds'] < 2 * config['minimum_seconds']:
        raise ValueError('invalid envelope/reservation')
    if config['output_tokens'] < 2 * config['minimum_output_tokens']:
        raise ValueError('missing participant token reservation')
    if config['advisor_minimum_seconds'] > config['advisor_seconds']:
        raise ValueError('advisor minimum exceeds its cap')


def identity():
    paths = list((task.ROOT / 'scripts').rglob('*.py'))
    paths += list((task.ROOT / 'experiments/development-harness').rglob('*.py'))
    paths += [task.CAPSULE, task.CATALOG, Path(__file__).with_name('synthesis-protocol.md')]
    return {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(paths)}


def actor_manifest(config, condition, role, seconds, tokens, advice):
    text = task.prompt(role, advice)
    values = {'schema_version': 2, 'clock': runner.CLOCK, 'study_id': KIND,
              'condition': 'control' if condition == 'solo' else 'improved', 'scale': 'small',
              'model': config['model'], 'effort': config['effort'], 'cli_version': config['cli_version'],
              'max_seconds': seconds, 'max_sessions': 1, 'max_output_tokens': tokens,
              'max_snapshot_bytes': config['snapshot_bytes'],
              'phases': [{'id': role, 'prompt': text, 'prompt_sha256': prior.digest(text.encode()), 'seconds': seconds}],
              'admission': {'schema_version': 1, 'kind': 'planning_prior', 'scope': KIND,
                            'rationale': 'retain finite maker budget after advice', 'owner': 'primary/integrator',
                            'update_when': 'new sealed task or runtime', 'stages': {role: {
                                'minimum_seconds': config['advisor_minimum_seconds'] if role == 'advisor' else config['minimum_seconds'],
                                'minimum_output_tokens': config['minimum_output_tokens']}}}}
    values.update({k: config[k] for k in ('stop_seconds', 'capture_seconds', 'capture_window_seconds')})
    runner.validate(values)
    return values


def difference_paths(left, right, prefix=''):
    if isinstance(left, dict) and isinstance(right, dict):
        return [path for key in sorted(set(left) | set(right))
                for path in difference_paths(left.get(key), right.get(key), prefix + '/' + key)]
    if isinstance(left, list) and isinstance(right, list) and len(left) == len(right):
        return [path for i, (a, b) in enumerate(zip(left, right))
                for path in difference_paths(a, b, prefix + '/' + str(i))]
    return [] if left == right else [prefix]


def read_advice(source, cap):
    if (source / 'advice.json').stat().st_size > cap:
        raise ValueError('advice exceeds cap')
    value = prior.observe.read_json(source / 'advice.json')
    if (not isinstance(value, dict) or set(value) != {'recommendation', 'evidence', 'uncertainty'}
            or any(not isinstance(value[k], str) or not value[k].strip() for k in ('recommendation', 'uncertainty'))
            or not isinstance(value['evidence'], list) or not value['evidence']
            or any(not isinstance(v, str) or not v.strip() for v in value['evidence'])):
        raise ValueError('invalid advice')
    return value


def _run(config, output, *, auth=None, fake=None, cancelled=None):
    validate(config)
    if (config['execution'] == 'live') != (auth is not None) or (config['execution'] == 'calibration') != (fake is not None):
        raise ValueError('live needs private auth only; calibration needs deterministic provider only')
    config = copy.deepcopy(config)
    output = output.resolve()
    output.mkdir(parents=True, mode=0o700, exist_ok=False)
    started = time.monotonic()
    seal = identity()
    result = {'kind': KIND, 'execution': config['execution'], 'status': 'preparing', 'conditions': {},
              'failure': None, 'all_writers_stopped': False, 'speed_ratio': None,
              'requested_model': config['model'], 'requested_effort': config['effort'],
              'resolved_model': None, 'applied_effort': None, 'monetary_cost': None}
    transports = {}
    credential = output / 'auth.json'
    baseline = output / 'private-fixture'
    try:
        if auth is not None:
            checked = _validate_provider_credential_window('codex', auth,
                timeout_seconds=2 * config['condition_seconds'] + 600)
            shutil.copyfile(checked, credential)
            credential.chmod(0o600)
        fixture = task.build(baseline)
        base_identity = task.inventory(baseline / 'workspace')
        release = output / 'public-checks'
        release.mkdir()
        (release / 'capability.py').write_text(PROBE)
        (release / 'capability.py').chmod(0o444)
        environments = []
        for index, actor in enumerate(ACTORS):
            workspace = output / ('workspace-' + str(index))
            shutil.copytree(baseline / 'workspace', workspace)
            transport = codex_transport.Transport(workspace, release, config,
                        credential if auth else None, fake)
            transports[actor] = transport
            if transport.image != config['image']:
                raise ValueError('actual image differs from pinned image')
            environments.append(transport.environment())
        if any(e != environments[0] for e in environments):
            raise ValueError('participant environments differ: ' + ','.join(
                path for e in environments[1:] for path in difference_paths(environments[0], e)))
        runner.campaign.save(output / 'seal.json', {'config': config, 'code_sha256': seal,
            'fixture': fixture, 'source_sha256': base_identity, 'environment': environments[0],
            'public_capability_sha256': prior.digest(PROBE.encode())})
        for actor, transport in transports.items():
            if cancelled:
                raise ValueError('cancelled during preparation')
            probe = transport.probe()
            runner.campaign.save(output / (actor + '-probe.private.json'), probe)
            if task.inventory(transport.workspace) != base_identity:
                raise ValueError('capability probe changed task inputs')
        result['preparation_seconds'] = time.monotonic() - started
        if cancelled or identity() != seal:
            raise ValueError('cancelled or sealed code changed before execution')
        runner.campaign.save(output / 'execution-started.json', {'unix': time.time()})
        if not cancelled:
            for condition in config['order']:
                begin = time.monotonic()
                deadline = begin + config['condition_seconds']
                row = {'status': 'running', 'actors': [], 'quality': None, 'advice': None,
                       'usage_complete': True, 'usage': {'input_tokens': 0, 'cached_input_tokens': 0, 'output_tokens': 0},
                       'usage_sum_scope': 'observed records only; missing total usage remains unknown'}
                result['conditions'][condition] = row
                advice = None
                for role in (['maker'] if condition == 'solo' else ['advisor', 'maker']):
                    if cancelled or identity() != seal:
                        raise ValueError('cancelled or sealed code changed')
                    reserved = config['minimum_seconds'] if role == 'advisor' else 0
                    tokens = config['output_tokens'] - row['usage']['output_tokens'] - (config['minimum_output_tokens'] if reserved else 0)
                    seconds = deadline - time.monotonic() - reserved
                    if role == 'advisor':
                        seconds = min(seconds, config['advisor_seconds'])
                    minimum = config['advisor_minimum_seconds'] if role == 'advisor' else config['minimum_seconds']
                    if seconds < minimum or tokens < config['minimum_output_tokens']:
                        raise ValueError('remaining participant budget unavailable')
                    actor = condition + '-' + role
                    transport = transports[actor]
                    state_path = output / (actor + '-state')
                    manifest = actor_manifest(config, condition, role, seconds, tokens, advice)
                    runner.initialize(manifest, transport.workspace, state_path, transport)
                    transport.prompt_directory = state_path
                    with runner.locked(state_path):
                        state = runner._run_stage(state_path, transport, deadline=deadline - reserved)
                    session = state['sessions'][0]
                    row['actors'].append({'role': role, 'status': state['status'], 'clock': session['clock'],
                        'usage_complete': session['usage_complete'], 'state': state_path.name,
                        'actual_prompt_sha256': prior.digest(manifest['phases'][0]['prompt'].encode())})
                    row['usage_complete'] &= session['usage_complete']
                    prior.add_usage(row['usage'], session['observation'])
                    if not session['stop_evidence'].get('stopped') or not session['artifact']:
                        raise ValueError('participant stop/archive unavailable')
                    transport.stopped()
                    source = output / (actor + '-artifact')
                    runner.legacy.extract(state_path / session['directory'] / 'terminal/workspace.tar',
                        session['artifact']['sha256']['workspace.tar'], source, config['snapshot_bytes'])
                    if role == 'maker':
                        row['source'] = source.name
                    if not runner.assess(state)['submitted_within_budget'] or session['capture_window_ok'] is not True:
                        raise ValueError('participant incomplete or outside budget/window')
                    task.validate_source(source, baseline / 'workspace', role)
                    if role == 'advisor':
                        advice = read_advice(source, config['advice_bytes'])
                        row['advice'] = {'delivered': True, 'sha256': prior.digest((source / 'advice.json').read_bytes()),
                                         'semantic_adoption': 'unknown'}
                row['execution_seconds'] = time.monotonic() - begin
                row['status'] = 'submitted'
                if row['execution_seconds'] > config['condition_seconds']:
                    raise ValueError('condition budget exceeded')
        result['status'] = 'executed'
    except Exception as error:
        (output / 'controller.private.log').write_text(traceback.format_exc())
        (output / 'controller.private.log').chmod(0o600)
        result.update(status='interrupted', failure=type(error).__name__)
        if result['conditions']:
            row['status'] = 'halted'
            row['execution_seconds'] = time.monotonic() - begin
    finally:
        proofs = []
        for transport in transports.values():
            try:
                transport.stop_bounded(config['stop_seconds'])
                proofs.append(transport.stopped())
            except Exception:
                proofs.append({'stopped': False})
        result['all_writers_stopped'] = all(p.get('stopped') is True for p in proofs)
        result['stop_proofs'] = proofs
        for condition in config['order']:
            result['conditions'].setdefault(condition, {'status': 'not_started', 'quality': None})
        runner.campaign.save(output / 'execution.json', result)
    try:
        if not result['all_writers_stopped']:
            raise ValueError('no all-writer stop proof')
        if identity() != seal:
            raise ValueError('sealed evaluator changed')
        for condition, row in result['conditions'].items():
            if not row.get('source'):
                continue
            evaluation_started = time.monotonic()
            try:
                row['quality'] = task.evaluate(output / row['source'], baseline, output / (condition + '-evaluation'), config['image'])
            except Exception as error:
                row['quality'] = {'status': 'unknown', 'reason': type(error).__name__}
            row['evaluation_seconds'] = time.monotonic() - evaluation_started
        if result['status'] == 'executed':
            result['status'] = 'completed'
    except Exception as error:
        result.update(status='interrupted', failure='evaluation-' + type(error).__name__)
    finally:
        # Only the containers created by this invocation are removed.
        result['cleanup'] = []
        for transport in transports.values():
            try:
                done = subprocess.run(['docker', 'rm', '-f', transport.identity], capture_output=True, timeout=30)
                removed = done.returncode == 0
            except (OSError, subprocess.SubprocessError):
                removed = False
            result['cleanup'].append({'container_id': transport.identity, 'removed': removed})
        credential.unlink(missing_ok=True)
        result['total_seconds'] = time.monotonic() - started
        runner.campaign.save(output / 'result.json', result)
    return result


def run(config, output, *, auth=None, fake=None):
    with runner.cancellation() as cancelled:
        return _run(config, output, auth=auth, fake=fake, cancelled=cancelled)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--auth', type=Path)
    parser.add_argument('--fake-provider', type=Path)
    args = parser.parse_args()
    os.umask(0o077)
    result = run(json.loads(args.config.read_text()), args.output, auth=args.auth, fake=args.fake_provider)
    print(json.dumps({'status': result['status'], 'conditions': {k: v['status'] for k, v in result['conditions'].items()}}))
    raise SystemExit(result['status'] != 'completed')
