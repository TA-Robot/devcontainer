import importlib.util
import os
from pathlib import Path
import sys
import tempfile
import unittest

HERE = Path(__file__).resolve().parents[1]/'experiments/development-harness/scheduling/timing_diagnostic_v1'
sys.path.insert(0, str(HERE))
spec = importlib.util.spec_from_file_location('timing_transport', HERE/'transport.py')
transport = importlib.util.module_from_spec(spec); spec.loader.exec_module(transport)
Policy = transport.Policy


class TimingTests(unittest.TestCase):
    def test_physical_runtime_unchanged(self):
        self.assertEqual((HERE/'runtime.py').read_bytes(), (HERE.parent/'dynamic_v1/runtime.py').read_bytes())
        policy = Policy('/unused')
        self.assertEqual((policy.seconds, policy.response_seconds), (90, 5))

    @unittest.skipUnless(os.environ.get('DYNAMIC_TIMING_DOCKER') == '1', 'explicit Docker timing test')
    def test_timeout_causes_and_cleanup(self):
        with tempfile.TemporaryDirectory() as d:
            source = Path(d)/'policy.py'
            source.write_text('import json,sys,time\nfor line in sys.stdin:\n r=json.loads(line);time.sleep(.2);print(json.dumps({"request_id":r["request_id"],"assignments":[]}),flush=True)\n')
            for seconds, response, cause in [(3, .05, 'response_deadline'), (.5, 5, 'scenario_deadline')]:
                policy = Policy(source, seconds=seconds, response_seconds=response)
                with self.assertRaisesRegex(TimeoutError, cause):
                    with policy:
                        for _ in range(10): policy.choose({})
                self.assertTrue(policy.record['removed'])
                self.assertGreater(policy.record['max_request_seconds'], 0)


if __name__ == '__main__': unittest.main()
