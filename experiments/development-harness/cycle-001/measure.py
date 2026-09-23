#!/usr/bin/env python3
"""One bounded real-development observation, not an agent scheduler.

Raw reasoning is discarded. Private evidence contains only commands, final
messages, errors and aggregates; published reports use the aggregates.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--container', required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--task', type=Path, default=Path(__file__).with_name('task.md'))
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False, mode=0o700)
    task = args.task.read_bytes()
    argv = ['docker', 'exec', '-i', '-e', 'DEVCONTAINER_CODEX_CLI_VERSION=0.153.0',
            '-w', '/workspace', args.container,
            'codex', 'exec', '--json', '--ephemeral', '--ignore-user-config',
            '-m', 'gpt-6-astra', '-c', 'model_reasoning_effort="high"',
            '-c', 'approval_policy="never"', '-c', 'agents.enabled=false',
            '-c', 'features.multi_agent=false',
            '--sandbox', 'workspace-write', '-']
    started = time.time()
    began = time.monotonic()
    process = subprocess.Popen(argv, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE, start_new_session=True)
    (args.output / 'running.json').write_text(json.dumps({
        'pid': process.pid, 'container': args.container, 'started_unix': started,
        'deadline_seconds': 900, 'task_sha256': hashlib.sha256(task).hexdigest(),
    }, indent=2) + '\n')
    timed_out = False
    try:
        stdout, stderr = process.communicate(task, timeout=900)
    except subprocess.TimeoutExpired:
        timed_out = True
        # The dedicated container owns this one observation. Stop it so a lost
        # docker exec client cannot leave an unowned provider running.
        subprocess.run(['docker', 'stop', '--time', '5', args.container],
                       check=False, stdout=subprocess.DEVNULL, timeout=30)
        stdout, stderr = process.communicate(timeout=30)
    events = []
    counts: dict[str, int] = {}
    usage = []
    commands = []
    parse_errors = 0
    for line in stdout.splitlines():
        try:
            event = json.loads(line)
        except (ValueError, UnicodeError):
            parse_errors += 1
            continue
        kind = event.get('type', 'unknown')
        counts[kind] = counts.get(kind, 0) + 1
        if kind == 'turn.completed':
            usage.append(event.get('usage', {}))
        item = event.get('item', {})
        if kind == 'item.completed' and item.get('type') == 'command_execution':
            commands.append({key: item.get(key) for key in ('command', 'status', 'exit_code')})
        if kind in ('error', 'turn.failed'):
            events.append(event)
        if kind == 'item.completed' and item.get('type') == 'agent_message':
            events.append(event)
    report = {
        'schema_version': 1, 'container': args.container,
        'task_sha256': hashlib.sha256(task).hexdigest(),
        'requested_model': 'gpt-6-astra', 'requested_effort': 'high',
        'applied_model': None, 'applied_effort': None,
        'surface': 'codex-exec-json-ephemeral-workspace-write',
        'started_unix': started, 'wall_seconds': round(time.monotonic() - began, 3),
        'process_exit_code': process.returncode, 'timed_out': timed_out,
        'event_counts': counts, 'parse_errors': parse_errors, 'usage': usage,
        'commands_completed': len(commands),
        'commands_nonzero': sum(c['exit_code'] not in (0, None) for c in commands),
        'task_accepted': None,
    }
    for name, value in [('observation.json', report), ('commands.private.json', commands),
                        ('messages.private.json', events)]:
        path = args.output / name
        path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')
        path.chmod(0o600)
    # Provider stderr can contain configuration details. Keep it private and
    # bounded; never copy it into the published aggregate.
    (args.output / 'stderr.private.txt').write_bytes(stderr[-65536:])
    (args.output / 'stderr.private.txt').chmod(0o600)
    (args.output / 'running.json').unlink()
    print(json.dumps(report, indent=2))
    return 124 if timed_out else process.returncode


if __name__ == '__main__':
    raise SystemExit(main())
