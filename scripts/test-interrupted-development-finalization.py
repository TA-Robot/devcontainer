"""Recovery must not turn saved passing code into submitted or known-cost success."""
import copy
import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]

def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module

finalizer = load('interrupted_finalizer', ROOT / 'experiments/development-harness/automatic/finalize_interrupted.py')
report = load('interrupted_report', ROOT / 'experiments/development-harness/automatic/report.py')
fixtures = load('recovery_campaign_fixture', ROOT / 'scripts/test-development-campaign.py')


class InterruptedFinalizationTests(unittest.TestCase):
    def setUp(self):
        self.f = fixtures.CampaignTests();self.f.setUp();self.addCleanup(self.f.doCleanups)
        self.f.manifest['scale'] = 'small'
        self.f.manifest['phases'] = self.f.manifest['phases'][:1]
        self.state = self.f.initialize()
        self.state.update(status='interrupted', active={'phase': self.state['manifest']['phases'][0]['id'],
                          'session': 'session-00', 'reserved_seconds': 1})

    def test_projection_preserves_original_and_leaves_usage_unknown_and_unsubmitted(self):
        original = copy.deepcopy(self.state)
        value = finalizer.projected_state(self.state)
        self.assertEqual(self.state, original)
        self.assertEqual(value['total_seconds'], 1)
        self.assertEqual(value['sessions'], [])
        self.assertEqual(value['next_phase'], 0)
        decision = finalizer.compare.admission.assess(value)
        self.assertFalse(decision['usage_complete'])
        self.assertFalse(decision['submitted_within_observed_budget'])
        self.assertFalse(decision['admitted'])

    def test_passing_recovered_artifact_cannot_be_a_final_submission_or_speed_claim(self):
        state = finalizer.projected_state(self.state)
        expected = [{'name': 'required', 'phase': 1, 'dimension': 'behavior'}]
        quality = finalizer.compare.grade({'source_unchanged': True, 'checks': [{**expected[0], 'status': 'passed'}]}, expected)
        rows = [{'condition': name, 'kind': 'recovered', 'phase': 1, 'seconds': None, 'quality': quality}
                for name in ('control', 'improved')]
        config = {'task': 'duplicates-v1', 'mode': 'prospective', 'conditions': [{'id': 'control'}, {'id': 'improved'}]}
        result = finalizer.compare.summarize(config, [state, state], rows, expected)
        self.assertIsNone(result['speed_ratio'])
        for value in result['conditions'].values():
            self.assertIsNone(value['terminal'])
            self.assertIsNone(value['final_quality_accepted'])
            self.assertFalse(value['quality_and_budget_passed'])

    def test_invalid_or_repeated_recovery_is_rejected(self):
        for change in ({'reserved_seconds': 1e9}, {'session': '../escape'}, {'phase': 'unreleased'}):
            value = copy.deepcopy(self.state);value['active'].update(change)
            with self.subTest(change=change), self.assertRaises(ValueError):
                finalizer.projected_state(value)
        value = finalizer.projected_state(self.state)
        value['status'] = 'interrupted';value['active'] = self.state['active']
        with self.assertRaises(ValueError):finalizer.projected_state(value)

    def test_report_exposes_unknown_usage_and_reservation_instead_of_observed_duration(self):
        state = finalizer.projected_state(self.state)
        config = {'task': 'duplicates-v1', 'mode': 'prospective', 'conditions': [{'id': 'control'}, {'id': 'improved'}]}
        result = finalizer.compare.summarize(config, [state, state], [], [])
        result['automatic_execution_completed'] = False
        for value in result['conditions'].values():
            value['development_seconds_kind'] = 'conservative_reservation'
        text = report.render(result)
        self.assertIn('予約分を計上、実測欠測', text)
        self.assertIn('使用量不明', text)
        self.assertIn('一括実行は中断', text)
        self.assertIn('速度比: 算出しない', text)

    def test_no_artifact_or_output_created_without_verified_stop(self):
        output = self.f.root / 'finalized'
        config = {'conditions': [{'id': 'control', 'state': str(self.f.output)},
                                  {'id': 'improved', 'state': str(self.f.output)}]}
        sealed = self.f.root / 'sealed'
        with patch.object(finalizer.compare.campaign, 'read', side_effect=[{'config': config}, self.state, self.state]), \
             patch.object(finalizer.compare, 'verify'), \
             patch.object(finalizer.compare, 'stopped_state', side_effect=ValueError('still running')), \
             patch.object(finalizer.compare.campaign, 'snapshot') as snapshot:
            with self.assertRaises(ValueError):finalizer.finalize(sealed, output)
            snapshot.assert_not_called()
            self.assertFalse(output.exists())


if __name__ == '__main__':unittest.main()
