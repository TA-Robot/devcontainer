import importlib.util
import os
from pathlib import Path
import tempfile
import unittest

HERE = Path(__file__).resolve().parents[1]/'experiments/development-harness/scheduling/startup_probe_v1'
spec = importlib.util.spec_from_file_location('startup_probe_tests', HERE/'run.py')
probe = importlib.util.module_from_spec(spec); spec.loader.exec_module(probe)


class StartupProbeTests(unittest.TestCase):
    def test_fixed_fixture_matrix_and_unchanged_transport(self):
        self.assertEqual([probe.expected(p, c) for p in ('normal', 'startup_delay', 'response_delay')
                          for c in ('legacy', 'ready')],
                         ['responded', 'responded', 'deadline', 'responded', 'deadline', 'deadline'])
        source = probe.identity()
        self.assertEqual(source['experiments/development-harness/scheduling/timing_diagnostic_v1/transport.py'],
                         'bdca10b6e93a0c7513ee73eb97b5aca69624c941c1ac1d7e1d111677f4bf13e2')
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(ValueError): probe.trial(Path(d)/'bad', 'unknown', 'ready')
            self.assertFalse((Path(d)/'bad').exists())

    @unittest.skipUnless(os.environ.get('STARTUP_PROBE_DOCKER') == '1', 'explicit isolated Docker diagnostic')
    def test_controlled_startup_and_response_delays(self):
        with tempfile.TemporaryDirectory() as d:
            output = Path(os.environ.get('STARTUP_PROBE_EVIDENCE', str(Path(d)/'probe')))
            result = probe.run(output)
            self.assertEqual(result['status'], 'observed_expected_separation', result)
            self.assertEqual(len(result['trials']), 6)
            for row in result['trials']:
                self.assertEqual(row['recovery']['status'], 'confirmed')
                self.assertTrue(row['policy_unchanged'])
                if row['clock_mode'] == 'ready':
                    self.assertIsNotNone(row['readiness_wait_seconds'])
            with self.assertRaises(FileExistsError): probe.run(output)


if __name__ == '__main__': unittest.main()
