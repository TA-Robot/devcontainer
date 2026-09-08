import importlib.util
import os
from pathlib import Path
import tempfile
import unittest

HERE = Path(__file__).resolve().parents[1]/'experiments/development-harness/scheduling/adaptive_pair_v1'
spec = importlib.util.spec_from_file_location('adaptive_pair', HERE/'run.py')
pair = importlib.util.module_from_spec(spec); spec.loader.exec_module(pair)


class PairTests(unittest.TestCase):
    def test_fixed_order_budget_and_source_surface(self):
        config = pair.read(HERE/'config.json')
        self.assertEqual(config['conditions'], ['solo', 'adaptive'])
        self.assertEqual(config['max_live_starts'], 2)
        sources = pair.identity()
        self.assertIn(str(HERE.relative_to(pair.ROOT)/'protocol.md'), sources)
        self.assertIn('experiments/development-harness/scheduling/native_actor_v1/accounting.py', sources)

    def test_submission_symlink_and_size(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d); (p/'a').write_text('valid bytes'); (p/'b').symlink_to(p/'a')
            with self.assertRaises(OSError): pair.freeze_submission(p/'b',p/'out')
            (p/'a').write_bytes(b'a'*65537)
            with self.assertRaises(ValueError): pair.freeze_submission(p/'a',p/'out')

    def test_execution_rejects_changed_seal_before_start(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)
            pair.save(p/'plan.json', {'source_sha256': {}, 'config': pair.read(HERE/'config.json'), 'execution':'synthetic'})
            with self.assertRaises(ValueError): pair.execute(p,True,None)
            self.assertFalse((p/'start-solo.json').exists())

    @unittest.skipUnless(os.environ.get('ADAPTIVE_PAIR_DOCKER')=='1','explicit Docker preflight')
    def test_frozen_pair_full_path_and_no_replay(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(os.environ.get('ADAPTIVE_PAIR_EVIDENCE',str(Path(d)/'pair')))
            result=pair.run(p,fake=True)
            self.assertEqual(result['status'],'completed',result)
            raw=pair.read(p/'result.json')
            self.assertEqual(set(raw['actors']),{'solo','adaptive'})
            self.assertTrue(all(r['status']=='completed' and r['removed'] for r in raw['actors'].values()))
            self.assertTrue(all(r['cleanup']=='confirmed' for r in raw['assessments'].values()))
            self.assertEqual(pair.read(p/'plan.json')['source_sha256'],pair.identity())
            self.assertLess((p/'start-adaptive.json').stat().st_mtime_ns,(p/'assessment-solo/seal.json').stat().st_mtime_ns)
            with self.assertRaises(FileExistsError): pair.run(p,fake=True)


if __name__=='__main__':unittest.main()
