#!/usr/bin/env python3
"""Calibrate acceptance observations against partial valid behavior and mutants.

The copying stub deliberately lacks update safety. It is not a reference
solution and is never used as a candidate starting implementation.
"""
import importlib.util
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location('lifecycle_evaluator', ROOT / 'experiments/development-harness/multi-scale/large-01/evaluate.py')
evaluator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(evaluator)

COPYING_MUTANT = r'''#!/usr/bin/python3
import argparse,json,shutil
from pathlib import Path
p=argparse.ArgumentParser()
p.add_argument('command'); p.add_argument('--source'); p.add_argument('--target'); p.add_argument('--plan'); p.add_argument('--json',action='store_true')
a=p.parse_args(); target=Path(a.target)
if a.command=='plan':
    source=Path(a.source)
    print(json.dumps({'schema_version':1,'status':'ready','source':str(source),
                     'actions':[{'path':str(x.relative_to(source)),'kind':'add'} for x in source.rglob('*') if x.is_file()]}))
elif a.command=='apply':
    plan=json.loads(Path(a.plan).read_text()); source=Path(plan['source'])
    if MODE!='lie':
        shutil.copytree(source,target,dirs_exist_ok=True)
        (target/'.agent-project').mkdir(exist_ok=True)
        (target/'.agent-project/state.json').write_text(json.dumps({'managed_paths':sorted(str(x.relative_to(source)) for x in source.rglob('*') if x.is_file())}))
    print(json.dumps({'status':'applied','transaction_id':'mutant-transaction'}))
elif a.command=='status':
    print((target/'.agent-project/state.json').read_text())
'''


class EvaluatorTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='lifecycle-evaluator-test-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.candidate = self.root / 'candidate'
        (self.candidate / 'scripts').mkdir(parents=True)

    def scenario(self, mode='copy'):
        cli = self.candidate / 'scripts/manage-agent-project'
        cli.write_text(COPYING_MUTANT.replace('import argparse,json,shutil', f"MODE={mode!r}\nimport argparse,json,shutil"))
        cli.chmod(0o755)
        case = self.root / 'case'
        case.mkdir()
        return evaluator.Scenario(case, self.candidate)

    def test_valid_fresh_copy_passes_bytes_modes_and_preservation_checks(self):
        evaluator.install(self.scenario())

    def test_self_reported_success_without_files_is_rejected(self):
        with self.assertRaises(AssertionError):
            evaluator.install(self.scenario('lie'))

    def test_copying_over_existing_user_content_is_rejected(self):
        with self.assertRaisesRegex(AssertionError, 'unsafe operation returned success'):
            evaluator.existing_conflict(self.scenario())

    def test_copying_over_local_edit_is_rejected(self):
        with self.assertRaisesRegex(AssertionError, 'local customization lost'):
            evaluator.local_preserved(self.scenario())

    def test_missing_implementation_has_no_semantic_passes(self):
        result = evaluator.evaluate(self.candidate, 3)
        self.assertEqual(result['semantic_checks_passed'], 0)
        self.assertFalse(result['semantic_checks_accepted'])
        self.assertIsNone(result['release_accepted'])

    def test_later_stages_retain_every_earlier_scenario(self):
        first = {name for name, _ in evaluator.scenarios(1)}
        second = {name for name, _ in evaluator.scenarios(2)}
        third = {name for name, _ in evaluator.scenarios(3)}
        self.assertTrue(first < second < third)
        self.assertEqual(len(third), len(evaluator.scenarios(3)))


if __name__ == '__main__':
    unittest.main()
