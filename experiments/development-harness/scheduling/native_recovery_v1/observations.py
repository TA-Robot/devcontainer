"""Content-free terminal inventory and known response records, independent axes.

The original strict collector decides record completeness. This reader retains
later valid records after a missing response and checks lifecycle independently.
Neither collector certifies a provider invoice or unreported consumption.
"""
import hashlib
import importlib.util
import json
from pathlib import Path
import sqlite3

LEGACY = Path(__file__).resolve().parent.parent/'native_actor_v1/accounting.py'


def inspect(folder, database, condition):
    spec = importlib.util.spec_from_file_location('recovery_strict_accounting', LEGACY)
    strict = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(strict)
    lifecycle_errors, record_errors, threads, sources = [], [], {}, {}
    responses = {}
    for path in sorted(Path(folder).rglob('*.jsonl')):
        try:
            if path.is_symlink():
                raise ValueError('symlink rollout')
            data = path.read_bytes()
            sources[str(path.relative_to(folder))] = hashlib.sha256(data).hexdigest()
            rows = [json.loads(line) for line in data.splitlines()]
            if not rows or rows[0]['type'] != 'session_meta':
                raise ValueError('missing session identity')
            meta = rows[0]['payload']
            tid, sid = meta['id'], meta['session_id']
            if tid in threads or meta['cli_version'] != '0.153.0':
                raise ValueError('duplicate thread or unsupported CLI')
            thread = {'thread_id': tid, 'session_id': sid, 'parent_thread_id': meta.get('parent_thread_id'), 'turns': {}}
            threads[tid] = thread
            active, owned = None, True
            for row in rows[1:]:
                kind, payload = row['type'], row['payload']
                if kind == 'session_meta':
                    owned = payload['id'] == tid
                    continue
                if (kind == 'event_msg' and payload.get('type') == 'thread_settings_applied'
                        and payload.get('thread_id') == tid):
                    owned = True
                    continue
                if not owned:
                    continue
                if kind == 'token_usage_record':
                    try:
                        if payload['thread_id'] != tid or payload['session_id'] != sid:
                            raise ValueError('foreign usage')
                        rid = payload['response_id']
                        if not isinstance(rid, str) or not rid or active != payload['turn_id']:
                            raise ValueError('usage outside active turn')
                        key = (tid, rid)
                        if key in responses:
                            raise ValueError('duplicate response')
                        responses[key] = strict.usage(payload['usage'])
                    except (KeyError, TypeError, ValueError) as exc:
                        record_errors.append({'thread_id': tid, 'failure': str(exc)[:160]})
                elif kind == 'event_msg':
                    event = payload.get('type')
                    if event == 'task_started':
                        turn = payload['turn_id']
                        if active is not None or turn in thread['turns']:
                            raise ValueError('overlapping or duplicate turn')
                        active = turn
                        thread['turns'][turn] = 'started'
                    elif event in ('task_complete', 'turn_aborted'):
                        turn = payload.get('turn_id', active)
                        if active is None or turn != active:
                            raise ValueError('terminal without matching active turn')
                        thread['turns'][turn] = event
                        active = None
            if active is not None or not thread['turns']:
                lifecycle_errors.append({'thread_id': tid, 'failure': 'unfinished participant'})
            if any(state != 'task_complete' for state in thread['turns'].values()):
                lifecycle_errors.append({'thread_id': tid, 'failure': 'incomplete or aborted turn'})
        except (OSError, KeyError, TypeError, ValueError) as exc:
            lifecycle_errors.append({'file': path.name, 'failure': str(exc)[:160]})
    roots = [t['thread_id'] for t in threads.values() if t['parent_thread_id'] is None]
    if len(roots) != 1:
        lifecycle_errors.append({'failure': 'expected one root'})
    else:
        for tid, thread in threads.items():
            seen, current = set(), tid
            while current in threads and current not in seen:
                seen.add(current)
                current = threads[current]['parent_thread_id']
            if current is not None or roots[0] not in seen or thread['session_id'] != roots[0]:
                lifecycle_errors.append({'failure': 'disconnected thread graph'})
    inventory = []
    try:
        with sqlite3.connect(Path(database).resolve().as_uri()+'?mode=ro', uri=True) as connection:
            inventory = [{'thread_id': r[0], 'model': r[1], 'effort': r[2], 'cli_version': r[3]}
                         for r in connection.execute('SELECT id, model, reasoning_effort, cli_version FROM threads')]
        if len(inventory) != len(threads) or {r['thread_id'] for r in inventory} != set(threads):
            raise ValueError('inventory mismatch')
        if any(r['model'] != 'gpt-6-astra' or r['effort'] != 'high' or r['cli_version'] != '0.153.0' for r in inventory):
            raise ValueError('participant configuration mismatch')
        if condition == 'solo' and len(threads) != 1:
            raise ValueError('unexpected solo participant')
    except (OSError, ValueError, sqlite3.Error) as exc:
        lifecycle_errors.append({'failure': str(exc)[:160]})
    formal = strict.collect(folder, database)
    known = ({k: sum(amount[k] for amount in responses.values()) for k in strict.FIELDS}
             if responses else None)
    complete = (formal['status'] == 'completed' and not lifecycle_errors and not record_errors
                and formal['usage'] == known)
    return {'lifecycle': {'status': 'unknown' if lifecycle_errors else 'completed',
                         'failures': lifecycle_errors, 'threads': list(threads.values()), 'inventory': inventory},
            'usage': {'status': 'complete' if complete else 'partial' if known is not None else 'unknown',
                      'known_usage': known, 'known_response_records': len(responses),
                      'billing_completeness': 'unknown',
                      'scope': 'validated response records; unreported consumption excluded',
                      'record_errors': record_errors, 'strict_failures': formal['failures']},
            'source_sha256': sources}
