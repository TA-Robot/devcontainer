import importlib.util
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import time
import unittest
from unittest import mock

HERE=Path(__file__).resolve().parents[1]/'experiments/development-harness/scheduling/solo_v1'
sys.path.insert(0,str(HERE))
import runner


class UnitTests(unittest.TestCase):
    def test_unknown_usage_and_extra_model_calls_are_not_solo_success(self):
        rows=[{'type':'item.completed','item':{'type':'agent_message','text':'done'}},
              {'type':'turn.completed','usage':{'input_tokens':10,'cached_input_tokens':0,'output_tokens':2}}]
        encode=lambda data:'\n'.join(json.dumps(r) for r in data)
        self.assertEqual(runner.parse(encode(rows))['usage']['output_tokens'],2)
        for bad in [rows[:-1],rows+[{'type':'turn.started'}],
                    [{'type':'item.completed','item':{'type':'command_execution','command':'codex exec other-task'}}]+rows,
                    [{'type':'item.completed','item':{'type':'collab_tool_call'}}]+rows]:
            with self.assertRaises(ValueError):runner.parse(encode(bad))
        rows[-1]['usage']=None
        with self.assertRaises(ValueError):runner.parse(encode(rows))

    def test_projection_has_exact_public_allowlist_and_no_reference(self):
        with tempfile.TemporaryDirectory() as raw:
            root=Path(raw)/'public';manifest=runner.projection.prepare(root)
            self.assertEqual(set(manifest),{'TASK.md','WORKLOAD.md','runtime.py','transport.py','public_check.py','fifo.py','ACTOR_ONLY','development.json','targets.json'})
            cases=json.loads((root/'development.json').read_text())
            self.assertTrue(all(c['id'].startswith('development-') for c in cases))
            self.assertEqual(json.loads((root/'targets.json').read_text()),json.loads((runner.WORKLOAD/'qualification.json').read_text())['targets']['development'])
            with self.assertRaises(FileExistsError):runner.projection.prepare(root)

    def test_submission_refuses_symlinks_and_preserves_exact_bytes(self):
        with tempfile.TemporaryDirectory() as raw:
            root=Path(raw);work=root/'work';work.mkdir();code=b'# exact \xe6\x97\xa5\xe6\x9c\xac\xe8\xaa\x9e\nprint(1)\n'
            (work/'submission.py').write_bytes(code)
            self.assertEqual(runner.submission(work,root/'frozen.py'),runner.digest(code))
            self.assertEqual((root/'frozen.py').read_bytes(),code)
            (work/'submission.py').unlink();(work/'submission.py').symlink_to(root/'frozen.py')
            with self.assertRaises(OSError):runner.submission(work,root/'other.py')


@unittest.skipUnless(os.environ.get('SCHEDULING_SOLO_DOCKER'),'set SCHEDULING_SOLO_DOCKER=1')
class DockerTests(unittest.TestCase):
    def test_two_fresh_runs_retain_nonattainment_and_all_cleanup(self):
        with tempfile.TemporaryDirectory() as raw:
            result=runner.run(Path(raw)/'pair',fake=True)
            self.assertEqual(result['status'],'completed',result)
            self.assertEqual([r['status'] for r in result['runs']],['not-attained','not-attained'])
            self.assertTrue(result['all_recorded_containers_removed'])
            self.assertTrue(result['credential_copy_removed'])
            self.assertFalse(result['confirmation_executed'])
            self.assertEqual(result['execution'],'provider-free')

    def test_actual_cli_edit_public_repair_network_and_independent_evaluation(self):
        with tempfile.TemporaryDirectory() as raw:
            root=Path(raw);runner.projection.prepare(root/'public')
            record=runner.actor(root/'actor',root/'public',fake=True,seconds=120)
            self.assertEqual(record['status'],'completed',record)
            cap=record['capability']
            self.assertEqual(cap['requests'],4)
            self.assertTrue(cap['broken_detected'],cap)
            self.assertTrue(cap['repair_passed'],cap)
            self.assertTrue(cap['shell_network_denied'],cap)
            self.assertTrue(all(s['shell_available'] and not s['subagent_available'] for s in cap['surfaces']))
            self.assertTrue(record['removed'])
            public=json.loads((root/'actor/work/repaired-report.json').read_text())
            sha=runner.submission(root/'actor/work',root/'selected.py')
            final=runner.evaluate(root/'selected.py',runner.suite('development'),root/'external')
            self.assertEqual(runner.aggregate(final),public['families'])
            self.assertEqual(json.loads((root/'external/seal.json').read_text())['candidate_sha256'],sha)
            self.assertTrue(final['all_containers_removed'])

    def test_actor_deadline_removes_container(self):
        with tempfile.TemporaryDirectory() as raw:
            root=Path(raw);runner.projection.prepare(root/'public')
            record=runner.actor(root/'actor',root/'public',fake=True,seconds=.3)
            self.assertEqual(record['status'],'stopped')
            self.assertTrue(record['removed'],record)
            self.assertIsNone(record['usage'])


if __name__=='__main__':unittest.main()
