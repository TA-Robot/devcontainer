import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


HERE = Path(__file__).resolve().parents[1] / 'experiments/development-harness/scheduling/native_actor_v1'
spec = importlib.util.spec_from_file_location('native_development_actor', HERE / 'actor.py')
actor = importlib.util.module_from_spec(spec)
spec.loader.exec_module(actor)


class NativeActorTests(unittest.TestCase):
    def test_common_public_clock_and_contract(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / 'public'; actor.prepare_public(p)
            self.assertEqual((p / 'transport.py').read_bytes(), (actor.TIMING / 'transport.py').read_bytes())
            self.assertEqual((p / 'runtime.py').read_bytes(), (actor.TIMING / 'runtime.py').read_bytes())
            self.assertIn('90 seconds per scenario', (p / 'RUNTIME.md').read_text())
            self.assertNotIn('Do not call another model or spawn an agent', (p / 'TASK.md').read_text())
            self.assertEqual(len(json.loads((p / 'development.json').read_text())), 24)

    @unittest.skipUnless(os.environ.get('NATIVE_ACTOR_DOCKER') == '1', 'explicit actual CLI/Docker preflight')
    def test_common_bridge_normal_and_failure_paths(self):
        configurations = [('solo', 'solo', 'fork_none', 60, 80000, 'completed'),
                          ('adaptive', 'adaptive', 'fork_all', 60, 80000, 'completed'),
                          ('missing', 'adaptive', 'missing_usage', 60, 80000, 'withhold'),
                          ('timeout', 'adaptive', 'child_timeout', 8, 80000, 'withhold'),
                          ('cost', 'adaptive', 'fork_all', 60, 40, 'withhold')]
        with tempfile.TemporaryDirectory() as d:
            base = Path(os.environ.get('NATIVE_ACTOR_EVIDENCE', d))
            if str(base) != d:
                base.mkdir(mode=0o700, parents=True, exist_ok=False)
            actor.prepare_public(base / 'public')
            for name, condition, mode, seconds, cap, expected in configurations:
                with self.subTest(name=name):
                    r = actor.run(base / name, base / 'public', condition=condition, fake=True,
                        fake_mode=mode, seconds=seconds, output_tokens=cap, prompt='Finite synthetic bridge preflight.')
                    self.assertEqual(r['status'], expected, r)
                    self.assertTrue(r['removed'] and r['credential_copy_removed'] and r['source_unchanged'])
                    if expected == 'completed':
                        self.assertEqual(r['usage']['input_tokens'], 80 if condition == 'solo' else 180)
                        grading = base / (name + '-assessment')
                        subprocess.run([sys.executable, str(actor.TIMING / 'evaluate.py'),
                            '--candidate', str(base / name / 'work/submission.py'),
                            '--scenarios', str(base / 'public/probe.json'), '--output', str(grading)],
                            check=True, capture_output=True, timeout=120)
                        external = actor.read(grading / 'result.json')
                        self.assertEqual(external['status'], 'completed')
                        self.assertTrue(external['all_containers_removed'])
                        filename = 'repaired-report.json' if condition == 'solo' else 'child-report.json'
                        public = actor.read(base / name / 'work' / filename)
                        self.assertEqual(external['cases'][0]['result'], public['cases'][0]['result'])
                    else:
                        self.assertIsNone(r['usage'])
                    if name == 'timeout':
                        self.assertTrue((base / name / 'work/child-running.txt').is_file())
                        self.assertIn('deadline', r['bridge']['reason'])
                        self.assertIn('accounting', r['bridge'])
                    if name == 'missing':
                        self.assertEqual(r['bridge']['accounting']['observed_usage']['input_tokens'], 160)
                    if name == 'cost':
                        self.assertEqual(r['bridge']['reason'], 'observed output token cap exceeded')
                    if name == 'adaptive':
                        checks = actor.read(base / name / 'work/child-network.json')
                        self.assertTrue(checks['denied'] and checks['observation_protected'])
                        self.assertFalse((base / name / 'observation/forged').exists())
                        self.assertEqual(actor.read(base / name / 'work/child-report.json')['valid'], True)
                    # Neither the copied native home nor credentials are in evidence.
                    self.assertFalse((base / name / 'observation/auth.json').exists())


if __name__ == '__main__':
    unittest.main()
