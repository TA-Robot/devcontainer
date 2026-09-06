#!/usr/bin/env python3
"""Bounded event recorder, supervised by runner.py; never owns container stop."""
import json
import os
from pathlib import Path
import selectors
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import campaign


def record(spec, directory):
    result = {'exit_code': None, 'stop_reason': None, 'usage': [],
              'parse_errors': 0, 'commands_completed': 0, 'commands_nonzero': 0}
    selector = selectors.DefaultSelector()
    buffer = b''
    stderr = b''
    retained_bytes = 0
    with (directory / 'prompt.private.txt').open('rb') as source:
        process = subprocess.Popen(spec['argv'], stdin=source, stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE)
    campaign.save(directory / 'provider.json', {'pid': process.pid})

    def consume(line, events):
        nonlocal retained_bytes
        try:
            event = json.loads(line)
            if not isinstance(event, dict):
                raise ValueError('not an event')
            kind = event.get('type')
            item = event.get('item') or {}
            if not isinstance(item, dict):
                raise ValueError('invalid item')
            retained = None
            if kind == 'turn.completed':
                usage = event.get('usage')
                if not isinstance(usage, dict) or not all(
                        type(usage.get(k)) is int and usage[k] >= 0
                        for k in ('input_tokens', 'output_tokens')):
                    raise ValueError('invalid usage')
                result['usage'].append(usage)
                campaign.save(directory / 'progress.json', result)
                retained = {'type': kind, 'usage': usage}
            elif kind == 'item.completed' and item.get('type') == 'command_execution':
                result['commands_completed'] += 1
                result['commands_nonzero'] += item.get('exit_code') not in (0, None)
                retained = {'type': kind, 'item': {k: item.get(k) for k in
                            ('type', 'command', 'exit_code', 'status')}}
            elif kind == 'item.completed' and item.get('type') == 'agent_message':
                retained = {'type': kind, 'item': {'type': 'agent_message', 'text': item.get('text', '')}}
            if retained is not None:
                encoded = json.dumps(retained, ensure_ascii=False) + '\n'
                retained_bytes += len(encoded.encode())
                if retained_bytes > 64 * 1024 * 1024:
                    result['stop_reason'] = 'record_byte_cap'
                else:
                    events.write(encoded)
                    events.flush()
        except (ValueError, UnicodeError, TypeError):
            result['parse_errors'] += 1

    try:
        for stream in (process.stdout, process.stderr):
            os.set_blocking(stream.fileno(), False)
            selector.register(stream, selectors.EVENT_READ)
        with (directory / 'events.private.jsonl').open('w') as events:
            while True:
                for key, _ in selector.select(timeout=.05):
                    stream = key.fileobj
                    chunk = os.read(stream.fileno(), 65536)
                    if not chunk:
                        selector.unregister(stream)
                        if stream is process.stdout and buffer:
                            consume(buffer, events)
                            buffer = b''
                        continue
                    if stream is process.stderr:
                        stderr = (stderr + chunk)[-65536:]
                        continue
                    buffer += chunk
                    while b'\n' in buffer:
                        line, buffer = buffer.split(b'\n', 1)
                        consume(line, events)
                    if len(buffer) > 8 * 1024 * 1024:
                        result['stop_reason'] = 'event_line_cap'
                if sum(u['output_tokens'] for u in result['usage']) >= spec['output_cap']:
                    result['stop_reason'] = 'observed_output_cap'
                if result['stop_reason']:
                    break
                # Open inherited pipes cannot postpone the supervisor deadline.
                if process.poll() is not None and not selector.get_map():
                    result['exit_code'] = process.returncode
                    break
        (directory / 'stderr.private.txt').write_bytes(stderr)
        campaign.save(directory / 'record.json', result)
    finally:
        selector.close()
        process.stdout.close()
        process.stderr.close()
    return result


if __name__ == '__main__':
    os.umask(0o077)
    if sys.argv[1] == 'snapshot':
        campaign.snapshot(Path(sys.argv[2]), Path(sys.argv[3]), int(sys.argv[4]))
    else:
        folder = Path(sys.argv[1])
        record(campaign.read(folder / 'spec.json'), folder)
