#!/usr/bin/env python3
"""Calibrate the small-task evaluator against controlled parsers and real support modules."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parent.parent
EVALUATOR = ROOT / 'experiments/development-harness/multi-scale/evaluate_small.py'
PARSER_CONTROL = '''import os, math
from agentctl_jobs import AgentctlJobError
class Supervisor:
    def __init__(self, paths, entrypoint):
        raw = os.environ.get('AGENTCTL_ORPHAN_AFTER_SECONDS', '30')
        try:
            self.orphan_after_seconds = float(raw)
        except ValueError as error:
            raise AgentctlJobError('invalid AGENTCTL_ORPHAN_AFTER_SECONDS') from error
        if self.orphan_after_seconds < 0.1:
            raise AgentctlJobError('invalid AGENTCTL_ORPHAN_AFTER_SECONDS')
'''


class SmallEvaluatorTests(unittest.TestCase):
    def evaluate_copy(self, transform):
        with tempfile.TemporaryDirectory(prefix='small-evaluator-control-') as raw:
            root = Path(raw)
            scripts = root / 'candidate/scripts'
            scripts.mkdir(parents=True)
            for name in ('agentctl_jobs.py', 'agent_contracts.py'):
                shutil.copy2(ROOT / 'scripts' / name, scripts / name)
            supervisor = scripts / 'agentctl_supervisor.py'
            supervisor.write_text(transform(PARSER_CONTROL))
            result_path = root / 'result.json'
            process = subprocess.run([sys.executable, str(EVALUATOR), '--candidate', str(scripts.parent),
                                      '--output', str(result_path)],
                                     env={**os.environ, 'PYTHONDONTWRITEBYTECODE': '1'},
                                     capture_output=True, text=True, timeout=20)
            return process, json.loads(result_path.read_text())

    def test_non_finite_accepting_parser_is_rejected(self):
        process, result = self.evaluate_copy(lambda text: text)
        self.assertEqual(process.returncode, 1)
        self.assertEqual(result['passed'], 16)
        self.assertEqual(result['total'], 21)
        self.assertFalse(result['accepted'])

    def test_finite_guard_control_is_accepted_without_runtime_side_effects(self):
        def control(text):
            needle = 'if self.orphan_after_seconds < 0.1:'
            self.assertIn(needle, text)
            return text.replace(needle, "if not __import__('math').isfinite(self.orphan_after_seconds) or self.orphan_after_seconds < 0.1:")
        process, result = self.evaluate_copy(control)
        self.assertEqual(process.returncode, 0, process.stderr)
        self.assertEqual(result['passed'], 21)
        self.assertTrue(result['accepted'])
        self.assertTrue(result['source_unchanged'])
        self.assertTrue(result['no_runtime_state_created'])

    def test_constant_default_mutant_cannot_pass(self):
        process, result = self.evaluate_copy(lambda text: text.replace(
            'self.orphan_after_seconds = float(raw)', 'self.orphan_after_seconds = 30.0'))
        self.assertEqual(process.returncode, 1)
        self.assertFalse(result['accepted'])
        self.assertEqual(result['passed'], 2)


if __name__ == '__main__':
    unittest.main()
