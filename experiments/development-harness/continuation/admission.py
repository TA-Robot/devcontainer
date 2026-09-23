#!/usr/bin/env python3
"""Prospective campaign admission; the frozen campaign implementation is retained."""
import argparse
import fcntl
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import subprocess
import sys

SPEC = importlib.util.spec_from_file_location('frozen_campaign', Path(__file__).resolve().parents[1] / 'campaign.py')
campaign = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(campaign)


def policy_for(manifest):
    policy = manifest.get('admission')
    if policy is None:
        return None
    if not isinstance(policy, dict) or policy.get('schema_version') != 1:
        raise campaign.CampaignError('unsupported admission policy')
    for field in ('scope', 'rationale', 'owner', 'update_when'):
        if not isinstance(policy.get(field), str) or not policy[field].strip():
            raise campaign.CampaignError('admission policy requires ' + field)
    if policy.get('kind') != 'planning_prior':
        raise campaign.CampaignError('stage minimums must be declared as planning_prior')
    stages = policy.get('stages')
    if not isinstance(stages, dict) or set(stages) != {p['id'] for p in manifest['phases']}:
        raise campaign.CampaignError('admission minimums must cover exactly the declared phases')
    for phase in manifest['phases']:
        row = stages[phase['id']]
        if not isinstance(row, dict):
            raise campaign.CampaignError('invalid stage minimums')
        for field in ('minimum_seconds', 'minimum_output_tokens'):
            campaign.positive(row.get(field), field)
        if type(row['minimum_output_tokens']) is not int:
            raise campaign.CampaignError('minimum output tokens must be integers')
        if row['minimum_seconds'] > phase['seconds']:
            raise campaign.CampaignError('stage minimum exceeds its wall cap')
    for field, cap in [('minimum_seconds', 'max_seconds'), ('minimum_output_tokens', 'max_output_tokens')]:
        if sum(row[field] for row in stages.values()) > manifest[cap]:
            raise campaign.CampaignError('stage minimums exceed whole-campaign cap')
    return policy


def assess(state):
    """Read only: unknown usage and unavailable future-stage budgets deny launch.

    Stage minimums reserve admission headroom, not provider-enforced token quotas.
    This report is neither proof of stopped processes nor acceptance of quality.
    """
    manifest = state['manifest']
    campaign.validate(manifest)
    encoded = json.dumps(manifest, sort_keys=True, ensure_ascii=False, allow_nan=False).encode()
    if campaign.digest(encoded) != state['manifest_sha256']:
        raise campaign.CampaignError('stored manifest changed after initialization')
    policy = policy_for(manifest)
    sessions = state['sessions']
    total = 0.0
    output = 0
    submitted_phases = 0
    complete_usage = state['usage_complete'] is True
    for session in sessions:
        observation = session['observation']
        if (submitted_phases >= len(manifest['phases'])
                or session['phase'] != manifest['phases'][submitted_phases]['id']):
            raise campaign.CampaignError('session order differs from released phases')
        if observation['exit_code'] == 0 and observation['stop_reason'] is None:
            submitted_phases += 1
        seconds = observation['wall_seconds']
        if isinstance(seconds, bool) or not isinstance(seconds, (int, float)) or not math.isfinite(seconds) or seconds < 0:
            raise campaign.CampaignError('invalid recorded duration')
        total += seconds
        usage = observation['usage']
        complete_usage &= bool(usage) and observation['parse_errors'] == 0
        for row in usage:
            for field in ('input_tokens', 'output_tokens'):
                if type(row.get(field)) is not int or row[field] < 0:
                    raise campaign.CampaignError('invalid recorded usage')
            output += row['output_tokens']
    # Recovery may conservatively charge time without a completed session.
    recovery = state.get('recovery')
    if recovery:
        campaign.positive(recovery['charged_seconds'], 'recovery charge')
        total += recovery['charged_seconds']
        complete_usage = False
    if (type(state['output_tokens']) is not int or output != state['output_tokens']
            or isinstance(state['total_seconds'], bool)
            or not math.isclose(total, state['total_seconds'], rel_tol=0, abs_tol=1e-6)):
        raise campaign.CampaignError('cumulative usage/duration does not match recorded sessions')
    index = state['next_phase']
    if type(index) is not int or not 0 <= index <= len(manifest['phases']):
        raise campaign.CampaignError('invalid next phase')
    if index != submitted_phases:
        raise campaign.CampaignError('next phase differs from completed session records')
    remaining = {'seconds': manifest['max_seconds'] - total,
                 'output_tokens': manifest['max_output_tokens'] - output,
                 'sessions': manifest['max_sessions'] - len(sessions)}
    exceeded = [name for name, value in remaining.items() if value < 0]
    reasons = []
    if exceeded:
        reasons.append('observed_budget_exceeded')
    if not complete_usage:
        reasons.append('usage_unknown')
    if state['status'] != 'ready':
        reasons.append('state_not_ready')
    if state.get('active'):
        reasons.append('active_session_requires_ownership_review')
    if index == len(manifest['phases']):
        reasons.append('all_phases_submitted')
    elif any(value <= 0 for value in remaining.values()):
        reasons.append('admission_cap_exhausted')
    reserve = None
    if policy and index < len(manifest['phases']):
        future = [policy['stages'][p['id']] for p in manifest['phases'][index:]]
        reserve = {'seconds': sum(p['minimum_seconds'] for p in future),
                   'output_tokens': sum(p['minimum_output_tokens'] for p in future),
                   'sessions': len(future)}
        if any(remaining[k] < reserve[k] for k in reserve):
            reasons.append('remaining_stage_minimums_unavailable')
    if policy is None:
        reasons.append('prospective_admission_policy_absent')
    return {'schema_version': 1, 'study_id': manifest['study_id'], 'condition': manifest['condition'],
            'controller_status': state['status'], 'admitted': not reasons, 'reasons': reasons,
            'remaining': remaining, 'minimums_for_unsubmitted_stages': reserve,
            'observed_budget_exceeded': exceeded, 'usage_complete': complete_usage,
            'submitted_within_observed_budget': (state['status'] == 'submitted'
                and index == len(manifest['phases']) and complete_usage and not exceeded
                and not state.get('active')),
            'quality_accepted': None, 'container_stopped': None,
            'within_turn_output_enforcement': False,
            'policy': policy, 'next_phase': index}


