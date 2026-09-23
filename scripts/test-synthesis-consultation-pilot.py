"""New pilot adapter tests; real image probes, deterministic provider outputs."""
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
HERE = ROOT / 'experiments/development-harness/consultation'
sys.path.insert(0, str(HERE))
import synthesis_pilot as pilot
import synthesis_task as task


def config(image):
    return {'kind': pilot.KIND, 'execution': 'calibration', 'model': 'fake', 'effort': 'fake',
            'cli_version': '0.153.0', 'image': image, 'order': ['solo', 'consult'],
            'condition_seconds': 90, 'advisor_seconds': 15, 'advisor_minimum_seconds': 1, 'minimum_seconds': 1,
            'output_tokens': 1000, 'minimum_output_tokens': 10, 'stop_seconds': 10,
            'capture_seconds': 30, 'capture_window_seconds': 10,
            'snapshot_bytes': 16777216, 'advice_bytes': 16384}


class PilotTests(unittest.TestCase):
    def test_maker_reservation_does_not_become_advisor_minimum(self):
        value = config('sha256:' + 'a' * 64)
        value.update(condition_seconds=900, advisor_seconds=180, advisor_minimum_seconds=30, minimum_seconds=300)
        pilot.validate(value)
        manifest = pilot.actor_manifest(value, 'consult', 'advisor', 180, 990, None)
        self.assertEqual(manifest['admission']['stages']['advisor']['minimum_seconds'], 30)
        state = {'manifest': manifest, 'manifest_sha256': pilot.runner.fingerprint(manifest),
                 'sessions': [], 'next_phase': 0, 'status': 'ready'}
        self.assertTrue(pilot.runner.assess(state)['admitted'])

    def test_environment_order_is_normalized_but_duplicate_keys_are_rejected(self):
        transport = object.__new__(pilot.codex_transport.Transport)
        for env, expected in ((['B=2','A=1'], ['A=1','B=2']), (['A=9','B=2'], ['A=9','B=2'])):
            with patch.object(pilot.codex_transport.public.Docker, 'environment', return_value={'config': {'Env': env}}):
                self.assertEqual(transport.environment()['config']['Env'], expected)
        with patch.object(pilot.codex_transport.public.Docker, 'environment', return_value={'config': {'Env': ['A=1','A=2']}}):
            with self.assertRaises(ValueError):
                transport.environment()

    def test_relay_replaces_generic_handoff_and_rejects_changed_input(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            actual = root / 'actual'
            actual.write_bytes(b'ONLY_TASK_DELIVERABLES')
            spec = root / 'spec.json'
            spec.write_text(json.dumps({'terminal_prompt_sha256': hashlib.sha256(b'OLD_ENVELOPE').hexdigest(),
                'actual_prompt': str(actual), 'actual_prompt_sha256': hashlib.sha256(actual.read_bytes()).hexdigest(),
                'argv': [sys.executable, '-c', 'import sys;print(sys.stdin.read())']}))
            ok = subprocess.run([sys.executable, str(HERE / 'prompt_relay.py'), str(spec)],
                                input='OLD_ENVELOPE', capture_output=True, text=True)
            self.assertEqual(ok.returncode, 0, ok.stderr)
            self.assertEqual(ok.stdout.strip(), 'ONLY_TASK_DELIVERABLES')
            bad = subprocess.run([sys.executable, str(HERE / 'prompt_relay.py'), str(spec)],
                                 input='CHANGED', capture_output=True, text=True)
            self.assertNotEqual(bad.returncode, 0)

    def test_mode_and_caps_are_explicit(self):
        value = config('sha256:' + 'a' * 64)
        pilot.validate(value)
        for key, bad in (('execution', 'unspecified'), ('image', 'latest'), ('condition_seconds', float('inf')),
                         ('advisor_seconds', True), ('order', ['solo'])):
            with self.subTest(key=key), self.assertRaises(ValueError):
                pilot.validate({**value, key: bad})

    def test_task_boundary_rejects_unpublished_handoff_and_source_edits(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            task.build(root / 'fixture')
            base = root / 'fixture/workspace'
            candidate = root / 'candidate'
            shutil.copytree(base, candidate)
            for name in task.OUTPUTS:
                (candidate / name).write_text('{}')
            task.validate_source(candidate, base, 'maker')
            (candidate / 'DEVELOPMENT_HANDOFF.md').write_text('unexpected')
            with self.assertRaises(ValueError):
                task.validate_source(candidate, base, 'maker')
            (candidate / 'DEVELOPMENT_HANDOFF.md').unlink()
            (candidate / 'constraints.json').write_text('{}')
            with self.assertRaises(ValueError):
                task.validate_source(candidate, base, 'maker')

    @unittest.skipUnless(os.environ.get('SYNTHESIS_PILOT_IMAGE'), 'set verified image ID')
    def test_real_sandbox_probes_pair_relay_and_independent_scoring(self):
        with tempfile.TemporaryDirectory(prefix='synthesis-pilot-test-') as raw:
            root = Path(raw)
            fake = root / 'fake'
            fake.mkdir()
            (fake / 'answer.json').write_text(json.dumps(task.f12.L_GOOD))
            (fake / 'answer.md').write_text(task.f12.L_GOOD_MD)
            (fake / 'provider.py').write_text('''import json,sys,shutil
from pathlib import Path
prompt=sys.stdin.read()
assert 'Inspect existing source and DEVELOPMENT_HANDOFF.md' not in prompt
root=Path('/workspace')
if 'ADVISORY DISPATCH' in prompt:
 (root/'advice.json').write_text(json.dumps({'recommendation':'CALIBRATED_ADVICE','evidence':['CON-MIGRATION'], 'uncertainty':'not operationally verified'}))
else:
 shutil.copyfile('/calibration/answer.json',root/'decision-record.json')
 shutil.copyfile('/calibration/answer.md',root/'DECISION-RECORD.md')
if not (Path('/calibration/unknown-usage').exists() and 'ADVISORY DISPATCH' in prompt):
 print(json.dumps({'type':'turn.completed','usage':{'input_tokens':100,'cached_input_tokens':20,'output_tokens':7}}))
''')
            result = pilot.run(config(os.environ['SYNTHESIS_PILOT_IMAGE']), root / 'run', fake=fake)
            diagnostic = root / 'run/controller.private.log'
            self.assertEqual(result['status'], 'completed', (result, diagnostic.read_text() if diagnostic.exists() else ''))
            self.assertTrue(result['all_writers_stopped'])
            self.assertTrue(all(row['removed'] for row in result['cleanup']))
            for row in result['conditions'].values():
                self.assertEqual(row['quality']['status'], 'pass', row)
                self.assertEqual(row['quality']['score']['passed'], 12)
                self.assertFalse(row['quality']['isolation']['credential_mounts'])
            self.assertEqual(result['conditions']['consult']['usage']['output_tokens'], 14)
            self.assertEqual(result['conditions']['solo']['usage']['output_tokens'], 7)
            actual = (root / 'run/consult-maker-state/actual-prompt.private.txt').read_text()
            self.assertIn('CALIBRATED_ADVICE', actual)
            self.assertNotIn('CALIBRATED_ADVICE', json.dumps(result))
            with self.assertRaises(FileExistsError):
                pilot.run(config(os.environ['SYNTHESIS_PILOT_IMAGE']), root / 'run', fake=fake)
            (fake / 'unknown-usage').touch()
            second = config(os.environ['SYNTHESIS_PILOT_IMAGE'])
            second['order'] = ['consult', 'solo']
            stopped = pilot.run(second, root / 'unknown-run', fake=fake)
            self.assertEqual(stopped['status'], 'interrupted', stopped)
            self.assertTrue(stopped['all_writers_stopped'])
            self.assertTrue(all(row['removed'] for row in stopped['cleanup']))
            self.assertEqual(len(stopped['conditions']['consult']['actors']), 1)
            self.assertFalse(stopped['conditions']['consult']['usage_complete'])
            self.assertIsNone(stopped['conditions']['consult']['quality'])
            self.assertEqual(stopped['conditions']['solo']['status'], 'not_started')


if __name__ == '__main__':
    unittest.main()
