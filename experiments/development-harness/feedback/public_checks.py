#!/usr/bin/env python3
"""Trusted, phase-released public checks under the developer's named policy."""
import hashlib
import json
import os
from pathlib import Path
import re
import selectors
import shlex
import subprocess
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'terminal'))
import runner
Error = runner.Error
PROFILE = 'harness-public'
MOUNT = '/public-checks'
CONFIG_HOME = '/home/devuser/.local/state/harness-public-config'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def validate(contract, phases):
    if contract.get('schema_version') != 1:
        raise Error('unsupported public-check contract')
    for key in ('scope', 'rationale', 'owner', 'update_when'):
        if not isinstance(contract.get(key), str) or not contract[key].strip():
            raise Error('public checks require ' + key)
    if contract.get('limits_kind') != 'cost_cap':
        raise Error('public-check resource limits must be cost caps')
    for key in ('max_output_bytes', 'max_source_bytes', 'max_feedback_rounds', 'retry_min_output_tokens'):
        if type(contract.get(key)) is not int or contract[key] <= 0:
            raise Error(key + ' must be a positive integer')
    runner.campaign.positive(contract.get('retry_min_seconds'), 'retry_min_seconds')
    if type(contract.get('network_access')) is not bool:
        raise Error('public network policy must be explicit')
    checks = contract.get('checks')
    if not isinstance(checks, list) or not checks:
        raise Error('public check table required')
    ids, total = set(), 0
    for check in checks:
        ident = check.get('id', '')
        if not re.fullmatch(r'[a-z][a-z0-9_-]*', ident) or ident in ids:
            raise Error('invalid/duplicate public-check id')
        ids.add(ident)
        if type(check.get('phase')) is not int or not 1 <= check['phase'] <= phases:
            raise Error('invalid public-check release phase')
        if check.get('tier') not in ('capability', 'focused', 'required'):
            raise Error('unknown public-check tier')
        if check['tier'] == 'capability' and check['phase'] != 1:
            raise Error('capability checks must be available before development')
        if not isinstance(check.get('description'), str) or not check['description'].strip():
            raise Error('public-check instructions required')
        runner.campaign.positive(check.get('seconds'), 'public-check seconds')
        source = check.get('source')
        if not isinstance(source, str) or sha(source.encode()) != check.get('sha256'):
            raise Error('public-check source identity mismatch')
        total += len(source.encode())
        argv = check.get('argv')
        # Deliberately small contract: a fixed Python entrypoint and literal args.
        if (not isinstance(argv, list) or len(argv) < 2
                or argv[:2] != ['python3', f'{MOUNT}/{ident}.py']
                or any(not isinstance(x, str) or '\0' in x for x in argv)):
            raise Error('public command must name its own fixed entrypoint')
    if total > contract['max_source_bytes']:
        raise Error('public source byte cap exceeded')
    if not any(c['tier'] == 'capability' for c in checks):
        raise Error('pre-development capability witness required')
    selection = contract.get('phase_check_ids')
    if not isinstance(selection, dict) or set(selection) != {str(n) for n in range(1, phases + 1)}:
        raise Error('explicit check selection for every phase required')
    for number in range(1, phases + 1):
        chosen = selection[str(number)]
        eligible = {c['id'] for c in checks if c['phase'] <= number and c['tier'] != 'capability'}
        required = {c['id'] for c in checks if c['phase'] <= number and c['tier'] == 'required'}
        if (not isinstance(chosen, list) or not chosen or len(chosen) != len(set(chosen))
                or not set(chosen) <= eligible or not required <= set(chosen)):
            raise Error('selection misses required checks or includes unknown/unreleased checks')


def policy_args(contract):
    return ['-c', f'default_permissions="{PROFILE}"',
            '-c', f'permissions.{PROFILE}.extends=":workspace"',
            '-c', f'permissions.{PROFILE}.network.enabled={str(contract["network_access"]).lower()}',
            '-c', f'permissions.{PROFILE}.network.allow_local_binding=true',
            '-c', 'features.network_proxy=false']


