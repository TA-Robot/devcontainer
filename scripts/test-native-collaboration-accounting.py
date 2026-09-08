import copy
import importlib.util
import json
import os
from pathlib import Path
import sqlite3
import tempfile
import unittest


HERE = Path(__file__).resolve().parents[1] / 'experiments/development-harness/scheduling/native_probe_v1'


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


accounting = module('native_accounting', HERE / 'accounting.py')
runner = module('native_probe_runner', HERE / 'run.py')


def row(kind, **payload):
    return {'type': kind, 'payload': payload}


def event(kind, **payload):
    return row('event_msg', type=kind, **payload)


AMOUNT = dict(input_tokens=20, cached_input_tokens=7, output_tokens=5,
              cache_write_input_tokens=0, reasoning_output_tokens=0, total_tokens=25)


def records(tid, parent=None):
    turn = tid + '-turn'
    return [row('session_meta', id=tid, session_id='root', parent_thread_id=parent, cli_version='0.153.0'),
            event('task_started', turn_id=turn),
            row('response_item', type='message', text='PRIVATE_CONTENT_MUST_NOT_ESCAPE'),
            row('token_usage_record', thread_id=tid, session_id='root', turn_id=turn,
                response_id=tid + '-response', usage=AMOUNT.copy(), thread_token_usage=AMOUNT.copy()),
            event('token_count', info={'total_token_usage': AMOUNT.copy()}),
            event('task_complete', turn_id=turn)]


class AccountingTests(unittest.TestCase):
    def assess(self, root=None, child=None, extra_inventory=False):
        with tempfile.TemporaryDirectory() as d:
            base = Path(d)
            sessions = base / 'sessions'
            sessions.mkdir()
            data = {'root': records('root') if root is None else root}
            if child is not None:
                data['child'] = child
            for tid, rows in data.items():
                (sessions / (tid + '.jsonl')).write_text('\n'.join(json.dumps(r) for r in rows) + '\n')
            db = base / 'state.sqlite'
            with sqlite3.connect(db) as c:
                c.execute('CREATE TABLE threads (id TEXT, model TEXT, reasoning_effort TEXT, cli_version TEXT)')
                for tid in list(data) + (['missing'] if extra_inventory else []):
                    c.execute('INSERT INTO threads VALUES (?, ?, ?, ?)', (tid, 'gpt-6-astra', 'high', '0.153.0'))
            return accounting.collect(sessions, db)

    def test_sum_actual_responses_and_no_content(self):
        result = self.assess(child=records('child', 'root'))
        self.assertEqual(result['status'], 'completed')
        self.assertEqual(result['usage'], {k: 2 * v for k, v in AMOUNT.items()})
        self.assertNotIn('PRIVATE_CONTENT', json.dumps(result))

    def test_fork_history_not_counted(self):
        child = records('child', 'root')
        child[1:1] = records('root') + [event('thread_settings_applied', thread_id='child')]
        result = self.assess(child=child)
        self.assertEqual(result['status'], 'completed', result)
        self.assertEqual(result['usage']['input_tokens'], 40)

    def test_missing_later_usage_is_not_previous_total_or_zero(self):
        rows = records('root')
        rows.insert(-1, event('token_count', info={'total_token_usage': AMOUNT.copy()}))
        result = self.assess(root=rows)
        self.assertEqual(result['status'], 'withhold')
        self.assertIsNone(result['usage'])
        self.assertEqual(result['observed_usage']['input_tokens'], 20)

    def test_missing_rollout_in_inventory(self):
        self.assertEqual(self.assess(extra_inventory=True)['status'], 'withhold')

    def test_unfinished_and_aborted_turn(self):
        for rows in [records('root')[:-1], records('root')[:-1] + [event('turn_aborted', turn_id='root-turn')]]:
            with self.subTest(rows=rows[-1]['payload'].get('type')):
                self.assertEqual(self.assess(root=rows)['status'], 'withhold')

    def test_unknown_or_duplicate_usage(self):
        for change in ('unknown', 'bool', 'cache', 'duplicate'):
            rows = records('root')
            if change == 'unknown':
                del rows[3]['payload']['usage']['input_tokens']
            elif change == 'bool':
                rows[3]['payload']['usage']['input_tokens'] = True
            elif change == 'cache':
                rows[3]['payload']['usage']['cached_input_tokens'] = 21
            else:
                rows[5:5] = copy.deepcopy(rows[3:5])
            with self.subTest(change=change):
                self.assertEqual(self.assess(root=rows)['status'], 'withhold')

    def test_disconnected_child(self):
        self.assertEqual(self.assess(child=records('child', 'missing'))['status'], 'withhold')

    def test_missing_whole_usage_pair_detected_by_cumulative(self):
        rows = records('root')
        rows[3]['payload']['thread_token_usage'] = {k: 2 * v for k, v in AMOUNT.items()}
        self.assertEqual(self.assess(root=rows)['status'], 'withhold')

    @unittest.skipUnless(os.environ.get('NATIVE_ACCOUNTING_DOCKER') == '1', 'explicit Docker preflight')
    def test_actual_cli_fork_followup_and_missing_usage(self):
        for mode in ('fork_none', 'fork_all', 'missing_usage'):
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as d:
                r = runner.run(Path(d) / 'run', mode)
                self.assertEqual(r['status'], 'passed', r)
                self.assertTrue(r['removed'])
                p = r['probe']
                self.assertEqual(p['root_stdout_usage']['input_tokens'], 120)
                self.assertEqual(p['accounting']['observed_usage']['input_tokens'], 160 if mode == 'missing_usage' else 180)

    @unittest.skipUnless(os.environ.get('NATIVE_ACCOUNTING_DOCKER') == '1', 'explicit Docker preflight')
    def test_container_timeout_cleanup(self):
        with tempfile.TemporaryDirectory() as d:
            r = runner.run(Path(d) / 'run', 'fork_none', start_seconds=.3)
            self.assertEqual(r['status'], 'withhold')
            self.assertTrue(r['removed'])
            self.assertNotIn('probe', r)

    @unittest.skipUnless(os.environ.get('NATIVE_ACCOUNTING_DOCKER') == '1', 'explicit Docker preflight')
    def test_active_child_timeout_cleanup(self):
        with tempfile.TemporaryDirectory() as d:
            r = runner.run(Path(d) / 'run', 'child_timeout')
            self.assertEqual(r['status'], 'withhold')
            self.assertTrue(r['removed'])
            self.assertTrue(r['child_running_observed'])
            self.assertNotIn('probe', r)


if __name__ == '__main__':
    unittest.main()
