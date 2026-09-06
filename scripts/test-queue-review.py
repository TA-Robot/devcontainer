"""Queue task boundaries, external code isolation and the frozen pilot binding."""
import copy
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
HERE = ROOT / 'experiments/development-harness/queue_review/v1'
sys.path.insert(0, str(HERE))
import behavior
import task
import pilot
import queue_calibration as calibration


class QueueReviewTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='test-queue-review-')
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)

    def fixture(self, variant):
        path = self.root / variant
        task.build(path, variant)
        return path

    def test_public_brief_and_tools_do_not_disclose_private_scenario(self):
        inputs = [task.files(v) for v in task.VARIANTS]
        for key in ('AGENTS.md', 'TASK.md', 'FORMAT.md', 'tools/check_queue.py', 'tests/test_queue_store.py'):
            self.assertTrue(all(value[key] == inputs[0][key] for value in inputs))
        self.assertFalse(any('calibration' in path or 'reference' in path for path in inputs[0]))
        for variant, expected in (('repair', 'fail'), ('preserve', 'pass'), ('confirmation', 'fail')):
            self.assertEqual(behavior.evaluate(self.fixture(variant) / 'workspace')['status'], expected)

    def test_noop_is_valid_and_reviewer_cannot_change_source(self):
        baseline = self.fixture('preserve') / 'workspace'
        candidate = self.root / 'candidate'
        shutil.copytree(baseline, candidate)
        task.validate_source(candidate, baseline, 'maker')
        (candidate / 'advice.json').write_text('{}')
        task.validate_source(candidate, baseline, 'advisor')
        (candidate / 'queue_store.py').write_text('changed')
        with self.assertRaises(ValueError):
            task.validate_source(candidate, baseline, 'advisor')

    def test_fixed_tool_extra_artifacts_symlinks_and_executable_mode_are_rejected(self):
        baseline = self.fixture('repair') / 'workspace'
        for label in ('tool', 'extra', 'symlink', 'mode'):
            candidate = self.root / label
            shutil.copytree(baseline, candidate)
            if label == 'tool': (candidate / 'tools/check_queue.py').write_text('print("pass")')
            elif label == 'extra': (candidate / 'extra').mkdir()
            elif label == 'symlink':
                (candidate / 'queue_store.py').unlink()
                (candidate / 'queue_store.py').symlink_to('/etc/passwd')
            else: (candidate / 'bin/queuectl').chmod(0o644)
            with self.subTest(label=label), self.assertRaises(ValueError):
                task.validate_source(candidate, baseline, 'maker')

    def test_safe_state_reader_rejects_symlinks_fifo_and_oversize(self):
        p = self.root / 'state'
        p.symlink_to('/etc/passwd')
        with self.assertRaises(OSError): behavior.read_bytes(p)
        p.unlink()
        os.mkfifo(p)
        with self.assertRaises(ValueError): behavior.read_bytes(p)
        p.unlink()
        p.write_bytes(b'x' * (behavior.BYTE_CAP + 1))
        with self.assertRaises(ValueError): behavior.read_bytes(p)

    def test_binding_does_not_mutate_historical_pilot_and_reserves_confirmation(self):
        sys.path.insert(0, str(pilot.CONSULTATION))
        import synthesis_pilot
        old_kind, old_task = synthesis_pilot.KIND, synthesis_pilot.task
        engine = pilot.binding('repair', pilot.IMAGE)
        self.assertEqual(engine.KIND, pilot.KIND)
        self.assertEqual(synthesis_pilot.KIND, old_kind)
        self.assertIs(synthesis_pilot.task, old_task)
        with self.assertRaises(ValueError): pilot.live_config('confirmation')
        with self.assertRaises(ValueError): pilot.run({**pilot.live_config('repair'), 'output_tokens': 99999}, self.root / 'bad')
        self.assertFalse((self.root / 'bad').exists())

    def test_timeout_stays_unknown(self):
        def timed_out(*args): raise subprocess.TimeoutExpired('queue', 1)
        value = behavior.evaluate(self.root, timed_out)
        self.assertEqual(value['status'], 'unknown')

    def test_output_stream_cap_and_timeout_stop_owned_process(self):
        with self.assertRaises(ValueError):
            behavior.capture([sys.executable, '-c', 'import sys;sys.stderr.write("x"*1000000)'], 5)
        with self.assertRaises(subprocess.TimeoutExpired):
            behavior.capture([sys.executable, '-c', 'import time;time.sleep(60)'], .1)
        self.assertEqual(behavior.capture([sys.executable, '-c', 'print("ok")'], 5), (0, 'ok\n'))

    @unittest.skipUnless(os.environ.get('QUEUE_REVIEW_IMAGE'), 'set verified image ID')
    def test_external_calibration_accepts_alternative_and_rejects_known_defects(self):
        value = calibration.calibrate(os.environ['QUEUE_REVIEW_IMAGE'])
        self.assertEqual(value['status'], 'pass', [(r['candidate'], r['external']) for r in value['records'] if r['status'] != 'pass'])
        self.assertEqual(len(value['records']), 9)
        self.assertTrue(all(not r['external']['isolation']['evaluator_code_mounted_to_candidate'] for r in value['records']))

    @unittest.skipUnless(os.environ.get('QUEUE_REVIEW_IMAGE'), 'set verified image ID')
    def test_both_pairs_capture_review_usage_noop_and_external_results(self):
        fake = self.root / 'fake'
        fake.mkdir()
        (fake / 'answer').mkdir()
        for name, source in task.fixtures.L_GOOD.items():
            target = fake / 'answer' / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(source)
        (fake / 'provider.py').write_text('''import json,sys,shutil
from pathlib import Path
prompt=sys.stdin.read()
root=Path('/workspace')
assert 'Inspect existing source and DEVELOPMENT_HANDOFF.md' not in prompt
if 'ADVISORY DISPATCH' in prompt:
 (root/'advice.json').write_text(json.dumps({'recommendation':'REVIEW_TRANSFER_MARKER', 'evidence':['queue_store.py','bin/queuectl'], 'uncertainty':'verify behavior'}))
else:
 for name in ('queue_store.py','queue_cli.py','bin/queuectl'):
  shutil.copyfile(Path('/calibration/answer')/name,root/name)
if not (Path('/calibration/unknown-usage').exists() and 'ADVISORY DISPATCH' in prompt):
 print(json.dumps({'type':'turn.completed','usage':{'input_tokens':100,'cached_input_tokens':20,'output_tokens':7}}))
''')
        for variant in ('repair', 'preserve'):
            config = pilot.live_config(variant)
            config.update(execution='calibration', model='fake', effort='fake',
                          condition_seconds=90, advisor_seconds=15, advisor_minimum_seconds=1,
                          minimum_seconds=1, output_tokens=1000, minimum_output_tokens=10)
            output = self.root / ('run-' + variant)
            value = pilot.run(config, output, fake=fake)
            self.assertEqual(value['status'], 'completed', (value, (output / 'controller.private.log').read_text() if (output / 'controller.private.log').exists() else ''))
            self.assertTrue(value['all_writers_stopped'])
            self.assertTrue(all(r['removed'] for r in value['cleanup']))
            for row in value['conditions'].values(): self.assertEqual(row['quality']['status'], 'pass', row)
            self.assertEqual(value['conditions']['consult']['usage']['output_tokens'], 14)
            self.assertEqual(value['conditions']['solo']['usage']['output_tokens'], 7)
            summary = json.loads((output / 'queue-summary.json').read_text())
            self.assertEqual(summary['initial_quality']['status'], 'fail' if variant == 'repair' else 'pass')
            self.assertIn('REVIEW_TRANSFER_MARKER', (output / 'consult-maker-state/actual-prompt.private.txt').read_text())
            if variant == 'preserve':
                self.assertEqual(value['conditions']['solo']['quality']['changed_paths'], [])
            with self.assertRaises(FileExistsError): pilot.run(config, output, fake=fake)
        (fake / 'unknown-usage').touch()
        config['order'] = ['consult', 'solo']
        value = pilot.run(config, self.root / 'unknown', fake=fake)
        self.assertEqual(value['status'], 'interrupted')
        self.assertEqual(value['conditions']['solo']['status'], 'not_started')
        self.assertEqual(len(value['conditions']['consult']['actors']), 1)
        self.assertTrue(value['all_writers_stopped'])


if __name__ == '__main__':
    unittest.main()
