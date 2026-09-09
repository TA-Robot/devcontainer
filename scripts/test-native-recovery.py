import importlib.util
import json
import os
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parents[1]/'experiments/development-harness/scheduling/native_recovery_v1'
spec = importlib.util.spec_from_file_location('native_recovery_actor', HERE/'actor.py')
actor = importlib.util.module_from_spec(spec)
spec.loader.exec_module(actor)
observe = actor.load('recovery_test_observations', HERE/'observations.py')
grader = actor.load('recovery_test_assessment', HERE/'assess.py')


def event(kind, **payload):
    return {'type': kind, 'payload': payload}


def fixture(path, *, gap=False, aborted=False):
    folder = path/'observation/sessions.private'
    folder.mkdir(parents=True)
    amount = dict(input_tokens=20, cached_input_tokens=7, output_tokens=5,
                  cache_write_input_tokens=0, reasoning_output_tokens=0, total_tokens=25)
    rows = [event('session_meta', id='root', session_id='root', parent_thread_id=None, cli_version='0.153.0'),
            event('event_msg', type='task_started', turn_id='t')]
    for i in (1, 2):
        if i == 2 and gap:
            rows += [event('response_item', type='message', role='assistant', content='PRIVATE_PARTIAL'),
                     event('event_msg', type='token_count', info={'total_token_usage': amount}),
                     event('inter_agent_communication_metadata', trigger_turn=False)]
        total = {k: v*i for k, v in amount.items()}
        rows += [event('token_usage_record', thread_id='root', session_id='root', turn_id='t',
                       response_id='r'+str(i), usage=amount, thread_token_usage=total),
                 event('event_msg', type='token_count', info={'total_token_usage': total})]
    rows.append(event('event_msg', type='turn_aborted' if aborted else 'task_complete', turn_id='t'))
    (folder/'root.jsonl').write_text('\n'.join(json.dumps(r) for r in rows)+'\n')
    with sqlite3.connect(path/'observation/inventory.sqlite') as db:
        db.execute('CREATE TABLE threads (id TEXT, model TEXT, reasoning_effort TEXT, cli_version TEXT)')
        db.execute('INSERT INTO threads VALUES (?,?,?,?)', ('root', 'gpt-6-astra', 'high', '0.153.0'))
    (path/'work').mkdir()
    (path/'work/submission.py').write_text('raise RuntimeError("never execute candidate on host")\n')
    return dict(status='withhold', removed=True, credential_copy_removed=True, source_unchanged=True,
                returncode=0, bridge={'status': 'completed', 'returncode': 0, 'reason': None,
                                      'development_seconds': 1})


