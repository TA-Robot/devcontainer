"""Bounded JSONL policy process in a fixed credential/network-free Docker image."""
import os
from pathlib import Path
import selectors
import subprocess
import time
import uuid
import json
import sys

from runtime import Invalid, decode, require
from recovery import drain

IMAGE = 'sha256:df8eb7a18e1d462af44d23e9d9c0d32c2c960a49452c61fa17e0d215c821a9e0'
HERE = Path(__file__).resolve().parent
READY = b'EVALUATOR_RUNTIME_READY_V1\n'


class CapacityError(RuntimeError):
    """Evaluator cannot deliver a legal observation; not candidate misconduct."""


class Policy:
    def __init__(self, snapshot, *, seconds=90, response_seconds=5, readiness_seconds=20):
        self.snapshot = Path(snapshot).resolve()
        self.seconds = seconds
        self.response_seconds = response_seconds
        self.readiness_seconds = readiness_seconds
        self.activated = False
        self.name = 'scheduling-policy-' + uuid.uuid4().hex
        self.process = None
        self.record = {'container': self.name, 'removed': False, 'request_seconds': 0.0,
                       'requests': 0, 'output_bytes': 0, 'image': IMAGE, 'scenario_budget_seconds': seconds,
                       'response_budget_seconds': response_seconds, 'max_request_seconds': 0.0,
                       'readiness_budget_seconds': readiness_seconds, 'runtime_ready': False}
        self.pending = bytearray()

    def await_ready(self):
        began = time.monotonic(); pending = bytearray()
        try:
            with selectors.DefaultSelector() as sel:
                sel.register(self.process.stderr, selectors.EVENT_READ)
                sel.register(self.process.stdout, selectors.EVENT_READ)
                while True:
                    remaining = min(self.deadline, began+self.readiness_seconds)-time.monotonic()
                    if remaining <= 0:
                        raise TimeoutError('scenario_deadline' if time.monotonic() >= self.deadline else 'runtime_readiness_deadline')
                    for key, _ in sel.select(min(remaining, .05)):
                        chunk = os.read(key.fd, 4096)
                        if not chunk: raise CapacityError('runtime exited before readiness')
                        if key.fileobj is self.process.stdout: raise CapacityError('output before activation')
                        pending.extend(chunk)
                        # The immutable launcher blocks on activation after
                        # this marker, so no candidate output is legal here.
                        if not READY.startswith(pending): raise CapacityError('runtime readiness protocol')
                        if pending == READY:
                            self.record['runtime_ready'] = True
                            return
        finally:
            self.record['readiness_wait_seconds'] = time.monotonic()-began

    def __enter__(self):
        self.started = time.monotonic()
        self.deadline = self.started + self.seconds
        args = ['docker', 'create', '-i', '--name', self.name, '--init', '--network', 'none', '--read-only',
                '--cap-drop', 'ALL', '--security-opt', 'no-new-privileges', '--pids-limit', '64',
                '--memory', '256m', '--cpus', '1', '--user', f'{os.getuid()}:{os.getgid()}',
                '--log-driver', 'none', '--tmpfs', '/tmp:rw,nosuid,nodev,size=16m,mode=1777',
                '--tmpfs', '/work:rw,nosuid,nodev,size=16m,mode=1777', '--workdir', '/work',
                '--mount', f'type=bind,src={self.snapshot},dst=/policy.py,readonly',
                '--mount', f'type=bind,src={HERE / "launcher.py"},dst=/launcher.py,readonly',
                '-e', 'PYTHONDONTWRITEBYTECODE=1', '-e', 'HOME=/nonexistent',
                IMAGE, 'python3', '-u', '/launcher.py', '/policy.py']
        try:
            subprocess.run(args, check=True, capture_output=True, timeout=min(15, self.seconds))
            self.process = subprocess.Popen(['docker', 'start', '-ai', self.name], stdin=subprocess.PIPE,
                                            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            for stream in (self.process.stdin, self.process.stdout, self.process.stderr):
                os.set_blocking(stream.fileno(), False)
            self.record['startup_seconds'] = time.monotonic() - self.started
            self.await_ready()
            return self
        except BaseException:
            self.close()
            raise

    def choose(self, state):
        began = time.monotonic()
        seq = self.record['requests']
        payload = (json.dumps({'request_id': seq, 'state': state}, allow_nan=False)+'\n').encode()
        if len(payload) > 1048576:
            raise CapacityError('evaluator observation exceeds transport cap')
        # The first response clock above begins BEFORE activation is sent.
        # Candidate imports/initialization therefore consume the same 5s cap.
        data = memoryview((b'\x01' if not self.activated else b'')+payload)
        self.activated = True
        require(not self.pending, 'unsolicited output')
        try:
            with selectors.DefaultSelector() as sel:
                sel.register(self.process.stdin, selectors.EVENT_WRITE)
                sel.register(self.process.stdout, selectors.EVENT_READ)
                sel.register(self.process.stderr, selectors.EVENT_READ)
                while True:
                    remaining = min(self.deadline, began + self.response_seconds) - time.monotonic()
                    if remaining <= 0:
                        raise TimeoutError('scenario_deadline' if time.monotonic() >= self.deadline else 'response_deadline')
                    for key, mask in sel.select(min(remaining, .05)):
                        if key.fileobj is self.process.stdin:
                            sent = os.write(key.fd, data)
                            data = data[sent:]
                            if not data:
                                sel.unregister(self.process.stdin)
                        else:
                            chunk = os.read(key.fd, 65536)
                            if not chunk:
                                sel.unregister(key.fileobj)
                                if key.fileobj is self.process.stdout:
                                    raise Invalid('policy exited without response')
                                continue
                            self.record['output_bytes'] += len(chunk)
                            require(self.record['output_bytes'] <= 262144, 'combined output cap')
                            if key.fileobj is self.process.stdout:
                                self.pending.extend(chunk)
                    if b'\n' in self.pending:
                        line, tail = self.pending.split(b'\n', 1)
                        require(not tail and not data, 'extra or premature response')
                        self.pending.clear()
                        value = decode(line)
                        require(isinstance(value, dict) and set(value) == {'request_id', 'assignments'}, 'response schema')
                        require(type(value['request_id']) is int and value['request_id'] == seq, 'request identity')
                        self.record['requests'] += 1
                        return value['assignments']
        finally:
            elapsed = time.monotonic() - began
            self.record['request_seconds'] += elapsed
            self.record['max_request_seconds'] = max(self.record['max_request_seconds'], elapsed)

    def close(self):
        began = time.monotonic()
        try:
            result = drain(self.name, create_completed='startup_seconds' in self.record, seconds=20)
            self.record['recovery_audit'] = result
            self.record['removed'] = result['status'] == 'confirmed'
        except (OSError, subprocess.SubprocessError):
            pass
        if self.process:
            try:
                self.process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                self.process.kill(); self.process.wait(timeout=3)
            for stream in (self.process.stdin, self.process.stdout, self.process.stderr):
                stream.close()
        self.record['cleanup_seconds'] = time.monotonic() - began
        self.record['elapsed_seconds'] = time.monotonic() - self.started

    def __exit__(self, *args):
        self.close()


class LocalPolicy(Policy):
    def __enter__(self):
        if not Path('/public/ACTOR_ONLY').is_file() or not Path('/.dockerenv').exists():
            raise CapacityError('dedicated actor environment required')
        self.started = time.monotonic(); self.deadline = self.started+self.seconds
        self.record.pop('image', None)
        self.record['execution_scope'] = 'local process; outer actor image recorded by controller'
        try:
            self.process = subprocess.Popen([sys.executable, '-u', str(HERE/'launcher.py'), str(self.snapshot)],
                stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, start_new_session=True,
                env={'PATH': '/usr/local/bin:/usr/bin:/bin', 'HOME': '/nonexistent', 'PYTHONDONTWRITEBYTECODE': '1'})
            for stream in (self.process.stdin, self.process.stdout, self.process.stderr): os.set_blocking(stream.fileno(), False)
            self.record['startup_seconds'] = time.monotonic()-self.started
            self.await_ready()
            return self
        except BaseException:
            self.close(); raise

    def close(self):
        began = time.monotonic()
        if self.process:
            try: os.killpg(self.process.pid, 9)
            except ProcessLookupError: pass
            self.process.wait(timeout=3)
            for stream in (self.process.stdin, self.process.stdout, self.process.stderr): stream.close()
        self.record.update(removed=True, cleanup_seconds=time.monotonic()-began,
                           elapsed_seconds=time.monotonic()-self.started)
