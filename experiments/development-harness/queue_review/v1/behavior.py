"""Published queue behavior checks. External evaluation supplies an isolated command runner."""
import argparse
import json
import os
from pathlib import Path
import selectors
import signal
import stat
import subprocess
import tempfile
import time

CHECKS = ('restart-idempotence', 'argument-boundaries', 'invalid-state-preservation', 'atomic-replacement')
BYTE_CAP = 524288


def open_regular(path):
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    try:
        info = os.fstat(descriptor)
        if not stat.S_ISREG(info.st_mode) or info.st_size > BYTE_CAP:
            raise ValueError('invalid state file')
        return os.fdopen(descriptor, 'rb', buffering=0)
    except BaseException:
        os.close(descriptor)
        raise


def read_bytes(path):
    with open_regular(path) as stream:
        content = stream.read(BYTE_CAP + 1)
    if len(content) > BYTE_CAP:
        raise ValueError('state exceeds cap')
    return content


def capture(argv, seconds, **kwargs):
    process = subprocess.Popen(argv, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                               start_new_session=True, **kwargs)
    selector = selectors.DefaultSelector()
    output, total = bytearray(), 0
    deadline = time.monotonic() + seconds
    try:
        for stream in (process.stdout, process.stderr):
            os.set_blocking(stream.fileno(), False)
            selector.register(stream, selectors.EVENT_READ)
        while selector.get_map() or process.poll() is None:
            if time.monotonic() >= deadline:
                raise subprocess.TimeoutExpired(argv, seconds)
            for key, _ in selector.select(timeout=.02):
                chunk = os.read(key.fileobj.fileno(), 65536)
                if not chunk:
                    selector.unregister(key.fileobj)
                    continue
                total += len(chunk)
                if total > 65536:
                    raise ValueError('combined command output exceeds cap')
                if key.fileobj is process.stdout:
                    output.extend(chunk)
        return process.returncode, output.decode('utf-8')
    finally:
        selector.close()
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        process.wait(timeout=5)
        process.stdout.close()
        process.stderr.close()


def local_command(workspace, store, arguments):
    return capture([str(workspace / 'bin/queuectl'), '--store', str(store), *arguments], 5,
        cwd=store.parent, env={'PATH': os.environ.get('PATH', '/usr/bin:/bin'), 'HOME': '/nonexistent',
        'LANG': 'C.UTF-8', 'PYTHONDONTWRITEBYTECODE': '1'})


def observe(workspace, check, command=local_command):
    with tempfile.TemporaryDirectory(prefix='queue-review-state-') as raw:
        store = Path(raw) / 'queue file 日本語.json'
        events = []

        def require(value):
            if not value:
                raise ValueError('requirement failed')

        def call(*args, code=0, output=None):
            actual, text = command(workspace, store, list(args))
            events.append({'operation': args[0], 'returncode': actual})
            require(actual == code if code is not None else actual != 0)
            if output is not None:
                require(text == output)

        def state():
            return json.loads(read_bytes(store))

        try:
            if check == 'restart-idempotence':
                call('enqueue', 'z-item', 'second')
                call('enqueue', 'a-item', 'first')
                call('pending', output='a-item\nz-item\n')
                call('ack', 'a-item')
                before = read_bytes(store)
                call('ack', 'a-item')
                require(read_bytes(store) == before)
                item = state()['items']['a-item']
                require(item['acknowledged'] is True and type(item['ack_count']) is int and item['ack_count'] == 1)
                call('pending', output='z-item\n')
            elif check == 'argument-boundaries':
                payload = 'payload "quoted" 日本語\nsecond line'
                call('enqueue', 'item one', payload)
                require(state()['items']['item one']['payload'] == payload)
                call('pending', output='item one\n')
                call('ack', 'item one')
                call('pending', output='')
            elif check == 'invalid-state-preservation':
                call('enqueue', 'kept', 'value')
                before = read_bytes(store)
                call('ack', 'absent', code=4)
                require(read_bytes(store) == before)
                # The path was checked as regular; unlink before creating evaluator data.
                store.unlink()
                with store.open('xb') as stream:
                    stream.write(b'{broken-json\n')
                before = read_bytes(store)
                call('enqueue', 'new', 'value', code=None)
                require(read_bytes(store) == before)
            elif check == 'atomic-replacement':
                call('enqueue', 'kept', 'value')
                for arguments in (('enqueue', 'new', 'other'), ('ack', 'kept')):
                    before = read_bytes(store)
                    with open_regular(store) as reader:
                        call(*arguments)
                        retained = reader.read(BYTE_CAP + 1)
                    after = read_bytes(store)
                    require(retained == before and after != before)
                value = state()
                require(value['version'] == 1 and value['items']['kept']['acknowledged'] is True)
                require(value['items']['new']['payload'] == 'other')
            else:
                raise ValueError('unknown check')
        except subprocess.TimeoutExpired:
            return {'name': check, 'status': 'unknown', 'reason': 'command-timeout', 'events': events}
        except (OSError, ValueError, KeyError, TypeError):
            return {'name': check, 'status': 'fail', 'events': events}
    return {'name': check, 'status': 'pass', 'events': events}


def evaluate(workspace, command=local_command):
    checks = [observe(workspace, check, command) for check in CHECKS]
    status = 'unknown' if any(c['status'] == 'unknown' for c in checks) else (
        'pass' if all(c['status'] == 'pass' for c in checks) else 'fail')
    return {'status': status, 'checks': checks, 'scope': 'published-queue-behavior',
            'crash_durability_measured': False, 'concurrent_writers_measured': False}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--workspace', type=Path, default=Path.cwd())
    args = parser.parse_args()
    value = evaluate(args.workspace.resolve())
    print(json.dumps(value, ensure_ascii=False))
    raise SystemExit(0 if value['status'] == 'pass' else 1 if value['status'] == 'fail' else 2)