class RecoveryTests(unittest.TestCase):
    def test_evaluator_failure_is_not_invalid_policy_or_zero_quality(self):
        measured = [{'status': 'measured'}]
        invalid = [{'status': 'measured'}, {'status': 'invalid-policy'}]
        self.assertEqual(grader.quality_status(measured, 0), 'measured')
        self.assertEqual(grader.quality_status(invalid, 1), 'invalid-policy')
        for rows, code in ((measured, 1), (measured, -9), (invalid, 0),
                           (invalid+[{'status': 'unmeasured'}], 1), ([], 0)):
            self.assertEqual(grader.quality_status(rows, code), 'withhold')

    def test_gap_preserves_lifecycle_and_later_usage_without_budget_admission(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            report = fixture(root, gap=True)
            actor.finish(root, report, condition='solo', seconds=60, output_tokens=80000)
            self.assertEqual(report['lifecycle']['status'], 'completed')
            self.assertEqual(report['usage']['status'], 'partial')
            self.assertEqual(report['usage']['known_usage']['output_tokens'], 10)
            self.assertEqual(report['usage']['known_response_records'], 2)
            self.assertEqual(report['budget']['output_tokens'], 'unknown')
            self.assertEqual(report['quality']['status'], 'eligible')
            self.assertEqual(report['admission'], 'withhold')
            self.assertNotIn('PRIVATE_PARTIAL', json.dumps(report))
            stages = [r['stage'] for r in report['milestones']]
            self.assertLess(stages.index('artifact_sealed'), stages.index('accounting_started'))

    def test_time_abort_cost_cleanup_and_bad_source_are_distinct(self):
        for mode in ('time', 'abort', 'partial_cost', 'cost', 'cleanup', 'source', 'symlink'):
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as d:
                root = Path(d)
                report = fixture(root, gap=mode == 'partial_cost', aborted=mode == 'abort')
                if mode == 'time': report['bridge']['development_seconds'] = 61
                if mode == 'cleanup': report['removed'] = False
                if mode == 'source': report['source_unchanged'] = False
                if mode == 'symlink':
                    (root/'work/submission.py').rename(root/'work/other.py')
                    (root/'work/submission.py').symlink_to(root/'work/other.py')
                actor.finish(root, report, condition='solo', seconds=60, output_tokens=9)
                self.assertEqual(report['admission'], 'withhold')
                if mode in ('partial_cost', 'cost'):
                    self.assertEqual(report['budget']['output_tokens'], 'exceeded')
                    self.assertEqual(report['quality']['status'], 'eligible')
                else:
                    self.assertEqual(report['quality']['status'], 'withhold')
                if mode in ('time', 'abort'):
                    self.assertEqual(report['artifact']['status'], 'sealed')
                if mode in ('cleanup', 'source', 'symlink'):
                    self.assertFalse((root/'submission.py').exists())

    def test_collector_failure_cannot_erase_seal_and_seal_is_exclusive(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            report = fixture(root)
            def fail(*args):
                self.assertTrue((root/'submission-seal.json').exists())
                raise ValueError('broken collector')
            with patch.object(actor, 'load', side_effect=fail):
                actor.finish(root, report, condition='solo', seconds=60, output_tokens=80000)
            self.assertEqual(report['artifact']['status'], 'sealed')
            self.assertEqual(report['quality']['status'], 'withhold')
            self.assertEqual(report['admission'], 'withhold')
            with self.assertRaises(FileExistsError):
                actor.freeze_submission(root/'work/submission.py', root/'submission.py')

    def test_inventory_mismatch_and_bad_usage_do_not_become_complete(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            fixture(root)
            with sqlite3.connect(root/'observation/inventory.sqlite') as db:
                db.execute("UPDATE threads SET model='unexpected'")
            result = observe.inspect(root/'observation/sessions.private', root/'observation/inventory.sqlite', 'solo')
            self.assertEqual(result['lifecycle']['status'], 'unknown')
            self.assertEqual(result['usage']['status'], 'partial')
            source = root/'observation/sessions.private/root.jsonl'
            rows = [json.loads(line) for line in source.read_text().splitlines()]
            rows[2]['payload']['usage']['cached_input_tokens'] = 99
            source.write_text('\n'.join(json.dumps(r) for r in rows)+'\n')
            result = observe.inspect(root/'observation/sessions.private', root/'observation/inventory.sqlite', 'solo')
            self.assertEqual(result['usage']['known_response_records'], 1)

    @unittest.skipUnless(os.environ.get('NATIVE_RECOVERY_DOCKER') == '1', 'explicit pinned CLI/Docker preflight')
    def test_tree_compaction_and_missing_compaction_records(self):
        with tempfile.TemporaryDirectory() as d:
            evidence = os.environ.get('NATIVE_RECOVERY_EVIDENCE')
            base = Path(evidence+'-extended') if evidence else Path(d)/'extended'
            base.mkdir(parents=True, mode=0o700, exist_ok=False)
            initial = actor.identity()
            actor.save(base/'plan.json', {'source_sha256': initial, 'live_calls': 0})
            actor.prepare_public(base/'public')
            for mode in ('tree', 'compact', 'remote_compact', 'missing_compact'):
                with self.subTest(mode=mode):
                    r = actor.run(base/mode, base/'public', condition='adaptive', fake=True, fake_mode=mode,
                                  seconds=60, output_tokens=80000, prompt='Finite accounting regression.')
                    self.assertTrue(r['removed'] and r['source_unchanged'])
                    self.assertEqual(r['lifecycle']['status'], 'completed', r)
                    self.assertEqual(r['quality']['status'], 'withhold')  # Fixture does not submit a policy.
                    self.assertEqual(r['usage']['status'], 'partial' if mode == 'missing_compact' else 'complete', r)
                    fixture_report = actor.read(base/mode/'stdout.private.txt')
                    self.assertEqual(r['usage']['known_usage']['output_tokens'],
                        sum(q['usage']['output_tokens'] for q in fixture_report['requests'] if q['usage']))
                    if mode == 'tree': self.assertEqual(len(r['lifecycle']['threads']), 4)
                    if mode == 'remote_compact':
                        self.assertGreater(r['usage']['known_usage']['output_tokens'],
                                           fixture_report['root_stdout_usage']['output_tokens'])
            self.assertEqual(actor.identity(), initial)

    @unittest.skipUnless(os.environ.get('NATIVE_RECOVERY_DOCKER') == '1', 'explicit pinned CLI/Docker preflight')
    def test_pinned_native_execution_recovery_and_independent_quality(self):
        configurations = [
            ('solo', 'solo', 'fork_none', 60, 80000, 'complete', 'within', 'eligible'),
            ('adaptive', 'adaptive', 'fork_all', 60, 80000, 'complete', 'within', 'eligible'),
            ('missing', 'adaptive', 'missing_usage', 60, 80000, 'partial', 'unknown', 'eligible'),
            ('timeout', 'adaptive', 'child_timeout', 8, 80000, 'partial', 'unknown', 'withhold'),
            ('cost', 'adaptive', 'fork_all', 60, 40, 'complete', 'exceeded', 'eligible'),
            ('notice_delayed', 'adaptive', 'notice_delayed', 30, 80000, 'complete', 'within', 'eligible'),
            ('notice_missing', 'adaptive', 'notice_missing', 30, 80000, 'partial', 'unknown', 'eligible'),
            ('notice_control', 'adaptive', 'notice_control', 30, 80000, 'complete', 'within', 'eligible'),
        ]
        with tempfile.TemporaryDirectory() as d:
            base = Path(os.environ.get('NATIVE_RECOVERY_EVIDENCE', str(Path(d)/'preflight')))
            base.mkdir(parents=True, mode=0o700, exist_ok=False)
            initial = actor.identity()
            actor.save(base/'plan.json', {'source_sha256': initial, 'cases': configurations, 'live_calls': 0})
            actor.prepare_public(base/'public')
            summary = {}
            try:
                for name, condition, mode, seconds, cap, usage, budget, quality in configurations:
                    with self.subTest(name=name):
                        r = actor.run(base/name, base/'public', condition=condition, fake=True, fake_mode=mode,
                                      seconds=seconds, output_tokens=cap, prompt='Finite recovery calibration.')
                        summary[name] = r
                        self.assertTrue(r['removed'] and r['credential_copy_removed'] and r['source_unchanged'])
                        self.assertEqual(r['usage']['status'], usage, r)
                        self.assertEqual(r['budget']['output_tokens'], budget, r)
                        self.assertEqual(r['quality']['status'], quality, r)
                        expected = 'admitted' if usage == 'complete' and budget == 'within' and quality == 'eligible' else 'withhold'
                        self.assertEqual(r['admission'], expected)
                        if name == 'timeout':
                            self.assertIn('deadline', r['bridge']['reason'])
                            self.assertEqual(r['budget']['wall_clock'], 'exceeded')
                            continue
                        self.assertEqual(r['lifecycle']['status'], 'completed')
                        stages = [s['stage'] for s in r['milestones']]
                        self.assertLess(stages.index('artifact_sealed'), stages.index('accounting_started'))
                        if name != 'solo':
                            fixture_report = actor.read(base/name/'stdout.private.txt')
                            self.assertEqual(r['usage']['known_usage']['output_tokens'],
                                sum(q['usage']['output_tokens'] for q in fixture_report['requests'] if q['usage']))
                            if name in ('adaptive', 'missing', 'cost'):
                                self.assertTrue(fixture_report['child_network_denied'])
                                self.assertFalse((base/name/'observation/forged').exists())
                        assessed = grader.assess(base/name, base/'public/probe.json', base/(name+'-assessment'))
                        self.assertEqual(assessed['status'], 'measured', assessed)
                        self.assertEqual(assessed['budget_admission'], expected)
                        self.assertEqual(assessed['cleanup'], 'confirmed')
                        # Frozen fake sources all select the exact public FIFO.
                        self.assertEqual(r['artifact']['sha256'], actor.sha(base/'public/fifo.py'))
                        public_name = 'repaired-report.json' if name == 'solo' else 'child-report.json'
                        if (base/name/'work'/public_name).exists():
                            self.assertEqual(assessed['evaluation']['cases'][0]['result'],
                                             actor.read(base/name/'work'/public_name)['cases'][0]['result'])
                self.assertEqual(actor.identity(), initial)
                with self.assertRaises(FileExistsError):
                    actor.run(base/'solo', base/'public', condition='solo', fake=True, prompt='No replay.')
            finally:
                actor.save(base/'results.json', summary)


if __name__ == '__main__':
    unittest.main()