def publish(contract, phase, release):
    """The read-only mount publishes only current/past task-owned source."""
    if release.is_symlink() or not release.is_dir():
        raise Error('release directory must already be a real, dedicated directory')
    expected = {c['id'] + '.py': c['source'] for c in contract['checks'] if c['phase'] <= phase}
    expected['checks.json'] = json.dumps({
        'checks': [{k: c[k] for k in ('id', 'phase', 'tier', 'description', 'argv', 'seconds', 'sha256')}
                   for c in contract['checks'] if c['phase'] <= phase],
        'selection': {str(n): contract['phase_check_ids'][str(n)] for n in range(1, phase + 1)}}, indent=2) + '\n'
    for path in release.iterdir():
        if path.name not in expected and path.name != 'campaign.lock':
            raise Error('unexpected content in the public release directory')
    for name, content in expected.items():
        path = release / name
        if path.is_symlink() or path.exists() and not path.is_file():
            raise Error('invalid public release path')
        if path.exists():
            if path.read_text() != content and name != 'checks.json':
                raise Error('published public-check source changed')
            path.chmod(0o600)
        path.write_text(content)
        path.chmod(0o444)
    return {name: sha(content.encode()) for name, content in expected.items()}


def instructions(contract, phase):
    rows = ['Public checks are available in /public-checks/checks.json. '
            'You may run any released check, repeat it, inspect its source, and repair freely within your budget. '
            'You choose when your candidate is ready to submit.']
    for c in contract['checks']:
        if c['phase'] <= phase:
            rows.append(f"{c['id']} [{c['tier']}; {c['seconds']} seconds]: {c['description']}\n"
                        + shlex.join(c['argv']))
    rows.append('Registered submission checks: ' + ', '.join(contract['phase_check_ids'][str(phase)]))
    return '\n\n'.join(rows)


class Docker(runner.Docker):
    def __init__(self, container, workspace, release, contract, expected_id=None):
        super().__init__(container, workspace, expected_id)
        self.contract = contract
        self.release = release.resolve()
        mounts = [m for m in self.info()['Mounts'] if m['Destination'] == MOUNT]
        if (len(mounts) != 1 or mounts[0]['Type'] != 'bind' or mounts[0]['RW']
                or Path(mounts[0]['Source']).resolve() != self.release):
            raise Error('public checks require the registered read-only bind mount')

    def environment(self):
        """Compare launch configuration, extra read-only inputs and initial layers."""
        info = self.info()
        settings = {k: v for k, v in info['Config'].items() if k not in ('Hostname', 'Labels')}
        host = {k: v for k, v in info['HostConfig'].items() if k not in ('Binds', 'Mounts')}
        mounts = []
        for mount in info['Mounts']:
            row = {k: mount[k] for k in ('Type', 'Destination', 'RW', 'Propagation')}
            if mount['Destination'] not in ('/workspace', MOUNT):
                if mount['Type'] != 'bind' or mount['RW']:
                    raise Error('extra inputs must be read-only bind mounts')
                source = Path(mount['Source'])
                row['sha256'] = runner.legacy.tree_hash(source) if source.is_dir() else sha(source.read_bytes())
            mounts.append(row)
        changes = runner.campaign.command(['docker', 'diff', self.identity]).strip()
        if changes:
            raise Error('seal requires fresh container layers; warm caches must be fixed read-only inputs')
        return {'config': settings, 'host': host, 'mounts': sorted(mounts, key=lambda r: r['Destination'])}

    def start(self):
        super().start()
        runner.campaign.command(['docker', 'exec', self.identity, 'mkdir', '-p', CONFIG_HOME])
        if hasattr(self, 'expected_cli_version'):
            value = runner.campaign.command(['docker', 'exec', self.identity, 'codex', '--version']).strip()
            if value != 'codex-cli ' + self.expected_cli_version:
                raise Error('verification/development CLI version differs from the sealed version')

    def argv(self, manifest, seconds):
        argv = super().argv(manifest, seconds)
        index = argv.index('--sandbox')
        del argv[index:index + 2]
        for index in reversed(range(len(argv) - 1)):
            if argv[index] == '-c' and argv[index + 1].startswith('sandbox_workspace_write.network_access='):
                del argv[index:index + 2]
        argv[3:3] = ['-e', 'DEVCONTAINER_CODEX_DANGEROUS_DEFAULT=0']
        argv[-1:-1] = policy_args(self.contract)
        return argv

    def check_argv(self, check):
        return ['docker', 'exec', '-e', f'CODEX_HOME={CONFIG_HOME}',
                '-e', 'DEVCONTAINER_CODEX_DANGEROUS_DEFAULT=0', '-e', 'PYTHONDONTWRITEBYTECODE=1',
                '-w', '/workspace', self.identity, 'codex', 'sandbox', '-P', PROFILE,
                '--include-managed-config', '-C', '/workspace', *policy_args(self.contract), '--', *check['argv']]