def run(output, transport_factory):
    """Use the same exclusive lock as the legacy entrypoint; never replay a run."""
    with (output / 'campaign.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        raw = (output / 'state.json').read_bytes()
        state = json.loads(raw)
        decision = assess(state)
        decision['state_sha256'] = hashlib.sha256(raw).hexdigest()
        decision['stage_started'] = False
        if not decision['admitted']:
            # In particular, inspecting a historical denied run creates no new
            # session and does not rewrite its measurement or manifest.
            return decision
        transport = transport_factory(state)
        campaign.save(output / 'admission.json', decision)
        final_state = campaign.run_stage(output, transport)
        return {**assess(final_state), 'stage_started': True,
                'session': final_state['sessions'][-1]['directory']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('inspect', 'init', 'run'))
    parser.add_argument('--state', type=Path, required=True)
    parser.add_argument('--manifest', type=Path)
    parser.add_argument('--workspace', type=Path)
    parser.add_argument('--container')
    args = parser.parse_args()
    os.umask(0o077)
    output = args.state.resolve()
    if args.action == 'inspect':
        result = assess(campaign.read(output / 'state.json'))
    elif args.action == 'init':
        if not all((args.manifest, args.workspace, args.container)):
            parser.error('init requires --manifest, --workspace and --container')
        manifest = campaign.read(args.manifest)
        campaign.validate(manifest)
        if policy_for(manifest) is None:
            parser.error('init requires prospective admission policy in manifest')
        workspace = args.workspace.resolve()
        result = assess(campaign.initialize(manifest, workspace, output,
                                            campaign.Docker(args.container, workspace)))
    else:
        result = run(output, lambda state: campaign.Docker(
            state['container_id'], Path(state['workspace']), state['container_id']))
    print(json.dumps(result, indent=2, allow_nan=False))
    return 0 if args.action != 'run' or result['admitted'] or result['submitted_within_observed_budget'] else 2


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (campaign.CampaignError, OSError, ValueError, KeyError, TypeError,
            subprocess.SubprocessError) as error:
        print('admission: ' + str(error), file=sys.stderr)
        raise SystemExit(2)
