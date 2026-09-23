import importlib.util
import json
from pathlib import Path
import subprocess
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('study_runtime', ROOT / 'experiments/development-harness/cycle-003/large-02/runtime.py')
R = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(R)


class StartupTests(unittest.TestCase):
    def runtime(self):
        value = R.StudyDocker.__new__(R.StudyDocker)
        value.identity = 'owned-container'
        value.expected_cache = 'a' * 64
        value.preparation = None
        return value

    def test_docker_ready_alone_does_not_admit_model(self):
        value = self.runtime()
        ready = subprocess.CompletedProcess([], 0, json.dumps({'docker_version': 'fixture', 'cache_index_sha256': 'a' * 64}), '')
        with patch.object(R.campaign.Docker, 'start'), patch.object(R.subprocess, 'run', side_effect=[subprocess.CompletedProcess([], 1, '', ''), ready]) as run, patch.object(R.time, 'sleep'):
            value.start()
        self.assertEqual(run.call_count, 2)
        self.assertEqual(value.preparation['status'], 'ready')
        self.assertFalse(value.preparation['model_started_during_preparation'])

    def test_changed_cache_stops_container_before_model(self):
        value = self.runtime()
        wrong = subprocess.CompletedProcess([], 0, json.dumps({'docker_version': 'fixture', 'cache_index_sha256': 'b' * 64}), '')
        with patch.object(R.campaign.Docker, 'start'), patch.object(R.campaign.Docker, 'stop') as stop, patch.object(R.subprocess, 'run', return_value=wrong):
            with self.assertRaisesRegex(R.campaign.CampaignError, 'identity changed'):
                value.start()
        stop.assert_called_once()
        self.assertEqual(value.preparation['status'], 'failed')


if __name__ == '__main__':
    unittest.main()
