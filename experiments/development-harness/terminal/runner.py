#!/usr/bin/env python3
"""Terminal-only clock v2: supervise a recorder, stop, capture, then release."""
from contextlib import contextmanager
import argparse
import fcntl
import json
import math
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / 'automatic'))
import compare as legacy
campaign = legacy.campaign
Error = campaign.CampaignError
CLOCK = 'terminal-v2'


class DeadlineReached(Error):
    pass


def fingerprint(manifest):
    return campaign.digest(json.dumps(manifest, sort_keys=True, ensure_ascii=False, allow_nan=False).encode())


def validate(manifest):
    if manifest.get('schema_version') != 2 or manifest.get('clock') != CLOCK:
        raise Error('terminal runner requires schema 2 / terminal-v2; old runs cannot be resumed')
    if 'checkpoint_seconds' in manifest:
        raise Error('periodic checkpoints are not supported by the terminal clock')
    # Reuse only the frozen structural validator; never store or run this view.
    structural = {**manifest, 'schema_version': 1, 'checkpoint_seconds': 1}
    campaign.validate(structural)
    for key in ('stop_seconds', 'capture_seconds', 'capture_window_seconds'):
        campaign.positive(manifest.get(key), key)
    if type(manifest['max_snapshot_bytes']) is not int:
        raise Error('snapshot byte cap must be an integer')
    if legacy.admission.policy_for(structural) is None:
        raise Error('explicit phase reservation policy required')


def load(output):
    state = campaign.read(output / 'state.json')
    validate(state['manifest'])
    if state.get('schema_version') != 2 or fingerprint(state['manifest']) != state['manifest_sha256']:
        raise Error('state/manifest identity changed')
    return state


