import copy
import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile
import subprocess
import time
import unittest

HERE = Path(__file__).resolve().parents[1] / 'experiments/development-harness/scheduling/v1'
sys.path.insert(0, str(HERE))
# Avoid cross-suite modules with generic names.
def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec); spec.loader.exec_module(value)
    return value
runtime = module('scheduling_runtime', HERE/'runtime.py')
sys.modules['runtime'] = runtime
transport = module('scheduling_transport', HERE/'transport.py'); sys.modules['transport'] = transport
evaluator = module('scheduling_evaluate', HERE/'evaluate.py')
cases = module('scheduling_cases', HERE/'calibration_cases.py').cases


def fifo(state):
    result = []; free = list(state['idle_workers'])
    for job in state['ready']:
        worker = next((w for w in free if w['kind'] in job['compatible']), None)
        if worker:
            result.append({'job_id': job['id'], 'worker_id': worker['id']}); free.remove(worker)
    return result


class RuntimeTests(unittest.TestCase):
    def test_meaningful_policy_difference(self):
        scenario = cases()[0]
        def scarcity(state):
            state['ready'].sort(key=lambda j: len(j['compatible']))
            return fifo(state)
        self.assertEqual(runtime.simulate(scenario, fifo)['completion_ticks'], 20)
        self.assertEqual(runtime.simulate(scenario, scarcity)['completion_ticks'], 10)

    def test_state_mutation_cannot_change_clock_or_leak_failure(self):
        scenario = cases()[1]; before = copy.deepcopy(scenario)
        def malicious(state):
            self.assertNotIn('failing_jobs', state)
            for job in state['jobs']:
                for kind in job['duration']:
                    job['duration'][kind] = 0
            state['now'] = -100
            return fifo(state)
        result = runtime.simulate(scenario, malicious)
        self.assertEqual(scenario, before)
        self.assertEqual(result['blocker_ticks'], 2)
        self.assertEqual(result['busy_worker_ticks'], 4)
        self.assertEqual(result['committed_worker_ticks'], 12)

    def test_exact_events_and_cache(self):
        result = runtime.simulate(cases()[2], fifo)
        self.assertEqual(result['completion_ticks'], 5)
        self.assertEqual(result['busy_worker_ticks'], 5)

    def test_invalid_actions_are_not_scores(self):
        bad = [{'completion_time': 0}, [{'job_id':'flex','worker_id':'gpu'}]*2,
               [{'job_id':'cpu-only','worker_id':'gpu'}],
               [{'job_id':'flex','worker_id':'missing'}], [],
               [{'job_id':'flex','worker_id':'cpu','duration':0}]]
        for action in bad:
            with self.subTest(action=action), self.assertRaises(runtime.Invalid):
                runtime.simulate(cases()[0], lambda state: action)

    def test_schema_cycle_and_fractional_values_rejected(self):
        for mutation in ('cycle','fraction','bool','unknown','nan'):
            case = cases()[0]
            if mutation=='cycle':case['jobs'][0]['deps']=['flex']
            if mutation=='fraction':case['jobs'][0]['duration']['cpu']=.1
            if mutation=='bool':case['cold_start']=True
            if mutation=='unknown':case['failing_jobs']=['alien']
            if mutation=='nan':case['jobs'][0]['failure_probability']=float('nan')
            with self.subTest(mutation=mutation), self.assertRaises(runtime.Invalid):runtime.validate(case)
        for data in ['{"a":1,"a":2}', '[NaN]']:
            with self.assertRaises(runtime.Invalid):runtime.decode(data)


