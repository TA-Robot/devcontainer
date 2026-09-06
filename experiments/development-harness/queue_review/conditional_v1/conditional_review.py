"""Finite draft -> optional review -> final flow, shared by both information conditions."""
import argparse
import copy
import hashlib
import json
import math
import os
from pathlib import Path
import shutil
import subprocess
import time
import traceback

import route_contract as contract

base = contract.transport_module.binding('confirmation', contract.IMAGE)
runner, prior = base.runner, base.prior
CONDITIONS = ('control', 'informed')


def live_config():
    order = list(CONDITIONS)
    if hashlib.sha256(contract.KIND.encode()).digest()[0] % 2:
        order.reverse()
    return {'kind': contract.KIND, 'execution': 'live', 'image': contract.IMAGE,
            'model': 'gpt-6-astra', 'effort': 'high', 'cli_version': '0.153.0', 'order': order,
            'condition_seconds': 600, 'draft_seconds': 300, 'draft_minimum_seconds': 30,
            'advisor_seconds': 120, 'advisor_minimum_seconds': 15, 'minimum_seconds': 60,
            'final_reserve_seconds': 120, 'output_tokens': 12000, 'minimum_output_tokens': 1000,
            'stop_seconds': 10, 'capture_seconds': 30, 'capture_window_seconds': 10,
            'snapshot_bytes': 16777216, 'advice_bytes': 16384, 'request_bytes': 8192}


def validate(config):
    if config.get('order') not in (list(CONDITIONS), list(reversed(CONDITIONS))):
        raise ValueError('explicit condition order required')
    translated = {**config, 'order': ['solo', 'consult']}
    base.validate(translated)
    for key in ('draft_seconds', 'draft_minimum_seconds', 'final_reserve_seconds'):
        if type(config.get(key)) not in (int, float) or not math.isfinite(config[key]) or config[key] <= 0:
            raise ValueError('invalid cap ' + key)
    if (type(config.get('request_bytes')) is not int or not 0 < config['request_bytes'] <= 8192
            or config['final_reserve_seconds'] < config['minimum_seconds']
            or config['draft_seconds'] < config['draft_minimum_seconds']
            or config['condition_seconds'] < config['draft_minimum_seconds'] + config['advisor_minimum_seconds'] + config['final_reserve_seconds']
            or config['output_tokens'] < 3 * config['minimum_output_tokens']):
        raise ValueError('missing three-stage budget reservations')


def allowance(config, stage, remaining_seconds, remaining_tokens):
    reserve_seconds = (config['final_reserve_seconds'] + config['advisor_minimum_seconds'] if stage == 'drafter'
                       else config['final_reserve_seconds'] if stage == 'reviewer' else 0)
    reserve_tokens = config['minimum_output_tokens'] * (2 if stage == 'drafter' else 1 if stage == 'reviewer' else 0)
    cap = config['draft_seconds'] if stage == 'drafter' else config['advisor_seconds'] if stage == 'reviewer' else remaining_seconds
    minimum = config['draft_minimum_seconds'] if stage == 'drafter' else config['advisor_minimum_seconds'] if stage == 'reviewer' else config['minimum_seconds']
    seconds, tokens = min(cap, remaining_seconds - reserve_seconds), remaining_tokens - reserve_tokens
    if seconds < minimum or tokens < config['minimum_output_tokens']:
        raise ValueError('remaining stage budget unavailable')
    return seconds, tokens, minimum, reserve_seconds


def verify_preflight():
    path = contract.HERE / 'validation.json'
    value = json.loads(path.read_text())
    if (value.get('status') != 'pass' or value.get('image') != contract.IMAGE
            or value.get('source_sha256') != contract.identity()
            or value.get('verified_routes') != ['submit', 'consult', 'unknown-usage', 'invalid-request', 'invalid-advice']):
        raise ValueError('source-matched route preflight required')


