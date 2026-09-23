import importlib.util
from pathlib import Path
import sys
import unittest
import tempfile
from unittest import mock

HERE=Path(__file__).resolve().parents[1]/'experiments/development-harness/scheduling/workloads_v1'
sys.path.insert(0,str(HERE));sys.path.insert(0,str(HERE.parent/'v1'))
import workloads
import runtime
import qualify


class WorkloadTests(unittest.TestCase):
    def test_full_qualification_keeps_input_and_report_paths_distinct(self):
        def synthetic(candidate, cases, output):
            output.mkdir()
            rows=[]
            for case in cases:
                success=not case['failing_jobs']
                rows.append({'id':case['id'],'result':{'status':'completed' if success else 'blocked',
                    'completion_ticks':10 if success else None,'blocker_ticks':None if success else 4,'busy_worker_ticks':20}})
            return {'status':'completed','all_containers_removed':True,'cases':rows}
        with tempfile.TemporaryDirectory() as raw, mock.patch.object(qualify,'evaluate',side_effect=synthetic):
            path=Path(raw)/'qualification'
            report=qualify.run(path)
            self.assertTrue((path/'qualification.json').exists())
            self.assertTrue((path/'report.json').exists())
            self.assertFalse(report['confirmation_executed'])

    def test_valid_reproducible_populations_with_unrevealed_failure(self):
        signatures=set()
        for split in workloads.SPLITS:
            cases=workloads.suite(split)
            self.assertEqual(cases,workloads.suite(split))
            self.assertEqual(len(cases),24)
            self.assertEqual(len({s['id'] for s in cases}),24)
            for index in range(0,len(cases),2):
                left,right=cases[index:index+2]
                runtime.validate(left);runtime.validate(right)
                self.assertEqual({k:v for k,v in left.items() if k not in ('id','failing_jobs')},
                                 {k:v for k,v in right.items() if k not in ('id','failing_jobs')})
                signature=repr(left['jobs'])
                self.assertNotIn(signature,signatures);signatures.add(signature)
            counts={family:len([s for s in cases if '-'+family+'-' in s['id']]) for family in workloads.FAMILIES}
            self.assertEqual(set(counts.values()),{6})
        with self.assertRaises(ValueError):workloads.suite('invented')

    def test_aggregate_keeps_family_and_metric_axes_and_rejects_missing(self):
        rows=[]
        for case in workloads.suite('development'):
            success=not case['failing_jobs']
            rows.append({'id':case['id'],'result':{'status':'completed' if success else 'blocked',
                         'completion_ticks':10 if success else None,'blocker_ticks':None if success else 4,
                         'busy_worker_ticks':20}})
        report={'status':'completed','all_containers_removed':True,'cases':rows}
        summary=qualify.aggregate(report)
        for family in workloads.FAMILIES:
            self.assertEqual(summary[family],{'completion_sum':30,'blocker_sum':12,'busy_sum':120})
        for bad in [dict(report,status='withhold'),dict(report,all_containers_removed=False),dict(report,cases=rows[:-1])]:
            with self.assertRaises(ValueError):qualify.aggregate(bad)


if __name__=='__main__':unittest.main()