@unittest.skipUnless(os.environ.get('SCHEDULING_EVALUATOR_DOCKER'), 'set SCHEDULING_EVALUATOR_DOCKER=1')
class DockerTests(unittest.TestCase):
    def test_controller_sigterm_recovers_active_container(self):
        with tempfile.TemporaryDirectory() as raw:
            root=Path(raw); candidate=root/'slow.py';candidate.write_text('import sys,time;sys.stdin.readline();time.sleep(60)')
            data=root/'cases.json';data.write_text(json.dumps([cases()[0]]))
            process=subprocess.Popen([sys.executable,str(HERE/'evaluate.py'),'--candidate',str(candidate),
                '--scenarios',str(data),'--output',str(root/'result')],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
            try:
                limit=time.monotonic()+10
                while time.monotonic()<limit:
                    names=subprocess.check_output(['docker','ps','--filter','name=scheduling-policy-','--format','{{.Names}}'],text=True,timeout=2)
                    if names.strip():break
                    time.sleep(.05)
                else:self.fail('candidate container did not start')
                process.terminate()
                stdout,stderr=process.communicate(timeout=20)
                self.assertEqual(process.returncode,0,(stdout,stderr))
                result=json.loads((root/'result/result.json').read_text())
                self.assertEqual(result['status'],'withhold')
                self.assertTrue(result['all_containers_removed'])
                self.assertEqual(result['cases'][0]['failure'],'StopRequested')
            finally:
                if process.poll() is None:
                    process.kill();process.communicate(timeout=5)

    def test_dense_legal_dag_is_evaluator_capacity_not_bad_policy(self):
        case=cases()[2]
        prototype=case['jobs'][0]
        ids=[str(i).zfill(64) for i in range(256)]
        case['jobs']=[dict(prototype,id=name,deps=ids[:i]) for i,name in enumerate(ids)]
        runtime.validate(case)
        with tempfile.TemporaryDirectory() as raw:
            result=evaluator.evaluate(HERE/'calibration/fifo.py',[case],Path(raw)/'result')
            self.assertEqual(result['cases'][0]['status'],'unmeasured',result)
            self.assertEqual(result['cases'][0]['failure'],'CapacityError')
            self.assertTrue(result['all_containers_removed'])

    def test_valid_policies_and_fresh_output(self):
        with tempfile.TemporaryDirectory() as raw:
            for name, expected in [('fifo',20),('scarcity',10)]:
                output=Path(raw)/name
                result=evaluator.evaluate(HERE/'calibration'/f'{name}.py',cases(),output)
                self.assertEqual(result['status'],'completed',result)
                self.assertTrue(result['all_containers_removed'])
                self.assertEqual(result['cases'][0]['result']['completion_ticks'],expected)
                self.assertEqual(result['cases'][1]['result']['busy_worker_ticks'],4)
                with self.assertRaises(FileExistsError):evaluator.evaluate(HERE/'calibration'/f'{name}.py',cases(),output)

    def test_reference_hidden_and_input_mutation_is_inert(self):
        prefix="""from pathlib import Path
assert not any(Path(p).exists() for p in ['/var/run/docker.sock','/task','/codex/auth.json','/usr/local/bin/manage-agent-project','/usr/local/share/agent-project'])
"""
        code=(HERE/'calibration/fifo.py').read_text().replace("state = request['state']", "state = request['state']\n    assert 'failing_jobs' not in state\n    for j in state['jobs']:\n        for k in j['duration']: j['duration'][k] = 0")
        with tempfile.TemporaryDirectory() as raw:
            p=Path(raw)/'policy.py';p.write_text(prefix+code)
            result=evaluator.evaluate(p,[cases()[1]],Path(raw)/'result')
            self.assertEqual(result['status'],'completed',result)
            self.assertEqual(result['cases'][0]['result']['blocker_ticks'],2)
            self.assertEqual(result['cases'][0]['result']['busy_worker_ticks'],4)

    def test_spoof_duplicate_id_flood_and_timeout(self):
        programs={
          'spoof': 'print(\'{"status":"completed","completion_ticks":0}\',flush=True)',
          'duplicate': 'print(\'{"request_id":0,"request_id":0,"assignments":[]}\',flush=True)',
          'identity': 'print(\'{"request_id":99,"assignments":[]}\',flush=True)',
          'flood': 'import sys;sys.stderr.write("x"*300000);sys.stderr.flush()',
          'timeout': 'import time;time.sleep(20)',
        }
        with tempfile.TemporaryDirectory() as raw:
            for name,code in programs.items():
                with self.subTest(name=name):
                    p=Path(raw)/f'{name}.py';p.write_text(code)
                    result=evaluator.evaluate(p,[cases()[0]],Path(raw)/name)
                    self.assertEqual(result['status'],'withhold',result)
                    self.assertTrue(result['all_containers_removed'],result)
                    self.assertNotIn('result',result['cases'][0])


if __name__ == '__main__':unittest.main()
