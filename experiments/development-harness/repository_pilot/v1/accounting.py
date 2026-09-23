"""Content-free accounting for the pinned 0.156.0 native rollout format.

Derived from native_actor_v1 without changing its historical contract.
Fail closed on incomplete/unknown observations. This is not a provider invoice.
Never sum cumulative token_count events or copied parent history.
"""
import json
from pathlib import Path
import sqlite3


FIELDS = ('input_tokens', 'cached_input_tokens', 'output_tokens',
          'cache_write_input_tokens', 'reasoning_output_tokens', 'total_tokens')


def usage(value):
    if not isinstance(value, dict) or any(type(value.get(k)) is not int or value[k] < 0 for k in FIELDS):
        raise ValueError('unknown usage')
    if (value['cached_input_tokens'] > value['input_tokens']
            or value['reasoning_output_tokens'] > value['output_tokens']
            or value['total_tokens'] != value['input_tokens'] + value['output_tokens']):
        raise ValueError('inconsistent usage')
    return {k: value[k] for k in FIELDS}


def collect(folder, database):
    """Only read a dedicated, stopped actor's session directory."""
    threads = {}
    failures = []
    for path in sorted(Path(folder).rglob('*.jsonl')):
        try:
            if path.is_symlink():
                raise ValueError('symlink rollout')
            rows = [json.loads(line) for line in path.read_text().splitlines()]
            if not rows or rows[0]['type'] != 'session_meta':
                raise ValueError('missing session identity')
            meta = rows[0]['payload']
            tid = meta['id']
            if tid in threads or meta['cli_version'] != '0.156.0':
                raise ValueError('duplicate thread or unvalidated CLI')
            thread = {'thread_id': tid, 'session_id': meta['session_id'],
                      'parent_thread_id': meta.get('parent_thread_id'),
                      'turns': {}, 'responses': [], 'usage': {k: 0 for k in FIELDS}}
            threads[tid] = thread
            # Full-history forks prepend another session's records. The native
            # thread_settings_applied event marks the return to this child.
            owned = True
            active = None
            unmatched = 0
            pending_model_output = False
            for row in rows[1:]:
                p = row['payload']
                if row['type'] == 'session_meta':
                    owned = p['id'] == tid
                    continue
                if (row['type'] == 'event_msg' and p.get('type') == 'thread_settings_applied'
                        and p.get('thread_id') == tid):
                    owned = True
                    continue
                if not owned:
                    continue
                if row['type'] == 'compacted':
                    rid = p.get('compaction_response_id')
                    if not rid or not any(r['response_id'] == rid for r in thread['responses']):
                        raise ValueError('compaction response without usage')
                if row['type'] == 'response_item' and (p.get('type') in ('function_call', 'custom_tool_call', 'reasoning')
                        or (p.get('type') == 'message' and p.get('role') == 'assistant')):
                    pending_model_output = True
                if row['type'] == 'token_usage_record':
                    if p['thread_id'] != tid or p['session_id'] != meta['session_id']:
                        raise ValueError('foreign usage')
                    if active != p['turn_id'] or not p.get('response_id'):
                        raise ValueError('usage outside active turn')
                    amount = usage(p['usage'])
                    if any(r['response_id'] == p['response_id'] for r in thread['responses']):
                        raise ValueError('duplicate response')
                    thread['responses'].append({'response_id': p['response_id'],
                                                'turn_id': active, 'usage': amount})
                    for k in FIELDS:
                        thread['usage'][k] += amount[k]
                    if usage(p['thread_token_usage']) != thread['usage']:
                        raise ValueError('response ledger differs from thread cumulative usage')
                    unmatched += 1
                    pending_model_output = False
                elif row['type'] == 'event_msg':
                    kind = p.get('type')
                    if kind == 'task_started':
                        if active is not None or p['turn_id'] in thread['turns']:
                            raise ValueError('overlapping or duplicate turn')
                        active = p['turn_id']
                        thread['turns'][active] = 'started'
                    elif kind == 'token_count':
                        # A missing usage response can repeat the previous total.
                        # Require a fresh per-response record, not a non-null total.
                        info = p.get('info')
                        # Compaction/rate observations can repeat cumulative
                        # counters without a provider response. A new assistant
                        # output still requires its own usage record.
                        if (unmatched == 0 and not pending_model_output and info
                                and usage(info['total_token_usage']) == thread['usage']):
                            continue
                        if unmatched != 1 or not info:
                            raise ValueError('unmatched or unknown token observation')
                        unmatched = 0
                    elif kind in ('task_complete', 'turn_aborted'):
                        turn = p.get('turn_id', active)
                        if active is None or turn != active or unmatched or pending_model_output:
                            raise ValueError('inconsistent terminal turn')
                        thread['turns'][active] = kind
                        if not any(r['turn_id'] == active for r in thread['responses']):
                            raise ValueError('turn without usage')
                        active = None
            if active is not None or unmatched or not thread['turns']:
                raise ValueError('unfinished observation')
            if any(v != 'task_complete' for v in thread['turns'].values()):
                raise ValueError('aborted turn')
        except (AttributeError, KeyError, TypeError, ValueError, OSError) as exc:
            failures.append({'file': path.name, 'failure': str(exc)[:160]})
    roots = [t for t in threads.values() if t['parent_thread_id'] is None]
    if len(roots) != 1:
        failures.append({'failure': 'expected one root'})
    else:
        root = roots[0]['thread_id']
        for tid, t in threads.items():
            seen = set()
            current = tid
            while current is not None and current in threads and current not in seen:
                seen.add(current)
                current = threads[current]['parent_thread_id']
            if current is not None or root not in seen or t['session_id'] != root:
                failures.append({'failure': 'disconnected thread graph'})
    inventory = []
    try:
        with sqlite3.connect(Path(database).resolve().as_uri() + '?mode=ro', uri=True) as connection:
            inventory = [{'thread_id': row[0], 'model': row[1], 'reasoning_effort': row[2],
                          'cli_version': row[3]} for row in connection.execute(
                              'SELECT id, model, reasoning_effort, cli_version FROM threads ORDER BY id')]
        if {t['thread_id'] for t in inventory} != set(threads):
            raise ValueError('thread inventory differs from rollouts')
        if any(t['cli_version'] != '0.156.0' or t['model'] != 'gpt-6-astra'
               or t['reasoning_effort'] != 'high' for t in inventory):
            raise ValueError('unvalidated participant configuration')
    except (OSError, ValueError, sqlite3.Error) as exc:
        failures.append({'failure': str(exc)[:160]})
    total = {k: sum(t['usage'][k] for t in threads.values()) for k in FIELDS}
    return {'status': 'withhold' if failures else 'completed', 'failures': failures,
            'threads': list(threads.values()), 'inventory': inventory, 'observed_usage': total,
            'usage': None if failures else total}
