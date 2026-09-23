import json
import os
from pathlib import Path
import sys
import tempfile
import unittest

HERE = Path(__file__).resolve().parents[1]/'experiments/development-harness/scheduling/dynamic_solo_v1'
sys.path.insert(0, str(HERE))
import runner


class SoloTests(unittest.TestCase):
    def test_public_allowlist_and_replacement_contract(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)/'public'; manifest = runner.projection.prepare(p)
            self.assertEqual(set(manifest), {'TASK.md', 'RUNTIME.md', 'runtime.py', 'transport.py', 'fifo.py',
                             'public_check.py', 'development.json', 'probe.json', 'ACTOR_ONLY'})
            self.assertEqual(len(json.loads((p/'development.json').read_text())), 24)
            self.assertTrue(all(c['id'].startswith('development-') for c in json.loads((p/'development.json').read_text())))
            self.assertNotIn('A reachable demanding target will be fixed', (p/'RUNTIME.md').read_text())
            self.assertNotIn('def score', (p/'fifo.py').read_text())

    def test_unknown_usage_and_extra_model_stop(self):
        events = [{'type': 'item.completed', 'item': {'type': 'agent_message', 'text': 'done'}},
                  {'type': 'turn.completed', 'usage': {'input_tokens': 20, 'cached_input_tokens': 10, 'output_tokens': 5}}]
        encode = lambda e: '\n'.join(json.dumps(v) for v in e)
        self.assertEqual(runner.parse(encode(events))['usage']['output_tokens'], 5)
        for invalid in [events[:-1], [{'type': 'item.completed', 'item': {'type': 'collab_tool_call'}}]+events,
                        [{'type': 'item.completed', 'item': {'type': 'command_execution', 'command': 'codex exec another'}}]+events]:
            with self.assertRaises(ValueError): runner.parse(encode(invalid))

    def test_no_submission_symlink(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d); (p/'code.py').write_text('print(1)\n'); (p/'submission.py').symlink_to(p/'code.py')
            with self.assertRaises(OSError): runner.submission(p, p/'frozen.py')

    @unittest.skipUnless(os.environ.get('DYNAMIC_SOLO_DOCKER') == '1', 'explicit Docker preflight')
    def test_actual_cli_repair_sandbox_and_external_bytes(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)/'run'; report = runner.run(p, fake=True)
            self.assertEqual(report['status'], 'completed', report)
            cap = report['actor']['capability']
            self.assertTrue(cap['broken_detected'] and cap['repair_passed'] and cap['shell_network_denied'])
            self.assertTrue(all(s['shell_available'] and not s['subagent_available'] for s in cap['surfaces']))
            self.assertTrue(report['owned_cleanup_confirmed'] and report['credential_copy_removed'])
            public = json.loads((p/'developer/work/repaired-report.json').read_text())
            final = report['assessments']['submission']['result']
            self.assertEqual(public['cases'][0]['result'], final['cases'][0]['result'])
            self.assertEqual(report['submission_sha256'], runner.digest((p/'assessment-submission/policy.py').read_bytes()))
            self.assertEqual(json.loads((p/'seal.json').read_text())['source_sha256'], runner.identity())

    @unittest.skipUnless(os.environ.get('DYNAMIC_SOLO_DOCKER') == '1', 'explicit Docker preflight')
    def test_actor_timeout_cleanup(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d); runner.projection.prepare(p/'public')
            report = runner.actor(p/'actor', p/'public', fake=True, seconds=.3)
            self.assertEqual(report['status'], 'stopped')
            self.assertTrue(report['removed'])
            self.assertIsNone(report['usage'])


if __name__ == '__main__': unittest.main()
