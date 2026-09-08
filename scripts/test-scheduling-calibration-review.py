import copy
import importlib.util
import json
import hashlib
import shutil
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch, MagicMock

HERE = Path(__file__).resolve().parents[1]/'experiments/development-harness/scheduling/dynamic_v1'
sys.path.insert(0, str(HERE))
import calibrate_v2 as controller
from audit_bounds import bounds


def fixture():
    return {'id': 'tiny', 'horizon': 10, 'heartbeat': 2, 'memory': 4, 'cold_start': 0,
            'outages': [], 'workers': [{'id': 'w', 'kind': 'cpu', 'memory': 4}],
            'jobs': [{'id': 'a', 'release': 0, 'deadline': 5, 'weight': 16, 'deps': [], 'estimate': {'cpu': 2},
                      'actual': {'cpu': 8}, 'memory': 3, 'cache': 'x'}]}


class ReviewTests(unittest.TestCase):
    def test_start_failure_is_final_and_not_cleanup_success(self):
        with tempfile.TemporaryDirectory() as d, patch.object(controller.subprocess, 'Popen', side_effect=OSError('launch failed')):
            out = Path(d)/'run'; r = controller.run(out, 24)
            self.assertEqual(r['status'], 'withhold')
            self.assertEqual(len(r['attempts']), 1)
            self.assertFalse(r['all_started_assessments_cleanup_confirmed'])
            self.assertEqual(json.loads((out/'report.json').read_text())['status'], 'withhold')
            self.assertTrue((out/'fifo.start.json').exists())

    def test_timeout_stops_next_mode_and_marks_unknown_cleanup(self):
        proc = MagicMock(); proc.poll.return_value = None
        proc.communicate.side_effect = [subprocess.TimeoutExpired('evaluator', 300), (b'', b'')]
        with tempfile.TemporaryDirectory() as d, patch.object(controller.subprocess, 'Popen', return_value=proc) as launch:
            r = controller.run(Path(d)/'run', 24)
        self.assertEqual(launch.call_count, 1)
        proc.terminate.assert_called_once()
        self.assertEqual(r['attempts'][0]['cleanup'], 'unknown')
        self.assertFalse(r['all_started_assessments_cleanup_confirmed'])

    def test_forced_controller_kill_is_not_container_cleanup(self):
        proc = MagicMock(); proc.poll.return_value = None
        proc.communicate.side_effect = [subprocess.TimeoutExpired('e', 300), subprocess.TimeoutExpired('e', 30), (b'', b'')]
        with tempfile.TemporaryDirectory() as d, patch.object(controller.subprocess, 'Popen', return_value=proc):
            r = controller.run(Path(d)/'run', 24)
        proc.kill.assert_called_once(); self.assertEqual(r['status'], 'withhold')
        self.assertFalse(r['all_started_assessments_cleanup_confirmed'])

    def test_launch_reads_copied_source(self):
        with tempfile.TemporaryDirectory() as d:
            out = Path(d)/'run'
            def launch(args, **kwargs):
                self.assertEqual(Path(args[1]), out/'source/evaluate.py')
                self.assertEqual((out/'source/runtime.py').read_bytes(), (HERE/'runtime.py').read_bytes())
                raise OSError('bounded probe')
            with patch.object(controller.subprocess, 'Popen', side_effect=launch): controller.run(out, 24)

    def test_later_modes_use_snapshot_despite_checkout_edit(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d); checkout = root/'checkout'; checkout.mkdir()
            for name in controller.FILES:
                target = checkout/name; target.parent.mkdir(exist_ok=True)
                shutil.copyfile(HERE/name, target)
            original = (checkout/'policies/reference.py').read_bytes()
            out = root/'run'
            def launch(args, **kwargs):
                candidate = Path(args[args.index('--candidate')+1])
                self.assertTrue(candidate.read_bytes().endswith(original))
                (checkout/'policies/reference.py').write_text('raise RuntimeError("changed checkout")\n')
                folder = Path(args[args.index('--output')+1]); folder.mkdir()
                cases = json.loads(Path(args[args.index('--scenarios')+1]).read_text())
                plan = json.loads((out/'plan.json').read_text())
                seal = {'source_sha256': {n: plan['source_sha256'][n] for n in ('runtime.py', 'transport.py', 'evaluate.py', 'TASK.md')},
                        'candidate_sha256': hashlib.sha256(candidate.read_bytes()).hexdigest(),
                        'scenario_sha256': hashlib.sha256(json.dumps(cases, sort_keys=True, allow_nan=False).encode()).hexdigest()}
                (folder/'seal.json').write_text(json.dumps(seal))
                (folder/'result.json').write_text(json.dumps({'status': 'completed', 'all_containers_removed': True,
                    'cases': [{'id': c['id'], 'status': 'measured', 'execution': {'removed': True}} for c in cases]}))
                proc = MagicMock(); proc.poll.return_value = 0; proc.returncode = 0; proc.communicate.return_value = (b'', b'')
                return proc
            with patch.object(controller, 'HERE', checkout), patch.object(controller.subprocess, 'Popen', side_effect=launch):
                r = controller.run(out, 24)
            self.assertEqual(r['status'], 'completed')
            self.assertEqual(len(r['attempts']), 4)

    def test_empty_duplicate_or_wrong_seal_cannot_pass(self):
        cases = [{'id': 'a'}, {'id': 'b'}]
        raw = {'status': 'completed', 'all_containers_removed': True, 'cases': []}
        with self.assertRaises(ValueError): controller.assess(raw, {}, cases, '', {})
        row = {'id': 'a', 'status': 'measured', 'execution': {'removed': True}}
        raw['cases'] = [row, row]
        with self.assertRaises(ValueError): controller.assess(raw, {}, cases, '', {})
        raw['cases'] = [row, {**row, 'id': 'b'}]
        hashes = {n: 'fixed' for n in ('runtime.py', 'transport.py', 'evaluate.py', 'TASK.md')}
        with self.assertRaises(ValueError): controller.assess(raw, {}, cases, '', hashes)

    def test_bounds_reject_impossible_without_certifying_possible(self):
        s = fixture(); r = bounds(s)
        self.assertEqual(r['deadline_impossible_jobs'], ['a'])
        s['jobs'][0]['deadline'] = 10
        j = copy.deepcopy(s['jobs'][0]); j['id'] = 'b'; s['jobs'].append(j)
        r = bounds(s)
        self.assertFalse(r['deadline_impossible_jobs'])
        self.assertTrue(r['groups']['critical']['all_completion_impossible_by_capacity'])
        self.assertFalse(r['feasibility_proven'])

    def test_shared_dependencies_count_once_and_outage_reduces_supply(self):
        s = fixture(); s['jobs'][0].update(weight=0, deadline=10)
        s['jobs'][0]['actual']['cpu'] = 2
        for name in ['b', 'c']:
            j = copy.deepcopy(s['jobs'][0]); j.update(id=name, weight=16, deps=['a']); s['jobs'].append(j)
        s['outages'] = [{'worker_id': 'w', 'start': 0, 'end': 5}]
        r = bounds(s)['groups']['critical']
        self.assertEqual(r['required_worker_ticks_lower_bound'], 6)
        self.assertEqual(r['worker_ticks_available'], 5)


if __name__ == '__main__': unittest.main()
