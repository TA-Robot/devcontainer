"""Bounded JSONL policy process in a fixed credential/network-free Docker image."""
import os
from pathlib import Path
import selectors
import subprocess
import time
import uuid
import json

from runtime import Invalid, decode, require

IMAGE = 'sha256:df8eb7a18e1d462af44d23e9d9c0d32c2c960a49452c61fa17e0d215c821a9e0'


class CapacityError(RuntimeError):
    """Evaluator cannot deliver a legal observation; not candidate misconduct."""


class Policy:
    def __init__(self, snapshot, *, seconds=30):
        self.snapshot = Path(snapshot).resolve()
        self.seconds = seconds
        self.name = 'scheduling-policy-' + uuid.uuid4().hex
        self.process = None
        self.record = {'container': self.name, 'removed': False, 'request_seconds': 0.0,
                       'requests': 0, 'output_bytes': 0, 'image': IMAGE}
        self.pending = bytearray()

    def __enter__(self):
        self.started = time.monotonic()
        self.deadline = self.started + self.seconds
        args = ['docker', 'create', '-i', '--name', self.name, '--init', '--network', 'none', '--read-only',
                '--cap-drop', 'ALL', '--security-opt', 'no-new-privileges', '--pids-limit', '64',
                '--memory', '256m', '--cpus', '1', '--user', f'{os.getuid()}:{os.getgid()}',
                '--log-driver', 'none', '--tmpfs', '/tmp:rw,nosuid,nodev,size=16m,mode=1777',
                '--tmpfs', '/work:rw,nosuid,nodev,size=16m,mode=1777', '--workdir', '/work',
                '--mount', f'type=bind,src={self.snapshot},dst=/policy.py,readonly',
                '-e', 'PYTHONDONTWRITEBYTECODE=1', '-e', 'HOME=/nonexistent',
                IMAGE, 'python3', '-u', '/policy.py']
        try:
            subprocess.run(args, check=True, capture_output=True, timeout=min(15, self.seconds))
            self.process = subprocess.Popen(['docker', 'start', '-ai', self.name], stdin=subprocess.PIPE,
                                            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            for stream in (self.process.stdin, self.process.stdout, self.process.stderr):
                os.set_blocking(stream.fileno(), False)
            self.record['startup_seconds'] = time.monotonic() - self.started
            return self
        except BaseException:
            self.close()
            raise

    def choose(self, state):
        began = time.monotonic()
        seq = self.record['requests']
        data = memoryview((json.dumps({'request_id': seq, 'state': state}, allow_nan=False)+'\n').encode())
        if len(data) > 1048576:
            raise CapacityError('evaluator observation exceeds transport cap')
        require(not self.pending, 'unsolicited output')
        try:
            with selectors.DefaultSelector() as sel:
                sel.register(self.process.stdin, selectors.EVENT_WRITE)
                sel.register(self.process.stdout, selectors.EVENT_READ)
                sel.register(self.process.stderr, selectors.EVENT_READ)
                while True:
                    remaining = min(self.deadline, began + 5) - time.monotonic()
                    if remaining <= 0:
                        raise TimeoutError('policy deadline')
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
            self.record['request_seconds'] += time.monotonic() - began

    def close(self):
        began = time.monotonic()
        try:
            result = subprocess.run(['docker', 'rm', '-f', self.name], capture_output=True, timeout=15)
            self.record['removed'] = result.returncode == 0
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
