import copy
import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest

HERE = Path(__file__).resolve().parents[1]/'experiments/development-harness/scheduling/dynamic_v1'
sys.path.insert(0, str(HERE))
from runtime import Invalid, simulate, validate
from workloads import suite


def fixture():
    return {'id': 'fixture', 'horizon': 12, 'heartbeat': 2, 'memory': 4, 'cold_start': 0,
            'workers': [{'id': 'w', 'kind': 'cpu', 'memory': 4}], 'outages': [],
            'jobs': [{'id': 'a', 'release': 0, 'deadline': 10, 'weight': 4, 'deps': [], 'estimate': {'cpu': 2},
                      'actual': {'cpu': 4}, 'memory': 3, 'cache': 'x'}]}


def first(s):
    return [{'job_id': s['ready'][0]['id'], 'worker_id': s['idle_workers'][0]['id']}] if s['ready'] and s['idle_workers'] else []


class DynamicTests(unittest.TestCase):
    def test_completion_clock_and_capacity_accounting(self):
        result = simulate(fixture(), first)
        self.assertEqual((result['on_time_value'], result['busy_worker_ticks'], result['completion_times']), (4, 4, {'a': 4}))

    def test_interruption_restart_and_boundary_order(self):
        s = fixture(); s['outages'] = [{'worker_id': 'w', 'start': 3, 'end': 5}]
        r = simulate(s, first)
        self.assertEqual((r['completion_times'], r['busy_worker_ticks'], r['interrupted_worker_ticks'], r['attempts']), ({'a': 9}, 7, 3, 2))
        s['outages'][0]['start'] = 4
        r = simulate(s, first)
        self.assertEqual((r['completion_times'], r['interrupted_worker_ticks']), ({'a': 4}, 0))

    def test_no_future_or_actual_leak_and_mutation_isolated(self):
        s = fixture(); late = copy.deepcopy(s['jobs'][0]); late.update(id='b', release=6, deadline=12); s['jobs'].append(late)
        observations = []
        def inspect(state):
            observations.append(copy.deepcopy(state))
            action = first(state)
            state['workers'][0]['online'] = False
            state['completed']['a'] = -10
            state['jobs'][0]['estimate']['cpu'] = 999
            return action
        r = simulate(s, inspect)
        self.assertEqual(r['completion_times'], {'a': 4, 'b': 10})
        self.assertEqual({j['id'] for j in observations[0]['jobs']}, {'a'})
        for state in observations:
            self.assertNotIn('outages', state)
            self.assertTrue(all('actual' not in j for j in state['jobs']))
            self.assertTrue(all('finish' not in j for j in state['running']))

    def test_waiting_horizon_and_unfinished_not_zero(self):
        s = fixture(); s['jobs'][0]['actual']['cpu'] = 20
        r = simulate(s, first)
        self.assertEqual((r['on_time_value'], r['unfinished_value'], r['unfinished_worker_ticks'], r['deadline_deficit']), (0, 4, 12, 8))
        r = simulate(fixture(), lambda _: [])
        self.assertEqual((r['unfinished_value'], r['busy_worker_ticks'], r['response_p95_completed']), (4, 0, None))
        s['jobs'][0]['actual']['cpu'] = 12; s['jobs'][0]['deadline'] = 12
        self.assertEqual(simulate(s, first)['on_time_value'], 4)

    def test_combined_memory_and_unknown_assignment_rejected(self):
        s = fixture(); s['workers'].append({'id': 'v', 'kind': 'cpu', 'memory': 4})
        j = copy.deepcopy(s['jobs'][0]); j['id'] = 'b'; s['jobs'].append(j)
        with self.assertRaisesRegex(Invalid, 'shared memory'):
            simulate(s, lambda _: [{'job_id': 'a', 'worker_id': 'w'}, {'job_id': 'b', 'worker_id': 'v'}])
        with self.assertRaises(Invalid):
            simulate(fixture(), lambda _: [{'job_id': 'future', 'worker_id': 'w'}])

    def test_dependencies_and_cache(self):
        s = fixture(); s['cold_start'] = 2
        j = copy.deepcopy(s['jobs'][0]); j.update(id='b', deps=['a'], deadline=12); s['jobs'].append(j)
        r = simulate(s, first)
        self.assertEqual(r['completion_times'], {'a': 6, 'b': 10})
        self.assertEqual(r['busy_worker_ticks'], 10)
        s['jobs'][0]['deps'] = ['b']
        with self.assertRaises(Invalid): validate(s)

    def test_workload_population_and_disjointness(self):
        a, b = suite(), suite('qualification')
        self.assertEqual(len(a), 24)
        self.assertEqual(a, suite())
        self.assertFalse({s['id'] for s in a} & {s['id'] for s in b})
        for s in a+b: validate(s)
        self.assertEqual({len(s['jobs']) for s in a}, {96, 288, 768})
        self.assertTrue(any(s['outages'] for s in a))

    def test_value_propagation_protects_dependent_service(self):
        spec = importlib.util.spec_from_file_location('dynamic_reference', HERE/'policies/reference.py')
        ref = importlib.util.module_from_spec(spec); spec.loader.exec_module(ref)
        s = fixture(); s['horizon'] = 12
        low = s['jobs'][0]; low.update(weight=1, deadline=12)
        low['actual']['cpu'] = low['estimate']['cpu'] = 8
        prerequisite = copy.deepcopy(low)
        prerequisite.update(id='b', weight=0, deadline=5)
        prerequisite['actual']['cpu'] = prerequisite['estimate']['cpu'] = 2
        high = copy.deepcopy(prerequisite); high.update(id='c', weight=16, deps=['b'])
        s['jobs'] += [prerequisite, high]
        fifo = simulate(s, lambda state: ref.choose(state, 'fifo'))
        density = simulate(s, lambda state: ref.choose(state, 'density'))
        self.assertEqual(fifo['on_time_value'], 1)
        self.assertEqual(density['on_time_value'], 17)
        self.assertEqual(density['completion_times']['c'], 4)

    def test_noop_or_missing_service_cannot_claim_quality(self):
        s = fixture()
        with self.assertRaises(Invalid): simulate(s, lambda _: {'on_time_value': 1000})
        bad = copy.deepcopy(s); bad['jobs'][0]['release'] = True
        with self.assertRaises(Invalid): validate(bad)
        bad = copy.deepcopy(s); bad['outages'] = [{'worker_id': 'w', 'start': 1, 'end': 6}, {'worker_id': 'w', 'start': 5, 'end': 7}]
        with self.assertRaises(Invalid): validate(bad)

    @unittest.skipUnless(os.environ.get('SCHEDULING_DYNAMIC_DOCKER') == '1', 'explicit Docker calibration')
    def test_external_reference_and_illegal_policy(self):
        from evaluate import evaluate
        with tempfile.TemporaryDirectory() as d:
            p = Path(d); policy = p/'source.py'
            policy.write_text((HERE/'policies/reference.py').read_text())
            r = evaluate(policy, [fixture()], p/'valid')
            self.assertEqual(r['cases'][0]['result']['on_time_value'], 4)
            self.assertTrue(r['all_containers_removed'])
            policy.write_text('import json,sys\nfor line in sys.stdin:\n r=json.loads(line); print(json.dumps({"request_id":r["request_id"],"assignments":[{"job_id":"unknown","worker_id":"w"}]}),flush=True)\n')
            r = evaluate(policy, [fixture()], p/'invalid')
            self.assertEqual(r['cases'][0]['status'], 'invalid-policy')
            self.assertTrue(r['all_containers_removed'])


if __name__ == '__main__': unittest.main()
