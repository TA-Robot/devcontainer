"""One isolated native solo invocation; no task, solution or test data in this file."""
import json
import os
from pathlib import Path
import selectors
import signal
import sqlite3
import subprocess
import time
import tomllib


def overrides(table, prefix=()):
    for key, value in table.items():
        path = prefix + (key,)
        if isinstance(value, dict):
            yield from overrides(value, path)
        else:
            yield '-c'
            yield '.'.join(json.dumps(k) for k in path) + '=' + json.dumps(value)


def argv(extra=()):
    config = tomllib.loads(Path('/control/config.toml').read_text())
    return ['/usr/local/bin/codex', 'exec', '--ignore-user-config', '--ignore-rules',
            '--json', '--skip-git-repo-check', *overrides(config), *extra, '-']


def observed_usage():
    records = {}
    for path in Path('/codex/sessions').rglob('*.jsonl'):
        for line in path.read_bytes().splitlines():
            try:
                row = json.loads(line)
                if row['type'] == 'token_usage_record':
                    p = row['payload']
                    records[(p['thread_id'], p['response_id'])] = p['usage']
            except (ValueError, KeyError):
                pass  # Partial live lines are checked strictly after stopping.
    return {k: sum(v.get(k, 0) for v in records.values())
            for k in ('input_tokens', 'cached_input_tokens', 'output_tokens')}


def run(extra=()):
    output = Path('/observation')
    (output/'invocation').mkdir()
    limits = json.loads(Path('/control/limits.json').read_text())
    process = None
    result = {'status': 'interrupted', 'reason': None}
    began = time.monotonic()
    last_check = 0
    total_bytes = 0

    def interrupted(signum, frame):
        raise InterruptedError('external interruption')

    for sig in (signal.SIGTERM, signal.SIGINT):
        signal.signal(sig, interrupted)
    try:
        with (output/'stdout.private.jsonl').open('xb') as out, (output/'stderr.private.txt').open('xb') as err:
            with Path('/control/prompt.txt').open('rb') as prompt:
                process = subprocess.Popen(argv(extra), stdin=prompt, stdout=subprocess.PIPE,
                                           stderr=subprocess.PIPE, start_new_session=True)
            with selectors.DefaultSelector() as selector:
                for stream in (process.stdout, process.stderr):
                    os.set_blocking(stream.fileno(), False)
                    selector.register(stream, selectors.EVENT_READ)
                while selector.get_map() or process.poll() is None:
                    elapsed = time.monotonic() - began
                    if elapsed > limits['development_seconds']:
                        raise TimeoutError('development deadline')
                    if elapsed - last_check > 1:
                        known = observed_usage()
                        (output/'progress.json').write_text(json.dumps({'seconds': elapsed, 'known_usage': known}))
                        last_check = elapsed
                        for key in ('input_tokens', 'output_tokens'):
                            if known[key] > limits[key]:
                                raise RuntimeError('observed ' + key + ' cap exceeded')
                    for key, _ in selector.select(.1):
                        data = os.read(key.fd, 65536)
                        if not data:
                            selector.unregister(key.fileobj)
                            continue
                        total_bytes += len(data)
                        if total_bytes > limits['output_bytes']:
                            raise RuntimeError('CLI observation byte cap exceeded')
                        target = out if key.fileobj is process.stdout else err
                        target.write(data)
                        target.flush()
            result['returncode'] = process.returncode
            result['status'] = 'completed' if process.returncode == 0 else 'failed'
    except (OSError, RuntimeError, subprocess.SubprocessError) as exc:
        result['reason'] = str(exc)
    finally:
        for sig in (signal.SIGTERM, signal.SIGINT):
            signal.signal(sig, signal.SIG_IGN)
        if process is not None:
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                result['reason'] = 'process group did not stop'
        result['development_seconds'] = time.monotonic() - began
        try:
            with sqlite3.connect('file:/codex/state_5.sqlite?mode=ro', uri=True) as db:
                rows = db.execute('SELECT id, model, reasoning_effort, cli_version FROM threads').fetchall()
            with sqlite3.connect(output/'inventory.sqlite') as db:
                db.execute('CREATE TABLE threads (id TEXT, model TEXT, reasoning_effort TEXT, cli_version TEXT)')
                db.executemany('INSERT INTO threads VALUES (?, ?, ?, ?)', rows)
        except sqlite3.Error as exc:
            result['inventory_failure'] = str(exc)
        (output/'bridge.json').write_text(json.dumps(result, indent=2)+'\n')
    return result


if __name__ == '__main__':
    run()
