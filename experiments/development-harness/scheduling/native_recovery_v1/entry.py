#!/usr/bin/env python3
"""Container-side lifecycle bridge around the pinned Codex executable.

Used unchanged by synthetic-provider and live executions. Only this process
receives provider network access; the native shell sandbox remains enabled.
"""
import json
import os
from pathlib import Path
import selectors
import shutil
import signal
import sqlite3
import subprocess
import sys
import time

class StopRequested(RuntimeError):
    pass


def main():
    output = Path('/observation')
    # A second root invocation must not overwrite the first one's accounting.
    (output / 'invocation').mkdir()
    limits = json.loads(Path('/policy/limits.json').read_text())
    began = time.monotonic()
    result = {'status': 'withhold', 'reason': None}
    process = None
    total = 0
    handlers = {}

    def stop(signum, frame):
        raise StopRequested('bridge interrupted')

    try:
        for sig in (signal.SIGTERM, signal.SIGINT):
            handlers[sig] = signal.signal(sig, stop)
        with (output / 'stdout.private.jsonl').open('xb') as stdout, (output / 'stderr.private.txt').open('xb') as stderr:
            arguments = [a for a in sys.argv[1:] if a != '--ephemeral']
            if not arguments or arguments[0] != 'exec':
                raise ValueError('one exec invocation required')
            process = subprocess.Popen(['/usr/local/bin/codex', *arguments],
                stdin=sys.stdin, stdout=subprocess.PIPE, stderr=subprocess.PIPE, start_new_session=True)
            with selectors.DefaultSelector() as selector:
                for stream in (process.stdout, process.stderr):
                    os.set_blocking(stream.fileno(), False)
                    selector.register(stream, selectors.EVENT_READ)
                while selector.get_map() or process.poll() is None:
                    if time.monotonic() - began > limits['development_seconds']:
                        raise TimeoutError('development deadline')
                    for key, _ in selector.select(.05):
                        chunk = os.read(key.fd, 65536)
                        if not chunk:
                            selector.unregister(key.fileobj)
                            continue
                        total += len(chunk)
                        if total > limits['output_bytes']:
                            raise ValueError('CLI output cap')
                        target = stdout if key.fileobj is process.stdout else stderr
                        target.write(chunk)
                        target.flush()
                        # Preserve exec's interface for the synthetic provider.
                        forward = sys.stdout.buffer if key.fileobj is process.stdout else sys.stderr.buffer
                        forward.write(chunk)
                        forward.flush()
            result['returncode'] = process.returncode
    except (StopRequested, OSError, ValueError, subprocess.SubprocessError) as exc:
        result['reason'] = type(exc).__name__ + ': ' + str(exc)
    finally:
        # Stop native runtime and tool children before taking observations.
        for sig in handlers:
            signal.signal(sig, signal.SIG_IGN)
        if process is not None:
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            try:
                process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                result['reason'] = 'CLI process did not stop'
        result['development_seconds'] = time.monotonic() - began
        try:
            sessions = Path('/codex/sessions')
            if sessions.exists():
                shutil.copytree(sessions, output / 'sessions.private')
            # Copy only accounting inventory columns; never copy auth.json or
            # the whole Codex home to the host observation directory.
            with sqlite3.connect('file:/codex/state_5.sqlite?mode=ro', uri=True) as source:
                rows = source.execute('SELECT id, model, reasoning_effort, cli_version FROM threads').fetchall()
            with sqlite3.connect(output / 'inventory.sqlite') as target:
                target.execute('CREATE TABLE threads (id TEXT, model TEXT, reasoning_effort TEXT, cli_version TEXT)')
                target.executemany('INSERT INTO threads VALUES (?, ?, ?, ?)', rows)
            result['observation_copy'] = 'completed'
        except (OSError, ValueError, sqlite3.Error) as exc:
            result['observation_copy'] = 'unknown'
            result['collection_failure'] = type(exc).__name__
        # Execution status is independent of ledger completeness. The host
        # removes the container and seals the source BEFORE inspecting usage.
        if result.get('returncode') == 0 and result['reason'] is None:
            result['status'] = 'completed'
        (output / 'bridge.json').write_text(json.dumps(result, indent=2) + '\n')
    return 0 if result['status'] == 'completed' else 1


if __name__ == '__main__':
    raise SystemExit(main())
