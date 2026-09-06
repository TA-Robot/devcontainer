"""Conditional review contracts, information isolation and real-image routing preflight."""
import copy
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
HERE = ROOT / 'experiments/development-harness/queue_review/conditional_v1'
sys.path.insert(0, str(HERE))
import conditional_review as flow
import route_contract as contract
import conditional_report as report


class ConditionalReviewTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='test-conditional-review-')
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)

    def fixture(self):
        baseline = self.root / 'fixture'
        contract.build(baseline)
        return baseline

    def test_only_drafter_receives_condition_specific_information(self):
        a = contract.prompt('drafter', 'control')
        b = contract.prompt('drafter', 'informed')
        self.assertNotIn('Prior local evidence:', a)
        self.assertIn('Prior local evidence:', b)
        for stage in ('reviewer', 'final'):
            self.assertEqual(contract.prompt(stage, 'control'), contract.prompt(stage, 'informed'))
        flow.validate(flow.live_config())
        for condition in flow.CONDITIONS:
            self.assertIn('submit or consult', contract.prompt('drafter', condition))

    def test_request_requires_specific_question_and_real_evidence_without_semantic_gate(self):
        source = self.fixture() / 'workspace'
        valid = {'action': 'consult', 'reason': 'Uncertain', 'question': 'Is the repeated ack invariant preserved?',
                 'evidence': ['queue_store.py']}
        path = source / contract.REQUEST
        path.write_text(json.dumps(valid))
        self.assertEqual(contract.read_request(source, 8192, flow.prior.observe.read_json), valid)
        for key, value in (('action', 'other'), ('question', ''), ('evidence', ['../secret']),
                           ('evidence', ['queue_store.py', 'queue_store.py']), ('reason', '')):
            path.write_text(json.dumps({**valid, key: value}))
            with self.subTest(key=key), self.assertRaises(ValueError):
                contract.read_request(source, 8192, flow.prior.observe.read_json)
        path.write_text('{"action":"submit","action":"consult"}')
        with self.assertRaises(ValueError): contract.read_request(source, 8192, flow.prior.observe.read_json)
        path.write_text('x' * 8193)
        with self.assertRaises(ValueError): contract.read_request(source, 8192, flow.prior.observe.read_json)

    def test_projection_keeps_current_code_but_not_routing_or_git_metadata(self):
        baseline = self.fixture() / 'workspace'
        source = self.root / 'source'
        contract.project(baseline, source)
        (source / 'queue_store.py').write_text((source / 'queue_store.py').read_text() + '\n# transferred\n')
        (source / contract.REQUEST).write_text('{}')
        contract.validate_source(source, baseline, 'drafter')
        target = self.root / 'target'
        contract.project(baseline, target, source)
        self.assertIn('# transferred', (target / 'queue_store.py').read_text())
        self.assertFalse((target / contract.REQUEST).exists())
        self.assertEqual((target / 'TASK.md').read_bytes(), (baseline / 'TASK.md').read_bytes())
        with self.assertRaises(ValueError): contract.validate_source(source, baseline, 'reviewer')
        with self.assertRaises(ValueError): contract.validate_source(source, baseline, 'final')

    def test_reservations_and_nonfinite_caps_stop_admission(self):
        config = flow.live_config()
        for stage in ('drafter', 'reviewer', 'final'):
            with self.subTest(stage=stage), self.assertRaises(ValueError):
                flow.allowance(config, stage, 1, 1)
        seconds, tokens, _, reserve = flow.allowance(config, 'drafter', 600, 12000)
        self.assertEqual((seconds, tokens, reserve), (300, 10000, 135))
        for key, value in (('draft_seconds', True), ('final_reserve_seconds', float('nan')), ('request_bytes', 8193)):
            with self.subTest(key=key), self.assertRaises(ValueError): flow.validate({**config, key: value})

    def test_report_suppresses_ratio_on_missing_usage_stop_or_quality(self):
        row = {'status': 'submitted', 'usage_complete': True, 'execution_seconds': 100,
               'usage': {'input_tokens': 100, 'output_tokens': 100}, 'quality': {'status': 'pass'}}
        value = {'status': 'completed', 'all_writers_stopped': True, 'private_credential_copy_removed': True,
                 'initial_quality': {'status': 'fail'}, 'cleanup': [{'removed': True}],
                 'conditions': {'control': copy.deepcopy(row), 'informed': copy.deepcopy(row)}}
        self.assertEqual(report.interpret(value)['disposition'], 'no-improvement-established')
        value['conditions']['informed']['execution_seconds'] = 80
        self.assertEqual(report.interpret(value)['disposition'], 'candidate-for-independent-confirmation')
        for field, bad in (('usage_complete', False), ('execution_seconds', float('inf')),
                            ('quality', {'status': 'unknown'}), ('usage', {'input_tokens': None, 'output_tokens': 1})):
            invalid = copy.deepcopy(value)
            invalid['conditions']['control'][field] = bad
            self.assertFalse(report.interpret(invalid)['comparison_eligible'])
            self.assertIsNone(report.interpret(invalid)['quality_conditioned_time_ratio'])
        value['all_writers_stopped'] = False
        self.assertIsNone(report.interpret(value)['quality_conditioned_time_ratio'])

    def fake(self, mode):
        fake = self.root / ('fake-' + mode)
        fake.mkdir()
        (fake / 'mode').write_text(mode)
        (fake / 'answer').mkdir()
        for name, source in contract.queue.fixtures.L_GOOD.items():
            path = fake / 'answer' / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(source)
        (fake / 'provider.py').write_text('''import json,sys,shutil
from pathlib import Path
root=Path('/workspace');prompt=sys.stdin.read();mode=Path('/calibration/mode').read_text()
if 'DRAFT DISPATCH:' in prompt:
 if mode in ('submit','unknown-usage','invalid-request'):
  for name in ('queue_store.py','queue_cli.py','bin/queuectl'):shutil.copyfile(Path('/calibration/answer')/name,root/name)
 with (root/'queue_store.py').open('a') as stream:stream.write('\\n# CURRENT_DRAFT_MARKER\\n')
 action='consult' if mode in ('consult','invalid-advice') else 'submit'
 request={'action':action,'reason':'inspected current implementation','question':'Is repeated ack stable?' if action=='consult' else '', 'evidence':['queue_store.py']}
 if mode=='invalid-request':request['action']='bad'
 (root/'review-request.json').write_text(json.dumps(request))
elif 'REVIEW DISPATCH:' in prompt:
 assert 'CURRENT_DRAFT_MARKER' in (root/'queue_store.py').read_text()
 assert not (root/'review-request.json').exists()
 assert 'Is repeated ack stable?' in prompt
 (root/'advice.json').write_text(json.dumps({'recommendation':'' if mode=='invalid-advice' else 'CURRENT_REVIEW_MARKER','evidence':['queue_store.py','bin/queuectl'],'uncertainty':'verify actual behavior'}))
else:
 assert 'FINAL DISPATCH:' in prompt and 'CURRENT_REVIEW_MARKER' in prompt
 assert 'CURRENT_DRAFT_MARKER' in (root/'queue_store.py').read_text()
 assert not (root/'review-request.json').exists()
 for name in ('queue_store.py','queue_cli.py','bin/queuectl'):shutil.copyfile(Path('/calibration/answer')/name,root/name)
 with (root/'queue_store.py').open('a') as stream:stream.write('\\n# CURRENT_DRAFT_MARKER\\n')
if mode!='unknown-usage':print(json.dumps({'type':'turn.completed','usage':{'input_tokens':100,'cached_input_tokens':20,'output_tokens':7}}))
''')
        return fake

    @unittest.skipUnless(os.environ.get('CONDITIONAL_REVIEW_IMAGE'), 'set verified image ID')
    def test_real_submit_consult_and_failure_routes_preserve_inputs_and_costs(self):
        config = flow.live_config()
        config.update(execution='calibration', model='fake', effort='fake', condition_seconds=180,
                      draft_seconds=30, draft_minimum_seconds=1, advisor_seconds=30, advisor_minimum_seconds=1,
                      minimum_seconds=1, final_reserve_seconds=5, output_tokens=1000, minimum_output_tokens=10)
        for mode in ('submit', 'consult', 'unknown-usage', 'invalid-request', 'invalid-advice'):
            with self.subTest(mode=mode):
                output = self.root / mode
                value = flow.run(config, output, fake=self.fake(mode))
                detail = (output / 'controller.private.log').read_text() if (output / 'controller.private.log').exists() else ''
                self.assertTrue(value['all_writers_stopped'], detail)
                self.assertTrue(all(c['removed'] for c in value['cleanup']), detail)
                if mode in ('submit', 'consult'):
                    self.assertEqual(value['status'], 'completed', detail)
                    for row in value['conditions'].values():
                        self.assertEqual(row['quality']['status'], 'pass', row)
                        self.assertEqual(row['route']['action'], mode)
                        self.assertEqual(len(row['actors']), 1 if mode == 'submit' else 3)
                        self.assertEqual(row['usage']['output_tokens'], 7 if mode == 'submit' else 21)
                        if mode == 'consult':
                            self.assertEqual(row['draft_quality']['status'], 'fail')
                            self.assertTrue(row['route']['review_dispatched'])
                else:
                    self.assertEqual(value['status'], 'interrupted', detail)
                    self.assertEqual(value['conditions']['informed']['status'], 'not_started')
                    self.assertEqual(len(value['conditions']['control']['actors']), 2 if mode == 'invalid-advice' else 1)
                    self.assertFalse(report.interpret(value)['comparison_eligible'])
                with self.assertRaises(FileExistsError): flow.run(config, output, fake=self.root / ('fake-' + mode))


if __name__ == '__main__':
    unittest.main()
