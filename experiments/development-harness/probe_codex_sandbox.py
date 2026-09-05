#!/usr/bin/env python3
"""Observe local verification capabilities without a model or real credentials.

Run in a disposable container with --network none and no credential mounts.
Creates private temporary config only; never changes installed/user policy.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import signal
import socket
import subprocess
import tempfile
import threading


CHILD = r'''
import json, os, pathlib, socket
result = {}
for name, family in [('unix_listener', socket.AF_UNIX), ('loopback_listener', socket.AF_INET)]:
    try:
        with socket.socket(family, socket.SOCK_STREAM) as stream:
            address = str(pathlib.Path.cwd() / 'probe.sock') if family == socket.AF_UNIX else ('127.0.0.1', 0)
            stream.bind(address)
            stream.listen(1)
        result[name] = {'allowed': True}
    except OSError as error:
        result[name] = {'allowed': False, 'errno': error.errno}
path = pathlib.Path.cwd() / 'probe.sock'
if path.exists():
    path.unlink()
try:
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as stream:
        stream.settimeout(2)
        stream.connect(os.environ['HARNESS_PROBE_SOCKET'])
        result['existing_unix_connection'] = {'allowed': stream.recv(1) == b'x'}
except OSError as error:
    result['existing_unix_connection'] = {'allowed': False, 'errno': error.errno}
try:
    pathlib.Path(os.environ['HARNESS_PROBE_OUTSIDE'], 'owned-write-check').write_text('probe')
    result['outside_workspace_write'] = {'allowed': True}
except OSError as error:
    result['outside_workspace_write'] = {'allowed': False, 'errno': error.errno}
print(json.dumps(result))
'''


def capture(argv, *, cwd, env, timeout=30):
    with subprocess.Popen(argv, cwd=cwd, env=env, text=True, stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE, start_new_session=True) as process:
        try:
            stdout, stderr = process.communicate(timeout=timeout)
            return {'exit_code': process.returncode, 'timed_out': False,
                    'stdout': stdout, 'stderr': stderr[-2000:]}
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGKILL)
            stdout, stderr = process.communicate()
            return {'exit_code': process.returncode, 'timed_out': True,
                    'stdout': stdout, 'stderr': stderr[-2000:]}


def probe(codex):
    # Outside system temp, otherwise :workspace legitimately grants writes here.
    with tempfile.TemporaryDirectory(prefix='harness-probe-', dir=Path.home()) as raw:
        root = Path(raw)
        home, workspace, outside = (root / name for name in ('config', 'workspace', 'outside'))
        for directory in (home, workspace, outside):
            directory.mkdir(mode=0o700)
        endpoint = outside / 'listener.sock'
        env = {**os.environ, 'CODEX_HOME': str(home), 'PYTHONDONTWRITEBYTECODE': '1',
               'HARNESS_PROBE_SOCKET': str(endpoint), 'HARNESS_PROBE_OUTSIDE': str(outside)}
        # No model command is invoked. Callers must also keep real auth mounts out.
        server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        server.bind(str(endpoint))
        server.listen()
        server.settimeout(0.1)
        stop = threading.Event()
        def serve():
            while not stop.is_set():
                try:
                    connection, _ = server.accept()
                except socket.timeout:
                    continue
                with connection:
                    try:
                        connection.sendall(b'x')
                    except OSError:
                        pass
        thread = threading.Thread(target=serve)
        thread.start()
        observations = []
        try:
            for name, network, proxy in (
                    ('direct', False, False), ('workspace', False, False),
                    ('workspace-network', True, False), ('workspace-proxy-local', True, True)):
                config = ('default_permissions = "probe"\n'
                          f'[features]\nnetwork_proxy = {str(proxy).lower()}\n'
                          '[permissions.probe]\nextends = ":workspace"\n'
                          f'[permissions.probe.network]\nenabled = {str(network).lower()}\n'
                          'allow_local_binding = true\n'
                          '[permissions.probe.network.unix_sockets]\n'
                          f'{json.dumps(str(endpoint))} = "allow"\n')
                (home / 'config.toml').write_text(config)
                prefix = [] if name == 'direct' else [codex, 'sandbox', '-P', 'probe', '-C', str(workspace), '--']
                result = capture(prefix + ['python3', '-c', CHILD], cwd=workspace, env=env)
                try:
                    capabilities = json.loads(result['stdout']) if result['exit_code'] == 0 else None
                except json.JSONDecodeError:
                    capabilities = None
                observations.append({'case': name, 'exit_code': result['exit_code'],
                                     'timed_out': result['timed_out'], 'capabilities': capabilities,
                                     'diagnostic': result['stderr']})
            version = capture([codex, '--version'], cwd=workspace, env=env)
        finally:
            stop.set()
            thread.join(timeout=2)
            server.close()
        return {'schema_version': 1, 'cli_version': version['stdout'].strip(),
                'probe_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                'model_invocations': 0, 'user_configuration_changed': False,
                'measurement_complete': version['exit_code'] == 0 and all(x['capabilities'] is not None for x in observations),
                'scope': 'local sockets and filesystem only; no outbound connectivity or legacy exec-policy equivalence claim',
                'observations': observations}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--codex', default='codex')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = probe(args.codex)
    args.output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))
    return 0 if result['measurement_complete'] else 2


if __name__ == '__main__':
    raise SystemExit(main())
