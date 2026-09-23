import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

HERE = Path(__file__).resolve().parents[1]/'experiments/development-harness/scheduling/ready_runtime_v1'


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module); return module


def transport():
    previous = {n: sys.modules.get(n) for n in ('runtime', 'recovery')}
    try:
        for n in previous: sys.modules[n] = load('ready_test_'+n, HERE/(n+'.py'))
        return load('ready_test_transport', HERE/'transport.py')
    finally:
        for n, old in previous.items():
            if old is None: sys.modules.pop(n, None)
            else: sys.modules[n] = old


def evidence(default, suffix):
    base = os.environ.get('READY_RUNTIME_EVIDENCE')
    path = Path(base+'-'+suffix) if base else default/suffix
    path.mkdir(parents=True, mode=0o700, exist_ok=False)
    return path


class ReadyRuntimeTests(unittest.TestCase):
    def test_physics_and_host_execution_boundary(self):
        self.assertEqual((HERE/'runtime.py').read_bytes(), (HERE.parent/'timing_diagnostic_v1/runtime.py').read_bytes())
        self.assertEqual((HERE/'recovery.py').read_bytes(), (HERE.parent/'termination_pair_v1/recovery.py').read_bytes())
        module = transport()
        with self.assertRaisesRegex(module.CapacityError, 'dedicated actor'):
            module.LocalPolicy(HERE.parent/'continuation_pair_v1/initial-policy.txt').__enter__()

    @unittest.skipUnless(os.environ.get('READY_RUNTIME_DOCKER') == '1', 'explicit Docker startup/total bounds')
    def test_readiness_and_total_scenario_caps(self):
        module = transport(); support = load('ready_bound_support', HERE/'support.py')
        with tempfile.TemporaryDirectory() as d:
            path = evidence(Path(d), 'bounds'); source = support.identity()
            # A private evaluator-owned launcher fixture, never candidate code
            # or a change to the production launcher on disk.
            fixture = path/'fixture'; fixture.mkdir()
            launcher = (HERE/'launcher.py').read_text().replace('    os.write(2, READY)',
                '    import time\n    time.sleep(6)\n    os.write(2, READY)')
            (fixture/'launcher.py').write_text(launcher); (fixture/'launcher.py').chmod(0o444)
            module.HERE = fixture
            candidate = path/'unused.py'; candidate.write_text("raise AssertionError('candidate must never execute')\n")
            support.save(path/'plan.json', {'source_sha256':source,'launcher_fixture_sha256':support.sha(fixture/'launcher.py'),'live_provider_calls':0})
            rows = []
            for scenario, readiness, reason in ((90,2,'runtime_readiness_deadline'),(5,20,'scenario_deadline')):
                policy = module.Policy(candidate,seconds=scenario,readiness_seconds=readiness)
                with self.assertRaisesRegex(TimeoutError, reason): policy.__enter__()
                self.assertFalse(policy.record['runtime_ready']); self.assertFalse(policy.activated)
                self.assertTrue(policy.record['removed'], policy.record); rows.append(policy.record)
            self.assertEqual(support.identity(),source)
            support.save(path/'result.json',{'status':'passed','execution':rows,'live_provider_calls':0})

    @unittest.skipUnless(os.environ.get('READY_RUNTIME_DOCKER') == '1', 'explicit Docker ready-runtime validation')
    def test_activation_original_source_raw_stdin_and_initialization_budget(self):
        module = transport(); support = load('ready_test_support', HERE/'support.py')
        with tempfile.TemporaryDirectory() as d:
            path = evidence(Path(d), 'activation'); source = support.identity()
            support.save(path/'plan.json', {'source_sha256': source, 'live_provider_calls': 0})
            code = '''import hashlib,json,os,sys
from pathlib import Path
Path('/work/entered.json').write_text(json.dumps({'argv':sys.argv,'file':__file__,'sha':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}))
pending=b''
while True:
 data=os.read(0,4096)
 if not data:break
 pending+=data
 while b'\\n' in pending:
  line,pending=pending.split(b'\\n',1);r=json.loads(line)
  print(json.dumps({'request_id':r['request_id'],'assignments':[]}),flush=True)
'''
            candidate = path/'fixed.py'; candidate.write_text(code); candidate.chmod(0o444)
            rows = []
            with module.Policy(candidate) as policy:
                self.assertTrue(policy.record['runtime_ready'])
                check = subprocess.run(['docker','exec',policy.name,'test','!','-e','/work/entered.json'], capture_output=True, timeout=15)
                self.assertEqual(check.returncode, 0, 'candidate executed before activation')
                self.assertEqual(policy.choose({'example': 1}), [])
                self.assertEqual(policy.choose({'example': 2}), [])
                raw = subprocess.run(['docker','exec',policy.name,'cat','/work/entered.json'], capture_output=True, text=True, check=True, timeout=15)
                identity = json.loads(raw.stdout)
                self.assertEqual(identity, {'argv':['/policy.py'],'file':'/policy.py','sha':hashlib.sha256(code.encode()).hexdigest()})
                self.assertEqual(policy.record['requests'], 2)
            rows.append(policy.record); self.assertTrue(policy.record['removed'])
            echo = "import sys,json\nfor line in sys.stdin:\n r=json.loads(line);print(json.dumps({'request_id':r['request_id'],'assignments':[]}),flush=True)\n"
            for name, prefix in (
                ('initialization', 'import time\ntime.sleep(6)\n'),
                ('forged_readiness', "import sys,time\nsys.stderr.write('EVALUATOR_RUNTIME_READY_V1\\n');sys.stderr.flush();time.sleep(6)\n")):
                candidate = path/(name+'.py'); candidate.write_text(prefix+echo); candidate.chmod(0o444)
                with module.Policy(candidate) as policy:
                    self.assertTrue(policy.record['runtime_ready'])
                    with self.assertRaisesRegex(TimeoutError, 'response_deadline'): policy.choose({})
                self.assertTrue(policy.record['removed']); rows.append(policy.record)
            self.assertEqual(support.identity(), source)
            support.save(path/'result.json', {'status':'passed','execution':rows,'live_provider_calls':0})

    @unittest.skipUnless(os.environ.get('READY_RUNTIME_DOCKER') == '1', 'explicit public/independent Docker parity')
    def test_public_and_independent_smoke_and_invalid_output(self):
        support = load('ready_parity_support', HERE/'support.py')
        assess = load('ready_parity_assess', HERE/'assessment.py')
        with tempfile.TemporaryDirectory() as d:
            path = evidence(Path(d), 'parity'); source = support.identity()
            support.save(path/'plan.json', {'source_sha256':source,'live_provider_calls':0})
            seal = support.prepare_public(path/'public', smoke=True); results = {}
            for name in ('fifo', 'initial'):
                external = assess.evaluate(path/'public'/(name+'.py'),path/'public/development.json',path/('external-'+name),seconds=120)
                self.assertEqual(external['status'],'measured',external)
                public = support.public_execution(path/'public',path/('public-'+name),name)
                self.assertEqual(public['status'],'measured',public);self.assertTrue(public['removed'])
                records = support.read(path/('public-'+name)/'public-result.json')
                self.assertEqual([r['result'] for r in external['evaluation']['cases']], [r['result'] for r in records['cases']])
                self.assertTrue(all(r['execution']['runtime_ready'] for r in external['evaluation']['cases']))
                results[name] = {'external':external['status'],'public':public}
            invalid = path/'invalid.py'; invalid.write_text("import sys,json\nfor line in sys.stdin:\n r=json.loads(line);print(json.dumps({'request_id':r['request_id'],'assignments':None}),flush=True)\n")
            result = assess.evaluate(invalid,path/'public/probe.json',path/'invalid-assessment',seconds=120)
            self.assertEqual(result['status'],'invalid-policy',result)
            self.assertEqual(support.identity(),source)
            self.assertEqual(seal,{p.name:support.sha(p) for p in (path/'public').iterdir()})
            support.save(path/'result.json',{'status':'passed','results':results,'invalid':result['status'],'live_provider_calls':0})


if __name__ == '__main__': unittest.main()