def bounded(argv, seconds, cap, cancelled):
    """Read both pipes with a shared byte cap; never wait on an unbounded log."""
    started = time.monotonic()
    process = subprocess.Popen(argv, stdout=subprocess.PIPE, stderr=subprocess.PIPE, start_new_session=True)
    output = bytearray()
    truncated = False
    selector = selectors.DefaultSelector()
    reason = None
    try:
        for stream in (process.stdout, process.stderr):
            os.set_blocking(stream.fileno(), False)
            selector.register(stream, selectors.EVENT_READ)
        while selector.get_map() or process.poll() is None:
            if cancelled or time.monotonic() - started >= seconds:
                reason = 'interrupted' if cancelled else 'timeout'
                break
            for key, _ in selector.select(timeout=min(.02, max(.001, seconds - (time.monotonic() - started)))):
                chunk = os.read(key.fileobj.fileno(), 65536)
                if not chunk:
                    selector.unregister(key.fileobj)
                    continue
                room = max(0, cap - len(output))
                output.extend(chunk[:room])
                truncated |= len(chunk) > room
        code = process.poll()
    finally:
        selector.close()
        runner.terminate(process)
        process.stdout.close()
        process.stderr.close()
    return {'exit_code': code, 'reason': reason, 'output': output.decode(errors='replace'),
            'output_truncated': truncated, 'command_seconds': time.monotonic() - started}


def source_identity(workspace):
    return {'tree': runner.legacy.tree_hash(workspace),
            'head': runner.campaign.command(['git', '-C', str(workspace), 'rev-parse', 'HEAD']).strip(),
            'index_diff': sha(runner.campaign.command(['git', '-C', str(workspace), 'diff', '--cached', '--binary']).encode())}


def run(contract, ids, transport, workspace, directory, deadline, cancelled):
    """Run only task-owned commands; no developer stdout selects what executes."""
    started = time.monotonic()
    directory.mkdir(mode=0o700)
    result = {'status': 'unknown', 'checks': [], 'stopped': False, 'source_unchanged': None,
              'elapsed_seconds': None, 'failure': None}
    before = None
    try:
        before = source_identity(workspace)
        transport.stopped()
        if cancelled or time.monotonic() >= deadline:
            result['failure'] = 'interrupted' if cancelled else 'budget_exhausted'
            return result
        transport.start()
        for ident in ids:
            check = next(c for c in contract['checks'] if c['id'] == ident)
            source = transport.release / (ident + '.py')
            if source.is_symlink() or sha(source.read_bytes()) != check['sha256']:
                raise Error('published public-check source changed')
            remaining = deadline - time.monotonic()
            if remaining <= 0 or cancelled:
                result['failure'] = 'budget_exhausted' if not cancelled else 'interrupted'
                break
            row = bounded(transport.check_argv(check), min(check['seconds'], remaining),
                          contract['max_output_bytes'], cancelled)
            row.update(id=ident, status='passed' if row['exit_code'] == 0 and row['reason'] is None else 'failed')
            result['checks'].append(row)
            runner.campaign.save(directory / 'progress.json', result)
            if row['reason']:
                # A timed-out command may have remote descendants: stop before any next check.
                result['failure'] = row['reason']
                break
    except (OSError, ValueError, subprocess.SubprocessError, Error) as error:
        result['failure'] = type(error).__name__
    finally:
        try:
            proof = transport.stop_bounded(transport.stop_seconds)
            result['stopped'] = proof.get('stopped') is True
            result['stop_evidence'] = proof
            if not result['stopped'] or proof.get('errors'):
                result['failure'] = 'stop_unconfirmed' if not result['stopped'] else 'stop_api_error'
        except (OSError, ValueError, subprocess.SubprocessError, Error):
            result['failure'] = 'stop_unconfirmed'
        if result['stopped'] and before is not None:
            try:
                result['source_unchanged'] = before == source_identity(workspace)
                if not result['source_unchanged']:
                    result['failure'] = result['failure'] or 'public_check_mutated_source'
            except (OSError, ValueError, subprocess.SubprocessError, Error):
                result['failure'] = 'public_check_source_unavailable'
        if result['failure'] is None and time.monotonic() > deadline:
            result['failure'] = 'budget_exhausted'
        if result['failure'] is None and len(result['checks']) == len(ids):
            result['status'] = 'passed' if all(c['status'] == 'passed' for c in result['checks']) else 'failed'
        result['elapsed_seconds'] = time.monotonic() - started
        runner.campaign.save(directory / 'result.json', result)
    return result
