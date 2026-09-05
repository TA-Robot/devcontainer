#!/usr/bin/env python3
"""Observe the declared crash-recovery procedure without revising frozen scores."""
import argparse
import contextlib
import json
import os
from pathlib import Path
import signal
import sys
import tempfile

ORACLE = Path(__file__).resolve().parents[1] / 'cycle-003/large-02'
sys.path.insert(0, str(ORACLE))
from evaluate_staged import concurrency, gated, wait_for
from staged_fixture import StagedFixture


def group_running(group):
    """A missing process is stopped; unreadable ownership is not proof of stop."""
    if type(group) is not int or group <= 1:
        raise ValueError('unsafe process group identity')
    for node in Path('/proc').iterdir():
        if not node.name.isdecimal():
            continue
        try:
            fields = (node / 'stat').read_text().rsplit(') ', 1)[1].split()
        except (FileNotFoundError, ProcessLookupError):
            continue
        if int(fields[2]) == group and fields[0] != 'Z':
            return True
    return False


def observe(fixture, procedure):
    """Only the declared recovery call differs; overlap and strict gates remain."""
    if procedure not in ('automatic', 'explicit'):
        raise ValueError('unknown recovery procedure')
    original_check, original_stop = fixture.check, fixture.stop_worker
    confirmed = False
    recovery_calls = 0

    def stop_and_confirm():
        nonlocal confirmed
        group = None
        if fixture.worker_alive():
            identity = json.loads((fixture.root / 'worker-identity.json').read_text())
            group = os.getpgid(identity['pid'])
        original_stop()
        if group is not None:
            wait_for(lambda: not group_running(group), seconds=2)
        wait_for(lambda: not fixture.worker_alive(), seconds=2)
        confirmed = True

    def check(seconds=5):
        nonlocal recovery_calls
        if procedure == 'automatic' or not confirmed:
            return original_check(seconds)
        recovery_calls += 1
        process = fixture.start('job', 'check', fixture.job['job_id'], '--timeout', str(seconds),
                                '--recover-incomplete', '--json')
        return fixture.wait(process, seconds=20)

    fixture.check, fixture.stop_worker = check, stop_and_confirm
    try:
        if procedure == 'explicit':
            help_result = fixture.invoke('job', 'check', '--help')
            assert '--recover-incomplete' in help_result.stdout, 'declared recovery option absent'
        concurrency(fixture, signal.SIGKILL)
        gated(fixture, True)
        assert confirmed, 'old execution stop was not confirmed'
        assert fixture.counter.read_text() == '1', 'recovery launched another provider'
        result = {'status': 'passed', 'provider_invocations': 1}
    except Exception as error:
        result = {'status': 'failed' if isinstance(error, AssertionError) else 'unknown',
                  'detail': type(error).__name__ + ': ' + str(error)[:700]}
    finally:
        fixture.check, fixture.stop_worker = original_check, original_stop
    result.update(procedure=procedure, operator_confirmed_owned_process_group_stopped=confirmed,
                  explicit_recovery_calls=recovery_calls,
                  scope='supplemental declared procedure; frozen observations unchanged')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--candidate', type=Path)
    parser.add_argument('--template', type=Path)
    parser.add_argument('--installed', action='store_true')
    parser.add_argument('--procedure', required=True, choices=('automatic', 'explicit'))
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    if args.installed and (args.candidate or args.template):
        parser.error('installed mode cannot use candidate/template source')
    if not args.installed and not (args.candidate and args.template):
        parser.error('source mode requires candidate and template')
    with contextlib.ExitStack() as stack:
        if args.installed:
            candidate = Path(stack.enter_context(tempfile.TemporaryDirectory(prefix='installed-recovery-')))
            (candidate / 'scripts').symlink_to('/usr/local/bin', target_is_directory=True)
            template = Path('/usr/local/share/agent-project/template')
        else:
            candidate, template = args.candidate.resolve(), args.template.resolve()
        fixture = StagedFixture(candidate, template)
        stack.callback(fixture.close)
        result = observe(fixture, args.procedure)
    result['installed'] = args.installed
    # Mount context is an outside-observer fact, not inferred from this flag.
    result['candidate_checkout_mounted'] = None
    args.output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))
    return 0 if result['status'] == 'passed' else 1


if __name__ == '__main__':
    raise SystemExit(main())