@contextmanager
def locked(output):
    with (output / 'campaign.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        yield


def terminate(process):
    # The recorder and its CLI descendants share this owned process group.
    try:
        os.killpg(process.pid, signal.SIGKILL)
    except ProcessLookupError:
        pass
    process.wait(timeout=5)


def capture(workspace, destination, manifest):
    log = destination.parent / (destination.name + '-capture.private.log')
    with log.open('wb') as stream:
        process = subprocess.Popen([sys.executable, str(HERE / 'recorder.py'), 'snapshot',
                                    str(workspace), str(destination), str(manifest['max_snapshot_bytes'])],
                                   stdout=stream, stderr=subprocess.STDOUT, start_new_session=True)
        try:
            code = process.wait(timeout=manifest['capture_seconds'])
            if code:
                raise Error('archive incomplete; see private capture log')
        finally:
            if process.poll() is None:
                terminate(process)
    return campaign.read(destination / 'snapshot.json')


class Docker(campaign.Docker):
    def stopped(self):
        return legacy.stopped_state({'container_id': self.identity, 'image': self.image})

    def stop_bounded(self, seconds):
        errors = []
        deadline = time.monotonic() + seconds
        # No pause/unpause. A stop API error is not proof of a running or stopped writer.
        try:
            result = subprocess.run(['docker', 'stop', '--time', str(max(0, int(seconds / 2))), self.identity],
                                    capture_output=True, text=True, timeout=seconds * .75)
            if result.returncode:
                errors.append('stop_api_error')
        except (OSError, subprocess.SubprocessError):
            errors.append('stop_api_error')
        # Keep stop plus its independent proof within the same declared cap.
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise Error('stop proof deadline exhausted')
        result = subprocess.run(['docker', 'inspect', self.identity], capture_output=True,
                                text=True, timeout=remaining)
        if result.returncode:
            if 'no such object' not in result.stderr.lower() and 'no such container' not in result.stderr.lower():
                raise Error('stop state unavailable')
            proof = {'stopped': True, 'removed': True, 'container_id': self.identity}
        else:
            info = json.loads(result.stdout)[0]
            if (info['Id'] != self.identity or info['Image'] != self.image
                    or info['State']['Running'] or info['State'].get('Paused')):
                raise Error('writer stop not established')
            proof = {'stopped': True, 'removed': False, 'container_id': self.identity,
                     'finished_at': info['State'].get('FinishedAt')}
        return {**proof, 'errors': errors}

    def argv(self, manifest, seconds):
        # Provider policy is unchanged; only the observation/stop owner changes.
        return super().argv({**manifest, 'schema_version': 1, 'checkpoint_seconds': 1}, seconds)


def initialize(manifest, workspace, output, transport):
    started = time.monotonic()
    validate(manifest)
    workspace, output = workspace.resolve(), output.resolve()
    if workspace == output or workspace in output.parents or output in workspace.parents:
        raise Error('evidence and candidate paths must be disjoint')
    if campaign.command(['git', '-C', str(workspace), 'status', '--porcelain']).strip():
        raise Error('initial checkout must be clean')
    before = transport.stopped()
    output.mkdir(mode=0o700, parents=True, exist_ok=False)
    artifact = capture(workspace, output / 'initial', manifest)
    after = transport.stopped()
    state = {'schema_version': 2, 'manifest': manifest, 'manifest_sha256': fingerprint(manifest),
             'workspace': str(workspace), 'container_id': transport.identity, 'image': transport.image,
             'initial_snapshot': artifact, 'initial_stop_evidence': [before, after],
             'initialization_seconds': time.monotonic() - started,
             'status': 'ready', 'sessions': [], 'next_phase': 0}
    campaign.save(output / 'state.json', state)
    return state


def assess(state):
    validate(state['manifest'])
    if fingerprint(state['manifest']) != state['manifest_sha256']:
        raise Error('manifest identity changed')
    manifest = state['manifest']
    sessions = state['sessions']
    known_seconds = 0
    reserved_unknown = 0
    output_tokens = 0
    complete_usage = True
    submitted = 0
    for session in sessions:
        if session['phase'] != manifest['phases'][submitted]['id']:
            raise Error('session order differs from released phases')
        value = session['clock']['development_seconds']
        if value is None:
            reserved_unknown += session['reserved_seconds']
        else:
            if type(value) not in (int, float) or not math.isfinite(value) or value < 0:
                raise Error('invalid development duration')
            known_seconds += value
        complete_usage &= session['usage_complete'] is True
        for usage in session['observation']['usage']:
            if type(usage.get('output_tokens')) is not int or usage['output_tokens'] < 0:
                raise Error('invalid usage')
            output_tokens += usage['output_tokens']
        submitted += session['kind'] == 'submission'
    if state['next_phase'] != submitted:
        raise Error('phase counter differs from submissions')
    remaining = {'seconds': manifest['max_seconds'] - known_seconds - reserved_unknown,
                 'output_tokens': manifest['max_output_tokens'] - output_tokens,
                 'sessions': manifest['max_sessions'] - len(sessions)}
    reasons = []
    if not complete_usage:
        reasons.append('usage_unknown')
    if state['status'] != 'ready' or state.get('active'):
        reasons.append('state_not_ready')
    if any(s['infrastructure_failure'] or s['kind'] != 'submission' for s in sessions):
        reasons.append('prior_session_not_resumable')
    if submitted == len(manifest['phases']):
        reasons.append('all_phases_submitted')
    else:
        policy = manifest['admission']['stages']
        future = [policy[p['id']] for p in manifest['phases'][submitted:]]
        reserve = {'seconds': sum(x['minimum_seconds'] for x in future),
                   'output_tokens': sum(x['minimum_output_tokens'] for x in future), 'sessions': len(future)}
        if any(remaining[k] < reserve[k] for k in reserve):
            reasons.append('remaining_stage_minimums_unavailable')
    within = (state['status'] == 'submitted' and complete_usage and reserved_unknown == 0
              and all(v >= 0 for v in remaining.values())
              and all(s['clock']['development_seconds'] <= s['reserved_seconds'] for s in sessions))
    return {'admitted': not reasons, 'reasons': reasons, 'remaining': remaining,
            'known_development_seconds': known_seconds, 'reserved_unknown_seconds': reserved_unknown,
            'output_tokens': output_tokens, 'usage_complete': complete_usage,
            'submitted_within_budget': within}


def prompt_for(manifest, index):
    released = '\n\n'.join(f"Phase {p['id']}:\n{p['prompt']}" for p in manifest['phases'][:index + 1])
    return (released + '\n\nImplement the current phase in the existing checkout. Earlier requirements remain in force. '
            'Inspect existing source and DEVELOPMENT_HANDOFF.md, and leave a concise factual handoff there. '
            'Do not use other agents, contact people, publish externally, push, or change provider/model settings. '
            'Keep persistent development artifacts in the workspace.').encode()


def run_stage(output, transport):
    with locked(output):
        return _run_stage(output, transport)


@contextmanager
def cancellation():
    pending = []
    previous = {}
    try:
        for number in (signal.SIGINT, signal.SIGTERM):
            previous[number] = signal.signal(number, lambda signum, frame: pending.append(signum))
        yield pending
    finally:
        for number, handler in previous.items():
            signal.signal(number, handler)


def _run_stage(output, transport, *, deadline=None):
    """Caller holds the state lock, including during evaluation in a paired run."""
    with cancellation() as cancelled:
        state = load(output)
        decision = assess(state)
        if not decision['admitted']:
            raise Error('stage not admitted: ' + ', '.join(decision['reasons']))
        transport.stopped()
        manifest = state['manifest']
        index = state['next_phase']
        phase = manifest['phases'][index]
        seconds = min(phase['seconds'], decision['remaining']['seconds'])
        folder = output / f"session-{len(state['sessions']):02d}"
        folder.mkdir(mode=0o700)
        session = {'directory': folder.name, 'phase': phase['id'], 'reserved_seconds': seconds,
                   'kind': 'interrupted', 'usage_complete': False, 'artifact': None,
                   'observation': {'usage': [], 'exit_code': None, 'stop_reason': None, 'parse_errors': 0},
                   'clock': {'version': CLOCK, 'development_seconds': None, 'preparation_seconds': None,
                             'stop_requested_seconds': None, 'stop_confirmed_seconds': None,
                             'shutdown_seconds': None, 'capture_started_seconds': None,
                             'capture_completed_seconds': None, 'controller_seconds': None},
                   'stop_evidence': None, 'capture_window_ok': None, 'infrastructure_failure': None}
        state.update(status='running', active={'session': folder.name, 'phase': phase['id'],
                     'reserved_seconds': seconds, 'owner_pid': os.getpid(), 'started_unix': time.time()})
        campaign.save(output / 'state.json', state)
        overall = time.monotonic()
        started = None
        process = None
        try:
            transport.start()
            session['clock']['preparation_seconds'] = time.monotonic() - overall
            if cancelled:
                raise Error('controller interrupted during preparation')
            if deadline is not None:
                seconds = min(seconds, deadline - time.monotonic())
                if seconds <= 0:
                    raise DeadlineReached('enclosing development budget exhausted during preparation')
                session['reserved_seconds'] = seconds
                state['active']['reserved_seconds'] = seconds
            (folder / 'prompt.private.txt').write_bytes(prompt_for(manifest, index))
            (folder / 'prompt.private.txt').chmod(0o600)
            campaign.save(folder / 'spec.json', {'argv': transport.argv(manifest, seconds),
                          'output_cap': decision['remaining']['output_tokens']})
            started = time.monotonic()
            if deadline is not None and started >= deadline:
                raise DeadlineReached('enclosing development budget exhausted before recorder start')
            with (folder / 'recorder.private.log').open('wb') as log:
                process = subprocess.Popen([sys.executable, str(HERE / 'recorder.py'), str(folder)],
                                           stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
            state['active']['recorder_pid'] = process.pid
            campaign.save(output / 'state.json', state)
            stop_at = min(started + seconds, deadline) if deadline is not None else started + seconds
            while process.poll() is None and time.monotonic() < stop_at and not cancelled:
                time.sleep(min(.02, max(0, stop_at - time.monotonic())))
            elapsed = time.monotonic() - started
            session['clock']['development_seconds'] = elapsed
            evidence = folder / 'record.json'
            if not evidence.exists():
                evidence = folder / 'progress.json'
            if evidence.exists():
                session['observation'] = campaign.read(evidence)
            if cancelled:
                session['kind'] = 'interrupted'
                session['observation']['stop_reason'] = 'controller_signal'
                session['infrastructure_failure'] = 'controller_interrupted'
            elif time.monotonic() >= stop_at:
                session['kind'] = 'cutoff'
                session['observation']['stop_reason'] = 'wall_cap'
            elif process.returncode != 0 or not (folder / 'record.json').exists():
                session['infrastructure_failure'] = 'recorder_lost'
                session['clock']['development_seconds'] = None
            else:
                observed = session['observation']
                session['usage_complete'] = (bool(observed['usage']) and observed['parse_errors'] == 0
                                             and observed['exit_code'] == 0 and observed['stop_reason'] is None)
                session['kind'] = ('submission' if observed['exit_code'] == 0 and observed['stop_reason'] is None
                                   else 'cutoff' if observed['stop_reason'] else 'failed')
            # Persist the submission/cutoff observation before container shutdown.
            campaign.save(folder / 'terminal-event.json', session)
        except (OSError, ValueError, subprocess.SubprocessError, Error) as error:
            session['infrastructure_failure'] = ('controller_interrupted' if cancelled else
                                                 'startup_failed' if started is None else 'recorder_failed')
            if started is None:
                session['clock']['preparation_seconds'] = time.monotonic() - overall
            session['error_type'] = type(error).__name__
            if isinstance(error, DeadlineReached):
                session.update(kind='cutoff', infrastructure_failure=None)
                session['clock']['development_seconds'] = 0.0
                session['observation']['stop_reason'] = 'enclosing_budget_exhausted'
        finally:
            origin = started if started is not None else overall
            session['clock']['stop_requested_seconds'] = time.monotonic() - origin
            try:
                campaign.save(folder / 'stop-request.json', session)
            except OSError:
                # Evidence disk failure must not skip the independently owned stop.
                session['infrastructure_failure'] = 'recorder_failed'
            try:
                session['stop_evidence'] = transport.stop_bounded(manifest['stop_seconds'])
                session['clock']['stop_confirmed_seconds'] = time.monotonic() - origin
                if session['stop_evidence'].get('stopped') is not True:
                    raise Error('stop was not confirmed')
                if session['stop_evidence'].get('errors'):
                    session['infrastructure_failure'] = 'stop_api_error'
                session['clock']['shutdown_seconds'] = (session['clock']['stop_confirmed_seconds']
                                                        - session['clock']['stop_requested_seconds'])
            except (OSError, ValueError, subprocess.SubprocessError, Error):
                session['stop_evidence'] = {'stopped': False}
                session['clock']['stop_confirmed_seconds'] = None
                session['infrastructure_failure'] = 'stop_unconfirmed'
            finally:
                if process is not None:
                    try:
                        terminate(process)
                    except (OSError, subprocess.SubprocessError):
                        session['infrastructure_failure'] = 'recorder_cleanup_failed'
            if session['stop_evidence']['stopped']:
                try:
                    session['clock']['capture_started_seconds'] = time.monotonic() - origin
                    session['artifact'] = capture(Path(state['workspace']), folder / 'terminal', manifest)
                    session['capture_stop_evidence'] = transport.stopped()
                    session['clock']['capture_completed_seconds'] = time.monotonic() - origin
                    session['capture_window_ok'] = (session['clock']['development_seconds'] is not None
                        and session['clock']['stop_confirmed_seconds'] - session['clock']['development_seconds']
                        <= manifest['capture_window_seconds'])
                except (OSError, ValueError, subprocess.SubprocessError, Error):
                    session['artifact'] = None
                    session['infrastructure_failure'] = 'archive_failed'
            session['clock']['controller_seconds'] = time.monotonic() - overall
            if cancelled and session['infrastructure_failure'] is None:
                session['infrastructure_failure'] = 'controller_interrupted'
            campaign.save(folder / 'observation.json', session)
            state['sessions'].append(session)
            state['next_phase'] += session['kind'] == 'submission'
            if session['infrastructure_failure']:
                state['status'] = 'interrupted'
            elif session['kind'] != 'submission' or not session['usage_complete']:
                state['status'] = 'halted'
            else:
                state['status'] = 'submitted' if state['next_phase'] == len(manifest['phases']) else 'ready'
            state.pop('active', None)
            campaign.save(output / 'state.json', state)
        return state


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('init', 'run', 'status'))
    parser.add_argument('--state', type=Path, required=True)
    parser.add_argument('--manifest', type=Path)
    parser.add_argument('--workspace', type=Path)
    parser.add_argument('--container')
    args = parser.parse_args()
    os.umask(0o077)
    output = args.state.resolve()
    if args.action == 'init':
        if not all((args.manifest, args.workspace, args.container)):
            parser.error('init requires manifest, workspace, container')
        workspace = args.workspace.resolve()
        state = initialize(campaign.read(args.manifest), workspace, output, Docker(args.container, workspace))
    else:
        state = load(output)
        if args.action == 'run':
            state = run_stage(output, Docker(state['container_id'], Path(state['workspace']), state['container_id']))
    print(json.dumps({'status': state['status'], 'admission': assess(state)}, indent=2))


if __name__ == '__main__':
    main()