def _run(config, output, auth, fake, cancelled):
    validate(config)
    if (config['execution'] == 'live') != (auth is not None) or (config['execution'] == 'calibration') != (fake is not None):
        raise ValueError('live auth and deterministic calibration are exclusive')
    if config['execution'] == 'live':
        if config != live_config():
            raise ValueError('live configuration differs from fixed protocol')
        verify_preflight()
    config = copy.deepcopy(config)
    output = output.resolve()
    output.mkdir(parents=True, mode=0o700, exist_ok=False)
    started = time.monotonic()
    identity = contract.identity()
    preflight_digest = contract.digest(contract.HERE / 'validation.json') if config['execution'] == 'live' else None
    baseline = output / 'fixture'
    credential = output / 'auth.json'
    transports = []
    result = {'kind': contract.KIND, 'config': config, 'status': 'preparing', 'conditions': {},
              'initial_quality': None, 'all_writers_stopped': False, 'failure': None,
              'requested_model': config['model'], 'requested_effort': config['effort'],
              'resolved_model': None, 'applied_effort': None, 'monetary_cost': None}
    environment = None
    current = None

    def unchanged():
        if cancelled or contract.identity() != identity:
            raise ValueError('cancelled or sealed source changed')
        if preflight_digest and contract.digest(contract.HERE / 'validation.json') != preflight_digest:
            raise ValueError('preflight changed')

    def execute(condition, stage, row, deadline, source=None, request=None, advice=None):
        nonlocal environment
        unchanged()
        prefix = condition + '-' + stage
        workspace = output / (prefix + '-workspace')
        expected = contract.project(baseline / 'workspace', workspace, source)
        stage_baseline = output / (prefix + '-input')
        shutil.copytree(workspace, stage_baseline)
        transport = contract.transport_module.Transport(workspace, release, config,
                                                        credential if auth else None, fake)
        transports.append(transport)
        observed_environment = transport.environment()
        if transport.image != config['image'] or environment is not None and observed_environment != environment:
            raise ValueError('participant environment mismatch')
        if environment is None:
            runner.campaign.save(output / 'environment.json', observed_environment)
            result['environment_sha256'] = hashlib.sha256(json.dumps(observed_environment, sort_keys=True).encode()).hexdigest()
        environment = observed_environment
        runner.campaign.save(output / (prefix + '-probe.private.json'), transport.probe())
        if contract.queue.inventory(workspace) != expected:
            raise ValueError('probe changed stage input')
        seconds, tokens, minimum, reserve = allowance(config, stage, deadline - time.monotonic(), row['usage']['output_tokens_remaining'])
        text = contract.prompt(stage, condition, request, advice)
        base.task.prompt = lambda role, advice: text
        manifest = base.actor_manifest({**config, 'minimum_seconds': minimum},
            'solo' if condition == 'control' else 'consult', 'advisor' if stage == 'reviewer' else 'maker', seconds, tokens, None)
        state_path = output / (prefix + '-state')
        runner.initialize(manifest, workspace, state_path, transport)
        transport.prompt_directory = state_path
        unchanged()
        with runner.locked(state_path):
            state = runner._run_stage(state_path, transport, deadline=deadline - reserve)
        session = state['sessions'][0]
        row['actors'].append({'stage': stage, 'state': state_path.name, 'status': state['status'],
            'usage_complete': session['usage_complete'], 'clock': session['clock'],
            'prompt_sha256': hashlib.sha256(text.encode()).hexdigest(), 'input_sha256': expected,
            'environment_sha256': hashlib.sha256(json.dumps(environment, sort_keys=True).encode()).hexdigest()})
        if stage == 'reviewer':
            row['route']['review_dispatched'] = True
        totals = {key: row['usage'][key] for key in ('input_tokens', 'cached_input_tokens', 'output_tokens')}
        prior.add_usage(totals, session['observation'])
        row['usage'].update(totals)
        row['usage_complete'] &= session['usage_complete']
        if not session['stop_evidence'].get('stopped') or not session['artifact']:
            raise ValueError('stage stop/archive unavailable')
        transport.stopped()
        artifact = output / (prefix + '-artifact')
        runner.legacy.extract(state_path / session['directory'] / 'terminal/workspace.tar',
                              session['artifact']['sha256']['workspace.tar'], artifact, config['snapshot_bytes'])
        row['actors'][-1]['artifact'] = artifact.name
        if not runner.assess(state)['submitted_within_budget'] or session['capture_window_ok'] is not True:
            raise ValueError('stage incomplete or outside budget/window')
        row['actors'][-1]['source_sha256'] = contract.validate_source(artifact, stage_baseline, stage)
        row['usage']['output_tokens_remaining'] = config['output_tokens'] - totals['output_tokens']
        return artifact

    try:
        fixture = contract.build(baseline)
        result['initial_quality'] = contract.queue.evaluate(baseline / 'workspace', baseline, output / 'initial-evaluation', config['image'])
        if result['initial_quality']['status'] != 'fail':
            raise ValueError('confirmation baseline is not the expected behavioral failure')
        if auth is not None:
            checked = base._validate_provider_credential_window('codex', auth, timeout_seconds=2 * config['condition_seconds'] + 600)
            shutil.copyfile(checked, credential)
            credential.chmod(0o600)
        release = output / 'public-checks'
        release.mkdir()
        (release / 'capability.py').write_text(contract.transport_module.PROBE)
        runner.campaign.save(output / 'seal.json', {'config': config, 'code_sha256': identity,
            'fixture': fixture, 'preflight_sha256': preflight_digest})
        result['preparation_seconds'] = time.monotonic() - started
        for condition in config['order']:
            begin = time.monotonic()
            deadline = begin + config['condition_seconds']
            current = {'status': 'running', 'actors': [], 'route': None, 'quality': None, 'draft_quality': None,
                       'usage_complete': True, 'usage': {'input_tokens': 0, 'cached_input_tokens': 0,
                       'output_tokens': 0, 'output_tokens_remaining': config['output_tokens']}}
            result['conditions'][condition] = current
            draft = execute(condition, 'drafter', current, deadline)
            current['draft_source'] = draft.name
            request = contract.read_request(draft, config['request_bytes'], prior.observe.read_json)
            current['route'] = {'action': request['action'], 'request_sha256': contract.digest(draft / contract.REQUEST),
                                'semantic_need': 'unknown', 'review_dispatch_attempted': False, 'review_dispatched': False}
            final = draft
            if request['action'] == 'consult':
                current['route']['review_dispatch_attempted'] = True
                reviewed = execute(condition, 'reviewer', current, deadline, draft, request)
                advice = base.read_advice(reviewed, config['advice_bytes'])
                current['route']['advice_sha256'] = contract.digest(reviewed / 'advice.json')
                final = execute(condition, 'final', current, deadline, draft, request, advice)
            current['source'] = final.name
            current['execution_seconds'] = time.monotonic() - begin
            if current['execution_seconds'] > config['condition_seconds']:
                raise ValueError('condition exceeded shared budget')
            current['status'] = 'submitted'
        unchanged()
        result['status'] = 'executed'
    except Exception as error:
        (output / 'controller.private.log').write_text(traceback.format_exc())
        result.update(status='interrupted', failure=type(error).__name__)
        if current is not None:
            current.update(status='halted', execution_seconds=time.monotonic() - begin)
    finally:
        proofs = []
        for transport in transports:
            try:
                transport.stop_bounded(config['stop_seconds'])
                proofs.append(transport.stopped())
            except Exception:
                proofs.append({'stopped': False})
        result['all_writers_stopped'] = all(p.get('stopped') is True for p in proofs)
        result['stop_proofs'] = proofs
        for name in CONDITIONS:
            result['conditions'].setdefault(name, {'status': 'not_started', 'quality': None})
        runner.campaign.save(output / 'execution.json', result)
    try:
        if not result['all_writers_stopped']:
            raise ValueError('all-writer stop proof missing')
        unchanged()
        for name, row in result['conditions'].items():
            for field, key in (('draft_source', 'draft_quality'), ('source', 'quality')):
                if field not in row:
                    continue
                if key == 'quality' and row[field] == row.get('draft_source'):
                    row[key] = copy.deepcopy(row['draft_quality'])
                    continue
                projection = output / (name + '-' + key + '-projection')
                record = next(a for a in row['actors'] if a.get('artifact') == row[field])
                if contract.queue.inventory(output / row[field]) != record['source_sha256']:
                    raise ValueError('archived source changed')
                contract.project(baseline / 'workspace', projection, output / row[field])
                if contract.queue.inventory(output / row[field]) != record['source_sha256']:
                    raise ValueError('archived source changed during projection')
                row[key] = contract.queue.evaluate(projection, baseline, output / (name + '-' + key + '-evaluation'), config['image'])
        if result['status'] == 'executed':
            result['status'] = 'completed'
    except Exception as error:
        result.update(status='interrupted', failure='evaluation-' + type(error).__name__)
    finally:
        result['cleanup'] = []
        for transport in transports:
            try:
                removed = subprocess.run(['docker', 'rm', '-f', transport.identity], capture_output=True, timeout=30).returncode == 0
            except (OSError, subprocess.SubprocessError):
                removed = False
            result['cleanup'].append({'container_id': transport.identity, 'removed': removed})
        credential.unlink(missing_ok=True)
        result['private_credential_copy_removed'] = not credential.exists()
        result['total_seconds'] = time.monotonic() - started
        runner.campaign.save(output / 'result.json', result)
    return result


def run(config, output, *, auth=None, fake=None):
    with runner.cancellation() as cancelled:
        return _run(config, output, auth, fake, cancelled)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--auth', type=Path)
    parser.add_argument('--fake-provider', type=Path)
    args = parser.parse_args()
    os.umask(0o077)
    value = run(json.loads(args.config.read_text()), args.output, auth=args.auth, fake=args.fake_provider)
    print(json.dumps({'status': value['status']}))
    raise SystemExit(value['status'] != 'completed')
